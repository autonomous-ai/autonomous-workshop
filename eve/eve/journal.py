"""Append-only event journal.

Eve's journal is a running, human- and machine-readable narration of every
step it takes. Append-only: nothing is ever rewritten, so the ledger and the
queue can be audited against an immutable story of what actually happened.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Journal:
    def __init__(self, path: Path, enabled: bool = True):
        self.path = path
        self.enabled = enabled

    def append(self, event: str, *, game: Optional[str] = None, **fields) -> None:
        if not self.enabled:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        rec = {"ts": _now(), "event": event, "game": game, **fields}
        line = json.dumps(rec, sort_keys=True)
        with open(self.path, "a") as fh:
            fh.write(line + "\n")

    def read(self) -> list[dict]:
        if not self.path.exists():
            return []
        recs = []
        for ln in self.path.read_text().splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                recs.append(json.loads(ln))
            except json.JSONDecodeError:
                recs.append({"event": "unparseable", "raw": ln})
        return recs

    def tail(self, n: int = 20) -> list[dict]:
        return self.read()[-n:]


def open_journal(cfg) -> Journal:
    return Journal(cfg.journal_path)
