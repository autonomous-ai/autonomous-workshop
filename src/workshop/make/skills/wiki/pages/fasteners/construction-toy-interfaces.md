---
title: Construction-toy and play-system interfaces
tags: [construction-toy, brick, stud, anti-stud, compatibility, duplo, wooden-railway, track-connector, magnetic-tile, rod-connector, coupon]
aliases: [lego compatible, lego-compatible brick, brick compatible, building brick, stud and tube, studs and tubes, anti-stud, clutch power, stud pitch, stud coupon, duplo, duplo compatible, brio, brio compatible, wooden railway, wooden train track, toy train track, track connector, track peg, magnetic tile, magnetic building tile, knex, rod and connector, construction toy accessory]
sources:
  - https://www.cailliau.org/Alphabetical/L/Lego/Dimensions/More%20Dimensions/BBEditPreviewTemp.html (stud 4.8-4.9 mm, 1.8 high, 1.9 over the logo; n x 8 - 0.2 widths; studs held at about three rim points; moulds under 0.01 mm; Technic hole close to 4.90 at 5.8 mm and a stud fits it tightly)
  - http://www.lugnet.com/~330/FAQ/Build/dimensions (measured pitch 7.985-7.986, brick 9.582, plate 3.194; wall 1.5, stud height 1.7; bricks kept short of the grid so they do not push apart)
  - https://notebook.zoeblade.com/Lego_brick_dimensions.html (1.6 mm unit; stud 3 u, plate 2 u, brick 6 u; 0.1 mm per side)
  - https://patents.google.com/patent/US3005282A/en (tube touches four studs; each stud tangent at three points, tube and wall; tube bore equals stud diameter; filed 1958, expired)
  - https://github.com/cfinke/LEGO.scad (printable library: stud 4.8 x 1.8, wall 1.2 plus ribs, 0.1 wall play, 0.03 stud play, 3.18 bar in a 3.2 hollow stud, roof 1.0; per-printer stud_rescale 1.022-1.0475; DUPLO stud 9.4 x 4.5, hollow 6.5 with a 1.4 wall, tube 13.1; tiles print upside down)
  - https://raw.githubusercontent.com/openscad/MCAD/master/lego_compatibility.scad (knob 4.8, wall 1.45, post 6.5, pin 3, roof 1.05)
  - https://www.meshy.ai/blog/lego-compatible-3d-print-tolerances (vendor guide: moulded +/-0.01 vs FDM +/-0.1-0.2; printed stud target 4.75-4.85, anti-stud 4.90-5.00; a 4.95 stud will not connect, 4.65 falls out; XY compensation -0.08 to -0.18; ABS offsets differ from PLA)
  - https://EduTechWiki.unige.ch/en/Doblo_factory (DUPLO 16 mm grid, 19.2 and 9.6 heights, stud r 4.6-4.8, hollow r 3.22; 2x scaling holds for outside sizes only; too fat beats too slim, a loose fit cannot be fixed; three walls minimum)
  - https://www.lego.com/en-us/service/help/building-with-lego-and-duplo-bricks-ka000 (System bricks fit DUPLO with hollow studs; only even-stud System bricks fit under DUPLO)
  - https://www.dorsey.com/newsresources/publications/2010/09/lego-trade-mark-application-hits-a-brick-wall (brick shape refused as a trademark because purely functional; the expired patent is strong evidence)
  - https://en.wikipedia.org/wiki/Wooden_toy_train (track 40 x 12, grooves 6 wide 3 deep 20 apart; connector table pin 11.2, hole 12.5-13, neck 4.9-6.8, gateway 7.2-8.7; no agreed gauge)
  - https://woodenrailway.info/track/brio-track-guide (peg 11.5 on a 7 mm neck, socket 15-17 with a 5 mm throat; joint stretches 2-3 mm; groove centres 26, double track 46; curves 182/222 and 90; ascending piece 64 mm over 216)
  - https://github.com/dotscad/trains/blob/master/tracklib.scad (printable track: 40 x 12, wells 5.7 wide 3 deep 19.25 apart, plug r 6 on a 6 mm neck centred 12 mm from the end, socket r + 0.3, throat 7.5, 1 mm bevels)
  - https://patents.google.com/patent/US12377362B2/en (magnet free to rotate in an edge pocket; one at the side centre or two equidistant from it; fixed polarity limits orientations)
  - https://patents.google.com/patent/US5061219A/en (rod nominal 0.250 in, socket throat about 0.210 in; arms spread and close on a groove behind the end flange; 15 degree lead-in)
  - https://en.wikipedia.org/wiki/K%27Nex (pieces moulded in polyoxymethylene)
related: [push-pins-and-clip-fasteners, fdm-hole-accuracy, fit-derivation, dowel-pins-and-press-fits, fdm-first-layer-and-warping, magnets-and-strap-slots, toy-safety-constraints, snap-fit-design, creep-and-stress-relaxation, filament-properties, layer-anisotropy, known-object-sizes]
updated: 2026-10-10
---

# Construction-toy and play-system interfaces

A printed accessory for a brick, track or tile system joins a moulded part
whose half of every joint is fixed. Find the one dimension that carries the
joint, compare its moulded tolerance with what FDM holds, and calibrate that
dimension on a coupon. Technic pins and cross axles are in
[[push-pins-and-clip-fasteners#construction-toy-friction-pins]] and
[[push-pins-and-clip-fasteners#cross-axles-in-cross-holes]].

## Brick-system nominal dimensions

Everything derives from the pitch `p` and the stud diameter `d`; a 1.6 mm unit
gives stud 3 u, plate 2 u, brick 6 u.

| feature | value (mm) | note |
|---|---|---|
| stud pitch `p` | 8.0 | measured 7.985–7.986 |
| stud diameter `d` | 4.8 | measured 4.8–4.9 |
| stud height | 1.7–1.8 | 1.9 over a moulded logo |
| plate / brick height | 3.2 / 9.6 | measured 3.194 / 9.582 |
| outside of an n-stud side | `n·p − 0.2` | 0.1 short of the grid per side, so bricks never push apart |
| wall, 2-wide and wider | 1.45–1.5 | inner face at `(p − d)/2 = 1.6` from the grid line |
| wall, 1-wide | 1.2 + ribs | ribs reach the stud |
| underside tube OD | `p·√2 − d` = 6.51 | 6.5 in a library |
| underside tube bore | `d` = 4.8 | patent claim; a tube also seats on one stud |
| underside pin, 1-wide | `p − d` = 3.2 | 3.0–3.14 in libraries |
| hollow stud bore / bar | 3.2 / 3.18 | the bar presses in |
| Technic hole | 4.8–4.9, axis 5.8 above the brick bottom | |

## Where the clutch is

- **A three-point clamp at the stud rim.** The tube sits in the middle of four
  studs and touches all four; each stud touches the tube and a wall (the
  patent's three points). Stud diameter, tube OD and the wall's inner face set
  the grip; stud height and roof only stack. In 1-wide bricks the pin
  (`p − d`) and the wall ribs do the tube's work.
- **Nominal is line-to-line.** `p·√2 − d` and `(p − d)/2` are the tangency
  sizes for a 4.8 stud. The grip is the measured stud's excess, up to about
  0.05 mm per contact, taken up by flexing the thin tube wall (~0.85 mm) and
  the walls, which bow into the 0.1 mm side gap. Moulds held under 0.01 mm
  make every joint the same force.

## Why a printed stud needs its own number

- **The printer's error is 5–10× the interference.** Untuned FDM lands at
  ±0.1–0.2 mm; printed holes come out 0.1–0.3 undersize and pins about 0.1
  oversize ([[dowel-pins-and-press-fits#the-fdm-fit-ladder]]). A printed stud
  measuring 4.95 does not connect; one measuring 4.65 falls out.
- **The error has no universal sign.** One library's per-printer presets
  enlarge the modelled stud by 2.2–4.75 % (4.91–5.03 mm); a slicer guide
  shrinks it with −0.08 to −0.18 mm XY compensation. Corner cutting shrinks
  small circles ([[fdm-hole-accuracy#why-a-vertical-hole-comes-out-small]])
  while over-extrusion grows outer contours; which wins is the printer's.
- **Material.** PLA (about 3.4 GPa) is stiffer than ABS (2.1–2.4)
  ([[filament-properties#rules-that-fall-out-of-the-table]]), so the same
  interference grips harder and splits a thin tube; PLA creeps, so a tight
  joint loosens ([[creep-and-stress-relaxation#design-rules]]). PETG grips
  softer; ABS shrinks more, so PLA offsets do not transfer.
- **Err tight**: a tight print can be eased, a loose one cannot be fixed. The
  printed targets people converge on are *measured* values, stud 4.75–4.85
  and anti-stud bore 4.90–5.00 (vendor guide); reach them through a coupon.

## A stud coupon

- One row of seven studs modelled at 4.70, 4.75 … 5.00, indexed by notches on
  the side wall; a row of round sockets modelled at 4.80 … 5.10 for real
  studs; for a part that sits on studs, three 2×2 cells with tube OD 6.40 /
  6.50 / 6.60. Print it with the part's material, nozzle, layer height,
  profile and orientation, and measure each stud in two directions.
- Pass: holds a genuine 2×2 brick upside down when shaken and lets go to
  fingers without a tool. When two neighbours pass, take the smaller.
- Write the winner as `STUD_D_PRINT` with "coupon, material" provenance and
  re-run it for every new filament or printer
  ([[dowel-pins-and-press-fits#prove-it-on-a-coupon]]).

## Which half to print

- **Studs on the accessory** (bricks go on top): one dimension to calibrate,
  printed as vertical cylinders, the most accurate printed feature.
- **Anti-studs on the accessory** (it sits on studs): tube OD and wall face
  must both hit and their errors add. The simplest printed anti-stud is one
  round socket per stud, about Ø 4.9 as printed (a Technic hole that size grips
  a stud round its whole rim), tuned on the coupon's socket row.
- Keep printed tubes hollow, wall ≥ 2 line widths, so they flex like moulded
  ones; a solid post turns every 0.05 mm of print error into interference.
- Underside cavity depth ≥ stud height + 0.1, or the part rides on its studs.
- Long arrays: 16 × (8.000 − 7.986) = 0.22 mm, the whole side gap. A plate
  that binds only at its ends has a pitch or XY-scale error, not a stud error.

## Print orientation

- **Studs up, underside on the bed**; the roof bridges the open underside and
  prints rough there. A part with a smooth top and no studs (a tile) prints
  top down, so its underside faces up and needs no bridge.
- The tube and wall bottoms are the first layers, so elephant's foot widens
  the tube and narrows the wall face where a stud enters: model a 0.3 mm 45°
  chamfer on those bottom edges ([[fdm-first-layer-and-warping#elephants-foot]]).
- A stud on a side face prints as a horizontal cylinder, faceted and oval
  ([[fdm-hole-accuracy#horizontal-holes-teardrops-and-horiholes]]): calibrate
  it in that orientation or avoid it. Give walls at least three perimeters.

## DUPLO: the doubled grid

| feature | value (mm) |
|---|---|
| pitch; brick / plate height | 16.0 (`2·p`); 19.2 / 9.6 |
| stud diameter / height | 9.2–9.6 (9.4 in a library) / 4.5–4.55 |
| hollow stud bore | 6.44–6.5 (wall about 1.4) |
| underside tube OD | 13.1 (`16·√2 − 9.4` = 13.2) |

- **2× holds for grid and heights only**: never scale a System model by two.
- **System on DUPLO:** the hollow stud's bore equals the System tube's OD, so
  a System tube plugs into a DUPLO stud; the maker says System bricks fit only
  where DUPLO studs are hollow. A printed DUPLO stud that must take both
  systems is hollow, and its bore is a second coupon fit.
- **DUPLO on System:** the maker says only even-stud System bricks (2×2, 2×4)
  fit under DUPLO; no source here gives the mechanism, so measure a real
  DUPLO underside first. DUPLO-scale parts are for under-3s: keep every part,
  and anything that can break off, out of the
  [[toy-safety-constraints#small-parts-the-choke-test]].

## Wooden railway track

There is no agreed gauge; sources span these ranges.

| feature | value (mm) |
|---|---|
| track width / height; double-track centres | 40 / 12; 46 |
| groove width / depth | 5.7–6 / 3 |
| groove inner spacing / centres | 19.25–20 / 24.95–26 |
| peg diameter / neck width | 11.2–12 / 4.9–7 |
| peg centre from the track end | about 12–12.75 |
| socket diameter / throat width | 12.5–13 (one collector reports 15–17) / 7.2–8.7 |
| curves | 8 × 45° per circle; inner radius 182 (outer 222) or 90 |
| straights; ascending piece | 54, 72, 108, 144, 216; rises 64 over 216 |

## Joining printed track to wooden track

- **The play is the design.** Sockets run 0.6–1.8 larger than pegs and
  throats 1.5–2.3 wider than necks, so a joint stretches 2–3 mm and bends a
  few degrees, which lets loops close. That play is about ten times FDM error,
  so no coupon is needed; keep it: peg ≤ 11.5, socket ≥ 13, throat ≥ neck +
  1.5, and one printed piece joins every brand in the table. A socket sized
  with a snug or press class defeats it.
- **Print flat, grooves up.** The peg and neck lie in the layer plane, so a
  pull or bend loads them along the strands ([[layer-anisotropy]]), and the
  outlines print round. Bevel the socket mouth and groove ends about 1 mm so a
  wheel crossing a step does not catch; round the neck root in plan.
- **Ramps and piers.** One ascending piece rises 64 mm, so a printed pier for
  the upper level holds the track bottom at 64 mm. Round every crest and sag
  so a car of wheelbase `b` keeps belly clearance `c`: `R ≥ b² / (8·c)`.
- **Wheels run in the grooves.** Centre each wheel in the overlap of every
  brand's groove span. Worked: spans of 9.6–15.3 and 10–16 mm off the
  centreline overlap at 10–15.3, so wheel centres sit 25.3 mm apart and the
  tread is at most 4.3 mm wide with 0.5 mm clearance a side.

## Magnetic tiles

- Commercial tiles put one magnet at the centre of each side, or two
  equidistant from its midpoint, so sides align whichever way they meet.
- Fixed poles limit which ways tiles join. The remedy is a magnet free to turn
  in an edge pocket (a cylinder on its axis, or a sphere), poles across the
  diameter: print it with a free running clearance and seal it in with a
  pause ([[magnets-and-strap-slots#pause-and-embed]]); a press fit cannot turn.
- With fixed magnets, put opposite poles at equal distances either side of
  the midpoint: tiles face up always meet N to S, a flipped tile repels. Mark
  every pocket ([[magnets-and-strap-slots#polarity]]).
- No source gives tile edge or magnet positions: measure the set to be joined.
  Embedded magnets must survive abuse testing ([[toy-safety-constraints#magnets]]).

## Rod-and-connector systems

- The founding patent's rod is 0.250 in (6.35 mm) and its socket throat about
  0.210 in (5.3 mm), so each arm spreads about 0.5 mm and closes into a groove
  behind the rod's end flange; a stiff inner cavity holds the flange axially,
  and the arm tips diverge about 15° as a lead-in.
- The pieces are moulded in acetal (POM), far more forgiving than PLA. Size a
  printed connector as a cantilever snap ([[snap-fit-design#permissible-strain]]),
  `ε ≈ 1.5·h·y / L²`: with `h = 1.5`, `y = 0.51` a 5 mm arm strains 4.6 %, an
  8 mm arm 1.8 %. Lay it flat so the arms flex in the layer plane, or use PETG
  or nylon. Rod sizes differ between product lines: measure the rod.

## Naming

The functional dimensions are free (the patents expired; the EU Court of
Justice refused the brick shape as a trademark because it is functional), but
the names are trademarks: never on the part or as maker; say "compatible with".

## Checks

```python
import math
assert math.isclose(TUBE_OD, STUD_PITCH * math.sqrt(2) - STUD_D, abs_tol=0.05), "tube misses the four diagonal studs"
assert math.isclose(WALL_FACE_FROM_GRID, (STUD_PITCH - STUD_D) / 2, abs_tol=0.05), "wall face not tangent to the stud"
assert 4.70 <= STUD_D_PRINT <= 5.05 and STUD_D_PRINT_FROM_COUPON, "printed stud not calibrated on a coupon"
assert TUBE_HOLLOW and TUBE_WALL >= 2 * LINE_W, "solid or one-line tube"
assert UNDERSIDE_DEPTH >= STUD_H + 0.1, "part rides on its studs"
assert DUPLO_PITCH == 2 * STUD_PITCH and math.isclose(DUPLO_HOLLOW_ID, TUBE_OD, abs_tol=0.1)
assert PEG_D <= 11.5 and SOCKET_D >= 13.0 and THROAT_W >= NECK_W + 1.5, "printed track loses the joint play"
assert CREST_R >= WHEELBASE**2 / (8 * BELLY_CLEARANCE), "car grounds on a ramp crest"
assert 1.5 * ARM_T * ARM_Y / ARM_L**2 <= EPS_ALLOW, "printed rod connector arm cracks"
```

Open items: clutch force, its loss to creep and a free magnet's rotation are
forces and motion no rigid gate measures; record each as a coupon or play test.
