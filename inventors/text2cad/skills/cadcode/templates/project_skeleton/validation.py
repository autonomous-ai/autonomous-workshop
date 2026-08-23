"""Runtime checks on Params before any geometry is built.

Two layers (see references/component-integration.md):

  * ``validate_params`` — HARD asserts for impossible fits. A failure blocks
    the build (surfaces as VALIDATION_FAILED). Edit when you add new
    constraints; do not silence failures.
  * ``functional_warnings`` — SOFT, structured assembly-feasibility checks. The
    build still renders; the driver's functional-review loop won't finish while
    any remain. Return ``kind:"functional"`` entries.
"""

from __future__ import annotations

from params import Params


def functional_warnings(p: Params) -> list[dict]:
    """Assembly/installation feasibility → structured `functional` warnings.

    Return one dict per failed check; an empty list means "assembles fine".
    Each entry: ``{"part", "kind": "functional", "detail", "severity": "warning"}``.

    Example (delete if not integrating a captive-cable component):

        warnings = []
        if p.connector_pocket_dia < p.connector_dia + 0.6:
            warnings.append({
                "part": "body", "kind": "functional",
                "detail": "connector pocket can't clear the collar — won't install",
                "severity": "warning",
            })
        return warnings
    """
    return []


def validate_params(p: Params) -> None:
    # FDM printability
    assert p.wall >= 1.6, f"wall too thin for FDM: {p.wall} mm < 1.6 mm"
    assert p.fillet_radius < p.wall, (
        f"fillet {p.fillet_radius} would erode wall {p.wall}"
    )

    # Fastener spacing
    assert p.screw_margin > p.screw_boss_diameter / 2, (
        "screw_margin must clear the boss"
    )
    assert p.screw_boss_diameter > p.screw_diameter, (
        "screw boss must be wider than the screw"
    )

    # Footprint sanity
    assert p.width > 0 and p.depth > 0 and p.height > 0, "all dims positive"
    assert p.width >= 4 * p.wall, "width must clear two walls + margin"
    assert p.depth >= 4 * p.wall, "depth must clear two walls + margin"
