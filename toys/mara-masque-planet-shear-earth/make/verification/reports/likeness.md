# Likeness report

run **4**, 2026-09-16 07:48 -- mean IoU **0.922** against a 0.90 floor -- ok

| view | IoU | delta | trend | aspect (render/ref) | worst bands |
|---|---|---|---|---|---|
| hero | 0.922 | +0.000 | stalled | 0.964 | 0.50 → 0.929, 0.08 → 0.93, 0.33 → 0.939 |

Bands run from the top of the silhouette (0.00) to the bottom (0.92). A ratio above 1 means the model is too wide at that height, below 1 too narrow.

## History

One row per view per run. Read the delta before editing again: a round that moved the number down is a round to revert, and a run of `stalled` means the edits are not reaching the shape this gate measures. A floor marked `!` was lowered under `--accept-mismatch`; an IoU marked `*` is the best that view has reached, and the number this run had to beat.

| run | time | view | IoU | delta | trend | aspect | floor |
|---|---|---|---|---|---|---|---|
| 1 | 2026-09-16 07:36 | hero | 0.922 * | — | first | 0.964 | 0.90 |
| 2 | 2026-09-16 07:41 | hero | 0.922 | +0.000 | stalled | 0.964 | 0.90 |
| 3 | 2026-09-16 07:44 | hero | 0.922 | +0.000 | stalled | 0.964 | 0.90 |
| 4 | 2026-09-16 07:48 | hero | 0.922 | +0.000 | stalled | 0.964 | 0.90 |

Best so far: hero 0.922 (run 1). A run below its own best fails as `regressed-from-best`, floor or no floor.