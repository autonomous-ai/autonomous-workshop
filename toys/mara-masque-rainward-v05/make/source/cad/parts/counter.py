"""The two preserved counter silhouettes, unchanged 12 x 8 x 4 mm."""
from functools import lru_cache

from build123d import *
from OCP.BRep import BRep_Builder
from OCP.gp import gp_Pnt

import params as P
from parts import finish

# [preserved] Exact cubic Bezier control points of the cloned counters.
SINGLE_CURVES = [[[6, -1], [6, 0.657], [4.657, 2], [3, 2]], [[3, 2], [0.3, 2], [-2.8, 4], [-5, 4]], [[-5, 4], [-5.552, 4], [-6, 3.5296], [-6, 2.95]], [[-6, 2.95], [-6, 2.3704], [-5.552, 1.9], [-5, 1.9]], [[-5, 1.9], [-2.8, 1.9], [-0.3, -4], [3, -4]], [[3, -4], [4.657, -4], [6, -2.657], [6, -1]]]
FORK_CURVES = [[[6, -1], [6, 0.657], [4.657, 2], [3, 2]], [[3, 2], [0.3, 2], [-2.8, 4], [-5, 4]], [[-5, 4], [-5.552, 4], [-6, 3.5296], [-6, 2.95]], [[-6, 2.95], [-6, 2.3704], [-5.552, 1.9], [-5, 1.9]], [[-5, 1.9], [-4.6, 1.9], [-4.6, 1.1], [-5, 1.1]], [[-5, 1.1], [-5.552, 1.1], [-6, 0.652], [-6, 0.1]], [[-6, 0.1], [-6, -0.452], [-5.552, -0.9], [-5, -0.9]], [[-5, -0.9], [-2.8, -0.9], [-0.3, -4], [3, -4]], [[3, -4], [4.657, -4], [6, -2.657], [6, -1]]]


def canonical_vertices(shape):
    """Preserved roundoff normalisation; curves and features are unchanged.

    OCP otherwise alternates the preserved 0.1 endpoint across its
    scientific-format threshold and changes STEP bytes between identical builds.
    """
    builder = BRep_Builder()
    for vertex in shape.vertices():
        xyz = (vertex.X, vertex.Y, vertex.Z)
        fixed = tuple(round(v, 10) for v in xyz)
        assert max(abs(a - b) for a, b in zip(xyz, fixed)) < 1e-9
        builder.UpdateVertex(vertex.wrapped, gp_Pnt(*fixed), 1e-7)
    return shape


@lru_cache(maxsize=None)
def counter(kind):
    curves = SINGLE_CURVES if kind == "single" else FORK_CURVES
    wire = Wire([Edge.make_bezier(*[(x, y, 0) for x, y in row]) for row in curves])
    if kind == "fork":
        canonical_vertices(wire)
    body = extrude(Face(wire), amount=P.DROP_H, dir=(0, 0, 1))
    if kind == "fork":
        canonical_vertices(body)
    colour = P.SINGLE_COLOR if kind == "single" else P.FORK_COLOR
    filament = P.SINGLE_FILAMENT if kind == "single" else P.FORK_FILAMENT
    return finish(body, "%s_%s" % (kind, filament), colour)


def counter_label(kind, index):
    filament = P.SINGLE_FILAMENT if kind == "single" else P.FORK_FILAMENT
    return "%s_%02d_%s" % (kind, index, filament)
