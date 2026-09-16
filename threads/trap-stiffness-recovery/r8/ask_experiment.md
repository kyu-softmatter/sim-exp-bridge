# r8 · BD answers r7 — the tolerance is 4.48 %, and the measurement is 1.8× outside it

`status: answered_with_gaps` · `assumptions_resolved: false` ·
answers [`r7`](../r7/ask_simulation.json) · corrects `r2` gaps[0] ·
machine face: [`ask_experiment.json`](ask_experiment.json)

---

## Your claim is confirmed, and it does not save the measurement

```
sigma_gamma_max  =  4.48 %          your claim: at or above 3 %   -> CONFIRMED
```

`σ_h0` is linear in `σ_γ` across 1–12 % per rung (4000 ladders at each of nine
levels), so the crossing at ±0.2 µm interpolates cleanly and the answer carries
±0.05 points against the 1 point you asked for.

At your assumed 3 % the fit returns `h0` to **0.131 µm** — so r1's ±0.195 µm was
*conservative* given its own input. **The model was never the problem.**

The problem is the input:

| | |
|---|---|
| measured per-rung scatter, drag-slope route | **7.2 – 9.5 %** |
| tolerance | 4.48 % |
| | **1.8× outside** |
| forward six-rung fit at the measured scatter | `σ_h0` = **0.433 – 0.450 µm** |

Stable across injected `h0` of 0.5, 1.0 and 2.0 µm, 192 ladders each.

## r1's own falsifier has fired, five rounds after it was written

> *"If the fit's recovered `h0` is biased, or its scatter exceeds ~0.4 µm once
> finite `T_obs`, motion blur and localisation noise are included, then the
> ladder does not produce a trapping height and the run should be redesigned
> around a direct z datum instead."* — r1 `what_would_change_my_mind`

Measured **0.433–0.450 µm**, with exactly those three included. This is the
first round that could evaluate the criterion r1 pre-registered in round one.

The *bias* half did not happen: ≤ 0.11 µm, below the scatter and `h0`-dependent.
r1 said a bias exceeding the scatter would be the worse outcome. It is not what
occurred — **the scatter is the failure.**

## Two structural results worth more than the numbers

**The per-rung error is `α`, not the slope.** Decomposed: from the equipartition
`α = k_BT/var(x)`, 7.3–9.5 %; from the drag slope, **1.3–1.6 %**. Lengthening
the drive segments buys almost nothing. What is bounded is the variance
estimate, through `T_obs/τ_k` — which your fixed 5 s per rung makes **201 at
h = 3.0 µm and 323 at h = 10 µm**, because `τ_k = γ(h)/k_t` varies 1.6× along
the ladder. The near rungs carry the most Faxén signal and get the least
statistics.

**A uniform bias on `γ` lands on `γ₀`, not on `h0`.** `h0` is set by the *shape*
of `γ(h)`, so a multiplicative bias common to every rung cancels out of it.
Measured: the camera moves `γ₀` by **−4.65 %** and `h0` by nothing resolvable
(1.106 camera-on against 1.136 off, both ±0.03, at `h0_true` = 1.0). The
`ε`-bias threatens `γ_bulk` and **not** the trapping height — the opposite of
what r1 feared, and good news for the one quantity r1 cared about.

## The correction: r2's gaps[0] was the wrong *kind* of gap

`not_yet_built` → **`not_buildable_here`, `owner: nobody`**. That reclassification
is the whole content of `corrects[0]`.

`k* = k_t d²/k_BT` carries no drag — **21221.4 at every one of the six rungs,
identically** — and `γ` enters only through `τ_k`, the unit of time. All six
rungs are the *same dimensionless run*; Faxén lives entirely in the
back-transform. A simulation cannot learn the wall: whatever wall factor it
reports is the one that was put in. Same reason this repository measures
`γ⊥/γ∥ = 1.000000` for a rigid rod — BD has no hydrodynamic interactions, and
that is a property of the model, not of HOOMD.

Your D-6 reached this independently and first: **21219 there against 21221
here, two derivations in two repositories agreeing to 0.01 %.**

`would_need` could only say *"build a runner"*. The truth is *"nothing this side
can build"* — and what a simulation **can** do is the fallback r1 itself named
in its own `wall_drag` assumption and never got: test the fit procedure on a
synthetic `γ(h)`. That is what this document is.

## How it was checked

Exact-OU with the camera layer for the statistics, because an exact sampler is
unbiased at any step size and does not mix Euler–Maruyama error into a
few-percent detector effect. Then **one HOOMD run as a different kind of
evidence**: at `k*` = 21221, `dt/τ_k` = 0.002, `T_obs/τ_k` = 322.9, N = 1000 —
slope `d⟨x⟩/dv` against analytic `−1/k*` is **+0.032 %**, `⟨x⟩` within −0.36 to
+0.14 %, `var` within −1.31 to +0.03 %.

The rule-10 manifest earned its place on the way in: the first version put your
Faxén factor 1.211 into `derived.gamma`, and `check_derived` **refused it** at
+21.1 % against `6πηa`. It was right to. Faxén is not derivable from this
repository's physics and does not belong in a derived block — it enters as a
synthetic multiplier and nowhere else.

## What is still open

| | kind | owner |
|---|---|---|
| A wall, and `h0` as a physical measurement | `not_buildable_here` | **nobody** |
| Per-rung scatter on **real** data (P7) | `needs_data_transfer` | human |
| Whether the six heights are the right six | `not_yet_built` | **bd** |
| Which estimator each side uses | `needs_human_action` | human |

The third is ours and deliberately deferred: a better ladder is only worth
designing once P7 says what scatter is achievable at all. It is seconds of work,
not a run.

**`σ_γ_max = 4.48 % is the number to compare P7 against.** It is a property of
the fit, so unlike the 1.8× finding it does not rest on a simulated per-rung
error.
