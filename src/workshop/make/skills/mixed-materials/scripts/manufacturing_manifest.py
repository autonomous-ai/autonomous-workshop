#!/usr/bin/env python3
"""Validate Make's internal, versioned mixed-material manufacturing handoff.

This standalone module uses only the standard library. It never runs CAD,
performs engineering judgments, purchases components, or advances a host gate.
The public projection API checks file identity and disclosure boundaries only.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import stat
from typing import Any, Mapping
from urllib.parse import unquote, urlsplit

MANIFEST_PATH = "internal/manufacturing.json"
KIND = "workshop.manufacturing"
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_FILE_BYTES = 95 * 1024 * 1024
MAX_ITEMS = 512
PROCESSES = frozenset({"3d-print", "laser-cut", "cnc", "cut-fold", "sew", "cut-to-length", "purchased", "handcraft"})
MATERIAL_FAMILIES = frozenset({"polymer", "paper", "paperboard", "wood", "elastomer", "foam", "textile", "metal", "glass", "ceramic", "composite", "mixed", "other"})
PUBLIC_SUFFIXES = frozenset({".step", ".stp", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".webm", ".pdf", ".md", ".txt", ".html"})
IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif"})
FORBIDDEN_SUFFIXES = frozenset({".stl", ".3mf", ".glb", ".gltf", ".dxf", ".dwg", ".gcode", ".nc"})
TOP_FIELDS = {"schema_version", "kind", "delivery", "assembly", "components", "stock", "consumables", "tools", "assembly_steps", "public_assets"}
ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
ASSEMBLY_NODE_ID = re.compile(r"^o[1-9][0-9]*(?:\.[1-9][0-9]*)*$")


class ManufacturingManifestError(ValueError):
    """The declared manufacturing handoff is malformed or not byte-exact."""


def _error(message: str) -> None:
    raise ManufacturingManifestError(message)


def _object(value: Any, label: str, fields: set[str], optional: set[str] | None = None) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not fields <= set(value) or set(value) - fields - (optional or set()):
        _error(f"{label} has invalid fields")
    return value


def _text(value: Any, label: str, maximum: int = 4000) -> str:
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= maximum or any(ord(c) < 32 and c not in "\n\t" for c in value):
        _error(f"{label} must be bounded non-empty text")
    return value


def _id(value: Any, label: str) -> str:
    if not isinstance(value, str) or ID.fullmatch(value) is None:
        _error(f"{label} must be a stable lowercase identifier")
    return value


def _list(value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list) or not int(nonempty) <= len(value) <= MAX_ITEMS:
        _error(f"{label} must be a bounded {'non-empty ' if nonempty else ''}list")
    return value


def _number(value: Any, label: str, *, integer: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0 or value > 1e12 or not math.isfinite(value) or (integer and not isinstance(value, int)):
        _error(f"{label} must be a positive {'integer' if integer else 'finite number'}")
    return value


def _path(value: Any, label: str) -> PurePosixPath:
    if not isinstance(value, str) or len(value) > 1024 or any(ord(c) < 32 or ord(c) == 127 for c in value) or "\\" in value:
        _error(f"{label} must be a safe relative path")
    pure = PurePosixPath(value)
    if not value or pure.is_absolute() or pure.as_posix() != value or any(part in (".", "..") for part in pure.parts) or not pure.parts:
        _error(f"{label} must be a safe relative path")
    if pure.suffix.casefold() in FORBIDDEN_SUFFIXES:
        _error(f"{label}: STEP is the only supported geometry deliverable; mesh, DXF and CAM files are unsupported")
    return pure


def _root(product_root: Path) -> Path:
    root = Path(product_root)
    if root.is_symlink() or not root.is_dir():
        _error("product root must be a real directory")
    return root.resolve(strict=True)


def _regular_bytes(root: Path, relative: str, label: str, *, maximum: int = MAX_FILE_BYTES) -> bytes:
    pure = _path(relative, label)
    path = root
    try:
        for index, part in enumerate(pure.parts):
            path = path / part
            status = path.lstat()
            if stat.S_ISLNK(status.st_mode) or (index < len(pure.parts) - 1 and not stat.S_ISDIR(status.st_mode)):
                _error(f"{label} contains a symlink or non-directory")
        if not stat.S_ISREG(status.st_mode) or not 1 <= status.st_size <= maximum:
            _error(f"{label} must be a bounded non-empty regular file")
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            content = stream.read(maximum + 1)
        after = path.lstat()
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
        if identity(status) != identity(opened) or identity(status) != identity(after) or len(content) != status.st_size:
            _error(f"{label} changed while being read")
        return content
    except OSError as exc:
        raise ManufacturingManifestError(f"{label} is unavailable") from exc


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _error(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    _error(f"non-finite JSON value: {value}")


def _json(content: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(content.decode("utf-8"), object_pairs_hook=_strict_pairs, parse_constant=_reject_constant)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ManufacturingManifestError(f"{label} must be strict UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        _error(f"{label} must be a JSON object")
    return value


def _binding(value: Any, label: str) -> Mapping[str, str]:
    row = _object(value, label, {"path", "sha256"})
    _path(row["path"], label)
    if not isinstance(row["sha256"], str) or SHA256.fullmatch(row["sha256"]) is None:
        _error(f"{label} sha256 is invalid")
    return row


def _bound_file(root: Path, value: Any, label: str, *, maximum: int = MAX_FILE_BYTES) -> bytes:
    row = _binding(value, label)
    content = _regular_bytes(root, row["path"], label, maximum=maximum)
    if hashlib.sha256(content).hexdigest() != row["sha256"]:
        _error(f"{label} sha256 differs from the actual file")
    return content


def read_manifest(product_root: Path, product: Mapping[str, Any]) -> dict[str, Any] | None:
    """Read only an explicitly opted-in, hash-bound version 1 manifest.

    Missing marker preserves legacy behavior. A malformed or partial marker
    never silently becomes a legacy product.
    """
    if not isinstance(product, Mapping):
        _error("product must be an object")
    if "manufacturing" not in product:
        return None
    marker = _object(product["manufacturing"], "manufacturing binding", {"schema_version", "manifest_path", "manifest_sha256"})
    if type(marker["schema_version"]) is not int or marker["schema_version"] != 1 or marker["manifest_path"] != MANIFEST_PATH:
        _error("manufacturing binding must name schema version 1 and internal/manufacturing.json")
    content = _bound_file(_root(product_root), {"path": marker["manifest_path"], "sha256": marker["manifest_sha256"]}, "manufacturing manifest", maximum=MAX_JSON_BYTES)
    document = _json(content, "manufacturing manifest")
    _object(document, "manufacturing manifest", TOP_FIELDS)
    if type(document["schema_version"]) is not int or document["schema_version"] != 1 or document["kind"] != KIND or document["delivery"] != "assembled-product":
        _error("manufacturing manifest identity must be version 1 workshop.manufacturing / assembled-product")
    return document


def _assembly_bindings(document: Mapping[str, Any]) -> Mapping[str, Any]:
    assembly = _object(document["assembly"], "assembly", {"step", "occurrences"})
    step = _binding(assembly["step"], "complete assembly STEP")
    occurrence = _binding(assembly["occurrences"], "assembly occurrences")
    if PurePosixPath(step["path"]).suffix.casefold() not in (".step", ".stp"):
        _error("complete assembly must be STEP")
    if not occurrence["path"].startswith("internal/") or not occurrence["path"].endswith(".json") or occurrence["path"] == MANIFEST_PATH:
        _error("assembly occurrence descriptor must be an internal JSON file")
    return assembly


def _public_paths(root: Path, document: Mapping[str, Any], product: Mapping[str, Any]) -> tuple[str, ...]:
    assembly = _assembly_bindings(document)
    paths: list[str] = []
    image_found = False
    assembly_found = False
    documents: list[tuple[PurePosixPath, bytes]] = []
    for item in _list(document["public_assets"], "public_assets", nonempty=True):
        row = _binding(item, "public asset")
        pure = _path(row["path"], "public asset")
        if pure.parts[0] != "public" or len(pure.parts) < 2 or any(part.startswith(".") for part in pure.parts) or pure.suffix.casefold() not in PUBLIC_SUFFIXES:
            _error("public assets must be consumer display/document files beneath public/; source, JSON and internal files are private")
        if row["path"] in paths:
            _error("duplicate public asset path")
        if row["sha256"] == product["manufacturing"]["manifest_sha256"]:
            _error("internal manufacturing manifest cannot be disguised as a public asset")
        content = _bound_file(root, row, "public asset")
        _public_content(content, pure.suffix.casefold())
        if pure.suffix.casefold() in (".md", ".txt", ".html"):
            documents.append((pure, content))
        paths.append(row["path"])
        image_found |= pure.suffix.casefold() in IMAGE_SUFFIXES
        if pure.suffix.casefold() in (".step", ".stp"):
            if row["sha256"] != assembly["step"]["sha256"]:
                _error("public STEP must depict the complete assembly, not a production part")
            assembly_found = True
    if not assembly_found or not image_found:
        _error("public_assets must contain the complete assembled STEP and a finished-product image")
    for pure, content in documents:
        _public_document_links(pure, content.decode("utf-8"), set(paths))
    return tuple(paths)


def _public_document_links(path: PurePosixPath, text: str, public_paths: set[str]) -> None:
    """Resolve document resource links against the explicit public inventory."""
    links = re.findall(r"\b(?:src|href|poster|data|action)\s*=\s*[\"']([^\"']*)[\"']", text, re.IGNORECASE)
    links += re.findall(r"\]\(\s*<?([^\s)>]+)", text)
    links += re.findall(r"^\s*\[[^\]]+\]:\s*<?([^\s>]+)", text, re.MULTILINE)
    links += re.findall(r"url\(\s*[\"']?([^\s\"')]+)", text, re.IGNORECASE)
    # Active code can retrieve unlisted files or embed source; public pages in
    # this contract are static customer content, not executable applications.
    if re.search(r"<\s*(?:script|iframe|object|embed)\b|\bon[a-z]+\s*=", text, re.IGNORECASE):
        _error("public customer documents must not contain executable content")
    for link in links:
        decoded = unquote(link)
        try:
            parsed = urlsplit(decoded)
        except ValueError as exc:
            raise ManufacturingManifestError("public document link is malformed") from exc
        if parsed.scheme or parsed.netloc:
            if parsed.scheme != "https" or not parsed.hostname or parsed.username is not None or parsed.password is not None:
                _error("public document external links must use HTTPS without credentials")
            continue
        if not parsed.path:
            continue
        if "\\" in parsed.path or parsed.path.startswith("/"):
            _error("public document links must stay within the public asset inventory")
        resolved = posixpath.normpath(posixpath.join(path.parent.as_posix(), parsed.path))
        if resolved not in public_paths:
            _error("public document links must reference an explicitly allowlisted public asset")


def _public_content(content: bytes, suffix: str) -> None:
    """Reject obvious file-type disguises; this does not review customer copy."""
    signatures = {
        ".png": content.startswith(b"\x89PNG\r\n\x1a\n"),
        ".jpg": content.startswith(b"\xff\xd8\xff"),
        ".jpeg": content.startswith(b"\xff\xd8\xff"),
        ".gif": content.startswith((b"GIF87a", b"GIF89a")),
        ".webp": content.startswith(b"RIFF") and content[8:12] == b"WEBP",
        ".pdf": content.startswith(b"%PDF-"),
        ".mp4": content[4:8] == b"ftyp",
        ".webm": content.startswith(b"\x1a\x45\xdf\xa3"),
        ".step": content.lstrip().startswith(b"ISO-10303-21;"),
        ".stp": content.lstrip().startswith(b"ISO-10303-21;"),
    }
    if suffix in signatures and not signatures[suffix]:
        _error("public asset content does not match its declared file format")
    if suffix in (".md", ".txt", ".html"):
        try:
            text = content.decode("utf-8")
        except UnicodeError as exc:
            raise ManufacturingManifestError("public document must be UTF-8") from exc
        if "\x00" in text or re.search(r"(?:^|[\s\"'(=/])(?:internal/|\.\./|file:)", text, re.IGNORECASE):
            _error("public document references private or parent-relative content")


def public_asset_paths(product_root: Path, product: Mapping[str, Any]) -> tuple[str, ...] | None:
    """Return only byte-bound public assets, without running Make validation.

    In particular this API does not check component engineering, print scope,
    production-source files, stock or assembly instructions.
    """
    document = read_manifest(product_root, product)
    if document is None:
        return None
    return _public_paths(_root(product_root), document, product)


def _identifiers(value: Any, label: str, known: set[str] | None = None, *, nonempty: bool = False) -> list[str]:
    result = [_id(item, label) for item in _list(value, label, nonempty=nonempty)]
    if len(result) != len(set(result)):
        _error(f"{label} contains duplicate IDs")
    if known is not None and set(result) - known:
        _error(f"{label} references unknown IDs: {', '.join(sorted(set(result) - known))}")
    return result


def _inventory(value: Any, label: str, *, tools: bool = False) -> set[str]:
    ids: set[str] = set()
    for row in _list(value, label):
        _object(row, label, {"id", "name", "specification"} | (set() if tools else {"quantity", "unit"}))
        item_id = _id(row["id"], label)
        if item_id in ids:
            _error(f"{label} has duplicate IDs")
        ids.add(item_id)
        _text(row["name"], f"{label} name", 300)
        _text(row["specification"], f"{label} specification")
        if not tools:
            _number(row["quantity"], f"{label} quantity")
            _text(row["unit"], f"{label} unit", 40)
    return ids


def _occurrence_inventory(root: Path, assembly: Mapping[str, Any]) -> tuple[set[str], Mapping[str, Any]]:
    step_content = _bound_file(root, assembly["step"], "complete assembly STEP")
    descriptor_content = _bound_file(root, assembly["occurrences"], "assembly occurrence descriptor", maximum=MAX_JSON_BYTES)
    if step_content != _regular_bytes(root, "assembled.step", "canonical assembled.step"):
        _error("manufacturing assembly differs from canonical assembled.step")
    if descriptor_content != _regular_bytes(root, "assembled.step.json", "canonical assembled.step.json", maximum=MAX_JSON_BYTES):
        _error("manufacturing occurrences differ from canonical assembled.step.json")
    descriptor = _json(descriptor_content, "assembly occurrence descriptor")
    if descriptor.get("kind") != "assembly-package" or type(descriptor.get("schemaVersion")) is not int or descriptor["schemaVersion"] != 2 or descriptor.get("entryKind") != "assembly":
        _error("occurrences must describe a schemaVersion 2 CAD assembly-package")
    names: set[str] = set()
    for row in _list(descriptor.get("occurrences"), "assembly occurrences", nonempty=True):
        if not isinstance(row, dict):
            _error("assembly occurrence must be an object")
        name = _id(row.get("name"), "assembly occurrence name")
        if name in names:
            _error("assembly occurrence names must be unique")
        names.add(name)
    stats = descriptor.get("stats")
    if stats is not None:
        if not isinstance(stats, dict):
            _error("assembly occurrence stats must be an object")
        count = stats.get("occurrenceCount", len(names))
        if type(count) is not int or count != len(names):
            _error("assembly occurrenceCount differs from its occurrences")
    return names, descriptor


def _assembly_node_id(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 128 or ASSEMBLY_NODE_ID.fullmatch(value) is None:
        _error("assembly unit/node ID must be an exact CAD occurrence ID such as o1.2")
    return value


def _assembly_node_ids(value: Any, label: str) -> list[str]:
    result = [_assembly_node_id(item) for item in _list(value, label, nonempty=True)]
    if len(result) != len(set(result)):
        _error(f"{label} contains duplicate IDs")
    return result


def _assembly_unit_leaves(descriptor: Mapping[str, Any]) -> dict[str, set[str]]:
    """Resolve physical-unit subassemblies against the exact rendered leaf tree.

    This runs only for the optional physical-unit representation. Historical
    descriptors without hierarchy or occurrence IDs keep their original rules.
    """
    leaf_names: dict[str, str] = {}
    for row in descriptor["occurrences"]:
        node_id = _assembly_node_id(row.get("id"))
        if node_id in leaf_names:
            _error("assembly leaf occurrence IDs must be unique")
        leaf_names[node_id] = row["name"]
    assembly = descriptor.get("assembly")
    if not isinstance(assembly, Mapping) or not isinstance(assembly.get("root"), Mapping):
        _error("assembly_unit_ids require the exact CAD assembly hierarchy")
    seen: set[str] = set()
    units: dict[str, set[str]] = {}

    def walk(node: Any, depth: int, parent: str | None = None) -> set[str]:
        if depth > 64 or len(seen) >= MAX_ITEMS * 4:
            _error("assembly unit hierarchy exceeds its depth or node limit")
        if not isinstance(node, Mapping):
            _error("assembly unit hierarchy node must be an object")
        node_id = _assembly_node_id(node.get("id"))
        if node_id in seen:
            _error("assembly unit hierarchy contains duplicate node IDs")
        if parent is not None and node_id.rpartition(".")[0] != parent:
            _error("assembly unit hierarchy node ID differs from its parent path")
        seen.add(node_id)
        children = _list(node.get("children"), "assembly unit children")
        node_type = node.get("nodeType")
        declared = set(_assembly_node_ids(node.get("leafPartIds"), "assembly node leafPartIds"))
        if node_type == "part" and depth > 0:
            if children or node_id not in leaf_names or node.get("name") != leaf_names[node_id]:
                _error("assembly unit leaf differs from the rendered occurrence")
            leaves = {node_id}
        else:
            expected_type = "assembly" if depth == 0 else "subassembly"
            if node_type != expected_type or not children or node_id in leaf_names:
                _error("assembly unit hierarchy has an invalid assembly/subassembly node")
            leaves: set[str] = set()
            for child in children:
                child_leaves = walk(child, depth + 1, node_id)
                if leaves & child_leaves:
                    _error("assembly unit hierarchy overlaps leaf occurrences")
                leaves.update(child_leaves)
            if depth > 0:
                units[node_id] = {leaf_names[item] for item in leaves}
        if declared != leaves:
            _error("assembly node leafPartIds differ from its exact descendant leaves")
        return leaves

    if walk(assembly["root"], 0) != set(leaf_names):
        _error("assembly unit hierarchy must cover every rendered leaf exactly once")
    return units


def _files(root: Path, value: Any, label: str, *, nonempty: bool = False) -> list[str]:
    paths = []
    for row in _list(value, label, nonempty=nonempty):
        binding = _binding(row, label)
        pure = _path(binding["path"], label)
        if pure.parts[0] == "public" or binding["path"] == MANIFEST_PATH:
            _error(f"{label} must name internal production/evidence files, not public assets or the manifest itself")
        if binding["path"] in paths:
            _error(f"{label} contains duplicate file paths")
        _bound_file(root, binding, label)
        paths.append(binding["path"])
    return paths


def _production_part(component: Mapping[str, Any], files: list[str]) -> None:
    """Bind a colored printed unit to its production files, without building CAD."""
    grouped_print = component["process"] == "3d-print" and "assembly_unit_ids" in component
    if not grouped_print:
        if "production_part" in component:
            _error("production_part is supported only for grouped 3d-print components")
        return
    if "production_part" not in component:
        _error("grouped 3d-print components require production_part")
    production = _object(component["production_part"], "production_part", {"source_path", "step_path"})
    source = _path(production["source_path"], "production_part source_path")
    step = _path(production["step_path"], "production_part step_path")
    if not source.name.startswith("part_") or not source.name.endswith(".step.py") or source.name == "part_.step.py":
        _error("production_part source_path must name part_<role>.step.py")
    if step != source.with_suffix(""):
        _error("production_part step_path must name the production source's generated sibling STEP")
    sources = [path for path in files if path.endswith(".step.py")]
    if sources != [source.as_posix()]:
        _error("grouped 3d-print components require exactly one bound production source in component files")
    if step.as_posix() not in files:
        _error("production_part STEP must be bound in the same component files")
    # _files has checked both exact hashes. _print_scope checks the literal
    # PRINTABLE flag, source ownership and declared CAD scope for this source.


def _printable(root: Path, relative: str) -> bool | None:
    try:
        tree = ast.parse(_regular_bytes(root, relative, "CAD source", maximum=MAX_JSON_BYTES), filename=relative)
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise ManufacturingManifestError(f"CAD source is not valid Python: {relative}") from exc
    values: list[bool] = []
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        if any(isinstance(target, ast.Name) and target.id == "PRINTABLE" for target in targets):
            if not isinstance(node.value, ast.Constant) or type(node.value.value) is not bool:
                _error(f"{relative}: PRINTABLE must be an explicit literal True or False")
            values.append(node.value.value)
    if len(values) > 1:
        _error(f"{relative}: PRINTABLE must be declared once")
    return values[0] if values else None


def _print_scope(root: Path, components: list[dict[str, Any]], cad_project_path: str | None) -> None:
    print_sources: set[str] = set()
    nonprint_sources: set[str] = set()
    for component in components:
        sources = {row["path"] for row in component["files"] if row["path"].endswith(".step.py")}
        if component["process"] == "3d-print":
            if not sources:
                _error(f"printed component {component['id']} needs a printable .step.py source")
            if print_sources & sources:
                _error("a printable source must belong to one component definition; use occurrences for repeated parts")
            print_sources.update(sources)
            for source in sources:
                if _printable(root, source) is not True:
                    _error(f"printed component source {source} must explicitly declare PRINTABLE = True")
        else:
            nonprint_sources.update(sources)
            for source in sources:
                if _printable(root, source) is not False:
                    _error(f"nonprinted component source {source} must explicitly declare PRINTABLE = False")
    if print_sources & nonprint_sources:
        _error("the same source cannot be both printed and nonprinted")
    scan_root = root
    if cad_project_path is not None:
        pure = _path(cad_project_path, "CAD project path")
        scan_root = root.joinpath(*pure.parts)
        for index in range(1, len(pure.parts) + 1):
            ancestor = root.joinpath(*pure.parts[:index])
            if ancestor.is_symlink() or not ancestor.is_dir():
                _error("CAD project path contains a symlink or non-directory")
        if any(not (root / source).is_relative_to(scan_root) for source in print_sources | nonprint_sources):
            _error("component CAD entry lies outside the declared CAD project")
    for path in scan_root.rglob("*.step.py"):
        relative = path.relative_to(root).as_posix()
        if "__cadgen__" in path.parts or "__pycache__" in path.parts:
            continue
        declaration = _printable(root, relative)
        if declaration is True and relative not in print_sources:
            _error(f"printable source {relative} is absent from the manufacturing print subset")
        if relative not in print_sources and declaration is not False:
            _error(f"nonproduction/combined source {relative} must explicitly declare PRINTABLE = False")


def validate_manifest(product_root: Path, product: Mapping[str, Any], *, cad_project_path: str | None = None) -> dict[str, Any] | None:
    """Validate the complete internal manufacturing specification without CAD execution."""
    document = read_manifest(product_root, product)
    if document is None:
        return None
    root = _root(product_root)
    _public_paths(root, document, product)
    occurrence_names, descriptor = _occurrence_inventory(root, _assembly_bindings(document))
    assembly_units: dict[str, set[str]] | None = None
    stock_ids = _inventory(document["stock"], "stock")
    consumable_ids = _inventory(document["consumables"], "consumables")
    tool_ids = _inventory(document["tools"], "tools", tools=True)
    if stock_ids & consumable_ids or stock_ids & tool_ids or consumable_ids & tool_ids:
        _error("stock, consumable and tool IDs must be globally distinct")
    component_ids: set[str] = set()
    covered: set[str] = set()
    components = _list(document["components"], "components", nonempty=True)
    for component in components:
        _object(component, "component", {"id", "name", "material", "process", "quantity", "occurrences", "specification", "files", "stock_ids"}, {"sourcing", "dimensions_mm", "assembly_unit_ids", "production_part"})
        component_id = _id(component["id"], "component id")
        if component_id in component_ids or component_id in stock_ids | consumable_ids | tool_ids:
            _error("component IDs must be globally unique")
        component_ids.add(component_id)
        _text(component["name"], "component name", 300)
        _text(component["specification"], "component specification")
        material = _object(component["material"], "material", {"family", "specification"})
        if not isinstance(material["family"], str) or material["family"] not in MATERIAL_FAMILIES:
            _error("material family is unsupported")
        _text(material["specification"], "material specification")
        process = component["process"]
        if not isinstance(process, str) or process not in PROCESSES:
            _error("component process is unsupported")
        quantity = _number(component["quantity"], "component quantity", integer=True)
        occurrences = _identifiers(component["occurrences"], "component occurrences", occurrence_names, nonempty=True)
        if "assembly_unit_ids" in component:
            if process not in {"purchased", "3d-print"}:
                _error("assembly_unit_ids are supported only for purchased or 3d-print components")
            unit_ids = _assembly_node_ids(component["assembly_unit_ids"], "component assembly_unit_ids")
            if quantity != len(unit_ids):
                _error("component quantity must equal its assembly unit count")
            if assembly_units is None:
                assembly_units = _assembly_unit_leaves(descriptor)
            unit_occurrences: set[str] = set()
            for unit_id in unit_ids:
                if unit_id not in assembly_units:
                    _error("assembly_unit_ids must identify exact non-root CAD subassemblies")
                leaves = assembly_units[unit_id]
                if unit_occurrences & leaves:
                    _error("assembly units overlap leaf occurrences")
                unit_occurrences.update(leaves)
            if unit_occurrences != set(occurrences):
                _error("assembly units must exactly cover the component occurrences")
        elif quantity != len(occurrences):
            _error("component quantity must equal its assembly occurrence count")
        if covered & set(occurrences):
            _error("an assembly occurrence cannot belong to two components")
        covered.update(occurrences)
        _identifiers(component["stock_ids"], "component stock_ids", stock_ids, nonempty=process != "purchased")
        files = _files(root, component["files"], "component files", nonempty=process != "purchased")
        _production_part(component, files)
        if process == "purchased" and ("sourcing" not in component or "dimensions_mm" not in component):
            _error("purchased components require sourcing specifications and dimensions_mm")
        if "sourcing" in component:
            source = _object(component["sourcing"], "sourcing", {"url", "specification"}, {"part_number"})
            _text(source["specification"], "sourcing specification")
            _text(source["url"], "sourcing URL", 2000)
            try:
                parsed = urlsplit(source["url"])
                valid = parsed.scheme == "https" and bool(parsed.hostname) and parsed.username is None and parsed.password is None
            except ValueError:
                valid = False
            if not valid:
                _error("sourcing URL must be public HTTPS without credentials")
            if "part_number" in source:
                _text(source["part_number"], "sourcing part_number", 300)
        if "dimensions_mm" in component:
            dimensions = component["dimensions_mm"]
            if not isinstance(dimensions, dict) or not 1 <= len(dimensions) <= 32:
                _error("dimensions_mm must be a bounded non-empty named dimension map")
            for name, value in dimensions.items():
                _id(name, "dimension name")
                _number(value, "component dimension")
    if covered != occurrence_names:
        _error("components must cover the complete assembly exactly")
    _print_scope(root, components, cad_project_path)
    step_ids: set[str] = set()
    used_components: set[str] = set()
    for step in _list(document["assembly_steps"], "assembly_steps", nonempty=True):
        _object(step, "assembly step", {"id", "title", "instructions", "components", "consumables", "tools", "files"})
        step_id = _id(step["id"], "assembly step id")
        if step_id in step_ids or step_id in component_ids | stock_ids | consumable_ids | tool_ids:
            _error("assembly step IDs must be globally unique")
        step_ids.add(step_id)
        _text(step["title"], "assembly step title", 300)
        _text(step["instructions"], "assembly step instructions", 8000)
        used_components.update(_identifiers(step["components"], "assembly step components", component_ids, nonempty=True))
        _identifiers(step["consumables"], "assembly step consumables", consumable_ids)
        _identifiers(step["tools"], "assembly step tools", tool_ids)
        _files(root, step["files"], "assembly step files")
    if used_components != component_ids:
        _error("assembly steps must reference every component")
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("product_root", type=Path)
    parser.add_argument("--cad-project-path", "--cad-project", dest="cad_project")
    parser.add_argument("--public-assets", action="store_true", help="check only public file identity and disclosure")
    args = parser.parse_args()
    try:
        product = _json(_regular_bytes(_root(args.product_root), "product.json", "product.json", maximum=MAX_JSON_BYTES), "product.json")
        if args.public_assets:
            result = public_asset_paths(args.product_root, product)
            print(json.dumps({"public_assets": result}))
        else:
            result = validate_manifest(args.product_root, product, cad_project_path=args.cad_project)
            print(json.dumps({"status": "not-declared" if result is None else "passed", "component_count": 0 if result is None else len(result["components"])}))
        return 0
    except ManufacturingManifestError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
