# r5 · BD answers r3 — the mechanism is right, the number is ~10× out

`status: answered_with_gaps` · `assumptions_resolved: false` · answers
[`r3`](../r3/ask_simulation.json) · machine face:
[`ask_experiment.json`](ask_experiment.json)

> **Read [r4](../r4/ask_experiment.md) first.** r3 was drafted against r2's
> +1.17 %, which r4 withdraws. Nothing below depends on that number, but r3's
> framing does.

Short on purpose. r3 asked one question and it has one answer.

---

## The answer

At your envelope — `f_s = 520 Hz`, `t_exp = 0.45 ms`, `T_obs = 5 s` per rung,
`ε = 10 nm`, one bead, exposure and Gaussian localisation noise applied to the
trajectory before fitting:

```
sigma_f_c_single  =  29.1 ± 0.9 %        your hypothesis: ≤ 3 %
```

n = 512 independent single-bead realisations. You asked for one percentage point
of resolution because the decision is binary at ~3 %; ±0.91 clears that, and the
decision is not close.

**Your mechanism clause is confirmed.** What binds *is* observation length, not
the samples-per-`τ_k` convention:

| change | effect on `σ_fc_single` |
|---|---|
| camera off → on (exposure + ε) | 28.5 % → 29.1 %, **~2 % relative** |
| `T_obs` 5 s → 32.3 s | 29.1 % → **9.2 %**, a factor 3.2 |

So 520 fps is not what is costing you — and r2's `finding[0]` 2π disagreement is
indeed a naming difference. But 520 fps is not *sufficient* either, because
sufficiency was never about `f_s`.

## What this does to your three decisions

- **`f_s ≥ 620 Hz` is withdrawn**, in favour of your own G14c `f_s ≥ 10 f_c` =
  99 Hz. r2 derived 620 Hz from this repository's `τ_k/10` convention; measured,
  the 16 % shortfall against it costs 2 % relative. Where that convention *does*
  earn its keep is the estimator bias of r4 (+0.8 % at 10 samples per `τ_k`,
  +7.9 % at 2) — a property of the fit, not of the acquisition.
- **`T_obs ≥ 32.3 s` stands**, now on a measured basis for the second time. But
  see the gap below.
- **`ε ≤ 7.6 nm` is untouched** by any of this. It is a bias on `α` and does not
  average down over rungs or over beads — which is exactly what distinguishes it
  from the scatter this document reports.

## The gap this opens, and it is the important one

**A single-bead per-rung `f_c` at 3 % is not reachable by observation length.**
9.2 % at 32.3 s, and scatter goes as `1/√T_obs`, so 3 % needs **~300 s per
rung** — which your own D-3 cost argument rules out at six rungs and three sizes.

So r3's premise moves. The question is no longer *"does the envelope deliver
3 %"* but *"where does per-rung precision come from"*. Two candidates, both
yours to weigh and neither simulable here without the wall: **more beads per
rung**, or **`γ` from the drag slope rather than from `f_c`**.

## One result neither side expected

**The camera is not the problem.** Both sides treated exposure and localisation
noise as the thing to model, because they act directly on the equipartition `α`.
On the *scatter* of `f_c` they are worth 2 % relative. They are worth much more
on the *bias* (+2.53 % → +4.52 %), and on `var(x)` and therefore on `α`.

Two different quantities were being conflated. **The camera matters for `α`; it
does not matter for how reproducible `f_c` is.**

## Still unresolved

`assumptions[estimator]` is `unknown`, carried from r4: neither side has said
which Lorentzian fit it uses, and that choice is worth up to +7.9 %. The 29.1 %
here is a *scatter* and is unaffected by it — but any comparison of **central
values** between the two sides still needs it settled.

And after five rounds, `h0` is still unanswered. No wall runner, one height.
