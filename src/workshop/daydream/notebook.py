"""The persistent per-Inventor notebook of ideas already had."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from workshop.daydream._files import append_private_line, read_regular_bytes
from workshop.daydream.catalog import PriorWork
from workshop.daydream.contracts import (
    MAX_ONE_LINER_CHARS,
    MAX_TITLE_CHARS,
    bounded_line,
    canonical_json,
    require_created_at,
    require_daydream_id,
)
from workshop.errors import ContractError
from workshop._validation import require_sha256


NOTEBOOK_STATUSES = ("dreamed", "rejected")
MAX_NOTEBOOK_BYTES = 8 * 1024 * 1024
MAX_NOTEBOOK_LINE_BYTES = 8 * 1024
DEFAULT_NOTEBOOK_LIMIT = 200
_ENTRY_KEYS = frozenset(
    ("daydream_id", "created_at", "title", "one_liner", "idea_sha256", "status")
)


@dataclass(frozen=True)
class NotebookEntry:
    """One remembered idea: enough to avoid repeating it, nothing more."""

    daydream_id: str
    created_at: str
    title: str
    one_liner: str
    idea_sha256: str
    status: str

    def __post_init__(self) -> None:
        require_daydream_id(self.daydream_id, "notebook daydream_id")
        require_created_at(self.created_at, "notebook created_at")
        bounded_line(self.title, "notebook title", MAX_TITLE_CHARS)
        bounded_line(self.one_liner, "notebook one_liner", MAX_ONE_LINER_CHARS)
        require_sha256(self.idea_sha256, "notebook idea_sha256")
        if self.status not in NOTEBOOK_STATUSES:
            raise ContractError("notebook status must be one of %s" % (NOTEBOOK_STATUSES,))

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "NotebookEntry":
        if not isinstance(raw, Mapping) or set(raw) != _ENTRY_KEYS:
            raise ContractError("notebook entry keys must be exactly %s" % sorted(_ENTRY_KEYS))
        return cls(
            daydream_id=raw["daydream_id"],
            created_at=raw["created_at"],
            title=raw["title"],
            one_liner=raw["one_liner"],
            idea_sha256=raw["idea_sha256"],
            status=raw["status"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "daydream_id": self.daydream_id,
            "created_at": self.created_at,
            "title": self.title,
            "one_liner": self.one_liner,
            "idea_sha256": self.idea_sha256,
            "status": self.status,
        }


def append_notebook_entry(path: Path, entry: NotebookEntry) -> None:
    """Append one JSONL record to the owner-only notebook, creating it if absent."""

    if not isinstance(entry, NotebookEntry):
        raise ContractError("append_notebook_entry requires a NotebookEntry")
    line = (canonical_json(entry.to_dict()) + "\n").encode("utf-8")
    append_private_line(Path(path), line, label="daydream notebook")


def _parse_line(line: bytes) -> NotebookEntry | None:
    if not line.strip() or len(line) > MAX_NOTEBOOK_LINE_BYTES:
        return None
    try:
        raw = json.loads(line.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        return None
    if not isinstance(raw, dict):
        return None
    try:
        return NotebookEntry.parse(raw)
    except ContractError:
        return None


def read_notebook(
    path: Path, *, limit: int = DEFAULT_NOTEBOOK_LIMIT
) -> tuple[NotebookEntry, ...]:
    """Return the last ``limit`` well-formed entries; malformed lines are skipped."""

    if type(limit) is not int or limit < 1:
        raise ContractError("notebook limit must be a positive integer")
    try:
        payload = read_regular_bytes(
            Path(path), maximum=MAX_NOTEBOOK_BYTES, label="daydream notebook"
        )
    except FileNotFoundError:
        return ()
    entries = [
        entry
        for entry in (_parse_line(line) for line in payload.split(b"\n"))
        if entry is not None
    ]
    return tuple(entries[-limit:])


def render_notebook_markdown(entries: Sequence[NotebookEntry]) -> str:
    """Render the notebook the Inventor reads so it never repeats itself."""

    lines = ["# Your notebook (ideas you already had — do not repeat)", ""]
    if not entries:
        lines.append("(empty: this is your first daydream)")
    for entry in entries:
        if not isinstance(entry, NotebookEntry):
            raise ContractError("render_notebook_markdown requires NotebookEntry items")
        lines.append(
            "- **%s** (%s, %s, %s): %s"
            % (entry.title, entry.daydream_id, entry.status, entry.created_at, entry.one_liner)
        )
    return "\n".join(lines) + "\n"


def prior_work_from_notebook(entries: Sequence[NotebookEntry]) -> tuple[PriorWork, ...]:
    """Treat every remembered idea as prior work for the novelty lint."""

    selected = []
    for entry in entries:
        if not isinstance(entry, NotebookEntry):
            raise ContractError("prior_work_from_notebook requires NotebookEntry items")
        selected.append(
            PriorWork(
                source="notebook:%s" % entry.daydream_id,
                title=entry.title,
                summary=entry.one_liner,
            )
        )
    return tuple(selected)


__all__ = [
    "DEFAULT_NOTEBOOK_LIMIT",
    "MAX_NOTEBOOK_BYTES",
    "NOTEBOOK_STATUSES",
    "NotebookEntry",
    "append_notebook_entry",
    "prior_work_from_notebook",
    "read_notebook",
    "render_notebook_markdown",
]
