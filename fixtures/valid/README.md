# Positive fixtures

`fixtures/invalid/` proves a rule still bites. This directory proves a rule does
**not** bite something it should allow — a regression guard for cases where a
rule was too strict and was loosened on purpose. `--selftest` requires every file
here to pass.

| file | guards |
|---|---|
| `c6-correction-with-unknown.json` | **C6.** A correcting document (`status: supersedes_prior`) that also declares a newly-found `unknown` assumption. Under the first version of R4 this was impossible: any unknown forced `status: draft`, and a correction that becomes a draft does not correct anything. BD hit it while writing r4 and moved the item into `findings[]` rather than weaken it — filing an undeclared assumption as a disagreement, which is what R4 exists to prevent. The fix was not a carve-out: `status` was carrying two independent facts (where a document is in its lifecycle, and whether its assumptions are declared) and they are now separate fields. Copied from r4 with the assumption BD wanted to raise — the PSD estimator choice, measured at up to +7.9 %. |
