"""Single-start 60 deg (ISO-form) threads as swept solids.

build123d 0.11.1 ships no IsoThread, so the thread is a triangular profile
swept along a Helix and fused to a core cylinder. One solid out, flat ends.

Both halves of a threaded pair are derived from ONE nominal major diameter and
ONE flank clearance here, so the screw and the nut cannot drift apart.
"""

from __future__ import annotations

import math

from build123d import (
    Align,
    Cylinder,
    Helix,
    Location,
    Plane,
    Polygon,
    Vector,
    sweep,
)

TAN30 = math.tan(math.radians(30.0))


def _profile_half_width(r: float, r_crest: float, w_crest: float) -> float:
    """Axial half-width of the ISO flank at radius ``r``."""
    return w_crest + (r_crest - r) * TAN30


def _swept(
    pitch: float,
    height: float,
    z0: float,
    pts: list[tuple[float, float]],
    r_ref: float,
    core_r: float,
):
    over = pitch  # run the helix past both ends, then trim flat
    helix = Helix(
        pitch=pitch, height=height + 2 * over, radius=r_ref, center=(0, 0, z0 - over)
    )
    p0 = helix @ 0.0
    t0 = helix % 0.0
    radial = Vector(p0.X, p0.Y, 0).normalized()
    plane = Plane(origin=p0, x_dir=radial, z_dir=t0)
    ridge = sweep(plane * Polygon(*pts, align=None), path=helix, is_frenet=True)
    core = Cylinder(
        core_r, height + 2 * over, align=(Align.CENTER, Align.CENTER, Align.MIN)
    ).moved(Location((0, 0, z0 - over)))
    return core.fuse(ridge).clean()


def external_thread(major_d: float, pitch: float, height: float, z0: float = 0.0):
    """Screw thread, base at ``z0``. Crest diameter is exactly ``major_d``."""
    r_crest = major_d / 2
    h_tri = pitch * math.sqrt(3) / 2
    r_root = r_crest - 5 * h_tri / 8          # basic minor radius
    w_crest = pitch / 16                       # crest flat = p/8
    w_root = _profile_half_width(r_root, r_crest, w_crest)
    r_in = r_root - 0.4                        # overlap the core so the fuse is one solid
    pts = [
        (r_in - r_crest, -w_root),
        (0.0, -w_crest),
        (0.0, w_crest),
        (r_in - r_crest, w_root),
    ]
    solid = _swept(pitch, height, z0, pts, r_ref=r_crest, core_r=r_root)
    trim = Cylinder(
        r_crest + 1, height, align=(Align.CENTER, Align.CENTER, Align.MIN)
    ).moved(Location((0, 0, z0)))
    return (solid & trim).clean(), 2 * r_root


def nut_cut(
    screw_major_d: float,
    pitch: float,
    height: float,
    z0: float,
    flank_clearance_d: float,
    nut_major_d: float,
):
    """Negative space of the nut: cut this out of a boss to get the internal thread.

    ``flank_clearance_d`` is the TOTAL diametral clearance between the screw's
    flanks and the nut's flanks (the running fit). ``nut_major_d`` is the nut's
    bore (its thread root) — always the larger number, and it never touches the
    screw.
    """
    e = flank_clearance_d / 2                   # radial offset of the flanks
    r_screw_crest = screw_major_d / 2
    r_flank_crest = r_screw_crest + e           # the screw's crest, grown
    w_crest = pitch / 16
    r_outer = nut_major_d / 2                   # nut bore = cut's crest
    h_tri = pitch * math.sqrt(3) / 2
    r_nut_crest = r_screw_crest - 5 * h_tri / 8 + e   # nut's own crest (tap-drill radius)
    w_outer = _profile_half_width(r_outer, r_flank_crest, w_crest)
    if w_outer < 0.03:
        w_outer = 0.03
    r_in = r_nut_crest - 0.4
    w_in = _profile_half_width(r_in, r_flank_crest, w_crest)
    r_ref = (r_outer + r_nut_crest) / 2
    pts = [
        (r_in - r_ref, -w_in),
        (r_outer - r_ref, -w_outer),
        (r_outer - r_ref, w_outer),
        (r_in - r_ref, w_in),
    ]
    solid = _swept(pitch, height, z0, pts, r_ref=r_ref, core_r=r_nut_crest)
    trim = Cylinder(
        r_outer + 1, height, align=(Align.CENTER, Align.CENTER, Align.MIN)
    ).moved(Location((0, 0, z0)))
    return (solid & trim).clean(), 2 * r_nut_crest
