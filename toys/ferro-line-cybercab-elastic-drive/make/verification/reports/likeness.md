# Likeness report

run **2**, 2026-09-09 01:34 -- mean IoU **0.903** against a 0.90 floor -- ok

| view | IoU | delta | trend | aspect (render/ref) | worst bands |
|---|---|---|---|---|---|
| side | 0.903 | +0.002 | stalled | 0.976 | 0.67 → 0.916, 0.75 → 0.945, 0.33 → 0.947 |

Bands run from the top of the silhouette (0.00) to the bottom (0.92). A ratio above 1 means the model is too wide at that height, below 1 too narrow.

## History

One row per view per run. Read the delta before editing again: a round that moved the number down is a round to revert, and a run of `stalled` means the edits are not reaching the shape this gate measures. A floor marked `!` was lowered under `--accept-mismatch`; an IoU marked `*` is the best that view has reached, and the number this run had to beat.

| run | time | view | IoU | delta | trend | aspect | floor |
|---|---|---|---|---|---|---|---|
| 1 | 2026-09-09 00:32 | side | 0.901 | — | first | 0.974 | 0.90 |
| 2 | 2026-09-09 01:34 | side | 0.903 * | +0.002 | stalled | 0.976 | 0.90 |

Best so far: side 0.903 (run 2). A run below its own best fails as `regressed-from-best`, floor or no floor.