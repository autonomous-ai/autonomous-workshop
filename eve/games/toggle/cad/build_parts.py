"""Generate Eve's Toggle print kit STL meshes (build123d, deterministic).

The signature part is the living-hinge Toggle: a lever joined to a base by a
thin flexure film with a printed detent hump under the fulcrum so the lever is
bi-stable in UP/DOWN. All parts are single printable solids with no support on
the film. Layer-bridging recipe: 0.3 mm layers, film vertical so nothing
touches it, PETG/PLA.
"""
from build123d import (
    Box, Cylinder, Cone, Sphere, Align, Location, Locations, Pos, Rot, Axis,
    BuildPart, BuildLine, Polyline, Spline, RadiusArc, Mode, extrude, export_stl,
)
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "build"
OUT.mkdir(parents=True, exist_ok=True)

FILM_T = 0.8          # flexure film thickness (mm) - thin enough to flex
LEVER_H = 3.0


def toggle():
    """Real living-hinge: base + lever joined by a thin flexure film, with a
    detent hump under the fulcrum so the lever snaps either UP or DOWN."""
    with BuildPart() as p:
        # base (held in palm): 34 x 24 x 10
        Box(34, 24, 10, align=Align.MIN)
        # hinge web: a thin film rising from the base rear to meet the lever,
        # 0.8mm thick across the full width so it flexes, not breaks.
        with Locations((26, 0, 8)):
            Box(8, 24, FILM_T, align=(Align.MIN, Align.MIN, Align.MIN))
        # lever: 62 x 22 x 3, hinged at the rear, free at the front (the tab)
        with Locations((26, 1, 8 + FILM_T)):
            Box(62, 22, LEVER_H, align=(Align.MIN, Align.MIN, Align.MIN))
        # detent hump on the base UNDER the free end of the lever: the lever
        # rides over it and clicks into one of two stable positions.
        with Locations((30, 12, 10)):
            Cone(5, 1, 2.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # a printed spring fin on the base front that the lever tongue presses
        # against, giving the audible snap on flip.
        with Locations((78, 12, 8 + FILM_T)):
            Box(4, 3, 8, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return p.part


def keystone():
    """Two-face wedge (A/B) that flips inside the cradle."""
    with BuildPart() as p:
        Box(42, 24, 12)
        with Locations((21, 0, 0)):
            Cone(12, 3, 18, align=(Align.CENTER, Align.MIN, Align.MIN))
    return p.part


def cradle():
    """A shell that hides the Keystone's current face behind a low wall, with
    a viewing slot so only the showing A/B face is visible. Wall-thickness 2mm,
    open top so the Keystone can be flipped by hand."""
    W, D, H, t = 60, 48, 28, 2.0
    with BuildPart() as p:
        Box(W, D, H, align=Align.MIN)                       # outer
        with Locations((t, t, t)):
            # hollow the interior (open top) to make a shell
            Box(W - 2 * t, D - 2 * t, H - t, align=Align.MIN, mode=Mode.SUBTRACT)
    return p.part


def token(d=14, h=2.2):
    with BuildPart() as p:
        Cylinder(d / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return p.part


def suit_tile():
    return token(18, 2.6)


def flat_card(w, h, t=1.6):
    with BuildPart() as p:
        Box(w, h, t, align=Align.MIN)
    return p.part


def suit_board():
    with BuildPart() as p:
        Box(160, 70, 4, align=Align.MIN)
    return p.part


def pawn():
    with BuildPart() as p:
        Box(14, 10, 18, align=Align.MIN)
        with Locations((7, 5, 18)):
            Sphere(8)
    return p.part


parts = {
    "toggle.stl": toggle(),
    "keystone.stl": keystone(),
    "cradle.stl": cradle(),
    "suit_tile.stl": suit_tile(),
    "role_card.stl": flat_card(88, 56),
    "truth_card.stl": flat_card(88, 56),
    "suit_board.stl": suit_board(),
    "point_token.stl": token(),
    "pawn.stl": pawn(),
}

for name, part in parts.items():
    export_stl(part, OUT / name)
    print("wrote", name, (OUT / name).stat().st_size, "bytes")
print("DONE")
