#!/usr/bin/env python3
"""Blind judging packets for brainstorm-trend's round robin.

Each match's judge gets one directory holding draft A and draft B, in the
scheduled order: ``A.md`` and ``B.md``, each the contract's title and its
``## Trend Hook``, ``## Signature Motion`` and ``## Palette`` sections and
nothing else, beside ``A.<ext>`` and ``B.<ext>``, each draft's Concept Image.
The rest of a contract stays out, so an introduction that says who designed
it never reaches a judge.

A packet that still names a personality would unblind its judge, so the
build refuses before writing anything when a kept section carries the name
of a personality in this contest (``Cam Whisperer``, matched as written),
its hyphenated id (``cam-whisperer``), or the word ``personality``. The
contest is the run's draw and its replacements, read from ``run.json``; the
title is the toy's own name and is not searched. So a "Desk Walker" title,
or "Spinner" in a contest without the Spinner, stays usable, as do ordinary
lowercase words such as "walker". Deterministic tooling only, per
repo AGENTS.md: no model calls and no agent orchestration.

    blind_packets.py --schedule schedule.json --run-dir RUN --out PACKETS
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

import draw_personalities

SECTIONS = ("Trend Hook", "Signature Motion", "Palette")
CONCEPT_NAMES = ("concept.png", "concept.jpg", "concept.webp")

_FENCE_START = "```design-contract"
_HEADING = re.compile(r"^#{1,6}[ \t]", re.MULTILINE)
_TITLE = re.compile(r"^#[ \t]+(?P<title>.+?)[ \t]*$", re.MULTILINE)


class PacketError(ValueError):
    """A draft that cannot go to a judge, with every reason found."""

    def __init__(self, reasons: Sequence[str]) -> None:
        self.reasons = list(reasons)
        super().__init__("; ".join(self.reasons))


def _section_body(prose: str, title: str) -> str:
    heading = re.compile(
        r"^#{1,6}[ \t]*%s[ \t]*$" % re.escape(title), re.IGNORECASE | re.MULTILINE
    )
    match = heading.search(prose)
    if match is None:
        return ""
    after = prose[match.end():]
    next_heading = _HEADING.search(after)
    return (after[: next_heading.start()] if next_heading else after).strip()


def packet_text(contract: str) -> str:
    """The title and the three sections a judge reads, from a whole
    ``CONTRACT.md``."""

    prose = contract.split(_FENCE_START, 1)[0]
    title = _TITLE.search(prose)
    reasons = [] if title else ["no title heading"]
    parts = ["# %s" % title.group("title")] if title else []
    for name in SECTIONS:
        body = _section_body(prose, name)
        if not body:
            reasons.append("no %s section" % name)
        parts.append("## %s\n\n%s" % (name, body))
    if reasons:
        raise PacketError(reasons)
    return "\n\n".join(parts) + "\n"


def named_personalities(text: str, pool: Sequence[Mapping[str, Any]]) -> List[str]:
    """Every pool name, hyphenated pool id, or the word "personality" that
    ``text`` carries, in pool order."""

    found: List[str] = []
    for entry in pool:
        terms = [str(entry.get("name") or "")]
        if "-" in str(entry["id"]):
            terms.append(str(entry["id"]))
        for term in terms:
            if term and re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(term), text):
                found.append(term)
    if re.search(r"\bpersonalit(y|ies)\b", text, re.IGNORECASE):
        found.append("personality")
    return found


def contestants(
    run_dir: Path, pool: Sequence[Mapping[str, Any]]
) -> List[Mapping[str, Any]]:
    """The pool entries this run drew or drew as replacements, per its
    ``run.json``."""

    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    ids: List[str] = []
    for step in run.get("steps", []):
        if step.get("type") == "personalities_drawn":
            ids.extend(step.get("personalities", []))
        elif step.get("type") == "gate_rejected" and step.get("replacement_personality"):
            ids.append(step["replacement_personality"])
    by_id = {entry["id"]: entry for entry in pool}
    unknown = [item for item in ids if item not in by_id]
    if unknown:
        raise PacketError(["run.json names personalities not in the pool: %s" % ", ".join(unknown)])
    return [by_id[item] for item in ids]


def _draft(run_dir: Path, slot: str, pool: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    reasons: List[str] = []
    text = ""
    try:
        text = packet_text((run_dir / slot / "CONTRACT.md").read_text(encoding="utf-8"))
    except OSError:
        reasons.append("%s has no CONTRACT.md" % slot)
    except PacketError as exc:
        reasons.extend("%s: %s" % (slot, reason) for reason in exc.reasons)
    sections = text.split("\n", 1)[1] if "\n" in text else ""
    for name in named_personalities(sections, pool):
        reasons.append("%s names %s" % (slot, name))
    concepts = [run_dir / slot / name for name in CONCEPT_NAMES if (run_dir / slot / name).is_file()]
    if not concepts:
        reasons.append("%s has no Concept Image" % slot)
    return {"text": text, "concept": concepts[0] if concepts else None, "reasons": reasons}


def build_packets(
    schedule: Mapping[str, Any],
    run_dir: Path,
    out_dir: Path,
    pool: Sequence[Mapping[str, Any]],
) -> List[Path]:
    """Write one packet directory per scheduled match under ``out_dir``,
    which must not exist yet; refuse, writing nothing, when any draft cannot
    go to a judge."""

    if out_dir.exists():
        raise PacketError(["%s already exists; packets are never overwritten" % out_dir])
    pool = contestants(run_dir, pool)
    matches = list(schedule["matches"])
    slots: List[str] = []
    for match in matches:
        for slot in (match["a"], match["b"]):
            if slot not in slots:
                slots.append(slot)
    drafts = {slot: _draft(run_dir, slot, pool) for slot in slots}
    reasons = [reason for slot in slots for reason in drafts[slot]["reasons"]]
    if reasons:
        raise PacketError(reasons)

    # Build beside the target and rename, so a failed write leaves no
    # half-built packets for a judge to read.
    staging = out_dir.with_name(out_dir.name + ".partial")
    shutil.rmtree(staging, ignore_errors=True)
    names: List[str] = []
    for match in matches:
        name = "match-%02d" % match["index"]
        packet = staging / name
        packet.mkdir(parents=True)
        for side, slot in (("A", match["a"]), ("B", match["b"])):
            draft = drafts[slot]
            (packet / ("%s.md" % side)).write_text(draft["text"], encoding="utf-8")
            shutil.copyfile(draft["concept"], packet / (side + draft["concept"].suffix))
        names.append(name)
    staging.rename(out_dir)
    return [out_dir / name for name in names]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build brainstorm-trend's blind judging packets.")
    parser.add_argument("--schedule", type=Path, required=True, help="round_robin.py schedule output")
    parser.add_argument("--run-dir", type=Path, required=True, help="the run directory holding the slots")
    parser.add_argument("--out", type=Path, required=True, help="where to write match-NN/ packets")
    parser.add_argument("--pool", type=Path, default=draw_personalities.POOL_PATH)
    args = parser.parse_args(argv)

    try:
        schedule = json.loads(args.schedule.read_text(encoding="utf-8"))
        pool = draw_personalities.load_pool(args.pool)
        written = build_packets(schedule, args.run_dir, args.out, pool)
    except PacketError as exc:
        for reason in exc.reasons:
            print("blind-packets: %s" % reason, file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("blind-packets: %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        return 2
    print(json.dumps([str(path) for path in written], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
