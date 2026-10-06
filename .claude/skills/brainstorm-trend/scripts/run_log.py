"""Append-only writer/reader for a brainstorm-trend run.json.

One run lives at ``brainstorm-trend/<trend>-<date>/run.json`` (gitignored).
``RunLog.start`` writes the header once, after the Trend is chosen, with the
Trend and the shortlist it came from; each of its methods below appends one
step matching a `type` in ``../schemas/run.schema.json`` -- the two must stay
in sync. ``trend_evidence_reasons`` is the deterministic half of the Trend
eligibility rule: at least two sources on different sites, each dated within
the last 30 days. Whether a Trend is otherwise eligible is the orchestrator's
judgement. Deterministic tooling only: this module makes no model or agent
calls, per repo AGENTS.md.

The CLI lets the orchestrating agent use all of this without writing Python:

    run_log.py check-trends SHORTLIST.json [--today YYYY-MM-DD]
    run_log.py start RUN.json HEADER.json
    run_log.py append RUN.json STEP_TYPE FIELDS.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlparse

_REQUIRED_TOP_LEVEL = (
    "trend", "chosen_by", "shortlist", "seed", "image_model", "started_at", "steps",
)
CHOSEN_BY = ("given", "human")
CONTESTANTS = 6
MIN_TREND_SOURCES = 2
MAX_TREND_SOURCE_AGE_DAYS = 30

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
        trend: Mapping[str, Any],
        chosen_by: str,
        shortlist: Sequence[Mapping[str, Any]] | None,
        seed: int,
        image_model: str,
        today: date | None = None,
    ) -> "RunLog":
        """Write the header. A Trend the person named is ``given`` and has no
        shortlist; a Trend the person picked is ``human`` and must be one of a
        shortlist whose every entry passed ``trend_evidence_reasons``."""
        path = Path(path)
        if path.exists():
            raise FileExistsError(f"run log already exists: {path}")
        trend = dict(trend)
        if not str(trend.get("name") or "").strip():
            raise ValueError("trend needs a name")
        if chosen_by not in CHOSEN_BY:
            raise ValueError(f"chosen_by must be one of {CHOSEN_BY}, got {chosen_by!r}")
        if chosen_by == "given":
            if shortlist is not None:
                raise ValueError("a given Trend has no shortlist")
        else:
            shortlist = [dict(candidate) for candidate in shortlist or ()]
            if not shortlist:
                raise ValueError("a picked Trend needs the shortlist it was picked from")
            if trend["name"] not in [candidate.get("name") for candidate in shortlist]:
                raise ValueError("the picked Trend is not on the shortlist")
            for candidate in shortlist:
                reasons = trend_evidence_reasons(candidate, today=today)
                if reasons:
                    raise ValueError(
                        f"shortlisted Trend {candidate.get('name')!r} lacks evidence: "
                        + "; ".join(reasons)
                    )
        _refuse_credentials({"trend": trend, "shortlist": shortlist})
        path.parent.mkdir(parents=True, exist_ok=True)
        run = {
            "trend": trend,
            "chosen_by": chosen_by,
            "shortlist": shortlist,
            "seed": seed,
            "image_model": image_model,
            "started_at": _now(),
            "steps": [],
        }
        _write(path, run)
        return cls(path)

    def personalities_drawn(self, *, personalities: Sequence[str], seed: int) -> None:
        personalities = list(personalities)
        if len(personalities) != CONTESTANTS:
            raise ValueError(
                f"expected exactly {CONTESTANTS} personalities, got {len(personalities)}"
            )
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


def trend_evidence_reasons(
    candidate: Mapping[str, Any], *, today: date | None = None
) -> list[str]:
    """Why ``candidate`` lacks the evidence a shortlisted Trend needs.

    Empty when at least two of its ``sources`` are on different sites and
    dated (``published``, YYYY-MM-DD) within the last 30 days, never in the
    future. Only those sources count; others are ignored, not refused.
    """
    today = today or datetime.now(timezone.utc).date()
    oldest = today - timedelta(days=MAX_TREND_SOURCE_AGE_DAYS)
    reasons: list[str] = []
    if not str(candidate.get("name") or "").strip():
        reasons.append("no name")
    sources = candidate.get("sources")
    if not isinstance(sources, list):
        return reasons + ["no sources list"]
    hosts: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, Mapping):
            reasons.append(f"sources[{index}] is not an object")
            continue
        host = (urlparse(str(source.get("url") or "")).hostname or "").lower()
        host = host[4:] if host.startswith("www.") else host
        try:
            published = date.fromisoformat(str(source.get("published")))
        except ValueError:
            continue
        if host and oldest <= published <= today:
            hosts.add(host)
    if len(hosts) < MIN_TREND_SOURCES:
        reasons.append(
            f"{len(hosts)} site(s) dated within {MAX_TREND_SOURCE_AGE_DAYS} days of "
            f"{today.isoformat()}; needs {MIN_TREND_SOURCES}"
        )
    return reasons


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
    if run["chosen_by"] not in CHOSEN_BY:
        raise ValueError(f"run.json 'chosen_by' must be one of {CHOSEN_BY}")
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


def _load_json_file(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="brainstorm-trend run.json tooling.")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check-trends", help="Check a shortlist's evidence.")
    check.add_argument("shortlist", help="JSON list of {name, summary, sources}")
    check.add_argument("--today", help="YYYY-MM-DD; defaults to today in UTC")
    start = commands.add_parser("start", help="Write a run's header.")
    start.add_argument("run")
    start.add_argument("header", help="JSON object of RunLog.start's keyword arguments")
    append = commands.add_parser("append", help="Append one step.")
    append.add_argument("run")
    append.add_argument("step_type", choices=sorted(_STEP_REQUIRED_FIELDS))
    append.add_argument("fields", help="JSON object of the step's fields")
    args = parser.parse_args(argv)

    try:
        if args.command == "check-trends":
            today = date.fromisoformat(args.today) if args.today else None
            results = [
                {"name": candidate.get("name"), "reasons": trend_evidence_reasons(candidate, today=today)}
                for candidate in _load_json_file(args.shortlist)
            ]
            print(json.dumps(results, indent=2))
            return 0 if all(not result["reasons"] for result in results) else 1
        if args.command == "start":
            RunLog.start(Path(args.run), **_load_json_file(args.header))
            return 0
        fields = _load_json_file(args.fields)
        if args.step_type == "standings":
            RunLog(Path(args.run)).standings(fields["standings"])
        else:
            getattr(RunLog(Path(args.run)), args.step_type)(**fields)
        return 0
    except (ValueError, TypeError, KeyError, FileExistsError) as exc:
        print(f"run-log: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
