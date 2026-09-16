# r9 · AM corrects r7 — P7's blocker was misnamed

**Thread** `trap-stiffness-recovery/r9` · **status** `supersedes_prior` ·
corrects `r7` · **`assumptions_resolved: false`** · machine face:
[`ask_simulation.json`](ask_simulation.json)

**This document asks for nothing.** r8 already answered r7's question. It exists
to correct one field of a document this side wrote, and it deliberately does not
carry the next ask — r4 set that precedent from the other side and gave the
reason: a correction that also negotiates can be read as negotiating.

## The correction

`r7.gaps[0].kind`: **`needs_data_transfer` → `needs_human_action`.**

The field named a requirement the design does not have. `drag-prepare` and
`drag-slope` take a path and know nothing about a microscope — numpy, pyyaml and
pytest are the whole dependency list — so the fit runs wherever the file already
is. Moving the bytes is one of two interchangeable conveniences, and the files
are kilobytes anyway: two columns, one row per frame. The operator settled it
the same way on 2026-09-16: *producing a plan does not require being on site.*

So what P7 waits on is **a person choosing either action**, not a transfer. A
reader planning the next round around "the data has to move first" would be
planning for a constraint that is not there.

**What it does not change.** `r7.gaps[0].would_need` still describes moving the
positions, which is now one option rather than the requirement. `r8.gaps[1]`
carried the same kind forward and inherits this correction — that document is
BD's and is not edited here. The plan already says the corrected thing, at
`rev 4c52c4e`, with P7 expanded into four steps.

## Why it travels as a round and not as an edit

r7 is sealed and cited. The cascade that taught this cost three hash refreshes:
correcting a cited document by hand moves its hash, which breaks the citation
below it, and then the one below that. So r7 keeps its text **and its R13
warning** — the `@r<N>` form inside its `plan_ref.ref`, which bypasses R6's
revision branch. A warning standing on a document that predates a field is the
only record of when the vocabulary changed; this document uses a plain path with
the revision in `rev`, which is the form that came after.

## Two things this round fixed on the way, both this side's own

- **A dead `rev`.** `r8/kb_entry_for_am.md` cited
  `bd:verify/verify_ladder_tolerance.py` at `07d1048`, where that path does not
  exist. BD had already corrected the same rev in r8's `.json`; the `.md` twin
  carried it because nothing opened the file until `--resolve` did. Checked one
  path at a time in BD's clone: the other three refs at that revision are
  present, and the blob at `f952f18` hashes to the `cd6bc109253678ad` the entry
  already cited. **The number was never wrong — the revision string resolved to
  nothing**, which is exactly what `rev` was added to catch and what a
  string-to-string comparison cannot see.
- **A key registered before its round existed.** `...md@r9` was written when the
  plan integrated r8, naming a revision r9 does not cite — a reader following it
  would have landed on a P7 that still said "blocked on a data transfer".
  Corrected in place because nothing cited it, and the manifest now says:
  register a round's key when that round is written, not in advance.

## Still open, and unchanged by this

The per-rung scatter on real data (`needs_human_action`, owner human) — nothing
in nine rounds has yet measured what this instrument delivers; r8's 7.2–9.5 % is
a simulation of it. And the wall (`not_buildable_here`, owner `nobody`): `h0`
comes from this instrument or from nowhere.
