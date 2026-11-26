"""The host's check of a Made kit's print layout (ADR 0104 decision 4).

Final verification lays every Sheet of a kit and every loose printed Part
copy into ``measure/kit/print.step`` and records it in
``measure/kit/print.json`` (``make-round/scripts/kit_print.py``). Before
Make is accepted the host checks, on the sealed bytes and without
rebuilding geometry (ADR 0061), that

- the record is for the sealed tree and names the sealed STEP by hash;
- its Sheets are the tree's Sheets with their contract copies, and its loose
  copies are every printed Part on no Sheet, as many as the toy uses plus
  the spares the Part declares (``spares``, 2026-11-16);
- the STEP's leaves are exactly ``<Sheet>`` for each Sheet and
  ``loose/<Part>#n`` for each loose copy, so no Bought Part body is in it;
  each Sheet and, since 2026-11-16, each loose copy is one connected solid
  (one solid, one outer shell), and every loose copy of one Part has the
  same volume and area.
- a tree that declares ``"spares": "none"`` (amendment 2026-11-26, the
  owner-approved kit that ships no spare piece) has no Part with
  ``spares`` and no Sheet copy beyond the toy's count, and its record says
  ``"spares": "none"``; a record says so only for such a tree. The
  accepted check carries ``"spares": "none"`` too, so the Make receipt
  shows the kit ships no spares.
- Parts that share a ``print`` code (ADR 0092 amendment 2026-11-26) are one
  print: the tree gives them one filament, and every leaf of each of them
  in the sealed ``assembled.step`` has the same volume, area and principal
  moments of inertia, a fingerprint no pose changes; every loose copy under
  one code matches too. A mismatch is refused, so the spare a shared code
  counts once is a spare of every place it is used. The accepted check
  lists the codes as ``shared_prints``.

Factory splits the STEP into its solids and arranges and slices each one on
its own, so a fused Sheet is weighed and placed as the one plate it prints
as (schema 2, 2026-11-14). Only schema 2 is accepted: no kit run ever wrote
the unfused schema 1, and accepting it would let a run ship unfused Sheets.

The accepted record names the file Release ships under ``parts/``, the one
set Factory prices, so Factory weighs the filament the maker prints, frames
included. Since 2026-11-23 the record may also name
``measure/kit/scene.step``, the scene without the Bought Part bodies
``not-printed.json`` lists: the host checks that it holds exactly every
other leaf of the sealed scene with its volume and area, and Release ships
it as the root ``assembled.step`` the shop's viewer shows. A record without
it keeps the earlier primary, the layout itself. A kit with Sheets must have one; a kit without
Sheets is checked when final verification wrote one (current tools always
do) and otherwise keeps its scene.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from workshop.errors import ContractError
from workshop.make.kit_tree import has_assembly_tree, install_document, not_printed, tree_digest, tree_totals
from workshop.wish.assembly_tree import NO_SPARES, print_groups, ships_no_spares

KIND = "kit-print-layout"
SCHEMA_VERSION = 2
STEP_PATH = "measure/kit/print.step"
REPORT_PATH = "measure/kit/print.json"
SCENE_STEP_PATH = "measure/kit/scene.step"
SCENE_PATH = "assembled.step"
LOOSE = "loose"
_TOLERANCE = 1e-5


def expected_copies(contract: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """``(sheets, loose)`` the sealed tree gives, as the run-local tool
    writes them."""

    tree = contract["assembly_tree"]
    totals = tree_totals(tree)
    sheets, on_sheet = [], set()
    for sheet in tree.get("sheets") or []:
        copies: dict[str, int] = {}
        for entry in sheet["parts"]:
            copies[entry["id"]] = copies.get(entry["id"], 0) + int(entry["count"])
            on_sheet.add(entry["id"])
        record = {"id": sheet["id"], "filament": sheet["filament"], "copies": copies}
        tests = [piece["id"] for piece in (sheet.get("fit_test") or {}).get("pieces") or ()]
        if tests:
            # ADR 0092 amendment 2026-11-26: fit-test pieces, fused with their
            # Sheet, are no Part copy and no spare.
            record["fit_tests"] = tests
        sheets.append(record)
    spares = {item["id"]: int(item.get("spares", 0)) for item in tree["parts"] if "filament" in item}
    loose = {part: totals.get(part, 0) + spares[part] for part in sorted(spares)
             if part not in on_sheet and totals.get(part, 0) > 0}
    return sheets, loose


def expected_bodies(sheets, loose) -> list[str]:
    names = [sheet["id"] for sheet in sheets]
    for part, count in loose.items():
        names += ["%s/%s#%d" % (LOOSE, part, n) for n in range(1, count + 1)]
    return sorted(names)


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= max(1e-6, _TOLERANCE * max(abs(a), abs(b)))


def check_layout_step(content: bytes, names: list[str], codes: Mapping[str, str] | None = None) -> int:
    """Refuse a layout STEP whose leaves are not exactly ``names``, hold no
    solid, whose fused Sheet is not one connected solid, or whose copies of
    one Part differ; return its leaf count."""

    from workshop.release.printed_primary import scene_bodies

    bodies = scene_bodies(content)
    found = sorted(body.name for body in bodies)
    if found != names:
        missing = sorted(set(names) - set(found))
        extra = sorted(set(found) - set(names))
        raise ContractError(
            "%s does not hold exactly the kit's Sheets and loose copies: missing %s; extra %s"
            % (STEP_PATH, ", ".join(missing[:6]) or "none", ", ".join(extra[:6]) or "none")
        )
    by_part: dict[str, list] = defaultdict(list)
    for body in bodies:
        if not body.solids or body.total[0] <= 0:
            raise ContractError("%s leaf %s holds no solid" % (STEP_PATH, body.name))
        if len(body.solids) != 1 or body.outer_shells != 1:
            if "/" not in body.name:
                raise ContractError(
                    "%s Sheet %s is not one connected solid but %d piece(s): Factory would price and arrange "
                    "its pieces as loose Parts" % (STEP_PATH, body.name, max(len(body.solids), body.outer_shells))
                )
            raise ContractError(
                "%s loose copy %s is not one connected solid but %d piece(s): Factory would print each piece "
                "as a stray Part" % (STEP_PATH, body.name, max(len(body.solids), body.outer_shells))
            )
        if "/" not in body.name:
            continue
        part = body.name.split("/", 1)[1].rsplit("#", 1)[0]
        by_part[(codes or {}).get(part, part)].append(body)
    for part, copies in by_part.items():
        first = copies[0].total
        if any(not (_close(c.total[0], first[0]) and _close(c.total[1], first[1])) for c in copies[1:]):
            raise ContractError("%s copies of %s differ in volume or area" % (STEP_PATH, part))
    return len(bodies)


_PRINT_TOLERANCE = 1e-4


def check_shared_prints(scene: bytes, tree: Mapping[str, Any]) -> dict[str, list[str]]:
    """Refuse a sealed scene in which Parts sharing a print code are not one
    print: every leaf of each of them (``<Part>`` or ``<Part>#n``) must give
    the same pose-free fingerprint, and the tree must give them one
    filament. Return the shared codes and their Parts."""

    groups = print_groups(tree)
    if not groups:
        return {}
    from workshop.release.printed_primary import scene_prints

    filament = {item["id"]: item.get("filament") for item in tree["parts"]}
    leaves: dict[str, list[tuple[str, tuple[float, ...]]]] = defaultdict(list)
    for name, fingerprint in scene_prints(scene):
        leaves[name.rsplit("#", 1)[0] if "#" in name else name].append((name, fingerprint))
    for code, parts in sorted(groups.items()):
        if len({filament.get(part) for part in parts}) != 1:
            raise ContractError("the Parts sharing print code %s are not one filament: %s"
                                % (code, ", ".join(parts)))
        found = [(name, fingerprint) for part in parts for name, fingerprint in leaves.get(part, ())]
        missing = [part for part in parts if part not in leaves]
        if missing:
            raise ContractError("%s holds no body of %s, so print code %s cannot be checked"
                                % (SCENE_PATH, ", ".join(missing), code))
        first_name, first = found[0]
        for name, fingerprint in found[1:]:
            if len(fingerprint) != len(first) or any(
                abs(a - b) > max(1e-6, _PRINT_TOLERANCE * max(abs(a), abs(b))) for a, b in zip(fingerprint, first)
            ):
                raise ContractError(
                    "%s and %s share print code %s but are not the same print: their volume, area or "
                    "moments of inertia differ in %s" % (first_name, name, code, SCENE_PATH)
                )
    return {code: list(parts) for code, parts in sorted(groups.items())}


def _removed_leaves(requested: list[str], names: list[str]) -> set[str]:
    """The scene leaves the not-printed bodies name, each exactly one leaf;
    a Part the scene holds once may be written without its ``#1``."""

    counts: dict[str, int] = defaultdict(int)
    for name in names:
        counts[name] += 1
    found: set[str] = set()
    for body in requested:
        match = body if body in counts or not body.endswith("#1") else body[: -len("#1")]
        if counts.get(match, 0) != 1 or match in found:
            raise ContractError(
                "%s names %s, which is %d leaf bodies of the sealed scene, not one"
                % (REPORT_PATH, body, counts.get(match, 0))
            )
        found.add(match)
    return found


def check_printed_scene(printed: bytes, scene: bytes, removed: list[str]) -> int:
    """Refuse a printed-only scene that is not exactly the sealed scene's
    leaves less the not-printed bodies, each with its volume and area;
    return how many leaves it holds."""

    from workshop.release.printed_primary import scene_bodies

    whole = scene_bodies(scene)
    cut = _removed_leaves(removed, [body.name for body in whole])
    expected = sorted((body.name, body.total) for body in whole if body.name not in cut)
    found = sorted((body.name, body.total) for body in scene_bodies(printed))
    if [name for name, _ in found] != [name for name, _ in expected]:
        missing = sorted({n for n, _ in expected} - {n for n, _ in found})
        extra = sorted({n for n, _ in found} - {n for n, _ in expected})
        raise ContractError(
            "%s does not hold exactly the sealed scene less its not-printed bodies: missing %s; extra %s"
            % (SCENE_STEP_PATH, ", ".join(missing[:6]) or "none", ", ".join(extra[:6]) or "none")
        )
    for (name, a), (_name, b) in zip(found, expected):
        if not (_close(a[0], b[0]) and _close(a[1], b[1])):
            raise ContractError("%s body %s is not the scene's body" % (SCENE_STEP_PATH, name))
    if not found:
        raise ContractError("%s holds no printed body" % SCENE_STEP_PATH)
    return len(found)


def printed_pieces(contract: Mapping[str, Any]) -> int:
    """How many printed pieces the buyer assembles: every printed Part as
    many times as the toy uses it, spares left out."""

    tree = contract["assembly_tree"]
    totals = tree_totals(tree)
    return sum(int(totals.get(item["id"], 0)) for item in tree["parts"] if "filament" in item)


def verify_made_print_layout(
    run_root: Path,
    made: Any,
    contract: Mapping[str, Any] | None,
    catalogue: Any,
) -> dict[str, Any] | None:
    """The printed-only primary record of a kit's layout, or None for a
    contract without an Assembly Tree or a kit without Sheets that wrote no
    layout. Raises ContractError naming what is wrong."""

    if not has_assembly_tree(contract) or not isinstance(catalogue, Mapping):
        return None
    product_root = Path(run_root).joinpath(*PurePosixPath(made.product_root).parts)
    entries = {entry.path: entry for entry in made.product_manifest.entries}
    prefix = PurePosixPath(made.cad_project_path)
    report_path = (prefix / REPORT_PATH).as_posix()
    if report_path not in entries:
        if contract["assembly_tree"].get("sheets"):
            raise ContractError(
                "final verification wrote no %s: a kit with Sheets ships its print layout as the "
                "Factory primary (ADR 0104 decision 4)" % REPORT_PATH
            )
        return None

    def sealed(path: str, missing: str) -> tuple[bytes, str]:
        entry = entries.get(path)
        if entry is None:
            raise ContractError(missing)
        data = product_root.joinpath(*PurePosixPath(path).parts).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if len(data) != entry.bytes or digest != entry.sha256:
            raise ContractError("the Made file %s differs from the Made manifest" % path)
        return data, digest

    raw, report_sha256 = sealed(report_path, "")
    try:
        report = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ContractError("%s is not JSON" % REPORT_PATH) from exc
    if not isinstance(report, Mapping) or report.get("kind") != KIND or (
        type(report.get("schema_version")) is not int or report["schema_version"] != SCHEMA_VERSION
    ):
        raise ContractError("%s is not a kit print layout record" % REPORT_PATH)
    if report.get("tree_sha256") != tree_digest(install_document(contract, catalogue)):
        raise ContractError("%s was laid out for another Assembly Tree than the sealed one" % REPORT_PATH)
    sheets, loose = expected_copies(contract)
    names = expected_bodies(sheets, loose)
    copies: dict[str, int] = defaultdict(int)
    for sheet in sheets:
        for part, count in sheet["copies"].items():
            copies[part] += count
    for part, count in loose.items():
        copies[part] += count
    no_spares = ships_no_spares(contract["assembly_tree"])
    if no_spares:
        totals = tree_totals(contract["assembly_tree"])
        spare = sorted(part for part, count in copies.items() if count > totals.get(part, 0))
        if spare:
            raise ContractError(
                "the sealed tree declares spares \"none\", but it carries spare copies of %s: a kit that "
                "ships no spares prints each Part exactly as often as the toy uses it" % ", ".join(spare[:6])
            )
    if ("spares" in report) != no_spares or (no_spares and report.get("spares") != NO_SPARES):
        raise ContractError(
            "%s %s: it records spares \"none\" exactly when the sealed tree declares the kit ships no spares"
            % (REPORT_PATH, "does not record spares \"none\"" if no_spares else "records spares the tree does not declare")
        )
    if report.get("sheets") != sheets or report.get("loose") != loose or report.get("copies") != dict(
        sorted(copies.items())
    ) or report.get("bodies") != names:
        raise ContractError(
            "%s does not lay out the sealed tree's Sheets and loose copies (each printed Part on no "
            "Sheet, as many times as the toy uses it plus its spares)" % REPORT_PATH
        )
    if report.get("step") != STEP_PATH:
        raise ContractError("%s names another STEP than %s" % (REPORT_PATH, STEP_PATH))
    step_path = (prefix / STEP_PATH).as_posix()
    content, step_sha256 = sealed(step_path, "the Made CAD project lacks %s" % STEP_PATH)
    if report.get("sha256") != step_sha256:
        raise ContractError("%s is not the layout %s names" % (STEP_PATH, REPORT_PATH))
    codes = {part: code for code, parts in print_groups(contract["assembly_tree"]).items() for part in parts}
    leaves = check_layout_step(content, names, codes)
    scene, scene_sha256 = sealed(SCENE_PATH, "the Made product lacks %s" % SCENE_PATH)
    shared = check_shared_prints(scene, contract["assembly_tree"])
    removed = [item["body"] for item in not_printed(contract, catalogue)]
    extra: dict[str, Any] = {}
    if "printed_scene" in report:
        record = report["printed_scene"]
        if not isinstance(record, Mapping) or set(record) != {
            "step", "sha256", "scene", "scene_sha256", "removed"
        } or record.get("step") != SCENE_STEP_PATH:
            raise ContractError("%s printed_scene is malformed" % REPORT_PATH)
        if record.get("scene_sha256") != scene_sha256:
            raise ContractError(
                "%s was cut from another scene than the sealed %s" % (SCENE_STEP_PATH, SCENE_PATH)
            )
        if record.get("removed") != sorted(removed):
            raise ContractError(
                "%s removed other bodies than the sealed tree's not-printed ones" % SCENE_STEP_PATH
            )
        printed_path = (prefix / SCENE_STEP_PATH).as_posix()
        printed, printed_sha256 = sealed(printed_path, "the Made CAD project lacks %s" % SCENE_STEP_PATH)
        if record.get("sha256") != printed_sha256:
            raise ContractError("%s is not the scene %s names" % (SCENE_STEP_PATH, REPORT_PATH))
        check_printed_scene(printed, scene, removed)
        extra = {
            "printed_scene_path": printed_path,
            "printed_scene_sha256": printed_sha256,
            "pieces": printed_pieces(contract),
        }
    if no_spares:
        extra["spares"] = NO_SPARES
    if shared:
        extra["shared_prints"] = shared
    return {
        **extra,
        "path": step_path,
        "sha256": step_sha256,
        "scene_path": SCENE_PATH,
        "scene_sha256": scene_sha256,
        "removed": removed,
        "printed_bodies": leaves,
        "removed_bodies": len(removed),
        "layout_path": report_path,
        "layout_sha256": report_sha256,
    }


__all__ = ["REPORT_PATH", "SCENE_STEP_PATH", "STEP_PATH", "check_layout_step", "check_printed_scene",
           "check_shared_prints",
           "printed_pieces", "expected_bodies", "expected_copies",
           "verify_made_print_layout"]
