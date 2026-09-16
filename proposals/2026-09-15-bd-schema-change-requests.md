# Change requests from the BD side — seven, none of them applied

**Status: proposals. Nothing under `schema/`, `validate.py` or `README.md` has
been touched**, per the file-ownership table.

**Revision 2, after `c288df6`.** The first revision of this file was written
before the bridge grew `corrects[]`, `rev` on a `ref`, and optional
`question`/`date`. Those changes closed one of the two observations at the end
and are noted below; **all five original requests are still open**, and r4 has
since given three of them a worked example rather than a hypothetical one.

Verified by execution at the time of writing: `validate.py --selftest` is clean
(12/12, with `jsonschema` present so R1 actually runs — note the `simulation_bot`
env does **not** have it, so a selftest run from there silently skips R1; use
`/opt/homebrew/Caskroom/miniconda/base/bin/python3`). All `bd:` hashes in
`hashes.json` verify against their files at the `rev` each one names.

Ordered by what blocks what. **C1–C3 block BD's import adapter, C4 blocks
`knowledge/external/am/`, C5 and C6 block nothing but are each a way for a
value to be silently wrong.**

---

## C1 · `tier` has no axis for *whose* evidence

**The problem.** T1 maps `measured → 0`. BD's tier 0 is defined in
`bdbot/provenance.py` as *"directly given or handbook"* — where "given" means the
sketch said so. After import:

| in `system.yaml` | what it means |
|---|---|
| `d: 5.0 um, tier: 0` | the sketch wrote it |
| `d: 4.95 um, tier: 0` | **measured on AM's instrument** |

Indistinguishable. `origin: am` carries it on the wire and is then dropped,
because `system.yaml` has no field for it — BD's rule 3 enumerates four
provenance kinds (sketch · literature · handbook · estimate) and `am:measured`
is a fifth.

This is the mirror image of something on the AM side: there, `evidence: computed`
already means *arithmetic over measured kb values*, so a simulated τ_c landing in
that token is indistinguishable from a propagated measurement. **Same failure,
once in each direction**, and no rule in either repository catches it.

**Requested.** Nothing in `schema/` — the wire is already right, `origin` is
required on every `quantity`. What is needed is a **stated rule in T1** that
`origin` is load-bearing *at rest* and not only in transit, so both importers are
obliged to keep it. BD will carry `origin:` plus
`provenance_kind: am_measured | am_computed | am_assumed` beside the existing
`tier`.

**Why not a new tier number.** Renumbering touches 145 KB entries and every
`system.yaml` in the BD repo, and it would encode "foreign" as a *confidence*
level, which it is not — an AM measurement is better evidence than most of BD's
tier 0, not worse.

## C2 · The shipped `tier` and the derived `tier` disagree — in the fixture

`common.defs.json` says `tier` is *"Optional on the wire: the importer derives it
from `evidence` via README table T1."* r1 ships a tier on all 12 values, and 6 of
them are not reproducible from T1:

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

**Requested — either is fine, but say which:** drop `tier` from the wire, or
rename it `tier_hint`. BD's adapter will derive independently and **fail loudly
on mismatch** either way; what is requested is that the README say which is
authoritative.

## C3 · `simulated` and `round_trip` have no tier at all

T1 gives `—` for both. From r3 onward BD's own numbers come home, so this is the
present round, not a future one.

**Requested.** BD's suggestion: `round_trip` → **not admissible as an input at
all**; refuse at import and point at the local original. That is R5 applied one
layer earlier — the reason a hard requirement may not rest on the consumer's own
number is the reason a `system.yaml` may not. `simulated` → no tier; lands only
in `knowledge/external/am/` with `may_be_gate_threshold: false`, never in
`system.yaml`.

## C4 · One `evidence_class` for an entry holding four kinds of evidence

`kb_external_entry.schema.json` has a single top-level `evidence_class`, and
`additionalProperties: false` means per-value evidence cannot be recorded at all.
`r1/kb_entry_for_bd.md` sets `evidence_class: measured` while carrying `T`
(assumed, tier 3, explicitly **not** measured — AM's own P3 blocks on a
thermometer), `eta` (computed from that assumed `T`) and `k_t` (a model value).
Three of seven primitives are not measurements. The body table says so correctly,
in prose; the frontmatter — the machine-readable part, the part a citation
surfaces — says `measured`. R9 only fires on `simulated` in a `calibrations`
path.

**Requested.** Either `evidence_class` becomes the **worst** evidence in the
entry, or an optional `evidence_classes: {symbol: evidence}` map is allowed
alongside and `evidence_class` is defined as the worst of it. BD prefers the
second: the mixed case is the normal case, and the first throws away the fact
that `d` and `pixel_size` really are measured.

**This one blocks work** — BD's `knowledge/external/am/` namespace is built on
this schema.

## C5 · `px` and `fps` are sanctioned units that carry a silent multiplier

`UNIT_TOKENS` includes `px`, `fps` and `count`. All three parse in pint. They
parse as **the wrong thing**:

```
fps  ->  0.3048 m/s      pint reads feet per second
px   ->  0.2646 mm       pint reads 1/96 inch, dimension [length]
```

AM's kb writes ROIs in px (`256(W) x 512(H) px`) and frame rates in fps
(`520 fps`) throughout. AM's pixel is 0.06453 µm, so a `px` value crossing the
wire is wrong by **~4100×** — and because pint's `px` is a *length*, it is
dimensionally consistent with what the receiver expects and **nothing raises**.

R1 passes. R2 passes — `parse_unit` checks that the token is *known*, not that it
means what the sender meant. pint passes. This is exactly the failure W2 exists to
prevent, sitting inside the vocabulary W2 is enforced against.

**Requested.** Remove `px`, `fps` and `count`. Frame rates cross as `Hz`; pixel
counts cross as `dimensionless` with the symbol carrying the meaning
(`roi_width_px`). One line, and no fixture uses them today — which is why the
selftest is clean and why this is cheap **now**.

---

## New in revision 2 — raised by writing r4

## C6 · A correcting document cannot also raise a new `unknown` assumption

R4 forces `status: draft` whenever any assumption is `unknown`. `corrects[]` and
`status: supersedes_prior` were added precisely so a correction **does not wait**.
The two collide: r4 needed to declare a newly-discovered unknown — *neither side
has said which Lorentzian estimator it uses*, and that choice is measured to be
worth up to +7.9 %, more than most of the physics differences in this thread —
and could not, without demoting the correction to a draft.

What BD did instead, rather than weaken the content: moved the item into
`findings[]` with `resolution_owner: human`. It is equally visible there. But it
is now filed as a disagreement rather than as an undeclared assumption, and R4
exists because those are different things.

**Requested.** Carve `supersedes_prior` out of R4, the way parity was carved out:
an `unknown` in a correcting document keeps the correction valid and flags the
unknown. Or add `status: supersedes_prior_draft` if the distinction is worth
keeping. Either is fine; the current state quietly pushes content out of
`assumptions[]`, which is the one block the README calls *"the ONLY block that is
not a number."*

## C7 · `chain` is documented as required and is enforced nowhere

`common.defs.json` describes `quantity.chain` as *"Required for the cycle check
(validator rule R5)."* It is not in `required`, `validate.py` contains the string
**zero** times, R5 reads `requirements[].basis_refs` instead, and no fixture
carries a `chain`.

**Requested.** Wire it or change the description. A rule that documents an
enforcement which does not exist is worse than an absent rule, because it gets
cited. (This was a non-request in revision 1; r4 is the first document whose
`derived_from` chain would actually have been checkable, so it is promoted.)

---

## Resolved since revision 1

- **`rev` on a `ref`** — raised as an observation, added in `3ddcf32`. The
  triggering case was this thread's own plan file: `58cfc405` on `main`,
  `514da4a0` on `worktree-work-2026-09-16`, **absent from `version2`**. One ref,
  three answers. Confirmed by the operator that the worktree is where work
  continues and moves to `main` when it works, so the ambiguity was live and not
  historical.
- **`question` / `date` on an imported entry** — AM proposed, accepted in
  `3ddcf32`.
- **`hashes.json` plan drift** — handled by the `@r<N>` key convention rather than
  by overwriting. Note that `tools/rehash.sh`, cited in the file's own
  `_comment`, **still does not exist**; the `am:bridge/.../r1/ask_simulation.json`
  key still holds the *plan's* hash rather than the ask's (deliberate, per r2's
  note), so the first regeneration would turn it into a false "moved upstream".
