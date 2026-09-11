"""Exact renderer arrays without OCCT array iteration or temporary Vectors."""

import numpy as np
from OCP.BRep import BRep_Tool
from OCP.TopAbs import TopAbs_Orientation
from OCP.TopLoc import TopLoc_Location


def tessellate_arrays(shape, tolerance: float, angular_tolerance: float = 0.1):
    """Retain Shape.tessellate's mesh, face order, native transforms and winding.

    Indexed triangle access avoids the OCP array iterator's binding overhead.
    Coordinates come from the same transformed native points, without wrapping
    and immediately unwrapping build123d Vectors. Nothing is cached or sampled.
    """
    if shape._wrapped is None:
        raise ValueError("Cannot tessellate an empty shape")
    shape.mesh(tolerance, angular_tolerance)
    vertices = []
    triangles = []
    offset = 0
    for face in shape.faces():
        assert face.wrapped is not None
        location = TopLoc_Location()
        poly = BRep_Tool.Triangulation_s(face.wrapped, location)
        transform = location.Transformation()
        reverse = face.wrapped.Orientation() == TopAbs_Orientation.TopAbs_REVERSED
        for index in range(1, poly.NbNodes() + 1):
            point = poly.Node(index).Transformed(transform)
            vertices.append((point.X(), point.Y(), point.Z()))
        for index in range(1, poly.NbTriangles() + 1):
            triangle = poly.Triangle(index)
            a, b, c = (triangle.Value(1) + offset - 1,
                       triangle.Value(2) + offset - 1,
                       triangle.Value(3) + offset - 1)
            triangles.append((a, c, b) if reverse else (a, b, c))
        offset += poly.NbNodes()
    return np.asarray(vertices, dtype=np.float64), np.asarray(triangles, dtype=np.int64)
