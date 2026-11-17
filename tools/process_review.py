#!/usr/bin/env python3
"""Slow-step review of the Workshop timing ledger (ADR 0106).

    process_review.py report   [--days 7] [--today YYYY-MM-DD] [--ledger PATH] [--out FILE]
    process_review.py backfill [ROOT ...] [--ledger PATH] [--workshop-home DIR]
    process_review.py annotate --source TEXT|--id ROW --class CLASS --note TEXT [--ledger PATH]

``report`` reads the ledger and ranks, over the last N days,

1. the steps with the most total wall time (each row's own time, its timed
   children's taken out);
2. steps rerun on unchanged inputs (equal input fingerprint or reuse key);
3. expensive steps that ran before a cheap step failed in the same session;
4. failures that were tool or harness errors, stale inputs or kills rather
   than product defects;
5. wait time between one step finishing and the next starting on a toy.

It writes a short Markdown report, the top 5 findings with evidence paths
and a suggested fix each, then the top 5 of every ranking, to
``docs/research/process-review/<date>.md``. It is deterministic: the same
ledger, annotations and date give the same bytes. No model is called; the
suggested fixes are fixed templates. Proposing and making a fix is agent
work, and an agent that diagnoses a failure differently from the ledger's
class records that with ``annotate`` (never by editing a row).

``backfill`` reads the logs build agents already left (``toys-spec/**``:
``*.log`` with ``date +%s`` lines and ``EXIT n``, ``[tool] x: rc=N in Ts``
lines, make_round's per-gate logs, ``measure/seeded-batch.json`` records,
and ``$WORKSHOP_HOME/state/*/wish-run-timing.json``) and appends rows marked
``source: backfill:<path>``. It is idempotent: a source already in the
ledger is skipped. Times a log does not state are marked estimated.

Nothing here changes a gate, a verdict or a threshold.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from workshop.runtime import timing_ledger as tl  # noqa: E402

ANNOTATION_KIND = "workshop-timing-annotation"
CHEAP_S = 60.0
EXPENSIVE_S = 600.0
MAX_WAIT_S = 2 * 3600.0
TOP = 5
HOT_IN_TOP = 2
REPORT_DIR = REPO / "docs" / "research" / "process-review"
WASTE_CLASSES = (tl.TOOL_ERROR, tl.STALE_INPUT, tl.KILLED)
_CHEAP_REASON = re.compile(r"expensive gates not started|preflight audit group", re.IGNORECASE)


# --------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------

def annotations_path(ledger: Path) -> Path:
    return ledger.with_name("annotations.jsonl")


def read_annotations(ledger: Path) -> list:
    path = annotations_path(ledger)
    if not path.is_file():
        return []
    found = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict) and value.get("kind") == ANNOTATION_KIND and isinstance(value.get("match"), dict):
            found.append(value)
    return found


def apply_annotations(rows: list, annotations: list) -> list:
    """Rows with an agent's later diagnosis applied: the last matching
    annotation's class wins. A match is every key equal, ``source`` by prefix."""

    result = []
    for row in rows:
        row = dict(row)
        for note in annotations:
            match = note["match"]
            if all((str(row.get(key) or "").startswith(str(value)) if key == "source" else row.get(key) == value)
                   for key, value in match.items()):
                if note.get("failure_class") in tl.FAILURE_CLASSES and row.get("outcome") != tl.PASS:
                    row["failure_class"] = note["failure_class"]
                    row["annotation"] = note.get("note")
        result.append(row)
    return result


def finished_rows(rows: list, start: float, end: float) -> list:
    """End rows inside the window, plus a killed row for each start row
    that never ended and has a later row for the same step and toy."""

    ends = [row for row in rows if row.get("event") == "end"]
    ended_ids = {row.get("id") for row in ends}
    later = defaultdict(list)
    for row in rows:
        if row.get("started_at"):
            later[(row.get("step"), row.get("toy"))].append(tl.parse_iso(row["started_at"]))
    for row in rows:
        if row.get("event") != "start" or row.get("id") in ended_ids or not row.get("started_at"):
            continue
        began = tl.parse_iso(row["started_at"])
        if not any(other > began for other in later[(row.get("step"), row.get("toy"))]):
            continue  # still running, or the newest: not judged
        killed = dict(row, event="end", ended_at=row["started_at"], wall_s=0.0, outcome=tl.KILLED,
                      failure_class=tl.KILLED, exit_code=None, reason="started, never ended", wall_unknown=True)
        ends.append(killed)
    window = []
    for row in ends:
        try:
            ended = tl.parse_iso(row["ended_at"])
        except (KeyError, ValueError, TypeError):
            continue
        if start <= ended < end:
            window.append(row)
    window.sort(key=lambda row: (row["started_at"], row["ended_at"], row.get("step") or "", row.get("id") or ""))
    return window


def evidence_of(row: dict) -> str:
    for key in ("evidence", "source_path", "project"):
        if row.get(key):
            return str(row[key])
    return "(ledger row %s)" % row.get("id")


def _fmt(seconds: float) -> str:
    seconds = float(seconds)
    if seconds >= 3600:
        return "%.1f h" % (seconds / 3600)
    if seconds >= 60:
        return "%.0f min" % (seconds / 60)
    return "%.1f s" % seconds


# --------------------------------------------------------------------------
# Rankings
# --------------------------------------------------------------------------

def children_of(rows: list) -> dict:
    by_parent = defaultdict(list)
    for row in rows:
        if row.get("parent"):
            by_parent[row["parent"]].append(row)
    return by_parent


def self_seconds(row: dict, kids: dict) -> float:
    if row.get("cache_hit"):
        return 0.0
    inner = sum(float(child.get("wall_s") or 0) for child in kids.get(row.get("id"), ()))
    return max(0.0, float(row.get("wall_s") or 0) - inner)


def rank_total(rows: list) -> list:
    kids = children_of(rows)
    groups: dict = defaultdict(lambda: {"seconds": 0.0, "runs": 0, "max": 0.0, "rows": []})
    for row in rows:
        group = groups[row["step"]]
        own = self_seconds(row, kids)
        group["seconds"] += own
        group["runs"] += 1
        group["max"] = max(group["max"], float(row.get("wall_s") or 0))
        group["rows"].append(row)
    ranked = [{"category": "total", "key": step, "seconds": round(value["seconds"], 3), "runs": value["runs"],
               "max": value["max"], "rows": value["rows"]} for step, value in groups.items() if value["seconds"] > 0]
    ranked.sort(key=lambda item: (-item["seconds"], item["key"]))
    return ranked


def rank_reruns(rows: list) -> list:
    """Runs after the first with the same step, project and input key. A
    rerun after a kill or timeout is not counted: the first never finished."""

    seen: dict = {}
    groups: dict = defaultdict(lambda: {"seconds": 0.0, "runs": 0, "rows": []})
    for row in rows:
        key = row.get("inputs_key")
        if not key or row.get("cache_hit"):
            continue
        ident = (row["step"], row.get("toy") or row.get("project"), key)
        previous = seen.get(ident)
        seen[ident] = row
        if previous is None or previous.get("outcome") == tl.KILLED:
            continue
        group = groups[ident]
        group["seconds"] += float(row.get("wall_s") or 0)
        group["runs"] += 1
        group["rows"].extend([previous, row])
    ranked = [{"category": "rerun", "key": "%s on %s" % (step, project), "step": step,
               "seconds": round(value["seconds"], 3), "runs": value["runs"], "rows": value["rows"]}
              for (step, project, _), value in groups.items() if value["seconds"] > 0]
    ranked.sort(key=lambda item: (-item["seconds"], item["key"]))
    return ranked


def is_cheap_failure(row: dict, kids: dict) -> bool:
    if row.get("outcome") != tl.FAIL:
        return False
    if float(row.get("wall_s") or 0) <= CHEAP_S or _CHEAP_REASON.search(row.get("reason") or ""):
        return True
    failing = [child for child in kids.get(row.get("id"), ()) if child.get("outcome") == tl.FAIL]
    return bool(failing) and min(float(child.get("wall_s") or 0) for child in failing) <= CHEAP_S


def rank_expensive_before_cheap(rows: list) -> list:
    """In one session (the children of one parent), expensive passing steps
    that ran before the first step that failed cheaply."""

    kids = children_of(rows)
    found = []
    for parent, members in kids.items():
        members = sorted(members, key=lambda row: (row["started_at"], row.get("step") or ""))
        failing = next((row for row in members if row.get("outcome") == tl.FAIL), None)
        if failing is None or not is_cheap_failure(failing, kids):
            continue
        before = [row for row in members if row["started_at"] <= failing["started_at"] and row is not failing
                  and row.get("outcome") == tl.PASS and not row.get("cache_hit")
                  and float(row.get("wall_s") or 0) >= EXPENSIVE_S]
        if not before:
            continue
        seconds = sum(float(row["wall_s"]) for row in before)
        found.append({"category": "order", "key": "%s before %s" % (" + ".join(sorted({r["step"] for r in before})),
                                                                     failing["step"]),
                      "step": failing["step"], "expensive": sorted({r["step"] for r in before}),
                      "seconds": round(seconds, 3), "runs": 1, "rows": before + [failing]})
    merged: dict = {}
    for item in found:
        if item["key"] in merged:
            merged[item["key"]]["seconds"] += item["seconds"]
            merged[item["key"]]["runs"] += 1
            merged[item["key"]]["rows"].extend(item["rows"])
        else:
            merged[item["key"]] = item
    ranked = list(merged.values())
    ranked.sort(key=lambda item: (-item["seconds"], item["key"]))
    return ranked


def rank_harness_failures(rows: list) -> list:
    groups: dict = defaultdict(lambda: {"seconds": 0.0, "runs": 0, "rows": []})
    for row in rows:
        if row.get("outcome") == tl.PASS or row.get("failure_class") not in WASTE_CLASSES:
            continue
        group = groups[(row["step"], row["failure_class"])]
        group["seconds"] += float(row.get("wall_s") or 0)
        group["runs"] += 1
        group["rows"].append(row)
    ranked = [{"category": "harness", "key": "%s (%s)" % (step, cls), "step": step, "class": cls,
               "seconds": round(value["seconds"], 3), "runs": value["runs"], "rows": value["rows"]}
              for (step, cls), value in groups.items()]
    ranked.sort(key=lambda item: (-item["seconds"], -item["runs"], item["key"]))
    return ranked


def rank_waits(rows: list) -> list:
    """Idle time on one toy between a top-level step ending and the next
    starting. Gaps over two hours are left out: those are the owner's
    review, a night, or an agent's design work, not a pipeline wait."""

    by_toy = defaultdict(list)
    for row in rows:
        # Whole steps only: a tool's per-check logs are parts of one step.
        if (not row.get("parent") and row.get("toy") and not row.get("aggregate")
                and not row.get("gate_log")):
            by_toy[row["toy"]].append(row)
    found = []
    for toy, members in by_toy.items():
        members.sort(key=lambda row: (row["started_at"], row.get("step") or ""))
        latest_end = None
        latest_row = None
        for row in members:
            began = tl.parse_iso(row["started_at"])
            if latest_end is not None and began > latest_end:
                gap = began - latest_end
                if gap <= MAX_WAIT_S:
                    found.append({"category": "wait", "key": "%s: %s -> %s" % (toy, latest_row["step"], row["step"]),
                                  "step": row["step"], "seconds": round(gap, 3), "runs": 1,
                                  "rows": [latest_row, row]})
            ended = tl.parse_iso(row["ended_at"])
            if latest_end is None or ended > latest_end:
                latest_end, latest_row = ended, row
    merged: dict = {}
    for item in found:
        if item["key"] in merged:
            merged[item["key"]]["seconds"] += item["seconds"]
            merged[item["key"]]["runs"] += 1
            merged[item["key"]]["rows"].extend(item["rows"])
        else:
            merged[item["key"]] = item
    ranked = list(merged.values())
    ranked.sort(key=lambda item: (-item["seconds"], item["key"]))
    return ranked


def suggestion(item: dict) -> str:
    category = item["category"]
    if category == "total":
        return ("Profile `%s`: key each sub-result on its own inputs so unchanged parts are reused, and run "
                "independent parts in parallel." % item["key"])
    if category == "rerun":
        return ("`%s` ran again on the same inputs: reuse the earlier result when the fingerprint matches "
                "(widen its reuse key), or stop the caller that reruns it." % item["step"])
    if category == "order":
        return ("Run `%s` (cheap) before %s: move it into the preflight layer so the attempt fails in seconds."
                % (item["step"], ", ".join("`%s`" % step for step in item["expensive"])))
    if category == "harness":
        cls = item["class"]
        if cls == tl.STALE_INPUT:
            return ("Check `%s`'s inputs for staleness in a preflight before the long work starts, and say "
                    "which file to refresh." % item["step"])
        if cls == tl.KILLED:
            return ("`%s` was killed or timed out: right-size its deadline from the ledger, make it resumable, "
                    "and do not stop a running step for a tool update; preflight first." % item["step"])
        return ("`%s` failed on the tool, not the product: fix the tool and add the failing case as a "
                "regression test." % item["step"])
    if category == "wait":
        return "Start the next step automatically when the previous one ends (chain it in the loop, or notify)."
    return ""


def _evidence(item: dict) -> list:
    seen = []
    for row in item["rows"]:
        path = evidence_of(row)
        if path not in seen:
            seen.append(path)
    return seen[:3]


def build_report(rows: list, *, today: date, days: int, ledger: Path) -> str:
    end = datetime(today.year, today.month, today.day, tzinfo=timezone.utc).timestamp() + 86400
    start = end - days * 86400
    window = finished_rows(rows, start, end)
    rankings = [
        ("Most total wall time", rank_total(window)),
        ("Rerun on unchanged inputs", rank_reruns(window)),
        ("Expensive steps before a cheap failure", rank_expensive_before_cheap(window)),
        ("Tool, harness, stale-input and kill failures", rank_harness_failures(window)),
        ("Waits between steps", rank_waits(window)),
    ]
    # The headline keeps at most HOT_IN_TOP hot steps: the rest of it is
    # time a fix can win back (reruns, order, non-product failures, waits).
    findings = [item for _, ranked in rankings[1:] for item in ranked]
    findings += rankings[0][1][:HOT_IN_TOP]
    findings.sort(key=lambda item: (-item["seconds"], item["category"], item["key"]))
    top, seen = [], set()
    for item in findings:
        if (item["category"], item["key"]) in seen:
            continue
        seen.add((item["category"], item["key"]))
        top.append(item)
        if len(top) == TOP:
            break
    lines = ["# Process review %s" % today.isoformat(), "",
             "Generated by `tools/process_review.py report --days %d --today %s` from the timing ledger "
             "(ADR 0106): %d finished steps between %s and %s. Deterministic; no model was called. "
             "Times marked estimated come from backfilled logs." % (
                 days, today.isoformat(), len(window), (today - timedelta(days=days - 1)).isoformat(),
                 today.isoformat()), "",
             "## Top %d" % TOP, ""]
    labels = {"total": "hot step", "rerun": "rerun, same inputs", "order": "expensive before cheap failure",
              "harness": "not a product defect", "wait": "wait"}
    if not top:
        lines.append("No findings in this window.")
    for number, item in enumerate(top, 1):
        lines.append("%d. **%s** (%s): %s over %d run(s)." % (number, item["key"], labels[item["category"]],
                                                              _fmt(item["seconds"]), item["runs"]))
        reason = next((row.get("reason") for row in item["rows"] if row.get("reason")), None)
        if reason and item["category"] in ("harness", "order"):
            lines.append("   - Last words: %s" % reason[-200:])
        lines.append("   - Evidence: %s" % "; ".join("`%s`" % path for path in _evidence(item)))
        lines.append("   - Suggested fix: %s" % suggestion(item))
    keyed = sum(1 for row in window if row.get("inputs_key"))
    for title, ranked in rankings:
        lines += ["", "## %s" % title, ""]
        if title.startswith("Rerun"):
            lines += ["%d of %d steps carry an input key (live rows, seeded batch records, and per-check "
                      "logs whose summary.json lists its sources); a rerun of a step without one is not "
                      "visible here." % (keyed, len(window)), ""]
        if not ranked:
            lines.append("None.")
            continue
        lines += ["| # | Step | Time | Runs | Evidence |", "|---|---|---|---|---|"]
        for number, item in enumerate(ranked[:TOP], 1):
            lines.append("| %d | `%s` | %s | %d | `%s` |" % (number, item["key"].replace("|", "/"),
                                                            _fmt(item["seconds"]), item["runs"],
                                                            _evidence(item)[0]))
    classes = defaultdict(int)
    for row in window:
        if row.get("outcome") != tl.PASS:
            classes[row.get("failure_class") or "none"] += 1
    lines += ["", "## Failure classes", "",
              ", ".join("%s %d" % (name, classes[name]) for name in sorted(classes)) or "No failures.", "",
              "Ledger: `%s`." % ledger, ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Backfill
# --------------------------------------------------------------------------

_EPOCH = re.compile(r"^\d{10}$")
_EXIT = re.compile(r"^EXIT (-?\d+)\s*$", re.MULTILINE)
# A gate log belongs to the run its directory's summary.json records when it
# was written at most this long before that summary.
SUMMARY_WINDOW_S = 6 * 3600.0
_GATE_LOG = re.compile(r"^\$ (?P<argv>.+)\n\((?P<wall>\d+(?:\.\d+)?)s, exit (?P<rc>-?\d+)\)", re.MULTILINE)
_SKIP_DIRS = ("prompts", "gen", "__cadgen__", "node_modules", ".git")
LOG_STEPS = (
    # (filename prefix, step, tool)
    ("seal_", "seal_proof/seal", "seal_proof"),
    ("preflight_", "seal_proof/preflight", "seal_proof"),
    ("printgates", "make_round/print-gates-only", "make_round"),
    ("helpers", "make_round/shared-helpers", "make_round"),
    ("kitprint", "kit_print/layout", "kit_print"),
    ("kit_sheets", "kit_sheets/check", "kit_sheets"),
    ("sheets_", "kit_sheets/check", "kit_sheets"),
    ("manual_", "kit_manual/build", "kit_manual"),
    ("build_", "kit_manual/build", "kit_manual"),
    ("verify", "verify_project/run", "verify_project"),
)
FIRST_LINE_STEPS = (
    (re.compile(r"^make_round print gates"), "make_round/print-gates-only", "make_round"),
    (re.compile(r"^make_round r\d+\s+shared-helpers"), "make_round/shared-helpers", "make_round"),
    (re.compile(r"^make_round r\d+\s+interface"), "make_round/interface", "make_round"),
    (re.compile(r"^make_round r\d+\s+component"), "make_round/component", "make_round"),
    (re.compile(r"^seal_proof: "), "seal_proof/seal", "seal_proof"),
)


def birth_time(path: Path) -> Optional[float]:
    try:
        done = subprocess.run(["stat", "-c", "%W", str(path)], capture_output=True, text=True, timeout=10)
        value = int(done.stdout.strip() or 0)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return float(value) if value > 0 else None


def step_of_log(path: Path, text: str) -> Optional[tuple]:
    """The step a log records: by its first line's tool banner, or by its
    file name when the log follows the step convention (``date +%s`` lines,
    ``EXIT n`` or ``rc=`` lines). A design script's own output, whatever its
    name, is no Workshop step."""

    body = [line for line in text.splitlines() if line.strip() and not _EPOCH.match(line.strip())]
    first = body[0] if body else ""
    for pattern, step, tool in FIRST_LINE_STEPS:
        if pattern.search(first):
            return step, tool
    lines = [line.strip() for line in text.splitlines()]
    if not (_EXIT.search(text) or (lines and _EPOCH.match(lines[0])) or tl.CHILD_LINE.search(text)):
        return None
    for prefix, step, tool in LOG_STEPS:
        if path.name.startswith(prefix):
            return step, tool
    return None


def _project_of(path: Path, text: str) -> str:
    match = re.search(r"(/\S+?/(?:proof|cad))(?:/|\s|$)", text)
    if match:
        return match.group(1)
    return str(path.parent)


def parse_log(path: Path, text: str, mtime: float, birth: Optional[float]) -> Optional[dict]:
    """What one hand-made step log says: start, end, exit, reason, children."""

    named = step_of_log(path, text)
    if named is None:
        return None
    lines = [line.strip() for line in text.splitlines()]
    epochs = [float(line) for line in lines if _EPOCH.match(line)]
    exits = _EXIT.findall(text)
    exit_code = int(exits[-1]) if exits else None
    ended_known = True
    if len(epochs) >= 2 and epochs[-1] > epochs[0]:
        started, ended = epochs[0], epochs[-1]
    elif epochs and lines and _EPOCH.match(lines[0]):
        started, ended = epochs[0], mtime
    elif birth is not None:
        started, ended = birth, mtime
    else:
        started, ended, ended_known = mtime, mtime, False
    words = [line for line in lines if line and not _EPOCH.match(line) and not _EXIT.match(line)]
    failing = [line for line in words if re.search(r"\bFAIL\b|refus|error|seal_proof: |UNVERIFIED|timed out", line)]
    reason = " ".join(failing[:3]) if failing else None
    return {"step": named[0], "tool": named[1], "project": _project_of(path, text), "started": started,
            "ended": ended, "exit_code": exit_code, "reason": reason, "text": text,
            "times_estimated": not (len(epochs) >= 2), "wall_unknown": not ended_known}


def _row(*, step, tool, project, started, ended, exit_code, reason, source, evidence, parent=None,
         outcome=None, failure_class=None, extra=None, text="", inputs_key=None, reuse=False, unverified=False):
    if outcome is None:
        outcome, failure_class = tl.classify(exit_code, output=text[-4000:], reason=reason, unverified=unverified)
    row = tl.end_row(row_id=uuid.uuid4().hex, step=step, tool=tool, project=project, parent=parent,
                     started=started, ended=ended, exit_code=exit_code, outcome=outcome,
                     failure_class=failure_class, reason=reason if outcome != tl.PASS else None, cache_hit=reuse,
                     inputs_key=inputs_key, source=source, evidence=evidence, extra=extra)
    row["host"] = "backfill"
    row["pid"] = None
    row["source_path"] = evidence
    return row


def backfill_log(path: Path, later_same_step: bool) -> list:
    text = path.read_text(encoding="utf-8", errors="replace")
    mtime = path.stat().st_mtime
    parsed = parse_log(path, text, mtime, birth_time(path))
    if parsed is None:
        return []
    source = "backfill:%s" % path
    extra = {"times_estimated": parsed["times_estimated"]}
    convention = bool(text.strip()) and _EPOCH.match(text.strip().splitlines()[0].strip())
    if parsed["exit_code"] is None:
        if not (later_same_step and convention):
            return []  # still running, or never finished and not yet superseded: not judged
        outcome, failure_class = tl.KILLED, tl.KILLED
        extra["wall_unknown"] = True
        reason = "log has no EXIT line; a later attempt superseded it"
    else:
        outcome = failure_class = None
        reason = parsed["reason"]
    unverified = parsed["exit_code"] == 0 and "UNVERIFIED" in text and "0 FAIL/UNVERIFIED" not in text
    parent = _row(step=parsed["step"], tool=parsed["tool"], project=parsed["project"], started=parsed["started"],
                  ended=parsed["ended"], exit_code=parsed["exit_code"], reason=reason, source=source,
                  evidence=str(path), outcome=outcome, failure_class=failure_class, extra=extra, text=text,
                  unverified=unverified)
    rows = [parent]
    children = tl.child_timings(text)
    if children:
        cursor = parsed["ended"]
        placed = []
        workflow_wall = 0.0
        for child in reversed(children):
            placed.append((cursor - child["wall_s"], cursor, child))
            if child["name"].endswith("workflow"):
                workflow_wall = max(workflow_wall, child["wall_s"])
            else:
                cursor -= child["wall_s"]
        for began, ended, child in reversed(placed):
            rows.append(_row(step="%s/%s" % (child["tool"], child["name"]), tool=child["tool"],
                             project=parsed["project"], started=began, ended=ended, exit_code=child["exit_code"],
                             reason=None if child["exit_code"] == 0 else _child_reason(text, child),
                             source=source, evidence=str(path), parent=parent["id"],
                             extra={"times_estimated": True}, text=_child_reason(text, child) or ""))
        # The seal's earlier layers: everything before final verification,
        # which the log shows only as a time gap. Inferred, never measured.
        if parsed["step"] == "seal_proof/seal" and workflow_wall and "final-verification (exit" in text:
            before = parsed["ended"] - workflow_wall - parsed["started"]
            if before > 0:
                rows.append(_row(step="seal_proof/layers-before-final (inferred)", tool="seal_proof",
                                 project=parsed["project"], started=parsed["started"],
                                 ended=parsed["started"] + before, exit_code=0, reason=None, source=source,
                                 evidence=str(path), parent=parent["id"], outcome=tl.PASS,
                                 extra={"times_estimated": True, "inferred": True}))
    return rows


def _child_reason(text: str, child: dict) -> Optional[str]:
    if child["exit_code"] == 0:
        return None
    for line in text.splitlines():
        if _CHEAP_REASON.search(line):
            return line.strip()[:300]
    for line in text.splitlines():
        if line.startswith("[") and ("FAIL" in line or "failure" in line):
            return line.strip()[:300]
    for line in text.splitlines():
        if "FAIL" in line or "failure" in line or "refus" in line:
            return line.strip()[:300]
    return None


def _summary_key(directory: Path, cache: dict) -> Optional[tuple]:
    """``(key, written)`` for the run that last wrote a gate-log directory:
    the hash of its ``summary.json`` ``sources`` (every source file's
    sha256) and the summary's mtime, when the summary records them."""

    if directory not in cache:
        key = None
        try:
            summary_path = directory / "summary.json"
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            if isinstance(summary, dict) and isinstance(summary.get("sources"), dict) and summary["sources"]:
                key = (hashlib.sha256(json.dumps(summary["sources"], sort_keys=True).encode("utf-8")).hexdigest(),
                       summary_path.stat().st_mtime)
        except (OSError, ValueError):
            pass
        cache[directory] = key
    return cache[directory]


def _gate_kind(path: Path) -> str:
    """``print-gate`` for ``measure/print-gates/``, ``helper-round`` for
    ``measure/helper-rounds/rNNNN/``, else the directory under ``measure/``."""

    parts = path.parent.parts
    if "measure" in parts:
        below = parts[parts.index("measure") + 1:]
        if below:
            name = below[0]
            if name.startswith("print-gates"):
                return "print-gate"
            return {"helper-rounds": "helper-round", "rounds": "round", "identities": "identity"}.get(name, name)
    return "gate-log"


def backfill_gate_log(path: Path, content: bytes, key_cache: dict) -> Optional[dict]:
    """One tool run's own log (``$ argv`` then ``(Ns, exit N)``), as make_round,
    the helper rounds and identities write them."""

    text = content.decode("utf-8", "replace")
    match = _GATE_LOG.search(text)
    if not match:
        return None
    argv = match.group("argv").split()
    script = next((Path(item).name for item in argv[1:3] if "/" in item), Path(argv[0]).name)
    wall = float(match.group("wall"))
    ended = path.stat().st_mtime
    parts = path.parent.parts
    project = str(Path(*parts[:parts.index("measure")])) if "measure" in parts else str(path.parent)
    summary = _summary_key(path.parent, key_cache)
    inputs_key = None
    # Only a log that summary's run wrote, never one kept from an earlier run.
    if summary and summary[1] - SUMMARY_WINDOW_S <= ended <= summary[1] + 5:
        summary_key = summary[0]
        # The same check on the same sources: the run's summary key plus the
        # command with the project path taken out (backups move the project).
        normal = [item.replace(project, "<project>") for item in argv[1:]]
        inputs_key = hashlib.sha256((summary_key + json.dumps(normal)).encode("utf-8")).hexdigest()
    return _row(step="%s/%s" % (_gate_kind(path), script), tool=script, project=project, started=ended - wall,
                ended=ended, exit_code=int(match.group("rc")), reason=None, source="backfill:%s" % path,
                evidence=str(path), inputs_key=inputs_key, text=text[-2000:],
                extra={"times_estimated": True, "gate_log": True})


def backfill_batch_record(path: Path) -> list:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(record, dict) or not isinstance(record.get("steps"), list):
        return []
    ended = path.stat().st_mtime
    steps = [step for step in record["steps"] if isinstance(step, dict) and step.get("status") != "skipped"]
    cursor = ended
    placed = []
    for step in reversed(steps):
        wall = float(step.get("duration_s") or 0)
        placed.append((cursor - wall, cursor, step))
        cursor -= wall
    project = str(path.parents[1])
    rows = []
    for began, end, step in reversed(placed):
        status = step.get("status")
        reason = step.get("reason") or ((step.get("excerpt") or "")[-300:] if status != "pass" else None)
        if status == "reused":
            rows.append(_row(step="seeded-batch/%s/%s" % (record.get("plan"), step.get("id")), tool="seeded_batch",
                             project=project, started=end, ended=end, exit_code=0, reason=None,
                             source="backfill:%s#%s" % (path, step.get("id")), evidence=str(path), outcome=tl.PASS,
                             cache_hit=True, inputs_key=step.get("key"), extra={"layer": step.get("layer")}))
            continue
        unverified = bool(reason and "UNVERIFIED" in reason)
        row = _row(step="seeded-batch/%s/%s" % (record.get("plan"), step.get("id")), tool="seeded_batch",
                   project=project, started=began, ended=end, exit_code=step.get("exit_code"), reason=reason,
                   source="backfill:%s#%s" % (path, step.get("id")), evidence=str(path),
                   inputs_key=step.get("key"), text=step.get("excerpt") or "", unverified=unverified,
                   extra={"layer": step.get("layer"), "batch_status": status, "times_estimated": True})
        if status == "harness-failure" and row["failure_class"] == tl.PRODUCT_DEFECT:
            row["failure_class"] = tl.TOOL_ERROR
        rows.append(row)
    return rows


def backfill_wish_timing(state: Path) -> list:
    rows = []
    for path in sorted(state.glob("*/wish-run-timing.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            ended = tl.parse_iso(record["last_observed_at"])
        except (OSError, ValueError, KeyError, TypeError):
            continue
        product = record.get("product_id") or path.parent.name
        for stage, operations in sorted((record.get("stages") or {}).items()):
            for operation, aggregate in sorted(operations.items()):
                wall = float(aggregate.get("elapsed_ms") or 0) / 1000.0
                states = aggregate.get("states") or {}
                failed = states.get("failed", 0)
                outcome, failure_class = (tl.FAIL, tl.TOOL_ERROR) if failed else (tl.PASS, None)
                rows.append(_row(step="workshop/%s/%s" % (stage, operation), tool="workshop", project=product,
                                 started=ended - wall, ended=ended, exit_code=None,
                                 reason="%d of %d failed" % (failed, aggregate.get("count", 0)) if failed else None,
                                 source="backfill:%s#%s/%s" % (path, stage, operation), evidence=str(path),
                                 outcome=outcome, failure_class=failure_class,
                                 extra={"aggregate": aggregate.get("count"), "times_estimated": True}))
    return rows


def _attach_gate_logs(rows: list) -> None:
    """A per-gate log belongs to the print-gates run (or seal) on the same
    project whose time span holds it: the smallest such run is its parent."""

    holders = [row for row in rows if row["tool"] in ("make_round", "seal_proof") and not row.get("parent")
               and not row.get("wall_unknown")]
    spans = [(tl.parse_iso(row["started_at"]), tl.parse_iso(row["ended_at"]), row) for row in holders]
    for row in rows:
        if not row.get("gate_log") or row.get("parent"):
            continue
        began, ended = tl.parse_iso(row["started_at"]), tl.parse_iso(row["ended_at"])
        inside = [(end - start, holder["id"]) for start, end, holder in spans
                  if holder.get("project") and row.get("project", "").startswith(holder["project"].rstrip("/"))
                  and start - 5 <= began and ended <= end + 5]
        if inside:
            row["parent"] = min(inside)[1]


def _attach_records(rows: list) -> None:
    """A batch record belongs to the seal log whose run wrote it: make its
    rows that log's children, so their time is not counted twice."""

    seals = [row for row in rows if row["step"] in ("seal_proof/seal", "seal_proof/preflight") and not row.get("parent")]
    for row in rows:
        if row["tool"] != "seeded_batch" or row.get("parent"):
            continue
        end = tl.parse_iso(row["ended_at"])
        for seal in seals:
            if (seal.get("project") and row.get("project", "").startswith(seal["project"].rstrip("/"))
                    and tl.parse_iso(seal["started_at"]) - 5 <= end <= tl.parse_iso(seal["ended_at"]) + 5):
                row["parent"] = seal["id"]
                break


def backfill(roots: Iterable[Path], ledger: Path, workshop_home: Optional[Path]) -> dict:
    existing = {row.get("source") for row in tl.read_rows(ledger) if str(row.get("source", "")).startswith("backfill:")}
    rows: list = []
    logs = []
    gate_dirs = []
    records = []
    for root in roots:
        for directory, names, files in os.walk(root):
            names[:] = sorted(name for name in names if name not in _SKIP_DIRS)
            here = Path(directory)
            for name in sorted(files):
                if name.endswith(".log"):
                    logs.append(here / name)
                elif name in ("seeded-batch.json", "seal-preflight.json") and here.name == "measure":
                    records.append(here / name)
    parsed_steps = defaultdict(list)
    seen_hashes: set = set()
    key_cache: dict = {}
    for path in logs:
        try:
            content = path.read_bytes()
        except OSError:
            continue
        if content.startswith(b"$ "):
            digest = hashlib.sha256(content).hexdigest()
            if digest in seen_hashes:
                continue  # a byte-identical backup copy of the same run
            seen_hashes.add(digest)
            gate_dirs.append(path.parent)
            made = backfill_gate_log(path, content, key_cache)
            if made is not None:
                rows.append(made)
            continue
        text = content.decode("utf-8", "replace")
        named = step_of_log(path, text)
        if named:
            parsed_steps[(path.parent, named[0])].append((path.stat().st_mtime, path))
    for (_, step), entries in sorted(parsed_steps.items(), key=lambda item: (str(item[0][0]), item[0][1])):
        entries.sort()
        for index, (_, path) in enumerate(entries):
            rows.extend(backfill_log(path, later_same_step=index < len(entries) - 1))
    for path in sorted(records):
        rows.extend(backfill_batch_record(path))
    if workshop_home is not None and (workshop_home / "state").is_dir():
        rows.extend(backfill_wish_timing(workshop_home / "state"))
    _attach_records(rows)
    _attach_gate_logs(rows)
    written = skipped = 0
    for row in rows:
        if row["source"] in existing:
            skipped += 1
            continue
        written += tl.append_row(row, ledger)
    return {"written": written, "skipped": skipped, "logs": len(logs), "gate_dirs": len(set(gate_dirs)),
            "records": len(records)}


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _ledger(value: Optional[str]) -> Path:
    path = Path(value) if value else tl.default_ledger_path()
    if path is None:
        raise SystemExit("process_review: the timing ledger is turned off (WORKSHOP_TIMING_LEDGER)")
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("report")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--today", help="the report's last day, YYYY-MM-DD (default: today, UTC)")
    p.add_argument("--ledger")
    p.add_argument("--out", help="default docs/research/process-review/<today>.md; '-' prints it")
    p = sub.add_parser("backfill")
    p.add_argument("roots", nargs="*", default=[str(REPO / "toys-spec")])
    p.add_argument("--ledger")
    p.add_argument("--workshop-home", help="default: the Workshop home; 'none' skips its run state")
    p = sub.add_parser("annotate")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--source", help="a row source, matched by prefix (backfill:<path>)")
    group.add_argument("--id", help="one row id")
    p.add_argument("--step", help="also match this step")
    p.add_argument("--class", dest="failure_class", required=True, choices=tl.FAILURE_CLASSES)
    p.add_argument("--note", required=True)
    p.add_argument("--ledger")
    args = parser.parse_args(argv)
    ledger = _ledger(args.ledger)
    if args.command == "annotate":
        match = {"source": args.source} if args.source else {"id": args.id}
        if args.step:
            match["step"] = args.step
        note = {"kind": ANNOTATION_KIND, "schema_version": 1, "match": match,
                "failure_class": args.failure_class, "note": args.note}
        if not tl.append_row(note, annotations_path(ledger)):
            print("process_review: could not write %s" % annotations_path(ledger), file=sys.stderr)
            return 1
        print("process_review: annotated %s as %s" % (json.dumps(match, sort_keys=True), args.failure_class))
        return 0
    if args.command == "backfill":
        if args.workshop_home == "none":
            home = None
        elif args.workshop_home:
            home = Path(args.workshop_home)
        else:
            from workshop.runtime.package_data import default_workshop_home
            home = Path(default_workshop_home())
        result = backfill([Path(root) for root in args.roots], ledger, home)
        print("process_review: backfill wrote %(written)d row(s), skipped %(skipped)d already there "
              "(%(logs)d logs, %(gate_dirs)d gate dirs, %(records)d batch records)" % result)
        return 0
    today = date.fromisoformat(args.today) if args.today else datetime.now(timezone.utc).date()
    rows = apply_annotations(tl.read_rows(ledger), read_annotations(ledger))
    text = build_report(rows, today=today, days=args.days, ledger=ledger)
    if args.out == "-":
        sys.stdout.write(text)
        return 0
    out = Path(args.out) if args.out else REPORT_DIR / ("%s.md" % today.isoformat())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print("process_review: wrote %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
