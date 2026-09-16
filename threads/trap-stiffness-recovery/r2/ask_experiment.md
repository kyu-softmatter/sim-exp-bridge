# r2 · BD → AM — f_c is recoverable to 1.17 %; h0 is not reachable here

**Thread** `trap-stiffness-recovery/r2` · **status** `answered_with_gaps` ·
**reply to** [`../r1/ask_simulation.json`](../r1/ask_simulation.json) ·
**machine copy** [`ask_experiment.json`](ask_experiment.json)

Built from [`bd:runs/trap-2d-5um__a5ef4f45d589`](../../../../) (verdict PASS).
Not a fresh run: the archived production run sits at a regime that **brackets**
AM's, which is stated as such rather than assumed away.

## What is answered, and what is refused

**Refused: `h0`.** This case has no wall and one height — there is no `h` in the
system at all. The answering quantity of r1 is not answered.

**Answered: `f_c`.** Recoverable from a finite Brownian trajectory to **+1.17 %**
against a 5 % tolerance at `T_obs/tau_k = 2000` with 10 samples per `tau_k`
(`metrics.json`: measured 40.1516 Hz vs analytic 39.6871 Hz; the other four
observables of the same run agree to better than 0.35 %). That is the largest
sub-question this case can close honestly: `f_c` is what sets `gamma_corr` per
rung, so the h0 fit's **per-rung input error** is set by acquisition length,
sampling rate and localisation noise — not by the fit.

## Unit round-trip — read this before the numbers

Everything AM sent, restated in AM's own units, plus what was derived here:

| derived | value | from |
|---|---|---|
| `a` | 2.475 µm | `d/2` — **the radius/diameter check**. Agrees with AM's tables and with `gamma = 6πηa`. |
| `kT` | 4.0478e-3 pN·µm | `k_B · 293.15 K` |
| `gamma_0` | 0.046725 pN·s/µm | `6πηa`, **bulk Stokes, no wall** |
| `gamma_corr` | 0.056584 pN·s/µm | `gamma_0 × 1.211`, where 1.211 is **AM's** declared Faxén factor — not this repository's physics |
| `l_k` | 33.98 nm | `sqrt(kT/k_t)` — against AM's quoted 34 nm: **agrees** |
| `tau_k` | 16.14 ms | `gamma_corr/k_t` |
| `f_c` | 9.86 Hz | against AM's quoted 9.9 Hz: **agrees to 0.4 %** |

`T` was imported at **tier 3**, not tier 0, because AM marked it `assumed`.

## Requirements — dimensional, in AM's units

AM never sees a dimensionless number. The inverse map is BD's job; the `from`
column is prose for a human to audit.

| quantity | requirement | hard | why |
|---|---|:-:|---|
| `T_obs` per rung | **≥ 32.3 s** | no | `T_obs/tau_k = 2000` is where the 1.17 % was actually measured. AM's 5 s gives **310** — clears this repo's soft floor of 100 with margin 3.1, but is **6.4× below** the validated configuration. |
| `f_s` | **≥ 620 Hz** | no | `tau_k/10` sampling. AM's envelope caps at 520 Hz = **8.39** samples/`tau_k`, 16 % short of a *convention*, not of a limit. |
| `epsilon` | **≤ 7.6 nm** | **yes** | `(epsilon/l_k)² ≤ 0.05`. AM's assumed 10 nm is 0.294 `l_k` → 8.7 % on `var(x)`, ~8 % on `alpha`. Hard because it is a **bias**: it does not average down over rungs or segments. |
| `sigma_gamma` per rung | ≤ 3.0 % | no | **AM's own figure, passed through unverified.** Recorded so it is visible; see gap 3 so it is not read as corroborated. |

## Regime — different systems, same question

The two calculations are **not** the same physical system, and they do not need
to be. What has to transfer is the recoverability of `f_c`:

| group | BD | AM | reading |
|---|---|---|---|
| `k*` = `k d²/kT` | 60 358 | 21 221 | BD is 2.84× stiffer — the **harder** case, so the 1.17 % transfers conservatively |
| `l_k/d` | 0.004070 | 0.006865 | AM's fluctuation is 1.69× larger relative to the bead: the favourable direction for localisation |
| `tau_p/tau_k` | 8.14e-4 | 7.30e-5 | overdamped both sides against a hard limit of 1e-2 — **genuinely shared** |
| `T_obs/tau_k` | 2000 | 310 | ≈ `sqrt(2000/310)` = 2.5× the scatter, so ~3 % not ~1.2 % |
| samples/`tau_k` | 10 | 8.39 | convention, 16 % short — see finding 1 |

## Four findings

1. **The two repositories' sampling conventions differ by exactly 2π.** AM's gate
   asks `f_s ≥ 10 f_c` = 99 Hz. BD's convention is `tau_k/10`, i.e.
   `f_s = 62.8 f_c` = 620 Hz. *Owner: human.*
2. **The localisation budget is already spent.** AM treats `epsilon = 10 nm` as
   ~9 % of `var(x)`, measurable and correctable. It is ~8 % on `alpha` and it is
   a bias — correcting for a measured `epsilon` is fine, but then the
   correction's own error becomes the budget. *Owner: AM.*
3. **5 s per rung is 6.4× below the validated configuration.** Passes the soft
   floor; implies ~3 % on `f_c`, leaving almost nothing for finding 2. *Owner: AM.*
4. **Every error bar here is an ensemble error bar.** `N = 1000` independent
   replicas. One bead at the same `T_obs/tau_k` would scatter ~32× more.
   **Comparing this 1.17 % against a single-bead measurement is invalid as
   stated.** *Owner: BD.* — this is the most important line in the document.

## Assumptions, now resolved

`differs`: **dimensionality** (2D vs 3D — worth **0 %** on these per-component
observables, but declared `differs` because the zero is conditional on the
observable list), **wall_drag** (no wall; worth 21.1 % on `gamma`, 17.4 % on
`f_c`, taken from AM's own factor), **camera_model** (no detector; worth ~8 %),
**particle_count** (1000 replicas; worth 0 % on the central value, **32× on the
error bar**), **drift** (absent by construction).

`shared`: medium, inertia, trap_linearity.

## Gaps

1. The Faxén separation, hence `h0`. Needs a **second runner** — a trapped sphere
   at a no-slip wall with height-dependent mobility. `RUNNERS` in `cli.py` has
   one card today, and running the trap runner on this would silently compute the
   wrong system.
2. Blur and `epsilon`. A post-processing layer over sampled positions, not a
   physics change — cheap, ~a day, and it would let r3 answer what r2 deferred.
3. The six-rung fit itself. Not simulated; AM's 3 %/rung passed through.
4. One bead vs 1000 replicas. **Re-run at `n_replicas = 1` with many seeds** —
   cheap, and it should be the first thing r3 does.
