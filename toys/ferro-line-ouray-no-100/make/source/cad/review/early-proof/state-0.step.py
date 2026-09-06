"""Neutral engaged state: rear hook is on the tender bar at zero yaw."""

from proof import build_state


def gen_step():
    return build_state(0)
