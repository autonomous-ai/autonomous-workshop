#!/usr/bin/env python3
"""Validate one packet-bound pre-render Concept without effects or writes."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from workshop.concept import ConceptProvenance, evaluate_concept_brief, load_pre_render_concept
from workshop.errors import ArtifactError, ContractError
from workshop.invent.native import NativeInvented
from workshop.match.native import InventorRoster, NativeMatchAssignment
from workshop.wish import Wish


SOURCE_PATHS = frozenset(
    ("brief.json", "derived_wish.json", "descriptor.json", "prompts.json", "research.json")
)
MAX_INPUT_BYTES = 8 * 1024 * 1024


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def safe_relative(value: Any, label: str) -> PurePosixPath:
    candidate = PurePosixPath(value) if isinstance(value, str) else PurePosixPath(".")
    if (
        not isinstance(value, str)
        or not value
        or value in (".", "..")
        or "\\" in value
        or candidate.is_absolute()
        or ".." in candidate.parts
        or candidate.as_posix() != value
    ):
        raise ContractError("%s must be a safe relative POSIX path" % label)
    return candidate


def read_regular(path: Path, label: str) -> bytes:
    before = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(before.st_mode):
        raise ArtifactError("%s must be a regular file" % label)
    content = path.read_bytes()
    after = path.lstat()
    if (
        (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
        != (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)
        or len(content) != before.st_size
    ):
        raise ArtifactError("%s changed while being read" % label)
    return content


def load_payload() -> dict[str, Any]:
    content = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if not content or len(content) > MAX_INPUT_BYTES:
        raise ContractError("Concept validator input is missing or oversized")
    value = json.loads(
        content.decode("utf-8"),
        object_pairs_hook=strict_object,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
    )
    expected = {
        "run_root",
        "concept_root",
        "wish",
        "assignment",
        "inventor_roster",
        "invented",
        "creative_source",
        "creative_source_hex",
        "creative_source_path",
        "creative_source_sha256",
        "round",
        "standing_concept_sha256",
        "revision_input_sha256",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise ContractError("Concept validator input fields are invalid")
    return value


def validate(payload: dict[str, Any]) -> dict[str, Any]:
    root = Path(payload["run_root"]).resolve(strict=True)
    if not root.is_dir():
        raise ArtifactError("Concept run root must be a directory")
    wish_binding = payload["wish"]
    if not isinstance(wish_binding, dict) or set(wish_binding) != {"path", "sha256"}:
        raise ContractError("Concept Wish binding fields are invalid")
    wish_relative = safe_relative(wish_binding["path"], "Concept Wish path")
    wish_content = read_regular(root.joinpath(*wish_relative.parts), "Concept Wish")
    if hashlib.sha256(wish_content).hexdigest() != wish_binding["sha256"]:
        raise ArtifactError("Concept Wish sha256 differs from its bytes")
    wish_value = json.loads(
        wish_content.decode("utf-8"),
        object_pairs_hook=strict_object,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
    )
    if not isinstance(wish_value, dict) or set(wish_value) != {
        "schema_version", "product_id", "objective", "constraints", "context"
    }:
        raise ContractError("Concept Wish fields are invalid")
    wish = Wish(**wish_value)

    assignment = NativeMatchAssignment.from_mapping(payload["assignment"])
    roster = InventorRoster.from_mapping(payload["inventor_roster"])
    assignment.assert_context(wish_sha256=wish_binding["sha256"], roster=roster)
    invented = NativeInvented.from_mapping(payload["invented"])
    invented.assert_context(assignment)
    expected_source = {
        "selected_inventor_id": assignment.selected_inventor_id,
        "ranking": [item.to_dict() for item in assignment.ranking],
        "concept": invented.to_dict()["concept"],
        "research": invented.to_dict()["research"],
    }
    if payload["creative_source"] != expected_source:
        raise ContractError("Concept creative source differs from assignment or Invented")
    try:
        source_content = bytes.fromhex(payload["creative_source_hex"])
        source_value = json.loads(
            source_content.decode("utf-8"),
            object_pairs_hook=strict_object,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("Concept creative source bytes are invalid") from exc
    if source_value != payload["creative_source"]:
        raise ContractError("Concept creative source bytes differ from parsed source")
    source_sha256 = hashlib.sha256(source_content).hexdigest()
    if source_sha256 != payload["creative_source_sha256"]:
        raise ContractError("Concept creative source sha256 is invalid")

    round_index = payload["round"]
    expected_root = "artifacts/concept/r%04d/concept" % round_index
    if payload["concept_root"] != expected_root:
        raise ContractError("Concept root is not canonical for its round")
    concept_relative = safe_relative(payload["concept_root"], "Concept root")
    concept_root = root.joinpath(*concept_relative.parts)
    root_identity = concept_root.lstat()
    if concept_root.is_symlink() or not stat.S_ISDIR(root_identity.st_mode):
        raise ArtifactError("Concept root must be a real directory")
    observed = set()
    for child in concept_root.iterdir():
        identity = child.lstat()
        if child.is_symlink() or not stat.S_ISREG(identity.st_mode):
            raise ArtifactError("Concept source entries must be regular files")
        observed.add(child.name)
    if observed != SOURCE_PATHS:
        raise ArtifactError("Concept root must contain exactly its five source files")

    provenance = ConceptProvenance(
        origin="invent",
        wish_sha256=wish_binding["sha256"],
        product_id=wish.product_id,
        objective=wish.objective,
        context=dict(wish.context),
        assignment_sha256=assignment.assignment_sha256,
        taste_sha256=assignment.selected_taste_sha256,
        blueprint_sha256=assignment.blueprint_sha256,
        invented_sha256=invented.invented_sha256,
        creative_source_path=payload["creative_source_path"],
        creative_source_sha256=source_sha256,
        round=round_index,
        standing_concept_sha256=payload["standing_concept_sha256"],
        revision_input_sha256=payload["revision_input_sha256"],
    )
    concept = load_pre_render_concept(root, provenance)
    concept.derived_wish.assert_context(wish)
    if concept.derived_wish.wish_sha256 != wish_binding["sha256"]:
        raise ContractError("derived Wish sha256 differs from the routed Wish")
    checks = dict(evaluate_concept_brief(concept, wish=wish))
    return {"checks": checks, "pre_render": concept.to_dict()}


def main() -> int:
    argparse.ArgumentParser().parse_args()
    try:
        result = validate(load_payload())
    except (ArtifactError, ContractError, OSError, UnicodeError, ValueError, TypeError) as exc:
        message = str(exc).replace("\n", " ")[:1000] or "Concept validation failed"
        sys.stdout.buffer.write(canonical_json({"error": message, "ok": False}))
        return 2
    sys.stdout.buffer.write(canonical_json({"ok": True, "result": result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
