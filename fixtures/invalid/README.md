# Violation fixtures

One file per rule, each mutated from the valid document in `threads/` so that the
named rule is the *only* thing wrong with it. `python3 ../../validate.py --all`
must report exactly one ERROR class per file. If a change to the schema makes one
of these pass, the schema lost a rule.

| file | rule | the accident it stands for |
|---|---|---|
| `r2-unparseable-unit.json` | R2 | `pN/µm` with the micro sign instead of `pN/um`. The likeliest real accident on this wire, and the reason the receiver refuses instead of guessing. |
| `r3-composite-in-primitives.json` | R3 | AM sends `gamma` instead of `eta` and `d`. `3*pi*eta*d` and `6*pi*eta*a` are the same formula, so this is where a factor of 2 enters without anybody being wrong. BD's own intake hit it once as ambiguity A1. |
| `r4-unknown-assumption-not-draft.json` | R4 | Eight assumptions still `unknown`, document marked `open`. Assumptions are the only content no number reveals, so an unresolved one has to hold the document at draft. |
| `r5-circular-evidence.json` | R5 | BD hands AM's own 3 %/rung estimate back as a **hard** requirement. Soft and disclosed is fine; hard is AM's number returning as independent evidence. Three rounds of this and both KBs agree with nothing measured twice. |
| `r6-stale-source-hash.json` | R6 | `metrics.json` was regenerated upstream. Every requirement resting on it is stale — supersede the import, never edit it in place. |
| `r7-machine-confirmed.json` | R7 | The bridge sets `confirmed_by: bdbot`. Both repositories reserve that field for a human, and the bridge is the one component positioned to forge it. |
| `r11-drifted-copy/` | **R11.** Two rounds of one thread where `blur_on_var_x` carries `origin: am` in both and disagrees — 1.86 in the first, 0.92 in the second — with no `corrects[]` entry naming it. This is the historical defect exactly: `2*D*t_exp/3` was wrong in r1 and still wrong three rounds later because each round copied it. Note the substituted value is the *right* one; a silent correction is as much a defect as a silent error, because nothing downstream learns it changed. Directory-shaped because R11 is the only thread-level rule. |
