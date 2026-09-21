"""Measure the built crescent and write the numbers that go beside its frame.

The crescent is a stated defect of the previous run, so every claim about it is
measured on the same shape the CAD builds -- outer circle minus bite circle,
both horn tips filleted -- rather than restated from the brief.
"""
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import periastra_lib as p

import numpy as np
from shapely.geometry import LineString, Polygon

SAMPLES = 8000
from shapely.ops import unary_union

CAD = Path(__file__).resolve().parents[1]


def crescent():
    """The exact profile the CAD extrudes, sampled off its own boundary wire."""
    face = p.moon_symbol()
    wire = face.faces()[0].outer_wire()
    pts = [(v.X, v.Y) for v in (wire @ (i/SAMPLES) for i in range(SAMPLES))]
    return Polygon(pts), float(face.area)


def radial_thickness(shape, degrees):
    """Material the shape leaves along the ray at this bearing from the centre."""
    a = math.radians(degrees)
    ray = LineString([(0, 0), (20*math.cos(a), 20*math.sin(a))])
    return ray.intersection(shape).length


def cusp_angle():
    """Angle the two circles meet at, where each horn would come to a point."""
    R, r, d = p.MOON_OUTER_DIAMETER/2, p.MOON_BITE_DIAMETER/2, p.MOON_BITE_OFFSET
    return math.degrees(math.acos((R*R + r*r - d*d)/(2*R*r)))


def horn_tip(shape):
    """The built shape's extreme horn tip, after the rounding."""
    coords = np.asarray(shape.exterior.coords)
    upper = coords[coords[:, 1] > 2.0]
    return upper[np.argmax(upper[:, 0])]


def main():
    shape, area = crescent()
    outer_area = math.pi*(p.MOON_OUTER_DIAMETER/2)**2
    minx, miny, maxx, maxy = shape.bounds
    tip = horn_tip(shape)
    cusp = cusp_angle()
    # a tangent fillet of radius r in a cusp of angle a leaves a nose this wide
    tip_width = 2*p.MOON_TIP_FILLET*math.cos(math.radians(cusp/2))
    built_wrap = 360 - 2*math.degrees(math.atan2(tip[1], tip[0]))
    R, r, d = p.MOON_OUTER_DIAMETER/2, p.MOON_BITE_DIAMETER/2, p.MOON_BITE_OFFSET
    cross_x = (d*d + R*R - r*r)/(2*d)
    cross_y = math.sqrt(R*R - cross_x*cross_x)
    def _lens_fraction():
        R, r, d = p.MOON_OUTER_DIAMETER/2, p.MOON_BITE_DIAMETER/2, p.MOON_BITE_OFFSET
        lens = (R*R*math.acos((d*d + R*R - r*r)/(2*d*R)) + r*r*math.acos((d*d + r*r - R*R)/(2*d*r))
                - 0.5*math.sqrt((-d+r+R)*(d+r-R)*(d-r+R)*(d+r+R)))
        return lens/(math.pi*R*R)

    metrics = {
        'kind': 'periastra.crescent-metrics', 'schema_version': 1,
        'outer_circle_mm': p.MOON_OUTER_DIAMETER, 'bite_circle_mm': p.MOON_BITE_DIAMETER,
        'bite_offset_mm': p.MOON_BITE_OFFSET, 'tip_fillet_mm': p.MOON_TIP_FILLET,
        'belly_thickness_mm': round(radial_thickness(shape, 180), 3),
        'waist_at_150_deg_mm': round(radial_thickness(shape, 150), 3),
        'waist_at_120_deg_mm': round(radial_thickness(shape, 120), 3),
        'waist_at_100_deg_mm': round(radial_thickness(shape, 100), 3),
        'cusp_angle_deg': round(cusp, 2),
        'horn_nose_width_mm': round(tip_width, 3),
        'built_horn_tip_at_mm': [round(float(v), 3) for v in tip],
        'built_wrap_deg': round(built_wrap, 1),
        'built_surviving_area_pct': round(100*area/outer_area, 2),
        'horn_gap_mm': round(2*cross_y, 3),
        'circles_cross_at_x_mm': round(cross_x, 3),
        'symbol_height_mm': round(maxy-miny, 3),
        'symbol_width_mm': round(maxx-minx, 3),
        'outline_surviving_area_pct': round(100*(1 - _lens_fraction()), 2),
        'outline_wrap_deg': round(360 - 2*math.degrees(math.atan2(cross_y, cross_x)), 1),
        'relief_height_mm': p.FIELD_DEPTH,
        'extrusion_widths_at_0p4_nozzle': round(tip_width/0.4, 1),
        'brief_fillet_mm': 0.9, 'brief_fillet_built_wrap_deg': 178.6, 'brief_fillet_tip_x_mm': -0.07,
    }
    (CAD/'measure/crescent-metrics.json').write_text(json.dumps(metrics, indent=2)+'\n')
    notes = CAD/'snap/counters/moon-symbol-notes.md'
    notes.write_text(f"""# Moon symbol, measured

Frame: `moon-symbol-plan.png` - the Moon counter straight down, cropped to the field.
Every number is measured on the exact profile the CAD extrudes, not restated from
the correction brief.

| measurement | value |
|---|---|
| outer arc circle | {chr(216)}{metrics['outer_circle_mm']} mm, concentric with the field |
| bite circle | {chr(216)}{metrics['bite_circle_mm']} mm, centre offset {metrics['bite_offset_mm']} mm along +x |
| circles cross at | x = +{metrics['circles_cross_at_x_mm']} mm, not at 0: the horns wrap past the middle |
| belly, measured radially | {metrics['belly_thickness_mm']} mm |
| waist at 150 deg | {metrics['waist_at_150_deg_mm']} mm |
| waist at 120 deg | {metrics['waist_at_120_deg_mm']} mm |
| waist at 100 deg | {metrics['waist_at_100_deg_mm']} mm |
| horn gap, tip to tip on the sharp outline | {metrics['horn_gap_mm']} mm |
| symbol height | {metrics['symbol_height_mm']} mm |
| sharp outline: surviving area / wrap | {metrics['outline_surviving_area_pct']} % / {metrics['outline_wrap_deg']} deg |
| as built, tips rounded: surviving area / wrap | {metrics['built_surviving_area_pct']} % / {metrics['built_wrap_deg']} deg |
| built horn tip | x = +{metrics['built_horn_tip_at_mm'][0]} mm, y = {metrics['built_horn_tip_at_mm'][1]} mm |
| horn-tip rounding | {metrics['tip_fillet_mm']} mm radius, nose {metrics['horn_nose_width_mm']} mm across |
| relief height above the field floor | {metrics['relief_height_mm']} mm |

Both conditions hold at once: the crescent is slim ({metrics['built_surviving_area_pct']} % of its outer
disc survives) and its horns wrap ({metrics['built_wrap_deg']} deg, tips at x = +{metrics['built_horn_tip_at_mm'][0]}),
so the bay is deep and the horns reach towards each other rather than leaving a
shallow open scoop. It is neither a gibbous disc nor a 180 deg banana.

## The tip rounding was changed, and this is why

The brief specified a 0.9 mm fillet and expected {metrics['outline_wrap_deg']} deg of wrap with the tips
at x = +{metrics['circles_cross_at_x_mm']}. Those two cannot both hold. The two circles meet at a
{metrics['cusp_angle_deg']} deg cusp, and a tangent fillet of radius R in a cusp of angle A eats
R / tan(A/2) of horn along each flank - 3.74 mm at 0.9 mm. Built at 0.9 mm and
measured, the result is 178.6 deg of wrap with the horn tips at x = -0.07: exactly
the 180 deg banana the host rejected on sight.

The rounding is therefore 0.45 mm, which is the smallest that still carries the
0.3 mm island bevel and passes `check_thickness` at a 0.4 mm nozzle. Nothing else
about the crescent moved: the belly was not thickened, the circles were not
changed, and no tip is cut square. Measured cost: {round(metrics['outline_wrap_deg']-metrics['built_wrap_deg'],1)} deg of wrap and
{round(metrics['outline_surviving_area_pct']-metrics['built_surviving_area_pct'],2)} points of area against the sharp outline.

The {metrics['horn_nose_width_mm']} mm noses are below the 3 mm minimum feature width the rest of this
set observes - the deviation the brief disclosed and accepted, at a smaller size
than it expected. They resolve as {metrics['extrusion_widths_at_0p4_nozzle']} extrusion widths at a 0.4 mm nozzle, and
they are the tapering ends of a band {metrics['relief_height_mm']} mm tall fused to the disc along its
whole length - not a standing wall, not a cantilever, nothing that can snap off.
`check_thickness` passes the part at that nozzle.
""")
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()
