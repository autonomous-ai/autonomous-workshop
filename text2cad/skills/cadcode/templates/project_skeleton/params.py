"""All dimensions for the project. Edit values here, not inside geometry."""

from dataclasses import dataclass


@dataclass
class Params:
    # AI_EDITABLE: dimensions only. Add new fields below as features need them.

    # Overall footprint
    width: float = 120.0
    depth: float = 80.0
    height: float = 35.0

    # Wall + cosmetic
    wall: float = 3.0
    corner_radius: float = 6.0
    fillet_radius: float = 1.5

    # Fasteners
    screw_diameter: float = 3.2          # M3 clearance
    screw_boss_diameter: float = 8.0
    screw_margin: float = 10.0

    # Assembly clearances
    lid_gap: float = 0.4                  # slip fit between base and lid
