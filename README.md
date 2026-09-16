# bridge — agentic-microscope ↔ Brownian-Dynamics-Agent

A schema and two worked round-trips for handing a **question** between the two
agents, so each one re-derives its own plan through its own gates instead of
importing the other's numbers.

```
python3 validate.py --selftest      # CI entry point: the rules still bite
python3 validate.py --all           # every document, warnings included
```

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
the document is a **draft** (rule R4).

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
| `computed` | 1 | …from measured inputs. **Inherits** the worst tier of its inputs — AM's `eta` is tier 3 here because it is computed from an assumed `T`. |
| `assumed` | 3 | a standing choice, a default, a placeholder |
| `simulated` | — | not admissible as a tier-0 input; lands as an external KB entry |
| `round_trip` | — | this number originated in the receiving repository |

## The seven rules

Only R1 is a shape rule. The others are about provenance, which no schema
expresses.

| | rule | what it prevents |
|---|---|---|
| R1 | JSON Schema | malformed document |
| R2 | every `unit` parses | `pN/µm` with the micro sign silently becoming something else |
| R3 | no composites in `system_primitives` | the `3πηd` / `6πηa` factor of two |
| R4 | an `unknown` assumption forces `status: draft` | an undeclared assumption difference reading as agreement |
| R5 | a **hard** requirement may not rest on the consumer's own number | circular evidence: three rounds and both KBs agree with nothing measured twice |
| R6 | cited hashes match `hashes.json` | a stale import, after upstream was corrected |
| R7 | `confirmed_by` is never a machine name | the bridge signing off on itself |

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

## 정정은 순번을 따르지 않는다

라운드 순번(홀수 = 실험, 짝수 = 시뮬)은 **새 질문**에만 적용된다. 자기가 앞서 낸
답이 틀렸다는 걸 발견한 쪽은 순번을 기다리지 않고 말한다 — 그걸 말할 수 있는 쪽은
그 한 쪽뿐이다. `corrects[]`를 싣고 `status: supersedes_prior`로 보내며, 정정된
문서는 `status: corrected`가 된다.

`corrects[].downstream`은 비워두지 않는다. **의존물을 지목하지 않는 정정은 그것들을
조용히 틀린 상태로 남긴다.** 2026-09-15에 실제로 일어난 일이 그 형태였다: BD가 r2의
+1.17 %가 물리가 아니라 추정기 편향이라는 것을 찾았고, r2의 `T_obs >= 32.3 s`
요구사항은 *그 1.17 %가 `T_obs/tau_k = 2000`에서 측정됐다는 근거로* 존재했다. 편향은
`T_obs`로 줄지 않으므로 그 요구사항의 근거가 사라졌는데, 같은 시각 AM은 이미 r3를
그 위에 쓰고 있었다.

## 리비전 없는 ref는 ref가 아니다

`ref`에 `rev`(커밋 sha, 없으면 브랜치명)를 같이 싣는다. 경로만 있는 참조는 브랜치마다
다른 답을 준다 — 이 스레드의 plan 파일이 실제로 그랬다: `main`에서 `58cfc405`,
`worktree-work-2026-09-16`에서 `514da4a0`, `version2`에는 **아예 없다**. 하나의 ref에
세 가지 답이 나오면 R6의 해시 검사는 무엇을 검사하는지 모르는 상태가 된다.

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
fixtures/invalid/               one file per rule; see its README
hashes.json                     upstream hashes, for R6
validate.py                     the seven rules
```

Threading is `<thread>/r<N>`, not by title. Titles collide or drift by round 3,
and the commonest failure in a round-trip loop is not that a step was wrong — it
is that after three rounds nobody is asking the original question any more.

## The worked thread

`trap-stiffness-recovery` is real on both sides:
AM's `kb/plans/2026-09-15-drag-calibration-stiffness-vs-size.md` and BD's
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

## Transport — what is actually needed to move a file

Nothing. Both agents are Claude Code sessions with shell and file tools, so a
shared path is the whole mechanism. What needs deciding is *who triggers a
round*, not how bytes move.

| | when it is the right answer |
|---|---|
| **shared directory** | same machine, one operator. Zero new code. Start here. |
| **a third git repo** ← recommended | gives R6 its hashes for free, survives two machines, and makes every round reviewable as a diff |
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
work), add `kb/external/bd/` as a namespace, and extend `plan-check` with one
rule: every number in a prose table must exist in the structured block. That rule
is hard rule 2 made mechanical, so it pays for itself.

**BD** — an adapter `ask_simulation.json → observation.yaml + system.yaml`
(beside `bdbot/intake.py`), the reverse `metrics.json → ask_experiment.json`
using the `groups` and `back_transform` blocks `spec.json` already carries, and
the two cheap gaps from r2: a sampling layer (integrate over `t_exp`, add
Gaussian `epsilon`) and a run at `n_replicas = 1` for per-realisation scatter.
