"""Neptune's companion cloud, turned toward the light.

`render_review` lights every scene from one fixed direction above the table,
so a marking on the southern half of a globe always sits in shade: at the
per-world frames the white companion cloud renders at the same mid grey as
the white band beside it, and close to the dark_gray spot.  The filaments are
sealed correctly (white #FFFEF7, dark gray #6F6E6D); it is the picture that
compresses them.  A person holding the piece would simply tilt it.

This frame does exactly that and nothing else.  It takes the exact colour
bodies `parts.world.world_bodies` builds, tessellated the way
`world_views._tessellate` does, and turns the WHOLE piece rigidly about the
globe's centre so the companion's outward direction points at the renderer's
own light, then photographs it from that same direction.  No colour, shading
rule or geometry is changed.  The base disc and its numeral inlay -- the bodies
that lie entirely at or below the disc's top face -- are left out of this one
frame, because once the piece is turned over the disc stands between the
camera and the southern hemisphere on the Sol army.  Every body of the globe,
its seat and its markings is drawn.

    "$WORKSHOP_PYTHON" companion_frame.py <scratch>/worlds \\
        <cad-skill-scripts-dir> snap/worlds

The scratch directory holds `neptune-<side>.step`, which `world_views.py`
writes.  Output: `snap/worlds/neptune-<side>-companion-lit.png`.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from build123d import Pos

import params as P
import parts.neptune_atlas as N
from features.patches import planet_frame
from world_views import FRAME_SIZE, _renderer, _tessellate

#: `render_review.render`'s own light direction, copied so the frame can face
#: it; the renderer keeps using its own copy.
LIGHT = np.array([0.35, -0.45, 0.82]) / np.linalg.norm([0.35, -0.45, 0.82])


def _rotation(a, b):
    """The rotation taking unit vector a onto unit vector b (Rodrigues)."""
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    s = float(np.linalg.norm(v))
    if s < 1e-12:
        return np.eye(3)
    k = v / s
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + s * K + (1 - c) * (K @ K)


def companion_direction(side: str) -> np.ndarray:
    """The companion centre's outward unit direction, in the piece frame."""
    lat, lon = math.radians(N.COMPANION_LAT), math.radians(N.COMPANION_LON)
    local = (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon),
             math.sin(lat))
    frame = planet_frame(P.PLANETS["neptune"]["tilt"], P.lean_sign(side),
                         P.globe_centre_z("neptune"))
    tip = (frame * Pos(*local)).position
    centre = (frame * Pos(0, 0, 0)).position
    d = np.array([tip.X - centre.X, tip.Y - centre.Y, tip.Z - centre.Z])
    return d / np.linalg.norm(d)


def render_side(side: str, steps: Path, scripts: Path, target: Path) -> Path:
    render_review = _renderer(scripts)
    _src, shape = render_review.build_shape(steps / ("neptune-%s.step" % side))
    occurrences = [item for item in _tessellate(render_review, shape)
                   if item[0][:, 2].max() > P.DISC_H + 1e-6]
    rot = _rotation(companion_direction(side), LIGHT)
    centre = np.array([0.0, 0.0, P.globe_centre_z("neptune")])
    turned = [((points - centre) @ rot.T + centre, faces, colour)
              for points, faces, colour in occurrences]
    # The camera leans 30 degrees away from the seat cone, which stands out
    # from the sphere below latitude -42 and would otherwise hide the Sol
    # army's companion.  Shading depends only on each face's normal against
    # the light, so moving the camera changes the view, not the tone.
    seat = rot @ np.array([0.0, 0.0, -1.0])
    away = seat - np.dot(seat, LIGHT) * LIGHT
    view = LIGHT - math.tan(math.radians(30.0)) * away / np.linalg.norm(away)
    view /= np.linalg.norm(view)
    azimuth = math.degrees(math.atan2(view[1], view[0]))
    elevation = math.degrees(math.asin(view[2]))
    out = target / ("neptune-%s-companion-lit.png" % side)
    render_review.render(turned, azimuth, elevation, FRAME_SIZE, 0.05).save(out)
    return out


if __name__ == "__main__":
    for side in ("sol", "anti"):
        print(render_side(side, Path(sys.argv[1]), Path(sys.argv[2]),
                          Path(sys.argv[3])))
