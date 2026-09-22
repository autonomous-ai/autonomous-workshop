# Periastra Syzygy CAD

A corrected revision of the published Periastra. Miniature English draughts in a removable-roof observatory, where the two sides are the Sun and the Moon and the roof is the dome that tracks them. Four independently printable designs form 26 physical parts: one base, one domed roof, twelve Sun counters and twelve Moon counters. No hardware or power.

`periastra.step.py` is the combined closed assembly; `assembly.py` positions its live-source children. `part_base.step.py`, `part_roof.step.py`, `part_sun_counter.step.py` and `part_moon_counter.step.py` return bed-oriented parts. `periastra_lib.py` holds dimensions and geometry. The 26 structural part keys — `base`, `roof`, `single_01`..`single_12`, `forked_01`..`forked_12` — are unchanged from the published set; `single_*` is the Sun counter and `forked_*` is the Moon counter.

Base 190 by 190 by 24 mm, board 176 mm with 22 mm cells and 0.8 mm alternate recesses. The base is unchanged from the published set and its generated STEP reproduces the published hash exactly (`measure/check_fit.py` asserts it). Print on a 220 by 220 mm or larger bed, 0.4 mm nozzle. All part bottoms sit at Z=0. Roof backing rests on integral base ledges at Z=21; nominal lateral clearance 0.8 mm per side. Slide the loose roof vertically upward 100 mm for the illustrated reveal, then set it aside to play. The base stops downward roof motion; no upward latch exists. Store all 24 counters in starting rows beneath it; roof underside is 10 mm above smooth board floor.

The roof is a domed observatory, not a cone. A 182.4 mm square backing plate 3 mm thick carries a 180 mm drum 14 mm high; one square-cut rotation-ring seam 2 mm wide and 1 mm deep runs all the way round the drum, centred 4 mm below its top. A smooth spherical cap of 90 mm base radius and 40 mm rise — a sphere of radius 121.25 mm, deliberately not a half sphere — sits on the drum, apex at Z=78 closed. One 30 mm wide shutter slit with parallel square-cut walls is cut through both dome and drum on a single meridian, open from the bottom of the drum, over the apex, and 30 mm of surface run down the far side, so the far half of the cap stays unbroken. A blunt-ended 24 mm tube on a 45 degree axis emerges through the slit, carried on a fork of two 6 mm arms that cradle it and rise into prongs clear above it, standing on a solid pier on the plate; pier, arms and tube are one fused buttressed structure fused to both inside walls of the slit. Nothing else is added: no railing, walkway, ladder, panelling, ribs or rivets, and the dome is smooth.

Counters are plain round discs 16.0 mm across and 7.0 mm thick with a perfectly circular outline — no tail, tab, notch or projection — and a 1.0 mm chamfer on the man-face edge. The same symbol pocket, 1.2 mm deep with square vertical walls and a flat floor, is sunk into *both* faces of a counter, so the owner reads whichever way up it lies. The Sun mark is a 4.4 mm ball with eight separate rays, each widest at its inner end and narrowing to a blunt flat tip, with a 1.0 mm undisturbed band between the ball and every ray; the Moon mark is one bold crescent, 3.5 mm across at its waist, with both horns truncated square. The sun mark fits a 10.0 mm frame and the crescent an 8.0 mm one. Rank is the edge: the man face is flat and plain, and the king face carries a flat annular rebate 2.0 mm wide and 1.2 mm deep leaving a raised 12.0 mm plateau — the dome's rotation ring at counter scale — with the same mark sunk into it.

Digital verification is required before the final handoff. No physical print, tactile fit, strength, durability or human playtesting has occurred. Motion is unverified for this revision: no motion sweep, animation or independent motion review was run. Miniature equipment and reversible king marking are explicitly requested substitutions for tournament equipment; legal gameplay follows WCDF 2012 section 1, unrestricted opening.

Recess corners use a 1.5 mm radius to avoid diagonal point contacts; cell pitch and full side width remain 22 mm. Corner webs stay at the smooth floor height, with no raised grid. Final mesh checks include manifold edges and vertices.

## Revision notes

Two geometry decisions depart from the correction brief's literal numbers because the brief's own numbers cannot all hold at once; both are recorded in `review/revision-notes.md` with the arithmetic and the measured evidence:

- the sun's ball is 4.4 mm, not 6.0 mm, because 6.0 mm cannot coexist with a 10.0 mm overall extent, a 1.0 mm band and 1.8 mm rays;
- the crescent's flat horn tips are 2.17 mm, not 3.0 mm, because a 3.0 mm tip removes the concave bite that makes the mark read as a moon.

Two geometry decisions depart because a measured gate failed the literal form:

- the rotation-ring seam's upper wall is relieved at 50 degrees from vertical rather than square-cut, because a square-cut ceiling is a 178 mm-span unsupported ring (`review/trial-a-square-ring-groove-overhang.md`);
- counters print man face down rather than king face down, because the king-face-down pose leaves the 2 mm annular rebate floor as a 15.8 mm-span unsupported ring (`review/trial-b-counter-king-face-down-overhang.md`).

Three geometry decisions depart because an independent blind reader could not see what the correction requires:

- the slit runs 30 mm of surface arc down the far side rather than 30 mm of vertical drop, because the vertical reading opened the cap to 89 per cent of its radius and the reader saw a computer mouse rather than a dome;
- the fork arms rise into prongs clear above the tube, so the telescope has a visible mount;
- the crescent is drawn on an 8.0 mm outer circle rather than 10.0 mm, because at 10.0 mm it merged with the king rebate and the reader could see no crescent at all on that face.
