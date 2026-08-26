"""Shared parameters and builders for the STEP-first gate regression fixture."""
from build123d import Align, Box, Pos


# All dimensions are millimetres and assumed specifically for this fixture.
RECEIVER_X = 60.0
RECEIVER_Y = 30.0
FLOOR_Z = 4.0
RAIL_Y = 4.0
RAIL_Z = 6.0
CHANNEL_Y = RECEIVER_Y - 2.0 * RAIL_Y
STOP_X = 4.0
SLIDER_X = 20.0
SLIDER_Y = 20.0
SLIDER_Z = 4.0
SIDE_CLEARANCE = (CHANNEL_Y - SLIDER_Y) / 2.0
ASSEMBLY_SLIDER_Z = FLOOR_Z


def validate_parameters() -> None:
    assert SIDE_CLEARANCE == 1.0
    assert SLIDER_Y < CHANNEL_Y
    assert STOP_X < RECEIVER_X / 2.0
    assert FLOOR_Z > 0 and RAIL_Z > 0 and SLIDER_Z > 0


def _box(x: float, y: float, z: float):
    return Box(x, y, z, align=(Align.CENTER, Align.CENTER, Align.MIN))


def build_receiver():
    validate_parameters()
    floor = _box(RECEIVER_X, RECEIVER_Y, FLOOR_Z)
    rail_offset_y = (RECEIVER_Y - RAIL_Y) / 2.0
    left_rail = Pos(0, rail_offset_y, FLOOR_Z) * _box(RECEIVER_X, RAIL_Y, RAIL_Z)
    right_rail = Pos(0, -rail_offset_y, FLOOR_Z) * _box(RECEIVER_X, RAIL_Y, RAIL_Z)
    stop_offset_x = (RECEIVER_X - STOP_X) / 2.0
    end_stop = Pos(stop_offset_x, 0, FLOOR_Z) * _box(STOP_X, CHANNEL_Y, RAIL_Z)
    receiver = floor + [left_rail, right_rail, end_stop]
    receiver.label = "receiver"
    return receiver


def build_slider():
    validate_parameters()
    slider = _box(SLIDER_X, SLIDER_Y, SLIDER_Z)
    slider.label = "slider"
    return slider
