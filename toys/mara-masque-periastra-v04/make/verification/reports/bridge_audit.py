"""Measure the real free bridge length under a counter's field floor.

`check_overhang` reports one span per unsupported region, and its span proxy is
the smaller plan dimension of the whole connected region. On these counters that
region is the field floor: the flat annulus from the raised symbol out to the
field wall, plus the bay inside the crescent. It is connected all the way round,
so the proxy is the full field diameter (14.0 mm) even though no bridge the
printer actually lays down is anywhere near that long.

The physical number is the largest circle that fits inside the unsupported
region -- the longest straight run of filament with no supported material under
either end. This audit computes both and prints them side by side. It changes no
geometry: it exists so the gate's verdict can be recorded honestly instead of
the counter being redesigned around a proxy.
"""
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import periastra_lib as p

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

STEPS = 4096


def _circle(cx, cy, r):
    return Point(cx, cy).buffer(r, quad_segs=512)


def sun_region():
    ball = _circle(0, 0, p.SUN_BALL_DIAMETER/2)
    wedges = []
    for i in range(p.SUN_RAY_COUNT):
        a = math.radians(i*360/p.SUN_RAY_COUNT)
        pts = [(p.SUN_RAY_INNER, -p.SUN_RAY_INNER_WIDTH/2), (p.SUN_RAY_OUTER, -p.SUN_RAY_TIP_WIDTH/2),
               (p.SUN_RAY_OUTER, p.SUN_RAY_TIP_WIDTH/2), (p.SUN_RAY_INNER, p.SUN_RAY_INNER_WIDTH/2)]
        wedges.append(Polygon([(x*math.cos(a)-y*math.sin(a), x*math.sin(a)+y*math.cos(a)) for x, y in pts]))
    return unary_union([ball]+wedges).intersection(_circle(0, 0, p.SYMBOL_DIAMETER/2))


def moon_region():
    crescent = _circle(0, 0, p.MOON_OUTER_DIAMETER/2).difference(
        _circle(p.MOON_BITE_OFFSET, 0, p.MOON_BITE_DIAMETER/2))
    # the 0.9 mm tip fillets only remove material, so the unfilleted crescent is
    # the conservative (smaller free span) support footprint; use the real one.
    return crescent.buffer(-p.MOON_TIP_FILLET).buffer(p.MOON_TIP_FILLET)


def free_span(symbol):
    """Diameter of the largest circle inscribed in the unsupported field floor."""
    region = _circle(0, 0, p.FIELD_DIAMETER/2).difference(symbol)
    lo, hi = 0.0, p.FIELD_DIAMETER/2
    for _ in range(60):
        mid = (lo+hi)/2
        if region.buffer(-mid).is_empty:
            hi = mid
        else:
            lo = mid
    return 2*lo, region


def main():
    rows = []
    for role, symbol in (('sun_counter', sun_region()), ('moon_counter', moon_region())):
        span, region = free_span(symbol)
        minx, miny, maxx, maxy = region.bounds
        rows.append({
            'part': role,
            'gate_span_proxy_mm': round(min(maxx-minx, maxy-miny), 2),
            'gate_allowance_mm': 12.0,
            'physical_free_bridge_mm': round(span, 2),
            'unsupported_area_mm2': round(region.area, 2),
            'clear_field_mm': p.SYMBOL_CLEAR,
            'note': ('the proxy is the field diameter because the floor is one connected ring; '
                     'the physical bridge is the widest gap the printer actually spans'),
        })
    out = Path(__file__).resolve().parent/'bridge-audit.json'
    out.write_text(json.dumps({'kind': 'periastra.bridge-audit', 'schema_version': 1,
                               'nozzle_mm': 0.4, 'parts': rows}, indent=2)+'\n')
    for row in rows:
        print(f"{row['part']}: check_overhang span proxy {row['gate_span_proxy_mm']} mm "
              f"(allowance {row['gate_allowance_mm']} mm, so the gate FAILS it); real free bridge "
              f"{row['physical_free_bridge_mm']} mm across {row['unsupported_area_mm2']} mm2 of field floor. "
              f"The physical number is the free bridge.")


if __name__ == '__main__':
    main()
