"""Where a run's make_round guard hook lives, and how a launcher runs it.

ADR 0080: a new Codex or Claude Code run keeps a ``PreToolUse`` hook script
in its private host state. The Make package owns the script's bytes, its
installation and the nonce check; a launcher only needs to find the
installed script and the command that runs it. A run without one launches
exactly as before.
"""

from __future__ import annotations

import shlex
import sys
from pathlib import Path
from typing import Optional

MAKE_ROUND_GUARD_DIRECTORY = "make-round-guard"
MAKE_ROUND_GUARD_SCRIPT = "make_round_guard.py"
HOOK_TIMEOUT_SECONDS = 10
# Managers whose PreToolUse hook names the calling subagent.
MAKE_ROUND_GUARD_MANAGER_IDS = frozenset({"codex", "claude"})
# Managers whose hooks also record subagent starts and reviewer reads, so a
# Component Review can be bound to one proven Component Reviewer (issue #77).
# Codex keeps its earlier review rules until it exposes the same evidence.
REVIEWER_BINDING_MANAGER_IDS = frozenset({"claude"})
# The environment variable naming the runtime whose native agent id format
# make_round requires of a Component Review's reviewer.
REVIEWER_RUNTIME_ENV = "WORKSHOP_REVIEWER_RUNTIME"


def installed_make_round_guard(host_state_root: Path) -> Optional[Path]:
    """The installed guard script, or None for a run created without one."""

    script = Path(host_state_root) / MAKE_ROUND_GUARD_DIRECTORY / MAKE_ROUND_GUARD_SCRIPT
    if script.is_symlink() or not script.is_file():
        return None
    return script


def make_round_guard_command(script: Path) -> str:
    """The shell command a runtime registers to run the installed guard."""

    return shlex.join([str(Path(sys.executable).absolute()), str(script)])


__all__ = [
    "HOOK_TIMEOUT_SECONDS",
    "MAKE_ROUND_GUARD_DIRECTORY",
    "MAKE_ROUND_GUARD_MANAGER_IDS",
    "MAKE_ROUND_GUARD_SCRIPT",
    "REVIEWER_BINDING_MANAGER_IDS",
    "REVIEWER_RUNTIME_ENV",
    "installed_make_round_guard",
    "make_round_guard_command",
]
