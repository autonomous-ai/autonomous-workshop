"""Resolve the operator's frozen motion-check choice without loading CAD."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def boolean(value: str) -> bool:
    if value.lower() not in ("true", "false"):
        raise argparse.ArgumentTypeError("expected true or false")
    return value.lower() == "true"


def enabled(option: bool | None = None) -> bool:
    if option is not None and type(option) is not bool:
        raise ValueError("check_motion must be boolean")
    # Resolve from immutable tool placement, never from the writable CAD project
    # (the host verifier runs against an isolated copy outside the run root).
    script = Path(__file__).resolve()
    root = script.parents[4]
    materialized = script.parents[3].name == ".agents"
    if not materialized:
        return False if option is None else option
    path = root / "MAKE-OPTIONS.json"
    if not path.exists() and not path.is_symlink():
        if not (root / ".workshop-product-run-root").is_file():
            return False if option is None else option
        # A deliberately refreshed legacy run retains its mandatory gate.
        selected = True
    else:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024:
            raise ValueError("invalid frozen Make options")
        payload = json.loads(path.read_bytes())
        if (not isinstance(payload, dict)
                or set(payload) != {"schema_version", "check_motion"}
                or type(payload["schema_version"]) is not int
                or payload["schema_version"] != 1
                or type(payload["check_motion"]) is not bool):
            raise ValueError("invalid frozen Make options")
        selected = payload["check_motion"]
    if option is not None and option != selected:
        raise ValueError("--check-motion conflicts with frozen MAKE-OPTIONS.json")
    return selected
