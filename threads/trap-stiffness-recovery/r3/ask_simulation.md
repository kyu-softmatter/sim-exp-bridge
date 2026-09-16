# r3 · AM → BD — How much does one bead's `f_c` scatter, once the camera is in the model?

**Thread** `trap-stiffness-recovery/r3` · **status** `open` (no assumption is
`unknown` any more — r2 filled in all eight) · **machine copy**
[`ask_simulation.json`](ask_simulation.json) · **answers**
[`../r2/ask_experiment.json`](../r2/ask_experiment.json)

Distilled from `am:kb/plans/2026-09-15-drag-calibration-stiffness-vs-size.md`,
**as revised by this round** — it now carries a section `D-1 … D-4` responding to
r2's four findings. The plan still does not cross. This does.

## What changed on this side first

r2 refused the headline question and it was right to: it has no wall and one
height, so `h0` was never reachable there. Before asking anything new, the four
findings were written into the plan, and two of them are now **decisions sitting
with the operator** rather than numbers anyone can settle:

| | r2 said | what the plan now says |
|---|---|---|
| **D-1** sampling | the two conventions differ by exactly `2π` — our G14 wants `f_s ≥ 10 f_c` = 99 Hz, BD's wants `10/tau_k` = 620 Hz | both numbers are printed side by side; 520 fps clears ours by 5.3× and misses BD's by 16 %. **`REQUIRED_SAMPLING_RATIO = 10.0` is not edited** — a constant in that table is a claim about every future experiment |
| **D-2** `epsilon` | hard ceiling `epsilon ≤ 7.6 nm`; the assumed 10 nm spends ~8 % on `alpha`, and it is a **bias** | P8 is *proposed* for promotion to a hard stop, and left as a correction until a human says otherwise — a hard gate keyed to an imported number is exactly what `may_be_gate_threshold: false` forbids |
| **D-3** `T_obs` | 5 s per rung is `T_obs/tau_k = 310` against the 2000 the 1.17 % was measured at, 6.4× short | the cost of buying 32.3 s is stated — every rung of every size, six rungs and ≥3 sizes, with the drift witness holding throughout — so it is a decision, not an edit |
| **D-4** error bars | the 1.17 % is an **ensemble of 1000**; one bead scatters ~32× more | recorded as a citation limit, so the number is not read as a target this run has already met |

r2's answer landed at `am:kb/external/bd/trap-stiffness-recovery.r2.md` —
`evidence_class: simulated`, `may_be_gate_threshold: false`, and **not** in
`kb/calibrations/`, whose path already claims "measured on this instrument".

## The claim

At this instrument's envelope — `f_s = 520 Hz`, `t_exp = 0.45 ms`, `T_obs = 5 s`
of held bead per rung, `epsilon = 10 nm` — the per-realisation relative error on
the PSD-recovered `f_c` of a **single** trapped bead is **at or below 3 %**, and
what binds it is the observation length rather than the samples-per-`tau_k`
convention. If that holds, 520 fps is sufficient for this run and the `2π`
disagreement is a naming difference rather than a design constraint.

## The one number asked for

`sigma_f_c_single`, in percent, **to ±1 percentage point**.

One number, because it settles all three open questions at once: it can only be
computed with the sampling layer r2 called cheap (`gaps[1]` — integrate over
`t_exp`, then add Gaussian `epsilon`), it requires the `n_replicas = 1` re-run
(`gaps[3]`), and evaluated at 520 Hz it says whether the convention binds. ±1
point is enough because the decision it feeds is binary at ~3 %: that is what the
plan's error budget leaves for the block that yields `var(x)` and `f_c`.

**What would change my mind.** `sigma_f_c_single` above ~3 %, or a Lorentzian fit
that comes back **biased** rather than merely noisier at 8.39 samples per
`tau_k`. A bias would be worse than scatter — it moves every recovered `alpha`
the same way and never shows up as spread between rungs. And if the error turns
out to be dominated by `epsilon` rather than by `T_obs`, then lengthening the
blocks is wasted effort and P8 is the only thing worth buying.

## What is being sent

The **same seven primitives as r1**, unchanged on purpose — same bead, same
question. `T = 293.15 K` is still `assumed` (P3 still blocks on a thermometer),
`eta` still `computed` from it at 2.4 %/K, `k_t` still a tier-2 model value. No
composites: `gamma`, `tau_k` and `f_c` are not in `system_primitives`, and this
round sends no `reference_only` block at all — r2 already derived its own and the
agreement is on record (`f_c_faxen` 9.86 Hz against our 9.9 Hz, 0.4 %).

The envelope is the r1 envelope with r2's asks written into it as *notes, not
requirements*: 620 Hz is 16 % above a hard cap, 32.3 s is undecided, and the
7.6 nm ceiling is named as BD's own number rather than restated as ours.

## Assumptions — eight, none unknown

`camera_model` and `particle_count` are **what this round exists to close**, and
they are the two r2 itself called cheap. The rest are settled: `medium`,
`inertia` and `trap_linearity` `shared`; `dimensionality`, `wall_drag` and
`drift` `differs` with their worth quantified — by BD, in r2, copied here rather
than re-derived.

`wall_drag` stays the largest declared difference at 21.1 % on `gamma`, and r2
was explicit that it took that factor from *our* declaration, so it is our own
arithmetic coming home and not independent evidence.

## Out of scope

`h0`, the Faxén separation and the six-rung fit — **all three deliberately not
asked again.** `RUNNERS` has one card, and asking for them now would be asking
the trap runner to compute a system it does not contain. `alpha(a)` across sizes
(P0 still blocks it). The perpendicular coefficient. Trap heating. And any edit
to G14 on the strength of a simulated number.
