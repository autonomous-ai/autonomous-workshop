# Grid Dock — working notes

## Hardware read

The hardware read is the same as for `../fx2-hover/NOTES.md` and comes from the same STEP, panel spec and schematic.

This option also uses the following:
- the CN1 (USB device) and CN2 (USB host) footprints at (+/-24, +17) for the pogo wiring;
- the diode-ORed 5 V inputs (Q1/Q2), which let the cable feed either the dock (through pogo to CN1) or the device's own USB-C.

The owner chose this on 2026-10-05: "cáp có thể cắm vào cả đế hoặc vào máy" (the cable can plug into either the dock or the device). The 5-pin magnetic pogo pair is specified by face size, 14.5 x 5.2 mm. Before the build, confirm it against the connectors on the owner's current dock.

## Images

AI generation and editing via OpenRouter `openai/gpt-5.4-image-2`. No web imagery was used.
- The assembly and the illustration descend from `concepts/handheld-dock/cur_dock_a`. That image was itself an AI edit of the owner's own dock photo, with the logo ignored.
- Every reference is generated, then AI-edited, then keyed to alpha, then rescaled horizontally by at most 20%, then padded to 800 x 800:
  - ref-01: x 0.94, chosen for the best silhouette IoU
  - ref-02: x 1.036
  - ref-03: x 1.144
  - ref-04: x 0.833
  - ref-05: x 1.128

The tilt moved from 25 to 22 degrees for the same reason as in the Hover Dock. The generator draws shallow ramps, and 22 degrees is inside the owner's 20 to 30 range.

Round cap: 4 rounds for the assembly and 3 for the face and back.

## Stage 3b — image vs contract

| Image | Check | Contract | Image | Verdict |
|---|---|---|---|---|
| ref-01 | side aspect W/H | 1.699 | 1.553 | DISAGREE (8.6%). Stretching to match the aspect drops the IoU to 0.900, so the scale that maximises IoU was kept |
| ref-01 | silhouette IoU as saved | >= 0.90 | 0.924 | ok |
| ref-01 | tilt (fit) | 22 | 21 | ok |
| ref-01 | floor height at the ledge | 10.0 | 13.0 | DISAGREE, raised |
| ref-01 | ledge bar height | 23.0 | 29.0 | DISAGREE, raised (image keeps it below the device face) |
| ref-01 | device thickness | 16.0 | 18.0 | DISAGREE, raised |
| ref-01 | device length / floor length | 104 / 96 | 104 / 99 | ok |
| ref-02 | aspect | 1.135 | 1.136 | ok |
| ref-02 | glass width | 85.0 (x +/-42.5) | 90 (x +/-45) | DISAGREE (5.9%), raised |
| ref-02 | glass top / bottom | 46.0 / -39.0 | 42.4 to 44.0 / -41.3 | DISAGREE, raised |
| ref-02 | ribs, right band (machine scan) | 10 (amended from 9) | 10, y -14.6 to 19.8 | ok |
| ref-02 | ribs, left band | 10 | 10 by crop inspection; the machine scan double-counts the groove highlights | ok |
| ref-02 | rib span | -14.5 to 19.7 (amended) | -14.6 to 19.8 | ok |
| ref-02 | stripe | 90.0 long at y -45.5 (amended from 84.0) | 89.8 long at y -45.7 | ok |
| ref-03 | aspect | 1.135 | 1.136 | ok |
| ref-03 | mic holes, back view | (53.3, -39.0), (-21.7, -39.0) | (52.7, -41.6), (-47.7, -41.6) | DISAGREE: one hole is in the wrong place and both are 2.6 mm low; raised (the board fixes them) |
| ref-04 | silhouette IoU at 22 degrees | >= 0.90 | 0.957 | ok |
| ref-04 | side aspect | 1.630 | 1.627 | ok |
| ref-05 | aspect | 5.565 | 5.564 | ok |

Not measurable in these views: the pogo slots and pockets, the USB-C openings, the bosses, the ballast pocket, the cheek grid pitch and the countersinks. The screw positions were detected only roughly. These are carried by the contract rows.

## Stage 3c — printability

| Part | Feature | Size | Minimum | Verdict | Resolution |
|---|---|---|---|---|---|
| front | rib slots | 1.2 x 11.0 | 0.5 opening | ok | |
| front | V-grooves | 1.2 wide | 1.0 decoration | ok | |
| front | stripe groove | 4.0 x 1.0 | 1.0 | ok | |
| front | glass ledge | 1.6 thick | 0.8 | ok | wall_min 1.6 |
| front, inner face down | window and countersinks open upward | | | ok | |
| back, back down | USB opening 9.4 | bridge | 12 | ok | |
| back | USB counterbore 12.4 | bridge | 12 | fixed | 45 degree gable top; 1.2 wall, wall_min 1.2 |
| back | pogo slots 14.5 wide | bridge | 12 | fixed | slots open to the seam, no roof |
| back | mic holes | 1.0 | 0.5 | ok | |
| wedge, bottom down | breakout pocket 16.4 | bridge | 12 | fixed | 45 degree gable top |
| wedge | ballast pocket 80.4 x 40.4 | bridge | 12 | fixed | gable roof; moved to y 75 so the roof clears the floor |
| wedge | wire channel | 4.0 | 12 | ok | diamond section |
| wedge | cheek grid on vertical faces | | 45 deg | ok | V-grooves |
| ledge, front face down | inner face 22 degrees from horizontal | | 45 deg | ok | |
| ledge | pogo pockets | axis 22 degrees off vertical | 45 deg | ok | |

## Stage 3d

No moving parts, so skipped.
