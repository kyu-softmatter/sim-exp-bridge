#!/usr/bin/env python3
"""Validate a bridge document. The README table names the rules and is the
one place that counts them -- this line said "Seven" for six of them ago.

    python3 validate.py threads/trap-stiffness-recovery/r1/ask_simulation.json
    python3 validate.py --all
    python3 validate.py --resolve --root am=PATH --root bd=PATH

JSON Schema covers R1 only. The rules that matter most here -- R3 (send
primitives, not composites), R4 (an unresolved assumption keeps the document a
draft) and R5 (a number may not come home and be read as independent) -- are
about *provenance*, which no schema expresses. They live here.

Exit 0 = clean or warnings only. Exit 1 = at least one error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEMA_DIR = ROOT / "schema"

SCHEMA_FOR = {
    "softmatter.ask_simulation/0.1": "ask_simulation.schema.json",
    "softmatter.ask_experiment/0.1": "ask_experiment.schema.json",
}

#: Who reads each direction. The consumer is what R5 is defined against.
CONSUMER = {"experiment_to_simulation": "bd", "simulation_to_experiment": "am"}

#: R3. Composites that must never appear in `system_primitives`.
#: gamma = 3*pi*eta*d and gamma = 6*pi*eta*a are the same formula, so sending
#: the composite is where a factor of 2 enters without anybody lying. Send eta
#: and d; let the side that owns pint form the product.
COMPOSITES = {
    "gamma", "gamma_0", "gamma_corr", "tau_k", "tau_b", "tau_p", "f_c",
    "d_diff", "diffusion", "l_k", "kt", "k_star", "s_0", "omega_c",
}

#: R2. A deliberately small unit vocabulary: this is the wire-level sanity
#: check, not a unit system. BD parses for real with pint.
UNIT_TOKENS = {
    "m", "cm", "mm", "um", "nm", "pm",
    "s", "ms", "us", "ns", "min", "hour",
    "K", "degC",
    "g", "kg", "mg",
    "N", "mN", "uN", "nN", "pN",
    "Pa", "mPa", "kPa",
    "J", "mJ", "uJ", "aJ",
    "Hz", "kHz", "MHz",
    "W", "mW", "uW",
    "mol", "L", "mL", "uL",
    "px", "count", "percent", "dimensionless", "fps", "rad",
}
_TOKEN_RE = re.compile(r"^([A-Za-z]+)(?:\^(-?\d+))?$")


def parse_unit(unit: str) -> tuple[bool, str]:
    """True if every token is known. No arithmetic -- existence only."""
    if not unit or unit.strip() != unit:
        return False, "empty or padded"
    for part in re.split(r"[*/]", unit):
        part = part.strip()
        if not part:
            return False, f"empty factor in {unit!r}"
        m = _TOKEN_RE.match(part)
        if not m:
            return False, f"{part!r} is not <token> or <token>^<int>"
        if m.group(1) not in UNIT_TOKENS:
            return False, f"unknown unit token {m.group(1)!r}"
    return True, ""


#: README table T1, in code so there is one copy. A range where the mapping
#: genuinely is a range: `computed` inherits the worst tier of its inputs, and the
#: wire does not carry the inputs, so 1-3 are all reachable and nothing narrower
#: can be checked. This is why `tier` is non-normative rather than validated.
T1 = {
    "measured": {0},
    "handbook": {0},
    "computed": {1, 3},        # 1 from measured inputs, 3 inherited from an assumed one
    "assumed": {3},
    "simulated": set(),        # not admissible as a tier at all -- see C3
    "round_trip": set(),
}

#: How bad a class is, for picking the worst in an entry (rule R10). A citation
#: must never read better than the entry's weakest number.
SEVERITY = {"measured": 0, "handbook": 0, "computed": 1,
            "simulated": 2, "round_trip": 2, "assumed": 3}


#: Rationales already printed in this run, keyed by (rule, rationale). The
#: reasoning in these messages is what makes them work -- R13's closing clause
#: is the reason it did not recruit a reader into editing a sealed file. But the
#: same multi-sentence rationale was being repeated up to eleven times in one
#: run, and at that volume people read the rule ID and skip the text, which
#: defeats the clause. So the rationale is printed once and referred to after.
#: Nothing is trimmed; it stops being duplicated.
_RATIONALES_SEEN: set[tuple[str, str]] = set()


class Report:
    def __init__(self, path: Path):
        self.path = path
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def _fmt(self, rule: str, head: str, why: str) -> str:
        if not why:
            return f"{rule}  {head}"
        key = (rule, why)
        if key in _RATIONALES_SEEN:
            return f"{rule}  {head}  [{rule} rationale printed above]"
        _RATIONALES_SEEN.add(key)
        return f"{rule}  {head} {why}"

    def err(self, rule: str, msg: str, why: str = "") -> None:
        self.errors.append(self._fmt(rule, msg, why))

    def warn(self, rule: str, msg: str, why: str = "") -> None:
        self.warnings.append(self._fmt(rule, msg, why))

    @property
    def ok(self) -> bool:
        return not self.errors


# ---------------------------------------------------------------- R1: schema
#: True while --selftest runs. A skipped rule is not a passed rule, so under the
#: CI entry point a missing dependency is an error rather than a warning. BD's
#: simulation_bot interpreter has no jsonschema, and `--selftest` there printed
#: "selftest clean" with R1 never having run -- a checker reporting clean with a
#: rule switched off is the exact failure both repositories keep writing down.
STRICT = False


def r1_schema(doc: dict, rep: Report) -> None:
    name = SCHEMA_FOR.get(doc.get("schema"))
    if name is None:
        rep.err("R1", f"unknown schema {doc.get('schema')!r}")
        return
    try:
        import jsonschema
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
    except ImportError:  # pragma: no cover
        (rep.err if STRICT else rep.warn)(
            "R1", f"jsonschema/referencing not importable under {sys.executable} "
                  "-- the shape rule did not run. Install them, or run this with an "
                  "interpreter that has them; do not read the absence as a pass.")
        return

    registry = Registry()
    for f in SCHEMA_DIR.glob("*.json"):
        registry = registry.with_resource(
            f.name, Resource.from_contents(json.loads(f.read_text()))
        )
    schema = json.loads((SCHEMA_DIR / name).read_text())
    validator = Draft202012Validator(schema, registry=registry)
    for e in sorted(validator.iter_errors(doc), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in e.path) or "<root>"
        rep.err("R1", f"{loc}: {e.message}")


# ------------------------------------------------------------ R2: unit parse
def r2_units(doc: dict, rep: Report) -> None:
    def walk(node, where):
        if isinstance(node, dict):
            if "unit" in node and isinstance(node["unit"], str):
                ok, why = parse_unit(node["unit"])
                if not ok:
                    rep.err("R2", f"{where}.unit = {node['unit']!r}: {why}. "
                                  "Refuse, do not guess -- a guessed unit is a "
                                  "silent factor.")
            for k, v in node.items():
                walk(v, f"{where}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{where}[{i}]")

    walk(doc, "")


# ------------------------------------------------- R3: primitives, not composites
def r3_primitives(doc: dict, rep: Report) -> None:
    for i, q in enumerate(doc.get("system_primitives", [])):
        sym = str(q.get("symbol", "")).lower()
        if sym in COMPOSITES:
            rep.err("R3", f"system_primitives[{i}] carries the composite "
                          f"{q.get('symbol')!r}. Move it to reference_only and "
                          "send the primitives it is built from; the receiving "
                          "side forms the product with its own unit library.")


# ------------------------------------------------- R4: unknown keeps it a draft
def r4_draft(doc: dict, rep: Report) -> None:
    """An unresolved assumption has to be declared as unresolved.

    Not "the document must be a draft". Those are different claims, and
    conflating them broke a correction: `supersedes_prior` exists so a fix does
    not wait, and requiring `draft` alongside it meant a correcting document
    could not also raise a newly-found unknown. BD hit this in r4 and moved the
    item into `findings[]` rather than weaken it -- which files an undeclared
    assumption as a disagreement, and R4 exists because those are not the same
    thing.

    So either form satisfies this rule: `assumptions_resolved: false`, which
    works with any status, or the older `status: draft` on its own.
    """
    unknown = [a["name"] for a in doc.get("assumptions", [])
               if a.get("status") == "unknown"]
    status = doc.get("status")
    resolved = doc.get("assumptions_resolved")

    if unknown:
        declared = resolved is False or status == "draft"
        if not declared:
            rep.err("R4", f"{len(unknown)} assumption(s) are still unknown "
                          f"({', '.join(unknown)}) but the document declares neither "
                          "`assumptions_resolved: false` nor `status: draft`. An "
                          "unresolved assumption is the one class of difference no "
                          "number reveals.")
        elif resolved is not False and status == "draft":
            rep.warn("R4", "unknowns are declared only through `status: draft`.",
                     "Prefer `assumptions_resolved: false`, which survives a later "
                     "status change.")
    else:
        if resolved is False:
            rep.err("R4", "`assumptions_resolved: false` but every assumption is "
                          "shared or differs. The flag is the claim, not decoration.")
        if status == "draft":
            rep.warn("R4", "every assumption is resolved; status may leave draft "
                           "once a human sets confirmed_by.")


# --------------------------------------------------------- R5: circular evidence
def r5_circular(doc: dict, rep: Report) -> None:
    """A binding requirement may not rest on the consumer's own number.

    The failure this catches is not "the other repo appears in my ancestry" --
    after two rounds it always does. It is narrower: a number this repository
    produced, handed back to it as though it were independent evidence. Three
    rounds of that and both knowledge bases agree with nobody having measured
    anything twice.

    Soft requirements may echo it, because a disclosed echo is useful. Hard ones
    may not, because a hard requirement is what a gate refuses against.
    """
    consumer = CONSUMER.get(doc.get("direction", ""))
    if consumer is None:
        return
    for i, req in enumerate(doc.get("requirements", [])):
        own = [r["ref"] for r in req.get("basis_refs", [])
               if r.get("ref", "").startswith(f"{consumer}:")]
        if not own:
            continue
        sym = req.get("symbol")
        if req.get("hard") is True:
            rep.err("R5", f"requirements[{i}] ({sym}) is hard and rests on "
                          f"{consumer}'s own number: {own[0]}. This is the "
                          "consumer's value returning as independent evidence. "
                          "Either derive it here, or mark hard: false and "
                          "declare it in gaps[].")
        else:
            rep.warn("R5", f"requirements[{i}] ({sym}) echoes {consumer}'s own "
                           f"number ({own[0]}).",
                     "Round-trip, soft, so allowed. Confirm it is declared in gaps[].")


def r5b_round_trip_labels(doc: dict, rep: Report) -> None:
    """A number the consumer produced must say so in `evidence`.

    R5 catches a *requirement* resting on the consumer's number. This catches the
    quantity itself: r2 carries `gamma_corr` with `origin: am`, honestly described
    in prose as "your assumption arithmetic", but tagged `evidence: assumed` --
    so only a reader of the prose learns it came home. `round_trip` exists for
    exactly this and nothing used it.

    `parsed_back.received` is exempt and must stay exempt: it exists to echo the
    consumer's numbers back in the consumer's own `evidence`, so that the
    consumer can check the round-trip. Relabelling those `round_trip` would
    destroy the block's only purpose. The rule is about a consumer-origin number
    sitting somewhere it could be read as the producer's own.

    A warning, not an error: the documents this fires on are not wrong, they are
    under-labelled, and they belong to the other side.
    """
    consumer = CONSUMER.get(doc.get("direction", ""))
    if consumer is None:
        return

    EXEMPT = ".parsed_back.received"

    def walk(node, where):
        if where.startswith(EXEMPT):
            return
        if isinstance(node, dict):
            if node.get("origin") == consumer and "evidence" in node:
                if node["evidence"] != "round_trip":
                    rep.warn("R5b", f"{where} ({node.get('symbol')}) has "
                                    f"origin: {consumer} -- the consumer's own "
                                    f"number -- but evidence: {node['evidence']!r}. "
                                    "`round_trip` is the label for a value that came "
                                    "home; prose in `source` does not reach a reader "
                                    "who only parses the JSON.")
            for k, v in node.items():
                walk(v, f"{where}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{where}[{i}]")

    walk(doc, "")


def r8_tier_not_derivable(doc: dict, rep: Report) -> None:
    """`tier` is non-normative, so this warns rather than refusing.

    It exists because the field drifted silently: across r1-r5 a `computed` value
    ships as tier 1, 2 and 3, and every tier-2 case descends from six values in
    r1 that were copied forward into three later rounds. Tier 2 in BD's scale
    means "literature, unverified", which is not what a model output from
    trapping/goa.py is -- the sender was using the receiver's vocabulary with a
    different meaning, and nothing checked it.
    """
    def walk(node, where):
        if isinstance(node, dict):
            ev, tier = node.get("evidence"), node.get("tier")
            if ev in T1 and isinstance(tier, int):
                allowed = T1[ev]
                if not allowed:
                    rep.warn("R8", f"{where} ({node.get('symbol')}) is "
                                   f"evidence: {ev!r}, which has no tier at all; "
                                   f"tier {tier} is ignored.")
                elif tier not in allowed:
                    rep.warn("R8", f"{where} ({node.get('symbol')}) ships tier "
                                   f"{tier} but evidence: {ev!r} reaches only "
                                   f"{sorted(allowed)} via T1.",
                             "Ignored -- `evidence` is authoritative. Leave sealed "
                             "documents alone; omit `tier` in new ones. This warning "
                             "standing is the record that the field was normative when "
                             "the document was written.")
            for k, v in node.items():
                walk(v, f"{where}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{where}[{i}]")

    walk(doc, "")


def r12_gap_kind(doc: dict, rep: Report) -> None:
    """A gap without a `kind` sends the reader to the wrong place.

    `would_need` collapses "work someone could do" with "a limit of the
    framework" and with "the bytes are on another machine". The thread paid for
    each of those once: r2 said a wall runner was needed when no runner there can
    learn anything about a wall, and AM's P7 read as a few minutes of analysis
    when it is a data transfer off an instrument PC. Both readings send somebody
    somewhere, and only one of them was right in each case.
    """
    for i, g in enumerate(doc.get("gaps", []) or []):
        if "kind" not in g:
            rep.warn("R12", f"gaps[{i}] ({str(g.get('what'))[:60]!r}) has no `kind`.",
                     "not_yet_built, not_buildable_here, needs_human_action and "
                     "needs_data_transfer are four different instructions to the "
                     "reader; `would_need` alone does not separate them. Leave sealed "
                     "documents alone -- backfilling `kind` into r2 is what caused the "
                     "R6 cascade. Carry it in new gaps.")
        elif g.get("kind") == "not_buildable_here" and g.get("owner") not in (None, "nobody", "human"):
            rep.warn("R12", f"gaps[{i}] is not_buildable_here but owner is "
                            f"{g.get('owner')!r}. If no work inside the framework helps, "
                            "assigning it to a side leaves a task nobody can finish; "
                            "`nobody` is the honest owner.")


def r13_ref_is_a_path(doc: dict, rep: Report) -> None:
    """`@r<N>` in a ref string masks R6's own revision branch.

    Before R6 resolved revisions, embedding `@r<N>` in the ref was the only way
    to cite a suffixed manifest key. It worked, and it cost two things: the ref
    stopped being a path, and the citation then matched by exact key -- so R6's
    revision branch fired on nothing and looked healthy. BD found this in its own
    r8 after the branch landed, which is why the branch needed inline checks to
    be observably alive.

    A warning and not an error, because the documents carrying it are sealed and
    a cited document is not edited. The warning standing forever is the record of
    when the convention changed.
    """
    def walk(node, where):
        if isinstance(node, dict):
            r = node.get("ref")
            if isinstance(r, str) and "@" in r:
                rep.warn("R13", f"{where}.ref is {r!r}.",
                         "`@r<N>` is a manifest key form, not part of a path. R6 "
                         "resolves revisions itself now, so the ref should be the path "
                         "and the hash should name the revision. Leave sealed documents "
                         "alone; do not write new ones this way.")
            for k, val in node.items():
                walk(val, f"{where}.{k}")
        elif isinstance(node, list):
            for i, val in enumerate(node):
                walk(val, f"{where}[{i}]")

    walk(doc, "")


# -------------------------------------------------------------- R6: hash drift
def r6_hashes(doc: dict, rep: Report, manifest: dict | None,
              path: Path | None = None) -> None:
    """Positive fixtures are exempt, and that exemption is the real fix.

    `fixtures/valid/c6-correction-with-unknown.json` guards R4. Its refs are a
    frozen snapshot, so coupling them to the live manifest meant a legitimate
    upstream change -- relabelling one `evidence` field in r2 -- turned the CI
    entry point red for a reason that had nothing to do with the rule under
    guard. The BD session repaired the hash by hand and flagged it; the repair
    was right triage and the coupling was my defect.

    `fixtures/invalid/r6-stale-source-hash.json` is NOT exempt: it is the test
    that R6 still fires.

    A manifest value of `sha256:PLACEHOLDER` is a *named refusal*, not a
    mismatch. Somebody wrote down that the hash is not known yet rather than
    guessing one -- the same instinct as `BLOCKED` over an invented number on
    the AM side, or refusing to run a card with no runner on the BD side. It
    still fails, because an unverified provenance claim is unverified; what
    changes is that the output says which of the two it is.
    """
    PLACEHOLDER = "placeholder"
    if path is not None and "fixtures/valid/" in path.as_posix():
        rep.warn("R6", "skipped: positive fixtures carry frozen snapshots by design.")
        return
    if manifest is None:
        rep.warn("R6", "no hashes.json -- upstream drift unchecked")
        return
    seen: list[tuple[str, str]] = []

    def walk(node):
        if isinstance(node, dict):
            if "ref" in node and "hash" in node:
                seen.append((node["ref"], node["hash"]))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(doc)
    for ref, h in seen:
        # A citation is FROZEN and a manifest is LIVE. Accept any registered
        # revision of a ref, not only the unsuffixed one.
        #
        # Without this, adding metadata to an already-cited document cascades
        # without limit. It happened: 4652273 added `gaps[].kind` to r2, which
        # moved r2's hash, which broke r8; refreshing the unsuffixed key broke
        # r4, which cites r2; refreshing r4 broke r5 and r7, which cite r4. The
        # refresh is the obvious move and it is the wrong one -- each repair
        # invalidates the next citation down. The `@r<N>` convention already in
        # this manifest is the right answer, and R6 now reads it.
        candidates = {k: v for k, v in manifest.items()
                      if k == ref or k.startswith(f"{ref}@")}
        known = manifest.get(ref)
        if candidates and h in candidates.values():
            matched = [k for k, v in candidates.items() if v == h]
            if ref not in matched:
                rep.warn("R6", f"{ref} matches {matched[0]} rather than the "
                               "unsuffixed key -- a citation frozen at an earlier "
                               "revision, which is expected and fine.")
            continue
        if not candidates:
            rep.err("R6", f"{ref} is in no manifest entry.",
                    "An unregistered ref is an unverifiable provenance claim, which is "
                    "what the PLACEHOLDER branch already refuses -- and less honest, "
                    "since nobody even declared it unknown. It was a warning until the "
                    "AM session found three plan citations pointing at entries that "
                    "exist only on another branch -- the sources of its ROI, its "
                    "exposure and its 520 fps -- while every check passed, because "
                    "nothing read a link. Register the ref, or do not cite it.")
        elif PLACEHOLDER in known.lower() or PLACEHOLDER in h.lower():
            rep.err("R6", f"{ref} is declared UNKNOWN on purpose -- the manifest "
                          f"carries {known}. This is a named refusal, not drift: "
                          "nobody guessed a hash. It still blocks, because the "
                          "provenance claim is unverified. Compute the hash, or "
                          "drop the ref until the artefact exists.")
        elif known != h or known is None:
            regs = ", ".join(f"{k.split('@')[1] if '@' in k else 'unsuffixed'}={v}"
                             for k, v in sorted(candidates.items()))
            rep.err("R6", f"{ref} has moved upstream: document cites {h}, and no "
                          f"registered revision matches ({regs}). Register the "
                          f"revision this document was written against as "
                          f"{ref}@r<N> -- do NOT refresh the unsuffixed key, which "
                          "invalidates every citation below it in turn.")


# ------------------------------------------------------- R7: confirmed_by is human
MACHINE_NAMES = {"am", "bd", "agent", "claude", "bot", "ci", "auto",
                 "bdbot", "simbot", "system", "pipeline", "true"}


def r7_confirmed_by(doc: dict, rep: Report) -> None:
    def walk(node, where):
        if isinstance(node, dict):
            if "confirmed_by" in node:
                v = node["confirmed_by"]
                if isinstance(v, str) and v.strip().lower() in MACHINE_NAMES:
                    rep.err("R7", f"{where}.confirmed_by = {v!r}. Both "
                                  "repositories reserve this field for a human; "
                                  "the bridge may never write it.")
            for k, v in node.items():
                walk(v, f"{where}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{where}[{i}]")

    walk(doc, "")


# ------------------------------------------- KB import entries (frontmatter)
def validate_kb_entry(path: Path, manifest: dict | None) -> Report:
    """The same seven rules, minus the ones that only apply to a wire document.

    An imported KB entry is where a foreign number comes to rest, so R6 (is the
    upstream still what we imported?) and R7 (nobody signed this but a human)
    are the two that matter; R1 runs against kb_external_entry.schema.json.
    """
    rep = Report(path)
    text = path.read_text()
    if not text.startswith("---\n"):
        rep.err("R0", "no YAML frontmatter")
        return rep
    end = text.find("\n---", 4)
    if end < 0:
        rep.err("R0", "unterminated frontmatter")
        return rep
    try:
        import yaml
        fm = yaml.safe_load(text[4:end])
        # YAML turns an unquoted 2026-09-15 into a date object. Both repositories
        # write frontmatter dates unquoted, so normalise rather than demand quotes.
        import datetime as _dt
        fm = {k: (v.isoformat() if isinstance(v, (_dt.date, _dt.datetime)) else v)
              for k, v in fm.items()}
    except ImportError:  # pragma: no cover
        rep.warn("R1", "PyYAML not installed -- frontmatter unchecked")
        return rep

    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        registry = Registry()
        for f in SCHEMA_DIR.glob("*.json"):
            registry = registry.with_resource(
                f.name, Resource.from_contents(json.loads(f.read_text()))
            )
        schema = json.loads((SCHEMA_DIR / "kb_external_entry.schema.json").read_text())
        for e in sorted(Draft202012Validator(schema, registry=registry).iter_errors(fm),
                        key=lambda e: list(e.path)):
            loc = "/".join(str(p) for p in e.path) or "<root>"
            rep.err("R1", f"{loc}: {e.message}")
    except ImportError:  # pragma: no cover
        rep.warn("R1", "jsonschema not installed -- frontmatter shape unchecked")

    # R6 against the entry's own source, plus every ref in derived_from.
    if manifest is not None:
        pairs = [(fm.get("source_ref"), fm.get("source_hash"))]
        pairs += [(d.get("ref"), d.get("hash")) for d in (fm.get("derived_from") or [])]
        for ref, h in pairs:
            if not ref:
                continue
            known = manifest.get(ref)
            if known is None:
                rep.warn("R6", f"{ref} not in hashes.json")
            elif known != h:
                rep.err("R6", f"{ref} has moved upstream ({h} -> {known}). "
                              "Supersede this entry; do not edit it in place.")

    # R10 -- one class for an entry holding several kinds of evidence.
    classes = fm.get("evidence_classes")
    if isinstance(classes, dict) and classes:
        worst = max(classes.values(), key=lambda c: SEVERITY.get(c, 0))
        declared = fm.get("evidence_class")
        if SEVERITY.get(declared, -1) < SEVERITY.get(worst, 0):
            bad = [k for k, v in classes.items() if v == worst]
            rep.err("R10", f"evidence_class: {declared!r} is better than the worst "
                           f"entry in evidence_classes ({worst!r}, on "
                           f"{', '.join(sorted(bad))}). The frontmatter is what a "
                           "citation surfaces; prose in the body does not reach a "
                           "reader who only sees the path and the class.")
    elif fm.get("evidence_class") in ("measured", "handbook"):
        rep.warn("R10", f"evidence_class: {fm.get('evidence_class')!r} with no "
                        "`evidence_classes` map. If any value in this entry is "
                        "assumed, computed or a model output, this reads better than "
                        "the entry is -- add the map.")

    r7_confirmed_by(fm, rep)

    # A foreign entry is never a gate threshold by default.
    if fm.get("may_be_gate_threshold") is True:
        rep.warn("R8", "may_be_gate_threshold: true on an imported entry. A gate "
                       "clearing against a foreign number emits a margin that "
                       "reads as locally measured.")
    # And a simulated number must not be sitting in a measured-only namespace.
    if fm.get("evidence_class") == "simulated" and "calibrations" in str(path):
        rep.err("R9", "an entry with evidence_class: simulated is in a "
                      "calibrations namespace, which means 'measured on this "
                      "instrument'. The path itself would be false.")
    return rep


# ------------------------------------- R11: a copy that drifted, across rounds
def _quantities(node, where, out):
    """Every `{symbol, value, unit, origin}` node in a document, with its path."""
    if isinstance(node, dict):
        if {"symbol", "value", "unit", "origin"} <= node.keys():
            out.append((node, where))
        for k, v in node.items():
            _quantities(v, f"{where}.{k}", out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _quantities(v, f"{where}[{i}]", out)


#: Relative tolerance below which a same-origin difference is recomputation
#: rather than drift. See r11_thread's docstring for how it was chosen.
R11_TOL = 1e-3


def r11_thread(thread_dir: Path, manifest: dict | None) -> Report:
    """One value, two documents, two answers -- and nothing noticed.

    This generalises the two defects this thread actually produced, which BD was
    right to call one shape rather than two coincidences:

      * `2 D t_exp / 3` was wrong in r1 and was still wrong three rounds later,
        because every later document had copied it;
      * six `tier` values in r1 were unreachable from their own `evidence` and
        propagated into r2, r3 and r5 the same way.

    Both were numbers living in text that each document carried carefully and
    nothing cross-checked. The discriminator is `origin`:

      same symbol, SAME origin   -> one is a copy of the other. They must agree.
      same symbol, DIFFERENT origin -> independent re-derivation, which is the
                                    protocol working. Reported, never an error:
                                    AM's f_c = 9.9 Hz against BD's 9.86 Hz is a
                                    round-trip check passing, not a defect.

    A disagreement named in some document's `corrects[]` is a declared
    supersession and is exempt -- that is what `corrects[]` is for.

    `R11_TOL` separates recomputation from disagreement. Re-deriving kT in a
    later round and printing one more figure moves it by ~1e-4 relative; the
    drifts this rule exists for are factors (2*u/3 against u/3 is 2x, and a tier
    does not have a value at all). 1e-3 sits two decades above the noise this
    thread actually produced and three below the smallest real drift in it.
    """
    rep = Report(thread_dir)
    docs = sorted(thread_dir.glob("r*/ask_*.json"))
    if len(docs) < 2:
        return rep

    corrected: set[str] = set()
    seen: dict[tuple[str, str], list[tuple[str, float, str, str]]] = {}
    for d in docs:
        try:
            doc = json.loads(d.read_text())
        except json.JSONDecodeError:
            continue
        for c in doc.get("corrects", []) or []:
            for token in (c.get("what", "") + " " + " ".join(c.get("downstream", []) or [])).split():
                corrected.add(token.strip(".,`'\"()"))
        found: list = []
        _quantities(doc, "", found)
        for node, where in found:
            key = (node["symbol"], node["origin"])
            seen.setdefault(key, []).append(
                (d.parent.name, node["value"], node["unit"], where))

    for (symbol, origin), rows in sorted(seen.items()):
        rounds = {r for r, *_ in rows}
        if len(rounds) < 2:
            continue
        units = {u for _, _, u, _ in rows}
        nums = [v for _, v, _, _ in rows]
        if len(units) == 1:
            lo, hi = min(nums), max(nums)
            scale = max(abs(lo), abs(hi)) or 1.0
            if (hi - lo) / scale <= R11_TOL:
                continue        # recomputation, not drift
        if symbol in corrected:
            rep.warn("R11", f"{symbol} (origin {origin}) differs across "
                            f"{sorted(rounds)} and is named in a corrects[] block "
                            "-- declared supersession, exempt.")
            continue
        detail = ", ".join(f"{r}: {v:g} {u}" for r, v, u, _ in rows)
        rep.err("R11", f"{symbol} carries origin {origin} in every round it "
                       f"appears, so the later ones are copies -- and they "
                       f"disagree: {detail}. Either one round corrected it "
                       "without saying so (use corrects[]), or a copy drifted. "
                       "This is the shape that kept 2*D*t_exp/3 alive for three "
                       "rounds.")

    cross: dict[str, set] = {}
    for (symbol, origin), rows in seen.items():
        cross.setdefault(symbol, set()).add(origin)
    for symbol, origins in sorted(cross.items()):
        if len(origins) > 1:
            rows = [r for o in origins for r in seen[(symbol, o)]]
            detail = ", ".join(f"{r}/{o}: {v:g} {u}"
                               for o in sorted(origins)
                               for r, v, u, _ in seen[(symbol, o)])
            nums = [v for o in origins for _, v, _, _ in seen[(symbol, o)]]
            units = {u for o in origins for _, _, u, _ in seen[(symbol, o)]}
            if len(units) > 1:
                verdict = ("in DIFFERENT UNITS, which the round-trip cannot compare "
                           "-- convert before reading this as agreement")
            else:
                spread = (max(nums) - min(nums)) / (max(abs(v) for v in nums) or 1.0)
                verdict = ("and they agree exactly" if spread == 0 else
                           f"and they agree to {spread * 100:.2g} %" if spread <= 0.05
                           else f"and they DIFFER by {spread * 100:.2g} %, which is "
                                "large for a round-trip check -- worth reading")
            rep.warn("R11", f"{symbol} is derived independently on both sides "
                            f"({detail}) {verdict}. Not a defect: this is the "
                            "round-trip check, and this line is its result.")
    return rep


def validate(path: Path, manifest: dict | None) -> Report:
    rep = Report(path)
    try:
        doc = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        rep.err("R0", f"not JSON: {e}")
        return rep
    r1_schema(doc, rep)
    r2_units(doc, rep)
    r3_primitives(doc, rep)
    r4_draft(doc, rep)
    r5_circular(doc, rep)
    r5b_round_trip_labels(doc, rep)
    r8_tier_not_derivable(doc, rep)
    r12_gap_kind(doc, rep)
    r13_ref_is_a_path(doc, rep)
    r6_hashes(doc, rep, manifest, path)
    r7_confirmed_by(doc, rep)
    return rep


# --------------------- R6, resolve branch: a cited revision resolves to a file
#: R6 compares a citation against `hashes.json` and stops there. Both sides of
#: that comparison are strings this repository wrote, and nothing ever opens the
#: file -- so a `rev` naming a commit where the path does not exist passes.
#: `813fcf2` corrected exactly that in r8's JSON; the `.md` twin two files away
#: carries the same ref at the same dead rev and was not corrected, because
#: nothing could see it. One instance is an accident. The second one, sitting in
#: the tree while the first was being fixed by hand, is what promotes this from
#: a note in the README to a branch of the rule.
#:
#: Not a fourteenth rule. R6 already claims a hash is the identity of an
#: upstream artefact, and an identity that resolves to nothing is not one: this
#: is the half of R6 that was never written. It needs checkouts of the two agent
#: repositories, so it cannot run in CI and is opt-in -- `--resolve`. The
#: selftest exercises the mechanism against a temporary git repository, so every
#: branch is observably alive even where the real roots are absent.
RESOLVE_STATUSES = {
    "ok_worktree":  "the working tree matches a registered revision",
    "ok_rev":       "the blob at the cited rev hashes to the cited value",
    "absent":       "the path does not exist in that checkout",
    "advanced":     "the path exists and matches no registered revision",
    "no_recipe":    "a directory ref, and nothing says what to hash",
    "rev_missing":  "the cited rev is not a commit in that checkout",
    "rev_absent":   "the path does not exist at the cited rev",
    "rev_mismatch": "the blob at the cited rev is not the cited hash",
    "no_root":      "no checkout configured for that side -- not checked",
    "no_rev":       "a path-only citation, so there is no revision to resolve",
    "unread":       "a document that could not be parsed -- its refs are UNCHECKED",
}
#: `advanced` is deliberately not an error: the `@r<N>` convention exists so
#: that upstream moving past a frozen citation is the normal case. What it buys
#: is that the move becomes visible at all, and it names the next key to write.
RESOLVE_ERRORS = {"absent", "rev_missing", "rev_absent", "rev_mismatch", "unread"}
RESOLVE_WARNINGS = {"advanced", "no_recipe"}


def _sha16(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()[:16]


def _route(ref: str, roots: dict[str, Path]) -> tuple[Path | None, str]:
    """`<side>:bridge/...` is this repository -- both sides cite bridge
    documents and those live here, which is also why r8's `rev 4652273`
    resolves in no agent repository. Everything else needs that side's
    checkout, and there is no default: guessing a sibling directory would make
    the check's answer depend on where somebody cloned."""
    side, _, path = ref.partition(":")
    # `path@r3` is a manifest key, not a filename. R13 warns on the documents
    # that write it; the resolver's first run tried to open the literal string
    # and reported two of AM's plan citations as missing files, which is a
    # checker inventing a defect -- worse than the one it was looking for.
    path = path.split("@")[0]
    if path.startswith("bridge/"):
        return ROOT, path[len("bridge/"):]
    return roots.get(side), path


def _git_blob(root: Path, rev: str, path: str) -> tuple[str, bytes | None]:
    """Kept separate so the caller can tell *no such commit* from *no such file
    at that commit*. They are different accidents: the first is a citation of
    work that was never pushed, the second is r8's -- a file that exists now,
    cited at a revision from before it was written."""
    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True)

    if git("cat-file", "-e", f"{rev}^{{commit}}").returncode != 0:
        return "rev_missing", None
    kind = git("cat-file", "-t", f"{rev}:{path}")
    if kind.returncode != 0:
        return "rev_absent", None
    if kind.stdout.strip() != b"blob":
        return "no_recipe", None
    return "ok_rev", git("show", f"{rev}:{path}").stdout


def resolve_manifest(manifest: dict, roots: dict[str, Path]) -> list[tuple]:
    """Every registered key, against the working tree of the side that owns it.

    Keys are grouped by path first: `ref` and `ref@r8` are two revisions of one
    artefact, and matching any of them is the point of the revision convention.

    `_subject_of` exists because one key is deliberately not the hash of its own
    path -- `am:bridge/.../r1/ask_simulation.json` holds the *plan's* hash, per
    r2's note, and the proposals file predicted that the first regeneration
    would read it as a false 'moved upstream'. It was right; this resolver was
    the regeneration. A fact that lives only in two prose notes is a fact the
    next checker trips over, so the manifest now states it.
    """
    subject = manifest.get("_subject_of", {})
    groups: dict[str, dict[str, str]] = {}
    for key, value in manifest.items():
        if key.startswith("_"):
            continue
        groups.setdefault(key.split("@")[0], {})[key] = value

    rows = []
    for base, registered in sorted(groups.items()):
        target = subject.get(base, base)
        via = "" if target == base else f"  (by `_subject_of` -> {target})"
        root, rel = _route(target, roots)
        if root is None:
            rows.append((base, "no_root", f"{target.split(':')[0]}: has no checkout{via}"))
            continue
        path = root / rel
        if not path.exists():
            rows.append((base, "absent", f"{rel} is not in {root}{via}"))
        elif path.is_dir():
            rows.append((base, "no_recipe", f"{rel} is a directory{via}"))
        else:
            found = _sha16(path.read_bytes())
            hit = [k for k, v in sorted(registered.items()) if v == found]
            if hit:
                rows.append((base, "ok_worktree", f"working tree = {hit[0]}{via}"))
            else:
                rows.append((base, "advanced",
                             f"working tree is {found}, which is none of the "
                             f"{len(registered)} registered revision(s) "
                             f"({', '.join(sorted(registered))}){via}. Register "
                             f"this one as {base}@r<N> before citing it; do not "
                             f"refresh the unsuffixed key."))
    return rows


def _citations(paths: list[Path]) -> tuple[dict[tuple[str, str, str], list[str]],
                                           list[str]]:
    """(ref, hash, rev) -> the documents carrying it.

    Deduplicated because resolving is a subprocess and r8 alone cites
    `verify_drag_ladder.py` three times; the count is kept because "which
    documents does this dead rev reach" is the first question after a failure.
    """
    out: dict[tuple[str, str, str], list[str]] = {}
    unread: list[str] = []
    for path in paths:
        text = path.read_text()
        if path.suffix == ".md":
            if not text.startswith("---\n"):
                unread.append(f"{path.name}: no frontmatter")
                continue
            end = text.find("\n---", 4)
            try:
                import yaml
                doc = yaml.safe_load(text[4:end])
            except Exception as e:
                # Without PyYAML every `.md` citation vanishes from the run and
                # the summary still reads clean -- one of this repository's two
                # named patterns, in its own new code. Say which documents.
                unread.append(f"{path.name}: {e.__class__.__name__}")
                continue
        else:
            try:
                doc = json.loads(text)
            except json.JSONDecodeError as e:
                unread.append(f"{path.name}: {e}")
                continue
        where = (path.relative_to(ROOT).as_posix()
                 if path.is_relative_to(ROOT) else path.name)

        def walk(node) -> None:
            if isinstance(node, dict):
                ref, h = node.get("ref"), node.get("hash")
                if isinstance(ref, str) and isinstance(h, str):
                    out.setdefault((ref, h, str(node.get("rev") or "")), []).append(where)
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(doc)
    return out, unread


def resolve_citations(paths: list[Path], roots: dict[str, Path],
                      subject: dict[str, str] | None = None) -> list[tuple]:
    """Each distinct citation against the blob at the revision it names.

    This is the half that verifies *history*. The working-tree pass above can
    only ever speak about the tip, and a bridge document is frozen by design --
    so without this, every sealed citation in the repository is unverifiable the
    moment its file is touched upstream.
    """
    rows = []
    cites, unread = _citations(paths)
    for name in unread:
        rows.append((name, "unread", "this document contributed no citations"))
    for (ref, cited, rev), docs in sorted(cites.items()):
        # The cited hash is part of the identity, not decoration: two documents
        # may cite one path at one rev and disagree about what is there, which
        # is the whole point. The selftest caught this line without it -- two
        # cases collapsed onto one key and the passing one overwrote the
        # failing one, which is a fixture reporting on the wrong row.
        seen = (f"{ref} @{rev or '-'} cites {cited}"
                f"  [{docs[0]}{f' +{len(docs) - 1}' if len(docs) > 1 else ''}]")
        if not rev:
            rows.append((seen, "no_rev", "the schema calls `rev` strongly wanted; "
                                         "this is what it buys"))
            continue
        target = (subject or {}).get(ref.split("@")[0], ref)
        if target != ref:
            seen += f"  (by `_subject_of` -> {target})"
        root, rel = _route(target, roots)
        if root is None:
            rows.append((seen, "no_root", f"{target.split(':')[0]}: has no checkout"))
            continue
        status, blob = _git_blob(root, rev, rel)
        if status != "ok_rev":
            rows.append((seen, status, f"git -C {root} cat-file -t {rev}:{rel}"))
            continue
        found = _sha16(blob)
        if found == cited:
            rows.append((seen, "ok_rev", f"{cited} confirmed at {rev}"))
        else:
            rows.append((seen, "rev_mismatch",
                         f"document cites {cited}, blob at {rev} is {found}"))
    return rows


def _r6_branch_checks() -> list[str]:
    """R6 has four branches and three of them fire nowhere in the live thread.

    A rule nobody can see fail has quietly stopped existing -- and the same is
    true of a branch. The revision-matching branch exists because a cascade
    happened once and must not happen again, so it has to be observably alive
    even while every current citation matches an unsuffixed key.
    """
    REF = "bd:doc"
    cases = [
        ("unsuffixed match",
         {REF: "sha256:aaaa1111"}, "sha256:aaaa1111", None, None),
        ("suffixed match",
         {REF: "sha256:bbbb2222", f"{REF}@r8": "sha256:aaaa1111"},
         "sha256:aaaa1111", None, "matches"),
        ("no revision matches",
         {REF: "sha256:bbbb2222", f"{REF}@r8": "sha256:cccc3333"},
         "sha256:aaaa1111", "has moved upstream", None),
        ("named refusal",
         {REF: "sha256:PLACEHOLDER"}, "sha256:aaaa1111",
         "declared UNKNOWN on purpose", None),
        ("unregistered ref",
         {}, "sha256:aaaa1111", "is in no manifest entry", None),
    ]
    failures = []
    for name, manifest, cited, want_err, want_warn in cases:
        doc = {"plan_ref": {"ref": REF, "hash": cited}}
        rep = Report(Path(f"<{name}>"))
        r6_hashes(doc, rep, manifest, None)
        got_err = " ".join(rep.errors)
        got_warn = " ".join(rep.warnings)
        if want_err and want_err not in got_err:
            failures.append(f"R6/{name}: expected error {want_err!r}, got {got_err!r}")
        if not want_err and rep.errors:
            failures.append(f"R6/{name}: unexpected error {got_err!r}")
        if want_warn and want_warn not in got_warn:
            failures.append(f"R6/{name}: expected warning {want_warn!r}, got {got_warn!r}")
    return failures


def _coverage_checks(expected: dict) -> list[str]:
    """Refuse to pass on nothing, and refuse to let an error rule go unfixtured.

    BD's ci.yml carries the same guard for a shell loop -- `if [ "$checked"
    -eq 0 ]; then echo "::error::no SEALED.sha256 found -- this job silently
    passed on nothing"` -- because a seal job that finds no seals is green.
    This one was green with every fixture and every thread deleted, and printed
    "0 fixtures, all pinned", which is vacuously true.

    The second half makes permanent the audit that found R0, R1, R9 and R10: any
    rule that can raise an error must have a negative fixture. Run by hand once,
    it is a one-off; run here, a new error rule cannot arrive unfixtured.
    """
    src = (ROOT / "validate.py").read_text()
    err_rules = set(re.findall(r'rep\.err\("(R\d+b?)"', src))
    fixture_rules = {n.split("-")[0].upper() for n in expected}

    out: list[str] = []
    for rule in sorted(err_rules - fixture_rules, key=lambda r: int(r.strip("Rb"))):
        out.append(f"{rule} can raise an error and has no negative fixture")

    # The manifest must stay sorted, and this is the check that keeps it sorted.
    # The prefix partition (am: keys to one side, bd: to the other) prevents a
    # SEMANTIC conflict -- neither side can overwrite the other's key. It does
    # not prevent a TEXTUAL one: in insertion order both sides append to the end
    # of the same JSON object and land on adjacent lines, which git conflicts on
    # even though the keys are disjoint. That it never happened was the writers
    # being serialised, not the design. Sorted, `am:*` and `bd:*` occupy disjoint
    # contiguous regions and an append by each touches a different part of the
    # file. Documentation keys (`_`-prefixed) stay first, in their own order.
    mf_path = ROOT / "hashes.json"
    if mf_path.exists():
        raw = json.loads(mf_path.read_text())
        refs = [k for k in raw if not k.startswith("_")]
        if refs != sorted(refs):
            first = next(i for i, (a, b) in enumerate(zip(refs, sorted(refs))) if a != b)
            out.append(f"hashes.json is not sorted (first divergence at index "
                       f"{first}: {refs[first]!r}). Sort the ref keys -- unsorted, "
                       "both sides append to the same last line and collide "
                       "textually even though the keys are disjoint.")
        doc_after_ref = [i for i, k in enumerate(raw) if k.startswith("_")
                         and any(not j.startswith("_") for j in list(raw)[:i])]
        if doc_after_ref:
            out.append("hashes.json has a `_`-prefixed documentation key after a "
                       "ref key; keep them at the top.")

    threads = list(ROOT.glob("threads/*/r*/ask_*.json"))
    valid = list((ROOT / "fixtures/valid").glob("*.json"))
    if not threads:
        out.append("no thread documents found -- this run verified nothing")
    if not valid:
        out.append("no positive fixtures found -- loosenings are unguarded")
    if not expected:
        out.append("expected.json is empty -- no failure identities are pinned")
    return out


def selftest() -> int:
    """A rule nobody can see fail is a rule that has quietly stopped existing.

    And a fixture that only asserts *a* failure can pass for the wrong reason.
    `expected.json` pins each fixture's failure identity: the rule alone is not
    enough once a rule has branches, and R6 has four.
    """
    global STRICT
    STRICT = True
    print(f"interpreter: {sys.executable}")

    exp_file = ROOT / "fixtures/invalid/expected.json"
    expected = {k: v for k, v in json.loads(exp_file.read_text()).items()
                if not k.startswith("_")} if exp_file.exists() else {}

    # Clause 3 applied to the enumeration itself, not only to the rules. BD
    # added the same meta-test and it rejected a 6-character fragment on its
    # first run. A fixture with no pinned fragment used to pass with a note;
    # that is a hole, since a new fixture would inherit the pass.
    MIN_FRAGMENT = 8
    fixture_names = {p.name for p in (ROOT / "fixtures/invalid").glob("*.json")
                     if p.name != "expected.json"}
    fixture_names |= {p.name for p in (ROOT / "fixtures/invalid").iterdir()
                      if p.is_dir()}
    meta: list[str] = []
    for name in sorted(fixture_names):
        frag = expected.get(name)
        if frag is None:
            meta.append(f"{name} pins no failure identity in expected.json")
        elif len(frag) < MIN_FRAGMENT:
            meta.append(f"{name} pins {frag!r}, {len(frag)} chars -- under "
                        f"{MIN_FRAGMENT}, so it may match a sibling branch")
    for name in sorted(expected):
        if name not in fixture_names:
            meta.append(f"expected.json names {name}, which is not a fixture")

    bad = 0
    coverage = _coverage_checks(expected)
    if coverage:
        bad += 1
        print("BAD   coverage:")
        for c in coverage:
            print(f"          {c}")
    else:
        print(f"ok    coverage  (every error rule has a fixture; "
              f"{len(list(ROOT.glob('threads/*/r*/ask_*.json')))} thread documents)")

    if meta:
        bad += 1
        print("BAD   expected.json meta-checks:")
        for m in meta:
            print(f"          {m}")
    else:
        print(f"ok    expected.json  ({len(fixture_names)} fixtures, all pinned, "
              f"all >= {MIN_FRAGMENT} chars)")

    branch_failures = _r6_branch_checks()
    if branch_failures:
        bad += 1
        print("BAD   R6 branch checks:")
        for f in branch_failures:
            print(f"          {f}")
    else:
        print("ok    R6 branch checks  (5 cases: unsuffixed, suffixed, none, "
              "placeholder, unregistered)")
    resolve_failures = _resolve_checks()
    if resolve_failures:
        bad += 1
        print("BAD   R6 resolve branch:")
        for f in resolve_failures:
            print(f"          {f}")
    else:
        print(f"ok    R6 resolve branch  ({len(RESOLVE_STATUSES)} statuses, each "
              "exercised against a temporary git repo; the real roots need "
              "--resolve and are NOT checked here)")

    _RATIONALES_SEEN.clear()
    mf = ROOT / "hashes.json"
    manifest = json.loads(mf.read_text()) if mf.exists() else None

    for p in sorted(ROOT.glob("threads/**/ask_*.json")) + \
            sorted(ROOT.glob("threads/**/kb_entry_for_*.md")) + \
            sorted(ROOT.glob("fixtures/valid/*.json")):
        rep = (validate_kb_entry if p.suffix == ".md" else validate)(p, manifest)
        if rep.ok:
            print(f"ok    {p.relative_to(ROOT)}")
        else:
            bad += 1
            print(f"BAD   {p.relative_to(ROOT)} should be valid:")
            for e in rep.errors:
                print(f"          {e}")

    for t in sorted(p for p in (ROOT / "threads").glob("*") if p.is_dir()):
        rep = r11_thread(t, manifest)
        if rep.ok:
            print(f"ok    threads/{t.name}/  (R11 cross-round)")
        else:
            bad += 1
            print(f"BAD   threads/{t.name}/ R11:")
            for e in rep.errors:
                print(f"          {e}")

    for t in sorted(p for p in (ROOT / "fixtures/invalid").glob("r11-*") if p.is_dir()):
        rep = r11_thread(t, manifest)
        hit = [e for e in rep.errors if e.startswith("R11")]
        frag = expected.get(t.name)
        identity = frag is None or any(frag in e for e in hit)
        if hit and len(hit) == len(rep.errors) and identity:
            print(f"ok    fixtures/invalid/{t.name}/ -> R11 fired, and only R11 "
                  f"({frag!r})" if frag else "")
        else:
            bad += 1
            print(f"BAD   fixtures/invalid/{t.name}/: "
                  f"{'R11 did not fire' if not hit else 'other rules fired too'}")
            for e in rep.errors:
                print(f"          {e}")

    md_fixtures = [p for p in sorted(ROOT.glob("fixtures/invalid/**/*.md"))
                   if p.name != "README.md"]
    json_fixtures = [p for p in sorted(ROOT.glob("fixtures/invalid/*.json"))
                     if p.name != "expected.json"]
    for p in json_fixtures + md_fixtures:
        # 'r5-circular....json' -> 'R5'; nested md fixtures take the rule from
        # the top-level directory under fixtures/invalid/.
        rel = p.relative_to(ROOT / "fixtures/invalid")
        want = rel.parts[0].split("-")[0].upper()
        rep = (validate_kb_entry if p.suffix == ".md" else validate)(p, manifest)
        hit = [e for e in rep.errors if e.startswith(want)]
        others = [e for e in rep.errors if not e.startswith(want)]
        frag = expected.get(rel.parts[0], expected.get(rel.name))
        identity = frag is None or any(frag in e for e in hit)
        if hit and not others and identity:
            tail = f" ({frag!r})" if frag else "  [no identity pinned]"
            print(f"ok    {p.relative_to(ROOT)} -> {want} fired, and only {want}{tail}")
        else:
            bad += 1
            reason = (f"{want} did not fire" if not hit
                      else f"{want} fired but so did {len(others)} other rule(s)"
                      if others
                      else f"{want} fired for the WRONG reason -- expected {frag!r}")
            print(f"BAD   {p.relative_to(ROOT)}: {reason}")
            for e in rep.errors:
                print(f"          {e}")

    print(f"\n{'selftest clean' if not bad else f'selftest: {bad} problem(s)'}")
    return 1 if bad else 0


def _resolve_checks() -> list[str]:
    """The resolve branch, against a git repository built three lines from here.

    The roots it exists for are two clones this repository does not have and CI
    will never have, so without this the whole mode is a script somebody has to
    remember to run -- the failure the `.github` directory was added to stop.
    Every status in RESOLVE_STATUSES must be produced by a case here: a new
    branch cannot arrive unexercised, which is `_coverage_checks` applied to a
    rule whose input is a filesystem rather than a document.
    """
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="bridge-resolve-"))
    am = tmp / "am"
    (am / "kb").mkdir(parents=True)

    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(am), "-c", "user.name=selftest",
             "-c", "user.email=selftest@example.invalid", *args],
            capture_output=True)

    if git("init", "-q").returncode != 0:
        return ["resolve: `git init` failed, so the rev branches were not "
                "exercised. That is a skipped rule, not a passed one."]

    (am / "kb/thing.md").write_text("v1")
    git("add", "-A")
    git("commit", "-qm", "one")
    rev1 = git("rev-parse", "--short", "HEAD").stdout.decode().strip()
    (am / "kb/thing.md").write_text("v2")
    (am / "kb/later.md").write_text("new")
    git("add", "-A")
    git("commit", "-qm", "two")
    (am / "kb/dir").mkdir()
    roots = {"am": am}  # `bd` deliberately absent: that is the no_root case.

    h1, h2 = _sha16(b"v1"), _sha16(b"v2")
    manifest = {
        "_subject_of": {"am:kb/proxy.md": "am:kb/thing.md"},
        "am:kb/thing.md": h1, "am:kb/thing.md@r2": h2,  # a later rev matches
        "am:kb/proxy.md": h2,                           # resolves via subject
        "am:kb/later.md": "sha256:2222222222222222",    # exists, matches none
        "am:kb/gone.md": "sha256:0000000000000000",     # path not there at all
        "am:kb/dir": "sha256:1111111111111111",
        "bd:anything.py": "sha256:3333333333333333",
    }
    want_manifest = {
        "am:kb/thing.md": "ok_worktree", "am:kb/proxy.md": "ok_worktree",
        "am:kb/later.md": "advanced", "am:kb/gone.md": "absent",
        "am:kb/dir": "no_recipe", "bd:anything.py": "no_root",
    }

    doc = [
        {"ref": "am:kb/thing.md", "hash": h1, "rev": rev1},        # ok_rev
        {"ref": "am:kb/thing.md", "hash": h2, "rev": rev1},        # rev_mismatch
        {"ref": "am:kb/thing.md", "hash": h1, "rev": "dead1beef"},  # rev_missing
        {"ref": "am:kb/later.md", "hash": _sha16(b"new"), "rev": rev1},  # rev_absent
        {"ref": "am:kb/thing.md", "hash": h1},                     # no_rev
        {"ref": "bd:anything.py", "hash": h1, "rev": rev1},        # no_root
        # The three cases the first real run produced as false defects, before
        # they were understood as the resolver's own. Each one is cheaper to
        # keep than to rediscover: they cost an hour of triage against real
        # documents that turned out to be fine.
        {"ref": "am:kb/thing.md@r2", "hash": h1, "rev": rev1},     # key suffix
        {"ref": "am:kb/proxy.md", "hash": h1, "rev": rev1},        # redirected
        {"ref": "am:kb", "hash": h1, "rev": rev1},                 # a tree
    ]
    docfile = tmp / "doc.json"
    docfile.write_text(json.dumps(doc))
    broken = tmp / "broken.json"
    broken.write_text("{not json")
    want_cites = {
        ("am:kb/thing.md", h1, rev1): "ok_rev",
        ("am:kb/thing.md", h2, rev1): "rev_mismatch",
        ("am:kb/thing.md", h1, "dead1beef"): "rev_missing",
        ("am:kb/later.md", _sha16(b"new"), rev1): "rev_absent",
        ("am:kb/thing.md", h1, ""): "no_rev",
        ("bd:anything.py", h1, rev1): "no_root",
        ("am:kb/thing.md@r2", h1, rev1): "ok_rev",
        ("am:kb/proxy.md", h1, rev1): "ok_rev",
        ("am:kb", h1, rev1): "no_recipe",
    }

    failures, seen = [], set()
    manifest_rows = resolve_manifest(manifest, roots)
    got_manifest = {ref: status for ref, status, _ in manifest_rows}
    for ref, want in want_manifest.items():
        seen.add(want)
        if got_manifest.get(ref) != want:
            failures.append(f"resolve/manifest {ref}: expected {want}, "
                            f"got {got_manifest.get(ref)}")
    subject_row = [d for r, _, d in manifest_rows if r == "am:kb/proxy.md"]
    if not subject_row or "_subject_of" not in subject_row[0]:
        failures.append("resolve/manifest: a redirected key does not say so in "
                        "its detail, so the reader cannot tell which file was read")

    rows = resolve_citations([docfile, broken], roots, manifest["_subject_of"])
    if not any(st == "unread" and "broken.json" in what for what, st, _ in rows):
        failures.append("resolve/citation: an unparseable document contributed "
                        "nothing and the run did not say so")
    seen.add("unread")
    got_cites = {}
    for seen_str, status, _ in rows:
        got_cites[seen_str.split("  [")[0]] = status
    for (ref, cited, rev), want in want_cites.items():
        seen.add(want)
        key = f"{ref} @{rev or '-'} cites {cited}"
        if got_cites.get(key) != want:
            failures.append(f"resolve/citation {key}: expected {want}, "
                            f"got {got_cites.get(key)}")

    unexercised = set(RESOLVE_STATUSES) - seen
    if unexercised:
        failures.append(f"resolve: {', '.join(sorted(unexercised))} can be "
                        "reported and no case produces it")
    shutil.rmtree(tmp, ignore_errors=True)
    return failures


def run_resolve(roots: dict[str, Path]) -> int:
    """`--resolve`. Opt-in, and it says what it did not check.

    It cannot run in CI: resolving `am:` and `bd:` needs the two agent
    repositories, and pointing CI at their default branches would be worse than
    not running it -- this thread's AM half lives on a worktree branch that is
    on neither `main` nor `version2`, so a green tick from `main` would mean
    'nine refs are missing' or 'nine refs are fine' depending on nothing.
    """
    manifest_path = ROOT / "hashes.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    docs = sorted(ROOT.glob("threads/**/ask_*.json")) + \
        sorted(ROOT.glob("threads/**/kb_entry_for_*.md"))

    print(f"resolve: bridge={ROOT}")
    for side in ("am", "bd"):
        print(f"         {side}={roots.get(side) or '(not configured -- not checked)'}")

    subject = manifest.get("_subject_of", {})
    rows = ([("manifest", *r) for r in resolve_manifest(manifest, roots)] +
            [("citation", *r) for r in resolve_citations(docs, roots, subject)])
    counts: dict[str, int] = {}
    for _kind, _what, status, _detail in rows:
        counts[status] = counts.get(status, 0) + 1

    for kind, what, status, detail in rows:
        # `_subject_of` rows print even when they pass. A declared exception
        # that goes quiet is how the prose note it replaces got forgotten.
        if status.startswith("ok_") and "_subject_of" not in f"{what}{detail}":
            continue
        mark = "ERROR   " if status in RESOLVE_ERRORS else \
               "warning " if status in RESOLVE_WARNINGS else "        "
        print(f"    {mark} {status:<12} {kind} {what}\n                          {detail}")

    print()
    for status, n in sorted(counts.items()):
        print(f"    {n:>3}  {status:<12} {RESOLVE_STATUSES[status]}")

    checked = sum(n for s, n in counts.items() if s not in ("no_root", "no_rev"))
    errors = sum(n for s, n in counts.items() if s in RESOLVE_ERRORS)
    if not checked:
        print("\nresolve: nothing was resolved. Configure --root am=PATH "
              "--root bd=PATH (or BRIDGE_ROOT_AM / BRIDGE_ROOT_BD); a run that "
              "checks nothing is not a run that passed.")
        return 1
    print(f"\nresolve: {checked} resolved, {errors} unresolvable")
    return 1 if errors else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--all", action="store_true",
                    help="every document under threads/ and fixtures/")
    ap.add_argument("--selftest", action="store_true",
                    help="threads/ must pass and every fixtures/invalid/ file "
                         "must fail with the rule its filename names. This is "
                         "the CI entry point: exit 0 means the rules still bite.")
    ap.add_argument("--resolve", action="store_true",
                    help="R6's resolve branch: open every registered revision "
                         "and every cited `rev` in the checkout that owns it. "
                         "Needs --root; not in CI, which has neither clone.")
    ap.add_argument("--root", action="append", default=[], metavar="side=PATH",
                    help="am=PATH or bd=PATH, repeatable. Also read from "
                         "BRIDGE_ROOT_AM / BRIDGE_ROOT_BD. Never defaulted to a "
                         "sibling directory: the answer must not depend on "
                         "where somebody cloned.")
    args = ap.parse_args()

    if args.resolve:
        roots: dict[str, Path] = {}
        for side in ("am", "bd"):
            env = os.environ.get(f"BRIDGE_ROOT_{side.upper()}")
            if env:
                roots[side] = Path(env).expanduser().resolve()
        for spec in args.root:
            side, _, where = spec.partition("=")
            if side not in ("am", "bd") or not where:
                ap.error(f"--root {spec!r}: expected am=PATH or bd=PATH")
            roots[side] = Path(where).expanduser().resolve()
        for side, where in roots.items():
            if not where.is_dir():
                ap.error(f"--root {side}={where}: not a directory")
        return run_resolve(roots)

    paths = list(args.paths)
    if args.all or not paths:
        paths = sorted(ROOT.glob("threads/**/ask_*.json")) + \
                sorted(ROOT.glob("threads/**/kb_entry_for_*.md")) + \
                sorted(ROOT.glob("fixtures/valid/*.json")) + \
                sorted(ROOT.glob("fixtures/invalid/*.json"))

    if args.selftest:
        return selftest()

    mf = ROOT / "hashes.json"
    manifest = json.loads(mf.read_text()) if mf.exists() else None

    failed = 0
    for p in paths:
        rep = (validate_kb_entry if p.suffix == ".md" else validate)(p, manifest)
        p = p.resolve()
        rel = p.relative_to(ROOT) if p.is_relative_to(ROOT) else p
        mark = "PASS" if rep.ok else "FAIL"
        print(f"\n{mark}  {rel}")
        for e in rep.errors:
            print(f"    ERROR    {e}")
        for w in rep.warnings:
            print(f"    warning  {w}")
        if not rep.ok:
            failed += 1

    print(f"\n{len(paths)} document(s), {failed} with errors")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
