from math import cos, radians, sin

from build123d import Align, Box, Cylinder, Pos, Rot
from features.forms import clipped_prism, color_part
from params import *


def build():
    body = clipped_prism(chassis_width, chassis_depth, chassis_height, chassis_corner_cut)
    lugs = []
    collars = []
    sockets = []
    for (x, y, z), angle in leg_roots.values():
        radial_shift = 3.0 if angle in (0.0, 180.0) else 6.5
        mount_x = x + radial_shift * cos(radians(angle))
        mount_y = y + radial_shift * sin(radians(angle))
        local_z = z - chassis_assembly_z
        lugs.append(
            Pos(mount_x, mount_y, chassis_height / 2)
            * Rot(0, 0, angle)
            * Pos(-5.0, 0, 0)
            * Box(10.0, 16.0, chassis_height, align=(Align.CENTER, Align.CENTER, Align.CENTER))
        )
        collars.append(
            Pos(mount_x, mount_y, local_z)
            * Rot(0, 0, angle)
            * Pos(-2.0, 0, 0)
            * Rot(0, 90, 0)
            * Cylinder(6.5, 4.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))
        )
        sockets.append(
            Pos(mount_x, mount_y, local_z)
            * Rot(0, 0, angle)
            * Pos(-hip_peg_length / 2, 0, 0)
            * Box(hip_peg_length + 0.5, hip_socket * 0.78, hip_socket, align=(Align.CENTER, Align.CENTER, Align.CENTER))
        )
    body = (body + lugs + collars) - sockets
    armor_sockets = [
        Pos(x, plate_centers_y[name] - plate_depths[name] / 2 + small_peg * 0.36, chassis_height - 2.0) * Box(small_socket, small_socket, 7.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))
        for name in ("fore", "center", "aft") for x in (-plate_peg_x, plate_peg_x)
    ]
    hub_socket_cut = Pos(0, hub_center_y - hub_depth / 2 + 4.0, chassis_height - 3.0) * Box(10.5, 8.5, 8.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    hub_spine_clearance = Pos(0, hub_center_y, chassis_height + 2.0) * Box(
        hub_width + 2.0,
        hub_depth + 14.0,
        4.0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    body = body - armor_sockets - hub_socket_cut - hub_spine_clearance
    return color_part(body, "chassis_core", black_rgb)
