"""mask_disc_a / mask_disc_b / mask_disc_c — one shared profile, three
window subsets and three grip-tab silhouettes.

All three discs share ONE window-track/rim-band profile, ONE bore diameter
and ONE 80mm-radius window ring (`features.ring`, the same list plinth_ring
cuts its wells from). Only the six-index window subset and the grip-tab
shape differ per disc, per idea.json's part_vocabulary ("told apart by
grip-tab alone").
"""
from __future__ import annotations

import math

import cadquery as cq

from params import Params
from features.ring import RING_XY, RING_ANGLES


def _disc_blank(p: Params, track_h: float | None = None) -> cq.Workplane:
    """`track_h` overrides the window-track band's own thickness (default
    `p.disc_track_h`, the shared b/c profile). mask_disc_a passes
    `p.disc_rim_h` instead: its track annulus needs a taller starting slab
    so the underside relief undercut (cut below, in `make_mask_disc`) has
    material to remove and still leaves a real remaining wall, rather than
    cutting clean through a slab that was never thicker than the cut is
    deep. The rim band itself (radially outside the track) is unaffected
    either way -- it is already `disc_rim_h` thick."""
    r = p.disc_dia / 2.0
    track_r = r - p.disc_rim_band_w
    bore_r = p.disc_bore_dia / 2.0
    th = p.disc_track_h if track_h is None else track_h

    track = (
        cq.Workplane("XY")
        .circle(track_r)
        .circle(bore_r)
        .extrude(th)
    )
    rim = (
        cq.Workplane("XY")
        .circle(r)
        .circle(track_r)
        .extrude(p.disc_rim_h)
    )
    return track.union(rim)


def _cut_windows(disc: cq.Workplane, p: Params, indices: tuple[int, ...]) -> cq.Workplane:
    cutter_h = p.disc_rim_h + 4.0
    pts = [RING_XY[i] for i in indices]
    cutter = cq.Workplane("XY").pushPoints(pts).circle(p.window_dia / 2.0).extrude(cutter_h)
    cutter = cutter.translate((0, 0, -2.0))
    return disc.cut(cutter)


def _paddle_tab(p: Params) -> cq.Workplane:
    """Broad rounded paddle grip-tab (mask_disc_a)."""
    r0 = p.disc_dia / 2.0
    r1 = r0 + p.grip_tab_len
    w = 14.0
    profile = (
        cq.Workplane("XY")
        .moveTo(r0 - 2.0, -w)
        .lineTo(r1 - w * 0.6, -w)
        .threePointArc((r1, 0), (r1 - w * 0.6, w))
        .lineTo(r0 - 2.0, w)
        .close()
    )
    return profile.extrude(p.disc_rim_h)


def _fin_tab(p: Params) -> cq.Workplane:
    """Pointed triangular fin grip-tab (mask_disc_b)."""
    r0 = p.disc_dia / 2.0
    r1 = r0 + p.grip_tab_len
    w = 13.0
    profile = (
        cq.Workplane("XY")
        .moveTo(r0 - 2.0, -w)
        .lineTo(r1, 0)
        .lineTo(r0 - 2.0, w)
        .close()
    )
    return profile.extrude(p.disc_rim_h)


def _prong_tab(p: Params) -> cq.Workplane:
    """Notched double-prong grip-tab (mask_disc_c)."""
    r0 = p.disc_dia / 2.0
    r1 = r0 + p.grip_tab_len
    prong_w = 4.0
    gap = 4.0
    one = (
        cq.Workplane("XY")
        .moveTo(r0 - 2.0, gap / 2.0)
        .lineTo(r1, gap / 2.0)
        .lineTo(r1, gap / 2.0 + prong_w)
        .lineTo(r0 - 2.0, gap / 2.0 + prong_w)
        .close()
        .extrude(p.disc_rim_h)
    )
    two = one.mirror(mirrorPlane="XZ")
    return one.union(two)


_TAB_BUILDERS = {"paddle": _paddle_tab, "fin": _fin_tab, "prong": _prong_tab}


def _witness_notch(p: Params, angle_deg: float = 20.0) -> cq.Workplane:
    """Own witness notch, offset in angle from the grip-tab (both sit at
    angle 0) so the notch cuts clean rim material, not the tab's base."""
    r = p.disc_dia / 2.0
    notch = (
        cq.Workplane("XY")
        .moveTo(r - p.witness_notch_depth, -p.witness_notch_w / 2.0)
        .lineTo(r + 2.0, 0)
        .lineTo(r - p.witness_notch_depth, p.witness_notch_w / 2.0)
        .close()
        .extrude(p.disc_rim_h)
    )
    return notch.rotate((0, 0, 0), (0, 0, 1), angle_deg)


def make_mask_disc(p: Params, windows: tuple[int, ...], tab: str,
                    undercut: bool = False) -> cq.Workplane:
    # mask_disc_a's track annulus is built to the taller disc_rim_h slab
    # (see `_disc_blank`'s docstring) so the undercut below has a real
    # remaining wall; mask_disc_b/c keep the shared disc_track_h profile.
    disc = _disc_blank(p, track_h=p.disc_rim_h if undercut else None)
    disc = _cut_windows(disc, p, windows)

    tab_shape = _TAB_BUILDERS[tab](p)
    disc = disc.union(tab_shape)

    notch = _witness_notch(p)
    disc = disc.cut(notch)

    if undercut:
        # A resting tile's knob rises the FULL 9mm above the ledge past
        # what the window-track band can locally clear when a well is
        # unaligned; relieve the track annulus (outside the through-windows,
        # which already clear it) by that same depth, but cut it as an
        # UPWARD-facing pocket from the TOP face instead of the underside.
        # Cutting from underneath leaves the entire track annulus attached
        # only at the outer rim -- a dead-flat 0deg overhang with no bed
        # contact under it and nothing to print it on. Cutting the
        # identical-depth pocket from the top instead leaves the underside
        # solid and flush (full bed contact, self-supporting print) while
        # removing the same material from the opposite face of the same
        # slab; the pocket itself opens upward, which never needs support
        # on an FDM printer.
        #
        # The slab this pocket is cut from is the disc_rim_h-thick track
        # blank above (not the shorter disc_track_h), per the brief's
        # amendment: disc_rim_h - disc_a_undercut_h = 11 - 9 = 2mm remains,
        # clearing the 1.6mm min_wall_mm floor instead of severing the
        # ring that connects the disc's bore/hub to its outer rim.
        r = p.disc_dia / 2.0
        track_r = r - p.disc_rim_band_w
        bore_r = p.disc_bore_dia / 2.0
        pocket = (
            cq.Workplane("XY")
            .circle(track_r)
            .circle(bore_r)
            .extrude(p.disc_a_undercut_h)
            .translate((0, 0, p.disc_rim_h - p.disc_a_undercut_h))
        )
        disc = disc.cut(pocket)

    return disc


def make_mask_disc_a(p: Params) -> cq.Workplane:
    return make_mask_disc(p, p.disc_a_windows, "paddle", undercut=True)


def make_mask_disc_b(p: Params) -> cq.Workplane:
    return make_mask_disc(p, p.disc_b_windows, "fin")


def make_mask_disc_c(p: Params) -> cq.Workplane:
    return make_mask_disc(p, p.disc_c_windows, "prong")
