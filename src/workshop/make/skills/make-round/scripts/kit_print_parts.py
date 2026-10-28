#!/usr/bin/env python3
"""Each printed Part of a kit Component, alone in its print stance (ADR 0092,
owner decision 2026-10-28).

    kit_print_parts.py describe <project>/part_<geometry>.step.py

A kit Component's ``gen_step()`` is the Component as it is assembled: in the
Display Pose a flat top board is an inner ceiling over air and a thin web is
measured inside a large model on a coarse grid. Each kit Part prints alone,
so its file also defines ``print_parts()``, returning ``{Part id: shape}``:
every printed Part of the Component, once per Part id (copies are the same
Part), each alone in the stance it prints in, bottom at Z 0. Bought Parts and
Print Pieces are never printed and are not in it. The Contract Proof writes
the same ``print_parts()`` and gates it with ``make_round --print-gates-only``.

``describe`` builds ``print_parts()`` once and prints one JSON line,
``{"kind": "kit-print-parts", "parts": {id: {"identity", "bottom_mm",
"solids"}}, "error": null}``; ``error`` says why there is nothing to gate
(no ``print_parts()``, not a dict, a value that is not a shape). Exit 0
with parts, 1 with an error, 2 on bad usage.

make_round and verify_project read the line, refuse a set of Parts that is
not the Component's printed Parts (:func:`failures`), and gate each Part
through its own entry (:func:`write_entries`): a ``part_<id>.step.py`` that
builds the Component's ``print_parts()`` and returns that one Part, so the
print gates build it from source with the feature tags its build records.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
from pathlib import Path

CAD_SCRIPTS = Path(__file__).resolve().parents[2] / "cad" / "scripts"
KIND = "kit-print-parts"
FUNCTION = "print_parts"
# How far a Part's bottom may sit from the bed and still be on it.
BED_TOLERANCE_MM = 0.01
RULE = ("a kit Component defines print_parts() returning {Part id: shape}: every printed Part of the "
        "Component, once per Part id, each alone in its print stance, bottom at Z 0; no Bought Part and "
        "no Print Piece (ADR 0092, owner decision 2026-10-28)")
_KIT_TREE = []


def _runtime_paths() -> None:
    for path in (CAD_SCRIPTS, CAD_SCRIPTS / "packages", CAD_SCRIPTS / "packages" / "cadgen" / "src"):
        text = str(path)
        if path.is_dir() and text not in sys.path:
            sys.path.insert(0, text)


def kit_tree():
    if not _KIT_TREE:
        spec = importlib.util.spec_from_file_location(
            "kit_print_parts_kit_tree", Path(__file__).resolve().with_name("kit_tree.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _KIT_TREE.append(module)
    return _KIT_TREE[0]


# ---------------------------------------------------------------------------
# which Parts a Component prints


def printed_parts(kit: dict, geometry: str) -> list[str] | None:
    """The printed Part ids of one Component, in tree order; None when the
    geometry is not a Component of the tree."""

    plan = kit_tree().Plan(kit)
    if geometry not in plan.component_parts:
        return None
    return [part for part in plan.component_parts[geometry] if part in plan.printed]


def failures(kit: dict, geometry: str, described: dict) -> list[str]:
    """Why a ``describe`` result cannot be gated: each line a repair."""

    entry = "part_%s.step.py" % geometry
    if not isinstance(described, dict):
        return ["%s: print_parts() was not described; %s" % (entry, RULE)]
    if described.get("error"):
        return ["%s: %s; %s" % (entry, described["error"], RULE)]
    parts = described.get("parts")
    if not isinstance(parts, dict):
        return ["%s: print_parts() returned no Parts; %s" % (entry, RULE)]
    plan = kit_tree().Plan(kit)
    expected = printed_parts(kit, geometry) or []
    found = []
    for key in parts:
        if key in expected:
            continue
        base = re.sub(r"#\d+$", "", key)
        if base != key and base in expected:
            why = "copies are one Part: name it once, %s, without #n" % base
        elif key in plan.bought or base in plan.bought:
            why = "%s is a Bought Part: it is never printed" % base
        elif key in plan.pieces or base in plan.pieces:
            why = "%s is a Print Piece: paper is never printed in plastic" % base
        elif key in plan.component_of:
            why = "%s is a Part of Component %s, not of this one" % (key, plan.component_of[key])
        else:
            why = "no printed Part of this Component is called %s" % key
        found.append("%s: print_parts() names %s: %s; leave it out" % (entry, key, why))
    for part in expected:
        if part not in parts:
            found.append("%s: print_parts() has no entry for printed Part %s: return it alone in its "
                         "print stance, bottom at Z 0" % (entry, part))
    for key in expected:
        item = parts.get(key)
        if not isinstance(item, dict):
            continue
        bottom = item.get("bottom_mm")
        if not isinstance(bottom, (int, float)) or abs(bottom) > BED_TOLERANCE_MM:
            found.append("%s: print_parts()[%r] has its bottom at Z %s mm, not on the bed: place the Part in "
                         "its print stance with its bottom at Z 0" % (
                             entry, key, "%.3f" % bottom if isinstance(bottom, (int, float)) else "?"))
        if not item.get("solids"):
            found.append("%s: print_parts()[%r] holds no solid" % (entry, key))
    return found


def identities(described: dict) -> dict[str, str]:
    """``{Part id: B-rep identity}`` of a described set; reuse compares them."""

    parts = described.get("parts") if isinstance(described, dict) else None
    return {key: item.get("identity") for key, item in (parts or {}).items() if isinstance(item, dict)}


def parse(stdout: str, returncode: int) -> dict:
    """A ``describe`` run's result from its JSON line."""

    for line in reversed((stdout or "").splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except ValueError:
            break
        if isinstance(payload, dict) and payload.get("kind") == KIND:
            return payload
        break
    return {"kind": KIND, "parts": None,
            "error": "print_parts() did not build (kit_print_parts.py exit %d)" % returncode}


# ---------------------------------------------------------------------------
# one entry per Part

ENTRY = '''\
"""Generated by make-round kit_print_parts.py: printed Part {part} of
{component}, alone in its print stance (ADR 0092, owner decision
2026-10-28). Never edit it; it is rewritten before every gate run."""

import importlib.util
import sys
from pathlib import Path

COMPONENT = (Path(__file__).resolve().parent / {relative!r}).resolve()
PART = {part!r}


def gen_step():
    project = str(COMPONENT.parent)
    if project not in sys.path:
        sys.path.insert(0, project)
    name = "_kit_print_part_" + COMPONENT.name.replace(".", "_")
    spec = importlib.util.spec_from_file_location(name, COMPONENT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.print_parts()[PART]
'''


def entry_path(directory: Path, part: str) -> Path:
    return Path(directory) / ("part_%s.step.py" % part)


def write_entries(component: Path, directory: Path, parts) -> dict[str, Path]:
    """Write one gate entry per Part into a fresh ``directory`` (inside the
    project's ``__cadgen__``, which no discovery or source hash reads)."""

    component, directory = Path(component).resolve(), Path(directory)
    if directory.is_dir() and not directory.is_symlink():
        shutil.rmtree(directory)
    directory.mkdir(parents=True, exist_ok=True)
    relative = os.path.relpath(component, directory.resolve())
    written = {}
    for part in parts:
        path = entry_path(directory, part)
        path.write_text(ENTRY.format(part=part, component=component.name, relative=relative), encoding="utf-8")
        written[part] = path
    return written


# ---------------------------------------------------------------------------
# describe


def describe(entry: Path) -> dict:
    _runtime_paths()
    from build123d import Shape

    from brepbundle import identity
    from printlib import detail_build, load_entry, project_on_path, tight_box

    with project_on_path(entry.parent), contextlib.redirect_stdout(io.StringIO()), detail_build():
        module = load_entry(entry, "kit_print_parts")
        builder = getattr(module, FUNCTION, None)
        if not callable(builder):
            return {"kind": KIND, "parts": None, "error": "%s defines no print_parts()" % entry.name}
        built = builder()
    if not isinstance(built, dict):
        return {"kind": KIND, "parts": None,
                "error": "print_parts() returned %s, not a dict of Part id to shape" % type(built).__name__}
    parts = {}
    for key, shape in built.items():
        if not isinstance(key, str) or not isinstance(shape, Shape):
            return {"kind": KIND, "parts": None,
                    "error": "print_parts()[%r] is %s, not a shape" % (key, type(shape).__name__)}
        solids = len(list(shape.solids()))
        bottom = tight_box(shape)[0][2] if solids else None
        parts[key] = {"identity": identity(shape), "bottom_mm": None if bottom is None else round(float(bottom), 6),
                      "solids": solids}
    return {"kind": KIND, "parts": dict(sorted(parts.items())), "error": None}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or args[0] != "describe" or not args[1].endswith(".step.py"):
        print("usage: kit_print_parts.py describe <project>/part_<geometry>.step.py", file=sys.stderr)
        return 2
    entry = Path(args[1]).resolve()
    if not entry.is_file():
        print("kit_print_parts.py: no such entry: %s" % entry, file=sys.stderr)
        return 2
    try:
        result = describe(entry)
    except Exception as error:  # noqa: BLE001 - the CLI boundary: report, do not traceback
        result = {"kind": KIND, "parts": None,
                  "error": "print_parts() failed: %s: %s" % (type(error).__name__, str(error)[:300])}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["error"] is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
