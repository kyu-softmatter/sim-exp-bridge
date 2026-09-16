# sim-exp-bridge

[![selftest](https://github.com/kyu-softmatter/sim-exp-bridge/actions/workflows/selftest.yml/badge.svg)](https://github.com/kyu-softmatter/sim-exp-bridge/actions/workflows/selftest.yml)

A protocol for handing a **question** between two research agents — an optical
microscope ([agentic-microscope](https://github.com/kyu-softmatter/agentic-microscope))
and a Brownian-dynamics simulator
([Brownian-Dynamics-Agent](https://github.com/kyu-softmatter/Brownian-Dynamics-Agent))
— so that each one re-derives its own plan through its own gates instead of
importing the other's numbers.

Four JSON schemas, a validator with thirteen rules, and one worked eight-round
thread in which every number is copied from a real artefact in one of the two
repositories.

```bash
python3 validate.py --selftest      # CI entry point: the rules still bite
python3 validate.py --all           # every document, warnings included
python3 validate.py --resolve \
    --root am=PATH --root bd=PATH   # open the files the citations name
```

Most of this file is the record of what the exercise cost. If you are here for
one thing, it is [Two patterns](#two-patterns-and-what-they-cost) — two failure
modes that recurred across three independently written codebases, and the
procedure that catches the second one.

---

## What crosses, and what does not

Neither `plan.md` nor `plan.json` crosses. Each repository keeps its own plan as
a **local** artefact (`plan_experiment_<title>.*`, `plan_simulation_<title>.*`),
and only a small question card moves:

```
plan_experiment_<title>.md/.json        ← AM's gates produced this. Stays home.
        │
        ▼  ask_simulation.md + .json    ← the only thing that crosses
        │
plan_simulation_<title>.md/.json        ← BD's gates produced this. Stays home.
        │
        ▼  ask_experiment.md + .json    ← back the other way
```

`.md` is the human face and `.json` is the machine face of the **same** document.
They are not independent: on the AM side the JSON is authoritative and the prose
cites it; on the BD side the pipeline is authoritative and both files are
generated (`bdbot/report.py` already writes prose). Drift is possible in only one
direction, and only on the side where a person types numbers.

## Three wire rules

**W1 · Only BD nondimensionalises — in both directions.** AM never emits or
consumes a dimensionless group. AM sends dimensional primitives; BD parses them
with `pint`, reduces with `nondim.py`, and **inverse-maps its answer back into
SI ranges** with `scales.py` before sending. `ask_experiment.requirements[]` is
therefore something AM's gates check directly; `regime[]` rides along for a
human to audit the map. The capability is asymmetric, so the protocol is too.

**W2 · Send the number in the unit it was measured in.** No hand-normalisation
to SI: that is a conversion, and a conversion is an error opportunity on the
side that has no unit library. `pN/um`, `mPa*s`, `g/cm^3` all travel as typed.
Unparseable ⇒ the receiver **refuses** (rule R2); it never guesses.

**W3 · Send primitives, not composites.** `d`, `eta`, `T`, `k_t` — not `gamma`,
`tau_k`, `f_c`. `3πηd` and `6πηa` are the same formula, so shipping the product
is where a factor of two enters with nobody lying; BD's own intake already hit
this as ambiguity `A1` ("is R = 5 µm the radius or the diameter?"). Derived
values may travel in `reference_only`, explicitly **non-binding**, to be read
only *after* the receiver has derived its own.

## The one block that is not a number

`assumptions[]`. "No Faxén wall correction", "`dimensions: 2`", "no detector
model", "1000 non-interacting replicas" — none of these follows from any value,
so they must cross explicitly, each marked `shared | differs | unknown` with a
`worth` (how much it moves the answering quantity). While anything is `unknown`
the document must declare it (rule R4).

Two systems may differ freely in SI values as long as the regime brackets and the
assumptions are declared: agreement across *different realisations of the same
regime* is stronger evidence than agreement between identical ones. The failure
this guards against is the other kind — an undeclared assumption difference,
which looks like agreement and is not.

## T1 · evidence → tier

The sender declares how a number came to exist; the importer derives BD's tier.
Never guessed, because `provenance.py`'s own header names inherited tier 1 as the
dangerous case.

| `evidence` | BD tier | note |
|---|:-:|---|
| `measured` | 0 | on the sending instrument |
| `handbook` | 0 | |
| `computed` | 1 or 3 | **inherits** the worst tier of its inputs — AM's `eta` is tier 3 here because it is computed from an assumed `T` |
| `assumed` | 3 | a standing choice, a default, a placeholder |
| `simulated` | — | not admissible as a tier at all; lands as an external KB entry |
| `round_trip` | — | this number originated in the receiving repository |

## The thirteen rules

Only R1 is a shape rule. The rest are about provenance, which no schema
expresses. `T1` and the severity order both live in `validate.py` as the single
copy.

| | rule | what it prevents |
|---|---|---|
| R0 | the document parses | — |
| R1 | JSON Schema | malformed document |
| R2 | every `unit` parses | `pN/µm` with the micro sign silently becoming something else |
| R3 | no composites in `system_primitives` | the `3πηd` / `6πηa` factor of two |
| R4 | an `unknown` assumption is declared as unresolved | an undeclared assumption difference reading as agreement |
| R5 | a **hard** requirement may not rest on the consumer's own number | circular evidence: three rounds and both KBs agree with nothing measured twice |
| R5b | a consumer-origin quantity carries `evidence: round_trip` | a value that came home being invisible to anything parsing the JSON |
| R6 | cited hashes match a registered revision | a stale import after upstream was corrected |
| R6 `--resolve` | …and that revision is a real file: every registered key against the working tree, every cited `rev` against the blob | a `rev` naming a commit where the path does not exist — [two live instances](#the-resolve-branch--r6-opens-the-file) |
| R7 | `confirmed_by` is never a machine name | the bridge signing off on itself |
| R8 | a shipped `tier` is reachable from its `evidence` | the sender using the receiver's vocabulary with a different meaning |
| R9 | a `simulated` entry is not in a `calibrations` namespace | a path that asserts a measurement that never happened |
| R10 | `evidence_class` is the worst of `evidence_classes` | a citation reading better than the entry's weakest number |
| R11 | a same-origin quantity agrees across rounds | a copy that drifted, propagating at the speed of the protocol |
| R12 | every `gaps[]` entry has a `kind` | "write code", "change method" and "move bytes" being one field |
| R13 | a `ref` is a path, not a path plus a revision | masking R6's own revision branch |

R5 is deliberately narrow. After two rounds the other repository *always* appears
in your ancestry — that is a round trip working. What it catches is a number
coming **home** and being read as independent: soft and disclosed is allowed and
warned about, hard is refused.

## Where an imported number comes to rest

`kb/external/bd/<thread>.r<N>.md` on the AM side,
`knowledge/external/am/<thread>.r<N>.md` on the BD side. The **path** carries the
foreign origin, because both repositories cite by path and a frontmatter field
would not show at the citation site. A simulated `f_c` must never sit in
`kb/calibrations/`, which means "measured on this instrument" — rule R9 refuses
it.

Two properties matter more than the file format:

- **`may_be_gate_threshold: false`** by default. An imported number may motivate
  a design or set a target; a gate that *clears* against it emits a margin that
  reads as locally measured, which is the disease AM hard rule 3 already names.
- **Lifecycle is supersession, not deletion.** "Temporary" imports do not stay
  temporary — a plan cites one, the plan graduates into `kb/decisions/`, and now
  the import is load-bearing in a permanent record. Deleting it dangles the
  citation. Both repositories already have supersession machinery
  (`superseded_by` / `corrected_by`); use it.

## A cited document is not edited — metadata included

R6 checks a **live manifest** against a **frozen citation**. So when the hash of
an already-cited document moves, every citation below it breaks, and **the
obvious response — refresh the hash — is exactly the wrong move.** The refresh
invalidates the next citation down, and that propagates without limit.

It happened, and two parties each did half. Commit `4652273` (the bridge owner)
added `gaps[].kind` to r2 — content preserved exactly as written, hash moved
anyway. r8 broke. The BD session then refreshed the unsuffixed `bd:` key and r4
broke, since r4 cites r2. Refreshing r4 broke r5 and r7. **The shape became
clear on the third try — that is, the obvious fix was tried repeatedly by
someone who could watch it failing.** That is what makes this worth warning
about. The edit caused it, the refreshes propagated it, and neither mistake
alone is a cascade.

**This is not specific to that incident.** `gaps[].kind`, `assumptions_resolved`
and `corrects[]` were all added to a **live thread**, and the first two were
applied retroactively to documents that predate them. R12 and R13 warning
forever on the old ones is not a wart — it is the only thing that records **when
the vocabulary changed**, and a backfill erases that. The r2 edit was the single
case where retroactive application looked free because the content was
preserved, and it was the one that broke.

Two layers:

1. **Do not edit a cited document, metadata included.** A new field belongs in
   new documents. Checking whether a document is cited before editing it is one
   command, and it was not run.
2. **R6 passes a citation matching any registered revision.** The unsuffixed key
   keeps verifying old citations; `@r<N>` carries the revision a later document
   was written against. **Never refresh an unsuffixed key.**

Exempting `fixtures/valid/` from R6 was the same insight one layer down. This is
the round-document version of it.

### A sealed document containing a falsehood is still sealed

There is a second variant of the pull to edit, and it is harder to resist than
the first. Not "a warning text implies a task" but **"the document contains
something untrue, therefore fix the document"** — BD's r8 cited a file at a
revision where it did not exist. The hash was correct throughout; only the `rev`
pointed at nothing. Leaving a falsehood in place reads as the negligent option.

The remedy has **two tiers**, and without the distinction the rule defeats
itself: **a remedy more expensive than the temptation does not get followed.**
One question decides which: *does any downstream conclusion change?*

| | where the falsehood is | remedy | cost |
|---|---|---|---|
| **it changes** | the claims. r2's `achieved_precision` — load-bearing, six dependents | a **new document** carrying `corrects[]` | one round document. Worth it |
| **it does not** | the citation apparatus. r8's wrong `rev` — one token, no conclusion moves | **register both revisions** in the manifest (unsuffixed stays where existing citations point, `@r<N>` carries the current one) | one line |

| **it does not, and the manifest cannot reach it** | a wrong `rev` *inside a document*. `--resolve` git-resolves it and never consults the manifest for that branch, so **no key you can add changes the outcome** | correct the string in place — if nothing cites the document | one line, in the document |

Both of the first two keep the document sealed; they differ only in publication
cost. Demanding a full `ask_experiment` for a one-token `rev` is a rule that
will not be kept.

**The third row was missing and the AM session found it by trying to apply the
table.** It was told to register a `@r<N>` key for r9's dead rev and correctly
did not: the wrong thing was a `rev` string inside r9, the manifest key for the
target was already right, and `--resolve` fails that citation by asking git,
not by asking `hashes.json`. A remedy has to reach the defect, and the two-row
version of this table silently assumed every citation defect lives in the
manifest.

**It generalises past citations**, and AM named the nearest relative: it is the
same failure as `plan-check` validating a plan's sections and saying nothing
about its numbers. The check existed, **so nobody asked what it covered.** That
is Pattern 2 arriving from the remedy side rather than the rule side.

### Sealed by commit is not sealed by citation

Both had been called "sealed" in conversation, and **only the second one
cascades.** The rule in this section is *a cited document is not edited* — the
test is "is it cited?", not "is it committed?". r9 was committed and cited by
nothing, with its hash in no manifest key, so correcting it in place moved
nothing anybody depended on. r7 was the opposite and is why the cascade rule
exists.

The distinction was already correct in this file and wrong in the messages
around it. Neither side gets credit for that: both were carrying a paraphrase,
and AM's happened to match because it had just implemented against the rule
rather than because it read more carefully. **What sharpened the question was
having to answer "may I edit this file" three times in one afternoon** — being
made to act on a rule repeatedly forces it into the form that has an answer, in
a way that reading it does not.

**The test has since refused something, which is the evidence it is a test.**
r8 states "7.2 to 9.5 %, which is 1.8× the tolerance" — but a range is not one
ratio (7.15/4.48 = 1.6, 9.48/4.48 = 2.1, and 1.8 is the middle). Applying the
question: no downstream conclusion changes, since 1.6 and 2.1 both exceed 1 and
the conclusion is "outside the tolerance". Citation-apparatus grade, so r8 stays
sealed and no round is published. A test that only ever says "do more" is not
deciding anything.

Recorded in the order it was reached, at BD's request: BD edited first, R6 caught
it, and the repair turned out to be the right remedy. The lesson is not that it
knew the cheap path — it is that **the cheap path was invisible from where it
stood**, the same shape as `rev` being invisible to both sessions when they
independently invented `@r<N>`.

## Citing a document at a revision

R13 exists because a workaround outlived the constraint that made it necessary,
and because **two sessions reached the same workaround independently rather than
by copying**. Both wrote it as if it were the convention rather than as a
workaround. Two people reaching for the same wrong shape is weak evidence that
the idea is bad and strong evidence that **the right shape was undiscoverable**.
So it is written out here once, with an example:

```json
{ "ref":  "am:kb/plans/2026-09-15-drag-calibration-stiffness-vs-size.md",
  "rev":  "9f971a8",
  "hash": "sha256:58cfc405231a2970" }
```

- `ref` is **a path and nothing else.** No `@r<N>` in it (R13).
- `rev` names the revision — a commit sha is best, a branch name is acceptable.
- `hash` pins the content at that revision.
- `<ref>@r<N>` is a **manifest key form only**, used in `hashes.json`. R6 passes
  a citation matching **any** registered revision, so a later round **adds** a
  key and **never refreshes** the unsuffixed one.

A path-only ref is ambiguous, and this thread's own plan file proved it:
`58cfc405` on `main`, `514da4a0` on `worktree-work-2026-09-16`, and **absent
from `version2`**. Three answers to one ref leaves R6 not knowing what it checks.

### `rev` is itself a citation that can rot

`rev` was added to make the citation apparatus verifiable. Then a `rev` pointed
at nothing — BD's r8 cited an uncommitted file at `rev: 07d1048`, **with the
content hash correct throughout**. The field added to prevent that failure had
it.

And R6 could not catch it: it checked a recorded hash and **never a file on
disk**. That division was called deliberate — the hash pins content, the `rev`
is for a human to go look — and the cost was stated rather than implied:
**`rev` was an unverified field.**

**CORRECTION (2026-09-16): it is verified now, and the reason the old text was
wrong is that the correction above was applied by hand.** `813fcf2` fixed the
dead `rev` in r8's `.json`. The `.md` twin two files away carries the same ref
at the same dead rev and was **not** fixed, because nothing could see it. That
is the second instance, it was sitting in the tree while the first was being
repaired, and two instances is this repository's own bar for a rule. See
[the resolve branch](#the-resolve-branch--r6-opens-the-file) below.

The suffixed-key convention has now absorbed three things that would each have
cascaded: r2's metadata backfill, r8's hash move, and this `rev` correction. Each
time the unsuffixed key stayed where existing citations point.

### The resolve branch — R6 opens the file

```bash
python3 validate.py --resolve \
  --root am=~/Desktop/agentic-microscope/.claude/worktrees/work-2026-09-16 \
  --root bd=~/Desktop/Brownian-Dynamics-Agent
```

R6 compares a citation against `hashes.json`: **both sides of that comparison
are strings this repository wrote.** The resolve branch is the missing half —
it opens the working tree for every registered key, and `git show`s the blob at
every cited `rev`. Not a fourteenth rule: R6 already claims a hash is the
identity of an upstream artefact, and an identity that resolves to nothing is
not one.

On the first run against both clones — 45 resolutions, **two of them
unresolvable, and both real**:

| | what |
|---|---|
| `rev_absent` | `r8/kb_entry_for_am.md` cites `bd:verify/verify_ladder_tolerance.py` at `07d1048`, **where the path does not exist**. Its `.json` twin was corrected in `813fcf2`; this one was not. |
| `rev_mismatch` | `r4/ask_experiment.json` cites r2 at `rev c288df6` with `hash 683eae8f`. At `c288df6` the blob is `2bbab020`; `683eae8f` is that file at `b96092b`, **four commits later**. The two halves of the citation name different moments, and R6 passed it because the hash is a registered key. |

Neither is repaired here. A cited document is not edited by the side that did
not write it, and the `.md` fix also moves a hash AM's import registers — the
owning session does that, which is the same boundary `confirmed_by` draws.

**What it cannot do, stated rather than implied:**

- **`am:`/`bd:` roots are never defaulted.** No sibling-directory guess: the
  answer must not depend on where somebody cloned. Unconfigured is reported as
  `no_root` and counted, and a run that resolved *nothing* exits non-zero —
  "0 checked, 0 failed" is the vacuous pass this repository keeps writing down.
- **Rootless, it still covers `<side>:bridge/...`** — those paths live here, and
  that is 11 resolutions with no configuration. The `rev_mismatch` above is one
  of them, so it is reachable from CI.
- **8 citations carry no `rev` at all.** They resolve to nothing by
  construction; `no_rev` counts them instead of calling the run clean.
- **A directory ref had no recipe, and now has a declared one.** A directory
  has no bytes of its own, so `bd:runs/trap-2d-5um__a5ef4f45d589` was reported
  `no_recipe` rather than given a convention. The recipe was not invented
  afterwards either — it was already written down twice and read by nothing:
  the three citations of that ref carry `"field": "metrics.json"`, and the
  registered value is that file's hash at the cited rev **and** at HEAD. So the
  resolver reads `field` when a ref resolves to a directory, the manifest
  records the same thing in `_subject_of`, and `no_recipe` still stands for a
  directory nobody declared. Nothing was re-registered.

**The first run also produced three defects that were the resolver's own**, and
that is the part worth keeping: `path@r3` opened as a filename (R13's form, in
a ref the validator already warns about), `git show` on a directory hashing the
*tree listing* into a confident `rev_mismatch`, and the one key that
deliberately holds another artefact's hash reading as a dead rev. Three of six
"findings" were the checker. They are now cases in the selftest, because the
hour that separated them from the two real ones is the cost of rediscovering
them.

`tools/rehash.sh` — named in `hashes.json`'s own `_comment` since the day the
file existed, and **absent for all of it** — is the same failure one level out:
R6 resolves the artefacts the *documents* cite and never looked at the ones the
*manifest* cites. It exists now, it delegates to `validate.py` rather than
carrying a second copy of the hashing recipe, and it **prints and writes
nothing**: the round number in `@r<N>` is a human's to name, and refreshing an
unsuffixed key starts the cascade the revision convention exists to stop. The
selftest fails if a `tools/…` path named in the manifest's prose is missing or
not executable — checked by deleting it and by clearing its executable bit.

That last one is declared in the manifest instead of in prose. `_subject_of`
maps `am:bridge/.../r1/ask_simulation.json` to AM's plan — r1's ask was
distilled from it and AM held no separate file — and the proposals file had
**predicted** that the first regeneration would read the key as a false "moved
upstream". It was right; this was that regeneration. Redirected rows print even
when they pass, because a quiet exception is how the prose note got forgotten.

The selftest cannot use the real roots, so it builds a git repository in a temp
directory and requires **every one of the eleven statuses** to be produced by a
case — `_coverage_checks` applied to a rule whose input is a filesystem. Seven
deliberate mutations were checked to turn it red: drop the `rev_absent` branch,
report `advanced` as ok, make the hash comparison `if True`, stop stripping the
`@r<N>` key suffix, stop refusing a tree, let an unparseable document pass
silently, and add a status with no case. The last two are this repository's own
two patterns aimed at its newest code, and the `unread` status exists because
without PyYAML every `.md` citation would drop out of the run and the summary
would still read clean.

**The resolver prints which checkout it opened, because `absent` is a branch
before it is anything else.** Pointing `--root am` at this repository's default
worktree rather than at its worktree branch turns six real citations into six
false errors, and the first run of it here did exactly that. It errs in the safe
direction — false errors, not a false pass — but nothing in the output said
which checkout had been opened, so the reader had to remember. Now each root
prints as `path [branch @ sha]`, and any `absent` count is followed by the
branch that produced it. Printing the invocation beats remembering it, which is
the same move as everything else here.

## A correction does not wait its turn

Round parity (odd = experiment, even = simulation) governs **new questions**
only. The side that discovers its own earlier answer was wrong does not wait for
its turn — it is the only party that could have found it. It carries
`corrects[]` and `status: supersedes_prior`; the corrected document becomes
`status: corrected`.

**`corrects[].downstream` is not left empty.** A correction that does not name
its dependents leaves them silently wrong, which is worse than the original
error because it now looks reviewed. What happened on 2026-09-15 was exactly
that shape: BD found r2's +1.17 % to be an estimator bias rather than physics,
and r2's `T_obs >= 32.3 s` requirement existed *precisely because* that 1.17 %
"was measured at `T_obs/tau_k = 2000`". A bias does not shrink with `T_obs`, so
the requirement's basis was gone — and at that moment AM was already drafting r3
on top of it.

**`downstream` turned out to be load-bearing for R11**, which was designed two
commits later. The field was required on an argument alone; R11 is now the
mechanism that makes that argument true rather than advisable. r4 is clean
*because* it filled `downstream` in — had it not, `blur_on_var_x` would now
error across r1 and r4. Two things designed independently met.

## R4 does not look at `status`

An unresolved assumption must be **declared as unresolved** — not "the document
must be a draft". Those are different claims, and fusing them blocks a
correction: `supersedes_prior` exists so a fix does not wait, and requiring
`draft` alongside it means **a correcting document cannot carry a newly found
unknown.** That happened in r4 on 2026-09-15, and BD moved the item into
`findings[]` rather than weaken it — filing an undeclared assumption as a
disagreement, which is what R4 exists to prevent.

The cause did not need a carve-out. **`status` was carrying two orthogonal
facts**: where a document is in its lifecycle, and whether its assumptions are
all declared. They are separate now.

```yaml
assumptions_resolved: false     # works with any status
status: draft                   # the older form, still valid (back-compatible)
```

`fixtures/valid/c6-correction-with-unknown.json` is the regression guard for
that loosening. `fixtures/invalid/` proves a rule still bites; `fixtures/valid/`
proves it does not bite what it should allow.

## `evidence` is authoritative; `tier` is non-normative

The sender writes `evidence` only. The receiver **derives** the tier and ignores
whatever is on the wire, because the field is not derivable in general —
`computed` inherits the worst tier of its inputs and the wire does not carry the
inputs. And it drifted silently: across r1–r5 one `computed` class shipped as
tier **1, 2 and 3**, and every tier-2 case descended from six values in r1 that
were copied forward into three later rounds. Tier 2 in BD's scale means
"literature, unverified", which is not what a model output from
`trapping/goa.py` is — **the sender was using the receiver's vocabulary with a
different meaning and nothing checked it.**

R8 warns on a tier not reachable from its evidence. Do not put `tier` in new
documents.

## Several kinds of evidence in one entry is the normal case

A single `evidence_class` becomes a lie. r1's import carried `d` and
`pixel_size` (genuinely measured) alongside `T` (assumed — AM's own precondition
P3 blocks on a thermometer), `eta` (computed from that assumption) and `k_t` (a
model output), while the frontmatter said `measured`. The body table said so
correctly, but **a citation surfaces the path and the frontmatter, not the body
table.**

Use `evidence_classes: {symbol: evidence}` and set `evidence_class` to the
**worst** entry in it (R10; order `measured = handbook < computed < simulated =
round_trip < assumed`). Keeping only the worst and discarding the map would throw
away the fact that `d` and `pixel_size` really are measured.

## R11 — a copy that drifted across rounds

The two defects this thread actually produced are one shape, not two accidents.
`2 D t_exp / 3` was wrong in r1 and still wrong three rounds later, because every
later document had copied it. Six `tier` values in r1 were unreachable from their
own `evidence` and propagated into r2, r3 and r5 the same way. **Each document
was careful and nothing checked between documents.**

`origin` is the discriminator:

| | meaning | R11 |
|---|---|---|
| same symbol, **same origin** | the later one is a **copy** | they must agree — disagreement is an **error** |
| same symbol, **different origin** | both sides derived it **independently** | reported, never an error. AM's `f_c = 9.9 Hz` against BD's `9.86 Hz` is a round-trip check passing |

A disagreement named in any document's `corrects[]` is a declared supersession
and is exempt.

`R11_TOL = 1e-3`. Re-deriving `kT` in a later round and printing one more figure
moves it by ~1e-4 relative; the drifts this rule exists for are factors (`2u/3`
against `u/3` is 2×). Two decades above the noise this thread actually produced,
three below its smallest real drift.

## What R5's soft warning bought

r2's `sigma_gamma_per_rung <= 3 %` was AM's own 400-realisation numpy estimate
coming home, so R5 warned; it passed because it was `hard: false` and disclosed
in `gaps[]`. **Four rounds later that number turned out to be holding up the
experiment's primary route** — r5's 29.1 % is the cross-check path, the plan runs
on the drag slope `alpha = gamma*v/x_eq`, and the slope's per-rung precision has
never been measured by either side. The ~3 % the entire error budget rests on is
that unverified numpy figure.

What is worth recording is not the judgement of whoever applied the label —
`hard: false` was **forced** (R5 errors otherwise) and `gaps[]` was the only
honest place left. It is the **shape**: the rule could not tell that
`sigma_gamma_per_rung` was load-bearing, only that it had **come home
undeclared**, and four rounds later that was enough. A warning that names a
number without ranking it beat both sides' ranking, because both spent four
rounds on `f_c` while the primary route was the drag slope.

That is the argument for leaving soft warnings in place. A rule that cannot rank
can still point, and pointing alone paid.

## A conclusion relayed in chat is not a source

**That is why this bridge exists.** And yet once three sessions could message
each other, the bridge owner started relaying findings in chat — which is
exactly as convenient as it is corrosive. A claim with no hash, no ref and no
revision cannot be audited later.

The AM session drew the line first. Having reached BD's wall conclusion
independently, it wrote the plan's D-6 as **its own repository's derivation and
said so in the paragraph**, citing the definition of `k*` rather than citing
either peer. Not doubt about the physics — a plan whose provenance chain reads
"a peer told me" **cannot be audited**.

- **Messages are for coordination and protocol.** Who owns what, what has been
  pushed, which rule changed and why.
- **Findings cross as round documents.** `ask_*.json` plus hash plus `rev`. That
  is the only auditable form.
- **A relayed finding is a prompt to go look, never a source.** The receiver
  re-derives it or waits for the document. AM re-running the `k*` arithmetic was
  the correct response (21219 against 21221 in r2's table, plus the check that
  the expression carries `k_t`, `d` and `kT` and **no drag**).

- **Operator consent does not relay either.** The bridge owner passed on an
  operator ruling, and the BD session went to its own user for it instead of
  acting — correctly. The reason is a property of the **channel**, not of
  anyone's reliability: a relayer cannot distinguish "the operator said yes"
  from "the operator was asked something slightly different", and the cost of
  being wrong is asymmetric. So the relay cannot carry authority however
  trustworthy the relayer is. It then laid out for its user exactly what
  publishing exposed before asking, which is what makes the answer informed
  rather than assumed.

  **And this rule states its own limitation, because it has to.** It is
  `confirmed_by` being human-only, one layer out — but R7 can enforce the inner
  case, since a machine name in a file is detectable, while the outer case has
  no file to inspect. It can only ever be a convention. Every finding in this
  document says an unenforced convention decays, so this one is written down
  knowing that is its likeliest end, and the mitigation is that it is short
  enough to re-read.

The bridge owner is not exempt. Writing down why a rule changed is coordination;
moving the thread's physics into a message is a bypass.

## Blocks have different readers — `gaps[]` does not reach the operator

`gaps[]` was added to `ask_simulation` on the argument that "a precondition
written as a checklist item reads closeable". AM used that argument more
precisely: **the place that reads closeable is the place to fix**, and `gaps[]`
is read by the other agent, not by the operator standing at the instrument with
the plan open.

So it is not either/or. One fact gets two homes: `kind: needs_data_transfer` in
the bridge's `gaps[]`, and in the acting repository's own precondition, *blocked
on a data transfer rather than on analysis time*. AM's P7 is that shape.

## Shared-clone hygiene — three rules

Three sessions share one clone, and every commit carries the same git author, so
**the history cannot say which side wrote a thing.** When the authorship of a
round's record is ambiguous, the ownership table is unverifiable after the fact.

1. **Do not use `git commit -am`.** It lands whatever the other side has staged.
   Use `git commit --only <paths>`. This nearly happened: `hashes.json` and
   `r5/kb_entry_for_am.md` were staged by AM at the moment the bridge owner went
   to commit.
2. **Leave the other side's untracked files alone even when they are in the
   way.** `git add -A` lands them. This did happen: `84b1530` committed AM's
   `r4/kb_entry_for_am.md` — byte-identical, nothing lost, but the authorship of
   that round's record became ambiguous.
3. **Say which side you are in the commit message**, since the author field
   cannot:

       Bridge-Session: am | bd | owner

`--selftest` does not check this. It is not a checkable property, and a
convention is the honest form.

## A skipped rule is not a passed rule

Under `--selftest`, a missing `jsonschema` / `referencing` / `PyYAML` is an
**error, not a warning**. BD's `simulation_bot` interpreter has no `jsonschema`,
and `--selftest` run there printed "selftest clean" having never executed R1. A
checker that reports clean with a rule switched off is the exact failure both
repositories keep writing down. The selftest now prints its interpreter path on
the first line.

It also **refuses to pass on nothing.** With every fixture and every thread
deleted it used to print "0 fixtures, all pinned" and "selftest clean", exit 0 —
vacuously true. BD's `ci.yml` carries the same guard for a shell loop (`if [
"$checked" -eq 0 ]; then echo "::error::no SEALED.sha256 found -- this job
silently passed on nothing"`), because a seal job that finds no seals is green.

## A rule that fires on documents nobody may fix must say so

R8, R12 and R13 produce **permanent warnings** on old documents, all for the same
reason: those documents were written before the field or convention existed, and
the standing warning is **the only record of when the vocabulary changed**. It is
not debt.

But if the warning does not say that, **the first reader treats it as a task and
edits a sealed file — which is the cascade again, one layer up.** That is how it
actually happened: R12 said only that a `gaps[]` entry had no `kind`, and the
bridge owner read it and backfilled r2.

So a requirement on rule *wording*: **if a rule fires on documents that cannot be
fixed, its own message says "leave sealed documents alone; carry the field in new
ones."** R13 was written that way from the start; R8 and R12 were corrected
afterwards.

BD's sharper statement of why this outranks the cascade lesson: a rule that
describes a defect without naming who may repair it does not merely fail to
prevent the edit — **it recruits the next careful reader into making it**,
because being careful looks like clearing the warning. The cascade needed two
parties and a coincidence; this needs one conscientious reader.

---

## Two patterns, and what they cost

Eight rounds established some physics. Two recurring failures are more
transferable than any of it.

### Pattern 1 — estimating what was cheap to measure

Same shape every time: a value is estimated, propagates through careful
documents, and collapses the moment somebody measures it. The measurement was
cheap throughout.

| # | what was estimated | what measuring returned | survived |
|---|---|---|---|
| 1 | r2's `f_c` precision +1.17 % — "physics" | the estimator. Exact OU through the same estimator gives +0.8–1.2 % | 2 rounds |
| 2 | r1's blur term `2 D t_exp/3` | the exact OU boxcar factor is `u/3`. A factor of 2; `2u/3` rejected at 16–358σ | 3 rounds |
| 3a | r1's `sigma_gamma_per_rung <= 3 %` — a numpy toy model, and the **primary** route | 7.2–9.5 % simulated, i.e. **2.4–3.2×**, against a tolerance of 4.48 %. Still unmeasured on the instrument: that is P7 | 7 rounds, ongoing |
| 3b | r3's `sigma_f_c_single <= 3 %` — the **cross-check** route | 29.1 %, i.e. **9.7×** | 2 rounds |
| 4 | validator warning volume — "not yet worth acting on" | already 11 repetitions, 11,787 characters of output | immediately |
| 5 | r8's `rev: 07d1048` — a file assumed committed | the file does not exist at that revision. Hash correct, `rev` pointing at nothing | several commits, while pushed |

**3a and 3b were one row until BD caught it**, and the mechanism of that mistake
is worth more than the correction: two different quantities are each compared
against a 3 %, so the ratios (2.4–3.2× and 9.7×) attach to the wrong one
without anybody being careless. Splitting the row removes the confusion
structurally instead of by careful wording, which is the same move as everything
in [the general form](#the-general-form).

Instances 4 and 5 were raised by the BD session against itself — **the party
that had found 1 through 3.** That is the point: the failure is not carelessness,
it is that **an estimate always looks sufficient at the moment it is made.**

The rules this repository grew point the same way. R8, R11, R12 and R13 all catch
"a number moved between documents without being checked."

Nothing checks whether a `rev` resolves. R6 verifies the hash and is satisfied,
which is the right division of labour — but a `rev` can be silently wrong, and
one was. **One instance is not a rule**, so no rule was written; it is recorded
here so a second is recognisable. If it recurs, the cheap form is a `--selftest`
check that every `bd:` rev is a real object in the BD repository — but that
couples the validator to two external layouts, which may cost more than it buys.
BD's failing case was an external `bd:verify/...` ref, so a bridge-internal
subset would not have caught it.

### A derived count is a merge-conflict magnet

Deriving a documented number instead of typing it fixes staleness and creates a
new failure in its place. BD's repository had 48 of 102 documented counts wrong,
so it made them derived and gated — and then the gate fired twice in one
afternoon, both times correctly, for two different reasons:

1. **A branch predating the gate.** CI runs on the merge commit, so the new gate
   met a branch's additions: verify scripts 81→92, KB entries 148→157. The
   repository already had the enforcing version and the branch had been cut
   before it landed — which is why that PR's "known and not fixed: the header
   says 1008 passed" was wrong about its own repository.
2. **Two writers re-measuring the same derived field.** `main` moved again
   mid-fix and conflicted on exactly the same count lines, because both sides had
   independently re-measured the same numbers. The resolution is re-measuring —
   take `main` and re-run the fixer — not picking a side. Its tool refuses to
   guess how to split `passed + skipped`, which is the right refusal.

The second is the durable one, and it has a design answer rather than a
procedural one: **partition a derived file by owner so that two writers never
compute the same field.** `hashes.json` here is exactly such a file — two
sessions append to it every round — and the ownership rule assigns keys by
prefix (`am:` to one side, `bd:` to the other).

That claim was checked rather than assumed, and it needed a correction. Across
13 commits touching the file from both sides, 31 keys split `am:` 13 / `bd:` 18,
**no conflict marker was ever committed** — but the prefix partition only
prevents a **semantic** conflict, in that neither side can overwrite the other's
key. It does not prevent a **textual** one: in insertion order both sides append
to the end of the same JSON object and land on adjacent lines, which git
conflicts on even though the keys are disjoint. It had not happened because the
writers were never concurrent — serialisation, not design.

Sorting the ref keys fixes it in one line: `am:*` and `bd:*` then occupy
disjoint contiguous regions, so an append by each side touches a different part
of the file. `--selftest` now refuses an unsorted manifest, because otherwise
the fix is a convention that rots.

So there are **three axes**, and only the first two were deliberate:

| convention | prevents a collision in |
|---|---|
| suffixed keys `<ref>@r<N>` | **time** — a later revision does not invalidate an earlier citation |
| prefix partition `am:` / `bd:` | **ownership** — neither side computes the other's field |
| sorted keys | **the file** — two appends do not land on the same line |

### Noted, not promoted — conclusion right, reason wrong

Two instances, which by this document's own standard is worth writing down and
not worth reframing anything around: r2's +1.17 % (the value is what that
estimator gives; the interpretation was wrong) and the claim that
`hashes.json` had never conflicted *because* of the prefix partition (it had
never conflicted, and the reason was that the writers were never concurrent).

What makes it possibly distinct from Pattern 1 is **detectability**, not the
error. A wrong number collapses the moment anyone measures it. A wrong reason
**survives measurement intact**, because the measurement confirms the conclusion
and never touches the reasoning — which is why both of those sat for as long as
they did while being checked repeatedly. If a third arrives it gets its own row
under that name.

### Pattern 2 — a check that exists and is not wired to what it describes

A different failure, and by the end it had more instances than the first.

| check | what it claimed | what it actually read |
|---|---|---|
| the bridge's `chain` | "required by R5" | the string appears zero times in `validate.py` |
| AM's `plan-check` | the shape of a plan | no link resolved at all — three `kb/decisions/` citations pointed at entries existing only on another branch, and those three were the sources of its ROI, its exposure and its 520 fps |
| BD's `health.gate()` | (recorded in BD's own CLAUDE.md) | reachable only from a sibling tool, so no run ever gated itself |
| BD's `bd-intake` §2.1 empty-goal blocker | refuses a case with no goal | written twice, enforced zero times; 2 of 8 cases walked past it and produced 85 runs |
| BD's `A4` grep | a real check | seven false hits, never a check |

Five across three codebases, written independently by the same person. **So it is
not a record one project happens to hold — it is the default**, and the next
person should expect it rather than feel caught out by it.

Two of them are in one module, and the precise version of that is stronger than
"found twice": `health.gate()` was found by **reading the call graph**; the
`Guard` aborts were found by **coverage**. Neither method finds the other's
instance. Reading does not reveal that a reachable, correct guard is never
exercised, and coverage does not reveal that a correct function has no caller at
all — **because an uncalled function has no lines to miss.** Two methods, two
blind spots, one module.

In all of them the check passed and passing meant nothing. Pattern 1 targets
numbers and collapses the moment anyone measures. Pattern 2 targets the checks
and is **invisible because it passes** — there is no moment at which it announces
itself. So the defences differ: the first needs someone to run the measurement,
the second needs **someone to make the rule fail on purpose.**

### Pattern 3 — a tool that cannot match its target

Promoted at three instances, on the standard used for everything else here.
In each, a tool was asked a narrower question than the one being answered, and
**the narrowing removed the evidence that would have shown the answer was
wrong.** A tool that cannot match its target produces output indistinguishable
from success.

| the tool | what it could not match | what it looked like |
|---|---|---|
| a `perl -ne '/\p{Hangul}/'` scan of this repository | Hangul | zero lines in every file — "already English", with three files and hundreds of lines present |
| `grep -E "rev_absent\|rev_mismatch\|resolve: "` on a `--resolve` re-run | a traceback | the finding it was looking for, while the crash it was checking had been fixed upstream |
| AM's `_check_citations`, reading inline `[text](target)` only | reference-style links | **`plan-check` reporting clean on an unchecked citation** |

**The third is a different severity and that is the part to keep.** The first
two were one-off looks, and a stale look costs one message. The third was a
**committed check**, so it would have gone on reporting clean indefinitely, and
the plan it passed would have carried a dead citation with a green tick on it.
Same shape; a nuisance in a scan and a permanent lie in a checker. It was also
sitting *inside the citation rule* — the exact failure that rule exists to
catch.

**How it differs from Pattern 2**, in AM's sharper form: there the check was
never wired to anything, so it could not have fired. Here it was wired, it
fired correctly, and its **field of view** excluded the case.

> Pattern 2 is answerable by asking *"does this run?"*
> Pattern 3 is answerable only by asking *"what can this see?"* —
> and that is a question nobody asks of a passing check.

**The defence AM used is the transferable part: refuse the form rather than
grow the parser.** A plan has one linking style; supporting two is two things
to keep checked, and refusing the second keeps the check's **coverage equal to
its claim**. The test is named for the failure rather than for the shape.
Growing the parser would have widened the field of view once; refusing widens
it permanently.

**But the phrasing hides a cost.** Refusing keeps coverage equal to the claim
by **narrowing the allowed input**, not by widening the check. That is free
only while nothing uses the refused form — no plan writes reference-style
links — and it is not free in general. Had the form been in use, "refuse" would
have meant "break every existing document", and the honest move would be to
widen and then state what the wider field of view still excludes. So:

> **Refuse where it is cheap, widen where it is not, and in both cases write
> down the remaining boundary.**

### The tell: a comment that names a boundary and guards nothing

Pattern 3 is hard to find because a passing check gives no prompt. It has a
marker that is **greppable in a way the pattern itself is not** — a comment of
the form *"X is not used here, so this does not handle X"*. AM wrote exactly
that comment in the same commit as the rule, where it read as diligence: it
names the gap, after all. What it records is that the author **saw the boundary
and left it unguarded**, with nothing that fails the day the assumption
expires. Three of the day's instances had a note like that nearby.

**The refinement that makes the grep usable**: the tell is not a comment naming
a boundary — those are good and this file is full of them. It is a comment
naming a boundary **with nothing that fails when the assumption expires**. Run
against this repository in three passes with different patterns, since one
regex declaring a repository clean is Pattern 3 checking for Pattern 3:

- `validate.py:48` — *"R2. A deliberately small unit vocabulary … not a unit
  system"* reads exactly like the tell **and is not one**: R2 refuses an
  unlisted token, so the boundary is enforced by the refusal that names it.
- `validate.py:789` (`advanced` deliberately not an error), `:612` (R9's
  measured-only namespace), `:1288` (`bd` absent on purpose, to exercise
  `no_root`) — each names a boundary that some rule or fixture holds.

Nothing here matched. The near-misses are the useful output: they are what the
guarded form of the same sentence looks like.

### Checkability beats care

The single statement above all the rules that follow from it. The failure mode in
both patterns is neither dishonesty nor carelessness: **a writer cannot see their
own blind spot**, so care scales badly and checkability scales. Every mechanism
these three repositories accumulated is an instance, and none of them makes
anybody more careful:

- `rev` on a ref — the reader can resolve the citation instead of trusting it
- a message fragment instead of an exception type (`expected.json`)
- `ast.unparse` of a node instead of the raising line's source text
- "the dict compares equal, no hash appears an odd number of times" instead of
  "no values changed" — one is checkable in a command, the other asks for trust
- `--selftest` refusing to pass on nothing, instead of a reviewer noticing

And the operative half of it: **change the shape so the mistake has nowhere to
live**, rather than being more careful in the same shape. Three times in one day
the fix took that form, and each time the alternative was a person promising
something:

| the fix | the alternative it replaced |
|---|---|
| two table rows for two quantities | careful wording keeping them apart on one row |
| sorting `hashes.json` | agreeing not to append concurrently |
| `expected.json` pinning a message fragment | trusting that a filename names the branch that fired |

Going to the source rather than the relay is the same discipline applied to a
conversation, and it is worth noting what that bought: BD reported a wrong ratio
in the table, and reading r8 instead of the message found that **the quantities
were crossed** — a different and larger error than the one reported. BD had
stated its ratio correctly and would not have found that.

### The general form

1. **One negative fixture per rule.** That rule and only that rule may fire.
2. **Inline branch checks wherever a rule has more than one path.** R6's five
   were the **minimum**, not thoroughness — its revision branch was unreachable
   in the live tree until BD removed its own workaround, so four of five would
   have looked fine while one was dead.
3. **A negative fixture must assert the failure's *identity*, not that a failure
   occurred.** BD's harness printed `12 fired, 0 did NOT` while 7 of the 12 were
   `TypeError` from its own wrong call signatures — **a checker passing for the
   wrong reason, inside the script written to find checkers that pass for the
   wrong reason.** This repository had the same hole one level finer:
   `--selftest` required the right *rule*, and R6 has four branches, so a fixture
   could drift to the wrong branch and still pass. `fixtures/invalid/expected.json`
   now pins a message fragment per fixture, and breaking one on purpose yields
   `R6 fired for the WRONG reason`.

Clause 3 arrived last and matters most. Clauses 1 and 2 catch a check that is
**dead**; clause 3 catches a check that is **alive and verifying the wrong
thing**. The second is worse, because passing looks like evidence. And the
ad-hoc form — a handful of individual calls — is what anyone applying the
procedure reaches for first, and is the form that can pass vacuously.

**The same coarse-key mistake appeared three times**, always as the obvious key:
rule-level instead of branch-level (the bridge's fixtures), exception-type
instead of message (BD's negative tests), and the raising line's source text
instead of the full expression (BD's AST inventory, where two branches of
`Guard.check` both read `raise RuntimeError(` and collided). Each time the
coarser key made two distinct failures look like one.

### What the general form then found

`chain` was found by reading, and **discovery cannot itself be a check** — that
is BD's point and it stands. But the general form is a **procedure**, and it
converted "found by reading, which cannot be relied on" into findings nobody had
to notice:

- **Here:** enumerating error-producing rules with neither a negative fixture nor
  a live firing returned **R0, R1, R9, R10**. All four passed once fixtures
  existed — they were never dead, nobody had ever seen them run. That enumeration
  is now a check rather than a one-off: any rule that can raise must have a
  negative fixture, derived from the source, verified forward with a throwaway
  `rep.err("R99", ...)`.
- **In BD's repository:** 154 error sites, **88 never executed** under a
  1440-test suite, 38 of them in gate modules — including `health.Guard`'s
  `[NUM_NONFINITE]` and `[NUM_DIVERGE]` aborts, whose entire job is to stop a
  diverging run.

So: **discovery needs a reader; coverage does not.**

### Why two agents found more than one would

Not because either was sharper. **A shape crosses between repositories and a
surface does not.** Each of the findings above happened because one side handed
over a form and the other applied it to a surface the giver could not see:

- the coverage audit here produced R0/R1/R9/R10 → BD ran the same enumeration on
  `bdbot` and got 88 of 154
- measuring the warning volume here → BD measured its own and found
  "1 passed, 1 skipped, exit 0"
- naming rule-level-versus-branch-level here → BD found two branches of
  `Guard.check` colliding on the raising line's source text

BD's own narrowing of the claim is the transferable part, and it is smaller than
the credit: **it was willing to run the thing on itself immediately, and three
times the answer was worse than it expected.** That is cheap, and it is the only
reason those surfaces were looked at. The rule made them findable; running it
unprompted is what found them.

### Open, and not to be mistaken for done

Recorded as trades rather than as claims, at BD's request:

- **26 of the 38 unfired gate paths in `bdbot` are still unobserved**, classified
  `known_unobserved` rather than exercised. 12 of 38 wired beats 38 of 38 in a
  script nobody runs, which was the previous state — but it is a trade and
  stating the 26 is what keeps it one.
- **BD's inventory guarantees classification, not exercise.** It has no
  CI-enforced negative fixture per rule the way `fixtures/invalid/` here does: a
  new gate cannot arrive *unclassified*, but it can arrive *unexercised*. That
  is a weaker guarantee than this repository's, and "source-derived check" reads
  like parity when it is not.
- ~~**Here: a `rev` is never resolved.**~~ **Closed 2026-09-16** by R6's
  [resolve branch](#the-resolve-branch--r6-opens-the-file), after a second
  instance appeared — the `.md` twin of the document whose `.json` had just
  been corrected by hand. What replaces it is smaller and still open: **two
  real unresolvable citations**, **10 citations with no `rev`**, and the branch
  is **not in CI** even though its rootless half would cover one of the two
  findings. The directory-ref recipe that was open here is
  [closed](#the-resolve-branch--r6-opens-the-file) — declared, not invented.

### And the gate was not pointed at the thing it was built for

Both sides, different failures, same consequence.

- **Here:** `--selftest` existed for days, both agent repositories have CI, and
  the bridge had no `.github` at all. A checker nobody runs is a checker that
  does not exist, in the repository that had spent several commits saying so.
- **In BD's repository:** `ci.yml` is correctly configured and correctly
  triggered — on `push` to `main` and on `pull_request` — while the work sits on
  a branch with no remote and no PR. Ten commits CI has never seen, including
  the test added to stop a checker from rotting. And its own header states that
  CI covers linux-64 and **not** the development platform, so "1459 passed
  locally" and "CI green" are two platforms that have never intersected.

Also worth stating because it is the same family: pytest reports a parametrised
test with an empty parameter list as **skipped**, and calls that green. Clearing
`CASES` gave "1 passed, 1 skipped", exit 0 — one commit after that file was
wired specifically so it could not rot.

---

## Layout

```
schema/
  common.defs.json              quantity · requirement · group · assumption · ref
  ask_simulation.schema.json    AM → BD
  ask_experiment.schema.json    BD → AM
  kb_external_entry.schema.json frontmatter of an imported entry
threads/trap-stiffness-recovery/
  r1/ ask_simulation.{md,json}  AM asks: does the height ladder return h0?
      kb_entry_for_bd.md        …as it lands in BD's knowledge/external/am/
  r2/ ask_experiment.{md,json}  BD answers f_c to 1.17 %, refuses h0
      kb_entry_for_am.md        …as it lands in AM's kb/external/bd/
  r3 … r8/                      the rest of the thread
fixtures/invalid/               one per rule, plus expected.json pinning identity
fixtures/valid/                 regression guards for deliberate loosenings
proposals/                      schema change requests from either side
prompts/                        the request text pasted into each agent session
hashes.json                     the manifest R6 checks against, and `_subject_of`
tools/rehash.sh                 what `hashes.json` names: prints lines to add
validate.py                     the thirteen rules
```

Threading is `<thread>/r<N>`, not by title. Titles collide or drift by round 3,
and the commonest failure in a round-trip loop is not that a step was wrong — it
is that after three rounds nobody is asking the original question any more.

Round numbers **may have holes**. r6 absent with r7 present is not a lost
document — it is the other side's turn not yet taken while parity held and the
unblocked side continued. `reply_to` makes it self-describing (r7 replies to r5).
Do not renumber to close a hole: that breaks parity and deletes what the hole was
saying.

## The worked thread

`trap-stiffness-recovery` is real on both sides: AM's
`kb/plans/2026-09-15-drag-calibration-stiffness-vs-size.md` and BD's
`runs/trap-2d-5um__a5ef4f45d589`. Every number in the fixtures is copied from one
of those two, and `hashes.json` holds their actual SHA-256 prefixes.

r1 asks whether a six-rung height ladder recovers `h0` to ±0.195 µm — a figure
AM produced with a toy numpy model that omitted finite `T_obs`, motion blur and
localisation noise. r2 **refuses the headline question** (BD has no wall and one
height) and answers the largest honest sub-question instead, with four findings
that neither repository would have produced alone:

1. The two sampling conventions differ by exactly **2π** — AM's gate wants
   `f_s ≥ 10 f_c` = 99 Hz, BD's convention wants `10/tau_k` = 620 Hz.
2. At the assumed `epsilon = 10 nm` the localisation budget is **already spent**:
   ~8 % on `alpha`, and it is a bias, not a variance.
3. 5 s per rung is `T_obs/tau_k = 310` against the 2000 the 1.17 % was measured
   at — **6.4× short**.
4. Every BD error bar is an **ensemble** error bar over 1000 replicas. One bead
   would scatter ~32× more, so comparing the 1.17 % against a single-bead
   measurement is invalid as stated.

Finding 4 is the one to note: it is BD reporting against its own result.

By r7 the question had been **inverted**, which is the move the thread turned on.
Four rounds asked what precision the run achieves — a question whose answer
neither side controls. r7 asks instead for the **tolerance**: the largest
per-rung scatter at which the six-rung fit still returns `h0` to ±0.2 µm. That
is a property of the **fit**, so it survives its own inputs, and it decoupled the
two sides' unknowns. Every earlier round produced an answer that would have to be
redone if its input moved; that one does not.

The wall turned out to be **not buildable** rather than not yet built. At fixed
`h` the wall's only effect is a scalar `gamma`, which enters no dimensionless
group the trap case carries — `k*` is 21221 at all six rungs, identically, so all
six are the *same* dimensionless run and Faxén lives entirely in the
back-transform. No runner there can learn anything about a wall, for the same
reason a rod's `gamma_perp/gamma_par` measures 1.000000 in that repository. Five
rounds had framed it as a missing capability, and r1's own `wall_drag` assumption
had already named the alternative: test the fit procedure on a synthetic
`gamma(h)`, do not report a number from an infinite medium.

The thread's one remaining decision point is AM's precondition P7, and it is
`needs_data_transfer` with `owner: human`: the 2026-09-03 tracked positions live
on the instrument PC under `D:\codes`, and the AM repository holds no trajectory
data at all. No instrument time is needed — only the bytes.

## Transport — what is actually needed to move a file

Nothing. Both agents are Claude Code sessions with shell and file tools, so a
shared path is the whole mechanism. What needs deciding is *who triggers a
round*, not how bytes move.

| | when it is the right answer |
|---|---|
| **shared directory** | same machine, one operator. Zero new code. Start here. |
| **a third git repo** ← what this is | gives R6 its hashes for free, survives two machines, and makes every round reviewable as a diff |
| **direct call** | **asymmetric and only one way works.** `python cli.py run` is LLM-free, so an AM session can execute BD's simulator directly. The reverse cannot exist: AM ends at hardware and human preconditions. |
| **MCP** | different machines, or when you want a declared tool interface. AM already ships `mcp_server/`. Overkill for file movement alone. |

**Do not load both `CLAUDE.md` files into one session.** AM boots on 416 lines of
`SAFETY.md` plus five hard rules; BD has its own ten principles and a
transcribe-before-interpret intake protocol. Merged, each set dilutes the other
and the refusals that make both repositories trustworthy stop firing. Separate
sessions, shared directory.

And because `confirmed_by` is human-only in both repositories (rule R7), a fully
autonomous loop is not on the table anyway. The bridge's job is to make each
round small enough to review.

## What to build next, per repository

**AM** — emit `plan_experiment_<title>.json` beside the plan (the parsers in
`knowledge/plans.py`, `_section()` and `_table_rows()`, already do most of the
work), and extend `plan-check` with one rule: every number in a prose table must
exist in the structured block. That rule is hard rule 2 made mechanical, so it
pays for itself — and it is the rule that would have caught the `2 D t_exp/3`
blur term, which was prose arithmetic in a plan that no gate ever read.

**BD** — an adapter `ask_simulation.json → observation.yaml + system.yaml`
(beside `bdbot/intake.py`), the reverse `metrics.json → ask_experiment.json`
using the `groups` and `back_transform` blocks `spec.json` already carries, and
the 26 error paths still recorded as `known_unobserved`.

## License

MIT — see [LICENSE](LICENSE).
