# r4 · BD corrects r2 — the +1.17 % was the estimator, and the blur term is half what was sent

`status: supersedes_prior` · corrects `r2` (now `corrected`) and AM's r1
`camera_model` · machine face: [`ask_experiment.json`](ask_experiment.json)

**This document answers no new question.** It exists because two numbers this
thread is built on are wrong, and r3 was already being written on top of one of
them. Round parity does not apply to a correction — the side that finds its own
earlier answer wrong is the only side that can say so.

Everything below was settled on **exact Ornstein–Uhlenbeck data, whose `f_c` is
known in closed form**, and not by argument. No HOOMD time was spent; an exact
OU sampler is unbiased at any step size, which is precisely what let the
estimator's bias be separated from integration error. A BD re-run could not have
separated them.

---

## 1 · `achieved_precision = 1.17 %` is withdrawn, and not replaced

r2 reported `f_c` recoverable to **+1.17 %**, citing
`metrics.json observables[] err_pct`. Feeding exact OU through **the archived
run's own estimator configuration** — Welch, `nperseg = 4096`, unweighted
`curve_fit` of `S0/(1+(f/f_c)²)` over the whole one-sided PSD, 250 traces
averaged before fitting — returns:

```
estimator bias on exact OU  =  +0.8 to +1.2 %
the run reported               +1.17 %
```

0.1 σ apart. **The simulation reproduced the estimator, and the estimator was
read as physics.**

It is a **bias, not a variance**: `T_obs × 26` does not remove it (+0.57 % at
`T_obs/τ_k = 310`, +0.98 % at 8000). The sampling dependence is non-monotonic —
+7.9 % at 2 samples per `τ_k`, +0.8 % at 10, +3.8 % at 50 — because an
unweighted least squares over the whole band is dominated by points far above
the corner, which carry no information about `f_c`.

**What replaces it: nothing.** Not another number. The ensemble's statistical
scatter at `T_obs/τ_k = 2000` is 0.43 % sd, but that is 250 non-interacting
replicas and corresponds to no experiment; one bead is 9.0 % sd at the same
window. All of them still sit on the bias. **How well `f_c` can be recovered is
not known until the estimator is fixed** — a weighted fit, or a band restricted
to the corner. That is an analysis change, not a physics change, and the
archived trajectory does not need re-running.

## 2 · The blur coefficient for a trapped bead is `u/3`, not `2u/3`

AM's r1 `camera_model` quotes `2·D·t_exp/3`. That is the **free-particle MSD**
blur term. For a bead in a harmonic trap the exposure-averaged variance is exact:

```
var_blur / var  =  2(u − 1 + e^−u) / u²        u = t_exp/τ_k
                →  1 − u/3        as u → 0
```

Measured against exact-OU boxcar averaging at five values of `u` from 0.028 to
3: the exact formula holds everywhere **within 3.3 σ**, `2u/3` is rejected at
**16 σ to 358 σ**.

Every entry of the plan's `blur on var(x)` column is exactly **half** what is
written: 0.60 % at `h = 3.0 µm` rising to 0.97 % at `h = 10 µm`, not 1.21 % to
1.94 %.

⚠️ **Not a flat offset.** `u = t_exp/τ_k(h)` varies monotonically along the
ladder, so correcting `α` by `2u/3` puts a monotonic-in-`h` error into the
quantity being fitted. The size is small — a 0.37 percentage-point swing across
the ladder against a Faxén signal of +86.6 % to +16.2 % — so this is **a
correction to make, not a threat to `h0`**. Stated with its size so it is not
over-read.

## 3 · r2's own single-bead ratio was also wrong

r2 `finding[3]` said one bead scatters **~32×** more, i.e. `√1000`. Measured:
**21.1×** at `T_obs/τ_k = 2000` and **15.5×** at 310. `f_c` is fitted to the
`n_trace = min(250, N)` subset, not to all 1000 particles, and averaging PSDs
before a non-linear fit is not averaging fits, so it is not `√n` either.

The ratio was the wrong thing to carry. **The absolute number is 9.2 % sd per
bead at 2000, and 29.1 % at 310.**

---

## What happens to r2's three requirements

| | verdict |
|---|---|
| `T_obs ≥ 32.3 s` | **same number, different basis.** Its justification was "2000 is where the 1.17 % was measured" — void. It survives on a measurement r2 did not have: 5 s → 32.3 s takes one bead from **29.1 ± 0.9 %** to **9.2 ± 0.3 %** scatter, a factor 3.2. Weigh D-3's cost against *that*, not against 1.17 % |
| `f_s ≥ 620 Hz` | **unchanged** — it came from the `τ_k/10` convention, never from the 1.17 %. One thing added: at your envelope the convention is **not what binds**. Turning the camera on and off at 5 s/rung moves the scatter 28.5 % → 29.1 %, about 2 % relative, while `T_obs` moves it by 3.2× |
| `ε ≤ 7.6 nm` | **unchanged and still hard.** Derived from `(ε/l_k)²`, independent of both corrected numbers. The blur fix moves the net camera effect on `α` from ~8.0 % to ~7.7 %, still ε-dominated |

## What this document does not do

- **It does not answer r3.** The measurement exists, but folding an answer into a
  correction would let the correction be read as a negotiation. Next round.
- **It does not restate recoverability.** Withdrawn, not replaced.
- **It does not close the wall.** Still no runner, still one height, `h0` still
  unanswered.

## One thing to settle, and it is not ours alone

**Neither side has said which Lorentzian estimator it uses.** Measured here, the
choice of fit is worth more than most of the physics differences in this thread
— up to +7.9 %. Until both sides name the fit (weighted or not, over what band),
an agreement on `f_c` between them is uninterpretable at the ~1 % level.

Raised as a `finding` rather than an `assumption` because R4 makes an `unknown`
assumption force `status: draft`, and a correction must not wait to be a draft.
The protocol has no carve-out for that; one is proposed rather than assumed.
