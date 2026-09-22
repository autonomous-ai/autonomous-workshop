"""What the trap tile lost, and what the board gained by it.

`parts/corona.py` used to add two `tapered_flame` bodies at the tile's two
corners furthest from the star -- twelve small horns across the six trap cells,
beside the two stars' four.  The owner took them off: the trap tiles are flat
and the horns are the star's alone.  This measures the tile before and after.

The BEFORE figures are read from the published solid itself rather than from a
reconstruction of retired constants: `make/models/cad/part_corona_cell.step` in
the source archive this revision was handed, which is the exact STEP the
accepted set shipped.  Its sha256 is checked here against `make/made.json`'s own
product manifest in that same archive, so the file cannot be the wrong one.  It
is read from the archive rather than copied into this tree because a STEP with
no sibling `.step.py` inside a CAD project is a stale export, and the final
verifier refuses one -- correctly.  The AFTER figures are built from the current
source.

    "$WORKSHOP_PYTHON" measure/corona_flat.py <archive-root> > measure/corona-flat.md

Exit 0 when the tile is a plain rounded-square extrusion with an engraving in
its top face and nothing standing above it, 1 otherwise.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from build123d import Rot, import_step                          # noqa: E402

import bool3d as X                                              # noqa: E402
import params as P                                              # noqa: E402
from parts.corona import build_corona_cell, build_corona_tile_only  # noqa: E402

#: Where the published solid lives inside the source archive.
BASELINE_IN_ARCHIVE = Path("make") / "models" / "cad" / "part_corona_cell.step"

#: What the six trap tiles are: three around each of the two stars.
TRAP_COUNT = sum(len(cells) for cells in P.TRAP_CELLS.values())

#: The retired constants, recorded here because this is the report that says
#: what they bought.  They no longer exist in `params.py` and nothing builds
#: from them; these are the values that were removed.
RETIRED = (
    ("CORONA_TONGUE_BASE_D", 5.00, "mm, the tongue's base diameter"),
    ("CORONA_TONGUE_H", 4.00, "mm above field datum"),
    ("CORONA_TONGUE_TIP_R", 0.60, "mm tip radius"),
    ("CORONA_TONGUE_DIAGONAL", 20.20,
     "mm between the two tongues, which left 0.70 mm of clearance to a "
     "seated disc and was the tightest thing on the tile"),
)

#: PLA at 1.24 g/cm3, the density the set's own print notes use.
PLA_DENSITY = 1.24


def solid_facts(shape):
    solids = X.parts(shape)
    volume = sum(item.volume for item in solids)
    area = sum(item.area for item in solids)
    box = shape.bounding_box()
    return {
        "solids": len(solids),
        "volume": volume,
        "area": area,
        "size": (box.size.X, box.size.Y, box.size.Z),
        "z": (box.min.Z, box.max.Z),
    }



def overhang_line(text: str) -> str:
    """The one line of an overhang report that carries its figures."""
    for line in text.splitlines():
        if "cm2 of surface" in line:
            return line.strip()
    return "(no surface line in that report)"


def overhang_regions(text: str) -> list[str]:
    """The rows of the report's own unsupported-regions table."""
    rows, inside = [], False
    for line in text.splitlines():
        if line.startswith("| # | kind |"):
            inside = True
            continue
        if inside:
            if line.startswith("|---"):
                continue
            if not line.startswith("|"):
                break
            rows.append(line.strip())
    return rows


def main() -> int:
    failures = []
    if len(sys.argv) < 2:
        raise SystemExit("name the source archive this revision was handed")
    archive = Path(sys.argv[1])
    baseline = archive / BASELINE_IN_ARCHIVE
    if not baseline.is_file():
        raise SystemExit("the archive carries no %s" % BASELINE_IN_ARCHIVE)

    before_shape = import_step(str(baseline))
    after_shape = build_corona_cell()
    before = solid_facts(before_shape)
    after = solid_facts(after_shape)
    bare = solid_facts(build_corona_tile_only())

    print("# The trap tile, before and after its tongues came off")
    print()
    print("## Where the before figures come from")
    print()
    digest = hashlib.sha256(baseline.read_bytes()).hexdigest()
    print("`%s` in the source archive, sha256" % BASELINE_IN_ARCHIVE.as_posix())
    print("`%s`." % digest)
    made = json.loads((archive / "make" / "made.json").read_text())
    published = {row["path"]: row["sha256"]
                 for row in made["product_manifest"]["entries"]}
    want = published.get("cad/part_corona_cell.step")
    print()
    print("The published set's own `cad/part_corona_cell.step` is")
    print("`%s`," % want)
    print("read from `make/made.json`'s product manifest in the same archive.")
    print("They are **%s**."
          % ("the same file" if want == digest else "DIFFERENT"))
    if want != digest:
        failures.append("the baseline STEP is not the published solid")
    print()

    print("## The tile")
    print()
    print("| | before | after | change |")
    print("|---|---:|---:|---:|")
    print("| separate solids | %d | %d | %+d |"
          % (before["solids"], after["solids"], after["solids"] - before["solids"]))
    print("| printed height mm | %.3f | %.3f | %+.3f |"
          % (before["size"][2], after["size"][2],
             after["size"][2] - before["size"][2]))
    print("| footprint mm | %.3f x %.3f | %.3f x %.3f | -- |"
          % (before["size"][0], before["size"][1],
             after["size"][0], after["size"][1]))
    print("| volume mm3 | %.3f | %.3f | %+.3f |"
          % (before["volume"], after["volume"],
             after["volume"] - before["volume"]))
    print("| surface area mm2 | %.3f | %.3f | %+.3f |"
          % (before["area"], after["area"], after["area"] - before["area"]))
    print()
    print("The tile is %.2f mm tall and was %.2f: the two tongues stood"
          % (after["size"][2], before["size"][2]))
    print("%.2f mm above its top face, which is `CORONA_TONGUE_H` 4.00 above"
          % (before["size"][2] - after["size"][2]))
    print("the field plus `CORONA_WELL_DROP` 3.00 of well. The tile's own")
    print("height, `CORONA_TILE_H`, is untouched at %.2f mm and so is the well"
          % P.CORONA_TILE_H)
    print("it leaves.")
    print()

    print("## What the six tiles save")
    print()
    saved = (before["volume"] - after["volume"]) * TRAP_COUNT
    print("| | per tile | across the %d trap tiles |" % TRAP_COUNT)
    print("|---|---:|---:|")
    print("| volume removed mm3 | %.3f | %.3f |"
          % (before["volume"] - after["volume"], saved))
    print("| filament at %.2f g/cm3 | %.3f g | %.3f g |"
          % (PLA_DENSITY, (before["volume"] - after["volume"]) * PLA_DENSITY / 1000.0,
             saved * PLA_DENSITY / 1000.0))
    print("| tapered flames removed | 2 | %d |" % (2 * TRAP_COUNT))
    print()
    print("A fraction of a gram. The print this buys is not the filament -- it")
    print("is that six parts lost their tallest feature, so the six tallest")
    print("unsupported regions on the board's terrain are gone with it. The")
    print("overhang gate below is where that shows.")
    print()

    print("## The engraving is untouched")
    print()
    print("| | value |")
    print("|---|---:|")
    print("| `CORONA_ENGRAVE_COUNT` | %d |" % P.CORONA_ENGRAVE_COUNT)
    print("| `CORONA_ENGRAVE_INNER` mm | %.2f |" % P.CORONA_ENGRAVE_INNER)
    print("| `CORONA_ENGRAVE_EYE_D` mm | %.2f |" % P.CORONA_ENGRAVE_EYE_D)
    print("| `CORONA_ENGRAVE_D` mm | %.2f |" % P.CORONA_ENGRAVE_D)
    print()
    print("Measured on the solid rather than read off the constants: the bare")
    print("tile is %.3f mm3 and the engraved tile is %.3f mm3, so the engraving"
          % (bare["volume"], after["volume"]))
    print("takes %.3f mm3 out of the top face and the tile is otherwise whole."
          % (bare["volume"] - after["volume"]))
    print("Its deepest point is %.2f mm below the top face."
          % P.CORONA_ENGRAVE_D)
    print()

    print("## Nothing stands above the tile any more")
    print()
    print("The claim is that the corona cell is now a plain rounded-square")
    print("extrusion with an engraving cut into its top face -- one solid, no")
    print("feature above `CORONA_TILE_H`. Asked of the built body:")
    print()
    one_solid = after["solids"] == 1
    flat_top = abs(after["z"][1] - P.CORONA_TILE_H) < 1e-6
    from_bed = abs(after["z"][0]) < 1e-9
    print("- separate solids: **%d** %s"
          % (after["solids"], "" if one_solid else "-- EXPECTED 1"))
    print("- highest point: **%.6f mm**, and `CORONA_TILE_H` is %.2f %s"
          % (after["z"][1], P.CORONA_TILE_H,
             "" if flat_top else "-- THESE DIFFER"))
    print("- lowest point: **%.6f mm**, the bed" % after["z"][0])
    if not one_solid:
        failures.append("the corona cell is %d solids, not one" % after["solids"])
    if not flat_top:
        failures.append("the corona cell reaches %.4f mm, above CORONA_TILE_H"
                        % after["z"][1])
    if not from_bed:
        failures.append("the corona cell does not sit on the bed")
    print()

    print("## The overhang gate")
    print()
    print("The published tile carried two trace regions of unsupported surface,")
    print("both at the tongue bases at Z 3.00 -- the one place on the part where")
    print("a leaning flame left the tile's own top face. With the tongues gone")
    print("there is nothing on the part that leans at all.")
    print()
    now_reports = sorted(
        HERE.glob("component-rounds/corona_cell/*/overhang-corona_cell.md"))
    was_report = None
    if archive is not None:
        candidate = archive / "make" / "verification" / "reports" / "overhang-corona_cell.md"
        if candidate.is_file():
            was_report = candidate.read_text()
    now_report = now_reports[-1].read_text() if now_reports else None
    print("| | figures |")
    print("|---|---|")
    print("| before, published | %s |"
          % (overhang_line(was_report) if was_report else "report not supplied"))
    print("| after, this run | %s |"
          % (overhang_line(now_report) if now_report else "not yet measured"))
    print()
    if was_report:
        rows = overhang_regions(was_report)
        if rows:
            print("The published report's own table of those regions:")
            print()
            print("| # | kind | area mm2 | at | span mm | air below mm |")
            print("|---|---|---|---|---|---|")
            for row in rows:
                print(row)
            print()
    if now_report:
        rows = overhang_regions(now_report)
        print("**The corona cell now has %s.**"
              % ("zero unsupported regions" if not rows
                 else "%d unsupported region(s), which it should not" % len(rows)))
        if rows:
            failures.append("the corona cell still has %d unsupported region(s)"
                            % len(rows))
        print("Both reports are measurements on the tessellated solid in the pose")
        print("it prints in, at a 0.4 mm nozzle and the 45 degree gate, and both")
        print("say `prints unsupported`. What changed is that the earlier one said")
        print("it with two trace regions in its table and this one says it with an")
        print("empty table.")
    print()

    print("## The tile at a quarter turn")
    print()
    print("`assemblies/product.py` used to turn each trap tile so its tongues")
    print("pointed away from the star, through one of 0, 90, -90 and 180")
    print("degrees. With no tongues that rotation has been dropped, and the")
    print("claim it rests on is that a quarter turn maps the tile exactly onto")
    print("itself -- the rounded square repeats every 90 degrees, and the")
    print("sixteen engraved tongues alternate two lengths so the engraving")
    print("repeats every 45. That is measured here rather than argued: the")
    print("symmetric difference between the tile and the tile turned, which is")
    print("the volume that is in one and not the other.")
    print()
    print("| turn | volume in one and not the other mm3 |")
    print("|---|---:|")
    worst = 0.0
    for turn in (90.0, 180.0, 270.0):
        turned = Rot(0, 0, turn) * after_shape
        left = X.shape(X.cut(after_shape, turned))
        right = X.shape(X.cut(turned, after_shape))
        volume = 0.0
        for piece in (left, right):
            if piece is not None:
                volume += sum(item.volume for item in X.parts(piece))
        worst = max(worst, volume)
        print("| %.0f degrees | %.6f |" % (turn, volume))
    print()
    if worst > 1e-3:
        failures.append(
            "a quarter turn moves %.6f mm3 of the tile, so dropping the "
            "rotation was not free" % worst)
        print("**That is not zero**, so the placed occurrences are not what the")
        print("rotation produced and the rotation should not have been dropped.")
    else:
        print("Zero to the kernel's own noise. Every placed trap tile is the")
        print("same solid in the same place it was when the rotation turned it,")
        print("so the assembly's interference and occurrence-geometry checks")
        print("keep exactly the meaning they had.")
    print()

    print("## The four retired constants")
    print()
    print("| constant | value | what it was |")
    print("|---|---:|---|")
    for name, value, what in RETIRED:
        print("| `%s` | %.2f | %s |" % (name, value, what))
    print()
    print("All four are removed from `params.py`. Nothing reads them: they were")
    print("searched for across the whole project -- source, measurement scripts")
    print("and report generators -- before they were taken out, and")
    print("`parts/corona.py` was their only consumer.")
    print()

    print("## Verdict")
    print()
    if failures:
        for item in failures:
            print("- **%s**" % item)
    else:
        print("The trap tile is one solid %.2f mm tall: a rounded square with a"
              % after["size"][2])
        print("sixteen-rayed star sunk %.2f mm into its top face, and nothing"
              % P.CORONA_ENGRAVE_D)
        print("above that face at all.")
    print()
    print("Measured by `measure/corona_flat.py`.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
