# Rainward Sun — final CAD specification

Text-derived original design; no reference image was supplied. Tags distinguish dimensions taken from the accepted Wish (`[observed]`), original design choices (`[assumed]`), and calculated consequences (`[inferred]`). The reviewed Mara Masque design supplies the construction intent. Historical rules and ink finishing are in [the playing instructions](../README.md).

## Required form and inventory

- The Sun alone is 190 × 190 × 28 mm [observed] (WISH.json). All individual parts stay below 200 mm [observed] (WISH.json). Accessories stand separately on the table; the whole displayed set is not one bed footprint.
- Exactly35 printed parts: one Sun, fifteen single-tail drops, fifteen fork-tail drops, two identical cubic dice and two open cups. All are loose, directly lifted and placed. No hardware, hinges, lids, captured joint, hidden path, added powers or doubling cube.
- Every drop is 12 × 8 × 4 mm [observed] (WISH.json), with planar top and bottom. Tail necks and cup walls/floors are at least 2 mm [observed] (WISH.json).
- Four banks each have six open lanes. Every point has five radial positions and three layers, so any point can hold all fifteen drops. Shape distinguishes sides without color.

## Coordinates and Sun construction

- Units are millimeters. The base is XY, center at origin and +Z upward. Every production entry rests at z=0; the combined entry uses table and board placements.
- Body disk radius 90 mm [assumed], deck height 16 mm [assumed]. Sixteen integral vertical ray lobes each have radius 5 mm [assumed], centered on that disk radius at equally spaced angles. The resulting maximum span is 190 mm [inferred] (twice the sum of body and ray radii).
- Global lane p has angle `-75 + 15*(p-1)` degrees. Four bank boundaries use recessed separators 3 mm [assumed] wide; other separators are 2 mm [assumed] wide. All recesses are 0.6 mm [assumed] deep and extend radially from 27 mm [assumed] to 88 mm [assumed]. No raised partition obstructs a drop.
- Drop center radii are 85,72,59,46,33 mm [assumed]. Consecutive envelopes have 1 mm [inferred] (radial pitch minus drop length) end clearance. Layers start at heights 16,20,24 mm [inferred] (deck plus multiples of drop thickness).
- The remaining deck below a groove is 15.4 mm [inferred] (deck minus groove depth). The disk and all rounded rays have one common flat underside.

## Drop and bar geometry

Both drop outlines are original closed polygons extruded to the specified thickness. Coordinates are `(radial,tangential)` in the part-local plane. Single tail: `[(-6,-1),(-6,1),(-2,2),(0,4),(3,4),(6,2),(6,-2),(3,-4),(0,-4),(-2,-2)]`. Fork tail: `[(-6,-3),(-6,-1),(-2,-1),(-2,1),(-6,1),(-6,3),(-2,3),(0,4),(3,4),(6,2),(6,-2),(3,-4),(0,-4),(-2,-3)]`. These coordinates are [assumed] original shape decisions satisfying the observed bounding box and blunt-tail minimum. Neither has top relief, a pointed thin tip, or an internal connector.

- The bar is an integral circular exposed platform of radius 24 mm [assumed] whose top is at height 24 mm [assumed]. Two far-side blunt crest lobes reach the Sun's specified maximum height and remain outside the six landing rectangles.
- Those rectangles have centers at x=-12,0,12 mm [assumed] and y=-5,+5 mm [assumed]. Six positions with up to five layers provide geometric capacity for all thirty drops; this is storage capacity, not a claim that all-bar states are legally reachable.
- Drops are oriented with tails inward. Adjacent polygon footprints at the innermost radial station must be checked as polygons; overlapping bounding rectangles do not imply intersecting shapes.

## Dice and cups

- Dice are identical solid cubes of edge 16 mm [assumed]. Use homogeneous solid printing and thin ink pips on all faces before play, opposite pairs summing to seven. There are no unequal engraved pip volumes. CAD symmetry preserves the intended ideal probability model; printed fairness requires physical qualification.
- Cups have outside diameter 42 mm [assumed], inside diameter 38 mm [assumed], height 28 mm [assumed], wall 2 mm [inferred] (half the diameter difference), and floor 2 mm [assumed] (satisfies observed minimum). Their open side faces up for printing.
- Two cubes side by side span a rectangle whose diagonal is 35.777 mm [inferred] (Pythagoras from two cube edges along one axis and one along the other), smaller than the cup interior. Dice are rolled on the unobstructed table, not on occupied lanes.

## Exact setup and signature states

A uses global points directly and travels24→1. B's own point q is global25-q and B travels1→24. Each side's standard own-point counts are24:2,13:5,8:3,6:5. Canonical setup has thirty drops and empty bar.

The legal trace is A6,1:13→7,8→7; B6,1:global12→18,1→2. A then rolls6,2. BEFORE freezes before A's six-point submove7→1; AFTER replaces the lone B on1 with the attacker and puts that B fully exposed on the raised bar. The remaining2 can play8→6. Only attacker and victim change poses; other twenty-eight drops, Sun, dice and cups retain exact transforms. This is one ordinary legal submove, not an extra mode.

- Victim initially has radius 85 mm [assumed], angle-75degrees and underside at deck height. Its blunt outer end overhangs the disk by 1 mm [inferred] (center radius plus half drop length minus disk radius) between the rounded rays; most of its footprint and its centroid remain supported.
- Its bar radius is `85 - sqrt(80*80 - 8*8)` = 5.4010050314704 mm [inferred] (required displacement and vertical height difference). Its underside rises 8 mm [inferred] (bar top minus deck). The full three-dimensional displacement is exactly 80 mm [observed] (WISH.json).
- State exports are [../evidence/states/before.step](../evidence/states/before.step) and [../evidence/states/after.step](../evidence/states/after.step). A fixed high three-quarter camera uses azimuth-75degrees and elevation55degrees [assumed]. Full setup hero and before/after interaction sheet use exact exported solids; only neutral state labels are added.

## Verification and limits

Generate the single combined entry and all thirty-five `part_*.step.py` occurrences. Require one positive watertight solid per production entry, flat bed contact, per-part envelope fit, no unintended combined clashes, and passing mesh, overhang and thickness gates at nozzle 0.4 mm [assumed] (manufacturing standard). `measure/check_fit.py` checks lane count/capacity, exact polygon separation, cup clearance, rim support, bar footprint and signature displacement. `measure/check_rules.py` checks setup and the legal signature trace. The specification numbers are checked against source geometry where supported by the deterministic suite.

The astronomy is an abstract analogy, not plasma simulation. No physical printing, tactile handling, stack stability, durability, statistically fair rolling or human playtesting has occurred. Round records and independent visual review preserve their actual evidence and limitations.
