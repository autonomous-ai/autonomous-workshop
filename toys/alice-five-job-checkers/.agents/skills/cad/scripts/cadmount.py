#!/usr/bin/env python3
"""Seats for off-the-shelf components, derived from the part's own STEP.

The third sibling. `cadfits` derives the second half of a mate from the first;
`cadprint` derives a wall from the nozzle; this one derives a **cavity from the
component that has to sit in it**, so that no dimension of a bought part is
ever typed into a generator.

    import cadmount
    servo = cadmount.load("ref/sg90_micro_servo.step")
    bracket -= cadmount.seat_for(servo, "slip")          # the pocket
    bracket -= cadmount.bolt_cutter(servo, depth=6)      # its screw holes

A motor seat sized by hand is the mate `cadfits` warns about, one step worse:
the nominal lives in a datasheet, a web page or a photograph rather than in the
project at all, so nothing downstream can even restate it. `validate`,
`interfere`, `check_fit` and `check_mesh` all pass a bracket whose pocket is
2 mm too shallow.

Never offset the imported solid
-------------------------------
`offset(solid, +c)` is the obvious way to grow a component into its clearance
envelope. On a real catalog STEP it is a trap. Measured on the step.parts SG90:

    motor    bbox z 0.00 .. 29.90
    offset(motor, +0.3)   bbox z -0.30 .. 27.00      <- 2.9 mm shorter

OCC dropped the output hub and all 24 spline teeth and returned a solid that is
*smaller* than its input where it matters, with no error. A pocket cut from
that envelope is a pocket the servo's spline crashes into.

So the shadow below is built from sections of the **raw** solid, and clearance
is applied as a 2D offset of the section union, where OCC is reliable. Every
seat is then verified to contain the component it was derived from, the sample
count is doubled until it does, and a seat that will not converge raises rather
than returning a plausible cavity.

Insertion
---------
A seat is a **prism** along `insert`: the union of the component's cross
sections swept straight through. That is what makes it insertable. An exact
offset of the component hugs it more closely and cannot be assembled at all
whenever the component is wider anywhere than it is at its mouth.

`seat_for` does not know where the bracket's surface is, so `mouth` extends the
cavity back along the insertion direction to break through it. A blind seat
(the default) is correct geometry and frequently leaves a skin the slicer
prints and the servo cannot pass.

What this cannot answer
-----------------------
That the seat is reachable in assembly order, and that the component can travel
to it through the rest of the model — `scripts/check_motion` with a manifest.
That the bracket around a thin seat wall can be printed — `check_thickness`.

    .venv/bin/python "$CAD_SKILL_ROOT/scripts/cadmount.py"      # self-check
"""

from __future__ import annotations

import math
from pathlib import Path

import cadfits

# Sections taken along the insertion axis to build the shadow. The default is
# generous for a prismatic component and is doubled on demand; the verification
# below is what makes the number safe rather than the number itself.
DEFAULT_SECTIONS = 24
MAX_SECTIONS = 384

# Component material allowed outside its own seat. Not zero: the section union
# is a sampled shadow and OCC booleans leave slivers well under this.
CONTAIN_TOL_MM3 = 1e-3

# A cylindrical face is a candidate screw hole only inside this band. Below it
# is a vent, a moulding pin or a spline tooth; above it is a bore for something
# other than a fastener, which is a seat rather than a bolt hole.
BOLT_D_MIN = 1.0
BOLT_D_MAX = 8.0

# How parallel a hole axis must be to the requested direction to count.
AXIS_TOL = 1e-3
# Fraction of a full turn a bore's faces must sweep between them. A rounded
# edge sweeps a quarter turn and a slot end exactly a half, so 0.6 separates a
# bore from both while still admitting the SG90 flange hole's trimmed 0.775.
MIN_TURN = 0.6


def load(path: str | Path):
    """Import a component STEP as one solid, or say why it is not one.

    Catalog parts are single solids; a multi-solid import is usually an
    assembly whose sub-parts move relative to each other, and a seat derived
    from all of them at once is a seat for a pose rather than for a part.
    """
    from build123d import import_step

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"no component STEP at {path}. Fetch one with "
            f"skills/step-parts/scripts/download_step_part.py --id <id> --download")
    shape = import_step(str(path))
    solids = shape.solids()
    if not solids:
        raise ValueError(f"{path.name} imported with no solid")
    if len(solids) > 1:
        raise ValueError(
            f"{path.name} imported as {len(solids)} solids. Pick the one to seat "
            "-- import_step(...).solids()[i] -- rather than seating the assembly, "
            "whose parts move relative to each other.")
    return solids[0]


def _axis_frame(insert):
    """Unit insertion direction and a plane normal to it, as build123d objects."""
    from build123d import Plane, Vector

    direction = Vector(insert)
    if direction.length < AXIS_TOL:
        raise ValueError(f"insert direction must be non-zero, got {insert}")
    direction = direction.normalized()
    return direction, Plane(origin=(0, 0, 0), z_dir=direction)


def shadow(component, insert=(0, 0, 1), sections: int = DEFAULT_SECTIONS):
    """The component's outline seen along `insert`, as a face at the origin plane.

    Sections of the raw solid, each carried back to the origin plane and
    unioned. Sampled, so it is a lower bound on the true silhouette; `seat_for`
    is what turns that into a guarantee.
    """
    from build123d import Location, Plane

    if sections < 1:
        raise ValueError(f"sections must be at least 1, got {sections}")
    direction, plane = _axis_frame(insert)
    box = component.bounding_box()
    corners = [
        (box.min.X, box.min.Y, box.min.Z), (box.max.X, box.min.Y, box.min.Z),
        (box.min.X, box.max.Y, box.min.Z), (box.max.X, box.max.Y, box.min.Z),
        (box.min.X, box.min.Y, box.max.Z), (box.max.X, box.min.Y, box.max.Z),
        (box.min.X, box.max.Y, box.max.Z), (box.max.X, box.max.Y, box.max.Z),
    ]
    from build123d import Vector
    spans = [Vector(c).dot(direction) for c in corners]
    low, high = min(spans), max(spans)

    merged = None
    for index in range(sections):
        offset_along = low + (index + 0.5) * (high - low) / sections
        cut = component & Plane(origin=tuple(direction * offset_along),
                                z_dir=direction)
        if cut is None or not cut.faces():
            continue
        flat = Location(-direction * offset_along) * cut
        merged = flat if merged is None else merged + flat
    if merged is None or not merged.faces():
        raise ValueError(
            f"no cross section of the component along {insert}; it may be empty")
    return merged, low, high, direction, plane


def outside_volume(outer, inner) -> float:
    """Volume of `inner` that lies outside `outer`. Zero means contained."""
    left = inner - outer
    if left is None:
        return 0.0
    return float(sum(solid.volume for solid in left.solids()))


def seat_for(component, fit: str | float = cadfits.DEFAULT_FIT, *,
             insert=(0, 0, 1), mouth: float = 0.0,
             sections: int = DEFAULT_SECTIONS,
             max_sections: int = MAX_SECTIONS):
    """The cavity to subtract so `component` drops in along `insert`.

    The component's silhouette along the insertion direction, grown by the
    per-side clearance for `fit`, swept through the component's own extent plus
    that clearance at each end, plus `mouth` more on the entry side.

    Verified to contain the component it came from, refining until it does.
    """
    from build123d import Kind, Location, extrude, offset as b3d_offset

    clearance = cadfits.mating_clearance(fit)
    if clearance <= 0:
        raise ValueError(
            f"fit {fit!r} gives a per-side clearance of {clearance} mm. A seat "
            "for a bought part cannot be an interference fit -- the component "
            "does not compress. Use 'snug' or looser.")
    if mouth < 0:
        raise ValueError(f"mouth must be >= 0, got {mouth}")

    count = sections
    while True:
        profile, low, high, direction, _plane = shadow(component, insert, count)
        grown = b3d_offset(profile, clearance, kind=Kind.INTERSECTION)
        if grown is None or not grown.faces():
            raise ValueError(
                f"growing the silhouette by {clearance} mm returned no face")
        length = (high - low) + 2 * clearance + mouth
        prism = extrude(grown, amount=length, dir=tuple(direction))
        cavity = Location(direction * (low - clearance)) * prism

        escaped = outside_volume(cavity, component)
        if escaped <= CONTAIN_TOL_MM3:
            return cavity
        if count >= max_sections:
            raise ValueError(
                f"a seat sampled at {count} sections still leaves "
                f"{escaped:.3f} mm3 of the component outside it. The silhouette "
                "is not converging -- use cadmount.envelope_for(), which cannot "
                "miss a feature, and accept the looser pocket.")
        count *= 2


def envelope_for(component, fit: str | float = cadfits.DEFAULT_FIT):
    """The component's bounding box grown by the clearance for `fit`.

    Looser than :func:`seat_for` and immune to every sampling question: a box
    around the extents cannot miss a feature. Reach for it when a seat refuses
    to converge, or when a rectangular pocket is what the bracket wanted.
    """
    from build123d import Box, Location

    clearance = cadfits.mating_clearance(fit)
    if clearance <= 0:
        raise ValueError(
            f"fit {fit!r} is an interference fit; a bought part does not compress")
    box = component.bounding_box()
    return Location(box.center()) * Box(box.size.X + 2 * clearance,
                                        box.size.Y + 2 * clearance,
                                        box.size.Z + 2 * clearance)


def _bores(component) -> list[dict]:
    """Cylindrical faces grouped into whole bores: co-axial, co-radial, sweep summed.

    A bore in an imported STEP is very often **not** one full cylindrical face.
    The step.parts SG90's two flange holes are single faces sweeping 77.5% of a
    turn each; other importers split a bore at its seam into halves. Requiring a
    full face misses the first kind, and reading a centre from `face.center()`
    misplaces both -- the centroid of a trimmed cylinder sits off its own axis,
    1.00 mm off on that servo, which is a screw hole drilled in the wrong place.

    So faces are keyed by the axis *line* and radius, their sweeps added, and
    every position derived from the axis rather than from a face.
    """
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from build123d import GeomType, Vector

    groups: dict[tuple, dict] = {}
    for face in component.faces():
        if face.geom_type != GeomType.CYLINDER:
            continue
        adaptor = BRepAdaptor_Surface(face.wrapped)
        cylinder = adaptor.Cylinder()
        radius = cylinder.Radius()
        vector = cylinder.Axis().Direction()
        axis = Vector(vector.X(), vector.Y(), vector.Z()).normalized()
        # One line, one key: flip the direction to a canonical sign so a bore
        # whose faces disagree about which way is "up" still groups.
        if (round(axis.X, 6), round(axis.Y, 6), round(axis.Z, 6)) < (0, 0, 0):
            axis = axis * -1
        point = cylinder.Axis().Location()
        origin = Vector(point.X(), point.Y(), point.Z())
        foot = origin - axis * origin.dot(axis)        # axis point nearest world origin
        key = (round(radius, 4),
               round(axis.X, 4), round(axis.Y, 4), round(axis.Z, 4),
               round(foot.X, 4), round(foot.Y, 4), round(foot.Z, 4))

        surface_point = face.position_at(0.5, 0.5)     # on the face, not in the solid
        radial = surface_point - (foot + axis * (surface_point - foot).dot(axis))
        if radial.length < AXIS_TOL:
            continue
        # Material is outside a hole and inside a boss, so the outward surface
        # normal on a hole points back towards its own axis. The whole classifier.
        concave = face.normal_at(surface_point).dot(radial.normalized()) < 0

        box = face.bounding_box()
        spans = [Vector(x, y, z).dot(axis)
                 for x in (box.min.X, box.max.X)
                 for y in (box.min.Y, box.max.Y)
                 for z in (box.min.Z, box.max.Z)]

        bore = groups.setdefault(key, {
            "diameter": 2 * radius, "axis": axis, "foot": foot,
            "sweep": 0.0, "area": 0.0, "concave_area": 0.0,
            "low": min(spans), "high": max(spans),
        })
        bore["sweep"] += adaptor.LastUParameter() - adaptor.FirstUParameter()
        bore["area"] += face.area
        if concave:
            bore["concave_area"] += face.area
        bore["low"] = min(bore["low"], min(spans))
        bore["high"] = max(bore["high"], max(spans))

    bores = []
    for bore in groups.values():
        bore["turn"] = bore["sweep"] / (2 * math.pi)
        bore["concave"] = bore["concave_area"] > bore["area"] / 2
        bore["centre"] = bore["foot"] + bore["axis"] * ((bore["low"] + bore["high"]) / 2)
        bore["span"] = bore["high"] - bore["low"]
        bores.append(bore)
    return bores


def bolt_holes(component, along=(0, 0, 1)) -> list[dict]:
    """Every fastener-sized bore whose axis lies along `along`.

    `along=None` accepts any axis and reports each bore's own, which is what a
    component already placed into an assembly needs: its holes point wherever
    the pose put them, and asking the placed solid directly beats transforming
    a pattern found in part coordinates.

    Returns dicts with `diameter`, `centre` (**on the axis**, at the bore's
    axial midpoint), `span`, `turn` and `along`. Honest rather than clever: a
    servo's horn screw comes back next to its two flange holes, because nothing
    in the geometry says which is for mounting. :func:`bolt_pattern` picks.
    """
    direction = None if along is None else _axis_frame(along)[0]
    holes = []
    for bore in _bores(component):
        if not bore["concave"]:
            continue
        if bore["turn"] < MIN_TURN:
            continue                                   # a slot end or a fillet
        if direction is not None and abs(abs(bore["axis"].dot(direction)) - 1.0) > AXIS_TOL:
            continue
        if not BOLT_D_MIN <= bore["diameter"] <= BOLT_D_MAX:
            continue
        holes.append({
            "diameter": round(bore["diameter"], 4),
            "centre": bore["centre"],
            "span": round(bore["span"], 4),
            "turn": round(bore["turn"], 4),
            "along": bore["axis"],
        })
    return sorted(holes, key=lambda h: (h["diameter"], h["centre"].X, h["centre"].Y))


def bolt_pattern(component, along=(0, 0, 1)) -> list[dict]:
    """The largest group of same-diameter holes along `along` -- the mount pattern.

    Two holes of one size beat one hole of another, which is what separates a
    flange pattern from the single bore that happens to share its axis
    direction. Ties go to the larger diameter, because a mounting screw is the
    bigger fastener on every servo and gearmotor in the catalog.
    """
    holes = bolt_holes(component, along)
    groups: dict[tuple, list[dict]] = {}
    for hole in holes:
        axis = hole["along"]
        # Group on the axis too: with `along=None` a component's flange holes
        # and an unrelated pair of bores across it are both pairs, and only the
        # co-directional group is a mounting pattern.
        groups.setdefault((hole["diameter"],
                           round(axis.X, 4), round(axis.Y, 4), round(axis.Z, 4)),
                          []).append(hole)
    if not groups:
        return []
    best = max(groups.items(), key=lambda item: (len(item[1]), item[0][0]))
    return best[1]


def bolt_cutter(component, fit: str | float = "free", *, depth: float,
                along=(0, 0, 1), holes: list[dict] | None = None):
    """Clearance holes through the bracket for the detected mount pattern.

    Diameters come from :func:`cadfits.slot_for`, so a screw clearance obeys the
    same table as every other mate in the project rather than a second one.
    """
    from build123d import Cylinder, Location, Plane

    if depth <= 0:
        raise ValueError(f"depth must be positive, got {depth}")
    direction, _plane = _axis_frame(along)
    pattern = holes if holes is not None else bolt_pattern(component, along)
    if not pattern:
        raise ValueError(
            f"no fastener-sized bore along {along} in this component. Check the "
            "axis, or pass holes= explicitly after reading bolt_holes().")
    cutter = None
    for hole in pattern:
        bore = cadfits.slot_for(hole["diameter"], fit)
        plane = Plane(origin=tuple(hole["centre"]), z_dir=direction)
        pin = plane.location * Cylinder(radius=bore / 2, height=depth)
        cutter = pin if cutter is None else cutter + pin
    return cutter


def seat_report(bracket, component) -> dict:
    """What the built bracket actually leaves the component, measured.

    Independent of how the seat was made: it reads the two solids as they are.
    An audit that recomputed `seat_for` would reduce to `True`.
    """
    overlap = bracket & component
    clash = float(sum(solid.volume for solid in overlap.solids())) if overlap else 0.0
    gap = None
    if clash <= CONTAIN_TOL_MM3:
        try:
            gap = float(bracket.distance_to(component))
        except Exception:                              # noqa: BLE001
            gap = None
    return {
        "clash_mm3": clash,
        "seated": clash <= CONTAIN_TOL_MM3,
        "min_clearance_mm": gap,
    }


def _self_check() -> int:
    """Assertions this module has to keep. Run as a script; no test framework."""
    import math

    from build123d import Axis, Box, Cylinder, Location, Plane, Pos, Rot

    failures: list[str] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        print(f"{'ok  ' if ok else 'FAIL'} {label}{('  - ' + detail) if detail else ''}")
        if not ok:
            failures.append(label)

    # --- a seat is the silhouette plus one clearance per side, exactly --------
    block = Box(10, 20, 30)
    slip = cadfits.mating_clearance("slip")
    seat = seat_for(block, "slip")
    want = (10 + 2 * slip) * (20 + 2 * slip) * (30 + 2 * slip)
    check("box seat is silhouette + 2x clearance",
          math.isclose(seat.volume, want, rel_tol=1e-9), f"{seat.volume:.4f} vs {want:.4f}")
    check("box seat contains its component",
          outside_volume(seat, block) <= CONTAIN_TOL_MM3)
    check("mouth extends the seat by exactly its length",
          math.isclose(seat_for(block, "slip", mouth=5).volume,
                       seat.volume + (10 + 2 * slip) * (20 + 2 * slip) * 5,
                       rel_tol=1e-9))

    # --- the shadow is the silhouette, not the bounding box -------------------
    ell = Box(30, 10, 10) + Pos(10, 10, 0) * Box(10, 10, 10)
    ell_seat = seat_for(ell, "slip")
    check("L-shape seat is tighter than its bounding box",
          ell_seat.volume < envelope_for(ell, "slip").volume,
          f"seat {ell_seat.volume:.0f} < envelope {envelope_for(ell, 'slip').volume:.0f}")
    check("L-shape seat still contains it",
          outside_volume(ell_seat, ell) <= CONTAIN_TOL_MM3)

    # --- an undercut is what the prism exists for -----------------------------
    # Narrow at the mouth, wide below: an exact offset of this cannot be
    # assembled, and the seat has to be a straight slot at the widest section.
    tee = Box(6, 6, 20) + Pos(0, 0, -13) * Box(20, 20, 6)
    tee_seat = seat_for(tee, "slip")
    check("undercut seat contains the whole component",
          outside_volume(tee_seat, tee) <= CONTAIN_TOL_MM3)
    check("undercut seat is prismatic at the widest section",
          math.isclose(tee_seat.bounding_box().size.X, 20 + 2 * slip, abs_tol=1e-6),
          f"{tee_seat.bounding_box().size.X:.4f}")

    # --- a seat that cannot converge refuses rather than under-cutting --------
    # One section through the middle of the tee misses the wide foot entirely.
    try:
        seat_for(tee, "slip", sections=1, max_sections=1)
    except ValueError as err:
        check("under-sampled seat refuses", "outside it" in str(err))
    else:
        check("under-sampled seat refuses", False, "returned a seat that misses material")

    # --- clearance comes from cadfits, and an interference fit is refused -----
    check("looser fit gives a bigger seat",
          seat_for(block, "free").volume > seat_for(block, "snug").volume)
    try:
        seat_for(block, "press")
    except ValueError as err:
        check("press fit refused for a bought part", "does not compress" in str(err))
    else:
        check("press fit refused for a bought part", False)

    # --- envelope can never miss a feature -----------------------------------
    env = envelope_for(ell, "slip")
    check("envelope contains the component", outside_volume(env, ell) <= CONTAIN_TOL_MM3)

    # --- holes are found, bosses are not -------------------------------------
    plate = Box(40, 20, 4)
    for x in (-15, 15):
        plate -= Pos(x, 0, 0) * Cylinder(radius=1.5, height=10)
    plate += Pos(0, 0, 4) * Cylinder(radius=4, height=6)          # a boss
    plate -= Pos(0, 0, 4) * Cylinder(radius=0.4, height=20)       # a vent, not a fastener
    found = bolt_holes(plate, along=(0, 0, 1))
    check("both mount holes found", len(found) == 2, f"{[h['diameter'] for h in found]}")
    check("hole diameter is the modelled one",
          all(math.isclose(h["diameter"], 3.0, abs_tol=1e-6) for h in found))
    check("the boss is not a hole",
          all(h["diameter"] < 7.9 for h in found))
    check("sub-fastener bore ignored",
          all(h["diameter"] >= BOLT_D_MIN for h in found))
    check("holes across the axis are not counted",
          bolt_holes(plate, along=(1, 0, 0)) == [])

    # --- a trimmed bore is still a bore, and its centre is on its axis -------
    # The regression the step.parts SG90 taught: its flange holes are single
    # faces sweeping 77.5% of a turn, and the centroid of such a face sits
    # 1.00 mm off the axis it belongs to. Requiring a full face loses the hole;
    # reading the centre off the face drills it in the wrong place.
    notched = Box(40, 20, 4) - Cylinder(radius=1.5, height=10)
    notched -= Pos(0, -6, 0) * Box(2, 10, 10)          # a channel into the bore
    trimmed = bolt_holes(notched, along=(0, 0, 1))
    check("a trimmed bore is still found", len(trimmed) == 1,
          f"{[(round(h['diameter'], 3), round(h['turn'], 3)) for h in trimmed]}")
    if trimmed:
        check("the trimmed bore sweeps less than a full turn",
              0.6 <= trimmed[0]["turn"] < 0.95, f"{trimmed[0]['turn']}")
        check("its centre is on the axis, not the face centroid",
              abs(trimmed[0]["centre"].X) < 1e-6 and abs(trimmed[0]["centre"].Y) < 1e-6,
              f"({trimmed[0]['centre'].X:.4f}, {trimmed[0]['centre'].Y:.4f})")

    # --- a bore split at its seam is one bore, not two halves -----------------
    barrel = Cylinder(radius=1.5, height=10)
    split = Box(40, 20, 4) - (barrel & Pos(0, 5, 0) * Box(10, 10, 20)) \
                           - (barrel & Pos(0, -5, 0) * Box(10, 10, 20))
    halves = bolt_holes(split, along=(0, 0, 1))
    check("a seam-split bore groups into one", len(halves) == 1,
          f"{[round(h['turn'], 3) for h in halves]}")

    # --- a half cylinder is a slot end, and is not a fastener hole ------------
    slotted = Box(20, 6, 4) - Pos(-10, 0, 0) * Cylinder(radius=2, height=10)
    check("a slot end is not a bolt hole", bolt_holes(slotted, along=(0, 0, 1)) == [],
          f"{[round(h['turn'], 3) for h in bolt_holes(slotted, along=(0, 0, 1))]}")

    # --- the pattern is the group, not every bore ----------------------------
    with_horn = plate - Pos(0, 0, 10) * Cylinder(radius=1.0, height=20)
    check("pattern picks the pair over the lone bore",
          len(bolt_pattern(with_horn)) == 2 and
          math.isclose(bolt_pattern(with_horn)[0]["diameter"], 3.0, abs_tol=1e-6),
          f"{[round(h['diameter'], 2) for h in bolt_holes(with_horn)]}")

    # --- any-axis detection, which is how a placed component is read --------
    # `check_mount` asks the component *after* the assembly pose has moved it,
    # so the holes point wherever that pose put them and no axis is known.
    tipped = Rot(0, 90, 0) * plate
    anywhere = bolt_holes(tipped, along=None)
    check("any-axis detection finds the same two holes", len(anywhere) == 2,
          f"{[round(h['diameter'], 3) for h in anywhere]}")
    check("each hole reports its own axis, now along X",
          all(math.isclose(abs(h["along"].X), 1.0, abs_tol=1e-6) for h in anywhere),
          f"{[tuple(round(c, 3) for c in (h['along'].X, h['along'].Y, h['along'].Z)) for h in anywhere]}")
    check("holes stay 30 mm apart through the rotation",
          len(anywhere) == 2 and
          math.isclose((anywhere[0]["centre"] - anywhere[1]["centre"]).length, 30.0,
                       abs_tol=1e-6),
          f"{(anywhere[0]['centre'] - anywhere[1]['centre']).length:.4f}" if len(anywhere) == 2 else "")

    # A pair across one axis and a pair across another are both pairs; only the
    # co-directional group is a mounting pattern.
    crossed = plate - Pos(0, 0, 0) * Rot(0, 90, 0) * Cylinder(radius=2.0, height=60)
    grouped = bolt_pattern(crossed, along=None)
    check("any-axis pattern groups on the axis, not just the diameter",
          len(grouped) == 2 and
          all(math.isclose(abs(h["along"].Z), 1.0, abs_tol=1e-6) for h in grouped),
          f"{len(grouped)} hole(s)")

    cutter = bolt_cutter(plate, "free", depth=12)
    free = cadfits.mating_clearance("free")
    want_bore = 3.0 + 2 * free
    check("cutter bores use the cadfits clearance",
          math.isclose(cutter.volume, 2 * math.pi * (want_bore / 2) ** 2 * 12,
                       rel_tol=1e-6),
          f"{cutter.volume:.3f}")

    # --- the report reads the built solids, not the recipe --------------------
    bracket = Box(40, 40, 40) - seat_for(block, "slip")
    good = seat_report(bracket, block)
    check("a cut bracket seats the component", good["seated"], str(good))
    check("clearance measured is the fit clearance",
          good["min_clearance_mm"] is not None
          and math.isclose(good["min_clearance_mm"], slip, abs_tol=1e-6),
          str(good["min_clearance_mm"]))
    tight = seat_report(Box(40, 40, 40) - seat_for(Box(9, 19, 29), "slip"), block)
    check("an undersized pocket is reported as a clash",
          not tight["seated"] and tight["clash_mm3"] > 1.0, str(tight))

    print(f"\n{len(failures)} failed" if failures else "\nall checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_self_check())
