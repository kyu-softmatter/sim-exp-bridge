# Request text for the experiment session (agentic-microscope)

> **Historical.** This is the text that was pasted into the microscope session to
> start the thread. It is kept as written except for translation and for counts
> that have since changed (the validator had seven rules then and has thirteen
> now). The thread has since run to r8; several implementation items below are
> done. Read `../README.md` for the current protocol.

---

## Purpose

This is the work of connecting this repository (the experiment / microscope
agent) to `~/Desktop/Brownian-Dynamics-Agent` (the simulation agent) **in both
directions**. Both flows have to work:

- **experiment → simulation**: BD designs a simulation on the basis of this
  repository's plans and results.
- **simulation → experiment**: this repository designs an experiment on the
  basis of BD's plans and results.

One principle carries the rest. **A question crosses, not numbers.** Do not copy
or translate the other side's plan. What arrives is a claim, the single
answering quantity, the required precision, the primitives that define the
system, and a declaration of assumptions — and **this repository's plan must come
out of its own gates, run from the start, with that as input.** Derived values
the other side computed are non-binding reference: **derive your own first, then
compare.**

The two systems need not be the same physical system. Differing SI values are
fine as long as the dimensionless regime brackets and the assumptions are
declared — that is in fact stronger evidence. What has to be prevented is an
**undeclared assumption difference**, which looks like agreement and is not.

## Read first

The shared repository already exists. **Read this before touching any code, and
report your review before implementing.**

    BRIDGE=~/Desktop/sim-exp-bridge

1. `$BRIDGE/README.md` — wire rules W1–W3, the evidence→tier table T1, the
   validator's rules, the layout, and what crosses versus what does not.
2. `$BRIDGE/threads/trap-stiffness-recovery/r1/ask_simulation.{md,json}` — an
   example of the document this repository **sends**. It was distilled from
   `kb/plans/2026-09-15-drag-calibration-stiffness-vs-size.md`, and every number
   in it is copied from that file.
3. `$BRIDGE/threads/trap-stiffness-recovery/r2/ask_experiment.{md,json}` — an
   example of the document this repository **receives**, produced by BD from
   `runs/trap-2d-5um__a5ef4f45d589`.
4. `$BRIDGE/threads/trap-stiffness-recovery/r2/kb_entry_for_am.md` — the form a
   received document takes when it lands in this repository's KB.
5. `$BRIDGE/schema/*.json` — the four schemas.

These are **both the specification and the worked example.** Do not design
something new; follow these shapes — and where one conflicts with a rule of this
repository, say so before implementing.

## Scope of this session

Work inside this repository (agentic-microscope) only. **Work on whatever branch
is currently checked out; do not switch branches or create one** — this session
already knows which branch it is on, and the person chose it for a reason. If it
is running in a worktree, that worktree is the working location.

**Read but never modify files in the BD repository
(`~/Desktop/Brownian-Dynamics-Agent`).** Do not load BD's `CLAUDE.md` either —
this repository boots on 416 lines of `SAFETY.md` plus five hard rules and BD has
its own ten principles, so merging them dilutes both and the refusals that make
each repository trustworthy stop firing.

## Wire rules — the part that applies here

**W1 · Do not nondimensionalise.** Do not build dimensionless-group code in this
repository. Things like `k d^2/kT` are BD's job in both directions, via
`bdbot/nondim.py` and `scales.py`. This repository **emits dimensional
quantities and receives dimensional ranges.** The `ask_experiment.requirements[]`
you receive are already SI ranges (`T_obs >= 32.3 s`, `f_s >= 620 Hz`,
`epsilon <= 7.6 nm`), so a gate can check them directly. The `regime[]` that
rides along is for a human to audit the inverse map and carries no force in any
machine check.

**W2 · Send the number in the unit it was measured in.** Do not normalise to SI
yourself — a conversion is where an error enters on the side with no unit
library. `pN/um`, `mPa*s`, `g/cm^3` travel as typed. **ASCII only**: `um`, not
`µm` (the validator's R2 refuses it).

**W3 · Send primitives, not composites.** Send `d`, `eta`, `T`, `k_t`; do not
send `gamma`, `tau_k`, `f_c`. `3*pi*eta*d` and `6*pi*eta*a` are the same formula,
so sending the product is where a factor of two enters with nobody lying — it is
the exact point BD's own intake already hit as ambiguity `A1` ("is R = 5 µm the
radius or the diameter?"). Derived values go in `reference_only`, **non-binding**.
R3 enforces this.

**Attach `evidence` to every number** (`measured | handbook | computed |
assumed`). BD derives its tier from that. Sending an unmeasured value as
`measured` makes BD inherit it at tier 0 — which is why r1 sends
`T = 293.15 K` as `assumed` and cites precondition P3.

## File ownership — how to share one repository without collisions

Each round has a defined writer, so the two sessions never touch the same file.

| file | written by |
|---|---|
| `threads/<thread>/r<N>/ask_simulation.{json,md}` | **this session** (odd rounds) |
| `threads/<thread>/r<N>/ask_experiment.{json,md}` | the BD session (even rounds) |
| `threads/<thread>/r<N>/kb_entry_for_am.md` | **this session** — the record of what it imported |
| `threads/<thread>/r<N>/kb_entry_for_bd.md` | the BD session |
| `hashes.json` | each side **only the keys with its own prefix**. `am:` keys are this session's, including `am:bridge/...` keys pointing at in-thread documents — the prefix means *who wrote it*, not where it lives |
| `schema/`, `validate.py`, `README.md` | propose changes; do not edit before agreement |

Thread paths are `<thread-id>/r<N>`. Do not thread by title — titles collide or
drift by round three, and the commonest failure in a round-trip loop is not that
a step was wrong but that after three rounds nobody is asking the original
question any more.

## Using the repository (git)

The shared repository is a git repository and all sessions use the same remote.

    https://github.com/kyu-softmatter/sim-exp-bridge
    local: ~/Desktop/sim-exp-bridge   (branch main, already cloned)

- **Always `git pull --rebase` before writing.** The other session may have
  pushed a round.
- **Commit only the files the ownership table assigns you.** One round = one
  commit, with the thread and round in the message
  (`r2: BD answers f_c to 1.17 %, refuses h0`).
- **Never `git push --force`.** The history is the record of the rounds.
- **If a conflict appears in a file you do not own, stop and report it.** That is
  not a merge to resolve; it is a signal that the ownership convention broke.
- **Do not use `git commit -am`** — it lands whatever the other side has staged.
  Use `git commit --only <paths>`.
- **Put your side in the commit message**, since the git author cannot
  distinguish sessions: `Bridge-Session: am`.
- This repository does not branch. A round is the unit of order, and the linear
  history on `main` is the record of the round trip. That is separate from the
  branch work in your own repository.

## Implementation items

1. **Emit a `plan_experiment_<title>.json` sidecar.** `knowledge/plans.py`
   already has the parsers (`_section()`, `_table_rows()`); reuse them. Numbers
   are authoritative in the structured block and the prose cites it, not the
   reverse.
2. **Add one rule to `plan-check`**: *every number in a prose table must exist in
   the structured block.* That is hard rule 2 made mechanical, so it pays for
   itself independently of the bridge.
3. **Create the `kb/external/bd/` namespace.** The path carries the foreign
   origin — this repository's plans cite by path, so a frontmatter field alone
   would not show at the citation site. Frontmatter follows
   `$BRIDGE/schema/kb_external_entry.schema.json`. **Never put an imported entry
   in `kb/calibrations/`** — that directory means "measured on this instrument",
   and a simulated `f_c` there is a lie the path itself tells.
4. **Actually enforce `may_be_gate_threshold: false`.** A foreign entry may set a
   target or motivate a design, but **it may not be the threshold a gate clears
   against.** A gate fed a simulated number emits a margin that reads as
   measured — the disease hard rule 3 already names. If you allow it, the margin
   must inherit the taint and read as `m = 1.05 (external-derived)`.
5. **Add a hash-drift check** to `python -m knowledge.cli`. When a `source_hash`
   diverges from upstream, name every plan citing that entry. The lifecycle is
   **supersession, not deletion** — an import deleted "temporarily" dangles the
   citations of plans that have already graduated into `kb/decisions/`. This
   repository already has `superseded_by` / `corrected_by`.
6. **An `ask_simulation.json` writer.** The r1 fixture is the target shape:
   `system_primitives` (primitives only, in the measured units, `evidence`
   required), `instrument_envelope` (what the instrument can actually do, so BD
   can answer "your camera cannot reach that"), `assumptions` (each
   `shared | differs | unknown`), `reference_only` (non-binding), and
   `required_precision` — **the only free number that must cross**, since without
   it BD's gates are unconstrained and any plan passes.
7. **Answer the three findings r2 has already raised.** This is the round's real
   output.
   - The sampling conventions differ by exactly 2π. This repository's gate asks
     `f_s >= 10 f_c` = 99 Hz; BD's convention asks `10/tau_k` = 620 Hz. 520 fps
     clears the former by 5.3× and is 16 % short of the latter. **Which governs
     is a human decision**, so put both numbers in the plan side by side and
     request the decision rather than settling it.
   - At `epsilon = 10 nm` the precision budget is already spent: ~8 % on `alpha`,
     and it is a **bias**, so it does not average down over rungs or segments.
     Consider promoting precondition P8 from a correction to a hard gate.
   - 5 s per rung is `T_obs/tau_k = 310` against the 2000 at which BD measured
     its 1.17 % — a factor of 6.4.

## Verification

    cd $BRIDGE && python3 validate.py --selftest     # do the rules still bite
    cd $BRIDGE && python3 validate.py threads/<thread>/r<N>/ask_simulation.json

`--selftest` requires that `threads/` passes and that each file in
`fixtures/invalid/` fires **only the rule its filename names**. Changes on this
side must additionally keep `python -m knowledge.cli plan-check` and the existing
tests passing.

## Never

- Do not write `confirmed_by`. Both repositories reserve it for a human, and the
  bridge is the one component positioned to forge it (R7).
- Do not summarise or restate a number you were given. **An import is a
  mechanical copy.** Summarising makes the file a new origination point, which
  hard rule 2 forbids.
- Do not guess at a unit string. If it does not parse, refuse.
- Do not build dimensionless-group code (W1).
- Do not modify the BD repository or load BD's `CLAUDE.md`.

## What the first response should be

Before writing code, report which of items 1–7 **conflict with a rule of this
repository or are larger than they look.** Item 4 in particular may require
touching gate implementations, so confirm where the change actually has to go
before proposing a plan.
