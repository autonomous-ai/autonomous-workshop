#!/usr/bin/env python3
"""The build-a-toy ledger: validate it, classify a stop, and say what comes next.

    python3 ledger.py check LEDGER.json        # schema errors, exit 1 if any
    python3 ledger.py next LEDGER.json         # the loop's next action, as JSON
    python3 ledger.py classify EVIDENCE.json   # a stop's diagnosis class, as JSON

The ledger is the unattended loop's only memory: a new session resumes the
loop by running `next` on it and doing what it prints. LEDGER.md describes
every field. A ledger without a `loop` object predates the unattended mode;
`check` accepts it and `next` asks for it to be migrated.

Everything here is deterministic bookkeeping. The diagnosis itself (reading
the receipt, the transcripts and the component rounds) is the agent's; the
evidence it found goes into `classify`, which applies the fixed precedence.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Iterable

SCHEMA = 1
STATES = ("launch", "watching", "diagnosing", "fixing", "awaiting-owner", "stopped", "done")
CLASSES = (
    "complete",
    "camera-need",
    "contract-contradiction",
    "reference-mismatch",
    "harness-defect",
    "budget-progressing",
    "other",
)
ISSUE_STATES = ("open", "implementing", "merged", "failed", "conflict", "abandoned")
CHECK_STATES = ("proposed", "open", "merged")
DEFAULT_COST_CAP = 100.0
NO_PROGRESS_LIMIT = 3
BUDGET_RAISE_TOKENS = 100_000_000


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _strings(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) and v.strip() for v in value)


def check(ledger: dict) -> list[str]:
    """Every schema error in a ledger; an empty list means it is valid."""

    errors: list[str] = []
    if not isinstance(ledger, dict):
        return ["the ledger is not a JSON object"]
    for key in ("contract", "title", "rounds"):
        if key not in ledger:
            errors.append(f"missing `{key}`")
    if not isinstance(ledger.get("rounds", []), list):
        errors.append("`rounds` is not a list")
    if "loop" not in ledger:
        return errors

    loop = ledger["loop"]
    if not isinstance(loop, dict):
        return errors + ["`loop` is not an object"]
    if loop.get("schema") != SCHEMA:
        errors.append(f"loop.schema is {loop.get('schema')!r}, expected {SCHEMA}")
    if loop.get("state") not in STATES:
        errors.append(f"loop.state {loop.get('state')!r} is not one of {', '.join(STATES)}")
    if not _is_int(loop.get("attempt")):
        errors.append("loop.attempt is not an integer")
    if loop.get("state") == "watching" and not loop.get("wish_id"):
        errors.append("loop.state is watching but loop.wish_id is empty")
    awaiting = loop.get("awaiting")
    if loop.get("state") == "awaiting-owner":
        if not isinstance(awaiting, dict) or not _strings(awaiting.get("reasons")) or not awaiting["reasons"]:
            errors.append("loop.state is awaiting-owner but loop.awaiting.reasons is empty")
    elif awaiting not in (None, {}):
        errors.append("loop.awaiting is set but loop.state is not awaiting-owner")

    versions = ledger.get("contract_versions") or {}
    raised: dict[int, int] = {}
    for index, stop in enumerate(_list(ledger, "stops", errors)):
        where = f"stops[{index}]"
        if not _is_int(stop.get("attempt")):
            errors.append(f"{where}.attempt is not an integer")
        if not stop.get("wish_id"):
            errors.append(f"{where}.wish_id is empty")
        if stop.get("class") not in CLASSES:
            errors.append(f"{where}.class {stop.get('class')!r} is not one of {', '.join(CLASSES)}")
        if not _strings(stop.get("evidence")) or not stop.get("evidence"):
            errors.append(f"{where}.evidence must list at least one finding")
        progress = stop.get("progress")
        if not isinstance(progress, dict) or not all(
            _is_int(progress.get(k)) for k in ("locked", "repeated_print_defects")
        ):
            errors.append(f"{where}.progress needs integer locked and repeated_print_defects")
        if stop.get("budget_raised") is True:
            raised[stop.get("attempt")] = raised.get(stop.get("attempt"), 0) + 1
    for attempt, count in sorted(raised.items(), key=lambda item: str(item[0])):
        if count > 1:
            errors.append(f"attempt {attempt} raised its token budget {count} times; the rule allows once")

    seen_ids = set()
    for index, item in enumerate(_list(ledger, "contract_contradictions", errors)):
        where = f"contract_contradictions[{index}]"
        if not item.get("id") or item.get("id") in seen_ids:
            errors.append(f"{where}.id is empty or repeated")
        seen_ids.add(item.get("id"))
        if not _is_int(item.get("attempt")):
            errors.append(f"{where}.attempt is not an integer")
        if not isinstance(item.get("signature"), str) or ":" not in item.get("signature", ""):
            errors.append(f"{where}.signature must be `<check>:<component>`")
        if not _strings(item.get("rows")) or len(item.get("rows") or []) < 2:
            errors.append(f"{where}.rows must quote at least two contract statements verbatim")
        amendment = item.get("amendment")
        if amendment is not None and amendment not in versions:
            errors.append(f"{where}.amendment {amendment!r} is not in contract_versions")
        if not isinstance(item.get("visible"), bool):
            errors.append(f"{where}.visible must be true or false")
        approved = item.get("approved")
        if item.get("visible") is True and approved == "not-needed":
            errors.append(f"{where} is a visible change, so it needs the owner's approval")
        if approved is not None and approved != "not-needed" and not str(approved).startswith("owner "):
            errors.append(f"{where}.approved must be null, `not-needed` or `owner <date>`")
        if not isinstance(item.get("applied"), bool):
            errors.append(f"{where}.applied must be true or false")
        if item.get("applied") is True and approved is None:
            errors.append(f"{where} is applied before it was approved")
        if item.get("applied") is True and not item.get("reaudit"):
            errors.append(f"{where} is applied without a whole-contract re-audit (`reaudit`)")
        design = item.get("design_check")
        if not isinstance(design, dict) or not design.get("name") or design.get("status") not in CHECK_STATES:
            errors.append(f"{where}.design_check needs a name and a status ({', '.join(CHECK_STATES)})")

    numbers = set()
    for index, issue in enumerate(_list(ledger, "harness_issues", errors)):
        where = f"harness_issues[{index}]"
        if not _is_int(issue.get("number")) or issue.get("number") in numbers:
            errors.append(f"{where}.number is missing or repeated")
        numbers.add(issue.get("number"))
        if not isinstance(issue.get("opened_by_loop"), bool):
            errors.append(f"{where}.opened_by_loop must be true or false")
        if issue.get("status") not in ISSUE_STATES:
            errors.append(f"{where}.status {issue.get('status')!r} is not one of {', '.join(ISSUE_STATES)}")
        if issue.get("status") == "merged" and not issue.get("merge_commit"):
            errors.append(f"{where} is merged without a merge_commit")
        if issue.get("status") == "implementing" and issue.get("opened_by_loop") is False:
            errors.append(f"{where}: the loop implements only issues it opened")

    cost = ledger.get("cost_units")
    if not isinstance(cost, dict):
        errors.append("`cost_units` is missing")
    else:
        by_attempt = cost.get("by_attempt")
        if not isinstance(by_attempt, dict) or not all(
            isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0 for v in by_attempt.values()
        ):
            errors.append("cost_units.by_attempt must map attempt numbers to cost units")
        else:
            total = round(sum(by_attempt.values()), 2)
            if abs(total - float(cost.get("total", -1))) > 0.011:
                errors.append(f"cost_units.total {cost.get('total')} is not the sum of by_attempt ({total})")
        if not isinstance(cost.get("cap", DEFAULT_COST_CAP), (int, float)) or cost.get("cap", 1) <= 0:
            errors.append("cost_units.cap must be a positive number")
    return errors


def _list(ledger: dict, key: str, errors: list[str]) -> list[dict]:
    value = ledger.get(key, [])
    if not isinstance(value, list) or not all(isinstance(v, dict) for v in value):
        errors.append(f"`{key}` must be a list of objects")
        return []
    return value


def progressing(progress: dict | None, previous: dict | None) -> bool:
    """New locked Components, or fewer repeated print defects, than before."""

    if not progress:
        return False
    if not previous:
        return progress.get("locked", 0) > 0
    return (
        progress.get("locked", 0) > previous.get("locked", 0)
        or progress.get("repeated_print_defects", 0) < previous.get("repeated_print_defects", 0)
    )


def classify(evidence: dict) -> dict:
    """A stop's class from the evidence found, in the fixed precedence.

    Evidence keys, each optional: status, stop_category, needs (objects with
    `kind` and `text`), blocked_reports_open, worker_blocked, forced_repeats,
    reference_mismatches, harness_defects, progress, previous_progress,
    budget_raised.
    """

    needs = evidence.get("needs") or []
    kinds = {need.get("kind") for need in needs}
    why: list[str]
    if evidence.get("status") == "complete" and not evidence.get("stop_category"):
        return {"class": "complete", "why": ["the run completed"]}
    if "camera" in kinds:
        return {"class": "camera-need", "why": ["a Reference Camera mismatch need keeps its existing path"]}
    why = []
    if "contract-contradiction" in kinds:
        why.append("a need quotes contradicting contract statements")
    if evidence.get("blocked_reports_open"):
        why.append(f"{evidence['blocked_reports_open']} Blocked Report(s) open or waiting")
    for item in evidence.get("worker_blocked") or []:
        why.append(f"a Component Worker reported contradicting rows: {item}")
    for item in evidence.get("forced_repeats") or []:
        why.append(f"a repeated print defect a contract row forces: {item}")
    if why:
        return {"class": "contract-contradiction", "why": why}
    if evidence.get("reference_mismatches"):
        return {"class": "reference-mismatch", "why": list(evidence["reference_mismatches"])}
    if evidence.get("harness_defects"):
        return {"class": "harness-defect", "why": list(evidence["harness_defects"])}
    if evidence.get("stop_category") == "budget":
        if evidence.get("budget_raised"):
            return {"class": "other", "why": ["a second budget stop in this attempt is diagnosed like any other stop"]}
        if progressing(evidence.get("progress"), evidence.get("previous_progress")):
            return {"class": "budget-progressing", "why": ["budget stop while Components still lock or repeats fall"]}
        return {"class": "other", "why": ["budget stop without progress"]}
    return {"class": "other", "why": [f"stop_category {evidence.get('stop_category')!r} with no known cause"]}


def _final_stops(stops: Iterable[dict]) -> list[dict]:
    """The last recorded stop of each attempt, in attempt order."""

    final: dict[int, dict] = {}
    for stop in stops:
        final[stop["attempt"]] = stop
    return [final[a] for a in sorted(final)]


def stop_conditions(ledger: dict) -> list[str]:
    """Every reason the loop must stop and ask the owner now."""

    reasons: list[str] = []
    fixed: dict[str, dict] = {}
    for item in ledger.get("contract_contradictions") or []:
        earlier = fixed.get(item.get("signature"))
        acknowledged = str(item.get("recurrence_acknowledged") or "").startswith("owner ")
        if earlier is not None and item.get("attempt", 0) > earlier.get("attempt", 0) and not acknowledged:
            reasons.append(
                f"Contract Contradiction {item['signature']} came back in attempt {item['attempt']} "
                f"after {earlier.get('amendment')} fixed it"
            )
        if item.get("applied") is True and item.get("signature") not in fixed:
            fixed[item["signature"]] = item

    streak = 0
    cleared = (ledger.get("loop") or {}).get("no_progress_cleared_through") or 0
    finals = _final_stops(
        s for s in ledger.get("stops") or [] if s.get("class") != "complete" and s.get("attempt", 0) >= cleared
    )
    for previous, current in zip(finals, finals[1:]):
        streak = 0 if progressing(current.get("progress"), previous.get("progress")) else streak + 1
    if streak >= NO_PROGRESS_LIMIT:
        reasons.append(f"{streak} consecutive attempts made no progress (locked Components, repeated print defects)")

    cost = ledger.get("cost_units") or {}
    cap = float(cost.get("cap", DEFAULT_COST_CAP))
    total = float(cost.get("total", 0))
    if total > cap:
        reasons.append(f"cumulative cost {total:g} cost units passed the cap of {cap:g}")

    for issue in ledger.get("harness_issues") or []:
        if issue.get("status") == "failed":
            reasons.append(f"harness issue #{issue['number']} fails tests the loop cannot fix")
        elif issue.get("status") == "conflict":
            reasons.append(f"harness issue #{issue['number']} meets a merge conflict on main")

    for item in ledger.get("contract_contradictions") or []:
        if item.get("visible") is True and item.get("approved") is None:
            reasons.append(f"visible change {item.get('amendment')} ({item['id']}) awaits the owner's approval")
    return reasons


def next_action(ledger: dict) -> dict:
    """What the loop does next, from the ledger alone."""

    errors = check(ledger)
    if "loop" not in ledger:
        return {"action": "migrate", "why": ["the ledger has no `loop`; add the fields LEDGER.md lists"]}
    if errors:
        return {"action": "repair-ledger", "why": errors}
    loop = ledger["loop"]
    reasons = stop_conditions(ledger)
    state = loop["state"]
    if state == "diagnosing":
        # A stop is diagnosed even when the loop must then stop: the owner is
        # asked once, with the diagnosis in hand.
        action = {"action": "diagnose", "wish_id": loop.get("wish_id"), "why": ["the last stop has no class yet"]}
        if reasons:
            action["then_ask_owner"] = reasons
        return action
    if reasons:
        return {"action": "ask-owner", "why": reasons}
    if state == "awaiting-owner":
        return {"action": "ask-owner", "why": loop["awaiting"]["reasons"]}
    if state in ("stopped", "done"):
        return {"action": state, "why": [f"loop.state is {state}"]}
    if state == "watching":
        return {"action": "watch", "wish_id": loop["wish_id"], "why": ["an attempt is running"]}
    if state == "launch":
        return {
            "action": "launch",
            "attempt": loop["attempt"] + 1,
            "source_commit": loop.get("source_commit"),
            "why": ["every fix is applied; start the next attempt from a fresh worktree"],
        }
    stops = [s for s in ledger.get("stops") or [] if s.get("wish_id") == loop.get("wish_id")]
    if not stops:
        return {"action": "diagnose", "wish_id": loop.get("wish_id"), "why": ["the last stop has no class yet"]}
    last = stops[-1]
    if last["class"] == "budget-progressing" and not any(s.get("budget_raised") for s in stops):
        return {
            "action": "resume-budget",
            "wish_id": last["wish_id"],
            "raise_tokens": BUDGET_RAISE_TOKENS,
            "why": ["a budget stop while progressing is resumed once with a raised cap"],
        }
    pending = [
        f"{item['id']}: apply {item.get('amendment')} and re-audit"
        for item in ledger.get("contract_contradictions") or []
        if item.get("applied") is not True
    ] + [
        f"#{issue['number']}: {issue['status']}"
        for issue in ledger.get("harness_issues") or []
        if issue.get("opened_by_loop") and issue.get("status") in ("open", "implementing")
    ]
    if pending:
        return {"action": "fix", "pending": pending, "why": [f"diagnosed {last['class']}"]}
    return {"action": "launch", "attempt": loop["attempt"] + 1, "source_commit": loop.get("source_commit"),
            "why": ["nothing is pending"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("command", choices=("check", "next", "classify"))
    parser.add_argument("path")
    args = parser.parse_args(argv)
    with open(args.path, encoding="utf-8") as handle:
        data = json.load(handle)
    if args.command == "check":
        errors = check(data)
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        return 1 if errors else 0
    if args.command == "classify":
        print(json.dumps(classify(data), indent=2))
        return 0
    print(json.dumps(next_action(data), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
