# RIDGELINE — Great Wall Path Puzzle

Nine mountain-wall modules. Two watchtowers. One continuous route.

## Start playing

Open **manual.pdf**, the 13-page illustrated guide. Remove the nine modules
and point the tray's **N arrow away from you**. The engraved grid has nine
spaces numbered 0-8, left to right and top to bottom. Match those spaces to
the challenge diagram. Each square takes one module; its number becomes
covered when occupied.

Begin with the guided starter: copy its seven fixed pieces and leave cells
0 and 1 for A and S. Lift, turn in 90-degree steps and place the remaining
pieces upright. The grid marks guide placement; they do not lock pieces.
Keep the tray level and lift a piece clear of its neighbors before turning.

Win by connecting G1 to G2 through all nine modules, matching both direction
and height at every seam. Open ends and separate loops do not win. Cell
numbers 0-8 name positions; the diagram's circled 0/1/2 marks name route
heights. Fourteen challenge setups and their answers follow the starter.

## Parts and size

The inventory is A, B, C, D, S, T, U, G1, G2 and one cradle. G1 and G2 are
included in the nine modules. This revision keeps all nine module geometries
and their assembly placements. Only the cradle changes.

The assembled size is **174 x 182 x 63 mm**, including the north tab. The
original square tray body is 174 x 174 mm; the tab adds 8 mm at the top edge.
The cradle remains one solid part, 5.5 mm high. V-shaped grid lines and digits
are recessed 0.6 mm into its 4 mm floor, leaving at least 3.4 mm below them.
Each module is 55.6 mm square on a 56 mm placement pitch.

## Files and colors

- `assembled.step`: the complete revised assembly.
- `parts/cradle.step`: the numbered tray; the other nine STEP files are the
  unchanged playing pieces.
- `manual.pdf`: the current 13-page guide, including empty-tray setup.
- `renders/cradle-grid-*.png`: views of the empty numbered tray.

The STEP retains detailed native CAD face colors. A viewer that reduces
each solid to one color shows A/B/C sandstone, D light sand, S/T/U three moss
shades, G1 brick red, G2 teal and a dark cradle. `renders/web-part-colors*.png`
shows that representation. Other renders show the detailed CAD face styles.
The grooves and symbols are actual recessed geometry in either view.
These colors do not specify a manufacturing or multicolor slicing method.

## Editable source and reproduction

Use Python with build123d 0.11.1 and OCP. The editable geometry entry point is
`ridgeline.step.py`, with `ridgeline_lib.py`, `cadfits.py`, `states.py` and
`cradle_grid.py`. Grid pitch, depth, stroke width and the tab outline live in
`cradle_grid.py`. All original module geometry functions remain intact.

To regenerate the current colored assembly without rebuilding the nine
modules, run **`python board/revise_board.py`** from this folder. The script
reads the archived preceding assembly in `board/previous-edition.zip`, verifies
its hash, revises only the cradle, applies `colors/part-palette.json`, and
writes `assembled.step`, `parts/cradle.step` and `board/grid-audit.json`.
`python colors/part_colors.py` forwards to the same current revision method.
STEP export timestamps can change hashes on regeneration.

The historical face-color tools and inputs remain in `colors/` for source
reference. They precede this board revision; the current final regeneration
entry point is `board/revise_board.py`.

`board/build_manual.py` regenerates the manual from the archived original
guide and the included renders, using reportlab and pypdf. The starter,
challenge, solution and failure-example diagrams are retained. Original
puzzle definitions and solvers remain in `puzzle/`.

## Prototype status

This is a digital prototype. CAD checks verify the new marks, remaining floor
and absence of module/cradle volume intersections; physical printing, fit,
handling, durability, safety and human enjoyment have not been tested.
