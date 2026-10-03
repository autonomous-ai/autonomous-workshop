#!/usr/bin/env python3
"""Where a Workshop run keeps its workspace and its Claude Code transcripts.

    uv run python runpaths.py <wish-id>     # prints workspace, make dir, transcripts

No path is hard-coded: the Workshop home comes from Workshop itself
(`WORKSHOP_HOME`, `XDG_DATA_HOME`, or the platform default), and the
transcripts from Claude Code's own layout under `CLAUDE_CONFIG_DIR` (default
`~/.claude`): `projects/<the workspace path, every character other than a
letter or digit replaced by '-'>`.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Mapping, Optional


def workshop_home(environment: Optional[Mapping[str, str]] = None) -> Path:
    try:
        from workshop.runtime.package_data import default_workshop_home
    except ImportError as exc:  # pragma: no cover - only outside the repo venv
        raise SystemExit(
            "cannot import workshop; run this with `uv run python` from the "
            "Workshop checkout, or pass --workspace"
        ) from exc
    return default_workshop_home(environment)


def run_workspace(wish_id: str, environment: Optional[Mapping[str, str]] = None) -> Path:
    return workshop_home(environment) / "runs" / wish_id / "workspace"


def make_dir(workspace: Path) -> Path:
    return Path(workspace) / "artifacts" / "make"


def claude_project_dir(workspace: Path, environment: Optional[Mapping[str, str]] = None) -> Path:
    values = os.environ if environment is None else environment
    config = Path(values.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude").expanduser()
    return config / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(Path(workspace)))


def resolve_workspace(wish_id: Optional[str], workspace: Optional[str]) -> Path:
    if workspace:
        return Path(workspace).expanduser()
    if not wish_id:
        raise SystemExit("give a wish id or --workspace")
    return run_workspace(wish_id)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: runpaths.py <wish-id>")
    space = run_workspace(sys.argv[1])
    print(f"workspace={space}")
    print(f"make={make_dir(space)}")
    print(f"transcripts={claude_project_dir(space)}")
