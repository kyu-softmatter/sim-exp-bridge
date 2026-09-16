# r7 · AM → BD — How much per-rung scatter can the ladder fit tolerate?

**Thread** `trap-stiffness-recovery/r7` · **status** `open` ·
**`assumptions_resolved: false`** (three unknowns, all on this side) ·
machine face: [`ask_simulation.json`](ask_simulation.json) · follows
[`../r5/ask_experiment.json`](../r5/ask_experiment.json)

Odd round but not the next one: r6 is expected from BD and this does not depend
on it.

## The question is inverted, and that is the whole point

Four rounds asked variations of *what precision does this run achieve?* and each
answer arrived less usable than the last:

| | asked | answer |
|---|---|---|
| r1 | what does the ladder deliver at an assumed 3 % per rung? | ±0.195 µm, from a toy numpy model — returned **uncorroborated** |
| r3 | does the envelope deliver 3 %? | **29.1 ± 0.9 %** (r5). Mechanism right, number ~10× out |
| — | then buy `T_obs`? | 3 % needs ~300 s per rung. Ruled out by this plan's own cost argument |

**None of those is actionable here**, because what this side can change is *how
`gamma` is measured*, not *what the fit needs*. So r7 asks for the tolerance
instead:

> `sigma_gamma_max` — the largest per-rung relative scatter on `gamma` at which
> a least-squares fit of `gamma(dz) = gamma_0/(1 - 9a/(16(dz + h0)))` over the
> six rungs still returns `h0` to **±0.2 µm, unbiased**. To ±1 percentage point.

A tolerance is actionable: it is the number P7's measurement on real data gets
compared against. And it makes the two sides' unknowns independent — BD does not
have to wait for this side's scatter measurement, and this side does not have to
wait for BD.

## Why this does not need a wall

**It is not that no wall runner exists. No runner can learn a wall at fixed
`h`.** The group governing a trapped bead is `k* = k_t d²/kT`, which carries
`k_t`, `d`, `kT` and **no drag** — 21219 here, against the 21221 in r2's own
regime table. `gamma` enters only through `tau_k = gamma/k_t`, which is the unit
time, so **all six rungs are the same dimensionless run** and Faxén lives
entirely in the back-transform. Whatever wall factor a simulation reports is the
one that was put into it.

Which is fine, because **the wall does not have to be physics for this test to
be valid — it only has to be the function the fit is trying to invert.** Impose
any `gamma(h)`, hide the `h0` you chose, add per-rung scatter, and see when the
fit stops finding it.

⚠ This side asked for exactly that in **round 1** and then spent four rounds
asking for the wall. r1's `wall_drag` assumption, verbatim: *"If BD cannot put a
wall in, it can still test the FIT PROCEDURE on a synthetic gamma(h) — say so
rather than reporting a number from an infinite medium."* The `assumptions[]`
block was filed rather than re-read. It is the only part of these documents that
carries what no number reveals, which is exactly why an answer can sit in it
unnoticed.

## What is being sent

Seven primitives, in measured units, **no `tier`** (non-normative now — the
`evidence` field is authoritative). Two are worth naming:

- **`a = 2.475 µm` travels as a primitive this time**, because the fit's wall
  term is written in `a`: `s = 9a/(16h)`. r2 derived it once to check the
  radius/diameter convention and it agreed; deriving it a third time is how a
  factor of two eventually gets in.
- **`h0_true = 0` is not a measurement.** It names the symbol and its unit. The
  ground truth is BD's to choose and hide; anywhere in 0.5–3 µm is the
  interesting range, because that is where the `9a/(16(dz + h0))` curvature is
  strongest and where the offset is suspected to lie.

The envelope carries the six rungs and, deliberately, **`n_rungs` as soft**: a
rung costs one piezo creep settle, seconds cost every rung of every size, so if
spacing or count buys more than per-rung precision does, this side would rather
spend there. That is `gaps[2]`.

## Three unknowns, all on this side

`assumptions_resolved: false` because of these, not because anything is hidden:

- **`per_rung_noise_model`** — the scatter on the drag-slope `gamma` has never
  been measured on data. The 3 % in the claim is the same 400-realisation numpy
  figure that went out through r2 and came back not corroborated. **Do not take
  it as an input and report what `h0` comes out at** — that is r1, and its
  ±0.195 µm is still uncorroborated. Sweep it.
- **`noise_shape`** — nobody has looked at whether the per-rung scatter is
  Gaussian, equal across rungs, or correlated with `h`. A monotonic-in-`h`
  component is the dangerous case: drift, the blur over-correction and the Faxén
  curve all have that shape. Gaussian i.i.d. is the acceptable baseline; say if
  it matters.
- **`estimator`** — this side still has not named its Lorentzian fit, and r4
  measured that the choice is worth up to +7.9 % on `f_c`. It matters less for
  this ask than for the others, but not zero: the equipartition `alpha` is what
  turns a slope into a `gamma`.

## The gap that is nobody's to close, and the one that is

- **`needs_data_transfer` · P7.** The per-rung scatter would be measured on the
  2026-09-03 run, which is on the instrument PC under `D:\codes`. This
  repository holds **no trajectory data at all**. So this round sets the target
  and not the verdict — and the next round should not be planned as though the
  comparison has been made.
- **`not_buildable_here` · the wall, owner `nobody`.** See above. `h0` comes
  from this instrument or from nowhere.

## Out of scope

Any restatement of `f_c`'s recoverability — r4 withdrew it and this ask does not
need it. `alpha(a)` across sizes (P0). The perpendicular coefficient. And any
gate threshold: whatever comes back is `simulated`, lands in `kb/external/bd/`
with `may_be_gate_threshold: false`, and does not move `REQUIRED_SAMPLING_RATIO`
in either direction.
