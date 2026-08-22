"""Tick time budget — the Peter-pattern with_budget ledger.

Why: text2cad's single 3-hour ceiling "killed healthy cycles ... publish
never ran and the whole spend was lost" — one big wall at the end loses
everything already paid for. The fix is the inverse: give the WHOLE tick a
total budget up front, then hand each step a cap that can never exceed
what's actually left. A tick then degrades gracefully — later steps get
squeezed, refused cleanly, and the tick still exits with its artifacts and
its ledger — instead of being shot mid-flight.

Contract (CONTRACTS §2 'timebudget'):
    open_run(total_minutes=25)          — start a fresh ledger for this tick
    step(cap_minutes) -> ctx manager    — yields the granted minutes;
                                          refuses (raises) when spent
    report() -> dict                    — totals + per-step rows

The granted value is min(cap, remaining) — "the last step gets
min(cap, remaining)" — so callers pass it straight into
run_agent(max_minutes=granted) and the run can never overshoot the tick.

Measurement is wall-clock (time.monotonic): agent subprocesses spend real
minutes whether or not Python is busy, and the launchd window is wall time.

Ledger lives at state/.tick-budget.json — a file, not module state, so a
crashed tick leaves an inspectable corpse and report() works from any
process. Stdlib only, Python 3.9. No env reads at import time.
"""

import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone

# Default matches the launchd cadence (30-min ticks): 25 minutes of work
# leaves 5 minutes of slack for the harness itself, so two ticks never
# overlap even when every step spends its full grant.
DEFAULT_TOTAL_MINUTES = 25


class BudgetExhausted(Exception):
    """The tick's time budget is spent. Do NOT start the step — end the
    tick cleanly and let the next tick pick the work up (idempotent
    catch-up is free; a killed half-step is not)."""


def _bob_home():
    """Repo root; BOB_HOME overrides. Read at call time (CONTRACTS §6)."""
    env = os.environ.get("BOB_HOME")
    if env:
        return os.path.abspath(env)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ledger_path():
    return os.path.join(_bob_home(), "state", ".tick-budget.json")


def _atomic_write(path, data):
    """tmp + os.replace: a crash mid-write must never half-corrupt the
    ledger the next report() reads."""
    tmp = "{}.tmp.{}".format(path, os.getpid())
    with open(tmp, "w") as f:
        f.write(data)
    os.replace(tmp, path)


def _load():
    path = _ledger_path()
    if not os.path.exists(path):
        raise BudgetExhausted(
            "No tick budget open at {}. Call open_run(total_minutes) at "
            "the start of the tick before taking any step.".format(path)
        )
    with open(path) as f:
        return json.load(f)


def _save(ledger):
    path = _ledger_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    _atomic_write(path, json.dumps(ledger, indent=1))


def _spent(ledger):
    return sum(float(s.get("minutes", 0.0)) for s in ledger.get("steps", []))


def open_run(total_minutes=DEFAULT_TOTAL_MINUTES):
    """Start a fresh budget ledger for this tick, replacing any prior one.

    Replacement (not append) is deliberate: each tick is a fresh run, and a
    stale ledger from a crashed tick must not eat the new tick's budget —
    the crash already paid its price in lost wall time.
    """
    ledger = {
        "opened": datetime.now(timezone.utc).isoformat(),
        "total_minutes": float(total_minutes),
        "steps": [],
    }
    _save(ledger)
    return ledger


@contextmanager
def step(cap_minutes):
    """Reserve one step of the tick. Yields granted minutes = min(cap,
    remaining); pass that straight to run_agent(max_minutes=granted).

    Refuses (BudgetExhausted) when the budget is spent — refusing BEFORE
    the step is the whole point: a step that starts and gets killed
    mid-flight loses its entire spend (the text2cad 3h-ceiling receipt),
    while a step that never starts costs nothing and retries free next
    tick.

    The elapsed wall time is recorded even when the step body raises:
    minutes spent on a failure are just as gone as minutes spent on a
    success, and the ledger must say where the tick's time actually went.
    """
    ledger = _load()
    remaining = ledger["total_minutes"] - _spent(ledger)
    if remaining <= 0:
        raise BudgetExhausted(
            "Tick budget spent ({:.2f}/{:.2f} min used). Refusing to start "
            "a {}-min step — end the tick; the next tick continues the "
            "work.".format(
                _spent(ledger), ledger["total_minutes"], cap_minutes
            )
        )
    granted = min(float(cap_minutes), remaining)
    t0 = time.monotonic()
    try:
        yield granted
    finally:
        elapsed_min = (time.monotonic() - t0) / 60.0
        # Reload before append: the step body may itself have taken
        # nested/parallel steps, and clobbering their rows would repeat
        # text2cad's 12%-low self-accounting.
        ledger = _load()
        ledger["steps"].append(
            {
                "at": datetime.now(timezone.utc).isoformat(),
                "cap": float(cap_minutes),
                "granted": granted,
                "minutes": elapsed_min,
            }
        )
        _save(ledger)


def report():
    """Totals + rows for the current ledger — the tick's time postmortem.

    Deterministic, no LLM, always runs (the postmortem principle): a tick
    that died still reports where its minutes went.
    """
    ledger = _load()
    spent = _spent(ledger)
    return {
        "opened": ledger.get("opened"),
        "total_minutes": ledger["total_minutes"],
        "spent_minutes": spent,
        "remaining_minutes": max(0.0, ledger["total_minutes"] - spent),
        "steps": list(ledger.get("steps", [])),
    }
