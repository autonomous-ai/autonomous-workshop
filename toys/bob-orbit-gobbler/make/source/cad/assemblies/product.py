"""Named placement only for the Orbit Gobbler inspection assembly."""

from build123d import Plane, Pos, Rot, mirror
from cadgen.assembly import AssemblyHelper
import params as p
from parts.base import build_base
from parts.frame import build_frame
from parts.brace import build_brace
from parts.frame_key import build_frame_key
from parts.central_axle import build_central_axle
from parts.carrier import build_carrier
from parts.lunar_slider import build_lunar_slider
from parts.follower_axle import build_follower_axle
from parts.follower_roller import build_follower_roller
from parts.moon import build_moon
from parts.small_washer import build_small_washer
from parts.small_clip import build_small_clip
from parts.eye_guard import build_eye_guard
from parts.pinion import build_pinion
from parts.crank_arm import build_crank_arm
from parts.pinion_washer import build_pinion_washer
from parts.pinion_key import build_pinion_key
from parts.grip import build_grip
from parts.mouth_bezel import build_mouth_bezel


def _frontward(shape, rear_y, x=0.0, z=p.ORBIT_Z, local_angle=0.0):
    return Pos(x, rear_y, z) * Rot(90.0, 0.0, 0.0) * Rot(0.0, 0.0, local_angle) * shape


def _rearward(shape, front_y, x=0.0, z=p.ORBIT_Z, local_angle=0.0):
    return Pos(x, front_y, z) * Rot(-90.0, 0.0, 0.0) * Rot(0.0, 0.0, local_angle) * shape


def _centered_key(shape, rear_y, x, z, local_angle=0.0):
    centered = Pos(-p.KEY_L / 2.0, -p.KEY_D / 2.0, 0.0) * shape
    return _frontward(centered, rear_y, x=x, z=z, local_angle=local_angle)


def _centered_key_rearward(shape, front_y, x, z, local_angle=0.0):
    centered = Pos(-p.KEY_L / 2.0, -p.KEY_D / 2.0, 0.0) * shape
    return _rearward(centered, front_y, x=x, z=z, local_angle=local_angle)


def build_product():
    asm = AssemblyHelper("orbit_gobbler")
    # Omit per-occurrence STEP presentation colors: Open CASCADE can reorder
    # equivalent style records across fresh processes, changing exact bytes
    # even when every geometric entity is identical. Labels and placements
    # remain deterministic and carry all inspection semantics.
    asm.add(build_base(), "base")
    asm.add(_frontward(build_frame(), p.FRAME_REAR_Y), "frame_cam")
    for side, x in (("left", -p.BRACE_X - p.BRACE_T / 2.0), ("right", p.BRACE_X - p.BRACE_T / 2.0)):
        placed = Pos(x, p.BRACE_BASE_Y, p.BRACE_BASE_Z) * Rot(0.0, 90.0, 90.0) * build_brace()
        asm.add(placed, "rear_brace", side)
    frame_key_y = p.FRAME_REAR_Y - p.FRAME_T / 2.0 + p.FRAME_KEY_L / 2.0
    frame_key_z = p.ORBIT_Z + p.FRAME_KEY_LOCAL_Y - p.KEY_T / 2.0
    for side, x in (("left", -p.FRAME_TENON_X), ("right", p.FRAME_TENON_X)):
        key = Pos(x - p.KEY_W / 2.0, frame_key_y - p.FRAME_KEY_L, frame_key_z) * build_frame_key()
        asm.add(key, "frame_key", side)

    asm.add(_frontward(build_central_axle(), p.CENTRAL_AXLE_REAR_Y), "central_axle")
    carrier_angle = p.REST_ANGLE_DEG - 90.0
    carrier = _rearward(build_carrier(), p.CARRIER_FRONT_Y, local_angle=carrier_angle)
    asm.add(carrier, "carrier")
    slider_center_r = p.SLIDER_CENTER_R
    slider = Pos(0.0, p.CARRIER_FRONT_Y, p.ORBIT_Z) * Rot(-90.0, 0.0, 0.0) * Rot(
        0.0, 0.0, carrier_angle
    ) * Pos(slider_center_r, 0.0, p.CHANNEL_FLOOR_T) * build_lunar_slider()
    asm.add(slider, "lunar_slider")

    moon_x, moon_z = p.polar_xy(p.OUTER_MOUTH_R, p.REST_ANGLE_DEG)
    moon_rear_y = p.MOON_FRONT_Y + p.MOON_T
    moon_angle = 90.0 - p.REST_ANGLE_DEG
    asm.add(
        _frontward(build_moon(), moon_rear_y, x=moon_x, z=p.ORBIT_Z + moon_z, local_angle=moon_angle),
        "moon",
    )
    asm.add(
        _rearward(
            build_follower_axle(), p.FOLLOWER_FRONT_Y,
            x=moon_x, z=p.ORBIT_Z + moon_z, local_angle=carrier_angle,
        ),
        "follower_axle",
    )
    asm.add(
        _rearward(build_follower_roller(), p.FOLLOWER_ROLLER_Y, x=moon_x, z=p.ORBIT_Z + moon_z),
        "follower_roller",
    )

    asm.add(_frontward(build_eye_guard(), p.EYE_FRONT_Y + p.EYE_T), "eye_guard")
    asm.add(_frontward(build_small_washer(), p.CARRIER_WASHER_REAR_Y), "carrier_washer")
    carrier_clip_rear = p.CENTRAL_AXLE_REAR_Y - p.CENTRAL_CLIP_Z0 - p.RUN_CLEAR
    asm.add(_frontward(build_small_clip(), carrier_clip_rear), "carrier_key")

    pinion = _rearward(
        Rot(0.0, 0.0, p.PINION_PHASE_DEG) * build_pinion(),
        p.PINION_FRONT_Y,
        x=p.PINION_X,
    )
    asm.add(pinion, "pinion")
    crank = _frontward(
        build_crank_arm(), p.CRANK_REAR_Y,
        x=p.PINION_X, local_angle=-p.PINION_PHASE_DEG,
    )
    asm.add(crank, "crank_arm")
    pinion_washer_front = p.CRANK_REAR_Y + p.RUN_CLEAR
    asm.add(_rearward(build_pinion_washer(), pinion_washer_front, x=p.PINION_X), "pinion_washer")
    pinion_key_front = p.PINION_FRONT_Y + p.PINION_CLIP_Z0 + p.RUN_CLEAR
    asm.add(
        _rearward(
            build_pinion_key(), pinion_key_front, p.PINION_X, p.ORBIT_Z,
            local_angle=p.PINION_PHASE_DEG,
        ),
        "pinion_key",
    )

    grip_x = p.CRANK_GRIP_WORLD_X
    grip_z = p.CRANK_GRIP_WORLD_Z
    grip_rear = p.CRANK_REAR_Y - p.CRANK_ARM_T - p.RUN_CLEAR
    asm.add(_frontward(build_grip(), grip_rear, x=grip_x, z=grip_z), "grip")
    asm.add(_frontward(build_small_washer(), grip_rear - p.GRIP_L - p.RUN_CLEAR, x=grip_x, z=grip_z), "grip_washer")
    grip_key_rear = p.CRANK_REAR_Y - p.GRIP_CLIP_Z0 - p.RUN_CLEAR
    asm.add(
        _frontward(
            build_small_clip(), grip_key_rear, grip_x, grip_z,
            local_angle=p.CRANK_ASSEMBLY_ANGLE_DEG,
        ),
        "grip_key",
    )

    bezel = mirror(build_mouth_bezel(), about=Plane.XZ)
    asm.add(_rearward(bezel, p.LIP_FRONT_Y), "mouth_bezel")
    return asm.compound()
