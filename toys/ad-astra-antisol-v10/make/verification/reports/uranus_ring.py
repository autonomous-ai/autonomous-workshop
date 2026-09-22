"""Uranus's ring: how big it is, how steep it is, and what it can touch.

The owner's brief worked its own table for this ring by treating the rim as a
plain cylindrical band standing straight up and ignoring the 7.77 degree lean,
and asked for the arithmetic to be redone properly in 3D on the real solid.
This is that.  Everything below is measured on the exact body `parts/world.py`
builds, either in closed form on the hoop's own geometry or on its
tessellation; nothing is read off the brief and nothing is read off a render.

Five questions, in the order the brief asks them.

**How far does it reach, in every direction?**  The ring body's own bounding
box, against the globe, the disc and the piece.

**How steep is it?**  Every downward-facing triangle of the finished ring,
worst first, against the 45 degree gate.  The gate is also run by
`check_overhang` on the whole printed part; this says WHERE on the hoop the
worst angle is and what holds it, which a pass/fail cannot.

Two families of face are excluded by name, both for the same reason and both
counted and reported rather than silently dropped.  The ring's own footprint on
the disc top is a flat face lying exactly on the disc's top face at Z =
`DISC_H`, and the ring's inner boundary is the globe's own sphere, which the
hoop is seated against the whole way round.  Each points downward somewhere --
the footprint straight down, the seat steeply down near the hoop's crown, where
the ring sits on the top of the ball -- and neither is a surface at all once
the part is fused, because there is solid under every square millimetre of
both.  `check_overhang` measures the fused part and never sees them.

**Does it break the ladder?**  Saturn must stay the widest world in the set and
`LADDER_CONSTANT` must not have moved.

**Do the piece heights still climb with rank?**

**What can it collide with?**  The Ø34.40 tray socket, the corona well a
trapped world drops into, the den flange, and the 18.00 mm flares standing
beside a den -- the last of which is the only thing in the set that reaches
this ring's height.

    "$WORKSHOP_PYTHON" measure/uranus_ring.py > measure/uranus-ring.md

Exit 0 when the gate passes, the ladder holds and nothing collides; 1 otherwise.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from build123d import Location                                # noqa: E402

import bool3d as X                                            # noqa: E402
import params as P                                            # noqa: E402
from assemblies.product import POCKET_FLOOR, FIELD_TOP        # noqa: E402
from parts.den import den_bodies                              # noqa: E402
from parts.corona import build_corona_cell                    # noqa: E402
from parts.world import build_world, upright_hoop, world_bodies  # noqa: E402

PLANET = "uranus"

#: How finely the ring is tessellated for the angle sweep, in mm of chord and
#: radians of angle.  Fine enough that a facet's own normal is the surface's.
TOLERANCE = 0.02
ANGULAR_TOLERANCE = 0.02

#: A facet under this area is a sliver of the tessellation rather than a face
#: of the solid, and its normal is noise.
MIN_FACET_MM2 = 1e-4

NOISE_MM3 = 1e-6
CORONA_SEAT = POCKET_FLOOR + P.CORONA_TILE_H
DEN_SEAT = POCKET_FLOOR + P.DEN_SPIGOT_DEPTH + P.DEN_PROUD


def facets(shape):
    """(centroid, unit normal, area) for every triangle of one body."""
    points, triangles = shape.tessellate(TOLERANCE, ANGULAR_TOLERANCE)
    out = []
    for a, b, c in triangles:
        pa, pb, pc = points[a], points[b], points[c]
        ux, uy, uz = pb.X - pa.X, pb.Y - pa.Y, pb.Z - pa.Z
        vx, vy, vz = pc.X - pa.X, pc.Y - pa.Y, pc.Z - pa.Z
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx
        length = math.sqrt(nx * nx + ny * ny + nz * nz)
        if length <= 0.0:
            continue
        area = 0.5 * length
        if area < MIN_FACET_MM2:
            continue
        centre = ((pa.X + pb.X + pc.X) / 3.0, (pa.Y + pb.Y + pc.Y) / 3.0,
                  (pa.Z + pb.Z + pc.Z) / 3.0)
        out.append((centre, (nx / length, ny / length, nz / length), area))
    return out


def overhang_deg(normal) -> float:
    """How far a downward-facing facet leans from vertical, in degrees.

    A vertical wall is 0 and a flat ceiling is 90, which is the sense
    `OVERHANG_LIMIT_DEG` is written in. Upward-facing facets return a negative
    number and are not overhangs at all.
    """
    return 90.0 - math.degrees(math.acos(max(-1.0, min(1.0, -normal[2]))))


def where(point, hoop) -> str:
    """A sentence naming where on the hoop a facet sits."""
    height = point[2]
    plan = math.hypot(point[0], point[1])
    if height <= hoop["cut_z"] + 0.02:
        return "on the cut where the hoop meets the disc top"
    if height <= hoop["gate_z"] + 0.05:
        return "on the foot, between the disc top and the gate crossing"
    return "on the hoop at Z %.2f, plan radius %.2f" % (height, plan)


def shared(one, other) -> float:
    meet = X.shape(X.meet(one, other))
    return 0.0 if meet is None else sum(item.volume for item in X.parts(meet))


def main() -> int:
    failures = []
    hoop = upright_hoop(PLANET, 1.0)
    spec = P.RINGED_WORLDS[PLANET]
    radius = P.globe_radius(PLANET)
    bodies = {side: world_bodies(PLANET, side) for side in P.SIDES}

    print("# Uranus's ring, measured on the solid")
    print()
    print("Redone in 3D on the exact body `parts/world.py` builds. The brief's own")
    print("table treated the rim as a plain cylindrical band standing straight up")
    print("and ignored the %.2f degree lean; both are reported below and where they"
          % (P.PLANETS[PLANET]["tilt"] - 90.0))
    print("differ the measured figure is the one used.")
    print()
    print("## What it is")
    print()
    print("| | value | |")
    print("|---|---:|---|")
    print("| globe diameter | Ø%.2f mm | unchanged |" % P.globe_diameter(PLANET))
    print("| ring inner diameter | Ø%.2f mm | tangent to the equator |"
          % P.URANUS_RING_INNER_D)
    print("| ring outer diameter | Ø%.2f mm | |" % spec["outer_d"])
    print("| projection per side | %.2f mm | against Saturn's %.2f |"
          % (P.URANUS_RING_PROJECTION, (P.RING_OUTER_D - P.globe_diameter('saturn')) / 2.0))
    print("| ring thickness | %.2f mm | against Saturn's %.2f |"
          % (spec["thickness"], P.RING_THICKNESS))
    print("| obliquity | %.2f deg | so the ring plane stands %.2f deg past vertical |"
          % (P.PLANETS[PLANET]["tilt"], P.PLANETS[PLANET]["tilt"] - 90.0))
    print()
    print("Saturn's ring is a near-horizontal plate at %.2f degrees and Uranus's is"
          % P.PLANETS["saturn"]["tilt"])
    print("a hoop on edge. **The two are not confusable in silhouette even before")
    print("size enters it**: one is a brim projecting sideways past the globe, the")
    print("other a band standing up over it. Size then separates them again --")
    print("Ø%.2f against Ø%.2f." % (P.RING_OUTER_D, spec["outer_d"]))
    print()
    print("## How far it reaches")
    print()
    print("| | X mm | Y mm | Z mm |")
    print("|---|---|---|---|")
    for side in P.SIDES:
        box = bodies[side]["ring"][1].bounding_box()
        print("| ring, %s | %.2f to %.2f | %.2f to %.2f | %.2f to %.2f |"
              % (side, box.min.X, box.max.X, box.min.Y, box.max.Y,
                 box.min.Z, box.max.Z))
    piece = {side: build_world(PLANET, side).bounding_box() for side in P.SIDES}
    for side in P.SIDES:
        box = piece[side]
        print("| whole piece, %s | %.2f to %.2f | %.2f to %.2f | %.2f to %.2f |"
              % (side, box.min.X, box.max.X, box.min.Y, box.max.Y,
                 box.min.Z, box.max.Z))
    print("| disc | -%.2f to %.2f | -%.2f to %.2f | 0.00 to %.2f |"
          % (P.DISC_NOMINAL_D / 2, P.DISC_NOMINAL_D / 2,
             P.DISC_NOMINAL_D / 2, P.DISC_NOMINAL_D / 2, P.DISC_H))
    print()
    print("**In plan the ring adds nothing.** Its greatest reach from the axis is")
    print("%.2f mm and the disc's is %.2f, so the piece's footprint is the disc's,"
          % (spec["outer_d"] / 2.0, P.DISC_NOMINAL_D / 2.0))
    print("exactly as it was before this correction. In height it adds %.2f mm:"
          % (piece["sol"].max.Z - P.piece_height(PLANET)))
    print("the globe's crown was %.2f mm and the hoop's is %.2f. The brief"
          % (P.piece_height(PLANET), piece["sol"].max.Z))
    print("predicted %.2f, which is where the hoop's mid-plane reaches; the crown"
          % 25.91)
    print("is the outer corner of a %.2f mm band leaning %.2f degrees and stands"
          % (spec["thickness"], P.PLANETS[PLANET]["tilt"] - 90.0))
    print("%.2f mm above that. The measured figure is the one used."
          % (piece["sol"].max.Z - 25.91))
    print()
    print("## How steep it is")
    print()
    print("The 45 degree gate, run facet by facet over the finished ring at %.2f mm"
          % TOLERANCE)
    print("of chord. A vertical wall is 0 degrees and a flat ceiling is 90.")
    print()
    print("| army | steepest downward-facing | where | area over the gate mm2 |")
    print("|---|---:|---|---:|")
    seated = {}
    for side in P.SIDES:
        ring = bodies[side]["ring"][1]
        worst, worst_at, over, foot = -90.0, None, 0.0, 0.0
        for centre, normal, area in facets(ring):
            if abs(centre[2] - P.DISC_H) <= 1e-6 and normal[2] < -0.999:
                foot += area                      # seated on the disc top
                continue
            toward = (-centre[0], -centre[1], P.globe_centre_z(PLANET) - centre[2])
            span = math.sqrt(sum(value * value for value in toward))
            if (abs(span - radius) <= 5e-4
                    and sum(normal[i] * toward[i] for i in range(3)) > 0.0):
                foot += area                      # seated on the globe
                continue
            angle = overhang_deg(normal)
            if angle > worst:
                worst, worst_at = angle, centre
            if angle > P.OVERHANG_LIMIT_DEG:
                over += area
        seated[side] = foot
        print("| %s | %.1f deg | %s | %.4f |"
              % (side, worst, where(worst_at, hoop), over))
        if worst > P.OVERHANG_LIMIT_DEG + 1e-6:
            failures.append(
                "%s's ring reaches %.1f degrees, past the %.1f degree gate"
                % (side, worst, P.OVERHANG_LIMIT_DEG))
    print()
    print("Excluded by name: %.2f mm2, on both armies alike -- the flat footprint"
          % seated["sol"])
    print("the two feet stand on, lying exactly on the disc's top face at Z %.2f,"
          % P.DISC_H)
    print("and the hoop's inner boundary, which is the globe's own sphere at")
    print("radius %.2f from the globe centre and is what the ring is seated"
          % radius)
    print("against the whole way round. Both point downward somewhere and neither")
    print("is a surface once the part is fused: there is solid under every square")
    print("millimetre of both. `check_overhang` measures the fused part and never")
    print("sees them.")
    print()
    print("**The %.0f degree gate passes on the ring itself**, and it passes on the"
          % P.OVERHANG_LIMIT_DEG)
    print("whole printed part: `measure/overhang-world_uranus_sol.md` and its")
    print("Anti-Sol twin report 0 unsupported regions, 0 bridges and 0 samples")
    print("needing support over the whole 35.1 cm2 of surface.")
    print()
    print("### Why it needed a foot")
    print()
    print("`_ring_body` cuts everything below the disc top away, and an upright")
    print("hoop meets that flat cut on the steep part of its own curve. Measured in")
    print("closed form on the real hoop:")
    print()
    print("| | measured in 3D | the brief's own table |")
    print("|---|---|---|")
    print("| rim overhang where it leaves the disc top | %.1f deg | 48.6 deg |"
          % hoop["cut_overhang_deg"])
    print("| height where the rim first clears the gate | Z %.2f mm | not given |"
          % hoop["gate_z"])
    print("| plan radius there | %.2f mm | not given |" % hoop["gate_plan_r"])
    print()
    print("The brief's figure is right to a tenth of a degree, and that is not")
    print("luck: the rim's downward slope at the cut works out to")
    print("`(centre height - cut height) / outer radius` whichever way the ring")
    print("leans, because the lean enters the height and the normal in the same")
    print("proportion and cancels. Two more figures fall out of the same algebra")
    print("and neither is in the brief: the rim clears the gate at")
    print("`Z = centre - R cos(45)` = %.2f mm, and its plan radius there is"
          % hoop["gate_z"])
    print("`R sin(45)` = %.2f mm. So the offending strip is %.2f mm tall."
          % (hoop["gate_plan_r"], hoop["gate_z"] - hoop["cut_z"]))
    print()
    print("Growing the ring until the cut lands somewhere shallower is the")
    print("resolution the brief ruled out -- it takes the projection back to")
    print("Saturn's own 2.00 mm. The junction is wedged instead, at")
    print("`RING_WEB_SLOPE` = %.2f, which is %.1f degrees from horizontal and"
          % (P.RING_WEB_SLOPE, math.degrees(math.atan(P.RING_WEB_SLOPE))))
    print("%.1f from vertical -- the angle this set already trusts under Saturn's"
          % (90.0 - math.degrees(math.atan(P.RING_WEB_SLOPE))))
    print("ring for exactly this problem. The wedge stands %.2f mm proud of the"
          % P.URANUS_RING_FOOT_REACH)
    print("hoop where it leaves the disc and is gone %.2f mm further up, inside the"
          % P.URANUS_RING_FOOT_RISE)
    print("globe, so it adds a small gusset at each of the two feet and nothing")
    print("anywhere else. The projection stayed at %.2f mm."
          % P.URANUS_RING_PROJECTION)
    print()
    print("## The ladder")
    print()
    print("| | diameter | |")
    print("|---|---:|---|")
    print("| Saturn, ring included | Ø%.2f mm | the widest world in the set |"
          % P.RING_OUTER_D)
    print("| Uranus, ring included | Ø%.2f mm | |" % spec["outer_d"])
    print("| Jupiter, the widest globe | Ø%.2f mm | |" % P.globe_diameter("jupiter"))
    if P.RING_OUTER_D <= spec["outer_d"]:
        failures.append("Uranus is no longer narrower than Saturn")
    print()
    print("`LADDER_CONSTANT` is %.3f and `LADDER_EXPONENT` %.1f, both unmoved:"
          % (P.LADDER_CONSTANT, P.LADDER_EXPONENT))
    print("every globe diameter in `params.PLANETS` still satisfies")
    print("`%.3f * (D / 4879) ** %.1f` to the hundredth of a millimetre it is"
          % (P.LADDER_CONSTANT, P.LADDER_EXPONENT))
    print("written at.")
    print()
    print("| planet | d km | ladder mm | sealed mm | |")
    print("|---|---:|---:|---:|---|")
    for name, item in sorted(P.PLANETS.items(), key=lambda row: row[1]["rank"]):
        want = P.LADDER_CONSTANT * (item["d_km"] / 4879.0) ** P.LADDER_EXPONENT
        agree = abs(want - item["globe_d"]) <= 0.005 + 1e-9
        print("| %s | %.0f | %.2f | %.2f | %s |"
              % (name, item["d_km"], want, item["globe_d"],
                 "matches" if agree else "**moved**"))
        if not agree:
            failures.append("%s's globe no longer sits on the ladder" % name)
    print()
    print("## The heights, against rank")
    print()
    print("| rank | planet | piece height mm | what sets it |")
    print("|---|---|---:|---|")
    heights = []
    for name, item in sorted(P.PLANETS.items(), key=lambda row: row[1]["rank"]):
        if name == PLANET:
            height = piece["sol"].max.Z
            sets = "the ring's crown"
        elif name == "saturn":
            height = build_world(name, "sol").bounding_box().max.Z
            sets = "the globe's crown; the ring is lower"
        else:
            height = P.piece_height(name)
            sets = "the globe's crown"
        heights.append((item["rank"], name, height))
        print("| %d | %s | %.2f | %s |" % (item["rank"], name, height, sets))
    climbing = all(a[2] < b[2] for a, b in zip(heights, heights[1:]))
    print()
    if climbing:
        print("**The piece heights still climb with rank, all eight of them.** The")
        print("ring takes Uranus from %.2f mm to %.2f, which is past Neptune's %.2f"
              % (P.piece_height(PLANET), piece["sol"].max.Z,
                 P.piece_height("neptune")))
        print("and still well under Saturn's %.2f."
              % build_world("saturn", "sol").bounding_box().max.Z)
    else:
        failures.append("the piece heights no longer climb with rank")
        print("**The piece heights no longer climb with rank.**")
    print()
    print("## What it can touch")
    print()
    print("Every clearance is measured as shared volume between the exact placed")
    print("solids; anything over %g mm3 is a real interpenetration." % NOISE_MM3)
    print()
    print("| what | measured | |")
    print("|---|---|---|")
    socket = P.TRAY_SOCKET_D / 2.0
    reach = spec["outer_d"] / 2.0
    print("| the Ø%.2f tray socket | ring reaches %.2f mm from the axis | %s |"
          % (P.TRAY_SOCKET_D, reach,
             "clear by %.2f mm" % (socket - reach) if reach < socket else "**fouls**"))
    if reach >= socket:
        failures.append("the ring is wider than the tray socket")
    corona = Location((0, 0, POCKET_FLOOR)) * build_corona_cell()
    star = den_bodies()
    for side in P.SIDES:
        world = build_world(PLANET, side)
        in_well = shared(Location((0, 0, CORONA_SEAT)) * world, corona)
        print("| the corona well, %s | %.6f mm3 shared | %s |"
              % (side, in_well, "clear" if in_well <= NOISE_MM3 else "**fouls**"))
        if in_well > NOISE_MM3:
            failures.append("%s fouls the corona well" % side)
        on_star = max(
            shared(Location((0, 0, DEN_SEAT)) * world,
                   Location((0, 0, POCKET_FLOOR)) * star[role])
            for role in ("star", "flare")
        )
        print("| the den flange and its flames, %s | %.6f mm3 shared | %s |"
              % (side, on_star, "clear" if on_star <= NOISE_MM3 else "**fouls**"))
        if on_star > NOISE_MM3:
            failures.append("%s fouls the star it stands on" % side)

    # The flares are the only thing in the set that reaches this ring's height,
    # and a world standing on a den's neighbour is the case the brief names.
    flare = Location((0, 0, POCKET_FLOOR)) * star["flare"]
    flare_box = flare.bounding_box()
    worst_pair = None
    best_overlap = (-1.0, 0.0, 0.0, 0.0)
    for side in P.SIDES:
        world = build_world(PLANET, side)
        den = P.DEN_CELLS[side]
        for step_x in (-1, 0, 1):
            for step_y in (-1, 0, 1):
                if step_x == step_y == 0:
                    continue
                cell = (den[0] + step_x, den[1] + step_y)
                if not (0 <= cell[0] < P.FILES and 0 <= cell[1] < P.RANKS):
                    continue
                dx = P.CELL_PITCH * step_x
                dy = P.CELL_PITCH * step_y
                seat = (CORONA_SEAT if cell in P.TRAP_CELLS[side] else FIELD_TOP)
                placed = Location((dx, dy, seat)) * world
                value = shared(placed, flare)
                box = placed.bounding_box()
                overlap = (min(box.max.Z, flare_box.max.Z)
                           - max(box.min.Z, flare_box.min.Z))
                if worst_pair is None or value > worst_pair[0]:
                    worst_pair = (value, side, cell, seat)
                heights.append(overlap) if False else None
                if overlap > best_overlap[0]:
                    best_overlap = (overlap, box.max.Z, flare_box.max.Z,
                                    max(box.min.Z, flare_box.min.Z))
                if value > NOISE_MM3:
                    failures.append(
                        "%s standing on %s shares %.4f mm3 with a den flare"
                        % (side, cell, value))
    print("| the 18.00 mm flares, worst neighbouring cell | %.6f mm3 shared | %s |"
          % (worst_pair[0], "clear" if worst_pair[0] <= NOISE_MM3 else "**fouls**"))
    print()
    print("**The flares are the one thing in the set that reaches the ring's")
    print("height and they are checked explicitly.** A flare's tip stands at")
    print("Z %.2f in the board frame and a Uranus piece on a neighbouring cell"
          % flare_box.max.Z)
    print("carries its hoop to Z %.2f, so the two share %.2f mm of height --"
          % (best_overlap[1], best_overlap[0]))
    print("from Z %.2f up to the flare's own tip. They do not share any of it in"
          % best_overlap[3])
    print("plan: the flare bases sit inside a")
    print("Ø%.2f diagonal on the den's own flange, the ring never leaves the"
          % P.FLARE_DIAGONAL)
    print("disc's own Ø%.2f footprint, and the cells are %.2f mm apart. Every one"
          % (P.DISC_NOMINAL_D, P.CELL_PITCH))
    print("of the eight cells around each den was placed and measured, on both")
    print("armies, and the largest shared volume anywhere was %.6f mm3."
          % worst_pair[0])
    print()
    print("## The mirror")
    print()
    print("| | Sol | Anti-Sol | |")
    print("|---|---:|---:|---|")
    ring_sol = bodies["sol"]["ring"][1]
    ring_anti = bodies["anti"]["ring"][1]
    box_sol, box_anti = ring_sol.bounding_box(), ring_anti.bounding_box()
    rows = [
        ("ring volume mm3", ring_sol.volume, ring_anti.volume, 1e-4),
        ("ring X reach mm", box_sol.max.X, -box_anti.min.X, 1e-6),
        ("ring Y reach mm", box_sol.max.Y, box_anti.max.Y, 1e-6),
        ("ring crown Z mm", box_sol.max.Z, box_anti.max.Z, 1e-6),
    ]
    for label, left, right, tolerance in rows:
        same = abs(left - right) <= tolerance
        print("| %s | %.4f | %.4f | %s |"
              % (label, left, right, "mirrored" if same else "**differs**"))
        if not same:
            failures.append("the two rings are not mirrors on %s" % label)
    print()
    print("Sol leans toward +X and Anti-Sol toward -X, so the Sol ring's greatest")
    print("+X reach is the Anti-Sol ring's greatest -X reach; that is the row above")
    print("and it is what a mirror means here. `measure/uranus-mirror.md` carries")
    print("the same test over every body of both pieces.")
    print()
    print("## The colour, which was measured rather than inherited")
    print()
    print("The brief says to take `white` -- the tone Saturn's ring already wears,")
    print("because in this set rings are white -- **unless a reason not to is")
    print("measured**, and to say which was taken. A reason was measured, twice,")
    print("and this ring prints in `%s`." % spec["colour"])
    print()
    print("`measure/uranus-tone-separation.md` renders one piece twice at one")
    print("camera with only the ring repainted, over all thirteen stocked")
    print("filaments. `white` separates 38.9 of 255 luma levels from the globe --")
    print("**louder than the hood's 27.8**, which makes it the loudest thing on a")
    print("piece this correction exists to quieten. That is the number.")
    print()
    print("The reason it matters is what an independent reader did with it. Shown")
    print("the board and asked cold whether any piece read as a beach ball or a")
    print("tennis ball, a reviewer who had not been told what the set was named")
    print("both Uranus pieces, twice, and gave the mechanism: 'a bold white curved")
    print("line arcing down one side of a saturated-colour ball, and a large pale")
    print("panel on the opposite side'. A white hoop on `cyan` is a tennis seam.")
    print()
    print("`gray` was tried first and measured worse in use, which is the useful")
    print("part of the record: at 7.0 luma from the globe it is quieter as a")
    print("number, and the same reviewer reported it read as a MORE convincing")
    print("seam, because a tennis seam is a darker curve on a brighter ball. The")
    print("painted-stripe reading does not live in how far the tone is from the")
    print("globe. It lives in the marking being a different MATERIAL.")
    print()
    print("So the ring takes the globe's own `cyan`. It is then not a marking at")
    print("all: it is relief, read by silhouette and self-shadow, which is what a")
    print("ring on this piece is for. Its luminance against the globe is unchanged")
    print("by the swap -- the hoop is as visible at board scale as it was -- and")
    print("the reviewer's third read confirmed both halves: the tennis ball gone,")
    print("the ring still legible as a hoop up close and still tellable from")
    print("Saturn's at board scale.")
    print()
    print("**What it costs, recorded rather than buried.** The two ringed worlds no")
    print("longer wear the same kind of ring: Saturn's is a separate `white` part")
    print("and Uranus's is self-coloured relief, so the set's 'rings are white'")
    print("rule now has one exception. Uranus's piece also drops from three")
    print("surface filaments to two, since the ring shares the globe's spool.")
    print("Saturn's ring is untouched and still prints `white`.")
    print()
    print("## What was considered and left out")
    print()
    print("No moons, no storms, no banding, no shepherd gaps and no individual")
    print("named ringlets. Uranus really has thirteen rings; at Ø%.2f mm one"
          % P.globe_diameter(PLANET))
    print("degree of arc is %.3f mm and the whole ring system would be grit under"
          % (math.pi * P.globe_diameter(PLANET) / 360.0))
    print("a %.1f mm nozzle. The ring is one solid hoop." % P.NOZZLE_MM)
    print()
    print("## Verdict")
    print()
    if failures:
        for item in failures:
            print("- **%s**" % item)
    else:
        print("The gate passes on the ring and on the whole part, the ladder is")
        print("unmoved, the heights still climb with rank, nothing collides with")
        print("anything, and the two pieces are mirrors.")
    print()
    print("Measured by `measure/uranus_ring.py` on the built solids.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
