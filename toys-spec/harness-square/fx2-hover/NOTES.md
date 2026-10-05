# Hover Dock — working notes

## Hardware read

All coordinates come from `hardware/PCB_Harness_pro_v1.step`. I loaded it with OCP and moved every part into the board's own plane, because the model tilts the board 30 degrees about X; that tilt explains the 80.7 x 35.2 x 22.3 bounding box. Measured from the file:
- The board is 80.0 x 40.0 x 1.2 mm.
- Side A parts stand at most 2.1 mm (the FPC connectors). The module on side B stands 3.72 mm.
- Four M2 holes of 2.2 mm diameter sit at (+/-33, -18) and (+/-24, +14).
- The USB-C sits at the -u end at v = +4.0.
- Two top-port mics sit at (+/-37.5, +13.0) and switches at (+/-37.1, -14.0).
- The TF socket and the WS2812 LED are on side A.
- CN1/CN2, the 4-pin footprints at 2.5 mm pitch, sit at (+/-24, +17), unpopulated in the model.

The panel figures come from `TXW395039B0-HYE_SPEC.pdf` (glass 84.37 x 84.37 x 1.8, stack 3.23). The rest comes from the schematic: diode-OR of the two 5 V inputs, CH343P auto-program, the IP5306 key on SW3, and the BOOT switch on SW1.

## Images

AI generation and editing via OpenRouter `openai/gpt-5.4-image-2`. No web imagery was used.
- The three-quarter illustration is an edit of the earlier `concepts/handheld-dock/hover_dock_b`.
- Every reference is generated, then AI-edited, then keyed to alpha, then squeezed horizontally by at most 20%, then padded to 800 x 800:
  - ref-01: x 0.865, chosen for the best silhouette IoU
  - ref-02: x 1.062
  - ref-03 and ref-04: none

The generator kept drawing ramps of 17 to 20 degrees and long wedges. That is why the contract moved from 25 to 22 degrees. The user's range is 20 to 30. At 22 degrees the base image matches the contract silhouette at IoU 0.971 with no resize.

Round cap: 4 rounds for the assembly and 3 for the tile back.

## Stage 3b — image vs contract

The silhouette IoU is against the contract's projected convex part model, side view (camera az 90, el 0).

| Image | Check | Contract | Image | Verdict |
|---|---|---|---|---|
| ref-01 | side aspect W/H | 1.348 | 1.224 | DISAGREE (9.2%). Squeezing to match the aspect drops the IoU to 0.887, so the scale that maximises IoU was kept |
| ref-01 | silhouette IoU as saved | >= 0.90 | 0.924 | ok |
| ref-01 | tilt (parameter fit) | 22 | 23 | ok |
| ref-01 | base front height | 18.5 | 17.0 | DISAGREE, raised at review |
| ref-01 | tile thickness | 15.5 | 16.5 | DISAGREE (1.0 mm), raised |
| ref-01 | tile overhang past base ends | 6.4 | 0 | DISAGREE, raised |
| ref-01 | 2.5 mm pad gap | visible | not resolved in silhouette | noted |
| ref-02 | aspect | 1.000 | 1.002 | ok |
| ref-02 | recess diameter | 11.6 | 11.6 | ok |
| ref-02 | grille hole count | 23 (amended from 19) | 23 | ok |
| ref-02 | grille centre, front view | (-27.0, 0.0) (amended from -21.0) | (-26.9, 0.1) | ok |
| ref-02 | grille hole diameter | 1.6 (amended from 1.5) | 1.6 | ok |
| ref-02 | grille circle | 20.0 | 20.2 | ok |
| ref-02 | mic holes, front view | (35.0, 39.3), (35.0, -35.7) | (35.9, 28.1), (35.9, -25.8) | DISAGREE, raised (the board fixes them) |
| ref-03 | silhouette IoU at 22 degrees | >= 0.90 | 0.971 | ok |
| ref-03 | side aspect | 1.517 | 1.526 | ok |
| ref-03 | front / rear height | 18.5 / 47.8 | fit 18.5 / 47.8 | ok |
| ref-03 | boss, horizontal width / height | 10.2 / 4.0 (11.0 at 22 degrees) | 6.0 / 3.6, centred 36.1 from front | DISAGREE on width, raised (hidden when docked) |
| ref-04 | aspect | 3.535 | 3.672 | ok (3.9%) |
| ref-04 | width at middle | 6.0 | 5.7 | ok (0.3 mm) |
| ref-04 | depth | 9.9 | 9.5 | ok (0.4 mm) |

Not measurable in these views: the USB-C opening and counterbore, the board bosses, the ballast pocket, the pad grooves and the foot recesses. All are hidden in the views drawn. They are carried by the contract rows only.

## Stage 3c — printability

| Part | Feature | Size | Minimum | Verdict | Resolution |
|---|---|---|---|---|---|
| tile | mic holes | 1.0 | 0.5 opening | ok | |
| tile | grille holes | 1.6 | 0.5 opening | ok | |
| tile | rim | 3.0 | 0.8 | ok | |
| tile | recess floor | 1.0 | 0.8 | ok | wall_min set to 1.0 |
| tile | wall behind USB counterbore | 1.0 | 0.8 | ok | |
| tile, back down | glass ledge underside | flat 2.5 overhang | 45 deg | fixed | 45 degree chamfer |
| tile, back down | recess ceiling | 11.6 bridge | 12 | ok | recess sized 11.6 for this |
| tile, back down | USB counterbore 12.4 wide | bridge | 12 | fixed | 45 degree gable top |
| base, bottom down | ballast pocket 60.4 x 40.4 | bridge | 12 | fixed | 45 degree gable roof |
| base | foot recesses 10.4 | bridge | 12 | ok | |
| base | boss 22 degrees off vertical | overhang | 45 deg | ok | |
| pad | 6.0 x 3.5 TPU, flat | | 0.8 | ok | |

## Stage 3d

No moving parts, so skipped.

## Revision for the updated design-a-toy skill (merged main d9e673dd, 2026-10-05)

The contract moved to schema 4. It now has a camera on every reference, three static Interfaces with text, a Print section carrying the two required rules word for word, and no print minimum of its own.

### Reference cameras (render_review convention)

| Ref | Camera | Cue |
|---|---|---|
| ref-01 | [0, 0] | pure side elevation, front on the image's left, so seen from +X, level |
| ref-02 | [90, -75] | square-on back face; the docked back faces 22 degrees off straight down (true -68, rounded) |
| ref-03 | [0, 0] | pure side elevation, front on the left |
| ref-04 | [-90, 75] | square-on to the pad top, which lies on the 22 degree slope (true 68, rounded) |

### Stage 3c against the library minimums (`print_details.py --limits --nozzle 0.4`)

| Part | Feature | Size | Minimum (name) | Verdict | Resolution |
|---|---|---|---|---|---|
| tile | mic hole | 1.0 | 0.5 (min_cut_width) | ok | |
| tile | grille hole | 1.6 | 0.5 (min_cut_width) | ok | |
| tile | material between grille holes | at least 1.8 (3.4 pitch) | 1.6 (min_web) | ok | pitch of at least 3.4 now stated; the image's spacing measured about 3.0 to 3.3 |
| tile | rim | 3.0 | 0.9 (min_relief_width) | ok | |
| base | boss | 11.0 across | 2.0 (min_feature) | ok | |
| base | pad groove | 6.4 wide, 1.0 deep | 0.5 / 0.5 | ok | |
| pad | width | 6.0 | 0.8 (min_wall) | ok | |

No stacked or curved detail sits on a host too small for it. No knife edge either: the base's top edges carry 3.0 mm rounds.

### Hidden joints

| Joint | Check | Value | Verdict | Resolution |
|---|---|---|---|---|
| boss in recess | clearance on each side | 0.3 | ok | |
| boss in recess | stands on a bed face? | the recess is a hole in the tile's bed face; the boss is on the base top | ok | |
| magnet in boss | clearance on each side | 0.05 (6.1 pocket) | fail | pocket enlarged to 6.4 |
| pad in groove | clearance on each side | 0.2 | ok | |
| pad in groove | groove in the base bed face? | no, it is in the top face | ok | |

### Stage 3d camera composition

No requirement names a camera or claims a composition. The old "35 / 22 fixed frame" wording appears in neither contract, so there is nothing to project.
