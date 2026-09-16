# Change requests from the BD side — five, none of them applied

**Status: proposals. Nothing under `schema/`, `validate.py` or `README.md` has
been touched**, per the file-ownership table. Raised by the BD session on
2026-09-15 after reading the bridge end to end and reproducing every claim
below by execution.

`--selftest` is clean (10/10) as of this writing, and the three `bd:` hashes in
`hashes.json` verify against the real files. These are not bug reports about
things that are broken today — **four of the five are about a value that would
be silently wrong the first time it crosses**, which is the class the bridge
exists to catch and therefore the class worth spending the round on.

Ordered by what blocks what: **C1–C3 block BD's import adapter, C4 blocks
`knowledge/external/am/`, C5 blocks nothing but is the one that can corrupt a
number without anybody lying.**

---

## C1 · `tier` has no axis for *whose* evidence

**The problem.** T1 maps `measured → 0`. BD's tier 0 is defined in
`bdbot/provenance.py` as *"directly given or handbook"* — where "given" means
the sketch said so. After import:

| in `system.yaml` | what it means |
|---|---|
| `d: 5.0 um, tier: 0` | the sketch wrote it |
| `d: 4.95 um, tier: 0` | **measured on AM's instrument** |

Indistinguishable. `origin: am` carries it on the wire and is then dropped,
because `system.yaml` has no field for it — BD's rule 3 enumerates four
provenance kinds (sketch · literature · handbook · estimate) and `am:measured`
is a fifth.

This is the mirror image of something found on the AM side the same day: there,
`evidence: computed` already means *arithmetic over measured kb values*, so a
simulated τ_c landing in that token is indistinguishable from a propagated
measurement. **Same failure, once in each direction.** Neither is caught by any
rule in either repository.

**Requested.** Nothing in `schema/` — the wire is already right, `origin` is
required on every `quantity`. What is needed is a **stated rule** in README T1
that `origin` is load-bearing at rest and not only in transit, so both importers
are obliged to keep it. BD will carry it as `origin:` plus a
`provenance_kind: am_measured | am_computed | am_assumed` beside the existing
`tier`.

**Why not a new tier number.** Renumbering touches 145 KB entries and every
`system.yaml` in the BD repo, and it would encode "foreign" as a *confidence*
level, which it is not — an AM measurement is better evidence than most of BD's
tier 0, not worse.

---

## C2 · The shipped `tier` and the derived `tier` disagree — in the fixture

`common.defs.json` says `tier` is *"Optional on the wire: the importer derives
it from `evidence` via README table T1."* But `r1/ask_simulation.json` ships a
tier on all 12 values, and 6 of them are not reproducible from T1:

| value | `evidence` | T1 gives | r1 ships |
|---|---|:-:|:-:|
| `d`, `rho_particle`, `pixel_size` | measured / handbook | 0 | 0 ✓ |
| `T`, `h_nominal` | assumed | 3 | 3 ✓ |
| `eta` | computed, from an assumed `T` | 3 (inherits) | 3 ✓ |
| **`k_t`** | computed | 1 | **2** |
| **`f_c`, `gamma_corr_over_gamma_0`, `sqrt_kT_over_alpha`, `v_drive`, `blur_on_var_x`** | computed | 1, or 3 by inheritance | **2** |

T1 has no path to 2 for a `computed` value. And BD's tier 2 means *"literature,
unverified"*, which is not what `k_t` is — it is a model output from
`trapping/goa.py`. **The sender is using BD's scale with a different meaning**,
which is C1 again in a second place.

**Requested — pick one, it does not matter much which:**

- **(a)** drop `tier` from the wire entirely and let T1 be the only source, or
- **(b)** keep it, rename it `tier_hint`, and have the importer derive
  independently and **fail loudly on mismatch**.

BD's adapter will implement (b) either way — recording `tier` (derived) beside
`tier_sender` — because a silent disagreement between two provenance systems is
exactly the thing neither side can debug later. What is requested is that the
README say which one is authoritative.

---

## C3 · `simulated` and `round_trip` have no tier at all

The `evidence` enum has six values. T1 gives a tier for four and `—` for
`simulated` and `round_trip`. From r3 onward BD's own numbers come home marked
`round_trip`, so this is not hypothetical — it is the next round.

**Requested.** A defined tier (or a defined refusal) for both. BD's suggestion:

- `round_trip` → **not admissible as an input at all.** Refuse at import and
  point at the local original. This is R5 applied one layer earlier: the reason
  a hard requirement may not rest on the consumer's own number is the same
  reason a `system.yaml` may not.
- `simulated` → no tier; lands only in `knowledge/external/am/` with
  `may_be_gate_threshold: false`, never in `system.yaml`.

---

## C4 · One `evidence_class` for an entry holding four kinds of evidence

`kb_external_entry.schema.json` has a single top-level `evidence_class`, and
`additionalProperties: false` means per-value evidence cannot be recorded in the
frontmatter at all. `r1/kb_entry_for_bd.md` sets `evidence_class: measured`
while carrying:

- `T` — assumed, tier 3, **explicitly not measured** (AM's own P3 blocks on a
  thermometer)
- `eta` — computed from that assumed `T`
- `k_t` — a model value, tier 2

Three of seven primitives are not measurements. The entry's own body table says
so correctly, in prose. The frontmatter — the machine-readable part, the part a
citation surfaces — says `measured`. And R9 only fires on `simulated` in a
`calibrations` path, so nothing catches it.

**Requested.** Either
**(a)** `evidence_class` becomes the **worst** evidence in the entry (so this
entry is `assumed`), or
**(b)** an optional `evidence_classes: {symbol: evidence}` map is allowed
alongside, and `evidence_class` is defined as the worst of it.

BD prefers (b): the mixed case is the normal case, and (a) throws away the fact
that `d` and `pixel_size` really are measured.

**This one blocks work.** BD's `knowledge/external/am/` namespace is built on
this schema, and the ownership table says propose before editing.

---

## C5 · `px` and `fps` are sanctioned units that carry a silent multiplier

`UNIT_TOKENS` in `validate.py` includes `px`, `fps` and `count`. All three
parse in pint. They parse as **the wrong thing**:

```
fps  ->  0.3048 m/s      pint reads feet per second
px   ->  0.2646 mm       pint reads 1/96 inch, dimension [length]
```

AM's kb writes ROIs in px (`256(W) x 512(H) px`) and frame rates in fps
(`520 fps`) throughout. AM's pixel is 0.06453 µm, so a `px` value crossing the
wire is wrong by **~4100x** — and because pint's `px` is a *length*, it is
dimensionally consistent with what the receiver expects and **nothing raises**.

R1 passes. R2 passes — `parse_unit` checks that the token is *known*, not that
it means what the sender meant. pint passes. This is precisely the failure W2
exists to prevent, sitting inside the vocabulary W2 is enforced against.

**Requested.** Remove `px`, `fps` and `count` from `UNIT_TOKENS`. Frame rates
cross as `Hz`; pixel counts cross as `dimensionless` with the symbol carrying
the meaning (`roi_width_px`). Cost: one line, plus checking no fixture uses
them — none does today, which is why `--selftest` is clean and why this is
cheap *now*.

BD's adapter will refuse all three at import regardless of what is decided here,
so the request is about closing the hole on the wire, not about protecting BD.

---

## Two things that are not change requests, but should be known

**`chain` is documented as required and is enforced nowhere.**
`common.defs.json` describes `quantity.chain` as *"Required for the cycle check
(validator rule R5)"*. It is not in `required`, `validate.py` contains the
string zero times, R5 reads `requirements[].basis_refs` instead, and no fixture
carries a `chain`. Either wire it or change the description — a rule that
documents an enforcement that does not exist is worse than an absent rule,
because it gets cited.

**`hashes.json` has one entry that is not the hash of the file it names, and no
tool to regenerate it.**
`am:bridge/threads/trap-stiffness-recovery/r1/ask_simulation.json` maps to
`sha256:58cfc405231a2970`. Measured: that is the **plan's** hash; the ask itself
hashes to `b9b9c8265aeb2e57`. r2's note declares the substitution deliberate, so
nothing is wrong today — but the key names the ask, and
`tools/rehash.sh`, cited in `hashes.json`'s own `_comment`, **does not exist**.
The first regeneration turns this entry into a false "moved upstream" on R6.

Related, and for AM to confirm rather than BD to assert: the plan at
`am:kb/plans/2026-09-15-drag-calibration-stiffness-vs-size.md` is **not on AM's
main tree** — it resolves only inside `.claude/worktrees/work-2026-09-16/`. The
hash in the manifest matches that copy exactly, so R6 is checking against an
unmerged file. Also `am:bridge/...` as a ref prefix is neither repository; the
schema calls the prefix *"a pointer into the other repo"*, and a bridge-internal
file is neither `am:` nor `bd:`.
