"""Append-only reward ledger — state/REWARD_LEDGER.jsonl.

Every scored event is one JSON line (docs/CONTRACTS.md §1). The ledger
is the raw material for the meta loop, the bandit, and the integrity
divergence check — so it is append-only: nothing here ever rewrites or
deletes a row. postmortem discipline from text2cad ("One function so a
cycle can never be summarised two different ways"): spend_today() is
THE way today's spend is computed, and it reconciles two records of the
same events by max, never sum.

Why append (O_APPEND) instead of tmp+os.replace here: replace-the-file
would make every append O(file) and, worse, lose a concurrent append
between read and replace. A single flushed+fsynced write of one line is
crash-consistent on APFS; the only possible corruption is a truncated
LAST line, which rows() detects and skips with a warning instead of
raising — a half-written tail must never poison the whole history.
All other state files in this repo use tmp+os.replace as contracted.
"""

import json
import os
from datetime import datetime, timezone

KINDS = ("iteration", "send", "publish", "market", "human_table")

# Full row schema (CONTRACTS §1); append() fills defaults so a caller
# can't produce a row other readers choke on.
_DEFAULTS = {
    "score": 0.0,
    "components": {},
    "delta": 0.0,
    "cost_usd": 0.0,
    "notes": "",
}


def _home():
    # Env read inside the function, never at import (CONTRACTS §6:
    # testability — tests point BOB_HOME at a temp dir per test).
    return os.environ.get("BOB_HOME") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))


def _ledger_path():
    return os.path.join(_home(), "state", "REWARD_LEDGER.jsonl")


def _daybook_path():
    return os.path.join(_home(), "state", "DAYBOOK.json")


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def append(row):
    """Append one scored event. Fills 'at' and schema defaults.

    Requires slug + kind (kind in KINDS) — a row that can't be attributed
    to a game and an event type is noise the meta loop can't learn from.
    """
    if not isinstance(row, dict):
        raise ValueError("ledger.append() takes a dict row; got %r. "
                         "Build the row per CONTRACTS §1." % type(row).__name__)
    if not row.get("slug"):
        raise ValueError("Ledger row needs a 'slug' — every reward event "
                         "belongs to a game.")
    kind = row.get("kind")
    if kind not in KINDS:
        raise ValueError("Ledger row 'kind' must be one of %s; got %r."
                         % (list(KINDS), kind))
    full = dict(_DEFAULTS)
    full.update(row)
    full.setdefault("at", _now_iso())
    full.setdefault("stage", "")

    path = _ledger_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    line = json.dumps(full, sort_keys=True) + "\n"
    # One write, flushed and fsynced: the append itself is the atom.
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())
    return full


def rows(since=None, slug=None):
    """Read rows oldest-first. `since` is an ISO-8601 UTC prefix or full
    timestamp (string compare is correct for ISO UTC); `slug` filters to
    one game. A truncated/corrupt line is skipped, never raised — the
    ledger outlives any single crashed writer.
    """
    path = _ledger_path()
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                # Truncated tail from a crash mid-append: skip, don't die.
                continue
            if slug is not None and row.get("slug") != slug:
                continue
            if since is not None and str(row.get("at", "")) < str(since):
                continue
            out.append(row)
    return out


def spend_today():
    """Today's (UTC) spend in USD.

    Two records exist for the same events: ledger rows carry cost_usd,
    and state/DAYBOOK.json carries per-day cost_usd + step costs
    (written by the tick loop). They are the SAME dollars observed from
    two places, so we take the MAX of the two totals, never the sum —
    summing would double-count and trip the daily budget at half spend.
    (text2cad receipt: run.json under-reported real spend by 12%; two
    imperfect meters, trust the higher one.)
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    ledger_total = 0.0
    for row in rows(since=today):
        if str(row.get("at", "")).startswith(today):
            try:
                ledger_total += float(row.get("cost_usd", 0.0) or 0.0)
            except (TypeError, ValueError):
                continue

    daybook_total = 0.0
    path = _daybook_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                daybook = json.load(f)
        except ValueError:
            daybook = {}
        day = daybook.get(today) or {}
        if isinstance(day, dict):
            try:
                field_total = float(day.get("cost_usd", 0.0) or 0.0)
            except (TypeError, ValueError):
                field_total = 0.0
            steps_total = 0.0
            for step in day.get("steps", []) or []:
                if isinstance(step, dict):
                    try:
                        steps_total += float(step.get("cost_usd", 0.0) or 0.0)
                    except (TypeError, ValueError):
                        continue
                elif isinstance(step, (int, float)):
                    steps_total += float(step)
            # Same reconciliation inside the daybook itself: the day
            # field and its steps describe the same events.
            daybook_total = max(field_total, steps_total)

    return max(ledger_total, daybook_total)
