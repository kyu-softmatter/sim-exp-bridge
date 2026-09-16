---
# Lands at  bd:knowledge/external/am/trap-stiffness-recovery.r1.md
# The path carries the foreign origin, because BD's own entries are cited by
# path and a frontmatter field alone would not show at the citation site.
id: trap-stiffness-recovery.r1
origin: am
source_ref: "am:kb/plans/2026-09-15-drag-calibration-stiffness-vs-size.md"
source_hash: "sha256:58cfc405231a2970"
evidence_class: measured
may_be_gate_threshold: false
derived_from: []
thread: trap-stiffness-recovery/r1
imported: 2026-09-15
supersedes: null
superseded_by: null
corrected_by: null
confirmed_by: null
---

# Instrument primitives for the drag-calibration height ladder (imported from AM)

**This entry originates outside this repository.** Nothing in it was measured,
derived or chosen here. The numbers are a mechanical copy of the fields in
`ask_simulation.json` — not a summary of them, because a summary would make this
file a new origination point, which rule 3 forbids.

`may_be_gate_threshold: false`. These values may set a target or motivate a
design; a check that *clears* against them would emit a margin that looks like
this repository's own.

## Primitives, at the tier the sender's `evidence` maps to

| symbol | value | tier | why that tier |
|---|---|:-:|---|
| `d` | 4.95 µm | 0 | `measured` — lot mean, `data/particles.yaml` |
| `rho_particle` | 1.05 g/cm³ | 0 | `handbook` — polystyrene |
| `T` | 293.15 K | **3** | `assumed`. **Not measured.** AM's precondition P3 blocks on a thermometer. Inheriting this as tier 0 is precisely what `provenance.py`'s header warns about; it is worth 2.4 %/K on `eta`. |
| `eta` | 1.0016e-3 Pa·s | **3** | `computed` from the assumed `T`, so it inherits |
| `k_t` | 3.5054 pN/µm | 2 | `computed` from a model (`trapping/goa.py`), unverified against measurement |
| `h_nominal` | 8.0 µm | 3 | piezo reading, **not** an absolute height — the absolute height is the unknown |
| `pixel_size` | 0.06453 µm | 0 | `measured`, two length standards agreeing to 0.24 % |

Units are as sent. Nondimensionalisation happens **at use time** in this
repository's own pipeline, not at import.

## Assumptions declared by the sender

3D chamber, x-only drive and measurement · Faxén parallel first order
`s = 9a/(16h)` · Newtonian water at 20 °C · 0.45 ms exposure with a
`2Dt_exp/3` blur term and `epsilon ≈ 10 nm` localisation noise · one isolated
bead per ROI · `x_eq ≤ 0.15a` · overdamped · z drift held under ~0.3 µm per rung.

**These are the part that no imported number could have told us.** Three of them
name things this repository has no representation for at all: the wall, the
detector, and the drift.

## Envelope

`f_s ≤ 520 Hz` hard · `t_exp ≤ 0.576 ms` · `T_obs = 5 s` per rung ·
`h ∈ [3.0, 10.0] µm` · `epsilon ≈ 10 nm` pending measurement.
