#!/usr/bin/env python3
"""Build deterministic design-reference indexes from upstream source archives."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Iterable


BATCH_RE = re.compile(r"(?:^|/)(\d{2})_([^/]+)/batch_(\d{3})\.py$")
DESCRIPTION_RE = re.compile(r"^\s*#\s*Description:\s*(.+?)\s*$")


def _operation_range(bucket: str) -> tuple[int, int | None]:
    if bucket.endswith("plus"):
        return int(bucket.removesuffix("plus")), None
    if "to" in bucket:
        low, high = bucket.removesuffix("ops").split("to", 1)
        return int(low), int(high)
    value = int(bucket.removesuffix("ops"))
    return value, value


def _description_before(lines: list[str], lineno: int) -> str:
    for line in reversed(lines[max(0, lineno - 5) : lineno - 1]):
        match = DESCRIPTION_RE.match(line)
        if match:
            return match.group(1)
        if line.strip() and not line.lstrip().startswith("#"):
            break
    return ""


def _models_metadata(tree: ast.Module) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "MODELS" for target in node.targets):
            continue
        if not isinstance(node.value, ast.Dict):
            raise ValueError("MODELS must be a literal dictionary")
        for key_node, value_node in zip(node.value.keys, node.value.values):
            if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
                continue
            if not isinstance(value_node, ast.Dict):
                continue
            values: dict[str, float] = {}
            for field_node, item_node in zip(value_node.keys, value_node.values):
                if not isinstance(field_node, ast.Constant) or field_node.value not in {"volume", "area"}:
                    continue
                value = ast.literal_eval(item_node)
                if not isinstance(value, (int, float)):
                    raise ValueError(f"{key_node.value}.{field_node.value} is not numeric")
                values[str(field_node.value)] = float(value)
            result[key_node.value] = values
    return result


def parse_batch(source_id: str, source_path: str, data: bytes) -> list[dict[str, Any]]:
    """Parse one upstream batch without importing or executing CAD code."""

    text = data.decode("utf-8")
    tree = ast.parse(text, filename=source_path)
    match = BATCH_RE.search(source_path)
    if not match:
        raise ValueError(f"Unsupported batch path: {source_path}")
    bucket = match.group(2)
    operation_min, operation_max = _operation_range(bucket)
    metadata = _models_metadata(tree)
    lines = text.splitlines()
    contact_sheet_path = source_path.removesuffix(".py") + "_contact_sheet.png"

    records: list[dict[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith("model_"):
            continue
        function_source = ast.get_source_segment(text, node)
        if function_source is None:
            raise ValueError(f"Could not extract {node.name} from {source_path}")
        doc = (ast.get_docstring(node, clean=True) or "").strip()
        title = doc.removeprefix("Model:").strip() if doc.startswith("Model:") else doc
        expected = metadata.get(node.name, {})
        records.append(
            {
                "id": f"{source_id}/{node.name}",
                "function": node.name,
                "title": title,
                "description": _description_before(lines, node.lineno),
                "operationBucket": bucket,
                "operationMin": operation_min,
                "operationMax": operation_max,
                "sourcePath": source_path,
                "contactSheetPath": contact_sheet_path,
                "position": len(records),
                "volume": expected.get("volume"),
                "area": expected.get("area"),
                "functionSha256": hashlib.sha256(function_source.rstrip().encode("utf-8")).hexdigest(),
            }
        )
    return records


def records_from_tar(archive: tarfile.TarFile, source_id: str) -> list[dict[str, Any]]:
    """Read all supported batches directly from an archive without extraction."""

    members = [member for member in archive.getmembers() if member.isfile() and BATCH_RE.search(member.name)]
    records: list[dict[str, Any]] = []
    for member in sorted(members, key=lambda item: item.name):
        match = BATCH_RE.search(member.name)
        assert match is not None
        source_path = member.name[match.start() :].lstrip("/")
        stream = archive.extractfile(member)
        if stream is None:
            raise ValueError(f"Could not read {member.name}")
        records.extend(parse_batch(source_id, source_path, stream.read()))
    return records


def records_from_tree(root: Path, source_id: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(root.glob("[0-9][0-9]_*/batch_*.py")):
        records.extend(parse_batch(source_id, path.relative_to(root).as_posix(), path.read_bytes()))
    return records


def validate_records(records: Iterable[dict[str, Any]], expected_count: int | None = None) -> list[dict[str, Any]]:
    materialized = list(records)
    ids = [str(record["id"]) for record in materialized]
    if len(ids) != len(set(ids)):
        raise ValueError("Catalog contains duplicate ids")
    if expected_count is not None and len(materialized) != expected_count:
        raise ValueError(f"Expected {expected_count} records, found {len(materialized)}")
    if any(not record.get("description") for record in materialized):
        missing = next(record["id"] for record in materialized if not record.get("description"))
        raise ValueError(f"Catalog record has no description: {missing}")
    for record in materialized:
        function = str(record.get("function") or "")
        if not re.fullmatch(r"model_[A-Za-z0-9_]+", function):
            raise ValueError(f"Unsafe model function in catalog: {function!r}")
        source_path = str(record.get("sourcePath") or "")
        if BATCH_RE.fullmatch(source_path) is None:
            raise ValueError(f"Unsafe source path in catalog: {source_path!r}")
        expected_sheet = source_path.removesuffix(".py") + "_contact_sheet.png"
        if record.get("contactSheetPath") != expected_sheet:
            raise ValueError(f"Unexpected contact sheet path for {record['id']}")
        if re.fullmatch(r"[0-9a-f]{64}", str(record.get("functionSha256") or "")) is None:
            raise ValueError(f"Invalid function hash for {record['id']}")
    return materialized


def write_jsonl(records: Iterable[dict[str, Any]], path: Path) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    materialized = list(records)
    payload = b"".join(
        json.dumps(record, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
        for record in materialized
    )
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    temporary.replace(path)
    return {
        "path": str(path),
        "recordCount": len(materialized),
        "byteSize": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def extract_function(data: bytes, function_name: str) -> str:
    """Return module imports plus one selected model as a reference-only excerpt."""

    text = data.decode("utf-8")
    tree = ast.parse(text)
    imports = [
        ast.get_source_segment(text, node)
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    function = next(
        (node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == function_name),
        None,
    )
    if function is None:
        raise ValueError(f"Function {function_name!r} not found in downloaded batch")
    function_source = ast.get_source_segment(text, function)
    if function_source is None:
        raise ValueError(f"Could not extract function {function_name!r}")
    return "\n".join(item for item in imports if item) + "\n\n\n" + function_source.rstrip() + "\n"
