"""Append-only writer/reader for a brainstorm-reskin run.json.

One run lives at ``brainstorm-reskin/<game>-<date>/run.json`` (gitignored).
``RunLog.start`` writes the header once; each of its methods below appends one
step matching a `type` in ``../schemas/run.schema.json`` -- the two must stay
in sync. Deterministic tooling only: this module makes no model or agent
calls, per repo AGENTS.md.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

_REQUIRED_TOP_LEVEL = ("game", "theme_hint", "seed", "image_model", "started_at", "steps")

# Field names that must never carry a credential, and value shapes common to
# the API keys this run touches (OpenRouter, generic `sk-`/bearer secrets).
_FORBIDDEN_FIELD_NAMES = re.compile(r"(key|token|secret|password|authorization)", re.IGNORECASE)
_KEY_SHAPED_VALUE = re.compile(r"\b(sk-[A-Za-z0-9_-]{10,}|Bearer\s+\S+)\b")


class RunLog:
    """Handle to one run's on-disk run.json."""

    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def start(
        cls,
        path: Path,
        *,
        game: str,
        theme_hint: str | None,
        seed: int,
        image_model: str,
    ) -> "RunLog":
        path = Path(path)
        if path.exists():
            raise FileExistsError(f"run log already exists: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        run = {
            "game": game,
            "theme_hint": theme_hint,
            "seed": seed,
            "image_model": image_model,
            "started_at": _now(),
            "steps": [],
        }
        _write(path, run)
        return cls(path)

    def personalities_drawn(self, *, personalities: Sequence[str], seed: int) -> None:
        personalities = list(personalities)
        if len(personalities) != 5:
            raise ValueError(f"expected exactly 5 personalities, got {len(personalities)}")
        self._append(
            "personalities_drawn",
            personalities=personalities,
            seed=seed,
        )

    def contract_generated(
        self,
        *,
        agent_id: str,
        personality: str,
        contract_path: str,
        hero_path: str,
        **extra: Any,
    ) -> None:
        self._append(
            "contract_generated",
            agent_id=agent_id,
            personality=personality,
            contract_path=contract_path,
            hero_path=hero_path,
            **extra,
        )

    def gate_rejected(
        self,
        *,
        agent_id: str,
        personality: str,
        reasons: Sequence[str],
        replacement_personality: str | None,
    ) -> None:
        reasons = list(reasons)
        if not reasons:
            raise ValueError("gate_rejected requires at least one reason")
        self._append(
            "gate_rejected",
            agent_id=agent_id,
            personality=personality,
            reasons=reasons,
            replacement_personality=replacement_personality,
        )

    def judgment(
        self,
        *,
        pair: tuple[str, str],
        ordering: str,
        winner: str | None,
        reason: str,
    ) -> None:
        if ordering not in ("ab", "ba"):
            raise ValueError(f"ordering must be 'ab' or 'ba', got {ordering!r}")
        self._append(
            "judgment",
            pair=list(pair),
            ordering=ordering,
            winner=winner,
            reason=reason,
        )

    def standings(self, standings: Iterable[Mapping[str, Any]]) -> None:
        standings = [dict(row) for row in standings]
        if not standings:
            raise ValueError("standings requires at least one row")
        self._append("standings", standings=standings)

    def tie_break(self, *, tied: Sequence[str], winner: str, reason: str) -> None:
        tied = list(tied)
        if len(tied) < 2:
            raise ValueError("tie_break requires at least two tied agents")
        self._append("tie_break", tied=tied, winner=winner, reason=reason)

    def winner(self, *, agent_id: str, contract_path: str) -> None:
        self._append("winner", agent_id=agent_id, contract_path=contract_path)

    def human_approval(self, *, approved_at: str) -> None:
        self._append("human_approval", approved_at=approved_at)

    def _append(self, step_type: str, **fields: Any) -> None:
        _refuse_credentials(fields)
        run = _read(self.path)
        run["steps"].append({"type": step_type, "at": _now(), **fields})
        _write(self.path, run)


def load(path: Path) -> dict[str, Any]:
    """Read and structurally validate a run.json, raising ValueError if malformed."""
    run = _read(Path(path))
    _validate_run(run)
    return run


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _write(path: Path, run: Mapping[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(run, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def _refuse_credentials(value: Any) -> None:
    """Recursively refuse credential-named keys and key-shaped string values."""
    if isinstance(value, str):
        if _KEY_SHAPED_VALUE.search(value):
            raise ValueError("refusing to log a value shaped like a credential")
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if _FORBIDDEN_FIELD_NAMES.search(str(key)):
                raise ValueError(f"refusing to log field named like a credential: {key!r}")
            _refuse_credentials(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _refuse_credentials(item)


_STEP_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "personalities_drawn": ("personalities", "seed"),
    "contract_generated": ("agent_id", "personality", "contract_path", "hero_path"),
    "gate_rejected": ("agent_id", "personality", "reasons", "replacement_personality"),
    "judgment": ("pair", "ordering", "winner", "reason"),
    "standings": ("standings",),
    "tie_break": ("tied", "winner", "reason"),
    "winner": ("agent_id", "contract_path"),
    "human_approval": ("approved_at",),
}


def _validate_run(run: Mapping[str, Any]) -> None:
    missing = [field for field in _REQUIRED_TOP_LEVEL if field not in run]
    if missing:
        raise ValueError(f"run.json missing required field(s): {missing}")
    if not isinstance(run["steps"], list):
        raise ValueError("run.json 'steps' must be a list")
    for index, step in enumerate(run["steps"]):
        _validate_step(step, index)


def _validate_step(step: Mapping[str, Any], index: int) -> None:
    if "type" not in step or "at" not in step:
        raise ValueError(f"step {index} missing 'type' or 'at'")
    step_type = step["type"]
    required = _STEP_REQUIRED_FIELDS.get(step_type)
    if required is None:
        raise ValueError(f"step {index} has unknown type: {step_type!r}")
    missing = [field for field in required if field not in step]
    if missing:
        raise ValueError(f"step {index} ({step_type}) missing required field(s): {missing}")
