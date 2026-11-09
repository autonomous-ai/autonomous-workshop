"""Reduce a direct publication's primary STEP to the bodies that are printed.

Factory weighs every solid in the one STEP that crosses (``assembled.step``):
it splits the file into its solids and slices each, with no name filter.
A CAD project's combined entry is a review scene. It places every printed
part and also the props and bought hardware the scene shows (headphones on a
stand, a steel rod, nuts, ballast), so publishing it unchanged bills those
bodies as filament.

The printed inventory is the project's ``PRINTABLE = True`` entries. Labels
differ between a part entry and the combined scene, so a scene body counts as
printed when every solid it holds has the volume and surface area of a solid
some printed entry builds, or the body as a whole has those of a printed
entry's body (some writers' parts read back as shells, not solids). Both
measures survive moving, turning or mirroring a part.

Every other body must be declared by the operator, as display-only or as
bought. Declared bodies are removed and reported. An undeclared one refuses
the publication, and so does a declaration that names a printed body or no
body at all. Nothing is ever dropped silently. When nothing is declared and
every body is printed, the primary's bytes are returned unchanged.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Mapping, Optional, Sequence, Tuple

from workshop.errors import ContractError


__all__ = ["PrintedPrimary", "SceneBody", "printed_only_primary", "scene_bodies"]


# Relative tolerance on volume and area. A STEP round trip keeps both to
# about 1e-9; a different part differs by far more than this.
_RELATIVE_TOLERANCE = 1e-5
_ABSOLUTE_TOLERANCE = 1e-6


@dataclass(frozen=True)
class SceneBody:
    """One leaf occurrence of a STEP: its name and each solid's measures."""

    name: str
    solids: Tuple[Tuple[float, float], ...]
    # The whole body's volume and area. Some writers' parts read back as
    # closed shells rather than solids; they are matched on this.
    total: Tuple[float, float] = (0.0, 0.0)


@dataclass(frozen=True)
class PrintedPrimary:
    content: bytes
    kept: Tuple[str, ...]
    stripped: Tuple[str, ...]


def _ocp():
    try:
        from OCP.BRepGProp import BRepGProp
        from OCP.GProp import GProp_GProps
        from OCP.IFSelect import IFSelect_RetDone
        from OCP.STEPCAFControl import STEPCAFControl_Reader
        from OCP.TCollection import TCollection_AsciiString, TCollection_ExtendedString
        from OCP.TDataStd import TDataStd_Name
        from OCP.TDF import TDF_Label, TDF_LabelSequence, TDF_Tool
        from OCP.TDocStd import TDocStd_Document
        from OCP.TopAbs import TopAbs_SOLID
        from OCP.TopExp import TopExp_Explorer
        from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ShapeTool
    except ImportError as exc:  # pragma: no cover - the CAD venv has OCP
        raise ContractError(
            "reading the primary STEP's bodies needs OCP (the CAD virtualenv)"
        ) from exc
    return locals()


def _read_document(content: bytes):
    ocp = _ocp()
    if not isinstance(content, bytes) or not content:
        raise ContractError("primary STEP is empty")
    with tempfile.TemporaryDirectory(prefix="workshop-printed-primary-") as temporary:
        path = Path(temporary) / "primary.step"
        path.write_bytes(content)
        document = ocp["TDocStd_Document"](ocp["TCollection_ExtendedString"]("XmlXCAF"))
        reader = ocp["STEPCAFControl_Reader"]()
        reader.SetNameMode(True)
        reader.SetColorMode(True)
        reader.SetLayerMode(True)
        if reader.ReadFile(os.fspath(path)) != ocp["IFSelect_RetDone"]:
            raise ContractError("primary STEP cannot be read")
        if not reader.Transfer(document):
            raise ContractError("primary STEP cannot be transferred")
    return document


def _name(label) -> Optional[str]:
    ocp = _ocp()
    attribute = ocp["TDataStd_Name"]()
    if label.FindAttribute(ocp["TDataStd_Name"].GetID_s(), attribute):
        value = attribute.Get().ToExtString()
        return value or None
    return None


def _measures(shape) -> Tuple[float, float]:
    ocp = _ocp()
    volume = ocp["GProp_GProps"]()
    ocp["BRepGProp"].VolumeProperties_s(shape, volume)
    area = ocp["GProp_GProps"]()
    ocp["BRepGProp"].SurfaceProperties_s(shape, area)
    return (abs(volume.Mass()), area.Mass())


def _solids(shape) -> Tuple[Tuple[float, float], ...]:
    ocp = _ocp()
    result = []
    explorer = ocp["TopExp_Explorer"](shape, ocp["TopAbs_SOLID"])
    while explorer.More():
        volume = ocp["GProp_GProps"]()
        ocp["BRepGProp"].VolumeProperties_s(explorer.Current(), volume)
        area = ocp["GProp_GProps"]()
        ocp["BRepGProp"].SurfaceProperties_s(explorer.Current(), area)
        result.append((abs(volume.Mass()), area.Mass()))
        explorer.Next()
    return tuple(sorted(result))


def _leaves(document) -> List[Tuple[object, Optional[object], SceneBody]]:
    """Every leaf as (its component label or free label, parent, body)."""

    ocp = _ocp()
    shape_tool = ocp["XCAFDoc_ShapeTool"]
    tool = ocp["XCAFDoc_DocumentTool"].ShapeTool_s(document.Main())
    found: List[Tuple[object, Optional[object], SceneBody]] = []

    def visit(label, parent, fallback: Optional[str]) -> None:
        referred = label
        if shape_tool.IsReference_s(label):
            referred = ocp["TDF_Label"]()
            shape_tool.GetReferredShape_s(label, referred)
        name = _name(referred) or _name(label) or fallback or "(unnamed)"
        if shape_tool.IsAssembly_s(referred):
            components = ocp["TDF_LabelSequence"]()
            shape_tool.GetComponents_s(referred, components, False)
            for index in range(1, components.Length() + 1):
                visit(components.Value(index), referred, None)
            return
        shape = shape_tool.GetShape_s(label)
        found.append((label, parent, SceneBody(
            name=name, solids=_solids(shape), total=_measures(shape))))

    free = ocp["TDF_LabelSequence"]()
    tool.GetFreeShapes(free)
    for index in range(1, free.Length() + 1):
        visit(free.Value(index), None, None)
    return found


def _groups(document) -> List[Tuple[Optional[object], object, str, int]]:
    """Every assembly as (its component label or None when free, the
    assembly label, its entry, its component count)."""

    ocp = _ocp()
    shape_tool = ocp["XCAFDoc_ShapeTool"]
    tool = ocp["XCAFDoc_DocumentTool"].ShapeTool_s(document.Main())
    found: List[Tuple[Optional[object], object, str, int]] = []

    def entry(label) -> str:
        text = ocp["TCollection_AsciiString"]()
        ocp["TDF_Tool"].Entry_s(label, text)
        return text.ToCString()

    def visit(label, component) -> None:
        referred = label
        if shape_tool.IsReference_s(label):
            referred = ocp["TDF_Label"]()
            shape_tool.GetReferredShape_s(label, referred)
        if not shape_tool.IsAssembly_s(referred):
            return
        components = ocp["TDF_LabelSequence"]()
        shape_tool.GetComponents_s(referred, components, False)
        found.append((component, referred, entry(referred), components.Length()))
        for index in range(1, components.Length() + 1):
            visit(components.Value(index), components.Value(index))

    free = ocp["TDF_LabelSequence"]()
    tool.GetFreeShapes(free)
    for index in range(1, free.Length() + 1):
        visit(free.Value(index), None)
    return found


def _drop_emptied_groups(document, had_components: set) -> None:
    """Remove every group the stripping left with no components (a powered
    toy's ``bought`` group, ADR 0095), then any group that left empty, so
    no empty group is written as a body. A group that was empty before is
    left alone."""

    ocp = _ocp()
    shape_tool = ocp["XCAFDoc_ShapeTool"]
    tool = ocp["XCAFDoc_DocumentTool"].ShapeTool_s(document.Main())
    while True:
        emptied = [
            (component, referred)
            for component, referred, key, count in _groups(document)
            if count == 0 and key in had_components
        ]
        if not emptied:
            return
        for component, referred in emptied:
            if component is not None:
                tool.RemoveComponent(component)
            if shape_tool.IsFree_s(referred):
                tool.RemoveShape(referred, True)
        tool.UpdateAssemblies()


def scene_bodies(content: bytes) -> Tuple[SceneBody, ...]:
    """Every leaf body in ``content``, in file order."""

    return tuple(body for _, _, body in _leaves(_read_document(content)))


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= max(_ABSOLUTE_TOLERANCE, _RELATIVE_TOLERANCE * max(abs(a), abs(b)))


def _matches(measure: Tuple[float, float], printed: Sequence[Tuple[float, float]]) -> bool:
    return any(_close(measure[0], v) and _close(measure[1], a) for v, a in printed)


def _is_printed(body: SceneBody, printed: Sequence[Tuple[float, float]]) -> bool:
    """Every solid of the body is a printed solid, or the whole body is a
    printed body. A body with no volume is never printed."""

    if body.total[0] <= _ABSOLUTE_TOLERANCE:
        return False
    if body.solids and all(_matches(solid, printed) for solid in body.solids):
        return True
    return _matches(body.total, printed)


def _write_document(document) -> bytes:
    from cadgen.step_export import write_xcaf_doc_step_file

    with tempfile.TemporaryDirectory(prefix="workshop-printed-primary-") as temporary:
        path = Path(temporary) / "assembled.step"
        write_xcaf_doc_step_file(document, path, originating_system="workshop printed-only primary")
        return path.read_bytes()


def printed_only_primary(
    primary: bytes,
    printed_entries: Mapping[str, bytes],
    *,
    declared: Iterable[str] = (),
) -> PrintedPrimary:
    """Return ``primary`` holding only printed bodies, or refuse.

    ``printed_entries`` maps each ``PRINTABLE = True`` entry's STEP path to
    its bytes. ``declared`` names every scene body the operator says is not
    printed; each of those is removed, and nothing else is.
    """

    if not printed_entries:
        raise ContractError("no PRINTABLE = True entry STEP to compare the primary with")
    printed: List[Tuple[float, float]] = []
    for path, content in sorted(printed_entries.items()):
        bodies = [body for body in scene_bodies(content) if body.total[0] > _ABSOLUTE_TOLERANCE]
        if not bodies:
            raise ContractError("printed entry %s holds no body with volume" % path)
        for body in bodies:
            printed.extend(body.solids)
            printed.append(body.total)

    document = _read_document(primary)
    leaves = _leaves(document)
    if not leaves:
        raise ContractError("primary STEP holds no body")
    wanted = set(declared)
    by_name: dict = {}
    for _, _, body in leaves:
        by_name.setdefault(body.name, []).append(_is_printed(body, printed))

    errors = []
    for name in sorted(wanted):
        states = by_name.get(name)
        if states is None:
            errors.append("%s is declared not printed but the primary has no body of that name" % name)
        elif any(states):
            errors.append(
                "%s is declared not printed but matches a PRINTABLE = True part" % name
            )
    undeclared = sorted(
        {
            body.name
            for _, _, body in leaves
            if body.name not in wanted and not _is_printed(body, printed)
        }
    )
    if undeclared:
        errors.append(
            "the primary STEP holds bodies no PRINTABLE = True entry builds, and Factory "
            "would bill them as filament: %s. Declare each one with --display-only NAME "
            "(a prop the buyer does not get) or --bought NAME=PART (hardware the buyer "
            "gets, billed as an extra material)" % ", ".join(undeclared)
        )
    if errors:
        raise ContractError("; ".join(errors))

    kept = tuple(body.name for _, _, body in leaves if body.name not in wanted)
    stripped = tuple(body.name for _, _, body in leaves if body.name in wanted)
    if not stripped:
        return PrintedPrimary(content=primary, kept=kept, stripped=())
    if not kept:
        raise ContractError("no printed body remains in the primary STEP")

    ocp = _ocp()
    shape_tool = ocp["XCAFDoc_ShapeTool"]
    tool = ocp["XCAFDoc_DocumentTool"].ShapeTool_s(document.Main())
    had_components = {key for _, _, key, count in _groups(document) if count > 0}
    orphans = []
    for label, parent, body in leaves:
        if body.name not in wanted:
            continue
        if parent is None:
            tool.RemoveShape(label, True)
            continue
        referred = ocp["TDF_Label"]()
        shape_tool.GetReferredShape_s(label, referred)
        tool.RemoveComponent(label)
        orphans.append(referred)
    # A part no component refers to any more becomes a free shape, which
    # the writer would still export; remove it as well.
    for referred in orphans:
        if not referred.IsNull() and shape_tool.IsFree_s(referred):
            tool.RemoveShape(referred, True)
    tool.UpdateAssemblies()
    _drop_emptied_groups(document, had_components)
    content = _write_document(document)

    after = scene_bodies(content)
    expected = sorted((body.name, (body.total,)) for _, _, body in leaves if body.name not in wanted)
    found = sorted((body.name, (body.total,)) for body in after)
    if [name for name, _ in found] != [name for name, _ in expected] or not all(
        len(a) == len(b) and all(_close(x[0], y[0]) and _close(x[1], y[1]) for x, y in zip(a, b))
        for (_, a), (_, b) in zip(found, expected)
    ):
        raise ContractError("the printed-only primary does not hold exactly the printed bodies")
    return PrintedPrimary(content=content, kept=kept, stripped=stripped)
