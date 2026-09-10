# Civic Skyline — source-level design specification

[assumed] Units: millimetres. Print envelope declaration: `--bed 220x220x220`.

This is original stylized architecture for a complete orthodox chess set. The host Wish requires the Empire State, Chrysler and Flatiron buildings; researched references to Chinatown, Williamsburg, the Bronx, Staten Island and Queens; a coherent collectible language; 32 clearly differentiated chessmen; a board; and practical editable CAD/print files. No electronics or purchased hardware is used. The source geometry is authoritative for dimensions; the research handoff also contains earlier recommendations that are not necessarily implemented.

## Source and evidence classification

- **[sourced]** Architectural and cultural facts come from the linked primary-source ledger in `../RESEARCH.md`, accessed 2026-09-09. They support recognisable form choices, not exact dimensions of the original buildings.
- **[assumed]** All tabletop dimensions, relief compositions, print clearances and chess adaptations below are original design choices. These are not architectural scale replicas.
- **[observed]** No user reference image was supplied for this Wish. No photograph-to-CAD likeness measurement is claimed.
- **[computed]** Actual geometry, topology, shell, thickness, mesh, placement and center-of-mass results belong in the generated `measure/` evidence. Assertions here state intended requirements and do not replace those results.

The repeated ruled-loft octagonal plinth, stepped massing, stout tips and shallow recessed detail unify the six role families. Both armies share exactly the same geometry and differ by high-contrast material color. There is no tactile side-band system in this version.

## Dimensions and datums

| Named source parameter | Value | Design purpose |
|---|---:|---|
| `SQUARE` | 42 | [assumed] Standard 8 × 8 alternating playing field |
| `FRAME` | 24 | [assumed] Cultural relief outside the playing field |
| `PANEL` | 192 | [assumed] One quarter of the board, within a 220 mm bed |
| `BOARD` | 384 | [assumed] `8*SQUARE + 2*FRAME`, also `2*PANEL` |
| `BOARD_H` | 5 | [assumed] Flat nominal playing surface |
| `SEAT_Z` | 2.4 | [assumed] Backing floor thickness below each tile pocket |
| `TILE_GAP` | 0.5 | [assumed] Total straight-edge tile-to-pocket width difference; nominal 0.25 per side |
| `POCKET_CORNER` | 2 | [assumed] Chamfer along each adjoining edge of every tile and internal pocket corner; seam corners open square |
| `TILE_H` | 2.6 | [assumed] Derived as `BOARD_H-SEAT_Z`; tile finishes flush |
| `RELIEF_Z` | 4.8 | [assumed] Relief starts 0.2 below the backing top |
| `RELIEF_H` | 1.4 | [assumed] Relief height; maximum board height 6.2 |
| `LINE_W` | 1.5 | [assumed] Cultural relief stroke width |
| `GROOVE_WIDTH` | 1.3 | [assumed] Straight facade-channel width |
| `GROOVE_DEPTH` | 0.65 | [assumed] Facade recess depth; crown windows use the same depth |

Board origin is its lower-left external corner as viewed by the light player. +X runs from a toward h; +Y from rank 1 toward rank 8; +Z is upward. A square center is `(FRAME+SQUARE*(file+0.5), FRAME+SQUARE*(rank+0.5), BOARD_H)` with zero-based indices. Dark squares satisfy `(file+rank)%2 == 0`, so a1 is dark and h1 is light.

Each board part is local to its quadrant's lower-left corner and stands at Z=0. Its assembly translation is `(qx*PANEL,qy*PANEL,0)`. Each tile is centered at local X=Y=0 with bottom Z=0 and is placed at the dark square's XY center, Z=`SEAT_Z`. Each chessman is centered on its local plinth at Z=0 and placed at its starting square, Z=`BOARD_H`. Dark back-rank pieces rotate 180 degrees around Z. No printed object is exported solely in assembly-height coordinates.

The assembly has 68 labeled occurrences: four panels, 32 dark inlays and 32 chessmen. Print entries comprise eleven unique models: four panel shapes, one tile and six role shapes. `city.step.py` contains assembly placement only and is not a print target. `city_lib.py` contains the shared geometry and parameters.

## Six role requirements

[assumed] Plinth profile stations are Z=0,2,4,7,9 with radius factors 1,1,0.93,0.93,0.78. Regular octagons have vertices rotated 22.5 degrees. A listed diameter below is the circumscribed diameter; axis-aligned footprint is smaller. Grasp the shaft/body, not the decorative tips.

| Role / total quantity | Height / nominal base diameter | Required exact-form read and source construction |
|---|---|---|
| King / 2 | 86 / 32 | [assumed] Empire State: seven overlapping rectilinear tiers. A broad 25 × 22 mm lower tier supports setbacks into a long 16 × 14 mm shaft from Z=34 to 63, followed by three narrowing mast tiers. Recessed vertical channels reinforce the long shaft. A stout 3.2 mm-section cross gives the king cue; it is an original chess adaptation. |
| Queen / 2 | 76 / 32 | [assumed] Chrysler: shaft tiers support four overlapping solid semicircular XZ fan volumes. Their radii are 10, 7.6, 5.2 and 3.2 mm; arch centers are Z=51, 57, 63 and 69; lower edges are Z=48, 54, 60 and 65; extrusion depths are 14, 11, 8 and 5 mm. Each successive fan has 5, 3, 1 or 0 triangular windows recessed 0.65 mm into each front/back face. A 3.2 mm square tip runs from Z=70.5 to 76. Actual stepped surfaces and triangular windows replace the former pointed crown with engraved concentric rings. |
| Bishop / 4 | 64 / 30 | [assumed] Flatiron: a symmetric truncated wedge has a 22 × 21 mm reference plan and a 3.2 mm blunt prow. Its long shaft uses 0.94 times that plan from Z=14 to 55; a full perimeter cornice uses 1.04 times the plan from Z=54 to 57. Four vertical channels on each sloping facade and three horizontal recessed bands create a gridded architectural surface. A smaller upper tier supports the retained planar mitre cap from Z=57 to 64, with a shallow diagonal groove and 4.2 mm rear web. The wedge and projecting cornice carry the landmark; the mitre is a chess adaptation. |
| Knight / 4 | 58 / 30 | [assumed] A recognizable horse-head side profile, forward muzzle, blunt joined ears and 11 mm profile depth, fused into a stout support and plinth. Shallow diamond-shaped eye recesses and mane recesses do not form separate pieces. |
| Rook / 4 | 52 / 30 | [assumed] Brooklyn Bridge: rectangular masonry mass, paired pointed Gothic portal recesses on front/back, broad cornice and four corner capstones that make a castle cue. Portals are blind recesses with solid backing. |
| Pawn / 16 | 40 / 26 | [assumed] Rooftop tank: continuous solid stem and shoulder, cylindrical tank, low conical roof and 1.8 mm-radius blunt tip. No thin freestanding water-tank legs. |

[assumed] Role height ordering is strict: king > queen > bishop > knight > rook > pawn. Each side has 1 king, 1 queen, 2 bishops, 2 knights, 2 rooks and 8 pawns. All role bases fit within one 42 mm square. There are no altered game rules, extra powers or nonstandard board spaces.

### Printability repair geometry

The following source changes add rising transitions below projecting features. These are design assumptions awaiting the current geometry and overhang checks; they are not print-success claims. All Z coordinates are local to the upright chessman.

| Role | Transition geometry |
|---|---|
| King | [assumed] Rectangular base shoulder rises from 19 × 16 mm at Z=4 to 25 × 22 mm at Z=8. Beneath the crossbar, a transition grows from a 3.2 × 3.2 mm stem at Z=77 to the 9 × 3.2 mm bar at Z=81. |
| Queen | [assumed] Base shoulder grows from 19 × 16 mm at Z=4 to 23 × 21 mm at Z=8. Crown support grows from 18 × 16 mm at Z=44 to 20 × 16 mm at Z=47. |
| Bishop | [assumed] Base transition grows from 0.8 times the reference wedge plan at Z=4 to the full plan at Z=8. Cornice support grows from 0.94 times the plan at Z=52 to 1.04 times at Z=54. Each horizontal recessed band's roof tapers from 0.885 to 0.94 times the plan over a 1.3 mm rise. |
| Knight | [assumed] Pedestal flares from 18 × 16 mm at Z=14 to 20 × 16 mm at Z=17. Diamond-shaped eye recesses replace circular recesses. |
| Rook | [assumed] Base shoulder grows from 17 × 15 mm at Z=4 to 21 × 19 mm at Z=8. Crown support grows from 21 × 19 mm at Z=41 to 24 × 22 mm at Z=44. |
| Pawn | [assumed] Tank shoulder grows from radius 5.4 mm at Z=17 to radius 8.5 mm at Z=22. |

## Cultural border requirements

All relief is original geometry fused into the panel backing, outside the playing field. None of the source links authorizes copying a logo, artwork, photograph or mesh, and none is used here. The five passages share the same relief level, line width and perimeter rail language.

| Passage | Global center X,Y / rotation | Geometry and grounded reference |
|---|---|---|
| Chinatown | 75,12 / 0° | Three compact gallery masses with recessed horizontal bands; a bent street trace. MOCA documents Doyers Street's sharp bend and NYC Archives documents adapted tong lau galleries. |
| Staten Island | 285,12 / 0° | Broad ferry hull, two deck levels, small stack and wake strokes. NYC DOT's ferry history grounds the daily St George–Whitehall connection. |
| Williamsburg | 12,108 / 90° | Masonry silhouette with three rounded-head recessed windows and a chimney. NYC Planning's sugar refinery account grounds the industrial waterfront reference. |
| Bronx | 110,372 / 180° | Paired concentric record rings with spindles and tonearm strokes on a common deck. Smithsonian sources ground Bronx hip-hop's two-turntable practice. |
| Queens | 372,276 / 90° | Elevated rail bars, repeated broad piers and two train cars. NY Transit Museum's International Express research grounds transport and community connections along the 7 line. |

The border is a selected cultural interpretation, not a comprehensive representation of any community. Both sides share all five references. No region is cast as an opposing faction.

## Assembly, print and stability requirements

[assumed] Panels are laid side by side on a flat table, with outer relief edges outward. They have no inter-panel retention. Dark-square pockets retain a 42 mm overall width. Internal pocket corners have 2 mm chamfers that leave material bridges between diagonally adjacent wells, eliminating the shared vertical edges that made the earlier checkerboard mesh nonmanifold. At panel seams only, the corner wedges are cut away to leave full square openings; this removes the thin wedges identified by the fixed-nozzle thickness check. The 2.4 mm backing floor remains continuous beneath each pocket.

[assumed] All 32 inlays use one universal shape: 41.5 mm overall with 2 mm chamfers at every corner, giving 0.5 mm total straight-edge clearance. Those chamfers leave small intentional corner gaps where pockets open square at panel seams. Each tile lowers vertically into its corresponding pocket and remains gravity seated.

[assumed] The 32 explicit tile paths in `measure/motion.json` sweep the tile from its installed position upward by 3 mm in 0.5 mm steps; the reversed path represents placement. These are collision checks, not friction, manufacturing-tolerance or retention tests. No blocked retention direction is claimed because none exists. Remove loose objects before moving the board.

[assumed] All print targets stand at Z=0 and fit the declared 220 mm build volume individually. Baseline slicer guidance is a 0.4 mm nozzle and 0.2 mm layer height; actual line width, cooling, material and calibration must be checked by the maker. Every printable must pass the geometric overhang gate in its supplied print pose at the default 45-degree threshold. The checker may report sufficiently short, supported bridge regions without failing; unsupported overhang regions must be repaired. Slicer support instructions do not waive this acceptance requirement. A passing geometric check still does not establish support-free results on every printer. The externally solid CAD is not a promise of 100% infill printing.

Stability comparison uses the actual uniform-solid CAD center of mass and the octagonal support polygon. A geometric tipping angle can be computed as `atan(horizontal support margin / center-of-mass height)` for the least favorable direction. This assumes a rigid body, level full base contact and uniform density. Printed infill distribution, warping, rough surfaces, friction, impacts and player handling can change behavior. Such a computation is a digital proxy only; no successful physical print or physical stability test is claimed.

## Digital acceptance record

[assumed] Before a Make-ready proposal, the project requires source-layout acceptance; topology and assembly interference checks; print-bed fit; one closed positive-volume shell per printable mesh; fixed 0.4 mm-nozzle thickness checks; the 32 gravity-tile placement sweeps; inventory/setup and dimension assertions; and inspection of the exact canonical product/role imagery. The independent visual review must identify recognizable chess roles and the architectural/cultural signatures. Only the generated reports establish which checks actually passed.

[assumed] Geometric overhang acceptance uses the default 45-degree threshold for every printable, as required above.

The complete workflow is documented in `../README.md`. From the Workshop workspace, the final local command is:

```sh
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/verify_project \
  artifacts/make/r0001/product/cad --exports --strict-fit \
  --bed 220x220x220 --motion-manifest measure/motion.json
```

After a shared-library change, rebuild the combined entry and every affected part explicitly. The current six-role printability repair uses this command from the Workshop workspace:

```sh
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/gen \
  artifacts/make/r0001/product/cad/city.step.py \
  artifacts/make/r0001/product/cad/part_king.step.py \
  artifacts/make/r0001/product/cad/part_queen.step.py \
  artifacts/make/r0001/product/cad/part_bishop.step.py \
  artifacts/make/r0001/product/cad/part_knight.step.py \
  artifacts/make/r0001/product/cad/part_rook.step.py \
  artifacts/make/r0001/product/cad/part_pawn.step.py --write --force
```

Then run `make_round` for the focused repair and the final integrated verification when ready. Source edits own geometry changes. The host performs its own authoritative isolated rebuild and stage gate. This document makes no publication, manufacture or delivery claim.
