#!/usr/bin/env python3
"""Run-local Daydream finalizer: validate ``work/IDEA.json`` and write the Goal marker.

The host copies this file into every daydream workspace.  The Inventor runs
it after writing its idea; it checks the file's shape and bounds, hashes the
exact bytes, and atomically writes ``agent-outcome.json``, which completes
the native Goal exactly as the product-stage finalizer does.  It does no
reasoning and cannot pass the host's novelty lint.  Standard library only:
it runs under whatever Python the Manager runtime provides.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

try:
    # The host copies schema.py beside this standalone finalizer under this
    # import name.  Package imports use the fallback in contributor tests.
    from daydream_schema import (  # type: ignore[import-not-found]
        DAYDREAM_IDEA_KIND,
        idea_problems,
    )
except ImportError:  # pragma: no cover - package import uses schema.py in this directory
    schema_path = Path(__file__).with_name("schema.py")
    schema_spec = importlib.util.spec_from_file_location("_workshop_daydream_schema", schema_path)
    if schema_spec is None or schema_spec.loader is None:
        raise
    schema_module = importlib.util.module_from_spec(schema_spec)
    schema_spec.loader.exec_module(schema_module)
    DAYDREAM_IDEA_KIND = schema_module.DAYDREAM_IDEA_KIND
    idea_problems = schema_module.idea_problems

DAYDREAM_OUTCOME_KIND = "autonomous-workshop.daydream-outcome"
IDEA_RELATIVE_PATH = "work/IDEA.json"
OUTCOME_FILE_NAME = "agent-outcome.json"
MAX_IDEA_FILE_BYTES = 64 * 1024


def finalize(run_root: Path, out=sys.stdout, err=sys.stderr) -> int:
    """Validate ``work/IDEA.json`` and write the outcome marker."""

    relative, checker, label = IDEA_RELATIVE_PATH, idea_problems, "idea"
    file_path = run_root / relative
    try:
        payload = file_path.read_bytes()
    except FileNotFoundError:
        print("finalize_daydream: %s is missing; write your %s first" % (relative, label), file=err)
        return 1
    except OSError as exc:
        print("finalize_daydream: cannot read %s: %s" % (relative, exc), file=err)
        return 1
    if len(payload) > MAX_IDEA_FILE_BYTES:
        print("finalize_daydream: %s exceeds %d bytes" % (relative, MAX_IDEA_FILE_BYTES), file=err)
        return 1
    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        print("finalize_daydream: %s is not valid UTF-8 JSON: %s" % (relative, exc), file=err)
        return 1
    problems = checker(raw)
    if problems:
        print("finalize_daydream: %s is not a valid %s:" % (relative, label), file=err)
        for problem in problems:
            print("  - %s" % problem, file=err)
        print("Fix the file and run the finalizer again.", file=err)
        return 1
    outcome = {
        "schema_version": 1,
        "kind": DAYDREAM_OUTCOME_KIND,
        "status": "ready",
        "idea_path": relative,
        "idea_bytes": len(payload),
        "idea_sha256": hashlib.sha256(payload).hexdigest(),
        "title": raw["title"],
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    outcome_path = run_root / OUTCOME_FILE_NAME
    temporary = run_root / (OUTCOME_FILE_NAME + ".tmp")
    encoded = (
        json.dumps(outcome, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")
    try:
        with open(temporary, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, outcome_path)
    except OSError as exc:
        print("finalize_daydream: cannot write %s: %s" % (OUTCOME_FILE_NAME, exc), file=err)
        return 1
    print(
        "finalize_daydream: %s is valid (%s, %d bytes); wrote %s. Mark the Goal complete and stop."
        % (relative, outcome["title"], len(payload), OUTCOME_FILE_NAME),
        file=out,
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="finalize_daydream.py",
        description="Validate work/IDEA.json and write agent-outcome.json to complete the Daydream Goal.",
    )
    parser.add_argument(
        "--run-root",
        default=".",
        help="the daydream workspace (default: the current directory)",
    )
    args = parser.parse_args(argv)
    return finalize(Path(args.run_root).resolve())


if __name__ == "__main__":
    sys.exit(main())
