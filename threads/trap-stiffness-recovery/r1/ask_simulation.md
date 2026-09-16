# r1 · AM → BD — Does the height ladder actually return a trapping height?

**Thread** `trap-stiffness-recovery/r1` · **status** `draft` (every assumption is
still `unknown`) · **machine copy** [`ask_simulation.json`](ask_simulation.json)

Distilled from [`am:kb/plans/2026-09-15-drag-calibration-stiffness-vs-size.md`](../../../../)
(`status: planned`). **The plan does not cross. This does.**

## The claim

On a six-rung height ladder — one bead at `a = 2.475 µm`, `h = 3.0 … 10 µm` —
combining the drag slope `x_eq(v)` with the equipartition stiffness `kT/var(x)`
separates `gamma_corr(h)` from `alpha`, and a least-squares fit of

    gamma(dz) = gamma_0 / (1 - 9a/(16(dz + h0)))

recovers the unknown focal-plane-to-trap offset **`h0` to ±0.195 µm** and
`gamma_bulk` to 2.1 %, unbiased.

## Why it is being asked

`h0` is the dominant systematic on `alpha`, it has never been measured on this
instrument, and SAFETY §9 lists it as an open safety question. The ±0.195 µm
above is **AM's own estimate**, from 400 numpy realisations at 3 % per point
(seed 3) — and that toy model assumed Gaussian per-rung error and *nothing
else*. No finite observation window, no motion blur, no localisation noise. The
question is whether the number survives real Brownian dynamics.

**What would change my mind.** A biased `h0`, or scatter beyond ~0.4 µm once
those three are included. A bias would be worse than scatter: it would put every
`alpha` in the series wrong in the same direction.

## What is being sent, and what deliberately is not

Seven primitives, **in the units they were measured in** — `d = 4.95 µm`
(measured lot mean), `rho = 1.05 g/cm³`, `eta = 1.0016e-3 Pa·s`,
`k_t = 3.5054 pN/µm`, `pixel_size = 0.06453 µm`. No SI normalisation, no
composites. `gamma`, `tau_k` and `f_c` are **not** in `system_primitives`; they
are in `reference_only`, non-binding, to be read only *after* BD has derived its
own. `3πηd` and `6πηa` are the same formula, and sending the product is where a
factor of two enters with nobody lying.

Two of the seven are honest weak points and are marked as such rather than
dressed up:

- **`T = 293.15 K` is `assumed`, not measured.** Precondition P3 blocks on a
  thermometer at the sample. Marked `evidence: assumed` so BD imports it at
  tier 3 instead of inheriting it as tier 0 — which is exactly the failure
  `bdbot/provenance.py` warns about in its own header.
- **`eta` is `computed` from that assumed `T`**, at 2.4 %/K. It inherits the
  assumption and says so.

`k_t` is a **model** value (`trapping/goa.py force-curve --dial 1`), tier 2. The
model predicts `alpha = 8.68/a` and nothing else, which is the thing the run
tests — so it is an input here only to set the timescales.

## The instrument's envelope

`f_s ≤ 520 Hz` (hard — ROI 256×512 at 16-bit sets it), `t_exp ≤ 0.576 ms`,
`T_obs = 5 s` per rung as currently planned, `h ∈ [3.0, 10.0] µm` (near end:
the `9a/(16h)` expansion refuses `h ≤ a`; far end: lens 4's RI-mismatch limit
`1.85/|dn|`), `epsilon ≈ 10 nm` assumed pending P8.

This block exists so BD can answer *"your camera cannot reach that"* instead of
proposing something unbuildable.

## Assumptions — all eight `unknown`, which is why this is a draft

`dimensionality` · `wall_drag` · `medium` · `camera_model` · `particle_count` ·
`trap_linearity` · `inertia` · `drift`

These are the only content in this document that **no number reveals**. "Faxén
parallel, first order, +16 % to +87 % over the ladder" does not follow from any
value BD receives, and neither does "3D chamber, x only". Two are flagged in
advance as probably load-bearing: BD's trap case has **no wall at all**, and a
BD trajectory has **no detector** — so it has neither the blur nor the `epsilon`
that the toy estimate also omitted.

## Out of scope

The perpendicular Faxén coefficient (the drive is in x; nothing here licenses an
axial claim). Trap heating. And `alpha(a)` across sizes — precondition P0 blocks
it, since only two registered sizes exist spanning 1.24× against a ~8 %
systematic. **This ask is one bead, one ladder.**
