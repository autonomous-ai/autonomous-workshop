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
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

DAYDREAM_IDEA_KIND = "autonomous-workshop.daydream-idea"
DAYDREAM_OUTCOME_KIND = "autonomous-workshop.daydream-outcome"
IDEA_RELATIVE_PATH = "work/IDEA.json"
OUTCOME_FILE_NAME = "agent-outcome.json"
MAX_IDEA_FILE_BYTES = 64 * 1024
_LINE_BOUNDS = {
    "title": 60,
    "one_liner": 200,
    "held_form": 240,
    "before_after": 300,
}
_PARAGRAPH_BOUNDS = {
    "what_you_do": 600,
    "what_happens": 600,
    "why_it_is_new": 600,
}
_REQUIRED_KEYS = frozenset(
    (
        "schema_version",
        "kind",
        "title",
        "one_liner",
        "held_form",
        "before_after",
        "what_you_do",
        "what_happens",
        "why_it_is_new",
        "prior_art",
        "taste_fit",
        "parts_estimate",
        "keywords",
    )
)


def _line_problems(value: Any, label: str, maximum: int, *, allow_newlines: bool) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        return ["%s must be a non-empty string" % label]
    problems = []
    if len(value) > maximum:
        problems.append("%s is longer than %d characters" % (label, maximum))
    permitted = "\n" if allow_newlines else ""
    if any(ord(character) < 32 and character not in permitted for character in value):
        problems.append("%s contains control characters" % label)
    if value != value.strip():
        problems.append("%s has leading or trailing whitespace" % label)
    return problems


def idea_problems(raw: Any) -> list[str]:
    """Return every shape or bound problem in a parsed idea; empty means valid."""

    if not isinstance(raw, Mapping):
        return ["IDEA.json must be one JSON object"]
    problems = []
    missing = sorted(_REQUIRED_KEYS - set(raw))
    unknown = sorted(set(raw) - _REQUIRED_KEYS)
    if missing:
        problems.append("missing keys: %s" % ", ".join(missing))
    if unknown:
        problems.append("unknown keys: %s" % ", ".join(unknown))
    if problems:
        return problems
    if raw["schema_version"] != 1:
        problems.append("schema_version must be 1")
    if raw["kind"] != DAYDREAM_IDEA_KIND:
        problems.append("kind must be %s" % DAYDREAM_IDEA_KIND)
    for key, maximum in _LINE_BOUNDS.items():
        problems.extend(_line_problems(raw[key], key, maximum, allow_newlines=False))
    for key, maximum in _PARAGRAPH_BOUNDS.items():
        problems.extend(_line_problems(raw[key], key, maximum, allow_newlines=True))
    prior_art = raw["prior_art"]
    if not isinstance(prior_art, list) or not 2 <= len(prior_art) <= 5:
        problems.append("prior_art must list 2 to 5 entries")
    else:
        for index, entry in enumerate(prior_art):
            if not isinstance(entry, Mapping) or set(entry) != {"name", "how_this_differs"}:
                problems.append("prior_art[%d] needs exactly name and how_this_differs" % index)
                continue
            problems.extend(
                _line_problems(entry["name"], "prior_art[%d].name" % index, 80, allow_newlines=False)
            )
            problems.extend(
                _line_problems(
                    entry["how_this_differs"],
                    "prior_art[%d].how_this_differs" % index,
                    300,
                    allow_newlines=False,
                )
            )
    taste_fit = raw["taste_fit"]
    if not isinstance(taste_fit, Mapping) or set(taste_fit) != {"honors", "steers_clear_of"}:
        problems.append("taste_fit needs exactly honors and steers_clear_of")
    else:
        for key in ("honors", "steers_clear_of"):
            items = taste_fit[key]
            if not isinstance(items, list) or not 1 <= len(items) <= 5:
                problems.append("taste_fit.%s must list 1 to 5 lines" % key)
                continue
            for index, item in enumerate(items):
                problems.extend(
                    _line_problems(item, "taste_fit.%s[%d]" % (key, index), 200, allow_newlines=False)
                )
    parts = raw["parts_estimate"]
    if type(parts) is not int or not 1 <= parts <= 12:
        problems.append("parts_estimate must be an integer from 1 to 12")
    keywords = raw["keywords"]
    if (
        not isinstance(keywords, list)
        or not 3 <= len(keywords) <= 8
        or len(set(keywords)) != len(keywords)
        or any(not isinstance(keyword, str) or not _is_slug(keyword) for keyword in keywords)
    ):
        problems.append("keywords must be 3 to 8 unique lowercase slugs")
    return problems


def _is_slug(value: str) -> bool:
    if not 2 <= len(value) <= 32 or not (value[0].isdigit() or value[0].islower()):
        return False
    return all(character.isdigit() or character.islower() or character == "-" for character in value)


def finalize(run_root: Path, out=sys.stdout, err=sys.stderr) -> int:
    """Validate work/IDEA.json and write the marker; return an exit code."""

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
