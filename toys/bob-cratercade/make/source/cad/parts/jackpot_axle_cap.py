"""Screwed axle end-retainer; outer faceX0, inner stand-offs toward+X.

Two integral pads contact the bearing tower. The unperforated centre plate
blocks the wooden axle's end, while the specified standoff preserves endplay.
The countersinks are deliberately sized from qualified commercial maxima.
"""
from build123d import Align, Box, Cone, Cylinder, Pos, Rot
import params as p


def build():
    cap = Pos(p.CAP_T / 2, 0, 0) * Box(p.CAP_T, 2 * p.CAP_HALF_Y, 2 * p.CAP_HALF_Z)
    for sign in (-1, 1):
        y = sign * p.CAP_BOLT_Y
        pad = Pos(p.CAP_T, y, p.CAP_BOLT_Z) * Rot(0, 90, 0) * Cylinder(p.CAP_BOSS_D / 2, p.CAP_STANDOFF, align=(Align.CENTER, Align.CENTER, Align.MIN))
        cap += pad
        bore = Pos(0, y, p.CAP_BOLT_Z) * Rot(0, 90, 0) * Cylinder(p.M4_BORE / 2, p.CAP_T + p.CAP_STANDOFF, align=(Align.CENTER, Align.CENTER, Align.MIN))
        recess = Pos(0, y, p.CAP_BOLT_Z) * Rot(0, 90, 0) * Cone(p.CSK_RECESS_D / 2, p.M4_BORE / 2, p.CSK_HEAD_MAX_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        cap -= bore + recess
    return cap


def print_shape():
    """Flat outer cap face on bed; the two stand-offs rise from the plate."""
    cap = Rot(0, -90, 0) * build()
    bounds = cap.bounding_box()
    return Pos(-bounds.min.X, -bounds.min.Y, -bounds.min.Z) * cap
