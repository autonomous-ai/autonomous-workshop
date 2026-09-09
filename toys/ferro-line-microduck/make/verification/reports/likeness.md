# Likeness report

run **3**, 2026-09-07 12:29 -- mean IoU **0.901** against a 0.90 floor -- ok

| view | IoU | delta | trend | aspect (render/ref) | worst bands |
|---|---|---|---|---|---|
| hero | 0.901 | -0.002 | stalled | 0.996 | 0.83 → 1.183, 0.92 → 1.171, 0.33 → 0.935 |

Bands run from the top of the silhouette (0.00) to the bottom (0.92). A ratio above 1 means the model is too wide at that height, below 1 too narrow.

## History

One row per view per run. Read the delta before editing again: a round that moved the number down is a round to revert, and a run of `stalled` means the edits are not reaching the shape this gate measures. A floor marked `!` was lowered under `--accept-mismatch`; an IoU marked `*` is the best that view has reached, and the number this run had to beat.

| run | time | view | IoU | delta | trend | aspect | floor |
|---|---|---|---|---|---|---|---|
| 1 | 2026-09-07 11:12 | hero | 0.900 * | — | first | 1.000 | 0.90 |
| 2 | 2026-09-07 11:34 | hero | 0.903 * | — | first | 0.996 | 0.90 |
| 3 | 2026-09-07 12:29 | hero | 0.901 | -0.002 | stalled | 0.996 | 0.90 |

Best so far: hero vs hero.png 0.903 (run 2), hero vs ref-01-microduck-grey-upright.png 0.900 (run 1). A run below its own best fails as `regressed-from-best`, floor or no floor.