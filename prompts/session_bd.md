# Request text for the simulation session (Brownian-Dynamics-Agent)

> **Historical.** This is the text that was pasted into the simulation session to
> start the thread. It is kept as written except for translation and for counts
> that have since changed. The thread has since run to r8; several implementation
> items below are done. Read `../README.md` for the current protocol.

---

## Purpose

This is the work of connecting this repository (the simulation agent) to
`~/Desktop/agentic-microscope` (the experiment / microscope agent) **in both
directions**. Both flows have to work:

- **simulation → experiment**: AM designs an experiment on the basis of this
  repository's plans and results.
- **experiment → simulation**: this repository designs a simulation on the basis
  of AM's plans and results.

One principle carries the rest. **A question crosses, not numbers.** Do not copy
or translate the other side's plan. What arrives is a claim, the single
answering quantity, the required precision, the primitives that define the
system, and a declaration of assumptions — and **this repository's spec must come
out of its own L0→L2→nondimensionalisation pipeline, run from the start, with
that as input.** Derived values the other side computed are non-binding
reference: **derive your own first, then compare.** Reversing that order turns
verification into anchoring.

The two systems need not be the same physical system. Differing SI values are
fine as long as the dimensionless regime brackets and the assumptions are
declared — that is in fact stronger evidence. What has to be prevented is an
**undeclared assumption difference**: matching every dimensionless group still
leaves two different systems if one has a wall and the other does not.

## Read first

The shared repository already exists. **Read this before touching any code, and
report your review before implementing.**

    BRIDGE=~/Desktop/sim-exp-bridge

1. `$BRIDGE/README.md` — wire rules W1–W3, the evidence→tier table T1, the
   validator's rules, the layout.
2. `$BRIDGE/threads/trap-stiffness-recovery/r1/ask_simulation.{md,json}` — an
   example of the document this repository **receives**, distilled from AM's
   `kb/plans/2026-09-15-drag-calibration-stiffness-vs-size.md`.
3. `$BRIDGE/threads/trap-stiffness-recovery/r2/ask_experiment.{md,json}` — an
   example of the document this repository **sends**, with every number copied
   from `runs/trap-2d-5um__a5ef4f45d589`'s `metrics.json` and `spec.json`.
4. `$BRIDGE/threads/trap-stiffness-recovery/r1/kb_entry_for_bd.md` — the form a
   received document takes when it lands in this repository's KB.
5. `$BRIDGE/schema/*.json` — the four schemas.

These are **both the specification and the worked example.** Do not design
something new; follow these shapes — and where one conflicts with a principle of
this repository (especially principle 1, dimensions first; principle 2, never
hand-write a dimensionless spec; principle 3, provenance), say so before
implementing.

## Scope of this session

Work inside this repository (Brownian-Dynamics-Agent) only. **Work on whatever
branch is currently checked out; do not switch branches or create one** — this
session already knows which branch it is on, and the person chose it for a
reason. If it is running in a worktree, that worktree is the working location.

**Read but never modify files in the AM repository
(`~/Desktop/agentic-microscope`).** Do not load AM's `CLAUDE.md` either — AM
boots on 416 lines of `SAFETY.md` plus five hard rules and this repository has
its own ten principles, so merging them dilutes both and the refusals that make
each repository trustworthy stop firing.

## Wire rules — this repository **owns** both conversions

**W1 · Nondimensionalisation is this repository's job in both directions.** AM
has no such capability, and forcing it to acquire one creates one more place for
an error. Hence the asymmetry in the protocol.

- **Receiving**: parse the dimensional primitives AM sent with `bdbot/units.py`
  (pint) and reduce with `nondim.py`.
- **Sending**: **inverse-map** the dimensionless result back into **SI ranges in
  AM's own units** with `scales.py`. That is what `ask_experiment.requirements[]`
  is, and it is all AM's gates need to see (`T_obs >= 32.3 s`, `f_s >= 620 Hz`,
  `epsilon <= 7.6 nm`). `regime[]` rides along so a human can audit the inverse
  map, stated as carrying no force in AM's machine checks. Its shape deliberately
  matches `spec.json`'s `groups[]`, so the adapter is nearly a copy.

**W2 · Do not guess at a received unit.** AM sends `pN/um`, `mPa*s`, `g/cm^3` in
the form they were measured. If pint cannot parse it, **refuse** — a guessed unit
is a silent multiplier. And **convert at use time, not at import time**: the
foreign KB entry keeps AM's units as sent, and the pipeline
nondimensionalises when it consumes them.

**W3 · This repository forms the composites.** AM sends only `d`, `eta`, `T`,
`k_t` and not `gamma`, `tau_k`, `f_c`. `3*pi*eta*d` and `6*pi*eta*a` are the same
formula, so receiving the product is where a factor of two enters with nobody
lying — it is the exact point this repository's own intake already hit as
ambiguity `A1` ("is R = 5 µm the radius or the diameter?").

**T1 · Derive the tier; never guess it.** AM attaches `evidence` to each number.

| `evidence` | tier | note |
|---|:-:|---|
| `measured` | 0 | measured on AM's instrument |
| `handbook` | 0 | |
| `computed` | 1 | but **inherits the worst tier of its inputs.** r1's `eta` is tier 3 because it is computed from an assumed `T` |
| `assumed` | 3 | a default, a placeholder, a standing choice |

"Tier 1 by inheritance", which `provenance.py`'s own header warns about, is
exactly this point. Inheriting is legitimate; recording it as if it were measured
is not.

**A unit round-trip echo is mandatory.** Because this repository owns both
conversions, nobody audits them. The physics cannot be checked from outside but
the units can: restate every primitive you parsed **in the unit AM sent it in**
under `parsed_back.received`, and put the composites you formed under
`parsed_back.derived_here`. That is why the r2 fixture states `a = d/2 = 2.475
um` explicitly and compares AM's 9.9 Hz against its own 9.86 Hz.

## File ownership — how to share one repository without collisions

| file | written by |
|---|---|
| `threads/<thread>/r<N>/ask_experiment.{json,md}` | **this session** (even rounds) |
| `threads/<thread>/r<N>/ask_simulation.{json,md}` | the AM session (odd rounds) |
| `threads/<thread>/r<N>/kb_entry_for_bd.md` | **this session** — the record of what it imported |
| `threads/<thread>/r<N>/kb_entry_for_am.md` | the AM session |
| `hashes.json` | each side **only the keys with its own prefix** (`bd:` here) |
| `schema/`, `validate.py`, `README.md` | propose changes; do not edit before agreement |

Thread paths are `<thread-id>/r<N>`, never by title. The commonest failure in a
round-trip loop is not that a step was wrong but that after three rounds nobody
is asking the original question any more.

## Using the repository (git)

The shared repository is a git repository and all sessions use the same remote.

    https://github.com/kyu-softmatter/sim-exp-bridge
    local: ~/Desktop/sim-exp-bridge   (branch main, already cloned)

- **Always `git pull --rebase` before writing.**
- **Commit only the files the ownership table assigns you.** One round = one
  commit, naming the thread and round.
- **Never `git push --force`.** The history is the record of the rounds.
- **If a conflict appears in a file you do not own, stop and report it.**
- **Do not use `git commit -am`** — it lands whatever the other side has staged.
  Use `git commit --only <paths>`, and leave the other side's untracked files
  alone even when they are in the way.
- **Put your side in the commit message**: `Bridge-Session: bd`.
- This repository does not branch; a round is the unit of order.

## Implementation items

1. **Import adapter: `ask_simulation.json → intake/<case>/observation.yaml +
   system.yaml`.** Put it beside `bdbot/intake.py`. `observation.yaml` is the
   transcription layer, so record the received document as its source;
   `system.yaml` is L2 and keeps its `derived_from`. **Derive** tiers via T1
   above. The received `assumptions` are not values and cannot be derived — carry
   them verbatim and fill in this repository's counterpart to settle each
   `shared | differs | unknown`.
2. **Export adapter: `metrics.json` + `spec.json` → `ask_experiment.json`.**
   Reuse the `groups[]` and `back_transform` that `spec.json` already carries.
   `achieved_precision` comes from `observables[].err_pct` — the value **achieved**,
   not the target. `requirements[]` is the inverse-map output, and each item's
   `from` carries the derivation in prose.
3. **Create the `knowledge/external/am/` namespace.** The path carries the
   foreign origin. Frontmatter follows
   `$BRIDGE/schema/kb_external_entry.schema.json`, with
   `may_be_gate_threshold: false` as the default. The lifecycle is
   **supersession, not deletion** — an import deleted "temporarily" dangles
   everything that cited it.
4. **A hash-drift check.** When a `source_hash` diverges from upstream, name the
   specs resting on that entry. The `bd:` keys in `$BRIDGE/hashes.json` are this
   session's to maintain.
5. **The two cheap gaps r2 left against itself.** These are what actually advance
   the next round.
   - **A sampling layer**: integrate positions over `t_exp`, then add Gaussian
     `epsilon`. It is post-processing rather than a change of physics, so it is
     cheap — and with it the next round can answer the question r2 deferred (what
     blur and localisation noise do to `h0` recovery).
   - **`n_replicas = 1` with many seeds**: the current 1.17 % is an
     ensemble-of-1000 error. The experiment has one bead per rung, so it would
     scatter ~32× more. Making the per-round error bars mean the same thing was
     the most important of r2's findings.
6. **A wall runner is a separate card.** Handling the
   `gamma(h) = gamma_0/(1 - 9a/(16h))` family needs a new entry in `RUNNERS`.
   **Do not quietly run it on the trap runner** — that computes the wrong system.
   It does not have to be built this round, and if it cannot be, say so in
   `gaps[]`. **A refusal is a valid result.**
7. **Leave `plan_simulation_<title>.md` as a generated artefact.**
   `bdbot/report.py` already writes prose, so do not hand-write it. The pipeline
   is authoritative and the markdown is its output, which makes md↔json drift
   structurally impossible on this side.

## Verification

    cd $BRIDGE && python3 validate.py --selftest     # do the rules still bite
    cd $BRIDGE && python3 validate.py threads/<thread>/r<N>/ask_experiment.json

`--selftest` requires that `threads/` passes and that each file in
`fixtures/invalid/` fires **only the rule its filename names**. Changes on this
side must additionally keep the existing tests and the `python cli.py` paths
working.

The rule this repository is most likely to trip is **R5 (circular evidence)**:
handing AM's own number back as the basis of a `requirements[]` entry while
marking it `hard: true` is refused, because that is AM's value returning as
independent evidence. r2's `sigma_gamma_per_rung` is exactly that case, left
`hard: false` and disclosed in `gaps[]` so that it warns rather than fails.

## Never

- Do not write `confirmed_by`. Both repositories reserve it for a human, and the
  bridge is the one component positioned to forge it (R7).
- Do not summarise or restate a received number. **An import is a mechanical
  copy.** An LLM summary makes the file a new origination point, which principle
  3 forbids.
- Do not guess at a unit. If it does not parse, refuse.
- Do not infer AM's `assumptions` from its values. "A system where a Faxén
  correction applies" follows from no number, so if it was not declared it is
  `unknown` and the document is a draft.
- Do not run a card that has no runner on the trap runner.
- Do not modify the AM repository or load AM's `CLAUDE.md`.

## What the first response should be

Before writing code, report which of items 1–7 **conflict with a principle of
this repository or are larger than they look.** Item 1 especially: confirm how a
foreign document should enter `observation.yaml` (the transcription layer) and
`system.yaml` (L2) without breaking principles 1 and 3 — that is the subtlest
point in this work — and propose a plan afterwards.
