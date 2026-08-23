#!/usr/bin/env python3
"""Bounded CREATE build/export/review gate.

``create-check <project | generator.py>`` is the production CREATE contract:

* one sandboxed ``scripts/cad`` build for each distinct source tree;
* deterministic solid/warning/artifact checks before visual review;
* one standard ``scripts/review`` pass, compacted into private QA montages;
* cached results for an unchanged source tree; and
* a hard, process-independent budget of distinct source attempts.

The attempt ledger and compact review montages live under ``.input/``.  That
directory survives for the duration of a worker claim but is excluded from the
published design snapshot.  The command intentionally owns orchestration only;
the existing cad and review launchers remain the geometry/rendering sources of
truth.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any


GATE = "create-check"
SCHEMA_VERSION = 1
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_REVIEW_TIMEOUT_S = 300.0
_STATE_RELATIVE_PATH = Path(".input") / "create-check" / "state.json"
_MONTAGE_RELATIVE_DIR = Path(".input") / "create-check" / "review"
_MONTAGE_ITEMS_PER_PAGE = 4

SCRIPTS_DIR = Path(__file__).resolve().parent

_SKIP_DIR_NAMES = frozenset({
    ".git",
    ".input",
    ".claude",
    ".idea",
    "__pycache__",
    ".pytest_cache",
})
_DERIVED_SUFFIXES = frozenset({
    ".step",
    ".stp",
    ".stl",
    ".glb",
    ".3mf",
    ".gcode",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".pyc",
})
_DERIVED_FILENAMES = frozenset({"_tree.json", "content.json"})


class CreateCheckError(RuntimeError):
    """A stable, user-source-addressable gate failure."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _max_attempts() -> int:
    raw = os.environ.get("CREATE_CHECK_MAX_ATTEMPTS", str(DEFAULT_MAX_ATTEMPTS))
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise CreateCheckError(
            "INVALID_CONFIGURATION",
            "CREATE_CHECK_MAX_ATTEMPTS must be an integer",
        ) from exc
    # The environment is an operator knob for reducing the canary budget, not
    # a way for an agent-owned Bash invocation to raise the production ceiling.
    if not 1 <= value <= DEFAULT_MAX_ATTEMPTS:
        raise CreateCheckError(
            "INVALID_CONFIGURATION",
            f"CREATE_CHECK_MAX_ATTEMPTS must be within 1..{DEFAULT_MAX_ATTEMPTS}",
        )
    return value


def _project_root(input_path: Path) -> Path:
    resolved = input_path.expanduser().resolve()
    if resolved.is_dir():
        return resolved
    return resolved.parent


def _is_source_file(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    if any(part in _SKIP_DIR_NAMES or part.endswith("_review") for part in relative.parts[:-1]):
        return False
    name = path.name.lower()
    if name in _DERIVED_FILENAMES or name.endswith(".step.json") or name.endswith(".stl.json"):
        return False
    if path.suffix.lower() in _DERIVED_SUFFIXES:
        return False
    return path.is_file() or path.is_symlink()


def source_fingerprint(input_path: Path) -> str:
    """Hash source/config bytes while excluding generated and private artifacts."""
    resolved = input_path.expanduser().resolve()
    if not resolved.exists():
        raise CreateCheckError("INPUT_NOT_FOUND", f"input not found: {resolved}")
    root = _project_root(resolved)
    # A single-file entrypoint can import sibling helpers. Hash the enclosing
    # project tree in both CLI forms so editing a helper can never return a
    # cached result for geometry that no longer matches the source.
    candidates = sorted(root.rglob("*"))
    files = [path for path in candidates if _is_source_file(path, root)]
    if not files:
        raise CreateCheckError(
            "NO_SOURCE_FILES",
            f"no source files found under {resolved}",
        )
    digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        try:
            data = (
                os.readlink(path).encode("utf-8")
                if path.is_symlink()
                else path.read_bytes()
            )
        except OSError as exc:
            raise CreateCheckError(
                "SOURCE_READ_FAILED",
                f"cannot read source file {path}: {exc}",
            ) from exc
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def _load_state(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"schema_version": SCHEMA_VERSION, "attempts": []}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CreateCheckError(
            "STATE_INVALID",
            "the private create-check attempt ledger is unreadable",
        ) from exc
    if not isinstance(raw, dict) or raw.get("schema_version") != SCHEMA_VERSION:
        raise CreateCheckError(
            "STATE_INVALID",
            "the private create-check attempt ledger has an unsupported schema",
        )
    attempts = raw.get("attempts")
    if not isinstance(attempts, list):
        raise CreateCheckError(
            "STATE_INVALID",
            "the private create-check attempt ledger has no valid attempts list",
        )
    return {"schema_version": SCHEMA_VERSION, "attempts": attempts}


def _write_state(path: Path, state: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(state, separators=(",", ":"), sort_keys=True),
            encoding="utf-8",
        )
        os.replace(temporary, path)
    except OSError as exc:
        raise CreateCheckError(
            "STATE_WRITE_FAILED",
            f"cannot persist the private create-check attempt ledger: {exc}",
        ) from exc


def _run_json(command: list[str], *, timeout_s: float) -> tuple[int, dict[str, Any]]:
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CreateCheckError(
            "TOOL_TIMEOUT",
            f"{Path(command[1]).name} exceeded {timeout_s:g}s",
        ) from exc
    lines = [line for line in (proc.stdout or "").splitlines() if line.strip()]
    if not lines:
        detail = " ".join((proc.stderr or "").split())[:500]
        raise CreateCheckError(
            "TOOL_PROTOCOL_ERROR",
            f"{Path(command[1]).name} produced no JSON output"
            + (f": {detail}" if detail else ""),
        )
    try:
        payload = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        raise CreateCheckError(
            "TOOL_PROTOCOL_ERROR",
            f"{Path(command[1]).name} returned invalid JSON",
        ) from exc
    if not isinstance(payload, dict):
        raise CreateCheckError(
            "TOOL_PROTOCOL_ERROR",
            f"{Path(command[1]).name} returned a non-object JSON value",
        )
    return proc.returncode, payload


def _blocking_warnings(build: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for warning in build.get("warnings") or []:
        if not isinstance(warning, dict):
            out.append({"kind": "unknown", "detail": str(warning), "severity": "warning"})
            continue
        if str(warning.get("severity", "warning")).lower() != "info":
            out.append({
                "part": str(warning.get("part", "")),
                "kind": str(warning.get("kind", "")),
                "detail": str(warning.get("detail", "")),
                "severity": str(warning.get("severity", "warning")),
            })
    return out


def _existing_file(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    path = Path(value)
    return str(path.resolve()) if path.is_file() else None


def _review_source_paths(review: dict[str, Any]) -> list[tuple[str, str]]:
    sources: list[tuple[str, str]] = []
    assembled = _existing_file(review.get("assembled_png"))
    if assembled:
        sources.append(("assembled", assembled))
    for item in review.get("renders") or []:
        if not isinstance(item, dict):
            continue
        path = _existing_file(item.get("png_path"))
        if path:
            sources.append((f"part:{item.get('part') or 'unnamed'}", path))
    for item in review.get("section_pngs") or []:
        if not isinstance(item, dict):
            continue
        path = _existing_file(item.get("png_path"))
        if path:
            sources.append((
                f"section:{item.get('part') or 'assembly'}:{item.get('axis') or '?'}",
                path,
            ))
    return sources


def _compose_review_montages(
    sources: list[tuple[str, str]],
    *,
    project_root: Path,
) -> list[str]:
    """Pack detailed renderer outputs into private, readable 2x2 contact sheets."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise CreateCheckError(
            "REVIEW_MONTAGE_UNAVAILABLE",
            "Pillow is unavailable; cannot create the bounded visual-review target",
        ) from exc

    output_dir = project_root / _MONTAGE_RELATIVE_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    for old in output_dir.glob("qa-*.png"):
        try:
            old.unlink()
        except OSError:
            pass

    tile_w, image_h, label_h = 820, 560, 34
    tile_h = image_h + label_h
    font = ImageFont.load_default()
    outputs: list[str] = []
    for page_index, start in enumerate(range(0, len(sources), _MONTAGE_ITEMS_PER_PAGE), 1):
        page = sources[start : start + _MONTAGE_ITEMS_PER_PAGE]
        cols = 1 if len(page) == 1 else 2
        rows = (len(page) + cols - 1) // cols
        canvas = Image.new("RGB", (cols * tile_w, rows * tile_h), (246, 247, 249))
        draw = ImageDraw.Draw(canvas)
        for index, (label, raw_path) in enumerate(page):
            try:
                with Image.open(raw_path) as opened:
                    image = opened.convert("RGB")
            except Exception as exc:
                raise CreateCheckError(
                    "REVIEW_IMAGE_INVALID",
                    f"cannot read review image {Path(raw_path).name}: {exc}",
                ) from exc
            image.thumbnail((tile_w - 20, image_h - 20))
            col, row = index % cols, index // cols
            x = col * tile_w + (tile_w - image.width) // 2
            y = row * tile_h + label_h + (image_h - image.height) // 2
            draw.text((col * tile_w + 12, row * tile_h + 10), label[:100], fill=(25, 30, 40), font=font)
            canvas.paste(image, (x, y))
        target = output_dir / f"qa-{page_index}.png"
        canvas.save(target, format="PNG", optimize=True)
        outputs.append(str(target.resolve()))
    return outputs


def _cached_result_is_intact(result: dict[str, Any]) -> bool:
    if result.get("status") != "PASS":
        return True
    build = result.get("build") or {}
    required = [
        build.get("step_path"),
        build.get("stl_path"),
        build.get("metadata_path"),
        *(
            path
            for part in build.get("parts") or []
            if isinstance(part, dict)
            for path in (part.get("step_path"), part.get("stl_path"))
        ),
        *((result.get("review") or {}).get("targets") or []),
    ]
    return bool(required) and all(_existing_file(value) for value in required)


def _attempt_summary(*, used: int, maximum: int) -> dict[str, int]:
    return {"used": used, "max": maximum, "remaining": max(0, maximum - used)}


def _failure(
    *,
    code: str,
    message: str,
    stage: str,
    source_sha256: str,
    attempts: dict[str, int],
    details: Any = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "gate": GATE,
        "schema_version": SCHEMA_VERSION,
        "status": "FAIL",
        "stage": stage,
        "source_sha256": source_sha256,
        "attempts": attempts,
        "error": {"code": code, "message": message},
        "next_action": (
            "Edit the source to address this exact failure, then rerun create-check. "
            "Do not repeat the command with unchanged source."
        ),
    }
    if details is not None:
        payload["details"] = details
    return payload


def _execute_attempt(
    input_path: Path,
    *,
    source_sha256: str,
    attempts: dict[str, int],
    wall_clock_s: float,
    review_timeout_s: float,
) -> tuple[dict[str, Any], int]:
    build_command = [
        sys.executable,
        str(SCRIPTS_DIR / "cad"),
        str(input_path),
        "--wall-clock-s",
        str(wall_clock_s),
    ]
    build_rc, build = _run_json(build_command, timeout_s=wall_clock_s + 30.0)
    if build_rc != 0 or not build.get("ok"):
        error = build.get("error") if isinstance(build.get("error"), dict) else {}
        return _failure(
            code=str(error.get("code") or "BUILD_FAILED"),
            message=str(error.get("message") or "the CAD build failed"),
            stage="build",
            source_sha256=source_sha256,
            attempts=attempts,
        ), 1
    try:
        volume_mm3 = float(build.get("volume_mm3") or 0)
    except (TypeError, ValueError):
        volume_mm3 = 0.0
    if (
        build.get("is_solid") is not True
        or not math.isfinite(volume_mm3)
        or volume_mm3 <= 0
    ):
        return _failure(
            code="INVALID_SOLID",
            message="the build did not produce a positive-volume solid",
            stage="validation",
            source_sha256=source_sha256,
            attempts=attempts,
            details={
                "is_solid": build.get("is_solid"),
                "volume_mm3": build.get("volume_mm3"),
            },
        ), 1
    blocking = _blocking_warnings(build)
    if blocking:
        return _failure(
            code="BLOCKING_GEOMETRY_WARNINGS",
            message=f"the build has {len(blocking)} blocking geometry warning(s)",
            stage="validation",
            source_sha256=source_sha256,
            attempts=attempts,
            details={"warnings": blocking[:20]},
        ), 1

    artifact_paths = {
        key: _existing_file(build.get(key))
        for key in ("step_path", "stl_path", "metadata_path")
    }
    missing_artifacts = [key for key, value in artifact_paths.items() if value is None]
    if missing_artifacts:
        return _failure(
            code="ARTIFACT_SET_INCOMPLETE",
            message="the build omitted required artifact files: " + ", ".join(missing_artifacts),
            stage="validation",
            source_sha256=source_sha256,
            attempts=attempts,
        ), 1

    expected_parts = build.get("parts") or []
    expected_part_names: list[str] = []
    missing_part_artifacts: list[str] = []
    part_artifacts: list[dict[str, str]] = []
    for index, part in enumerate(expected_parts):
        if not isinstance(part, dict):
            missing_part_artifacts.append(f"part[{index}]")
            continue
        name = str(part.get("name") or "").strip()
        step_path = _existing_file(part.get("step_path"))
        stl_path = _existing_file(part.get("stl_path"))
        if not name or not step_path or not stl_path:
            missing_part_artifacts.append(name or f"part[{index}]")
            continue
        expected_part_names.append(name)
        part_artifacts.append({
            "name": name,
            "step_path": step_path,
            "stl_path": stl_path,
        })
    if (
        missing_part_artifacts
        or len(expected_part_names) != len(expected_parts)
        or len(set(expected_part_names)) != len(expected_part_names)
    ):
        return _failure(
            code="PART_ARTIFACT_SET_INCOMPLETE",
            message="the build omitted or duplicated a named part STEP/STL pair",
            stage="validation",
            source_sha256=source_sha256,
            attempts=attempts,
            details={"invalid_parts": missing_part_artifacts[:20]},
        ), 1

    review_command = [
        sys.executable,
        str(SCRIPTS_DIR / "review"),
        str(artifact_paths["metadata_path"]),
    ]
    review_rc, review = _run_json(review_command, timeout_s=review_timeout_s)
    if review_rc != 0 or not review.get("ok"):
        error = review.get("error") if isinstance(review.get("error"), dict) else {}
        return _failure(
            code=str(error.get("code") or "REVIEW_FAILED"),
            message=str(error.get("message") or "the standard review render failed"),
            stage="review",
            source_sha256=source_sha256,
            attempts=attempts,
        ), 1

    rendered_parts = review.get("renders") or []
    rendered_part_names = [
        str(item.get("part") or "").strip()
        for item in rendered_parts
        if isinstance(item, dict)
    ]
    sections = review.get("section_pngs") or []
    section_axes = {
        str(item.get("axis"))
        for item in sections
        if isinstance(item, dict) and item.get("png_path")
    }
    if (
        len(rendered_part_names) != len(rendered_parts)
        or sorted(rendered_part_names) != sorted(expected_part_names)
        or section_axes != {"x", "y", "z"}
    ):
        return _failure(
            code="REVIEW_SET_INCOMPLETE",
            message="the standard review omitted a named part or x/y/z cross-section",
            stage="review",
            source_sha256=source_sha256,
            attempts=attempts,
            details={
                "expected_part_renders": len(expected_part_names),
                "actual_part_renders": len(rendered_parts),
                "expected_part_names": expected_part_names,
                "actual_part_names": rendered_part_names,
                "section_axes": sorted(section_axes),
            },
        ), 1

    sources = _review_source_paths(review)
    expected_sources = 1 + len(review.get("renders") or []) + len(review.get("section_pngs") or [])
    if len(sources) != expected_sources or not _existing_file(review.get("cover_png")):
        return _failure(
            code="REVIEW_SET_INCOMPLETE",
            message="the standard review did not produce every required QA/cover image",
            stage="review",
            source_sha256=source_sha256,
            attempts=attempts,
            details={"expected_qa_images": expected_sources, "actual_qa_images": len(sources)},
        ), 1

    targets = _compose_review_montages(sources, project_root=_project_root(input_path))
    payload = {
        "gate": GATE,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "stage": "visual_review",
        "source_sha256": source_sha256,
        "attempts": attempts,
        # Keep this exact nested ok/path contract: GreenBank recognizes it as
        # a clean exported CREATE checkpoint. FAIL payloads deliberately omit it.
        "build": {
            "ok": True,
            "step_path": artifact_paths["step_path"],
            "stl_path": artifact_paths["stl_path"],
            "metadata_path": artifact_paths["metadata_path"],
            "is_solid": True,
            "volume_mm3": volume_mm3,
            "bbox": build.get("bbox"),
            "part_count": len(build.get("parts") or []),
            "parts": part_artifacts,
        },
        "review": {
            "mode": "standard-full",
            "source_image_count": len(sources),
            "targets": targets,
        },
        "next_action": (
            "Read each review.targets montage exactly once. If the geometry is visually "
            "correct and matches the approved plan, finish immediately without another "
            "build, review, probe, or source edit. If it is wrong, make one focused source "
            "fix and rerun create-check."
        ),
    }
    return payload, 0


def run(
    input_path: Path,
    *,
    wall_clock_s: float,
    review_timeout_s: float,
) -> tuple[dict[str, Any], int]:
    resolved = input_path.expanduser().resolve()
    maximum = _max_attempts()
    source_sha256 = source_fingerprint(resolved)
    state_path = _project_root(resolved) / _STATE_RELATIVE_PATH
    state = _load_state(state_path)
    attempts_list = state["attempts"]

    prior_index = next(
        (
            index
            for index, item in enumerate(attempts_list)
            if isinstance(item, dict) and item.get("source_sha256") == source_sha256
        ),
        None,
    )
    if prior_index is not None:
        prior = attempts_list[prior_index]
        result = prior.get("result") if isinstance(prior.get("result"), dict) else None
        if result is not None and _cached_result_is_intact(result):
            cached = dict(result)
            cached["cached"] = True
            cached["attempts"] = _attempt_summary(used=len(attempts_list), maximum=maximum)
            return cached, 0 if cached.get("status") == "PASS" else 1

    if prior_index is None and len(attempts_list) >= maximum:
        return _failure(
            code="ATTEMPT_BUDGET_EXHAUSTED",
            message=(
                f"create-check already evaluated {maximum} distinct source versions; "
                "stop instead of starting another open-ended repair loop"
            ),
            stage="budget",
            source_sha256=source_sha256,
            attempts=_attempt_summary(used=len(attempts_list), maximum=maximum),
        ), 1

    used = len(attempts_list) + (0 if prior_index is not None else 1)
    attempts = _attempt_summary(used=used, maximum=maximum)
    try:
        result, exit_code = _execute_attempt(
            resolved,
            source_sha256=source_sha256,
            attempts=attempts,
            wall_clock_s=wall_clock_s,
            review_timeout_s=review_timeout_s,
        )
    except CreateCheckError as exc:
        result = _failure(
            code=exc.code,
            message=exc.message,
            stage="tool",
            source_sha256=source_sha256,
            attempts=attempts,
        )
        exit_code = 1

    record = {"source_sha256": source_sha256, "result": result}
    if prior_index is None:
        attempts_list.append(record)
    else:
        attempts_list[prior_index] = record
    _write_state(state_path, state)
    return result, exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=GATE,
        description=(
            "Build, validate, export, and compactly review one CREATE source version. "
            "Unchanged source is never rebuilt; distinct attempts are hard-capped."
        ),
    )
    parser.add_argument("input", type=Path, help="CadQuery project directory or generator .py")
    parser.add_argument(
        "--wall-clock-s",
        type=float,
        default=float(os.environ.get("CADCODE_WALL_CLOCK_S", "30")),
        help="sandboxed CAD compiler wall-clock budget",
    )
    parser.add_argument(
        "--review-timeout-s",
        type=float,
        default=DEFAULT_REVIEW_TIMEOUT_S,
        help="outer timeout for the standard review renderer",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        if (
            not math.isfinite(args.wall_clock_s)
            or not math.isfinite(args.review_timeout_s)
            or args.wall_clock_s <= 0
            or args.review_timeout_s <= 0
        ):
            raise CreateCheckError("INVALID_ARGUMENT", "timeouts must be finite and positive")
        payload, exit_code = run(
            args.input,
            wall_clock_s=args.wall_clock_s,
            review_timeout_s=args.review_timeout_s,
        )
    except CreateCheckError as exc:
        payload = {
            "gate": GATE,
            "schema_version": SCHEMA_VERSION,
            "status": "FAIL",
            "stage": "input",
            "error": {"code": exc.code, "message": exc.message},
        }
        exit_code = 2
    print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
