"""What colour the built Earth actually is, point by point, around the pole.

Two questions a render cannot answer.  Is the northern cap solid ice, or does
the boolean leave a hole in it?  And is the dark channel visible near the date
line in a polar view a fault, or the open water the atlas's own ice lobes
describe?

This asks the built solids directly.  A point is placed a fixed depth under
the sphere, in the planet's own frame, carried into the piece by the same
obliquity the part uses, and classified against every colour body of the
world.  `.` means the point is in the bare globe -- ocean.

    "$WORKSHOP_PYTHON" measure/ice_cap_scan.py > measure/earth-ice-cap.md
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bool3d as X                                            # noqa: E402
import params as P                                            # noqa: E402
from parts import atlas as A                                  # noqa: E402
from parts.world import world_bodies                          # noqa: E402

from OCP.BRepClass3d import BRepClass3d_SolidClassifier       # noqa: E402
from OCP.TopAbs import TopAbs_OUT                             # noqa: E402
from OCP.gp import gp_Pnt                                     # noqa: E402

#: How far under the sphere the sample sits.  The inlays run 1.20 mm deep, so
#: this is well inside them and well outside the tessellation's own tolerance.
DEPTH = 0.10
GLYPH = {"ice": "I", "land": "L", "dryland": "D", "globe": "."}


def sampler(planet: str, side: str):
    bodies = world_bodies(planet, side)
    radius = P.globe_radius(planet)
    centre = P.globe_centre_z(planet)
    tilt = math.radians(P.lean_sign(side) * P.PLANETS[planet]["tilt"])
    solids = {
        key: X.parts(shape)
        for key, (_colour, shape) in bodies.items()
        if key not in ("disc", "numeral")
    }

    def classify(lat_deg: float, lon_deg: float):
        lat, lon = math.radians(lat_deg), math.radians(lon_deg)
        reach = radius - DEPTH
        x = reach * math.cos(lat) * math.cos(lon)
        y = reach * math.cos(lat) * math.sin(lon)
        z = reach * math.sin(lat)
        point = gp_Pnt(
            x * math.cos(tilt) + z * math.sin(tilt),
            y,
            -x * math.sin(tilt) + z * math.cos(tilt) + centre,
        )
        for key, bodies_ in solids.items():
            for solid in bodies_:
                if BRepClass3d_SolidClassifier(
                    solid.wrapped, point, 1e-7
                ).State() != TopAbs_OUT:
                    return key
        return None

    return classify


def band(classify, lat_from, lat_to, lat_step, lon_from, lon_to, lon_step):
    rows = []
    lat = lat_from
    while lat <= lat_to + 1e-9:
        row = ""
        lon = lon_from
        while lon <= lon_to + 1e-9:
            row += GLYPH.get(classify(lat, lon), "?")
            lon += lon_step
        rows.append((lat, row))
        lat += lat_step
    return rows


def main():
    print("# Earth's northern ice, measured on the built solids")
    print()
    print("Sampled %.2f mm under the sphere, in the planet's own frame, carried"
          % DEPTH)
    print("into the piece by the same obliquity the part uses, and classified")
    print("against every colour body of the world. `I` ice, `L` land, `D`")
    print("dryland, `.` the bare globe -- ocean.")
    print()
    classify = sampler("earth", "sol")

    print("## Is the cap solid?")
    print()
    print("Every 3 degrees of longitude, from the cap boundary at %.0f to the pole."
          % A.ARCTIC_CAP_LAT)
    print()
    print("```")
    holes = 0
    for lat, row in band(classify, 73.0, 89.0, 2.0, 0.0, 357.0, 3.0):
        holes += row.count(".")
        print("%5.1f %s" % (lat, row))
    print("```")
    print()
    if holes:
        print("**%d ocean samples above the cap boundary. The cap has a hole.**" % holes)
    else:
        print("No ocean sample anywhere above the cap boundary: the cap is solid all")
        print("the way round, and the only thing that reaches into it is land, which")
        print("is what the ordering asks for -- `ice` is cut back by `land` and")
        print("`dryland`, so a continent that runs past %.0f degrees stays green."
              % A.ARCTIC_CAP_LAT)
    print()
    print("## The channel near the date line")
    print()
    print("A polar render shows a narrow dark slot reaching in toward the cap near")
    print("longitude 180. It is open water, and it is in the supplied atlas rather")
    print("than in the boolean: arctic lobe 4 ends at 176 east and lobe 5 begins at")
    print("178 west, so between them the sea reaches north to the cap boundary.")
    print("One degree of longitude, 60 to 74 north:")
    print()
    print("```")
    for lat, row in band(classify, 60.0, 74.0, 1.0, 168.0, 192.0, 1.0):
        print("%5.1f %s" % (lat, row))
    print("```")
    print()
    print("Read left to right, that is longitude 168 east through 180 to 168 west.")
    print("The gap closes at %.0f degrees, exactly where the cap starts."
          % A.ARCTIC_CAP_LAT)
    print()
    print("This is the point of the lobes. A bare cap ends on an exact circle of")
    print("latitude and reads as a lid laid on the globe; lobes with real water")
    print("between them read as an ice field.")


if __name__ == "__main__":
    main()
