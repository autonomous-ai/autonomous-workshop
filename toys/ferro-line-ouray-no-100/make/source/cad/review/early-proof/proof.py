"""Exact shared-parameter early proof for Ferro Line No. 100 Ouray.

The three exported states change actual wheel spoke orientation and tender yaw.
They are deliberately neutral blockouts: enough period form to judge the 2-8-0
identity before the final part tree or surface detail is authored.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from build123d import Axis, Box, Compound, Cone, Cylinder, Location, Sphere, export_step, export_stl


ROOT = Path(__file__).resolve().parent
DRIVER_DIAMETER = 10.51
PILOT_DIAMETER = 7.0
TENDER_DIAMETER = 7.59
TREAD_WIDTH = 2.0
GAUGE_CENTERS = (-5.25, 5.25)
DRIVER_X = (41.0, 52.0, 63.0, 74.0)
TENDER_AXLE_X = (124.0, 136.0, 151.0, 163.0)
STATE_PARAMETERS = {
    0: {"wheel_deg": 0.0, "tender_yaw_deg": 0.0, "tender_dx": 0.0},
    1: {"wheel_deg": 15.0, "tender_yaw_deg": 6.0, "tender_dx": 12.0},
    2: {"wheel_deg": 30.0, "tender_yaw_deg": 0.0, "tender_dx": 24.0},
}


def at(shape, xyz):
    return shape.moved(Location(xyz))


def axle_y_cylinder(radius: float, length: float):
    return Cylinder(radius, length).rotate(Axis.X, 90).moved(Location((0, length / 2.0, 0)))


def wheel(diameter: float, x: float, y: float, z: float, angle: float):
    radius = diameter / 2.0
    tyre = Cylinder(radius, TREAD_WIDTH) - Cylinder(radius - 1.2, TREAD_WIDTH + 0.2).moved(Location((0, 0, -0.1)))
    tyre = tyre.rotate(Axis.X, 90).moved(Location((x, y + TREAD_WIDTH / 2.0, z)))
    hub = Cylinder(1.8, TREAD_WIDTH + 0.6).rotate(Axis.X, 90).moved(Location((x, y + (TREAD_WIDTH + 0.6) / 2.0, z)))
    spokes = []
    for spoke_angle in (0.0, 45.0, 90.0, 135.0):
        spoke = Box(diameter - 1.6, TREAD_WIDTH + 0.3, 0.8)
        spoke = spoke.moved(Location((-diameter / 2.0 + 0.8, y - (TREAD_WIDTH + 0.3) / 2.0, -0.4)))
        spoke = spoke.rotate(Axis.Y, spoke_angle + angle)
        spoke = spoke.moved(Location((x, 0, z)))
        spokes.append(spoke)
    return Compound(children=[tyre, hub, *spokes])


def wheelset(diameter: float, axle_length: float, x: float, z: float, angle: float):
    axle = axle_y_cylinder(1.5, axle_length).moved(Location((x, -axle_length / 2.0, z)))
    return Compound(children=[axle, *(wheel(diameter, x, y, z, angle) for y in GAUGE_CENTERS)])


def locomotive(angle: float):
    pieces = []
    pieces.append(at(Box(77.0, 18.0, 4.0), (18.0, -9.0, 6.0)))
    pieces.append(at(Box(68.0, 2.0, 3.0), (25.0, -12.0, 9.0)))
    pieces.append(at(Box(68.0, 2.0, 3.0), (25.0, 10.0, 9.0)))
    boiler = Cylinder(11.5, 58.0).rotate(Axis.Y, 90).moved(Location((83.0, 0, 24.0)))
    pieces.append(boiler)
    pieces.append(at(Box(24.0, 27.0, 29.0), (70.0, -13.5, 10.0)))
    pieces.append(at(Box(29.0, 30.0, 2.0), (68.0, -15.0, 40.0)))
    pieces.append(at(Cylinder(5.0, 8.5), (50.0, 0, 34.0)))
    pieces.append(at(Sphere(5.0), (50.0, 0, 42.0)))
    pieces.append(at(Cylinder(5.5, 7.8), (64.0, 0, 34.0)))
    pieces.append(at(Sphere(5.5), (64.0, 0, 41.0)))
    pieces.append(at(Cylinder(4.0, 4.0), (34.0, 0, 34.0)))
    pieces.append(at(Cone(4.0, 8.0, 8.0), (34.0, 0, 38.0)))
    pieces.append(at(Cylinder(9.0, 1.8), (34.0, 0, 46.0)))
    pieces.append(at(Box(10.0, 12.0, 10.0), (20.0, -6.0, 30.0)))
    pieces.append(at(Box(18.0, 28.0, 3.0), (1.0, -14.0, 7.0)))
    for offset in (0.0, 4.0, 8.0, 12.0, 16.0):
        pieces.append(at(Box(16.0, 1.2, 1.2).rotate(Axis.Y, -28), (2.0 + offset * 0.55, -12.0 + offset * 1.5, 2.0)))
    for x in DRIVER_X:
        pieces.append(wheelset(DRIVER_DIAMETER, 26.0, x, DRIVER_DIAMETER / 2.0, angle))
    pieces.append(wheelset(PILOT_DIAMETER, 22.0, 23.0, PILOT_DIAMETER / 2.0, angle))
    # Fixed side rods remain safely outside the rotating wheel faces.
    pieces.append(at(Box(44.0, 1.0, 1.4), (36.0, -12.7, 5.0)))
    pieces.append(at(Box(44.0, 1.0, 1.4), (36.0, 11.7, 5.0)))
    # Broad rear hanger terminating in an exact 2.4 mm downward-open hook.
    hanger = at(Box(25.0, 4.0, 2.0), (94.0, -2.0, 7.5))
    hook_boss = at(Box(5.0, 4.0, 7.0), (116.5, -2.0, 3.5))
    hook_bore = axle_y_cylinder(1.2, 5.0).moved(Location((119.0, -2.5, 7.0)))
    hook_slot = at(Box(2.4, 5.0, 3.5), (117.8, -2.5, 3.5))
    pieces.append((hanger + hook_boss) - hook_bore - hook_slot)
    return Compound(children=pieces)


def tender(angle: float, yaw: float, dx: float):
    pieces = [
        at(Box(55.0, 24.0, 5.0), (116.0, -12.0, 7.0)),
        at(Box(55.0, 29.0, 28.0), (116.0, -14.5, 12.0)),
        at(Box(51.0, 25.0, 4.0), (118.0, -12.5, 40.0)),
        at(Box(22.0, 21.0, 3.0), (119.0, -10.5, 5.5)),
        at(Box(22.0, 21.0, 3.0), (146.0, -10.5, 5.5)),
        axle_y_cylinder(1.0, 16.0).moved(Location((119.0, -8.0, 7.0))),
        axle_y_cylinder(1.0, 16.0).moved(Location((168.0, -8.0, 7.0))),
    ]
    for x in TENDER_AXLE_X:
        pieces.append(wheelset(TENDER_DIAMETER, 25.0, x, TENDER_DIAMETER / 2.0, angle))
    assembly = Compound(children=pieces)
    assembly = assembly.moved(Location((-119.0, 0, 0))).rotate(Axis.Z, yaw).moved(Location((119.0 + dx, 0, 0)))
    return assembly


def build_state(state_index: int):
    params = STATE_PARAMETERS[state_index]
    return Compound(children=[locomotive(params["wheel_deg"]), tender(params["wheel_deg"], params["tender_yaw_deg"], params["tender_dx"])])


def load_state_module(index: int):
    path = ROOT / f"state-{index}.step.py"
    spec = importlib.util.spec_from_file_location(f"ouray_state_{index}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def export_all():
    for index in (0, 1, 2):
        model = load_state_module(index).gen_step()
        export_step(model, ROOT / f"state-{index}.step")
        export_stl(model, ROOT / f"state-{index}.stl", tolerance=0.05, angular_tolerance=0.12)


if __name__ == "__main__":
    export_all()
