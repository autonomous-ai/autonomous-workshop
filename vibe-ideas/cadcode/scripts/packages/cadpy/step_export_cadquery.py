"""CadQuery → XCAF-doc adapter for :mod:`cadpy.step_export`.

The OCCT-level pipeline (XCAF doc → STEPCAFControl_Writer → STEP file →
LoadedStepScene) is library-agnostic; only the *input* shape needs a
CadQuery-aware adapter. This module wraps `cq.Workplane`, `cq.Shape`, and
`cq.Assembly` into an XCAF-doc, then defers to the shared
`step_export.export_xcaf_doc_step_scene` / `write_xcaf_doc_step_file` helpers.

The contract that lets this work is: a CadQuery shape exposes its underlying
OCCT `TopoDS_Shape` via `.wrapped` (`cq.Workplane.val().wrapped`,
`cq.Assembly.toCompound().wrapped`), which the OCCT layer consumes directly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cadpy.step_export import (
    create_bin_xcaf_doc,
    export_xcaf_doc_step_scene,
    write_xcaf_doc_step_file,
)
from cadpy.step_scene import (
    LoadedStepScene,
    load_step_scene_from_xcaf_doc,
)


__all__ = [
    "is_cadquery_shape",
    "build_cadquery_step_scene",
    "export_cadquery_step_scene",
]


def _topods_from_cadquery(to_export: Any) -> Any:
    """Reduce a CadQuery-flavored input to its underlying OCCT `TopoDS_Shape`.

    Handles `cq.Workplane`, `cq.Shape`, and `cq.Assembly`. Raises
    :class:`TypeError` if the input cannot be reduced.
    """
    # cq.Assembly: prefer toCompound() so the children come along.
    if _is_cadquery_assembly(to_export):
        compound = to_export.toCompound()
        wrapped = getattr(compound, "wrapped", None)
        if wrapped is None:
            raise TypeError("cq.Assembly.toCompound() did not yield a wrapped TopoDS_Shape")
        return wrapped
    # cq.Workplane: collapse via .val(), then unwrap.
    val_fn = getattr(to_export, "val", None)
    if callable(val_fn):
        val = val_fn()
        wrapped = getattr(val, "wrapped", None)
        if wrapped is not None:
            return wrapped
    # cq.Shape (or any OCCT wrapper): read .wrapped directly.
    wrapped = getattr(to_export, "wrapped", None)
    if wrapped is not None:
        return wrapped
    raise TypeError(
        f"Cannot extract TopoDS_Shape from object of type {type(to_export).__name__}"
    )


def _is_cadquery_assembly(obj: Any) -> bool:
    # Duck-typed; matches cq.Assembly without importing cadquery at module load.
    if not hasattr(obj, "children"):
        return False
    to_compound = getattr(obj, "toCompound", None)
    return callable(to_compound)


def is_cadquery_shape(obj: Any) -> bool:
    """Duck-typed check: does `obj` look like a CadQuery shape we can handle?

    Returns True for `cq.Workplane` (has `.val()` returning something with
    `.wrapped`) and `cq.Shape` (has `.wrapped` directly *and* lives in the
    `cadquery` module hierarchy). `cq.Assembly` is also accepted (matches via
    `toCompound`).
    """
    if _is_cadquery_assembly(obj):
        return True
    val_fn = getattr(obj, "val", None)
    if callable(val_fn):
        try:
            val = val_fn()
        except Exception:  # pragma: no cover — defensive
            return False
        if getattr(val, "wrapped", None) is not None:
            module = type(obj).__module__ or ""
            return module.startswith("cadquery")
    wrapped = getattr(obj, "wrapped", None)
    if wrapped is not None:
        module = type(obj).__module__ or ""
        return module.startswith("cadquery")
    return False


def _color_rgba_quantity(color: Any) -> Any | None:
    """Convert a `cq.Color`, RGBA tuple, or wrapped OCCT color into
    `Quantity_ColorRGBA`.
    """
    if color is None:
        return None
    from OCP.Quantity import Quantity_ColorRGBA

    if isinstance(color, Quantity_ColorRGBA):
        return color
    wrapped = getattr(color, "wrapped", None)
    if isinstance(wrapped, Quantity_ColorRGBA):
        return wrapped
    if wrapped is not None and hasattr(wrapped, "GetRGB"):
        return wrapped
    # cq.Color exposes .toTuple() returning RGBA in 0..1.
    to_tuple = getattr(color, "toTuple", None)
    if callable(to_tuple):
        try:
            values = to_tuple()
        except Exception:  # pragma: no cover
            return None
        return _quantity_from_rgba(values)
    if isinstance(color, (tuple, list)):
        return _quantity_from_rgba(color)
    return None


def _quantity_from_rgba(values: Any) -> Any:
    from OCP.Quantity import Quantity_ColorRGBA

    floats = [max(0.0, min(1.0, float(c))) for c in values]
    if len(floats) == 3:
        floats.append(1.0)
    elif len(floats) < 3:
        floats = [0.72, 0.72, 0.72, 1.0]
    else:
        floats = floats[:4]
    return Quantity_ColorRGBA(*floats)


def _set_label_name(label: Any, name: str | None) -> None:
    if not name or label is None or label.IsNull():
        return
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDataStd import TDataStd_Name

    TDataStd_Name.Set_s(label, TCollection_ExtendedString(str(name)))


def _set_label_color(color_tool: Any, label: Any, color: Any) -> None:
    quantity = _color_rgba_quantity(color)
    if quantity is None or label is None or label.IsNull():
        return
    from OCP.XCAFDoc import XCAFDoc_ColorType

    color_tool.SetColor(label, quantity, XCAFDoc_ColorType.XCAFDoc_ColorSurf)


def _child_loc(child: Any) -> Any:
    """Reach OCCT `TopLoc_Location` from a cq.Assembly child (`child.loc`)."""
    from OCP.TopLoc import TopLoc_Location

    loc = getattr(child, "loc", None)
    if loc is None:
        return TopLoc_Location()
    wrapped = getattr(loc, "wrapped", None)
    if isinstance(wrapped, TopLoc_Location):
        return wrapped
    # cq.Location has a `wrapped` attr that IS a TopLoc_Location in current
    # cadquery, but defensively fall back to identity.
    if wrapped is not None:
        return wrapped
    return TopLoc_Location()


def _shape_without_location(wrapped: Any) -> Any:
    """Return the OCCT shape stripped of its `TopLoc_Location` placement."""
    from OCP.TopLoc import TopLoc_Location

    located = getattr(wrapped, "Located", None)
    if not callable(located):
        return wrapped
    try:
        return located(TopLoc_Location())
    except Exception:  # pragma: no cover — defensive
        return wrapped


def _add_cq_assembly_to_doc(assembly: Any, doc: Any) -> Any:
    """Walk a `cq.Assembly` and register it (recursively) with the XCAF doc.

    Returns the root definition label. Mirrors the recursive descent in
    :func:`cadpy.step_export._create_bin_xcaf_doc` but works against the
    `cq.Assembly` API surface (`.children`, `.name`, `.loc`, `.color`, `.obj`).
    """
    from OCP.XCAFDoc import XCAFDoc_DocumentTool

    shape_tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    color_tool = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())

    # Memoize prototype labels by id() of the wrapped shape so repeated
    # references to the same Workplane re-use the same OCCT definition.
    leaf_prototypes: dict[int, Any] = {}

    def add_leaf_prototype(wrapped: Any) -> Any:
        key = id(wrapped)
        cached = leaf_prototypes.get(key)
        if cached is not None:
            return cached
        unlocated = _shape_without_location(wrapped)
        definition_label = shape_tool.AddShape(unlocated, False)
        leaf_prototypes[key] = definition_label
        return definition_label

    def walk(node: Any) -> Any:
        children = list(getattr(node, "children", []) or [])
        name = getattr(node, "name", None)
        color = getattr(node, "color", None)
        obj = getattr(node, "obj", None)

        # A node may carry BOTH children and its own obj (cq lets you stack
        # geometry on a parent). We treat any node with children as an
        # "assembly" node, and synthesize
        # an extra child for `obj` if present.
        if children or obj is None:
            definition_label = shape_tool.NewShape()
            _set_label_name(definition_label, name)
            _set_label_color(color_tool, definition_label, color)

            if obj is not None:
                # Inline the parent's own geometry as a synthetic child.
                obj_wrapped = _resolve_obj_wrapped(obj)
                if obj_wrapped is not None:
                    leaf_definition = add_leaf_prototype(obj_wrapped)
                    component_label = shape_tool.AddComponent(
                        definition_label,
                        leaf_definition,
                        _child_loc(node) if not children else _identity_location(),
                    )
                    _set_label_name(component_label, name)
                    _set_label_color(color_tool, component_label, color)

            for child in children:
                child_definition = walk(child)
                component_label = shape_tool.AddComponent(
                    definition_label,
                    child_definition,
                    _child_loc(child),
                )
                _set_label_name(component_label, getattr(child, "name", None))
                _set_label_color(color_tool, component_label, getattr(child, "color", None))
            return definition_label

        # Leaf: a single solid hanging off this node.
        obj_wrapped = _resolve_obj_wrapped(obj)
        if obj_wrapped is None:
            # Empty leaf — create an empty assembly label so the tree stays
            # consistent.
            definition_label = shape_tool.NewShape()
            _set_label_name(definition_label, name)
            return definition_label

        definition_label = add_leaf_prototype(obj_wrapped)
        # Decorate with this node's name/color on the prototype label.
        _set_label_name(definition_label, name)
        _set_label_color(color_tool, definition_label, color)
        return definition_label

    root_label = walk(assembly)
    shape_tool.UpdateAssemblies()
    return root_label


def _identity_location() -> Any:
    from OCP.TopLoc import TopLoc_Location

    return TopLoc_Location()


def _resolve_obj_wrapped(obj: Any) -> Any | None:
    if obj is None:
        return None
    val_fn = getattr(obj, "val", None)
    if callable(val_fn):
        try:
            val = val_fn()
        except Exception:  # pragma: no cover
            return None
        wrapped = getattr(val, "wrapped", None)
        if wrapped is not None:
            return wrapped
    wrapped = getattr(obj, "wrapped", None)
    return wrapped


def _create_xcaf_doc_for_cadquery(to_export: Any) -> Any:
    """Build a labeled XCAF doc from a `cq.Workplane`, `cq.Shape`, or
    `cq.Assembly`.
    """
    if _is_cadquery_assembly(to_export):
        doc = create_bin_xcaf_doc()
        _add_cq_assembly_to_doc(to_export, doc)
        return doc

    # Single shape (cq.Workplane / cq.Shape): add it as a sole top-level
    # shape (single top-level shape).
    from OCP.XCAFDoc import XCAFDoc_DocumentTool

    wrapped = _topods_from_cadquery(to_export)
    doc = create_bin_xcaf_doc()
    shape_tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    color_tool = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    label = shape_tool.AddShape(wrapped, False)

    # cq.Workplane has no .label or .color attribute by default, but if the
    # caller attached one we honor it.
    name = getattr(to_export, "label", None) or getattr(to_export, "name", None)
    _set_label_name(label, name)
    _set_label_color(color_tool, label, getattr(to_export, "color", None))

    shape_tool.UpdateAssemblies()
    return doc


def export_cadquery_step_scene(
    to_export: Any,
    output_path: Path,
    *,
    text_to_cad_entry_kind: str | None = None,
    source_path: str | None = None,
    source_fingerprint: str | None = None,
    source_hash: str | None = None,
) -> LoadedStepScene:
    """Write a STEP file from a CadQuery shape/assembly and return the
    materialized :class:`LoadedStepScene`.
    """
    doc = _create_xcaf_doc_for_cadquery(to_export)
    label = (
        getattr(to_export, "name", None)
        or getattr(to_export, "label", None)
    )
    return export_xcaf_doc_step_scene(
        doc,
        output_path,
        label=label,
        originating_system="cadquery",
        text_to_cad_entry_kind=text_to_cad_entry_kind,
        source_path=source_path,
        source_fingerprint=source_fingerprint,
        source_hash=source_hash,
    )


def build_cadquery_step_scene(
    to_export: Any,
    output_path: Path,
    *,
    source_kind: str = "step",
    source_hash: str | None = None,
) -> LoadedStepScene:
    """Build a :class:`LoadedStepScene` from a CadQuery shape *without*
    writing the STEP file to disk.
    """
    doc = _create_xcaf_doc_for_cadquery(to_export)
    return load_step_scene_from_xcaf_doc(
        output_path,
        doc,
        source_kind=source_kind,
        source_hash=source_hash,
    )
