# Comet Heist CAD specification

`--bed 210x210x220`

## Coordinate and product contract

All dimensions are millimetres. The deployed assembly origin is the tray seam center; X runs goal-to-goal, Y runs side-to-side, and +Z is up. The source preserves the sealed 390 x 170 active field, 410 x 186 lapped tray body, gate planes X=-50/+50 (sealed coordinates 145/245), pivot Z=38, and 486 x 190 x 68 deployed envelope. All inputs are authored in `params.py`; `validation.py` asserts the controlling equations before geometry builds.

## Parts and quantities

| Printable entry | Qty | Purpose | Print pose | 45-degree support plan |
|---|---:|---|---|---|
| `part_tray_a` | 1 | Left half, lower seam lap, vaults/facets/cheeks | Play face up | Generated support everywhere for retention lip/local elevated facets |
| `part_tray_b` | 1 | Exact 180-degree end mirror, upper seam lap | Play face up | Generated support everywhere for retention lip/lap/local elevated facets |
| `part_seam_storage_key` | 2 | Locks seam lands; rim lock in storage | Flat | None |
| `part_gate_bridge` | 2 | 84 mm portal and printed bearing seats | Back face down | Generated support everywhere for elevated back-face steps |
| `part_gravity_blade` | 2 | Free gravity pendulum with integral trunnions | Panel parallel to bed, trunnions vertical | Generated support everywhere beneath the panel; lower trunnion end is the bed datum |
| `part_gate_keeper` | 2 | Retains trunnion ends | Flat | None |
| `part_comet_sun` | 6 | Sun tactile relief | Flat underside down | None |
| `part_comet_orbit` | 6 | Orbit tactile relief | Flat underside down | None |
| `part_ready_spent_magazine` | 2 | Two token wells and tactile state cue | Flat base down | Generated support everywhere beneath the elevated tongue |

Total printed instances: 24. `comet_heist.step.py` is a view-only deployed assembly of those 24 occurrences.

## Interfaces and dimensional ledger

- Trays: 206 x 186 x 20 each, 2 mm complementary half-thickness lap, 2.4 floor, 2.8 walls, 2 mm inward side lips. Largest part has 4 mm total nominal margin on a 210 mm bed.
- Gate: 110 span x 14 depth x 65.6 high from deck, 84 clear central portal, no underpass around the integral 30 mm station cheeks. Each asymmetric 12 x 18 T-foot lowers through an open keyhole, slides 6 mm, and sits 0.25 mm below an integral 2.5 mm retaining shoulder.
- Pendulum: pivot Z=38, paddle center radius 29, paddle 14 x 12 x 8, 6 x 4 arm, 4.0 trunnion in 4.6 seat, 0.35 axial clearance each side, nominal neutral floor clearance 3.0, ±50-degree intended swing.
- Comets: diameter 30 x 5.5, constructive 0.7 top edge bevel and <=0.6 tactile relief.
- Vault mouths: shooter-relative Medium 38 / Wide 50 / Narrow 34, with 4 / 2 / 6 recessed pips and 2.8 dividers; pocket depth 38.
- Magazines: 38 x 72 x 8 (the sealed 72 x 38 footprint, rotated in deployment), two 32 mm x 1.5 deep wells, 8 x 6 x 3 tongue with 0.30 nominal side clearance.
- No purchased parts. Intended FDM nozzle is 0.4 with 0.20 mm nominal layers. Floor and walls exceed three line widths; final per-STL thickness reports decide the digital wall gate. `measure/check_support.py` separately screens every fresh STL for downward facets beyond 45 degrees, verifies the support plan above, and records exact critical surface areas. It is not a slicer or a successful-print claim.

## Storage map

Inside the opposed 40 mm tray cavity, Tray A has bridge outlines at local X=10..120/Y=10..74 and Y=84..148, each at 14 mm thickness. A folded manual proxy no larger than 180 x 100 x 3 overlays X=10..190/Y=10..110, keeping the opposed maximum at 17 mm. Tray B maps twelve comets at X={25,56,87,118,149,180}, Y={25,60} and two magazines at X=10..82/Y=90..128 and X=90..162/Y=90..128. The packed analytic envelope is 210 x 190 x 52. Physical rattle and manual fit remain Playtest checks.

## Assembly and limitations

Seat each bridge between its integral cheeks, place the blade trunnions in the open seats, and retain them with the keeper. In the deployed CAD pose the seam keys rest across the two outer seam lands and the magazines engage the end slots. The deterministic motion manifest checks two blade sweep directions plus clear key removal and blocked downward key capture. The corrected blade print entry changes only manufacturing pose: deployed blade geometry and assembly placement remain unchanged. The support screen does not establish slicer support accessibility or removal quality. Neither digital check establishes friction, elastic snap behavior, gravity-return duration, impact retention, print tolerance, or successful manufacture; those remain physical Playtest needs.
