from math import cos, radians, sin

from build123d import Color, Pos, Rot
from cadgen.assembly import AssemblyHelper
from params import *
from parts import chassis_core, carapace_fore, carapace_center, carapace_aft
from parts import dorsal_fore, dorsal_center, dorsal_aft
from parts import joint_lock_pin
from parts import hip_yoke, upper_leg_beam, upper_leg_armor, lower_leg_beam, lower_leg_armor
from parts import energy_conduit, foot


def _place(root, angle, local_location, shape):
    return Pos(*root) * Rot(0, 0, angle) * Pos(*local_location) * shape


def _leg_mount(root, angle):
    radial_shift = 3.0 if angle in (0.0, 180.0) else 6.5
    return (
        root[0] + radial_shift * cos(radians(angle)),
        root[1] + radial_shift * sin(radians(angle)),
        root[2],
    )


def build():
    asm = AssemblyHelper("rivetback_h6")
    yellow = Color(*yellow_rgb)
    black = Color(*black_rgb)
    cable = Color(*cable_rgb)
    steel = Color(*steel_rgb)

    asm.add(Pos(0, 0, chassis_assembly_z) * chassis_core.build(), "chassis_core", color=black)
    for name, module in (("fore", carapace_fore), ("center", carapace_center), ("aft", carapace_aft)):
        plate_y = plate_centers_y[name]
        asm.add(Pos(0, plate_y, plate_assembly_z) * module.build(), f"carapace_{name}", color=yellow)
    for name, module in (("fore", dorsal_fore), ("center", dorsal_center), ("aft", dorsal_aft)):
        plate_y = plate_centers_y[name]
        asm.add(
            Pos(0, plate_y, plate_assembly_z + plate_height + 1.2) * module.build(),
            f"dorsal_{name}",
            color=yellow,
        )
    for leg_id, (root, angle) in leg_roots.items():
        root = _leg_mount(root, angle)
        upper_origin = (yoke_length, 0.0, 0.0)
        lower_origin = (yoke_length + upper_dx, 0.0, upper_dz)
        # The foot body starts at the reinforced beam endpoint; its rear-open
        # socket reaches back to the centred peg without body overlap.
        foot_origin = (yoke_length + upper_dx + lower_dx, 0.0, upper_dz + lower_dz - foot_socket_z)
        asm.add(_place(root, angle, (0, 0, 0), hip_yoke.build()), "hip_yoke", leg_id, color=black)
        asm.add(_place(root, angle, upper_origin, upper_leg_beam.build()), "upper_leg_beam", leg_id, color=black)
        asm.add(_place(root, angle, upper_origin, upper_leg_armor.build()), "upper_leg_armor", leg_id, color=yellow)
        asm.add(_place(root, angle, lower_origin, lower_leg_beam.build()), "lower_leg_beam", leg_id, color=black)
        asm.add(_place(root, angle, lower_origin, lower_leg_armor.build()), "lower_leg_armor", leg_id, color=yellow)
        conduit_loc = (yoke_length + upper_dx - 14.0, -10.5, upper_dz - 3.0)
        asm.add(_place(root, angle, conduit_loc, Rot(90, 0, 0) * energy_conduit.build()), "energy_conduit", leg_id, color=cable)
        asm.add(_place(root, angle, foot_origin, foot.build()), "foot", leg_id, color=black)
        # Removable hex-headed through-pins reinforce the keyed hip and knee
        # interfaces and provide the exposed fastener language of the reference.
        hip_pin_loc = (yoke_length - tenon_length / 2, 0.0, 0.0)
        knee_pin_loc = (yoke_length + upper_dx - tenon_length / 2, 0.0, upper_dz + 1.0)
        asm.add(_place(root, angle, hip_pin_loc, Rot(-90, 0, 0) * joint_lock_pin.build()), "hex_joint_pin_hip", leg_id, color=steel)
        asm.add(_place(root, angle, knee_pin_loc, Rot(-90, 0, 0) * joint_lock_pin.build()), "hex_joint_pin_knee", leg_id, color=steel)

    return asm.build()
