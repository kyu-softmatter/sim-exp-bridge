#!/usr/bin/env python3
"""Validate a bridge document. Seven rules; two of them are not shape rules.

    python3 validate.py threads/trap-stiffness-recovery/r1/ask_simulation.json
    python3 validate.py --all

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
import re
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


class Report:
    def __init__(self, path: Path):
        self.path = path
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, rule: str, msg: str) -> None:
        self.errors.append(f"{rule}  {msg}")

    def warn(self, rule: str, msg: str) -> None:
        self.warnings.append(f"{rule}  {msg}")

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
            rep.warn("R4", "unknowns are declared only through `status: draft`. "
                           "Prefer `assumptions_resolved: false`, which survives a "
                           "later status change.")
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
                           f"number ({own[0]}) -- round-trip, soft, so allowed. "
                           "Confirm it is declared in gaps[].")


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
                                   f"{sorted(allowed)} via T1. Ignored -- `evidence` "
                                   "is authoritative. Drop `tier` rather than "
                                   "correcting it.")
            for k, v in node.items():
                walk(v, f"{where}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{where}[{i}]")

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
    """
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
        known = manifest.get(ref)
        if known is None:
            rep.warn("R6", f"{ref} is not in hashes.json -- cannot check drift")
        elif known != h:
            rep.err("R6", f"{ref} has moved upstream: document cites {h}, "
                          f"manifest has {known}. Every requirement resting on "
                          "it is stale. Supersede the import, do not edit it.")


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
            rep.warn("R11", f"{symbol} is derived independently on both sides "
                            f"({detail}). Not a defect -- this is the round-trip "
                            "check, and agreement here is evidence.")
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
    r6_hashes(doc, rep, manifest, path)
    r7_confirmed_by(doc, rep)
    return rep


def selftest() -> int:
    """A rule nobody can see fail is a rule that has quietly stopped existing."""
    global STRICT
    STRICT = True
    print(f"interpreter: {sys.executable}")
    mf = ROOT / "hashes.json"
    manifest = json.loads(mf.read_text()) if mf.exists() else None
    bad = 0

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
        if hit and len(hit) == len(rep.errors):
            print(f"ok    fixtures/invalid/{t.name}/ -> R11 fired, and only R11")
        else:
            bad += 1
            print(f"BAD   fixtures/invalid/{t.name}/: "
                  f"{'R11 did not fire' if not hit else 'other rules fired too'}")
            for e in rep.errors:
                print(f"          {e}")

    for p in sorted(ROOT.glob("fixtures/invalid/*.json")):
        want = p.name.split("-")[0].upper()          # 'r5-circular...' -> 'R5'
        rep = validate(p, manifest)
        hit = [e for e in rep.errors if e.startswith(want)]
        others = [e for e in rep.errors if not e.startswith(want)]
        if hit and not others:
            print(f"ok    {p.relative_to(ROOT)} -> {want} fired, and only {want}")
        else:
            bad += 1
            reason = (f"{want} did not fire" if not hit
                      else f"{want} fired but so did {len(others)} other rule(s)")
            print(f"BAD   {p.relative_to(ROOT)}: {reason}")
            for e in rep.errors:
                print(f"          {e}")

    print(f"\n{'selftest clean' if not bad else f'selftest: {bad} problem(s)'}")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--all", action="store_true",
                    help="every document under threads/ and fixtures/")
    ap.add_argument("--selftest", action="store_true",
                    help="threads/ must pass and every fixtures/invalid/ file "
                         "must fail with the rule its filename names. This is "
                         "the CI entry point: exit 0 means the rules still bite.")
    args = ap.parse_args()

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
