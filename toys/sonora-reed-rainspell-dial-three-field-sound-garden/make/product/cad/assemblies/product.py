"""Named assembly placement only; part builders own geometry."""

from __future__ import annotations

import math

from build123d import Location
from cadgen import AssemblyHelper

import params as p
from parts.base import build_base
from parts.rib_deck import build_rib_deck
from parts.wheel import build_wheel
from parts.plectrum import build_plectrum
from parts.follower_keeper import build_follower_keeper
from parts.cap import build_cap


def build_product():
    assembly = AssemblyHelper("rainspell_dial")
    # The product is intentionally a one-filament object.  Keep component
    # labels, but omit optional STEP presentation colors: OpenCascade emits
    # their style records in process-dependent order, which changes otherwise
    # identical assembly STEP bytes during a fresh host rebuild.
    assembly.add(build_base(), "base")
    assembly.add(Location((0, 0, p.DECK_BOTTOM_Z)) * build_rib_deck(), "rib_deck")
    rest_rotation = Location((0, 0, 0), (0, 0, p.ASSEMBLY_REST_ANGLE_DEG))
    assembly.add(rest_rotation * Location((0, 0, p.CAGE_BOTTOM_Z)) * build_wheel(), "wheel")
    rest_angle = math.radians(p.ASSEMBLY_REST_ANGLE_DEG)
    follower_xy = (p.FOLLOWER_CENTER_RADIUS * math.cos(rest_angle), p.FOLLOWER_CENTER_RADIUS * math.sin(rest_angle))
    assembly.add(Location((follower_xy[0], follower_xy[1], p.PLECTRUM_ASSEMBLY_Z)) * build_plectrum(), "plectrum")
    assembly.add(rest_rotation * Location((0, 0, 28.0)) * build_follower_keeper(), "follower_keeper")
    assembly.add(Location((0, 0, p.CAP_BOTTOM_Z), (0, 0, p.CAP_LOCK_ROTATION_DEG)) * build_cap(), "cap")
    return assembly.compound()
