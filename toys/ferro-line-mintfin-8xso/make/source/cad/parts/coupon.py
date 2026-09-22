"""Real-size J08 tolerance-test coupon; physical fit remains untested.

J08 female derives from the actual rear barrel half, with the same slit roots
and print direction. Male is ONE sagittal half: print quantity TWO and bond
on the flat split faces. These coupons are test pieces, not motion actors.
No physical fit, insertion force, retention or durability result is claimed.
"""
from math import ceil
from build123d import (
    Align, Box, Color, Cylinder, Plane, Pos, Rot, Sphere,
)
from params import DESIGN
from params.body import BODY08_SEAM
from parts.body import body_half
from features.joints import y_cylinder, socket_cavity

MIN_SOCKET_FLOOR = 1.4
LAYER_HEIGHT = 0.2
MAGNET_D = 8.15
MAGNET_DEPTH = 1.2
MAGNET_EDGE_MARGIN = 2.0
J = DESIGN['joints'][8]


def coupon_socket():
    """Live body08 rear print on a base; exact cavity also clears the base."""
    rear_world = body_half(7, 'rear', print_pose=False)
    rear_print = body_half(7, 'rear', print_pose=True)
    # Shared architecture owns the seam. Fail on stale mixed source revisions.
    seam_y = BODY08_SEAM
    assert abs(rear_world.bounding_box().min.Y - seam_y) < 1e-5
    center_height = J['ball_center'][1] - seam_y
    cavity_intrusion = max(0.0, J['cavity_diameter']/2 - center_height)
    base_t = ceil((MIN_SOCKET_FLOOR + cavity_intrusion) / LAYER_HEIGHT
                  - 1e-9) * LAYER_HEIGHT
    center_z = DESIGN['segments'][7]['center'][2]
    world_to_print = Rot(90, 0, 0) * Pos(0, -seam_y, -center_z)
    transformed = world_to_print * rear_world
    normalize_z = -transformed.bounding_box().min.Z
    to_coupon = Pos(0, 0, base_t + normalize_z) * world_to_print

    bb = rear_print.bounding_box()
    # A separate right-hand pocket stays clear of all live rear-half geometry.
    magnet_x = bb.max.X + MAGNET_EDGE_MARGIN + MAGNET_D / 2
    x0 = bb.min.X - MAGNET_EDGE_MARGIN
    x1 = magnet_x + MAGNET_D / 2 + MAGNET_EDGE_MARGIN
    y0 = min(bb.min.Y - MAGNET_EDGE_MARGIN, -MAGNET_D / 2 - MAGNET_EDGE_MARGIN)
    y1 = max(bb.max.Y + MAGNET_EDGE_MARGIN, MAGNET_D / 2 + MAGNET_EDGE_MARGIN)
    base = Pos(x0, y0, 0) * Box(x1-x0, y1-y0, base_t,
        align=(Align.MIN, Align.MIN, Align.MIN))
    # Cut only the BASE: subtracting this cutter after union would erase the
    # rear half's intentional preload lands. The live half already has cavity.
    base = base.cut(to_coupon * socket_cavity(J))
    magnet = Pos(magnet_x, 0, base_t-MAGNET_DEPTH) * Cylinder(
        MAGNET_D/2, MAGNET_DEPTH+.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    base = base.cut(magnet)
    result = base.fuse(Pos(0, 0, base_t) * rear_print)
    assert result.is_valid and len(result.solids()) == 1
    assert abs(result.bounding_box().min.Z) < 1e-5
    result.color = Color(169/255, 205/255, 190/255)
    result.label = 'J08_actual_rear_socket_and_magnet_coupon'
    return result


def coupon_ball_full_local():
    """Assembly reference only. Joint center(0,0,0), neck points along+Y."""
    r = J['ball_diameter']/2
    # Sphere construction matches the shared family seam orientation exactly.
    sphere = Rot(0, 0, 90) * Sphere(r)
    neck = y_cylinder(J['neck_diameter']/2, 0, 14, 0)
    # The remote grip starts12mm behind center, clear of the contact region.
    grip = Pos(0, 16, 0) * Box(12, 8, 8)
    return sphere.fuse(neck, grip)


def coupon_ball():
    """One identical half, quantity TWO; largest sagittal plane on bed."""
    whole = coupon_ball_full_local()
    positive_x = Pos(0, -50, -50) * Box(100, 100, 100,
        align=(Align.MIN, Align.MIN, Align.MIN))
    half = whole & positive_x
    # Print(u,v,w)=(worldY,worldZ,worldX). No cone or suspended lower sphere.
    plane = Plane(origin=(0,0,0), x_dir=(0,1,0), z_dir=(1,0,0))
    result = plane.location.inverse() * half
    assert result.is_valid and len(result.solids()) == 1
    assert abs(result.bounding_box().min.Z) < 1e-5
    result.color = Color(238/255, 140/255, 125/255)
    result.label = 'J08_exact_ball_sagittal_half_print_two'
    return result
