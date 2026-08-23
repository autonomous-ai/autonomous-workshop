"""Two-part box + drop-in lid — the canonical multi-part FIT example.

Demonstrates the whole multi-part discipline in one file:
  * a real ``cq.Assembly`` of two separately-printed parts (base + lid), so each
    gets its own STL and the deterministic collision check applies;
  * ONE source-of-truth mating dimension: the lid lip is derived from the base
    cavity via ``cadlib.fits.peg_for`` — the male can never drift from the
    female because both come from ``cavity`` + the FDM ``fit`` clearance;
  * parts placed in their ASSEMBLED position that touch where they mate and do
    not interpenetrate (collision-clean);
  * declared ``functional_checks`` that prove the lid actually seats and is
    removable — fit/assembly verified, not assumed.

Tweak ``Params`` and re-run. Change ``fit`` to "snug" for a firmer hold or
"free" for an easy drop-in; everything else follows.
"""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq

from cadlib.enclosure import hollow_box
from cadlib.fits import mating_clearance, peg_for


@dataclass(frozen=True)
class Params:
    length: float = 80.0       # outer X
    width: float = 60.0        # outer Y
    height: float = 25.0       # base outer Z (cavity depth = height - wall)
    wall: float = 2.0          # uniform wall
    corner_radius: float = 4.0 # unified vertical radius (base + lid)
    lid_thickness: float = 3.0 # lid plate
    lip_height: float = 6.0    # how far the lid lip reaches into the cavity
    fit: str = "slip"          # FDM mating clearance class for the lip↔cavity

    # --- derived, single source of truth -------------------------------------
    @property
    def cavity_l(self) -> float:
        return self.length - 2 * self.wall

    @property
    def cavity_w(self) -> float:
        return self.width - 2 * self.wall

    @property
    def cavity_depth(self) -> float:
        return self.height - self.wall

    @property
    def lip_l(self) -> float:
        # The male lip is DERIVED from the female cavity at the chosen fit, so
        # the two halves share one nominal and cannot drift apart.
        return peg_for(self.cavity_l, self.fit)

    @property
    def lip_w(self) -> float:
        return peg_for(self.cavity_w, self.fit)


def build_base(p: Params) -> cq.Workplane:
    """Open-top shell; the cavity is the female half of the mate."""
    return hollow_box(
        length=p.length,
        width=p.width,
        height=p.height,
        wall=p.wall,
        corner_radius=p.corner_radius,
    )


def build_lid(p: Params) -> cq.Workplane:
    """Capping plate with a downward lip that drops into the cavity.

    Built in its own local frame, plate centred on the origin; the lip hangs
    below the plate's underside. ``assembly`` seats it onto the base.
    """
    plate = cq.Workplane("XY").box(p.length, p.width, p.lid_thickness)
    if p.corner_radius > 0:
        plate = plate.edges("|Z").fillet(p.corner_radius)
    lip = (
        cq.Workplane("XY")
        .box(p.lip_l, p.lip_w, p.lip_height)
        .translate((0, 0, -(p.lid_thickness + p.lip_height) / 2))
    )
    return plate.union(lip)


def functional_checks(p: Params) -> list[dict]:
    """Prove the lid seats and is removable — assembly feasibility, not geometry.

    Returns ``functional`` warnings (severity "warning", so the build loop treats
    them as blocking) when the mate can't work; an empty list means the design
    passes its own fit check.
    """
    warnings: list[dict] = []
    clearance = mating_clearance(p.fit)
    if not 0.05 <= clearance <= 0.35:
        warnings.append(
            {
                "part": "lid",
                "kind": "functional",
                "detail": (
                    f"lip↔cavity clearance {clearance} mm (fit '{p.fit}') is "
                    "outside the hand-assembly band 0.05–0.35 mm — the lid will "
                    "jam or rattle."
                ),
                "severity": "warning",
            }
        )
    if p.lip_height < 3.0:
        warnings.append(
            {
                "part": "lid",
                "kind": "functional",
                "detail": (
                    f"lip engagement {p.lip_height} mm < 3 mm — too shallow to "
                    "locate the lid; it will tip out."
                ),
                "severity": "warning",
            }
        )
    if p.lip_height >= p.cavity_depth:
        warnings.append(
            {
                "part": "lid",
                "kind": "functional",
                "detail": (
                    f"lip {p.lip_height} mm reaches the cavity floor "
                    f"({p.cavity_depth} mm deep) — the lid won't sit flush."
                ),
                "severity": "warning",
            }
        )
    return warnings


def assembly(p: Params) -> cq.Assembly:
    base = build_base(p)
    lid = build_lid(p)
    # Seat the lid: its plate underside rests on the base's top rim, lip into the
    # cavity. Plate underside (local -lid_thickness/2) -> base top (height/2).
    seat_z = p.height / 2 + p.lid_thickness / 2
    asm = cq.Assembly()
    asm.add(base, name="base", color=cq.Color(0.80, 0.82, 0.85))
    asm.add(lid, name="lid", loc=cq.Location((0, 0, seat_z)), color=cq.Color(0.30, 0.55, 0.90))
    return asm


def gen_step():
    p = Params()
    # Hard guard for the impossible (caught before paying a render cycle).
    assert p.lip_l > 0 and p.lip_w > 0, "lip clearance too large for the cavity"
    return {"shape": assembly(p), "warnings": functional_checks(p)}
