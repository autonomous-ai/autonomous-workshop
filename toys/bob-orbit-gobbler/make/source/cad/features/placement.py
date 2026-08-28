"""Assembly coordinate transforms."""

from build123d import Pos, Rot


def upright(shape, *, x: float = 0.0, y: float = 0.0, z: float = 0.0, angle_deg: float = 0.0):
    """Local XY profile -> world XZ; local +Z thickness -> world -Y."""
    return Pos(x, y, z) * Rot(0, 0, angle_deg) * Rot(90, 0, 0) * shape


def upright_rearward(shape, *, x: float = 0.0, y: float = 0.0, z: float = 0.0, angle_deg: float = 0.0):
    """Mirrored local XY profile -> world XZ; local +Z -> world +Y."""
    return Pos(x, y, z) * Rot(0, 0, angle_deg) * Rot(-90, 0, 0) * shape
