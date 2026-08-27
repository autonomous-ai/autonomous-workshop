"""Printed 20T pinion with integral D-flat crank sleeve."""

from cadgen.assembly import label_shape
from features.common import box_from, cylinder_from
from features.gears import spur_gear
import params as p


def build_pinion():
    gear = spur_gear(p.GEAR_MODULE, p.PINION_TEETH, p.GEAR_FACE, p.PRESSURE_ANGLE_DEG, p.GEAR_BACKLASH)
    sleeve = cylinder_from(p.PINION_SLEEVE_D / 2.0, p.PINION_SLEEVE_L)
    flat_z0 = p.GEAR_FACE
    flat_cut = box_from(
        p.D_FLAT_X, -p.PINION_SLEEVE_D, flat_z0,
        p.PINION_SLEEVE_D, 2.0 * p.PINION_SLEEVE_D, p.PINION_SLEEVE_L - flat_z0,
    )
    groove = cylinder_from(p.PINION_SLEEVE_D / 2.0, p.CLIP_GROOVE_W, z=p.PINION_CLIP_Z0)
    groove = groove - cylinder_from(p.PINION_GROOVE_CORE_D / 2.0, p.CLIP_GROOVE_W, z=p.PINION_CLIP_Z0)
    return label_shape(gear + sleeve - flat_cut - groove, "pinion")
