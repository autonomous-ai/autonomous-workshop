"""The counter. One silhouette, thirty identical solids, 10 x 7 x 4.5 mm.

The teardrop outline is the cloned counter's own set of cubic Beziers, scaled
from its 12 x 8 plan to the 10 x 7 the corrected brief carries. The two streams
are told apart by filament alone: all thirty pieces are the same solid.
"""
from functools import lru_cache

from build123d import *
from OCP.BRep import BRep_Builder
from OCP.gp import gp_Pnt

import params as P
from parts import finish

# [carried] Exact cubic Bezier control points of the cloned teardrop counter,
# drawn on its original 12 x 8 plan.
DROP_CURVES = [[[6, -1], [6, 0.657], [4.657, 2], [3, 2]], [[3, 2], [0.3, 2], [-2.8, 4], [-5, 4]], [[-5, 4], [-5.552, 4], [-6, 3.5296], [-6, 2.95]], [[-6, 2.95], [-6, 2.3704], [-5.552, 1.9], [-5, 1.9]], [[-5, 1.9], [-2.8, 1.9], [-0.3, -4], [3, -4]], [[3, -4], [4.657, -4], [6, -2.657], [6, -1]]]

SCALE_X = P.DROP_L / 12.0     # [inferred] 0.833333..., 12 mm plan to 10 mm
SCALE_Y = P.DROP_W / 8.0      # [inferred] 0.875, 8 mm plan to 7 mm


def canonical_vertices(shape):
    """Preserved roundoff normalisation; curves and features are unchanged.

    OCP otherwise alternates a control-point endpoint across its
    scientific-format threshold and changes STEP bytes between identical builds.
    """
    builder = BRep_Builder()
    for vertex in shape.vertices():
        xyz = (vertex.X, vertex.Y, vertex.Z)
        fixed = tuple(round(v, 10) for v in xyz)
        assert max(abs(a - b) for a, b in zip(xyz, fixed)) < 1e-9
        builder.UpdateVertex(vertex.wrapped, gp_Pnt(*fixed), 1e-7)
    return shape


def outline():
    """The counter plan at its built size, as scaled cubic Bezier rows."""
    return [[[round(x * SCALE_X, 10), round(y * SCALE_Y, 10)] for x, y in row]
            for row in DROP_CURVES]


@lru_cache(maxsize=None)
def counter(kind):
    """One counter. `kind` selects the filament tone, never the shape."""
    wire = Wire([Edge.make_bezier(*[(x, y, 0) for x, y in row])
                 for row in outline()])
    canonical_vertices(wire)
    body = extrude(Face(wire), amount=P.DROP_H, dir=(0, 0, 1))
    canonical_vertices(body)
    colour = P.SINGLE_COLOR if kind == "single" else P.FORK_COLOR
    filament = P.SINGLE_FILAMENT if kind == "single" else P.FORK_FILAMENT
    return finish(body, "drop_%s" % filament, colour)


def counter_label(kind, index):
    stream = "a" if kind == "single" else "b"
    filament = P.SINGLE_FILAMENT if kind == "single" else P.FORK_FILAMENT
    return "drop_%s%02d_%s" % (stream, index, filament)
