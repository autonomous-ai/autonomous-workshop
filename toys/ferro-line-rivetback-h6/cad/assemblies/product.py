from math import cos, radians, sin

from build123d import Color, Pos, Rot
from cadgen.assembly import AssemblyHelper
from params import *
from parts import chassis_core, carapace_fore, carapace_center, carapace_aft
from parts import hub_pedestal, cannon_body, muzzle_collar, sensor_insert
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
    cyan = Color(*cyan_rgb)

    asm.add(Pos(0, 0, chassis_assembly_z) * chassis_core.build(), "chassis_core", color=black)
    for name, module in (("fore", carapace_fore), ("center", carapace_center), ("aft", carapace_aft)):
        plate_y = plate_centers_y[name] + (4.0 if name == "fore" else 0.0)
        asm.add(Pos(0, plate_y, plate_assembly_z) * module.build(), f"carapace_{name}", color=yellow)
    asm.add(Pos(0, hub_center_y, hub_assembly_z) * hub_pedestal.build(), "hub_pedestal", color=black)
    # Seat the barrel directly on the crown so it reads as a forward weapon,
    # not as a detached vertical control in a top-biased camera view.
    cannon_origin = (0, hub_center_y + hub_depth / 2, 79.0)
    asm.add(Pos(*cannon_origin) * cannon_body.build(), "cannon_body", color=black)
    asm.add(Pos(cannon_origin[0], cannon_origin[1] + 49.0, cannon_origin[2]) * muzzle_collar.build(), "muzzle_collar", color=yellow)
    # Keep the triplet upright in a shallow front-open seat so its three
    # unequal masses remain legible from the signature frontal direction.
    asm.add(Pos(0, hub_center_y + hub_depth / 2 + 15.0, 65.0) * sensor_insert.build(), "sensor_insert", color=cyan)

    for leg_id, (root, angle) in leg_roots.items():
        root = _leg_mount(root, angle)
        upper_origin = (yoke_length, 0.0, 0.0)
        lower_origin = (yoke_length + upper_dx, 0.0, upper_dz)
        # The foot body starts at the reinforced beam endpoint; its rear-open
        # socket reaches back to the centred peg without body overlap.
        foot_origin = (yoke_length + upper_dx + lower_dx, 0.0, upper_dz + lower_dz - 5.25)
        asm.add(_place(root, angle, (0, 0, 0), hip_yoke.build()), "hip_yoke", leg_id, color=black)
        asm.add(_place(root, angle, upper_origin, upper_leg_beam.build()), "upper_leg_beam", leg_id, color=black)
        asm.add(_place(root, angle, upper_origin, upper_leg_armor.build()), "upper_leg_armor", leg_id, color=yellow)
        asm.add(_place(root, angle, lower_origin, lower_leg_beam.build()), "lower_leg_beam", leg_id, color=black)
        asm.add(_place(root, angle, lower_origin, lower_leg_armor.build()), "lower_leg_armor", leg_id, color=yellow)
        conduit_loc = (yoke_length + upper_dx - 6.0, -7.0, upper_dz - 5.0)
        asm.add(_place(root, angle, conduit_loc, Rot(90, 0, 0) * energy_conduit.build()), "energy_conduit", leg_id, color=cyan)
        asm.add(_place(root, angle, foot_origin, foot.build()), "foot", leg_id, color=black)

    return asm.build()
