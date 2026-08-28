"""One-piece two-deck carrier: front slider deck, hub bridge, rear 40T gear."""

import math
from build123d import Pos, Rot
from cadgen.assembly import label_shape
from features.common import box_from, cone_from, cylinder_from, prism
from features.gears import spur_gear
import params as p


def _radial_bar(r0, r1, width, z0, height):
    """Radial spoke with a semicircular distal end and a deep hub overlap."""
    tip_radius = width / 2.0
    tip_center = r1 - tip_radius
    points = [(r0, -tip_radius), (tip_center, -tip_radius)]
    points.extend(
        (
            tip_center + tip_radius * math.cos(math.radians(angle)),
            tip_radius * math.sin(math.radians(angle)),
        )
        for angle in range(-90, 91, 15)
    )
    points.append((r0, tip_radius))
    return Pos(0.0, 0.0, z0) * prism(points, height)


def build_carrier():
    gear = Pos(0.0, 0.0, p.GEAR_DECK_Z0) * spur_gear(
        p.GEAR_MODULE,
        p.CARRIER_TEETH,
        p.GEAR_FACE,
        p.PRESSURE_ANGLE_DEG,
        p.GEAR_BACKLASH,
        axial_fillet=0.0,
    )
    hub = cylinder_from(p.CARRIER_HUB_R, p.CARRIER_T)
    # Carry spokes through the complete hub.  This removes the narrow tangent
    # wedges produced by joining bars only at the hub circumference.
    spoke_root = 0.0
    active = _radial_bar(spoke_root, p.CARRIER_ACTIVE_R1, p.CARRIER_SPOKE_W, 0.0, p.SPOKE_DECK_T)
    deck = cylinder_from(p.CARRIER_ROOT_COLLAR_R, p.SPOKE_DECK_T) + active
    for angle in p.CARRIER_BALANCE_ANGLES:
        balance = _radial_bar(
            spoke_root, p.CARRIER_BALANCE_R1, p.CARRIER_BALANCE_W, 0.0, p.SPOKE_DECK_T
        )
        deck = deck + Rot(0.0, 0.0, angle) * balance
    channel_length = p.CHANNEL_R1 - p.CARRIER_ACTIVE_R0
    base_channel = box_from(
        p.CARRIER_ACTIVE_R0, -p.CHANNEL_BASE_W / 2.0, p.CHANNEL_FLOOR_T,
        channel_length, p.CHANNEL_BASE_W, p.CHANNEL_THROAT_Z0 - p.CHANNEL_FLOOR_T,
    )
    throat = box_from(
        p.CARRIER_ACTIVE_R0, -p.CHANNEL_THROAT_W / 2.0, p.CHANNEL_THROAT_Z0,
        channel_length, p.CHANNEL_THROAT_W, p.SPOKE_DECK_T - p.CHANNEL_THROAT_Z0,
    )
    follower_slot = box_from(
        p.FOLLOWER_PATH_R0 - p.FOLLOWER_OVERTRAVEL,
        -p.FOLLOWER_SLOT_W / 2.0,
        0.0,
        p.FOLLOWER_PATH_R1 - p.FOLLOWER_PATH_R0 + 2.0 * p.FOLLOWER_OVERTRAVEL,
        p.FOLLOWER_SLOT_W,
        p.CHANNEL_FLOOR_T,
    )
    bore = cylinder_from(p.CARRIER_BORE / 2.0, p.CARRIER_T)
    hub_blend = cone_from(
        p.CARRIER_ROOT_COLLAR_R,
        p.CARRIER_HUB_R,
        p.DECK_GAP + 2.0 * p.FUSE_OVERLAP,
        z=p.SPOKE_DECK_T - p.FUSE_OVERLAP,
    )
    result = gear + hub + deck + hub_blend - base_channel - throat - follower_slot - bore
    return label_shape(result, "two_deck_carrier")
