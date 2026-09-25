"""Deterministic round-robin scheduling and scoring for brainstorm-reskin.

Pure functions only: no model calls, no randomness, no agent orchestration,
per the repository's `AGENTS.md`. The orchestrating agent dispatches each
scheduled match to a fresh judge subagent and feeds the returned verdicts
back in for scoring.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

VERDICTS = ("a", "b", "split")


class RoundRobinError(ValueError):
    """A malformed contestant list, schedule, or verdict set."""


@dataclass(frozen=True)
class Match:
    index: int
    a: str
    b: str

    def to_json(self) -> dict:
        return {"index": self.index, "a": self.a, "b": self.b}


@dataclass(frozen=True)
class Standing:
    contestant: str
    points: float
    rank: int
    tied_with: tuple[str, ...]

    def to_json(self) -> dict:
        return {
            "contestant": self.contestant,
            "points": self.points,
            "rank": self.rank,
            "tied_with": list(self.tied_with),
        }


@dataclass(frozen=True)
class RoundRobinResult:
    standings: tuple[Standing, ...]
    unresolved_ties: tuple[tuple[str, ...], ...]

    def to_json(self) -> dict:
        return {
            "standings": [standing.to_json() for standing in self.standings],
            "unresolved_ties": [list(group) for group in self.unresolved_ties],
        }


def build_schedule(contestants: Sequence[str]) -> tuple[Match, ...]:
    """Every pair, both A/B orderings, in a fixed deterministic order."""
    if len(contestants) < 2:
        raise RoundRobinError("round robin needs at least two contestants")
    for name in contestants:
        if not isinstance(name, str) or not name:
            raise RoundRobinError("contestant names must be non-empty strings")
    if len(set(contestants)) != len(contestants):
        raise RoundRobinError("contestants must be unique")
    names = list(contestants)
    matches = []
    index = 0
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            matches.append(Match(index, names[i], names[j]))
            index += 1
            matches.append(Match(index, names[j], names[i]))
            index += 1
    return tuple(matches)


def _matched_contestants(schedule: Sequence[Match]) -> set[str]:
    contestants: set[str] = set()
    for match in schedule:
        contestants.add(match.a)
        contestants.add(match.b)
    return contestants


def _award_points(totals: dict[str, float], match: Match, verdict: str) -> None:
    """Credit one verdict; a split is a draw worth half a point each."""
    if verdict == "a":
        totals[match.a] += 1.0
    elif verdict == "b":
        totals[match.b] += 1.0
    else:
        totals[match.a] += 0.5
        totals[match.b] += 0.5


def score_matches(schedule: Sequence[Match], verdicts: Mapping[int, str]) -> dict[str, float]:
    """Tally points; a split verdict is a draw worth half a point each."""
    if set(verdicts) != {match.index for match in schedule}:
        raise RoundRobinError("verdicts must cover exactly the scheduled matches")
    scores = {name: 0.0 for name in _matched_contestants(schedule)}
    for match in schedule:
        verdict = verdicts[match.index]
        if verdict not in VERDICTS:
            raise RoundRobinError("verdict must be 'a', 'b', or 'split'")
        _award_points(scores, match, verdict)
    return scores


def _head_to_head_points(
    group: Sequence[str], schedule: Sequence[Match], verdicts: Mapping[int, str]
) -> dict[str, float]:
    members = set(group)
    totals = {name: 0.0 for name in group}
    for match in schedule:
        if match.a not in members or match.b not in members:
            continue
        _award_points(totals, match, verdicts[match.index])
    return totals


def rank_standings(schedule: Sequence[Match], verdicts: Mapping[int, str]) -> RoundRobinResult:
    """Rank by points; break ties by head-to-head among the tied group only.

    Any group still tied after head-to-head is reported in
    `unresolved_ties` for the orchestrator to settle.
    """
    scores = score_matches(schedule, verdicts)
    by_points: dict[float, list[str]] = {}
    for name, points in scores.items():
        by_points.setdefault(points, []).append(name)

    standings: list[Standing] = []
    unresolved_ties: list[tuple[str, ...]] = []
    rank = 1
    for points in sorted(by_points, reverse=True):
        group = sorted(by_points[points])
        if len(group) == 1:
            standings.append(Standing(group[0], points, rank, ()))
            rank += 1
            continue
        head_to_head = _head_to_head_points(group, schedule, verdicts)
        by_h2h: dict[float, list[str]] = {}
        for name in group:
            by_h2h.setdefault(head_to_head[name], []).append(name)
        for h2h_points in sorted(by_h2h, reverse=True):
            sub_group = sorted(by_h2h[h2h_points])
            if len(sub_group) > 1:
                unresolved_ties.append(tuple(sub_group))
            for name in sub_group:
                tied_with = tuple(n for n in sub_group if n != name)
                standings.append(Standing(name, points, rank, tied_with))
            rank += len(sub_group)
    return RoundRobinResult(tuple(standings), tuple(unresolved_ties))


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Round-robin schedule and score for brainstorm-reskin."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    schedule_cmd = subparsers.add_parser(
        "schedule", help="Produce the match schedule for a set of contestants."
    )
    schedule_cmd.add_argument(
        "--contestants", required=True, help="Path to a JSON list of contestant ids."
    )

    score_cmd = subparsers.add_parser(
        "score", help="Rank a completed schedule against its verdicts."
    )
    score_cmd.add_argument(
        "--schedule", required=True, help="Path to a schedule JSON produced by 'schedule'."
    )
    score_cmd.add_argument(
        "--verdicts",
        required=True,
        help="Path to a JSON object mapping match index to 'a', 'b', or 'split'.",
    )
    return parser


def run(args: argparse.Namespace) -> dict:
    if args.command == "schedule":
        contestants = _load_json(args.contestants)
        if not isinstance(contestants, list):
            raise RoundRobinError("contestants file must contain a JSON list")
        schedule = build_schedule(contestants)
        return {"matches": [match.to_json() for match in schedule]}
    if args.command == "score":
        schedule_data = _load_json(args.schedule)
        if not isinstance(schedule_data, dict) or not isinstance(schedule_data.get("matches"), list):
            raise RoundRobinError("schedule file must contain a JSON object with a 'matches' list")
        matches = tuple(
            Match(entry["index"], entry["a"], entry["b"]) for entry in schedule_data["matches"]
        )
        verdicts_data = _load_json(args.verdicts)
        if not isinstance(verdicts_data, dict):
            raise RoundRobinError("verdicts file must contain a JSON object")
        verdicts = {int(key): value for key, value in verdicts_data.items()}
        return rank_standings(matches, verdicts).to_json()
    raise RoundRobinError("unsupported command")  # pragma: no cover - argparse rejects unknown commands


def main(argv: Sequence[str] | None = None) -> int:
    try:
        result = run(_parser().parse_args(argv))
    except RoundRobinError as exc:
        print(f"round-robin: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
