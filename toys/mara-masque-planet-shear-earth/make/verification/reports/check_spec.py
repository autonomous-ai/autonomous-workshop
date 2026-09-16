"""Spec/source reconciliation: the approved spec must describe the live source.

Fails when a ledger value in `planet_shear_earth_spec.md` no longer matches the
literal in `planet_shear_lib.py`, when the printed-part count or the declared
occurrence set drifts, or when a defining feature stops being built the way the
spec says it is built.
"""
import inspect
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

import planet_shear_atlas as atlas  # noqa: E402
import planet_shear_lib as lib  # noqa: E402

SPEC = PROJECT / "planet_shear_earth_spec.md"
TOLERANCE = 1e-9

LEDGER_ROW = re.compile(r"^\|\s*`([A-Z_]+)`\s*\|\s*`(-?[0-9.]+)`\s*\|")

EXPECTED_ENTRIES = {"part_piece.step.py", "planet_shear_earth.step.py"}
EXPECTED_OCCURRENCES = {
    "disc_base", "ocean_seat", "ocean_globe",
    "land_americas", "land_africa", "land_eurasia", "land_australia",
    "dryland_sahara", "dryland_kalahari", "dryland_inner_asia",
    "dryland_american_southwest", "dryland_outback", "polar_ice",
}

# spec row -> (builder, construction family the spec names for it)
CONSTRUCTION = {
    "disc base": ("fused_body", "Cylinder"),
    "top round": ("fused_body", "fillet"),
    "ocean seat": ("ocean_seat", "Cone"),
    "ocean globe": ("globe_sphere", "Sphere"),
    "relief shell": ("relief_shell", "Sphere"),
    "numeral stroke": ("_stroke_blank", "loft"),
}


def fail(rows, message):
    rows.append(f"FAIL {message}")


def main():
    rows, bad = [], 0
    if not SPEC.exists():
        print("FAIL spec missing:", SPEC)
        return 2

    text = SPEC.read_text()

    # 1. every ledger value still matches the source literal
    claims = 0
    for line in text.splitlines():
        match = LEDGER_ROW.match(line.strip())
        if not match:
            continue
        name, written = match.group(1), float(match.group(2))
        actual = getattr(lib, name, None)
        claims += 1
        if actual is None:
            fail(rows, f"spec ledger names {name}, which the source does not define")
            bad += 1
        elif abs(float(actual) - written) > TOLERANCE:
            fail(rows, f"{name}: spec says {written}, source builds {actual}")
            bad += 1
    if claims < 15:
        fail(rows, f"spec ledger carries only {claims} rows; expected the full parameter block")
        bad += 1
    else:
        rows.append(f"ok   {claims} ledger value(s) match the source")

    # 2. printed part count and entry set
    entries = {p.name for p in PROJECT.glob("*.step.py")}
    if entries != EXPECTED_ENTRIES:
        fail(rows, f"entries {sorted(entries)} != spec's {sorted(EXPECTED_ENTRIES)}")
        bad += 1
    else:
        rows.append("ok   one printed entry and one combined entry, as section 6a says")

    printable = [name for name in entries
                 if "PRINTABLE = True" in (PROJECT / name).read_text()]
    if printable != ["part_piece.step.py"]:
        fail(rows, f"spec section 6a declares one printed part; source marks {printable}")
        bad += 1
    else:
        rows.append("ok   part_piece is the only print target")

    # 3. the occurrence set the combined entry seals
    combined = (PROJECT / "planet_shear_earth.step.py").read_text()
    # The entry names three bodies directly and takes the rest from the atlas'
    # own landmass and dryland groups, so a group renamed there is caught here.
    declared = set(re.findall(r'_add\(asm, lib\.\w+\(\), "([a-z_0-9]+)"', combined))
    declared |= {name for name, _outlines in atlas.LANDMASS_GROUPS}
    declared |= {name for name, _outlines in atlas.DRYLAND_GROUPS}
    declared.add("polar_ice")
    if declared != EXPECTED_OCCURRENCES:
        fail(rows, f"occurrence stems {sorted(declared)} != spec's {sorted(EXPECTED_OCCURRENCES)}")
        bad += 1
    else:
        rows.append("ok   thirteen colour groups, one per component in the ledger")

    # 4. each defining feature is still built by the operation the spec names
    for label, (builder, family) in CONSTRUCTION.items():
        source = inspect.getsource(getattr(lib, builder))
        if family not in source:
            fail(rows, f"{label}: {builder}() no longer uses {family}")
            bad += 1
        else:
            rows.append(f"ok   {label} is still a {family} in {builder}()")

    # 5. the Wish's hard dimensions, restated where CAD repair could have moved them
    for name, value in (("BASE_DIAMETER", 34.0), ("BASE_HEIGHT", 5.0),
                        ("GLOBE_DIAMETER", 21.08), ("RELIEF", 1.0), ("RANK_DIGIT", 4)):
        if abs(float(getattr(lib, name)) - value) > TOLERANCE:
            fail(rows, f"{name} moved off the Wish value {value}")
            bad += 1
    if not bad:
        rows.append("ok   the five Wish-fixed values are untouched")

    print("\n".join(rows))
    print(f"RESULT: {len(rows)} check(s), {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
