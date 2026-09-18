# Moon symbol, measured

Frame: `moon-symbol-plan.png` - the Moon counter straight down, cropped to the field.
Every number is measured on the exact profile the CAD extrudes, not restated from
the correction brief.

| measurement | value |
|---|---|
| outer arc circle | Ø12.5 mm, concentric with the field |
| bite circle | Ø11.2 mm, centre offset 2.85 mm along +x |
| circles cross at | x = +2.776 mm, not at 0: the horns wrap past the middle |
| belly, measured radially | 3.5 mm |
| waist at 150 deg | 3.303 mm |
| waist at 120 deg | 2.648 mm |
| waist at 100 deg | 1.899 mm |
| horn gap, tip to tip on the sharp outline | 11.199 mm |
| symbol height | 12.5 mm |
| sharp outline: surviving area / wrap | 37.85 % / 232.7 deg |
| as built, tips rounded: surviving area / wrap | 36.95 % / 206.6 deg |
| built horn tip | x = +1.355 mm, y = 5.729 mm |
| horn-tip rounding | 0.45 mm radius, nose 0.875 mm across |
| relief height above the field floor | 1.5 mm |

Both conditions hold at once: the crescent is slim (36.95 % of its outer
disc survives) and its horns wrap (206.6 deg, tips at x = +1.355),
so the bay is deep and the horns reach towards each other rather than leaving a
shallow open scoop. It is neither a gibbous disc nor a 180 deg banana.

## The tip rounding was changed, and this is why

The brief specified a 0.9 mm fillet and expected 232.7 deg of wrap with the tips
at x = +2.776. Those two cannot both hold. The two circles meet at a
27.13 deg cusp, and a tangent fillet of radius R in a cusp of angle A eats
R / tan(A/2) of horn along each flank - 3.74 mm at 0.9 mm. Built at 0.9 mm and
measured, the result is 178.6 deg of wrap with the horn tips at x = -0.07: exactly
the 180 deg banana the host rejected on sight.

The rounding is therefore 0.45 mm, which is the smallest that still carries the
0.3 mm island bevel and passes `check_thickness` at a 0.4 mm nozzle. Nothing else
about the crescent moved: the belly was not thickened, the circles were not
changed, and no tip is cut square. Measured cost: 26.1 deg of wrap and
0.9 points of area against the sharp outline.

The 0.875 mm noses are below the 3 mm minimum feature width the rest of this
set observes - the deviation the brief disclosed and accepted, at a smaller size
than it expected. They resolve as 2.2 extrusion widths at a 0.4 mm nozzle, and
they are the tapering ends of a band 1.5 mm tall fused to the disc along its
whole length - not a standing wall, not a cantilever, nothing that can snap off.
`check_thickness` passes the part at that nozzle.
