# amend-d — block-built surface and a forward-pointing foot (visible)

Owner request 2026-10-13: v01 looked too boxy, and its feet looked reversed.

Causes:
- The contract described every part as plain boxes and asked only for 0.6
  panel lines; ref-07 thigh and ref-09 spine were plain slabs, so Make built
  slabs while ref-01 shows a built-from-small-blocks toy.
- The boot ran Y -13 to 9, flush with the shin's front, with a heel to Y 14:
  only the back stuck out. Every shin reference was a front view, so no
  reviewer could see the foot's direction.

Changes:
- Print section: block-built surface rule (seams 0.6 x 0.5, blocks 5–15,
  brickwork offset, two proud blocks per front face, 0.8 chamfers at 52°
  on downward edges; square at bed faces, bores, joints and within 2 mm of
  another part). Seams keep each floor; arm-shell floor 2.5 -> 2.0.
- R10, R15, R17, R18, R19 name the seams.
- Boot: toe block Y -17 to -13, Z 0 to 7; heel step Y 9 to 12, Z 0 to 7
  (was Y 14, Z 0 to 27). Shin extents Y 29. R09 and the balance sentence:
  feet span Y -17 to 12, centre of mass Y 0.
- model.py: every sweep ≥ 0.5; car clearance of the toe 2.0; car 48.5.

Images (OpenRouter openai/gpt-5.4-image-2, prompts/):
| Ref | Source | Rounds | X stretch | Stage 3b |
|---|---|---|---|---|
| ref-07 thigh | m-thigh, edit of ref-07 + ref-01 for style | 1 | 1.046 | width 25.0, step at Z 20 inset 2.0, tongue X 3.5–12.1 (contract 4–14, 10 wide → 8.6; same as v1 image) |
| ref-09 spine | m-spine, edit of ref-09 + ref-01 | 1 | 0.996 | 83 x 122 |
| ref-12 shin side (new, camera [0, 0]) | s5-shin after s/s2/s3/s4 | 5 (cap) | 1.0 | depth 27.9 vs 29; shin 20.8 vs 22 (5.5%, 1.2 mm, residual at the cap); toe 3.9 ahead vs 4; toe 6.8 tall vs 7; heel 3.0 vs 3; knee pad 1.7 proud vs 1.0 (residual); tongue a rounded tab 5.6 wide at Z 82 vs 7.4 (hidden in the thigh in the Display Pose) |

Image wins: toe and heel height 7 (contract had 12 and 27). Contract wins
elsewhere; the residuals above are at the round cap.
