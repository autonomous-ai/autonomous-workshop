"""The host's check of a powered toy's Bought Parts in its model (ADR 0095
amendment of 2026-11-01).

Final verification runs the run-local ``make-round/scripts/bought_model.py
--final`` for a schema 10 circuit that is no kit, when the Wish's sealed
catalogue snapshot records a ``model`` for one of its parts. Before Make is
accepted the host checks, on the exact sealed bytes and without rebuilding
any geometry (ADR 0061), that

- final verification passed ``bought_model.py``;
- the body list ``measure/bought-bodies.json`` draws one body per carried
  part instance of the sealed circuit (none for the buyer's own supply), the
  board exactly when the contract names a ``pcba`` and exactly at its
  ``bounds_mm``, and every body's STEP is sealed with the hash the list
  records;
- the assembly-package carries exactly those bodies as its ``bought_``
  occurrences, each in the reserved not-printed magenta (ADR 0092 Q29);
- the three electrical pictures and the Electrical Assembly text are the
  ones ``measure/electrical/electrical.json`` names; and
- the product README carries that text verbatim, so what it says about who
  assembles and solders follows the contract, not the Manager's prose; and
- when ``electrical.json`` names a printed-only primary (ADR 0095 amendment,
  2026-11-07), that STEP is the sealed scene ``assembled.step`` without its
  bought bodies: the same printed leaves, each with the same solids by volume
  and surface area, no ``bought_`` leaf, and exactly the drawn bodies
  removed. The receipt seals its hash, and Release ships it as Factory's
  primary in place of the scene.

Nothing here judges a picture. A run sealed before catalogue models existed
records none and keeps what it sealed.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from workshop.errors import ContractError
from workshop.make.assembly_package import (
    ASSEMBLY_PACKAGE_PATH,
    BOUGHT_OCCURRENCE_PREFIX,
    read_assembly_package,
)
from workshop.make.power import PIPELINE_PATH, has_electrical
from workshop.wish.catalogues import BOUGHT_PART_HEX
from workshop.wish.electrical import pcba_bounds, pcba_parts

BODIES_PATH = "measure/bought-bodies.json"
ELECTRICAL_PATH = "measure/electrical/electrical.json"
ELECTRICAL_DIRECTORY = "measure/electrical"
PICTURES = ("exploded.png", "cutaway.png", "wiring.png")
ASSEMBLY_TEXT = "assembly.md"
BOUGHT_GATE = "bought_model.py"
BODIES_KIND = "bought-bodies"
ELECTRICAL_KIND = "electrical-pictures"
REPORT_SCHEMA = 1
BOARD_ID = "pcba"
README_PATH = "README.md"
PRINTED_PATH = "measure/electrical/printed.step"
PRINTED_FIELDS = {"step", "sha256", "scene", "scene_sha256", "removed"}
SCENE_PATH = "assembled.step"
# Relative tolerance on a solid's volume and area: a STEP round trip keeps
# both to about 1e-9, and another solid differs by far more.
_TOLERANCE = 1e-6


def _is_bought(name: str) -> bool:
    return name == "bought" or name.startswith(BOUGHT_OCCURRENCE_PREFIX)


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= max(1e-6, _TOLERANCE * max(abs(a), abs(b)))


def verify_printed_primary(scene: bytes, printed: bytes, removed) -> dict[str, Any]:
    """Refuse unless ``printed`` is ``scene`` without exactly its bought
    bodies: the same printed leaves by name, each with the same solids by
    volume and surface area, and no bought leaf. ``removed`` is the list of
    bought leaves the writer says it took out."""

    from workshop.release.printed_primary import scene_bodies

    scene_bodies_ = scene_bodies(scene)
    printed_bodies = scene_bodies(printed)
    bought = sorted(body.name for body in scene_bodies_ if _is_bought(body.name))
    if not isinstance(removed, list) or sorted(removed) != bought:
        raise ContractError(
            "the printed-only primary records removing %s, but the scene's bought bodies are %s"
            % (", ".join(sorted(map(str, removed or [])))[:200] or "none", ", ".join(bought)[:200] or "none")
        )
    left = sorted(body.name for body in printed_bodies if _is_bought(body.name))
    if left:
        raise ContractError("the printed-only primary still holds bought bodies: %s" % ", ".join(left[:6]))
    expected = sorted(
        ((body.name, body.solids, body.total) for body in scene_bodies_ if not _is_bought(body.name)),
        key=lambda item: (item[0], item[1], item[2]),
    )
    found = sorted(
        ((body.name, body.solids, body.total) for body in printed_bodies),
        key=lambda item: (item[0], item[1], item[2]),
    )
    if not expected:
        raise ContractError("the scene holds no printed body")
    if [item[0] for item in found] != [item[0] for item in expected]:
        missing = sorted((Counter(i[0] for i in expected) - Counter(i[0] for i in found)).elements())
        extra = sorted((Counter(i[0] for i in found) - Counter(i[0] for i in expected)).elements())
        raise ContractError(
            "the printed-only primary does not hold the scene's printed bodies: missing %s; extra %s"
            % (", ".join(missing[:6]) or "none", ", ".join(extra[:6]) or "none")
        )
    for (name, solids, total), (_name, want_solids, want_total) in zip(found, expected):
        if (
            len(solids) != len(want_solids)
            or not all(_close(a[0], b[0]) and _close(a[1], b[1]) for a, b in zip(solids, want_solids))
            or not (_close(total[0], want_total[0]) and _close(total[1], want_total[1]))
        ):
            raise ContractError(
                "the printed-only primary's %s is not the scene's: its solids differ in volume or area"
                % name
            )
    return {"printed_bodies": len(found), "removed_bodies": len(bought)}


def draws_bought_parts(contract: Any, catalogue: Any) -> bool:
    """Whether this run must model its Bought Parts: a schema 10 circuit
    that is no kit, whose sealed catalogue snapshot records a model for one
    of its parts. ``catalogue`` is the Wish's sealed ``kit_catalogue``."""

    if not has_electrical(contract) or contract.get("assembly_tree") is not None:
        return False
    entries = catalogue.get("bought_parts") if isinstance(catalogue, Mapping) else None
    if not isinstance(entries, Mapping):
        return False
    return any(
        isinstance((entries.get(item.get("bought")) or {}).get("model"), Mapping)
        for item in contract["electrical"].get("parts") or ()
        if isinstance(item, Mapping)
    )


def expected_bodies(electrical: Mapping[str, Any], entries: Mapping[str, Any]) -> list[str]:
    """Every body name the sealed circuit needs, in contract order: one per
    carried part instance and the board when the contract names one. Wires
    are drawn as routes, which are optional. ``entries`` is the sealed
    snapshot's Bought Parts."""

    names = []
    for item in electrical["parts"]:
        if item.get("external") is True or "bought" not in item:
            continue
        entry = entries.get(item["bought"]) or {}
        model = entry.get("model") if isinstance(entry.get("model"), Mapping) else {}
        if model.get("form", "wire" if entry.get("category") == "wire" else None) == "wire":
            continue
        count = int(item.get("count", 1))
        base = "bought_%s" % item["id"].replace("-", "_")
        names += [base] if count == 1 else ["%s_%d" % (base, n) for n in range(1, count + 1)]
    if pcba_parts(electrical):
        names.append("bought_%s" % BOARD_ID)
    return names


def verify_made_bought(
    run_root: Path,
    made: Any,
    contract: Mapping[str, Any] | None,
    catalogue: Any,
) -> dict[str, Any] | None:
    """The accepted Bought Part model's account, or None when the run draws
    none. Raises ContractError naming what is wrong."""

    if not draws_bought_parts(contract, catalogue):
        return None
    electrical = contract["electrical"]
    product_root = Path(run_root).joinpath(*PurePosixPath(made.product_root).parts)
    entries = {entry.path: entry for entry in made.product_manifest.entries}
    prefix = PurePosixPath(made.cad_project_path)

    def sealed(path: str, missing: str) -> bytes:
        entry = entries.get(path)
        if entry is None:
            raise ContractError(missing)
        data = product_root.joinpath(*PurePosixPath(path).parts).read_bytes()
        if len(data) != entry.bytes or hashlib.sha256(data).hexdigest() != entry.sha256:
            raise ContractError("the Made file %s differs from the Made manifest" % path)
        return data

    def cad(relative: str) -> bytes:
        return sealed((prefix / relative).as_posix(),
                      "the Made CAD project lacks %s: the sealed circuit's Bought Parts are drawn "
                      "into the model (ADR 0095, 2026-11-01)" % relative)

    def document(relative: str, kind: str) -> dict:
        try:
            value = json.loads(cad(relative).decode("utf-8"))
        except (UnicodeError, ValueError) as exc:
            raise ContractError("%s is not JSON" % relative) from exc
        if not isinstance(value, dict) or value.get("kind") != kind or value.get("schema_version") != REPORT_SCHEMA:
            raise ContractError("%s is not a %s report" % (relative, kind))
        return value

    # Read with the release's own reader of the record; imported here, as
    # Release depends on Make.
    from workshop.release.direct_publish import parse_pipeline_record

    try:
        rows = parse_pipeline_record(cad(PIPELINE_PATH).decode("utf-8"))
    except UnicodeError as exc:
        raise ContractError("%s is not text" % PIPELINE_PATH) from exc
    gate = [row for row in rows if row["gate"] == BOUGHT_GATE and row["status"] != "note"]
    if not gate or any(row["result"] != "pass" for row in gate):
        raise ContractError("final verification did not pass %s on the Bought Part model" % BOUGHT_GATE)

    bodies_raw = cad(BODIES_PATH)
    bodies = document(BODIES_PATH, BODIES_KIND)
    listed = [item for item in (bodies.get("bodies") or []) if isinstance(item, Mapping)]
    routes = [item for item in (bodies.get("routes") or []) if isinstance(item, Mapping)]
    names = [item.get("name") for item in listed]
    expected = expected_bodies(electrical, catalogue["bought_parts"])
    if Counter(names) != Counter(expected):
        missing = sorted((Counter(expected) - Counter(names)).elements())
        extra = sorted(str(item) for item in (Counter(names) - Counter(expected)).elements())
        raise ContractError(
            "%s does not draw the sealed circuit's Bought Parts: missing %s; extra %s"
            % (BODIES_PATH, ", ".join(missing[:6]) or "none", ", ".join(extra[:6]) or "none")
        )
    outline = pcba_bounds(electrical)
    if outline is not None:
        board = next(item for item in listed if item.get("name") == "bought_%s" % BOARD_ID)
        stated = [[float(v) for v in corner] for corner in outline]
        drawn_at = board.get("bounds")
        if (
            board.get("source") != "contract" or not isinstance(drawn_at, list) or len(drawn_at) != 2
            or any(not isinstance(corner, list) or len(corner) != 3 for corner in drawn_at)
            or any(abs(float(drawn_at[k][i]) - stated[k][i]) > 1e-6 for k in range(2) for i in range(3))
        ):
            raise ContractError(
                "the board body is not the contract's pcba.bounds_mm %s: the board is no catalogue part, "
                "so its outline is the contract's, never estimated" % outline
            )
    drawn = []
    for item in listed + routes:
        name, step = item.get("name"), item.get("step")
        if (
            not isinstance(name, str) or not name.startswith(BOUGHT_OCCURRENCE_PREFIX)
            or not isinstance(step, str) or not step.startswith("bought/")
        ):
            raise ContractError("%s lists a body outside the bought group: %s" % (BODIES_PATH, name))
        if hashlib.sha256(cad(step)).hexdigest() != item.get("step_sha256"):
            raise ContractError("the bought body %s is not the STEP %s records" % (step, BODIES_PATH))
        drawn.append(name)

    package = read_assembly_package(sealed(ASSEMBLY_PACKAGE_PATH, "the Made product lacks %s" % ASSEMBLY_PACKAGE_PATH))
    occurrences = {item.name: item for item in package.occurrences if item.name.startswith(BOUGHT_OCCURRENCE_PREFIX)}
    if sorted(occurrences) != sorted(drawn):
        raise ContractError(
            "the assembly does not carry exactly the drawn Bought Parts: add bought_group() to the "
            "assembly entry (missing %s; extra %s)"
            % (", ".join(sorted(set(drawn) - set(occurrences))[:6]) or "none",
               ", ".join(sorted(set(occurrences) - set(drawn))[:6]) or "none")
        )
    off = sorted(name for name, item in occurrences.items() if item.color_hex != BOUGHT_PART_HEX)
    if off:
        raise ContractError("Bought Part occurrences not in the not-printed %s: %s"
                            % (BOUGHT_PART_HEX, ", ".join(off[:6])))

    report = document(ELECTRICAL_PATH, ELECTRICAL_KIND)
    if report.get("bodies_sha256") != hashlib.sha256(bodies_raw).hexdigest():
        raise ContractError("%s was drawn from another body list" % ELECTRICAL_PATH)
    files = report.get("files") if isinstance(report.get("files"), Mapping) else {}
    if set(files) != set(PICTURES) | {ASSEMBLY_TEXT}:
        raise ContractError("%s does not name the three pictures and the assembly text" % ELECTRICAL_PATH)
    shas = {}
    for name in PICTURES + (ASSEMBLY_TEXT,):
        data = cad("%s/%s" % (ELECTRICAL_DIRECTORY, name))
        if hashlib.sha256(data).hexdigest() != files[name]:
            raise ContractError("%s/%s is not the file %s names" % (ELECTRICAL_DIRECTORY, name, ELECTRICAL_PATH))
        if name.endswith(".png") and not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ContractError("%s/%s is not a PNG" % (ELECTRICAL_DIRECTORY, name))
        shas[name] = files[name]
        if name == ASSEMBLY_TEXT:
            text = data

    printed_record = None
    printed = report.get("printed")
    if printed is not None:
        # ADR 0095 (2026-11-07): the primary Factory weighs holds printed
        # bodies only, and is the scene minus the bought bodies.
        if (
            not isinstance(printed, Mapping) or set(printed) != PRINTED_FIELDS
            or printed.get("step") != PRINTED_PATH
            or not isinstance(printed.get("removed"), list)
            or not all(isinstance(name, str) for name in printed["removed"])
        ):
            raise ContractError("%s names its printed-only primary malformed" % ELECTRICAL_PATH)
        printed_bytes = cad(PRINTED_PATH)
        if hashlib.sha256(printed_bytes).hexdigest() != printed.get("sha256"):
            raise ContractError("%s is not the printed-only primary %s names" % (PRINTED_PATH, ELECTRICAL_PATH))
        scene_bytes = sealed(SCENE_PATH, "the Made product lacks %s" % SCENE_PATH)
        scene_sha256 = hashlib.sha256(scene_bytes).hexdigest()
        if scene_sha256 != printed.get("scene_sha256"):
            raise ContractError(
                "the printed-only primary was drawn from another scene than the sealed %s" % SCENE_PATH
            )
        if sorted(printed["removed"] or []) != sorted(drawn):
            raise ContractError("the printed-only primary does not remove exactly the drawn Bought Parts")
        counts = verify_printed_primary(scene_bytes, printed_bytes, printed["removed"])
        printed_record = {
            "path": (prefix / PRINTED_PATH).as_posix(),
            "sha256": printed["sha256"],
            "scene_path": SCENE_PATH,
            "scene_sha256": scene_sha256,
            "removed": list(printed["removed"]),
            **counts,
        }

    readme = sealed(README_PATH, "the Made product lacks its README.md, which carries the "
                                 "Electrical Assembly text")
    if text.strip() not in readme:
        raise ContractError(
            "the product README does not carry %s/%s verbatim: who assembles and solders the "
            "circuit is the contract's, not the README's own prose" % (ELECTRICAL_DIRECTORY, ASSEMBLY_TEXT)
        )
    result = {
        "bodies": (prefix / BODIES_PATH).as_posix(),
        "bodies_sha256": hashlib.sha256(bodies_raw).hexdigest(),
        "bought_bodies": len(listed),
        "routes": len(routes),
        "pcba": BOARD_ID if pcba_parts(electrical) else None,
        "pcba_bounds_mm": outline,
        "pictures": {name: (prefix / ELECTRICAL_DIRECTORY / name).as_posix() for name in PICTURES},
        "files_sha256": shas,
    }
    if printed_record is not None:
        result["printed_primary"] = printed_record
    return result


__all__ = [
    "BODIES_PATH",
    "ELECTRICAL_PATH",
    "PRINTED_PATH",
    "draws_bought_parts",
    "expected_bodies",
    "verify_made_bought",
    "verify_printed_primary",
]
