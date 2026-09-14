# Veinwake CAD brief

Original text-derived design; no reference images. The completed selected-Inventor handoff is the design authority. Units are millimetres. Origin is the board footprint centre, bottom on XY, front negative Y and up positive Z.

## Overall form and construction

A flat-bottomed, irregular rounded rock rind surrounds shallow neutral growth pockets. The teeth are tall hexagonal prisms with inward tapered blunt tips; the bubbles have three fused cylindrical lobes with upper hemispherical crowns. The rim remains low enough that the crystal bodies remain exposed. Direct sRGB colours are supplementary to silhouettes.

- `BOARD_LENGTH` = 140 mm and `BOARD_WIDTH` = 130 mm [observed] (Wish).
- `ASSEMBLED_HEIGHT` = 32 mm; each `CLUSTER_HEIGHT` = 26 mm [observed] (Wish).
- `RIM_HEIGHT` = 14 mm; `FIELD_HEIGHT` = 8 mm [assumed] (completed design).
- `SEAT_DEPTH` = 2 mm; `SEAT_Z` = 6 mm [observed] (Wish; inferred floor).
- `GRID_PITCH` = 36 mm; `FOOT_DIAMETER` = 28 mm [observed] (Wish).
- `SEAT_CLEARANCE` = 1 mm per side; `SEAT_DIAMETER` = 30 mm [observed] (Wish; inferred diameter).
- `FOOT_HEIGHT` = 3 mm; `CORNER_RADIUS` = 6 mm [assumed] (completed design).
- `FIELD_LENGTH` = 114 mm; `FIELD_WIDTH` = 104 mm; `FIELD_RADIUS` = 22 mm [assumed] (completed design).
- `TOOTH_RADIUS` = 11 mm; `TOOTH_SHOULDER` = 18 mm; `TOOTH_TIP_RADIUS` = 2.5 mm; `TOOTH_TIP_OFFSET` = 2 mm [assumed] (completed design).
- `LOBE_RADIUS` = 7 mm; `LOBE_CROWN_Z` = 19 mm [assumed] (completed design).
- `LOBE_CENTER_RADIUS` = 6 mm [assumed] (repair of tangent foot junction). The earlier centre radius was 7 mm [assumed] (original handoff); moving the centres inward leaves a 1 mm foot margin [inferred] and removes pinched material at the top of the foot. External marker width and height are unchanged.
- `HELD_OFFSET` = 55 mm [observed] (Wish).

## Components and manufacturing

One rind, five identical teeth and four identical bubbles [observed] (Wish). Each is a separate single solid because every marker must be freely placed and removed. All bottoms lie at local Z zero. No hardware, glue, bought component, electricity, supports or external visual reference is required. Geometry uses smooth normalized pebble extrusion with outer top rounding and two cavity levels, pocket subtraction, ruled crystal loft and revolved bubble lobes.

Minimum material below a pocket is 6 mm and between neighbouring pockets is 6 mm [inferred]. Minimum required wall is 3 mm [observed] (Wish). The tooth's flat tip is 4.330 mm across flats [inferred], exceeding the required 2 mm blunt-tip span [observed] (Wish). No full sphere underside or bottom-edge round creates an unsupported overhang.

## Placement and state evidence

Nine identical circular pockets are at the Cartesian product of negative pitch, zero and positive pitch. Seats accept either marker at any rotation. Place clusters downward into the board, lift upward to reset. The downward direction below the floor is blocked; upward withdrawal is clear. These are open gravity rests, with no upward retention claim.

The explicit clearance helper band is widened locally to 1 mm [observed] (Wish) for the open game pockets, then restored. This intentionally exceeds its ordinary hand-assembly fit default; it does not alter a verification threshold.

The normal complete assembly shows the legal draw XOXXOOOXX, read from back-left. The before/after sheet instead shows back-left and back-middle teeth, middle-left and centre bubbles, and a third tooth held over back-right before being lowered. Only the held tooth changes transform. Unused markers are omitted from this focused interaction sheet; the complete assembly contains the entire inventory.

## 8. Powered system / mechanism

Nothing is powered or mechanically driven. Players supply the placement action directly. There is no physical growth or joining. The source asserts pocket spacing, floor depth, blunt tip and assembled height feasibility. Motion evidence checks clear upward withdrawal and blocked downward floor travel for both marker habits; these are assembly-only paths, not an operating mechanism.

## Verification targets

Measure the actual solid bounds, circular seat sections and radial clearance; check each habit in all nine pockets, one solid per printable file, bed datum, mesh, thickness and overhang. Compare before/after part signatures and the single held translation. Inspect front, top and iso views plus fixed elevated front state sheet; perform independent blind review. Run exhaustive digital rules equivalence separately. Physical printing, handling and durability remain untested.

## Rind visual repair

The initial octagonal tray and its weak cavity failed independent review. The completed selected-Inventor repair replaces them with a periodic superellipse pebble and two geological bands [assumed] (rind-repair-handoff.md). `ROCK_EXPONENT` = 3.5; `ROCK_TOP_RADIUS` = 4 mm; `CAVITY_INSET` = 13 mm; `GROWTH_KEEPOUT_RADIUS` = 16.5 mm; `TERRACE_WIDTH` = 2.5 mm; `TERRACE_Z` = 11 mm [assumed] (completed repair design). The upper opening is clipped to an outer inset of 7 mm [inferred], leaving at least 3 mm material after the 4 mm exterior top round [inferred]. The 2.5 mm terrace is a backed ledge, not a thin wall. All required seats, markers, grid and total envelope remain unchanged.
