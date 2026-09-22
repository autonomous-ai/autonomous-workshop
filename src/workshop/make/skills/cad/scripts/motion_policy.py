"""Resolve the operator's frozen Make options without loading CAD.

Two choices are frozen into the run root at creation and never move:
``check_motion`` and, for a correction, the carry policy. Schema 1 carries the
first alone and means "carry nothing"; schema 2 adds the second, written as
``carry_unchanged`` and, by the corrections created while the policy was
opt-in, as ``quick_fix``. A run created before the policy existed has no
schema-2 document and therefore reads exactly as it always did, even if its
tools are refreshed on resume.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def boolean(value: str) -> bool:
    if value.lower() not in ("true", "false"):
        raise argparse.ArgumentTypeError("expected true or false")
    return value.lower() == "true"


def _options_root() -> Path | None:
    """The run root whose frozen options govern, or None when not materialized."""
    # Resolve from immutable tool placement, never from the writable CAD project
    # (the host verifier runs against an isolated copy outside the run root).
    script = Path(__file__).resolve()
    if script.parents[3].name != ".agents":
        return None
    return script.parents[4]


def _payload(root: Path) -> dict | None:
    """The frozen options document, or None when the run predates the file."""
    path = root / "MAKE-OPTIONS.json"
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024:
        raise ValueError("invalid frozen Make options")
    payload = json.loads(path.read_bytes())
    if not isinstance(payload, dict):
        raise ValueError("invalid frozen Make options")
    version = payload.get("schema_version")
    if type(version) is not int or version not in (1, 2):
        raise ValueError("invalid frozen Make options")
    base = {"schema_version", "check_motion"}
    if version == 1:
        if set(payload) != base:
            raise ValueError("invalid frozen Make options")
    else:
        # Exactly one carry field, under either of its two names.
        names = {"carry_unchanged", "quick_fix"} & set(payload)
        if len(names) != 1 or set(payload) != base | names:
            raise ValueError("invalid frozen Make options")
        if type(payload[names.pop()]) is not bool:
            raise ValueError("invalid frozen Make options")
    if type(payload["check_motion"]) is not bool:
        raise ValueError("invalid frozen Make options")
    return payload


def enabled(option: bool | None = None) -> bool:
    if option is not None and type(option) is not bool:
        raise ValueError("check_motion must be boolean")
    root = _options_root()
    if root is None:
        return False if option is None else option
    payload = _payload(root)
    if payload is None:
        if not (root / ".workshop-product-run-root").is_file():
            return False if option is None else option
        # A deliberately refreshed legacy run retains its mandatory gate.
        selected = True
    else:
        selected = payload["check_motion"]
    if option is not None and option != selected:
        raise ValueError("--check-motion conflicts with frozen MAKE-OPTIONS.json")
    return selected


def carry_unchanged() -> bool:
    """Whether this run may carry an unchanged part's evidence forward.

    True for a correction, which is what schema 2 records; false for every run
    that has no source to carry from, and for every run created before the
    policy existed. The policy changes what a round may CARRY FORWARD, never
    what a gate accepts, so a wrong answer here costs time rather than
    correctness -- and the safe answer is the default.
    """
    root = _options_root()
    if root is None:
        return False
    payload = _payload(root)
    if payload is None:
        return False
    for key in ("carry_unchanged", "quick_fix"):
        if key in payload:
            return bool(payload[key])
    return False


#: The policy's original name, kept so a tool frozen into an older run resolves.
quick_fix = carry_unchanged
