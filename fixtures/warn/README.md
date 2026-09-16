# Warning fixtures and anchors

`fixtures/invalid/` guards the rules that raise an **error**: one document per
rule, each failing with that rule and nothing else. This directory is the other
half, and it exists because the coverage check could not see that half at all —
it enumerates `rep.err` calls in the source, so four rules that only ever warn
(**R5b, R8, R12, R13**) were outside every guard in a repository whose README
spends a section on [what R5's soft warning bought](../../README.md).

**Measuring first changed the fix.** All of them were firing; nothing would have
noticed if one stopped. So most entries in `expected.json` are **anchors** — a
sealed document that must keep producing a given warning — rather than new
fixtures. An anchor is cheaper and says more: it pins a fact about the archive.

Two rules needed a real fixture, and both are the ones that had never fired for
their own reason:

| file | rule | why an anchor would not do |
|---|---|---|
| `r5b-came-home-mislabelled.json` | **R5b** | Its only live firing was inside `fixtures/invalid/r1-direction-const.json`, where flipping `direction` flips which side is the consumer, so every `origin: am` value looks like it came home. Alive by accident, on another rule's fixture. This is r1 with one `reference_only` value's origin set to the consumer and its `evidence` left at `computed` — a number that came home and says nothing about it. |
| `r10-bare-evidence-class.md` | **R10** | The warn branch fires only on `measured`/`handbook` **with no** `evidence_classes` map, and every live entry has carried the map since C4 was answered — so the branch went quiet the day the schema improved. This is r1's import as it read before that. |

`expected.json` pins, per rule: the anchor, a fragment identifying the message,
and the **full set** of warning rules that anchor produces. Fragments come from
the message head and never the rationale — a rationale prints once per run and
is absent the second time.

It is **rule-level, not branch-level**, and `_branch_note` names the branches it
does not reach.
