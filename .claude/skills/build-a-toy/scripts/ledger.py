#!/usr/bin/env python3
"""The build-a-toy ledger: validate it, classify a stop, and say what comes next.

    python3 ledger.py check LEDGER.json        # schema errors, exit 1 if any
    python3 ledger.py next LEDGER.json         # the loop's next action, as JSON
    python3 ledger.py classify EVIDENCE.json   # a stop's diagnosis class, as JSON
    python3 ledger.py fold CONTRACT.md STATUS.json --out NEW.md
                                               # merge a run's in-run amendments

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
import re
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

    folded_keys = set()
    for index, item in enumerate(_list(ledger, "in_run_amendments", errors)):
        where = f"in_run_amendments[{index}]"
        if not _is_int(item.get("attempt")) or not item.get("wish_id"):
            errors.append(f"{where} needs the attempt and wish_id that made it")
        if not _is_int(item.get("amendment")):
            errors.append(f"{where}.amendment is not the run's amendment number")
        key = (item.get("wish_id"), item.get("amendment"))
        if key in folded_keys:
            errors.append(f"{where} repeats amendment {key[1]} of {key[0]}")
        folded_keys.add(key)
        if not _strings(item.get("rows")) or len(item.get("rows") or []) < 2:
            errors.append(f"{where}.rows must quote at least two contract statements verbatim")
        changes = item.get("changes")
        if not isinstance(changes, list) or not changes or not all(
            isinstance(c, dict) and all(isinstance(c.get(k), str) and c[k] for k in ("row", "from", "to"))
            for c in changes
        ):
            errors.append(f"{where}.changes must list each row with its from and to text")
        if not isinstance(item.get("folded"), bool):
            errors.append(f"{where}.folded must be true or false")
        if item.get("folded") is True and item.get("contract_version") not in versions:
            errors.append(f"{where} is folded without a contract_versions key (`contract_version`)")

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
    for item in evidence.get("worker_blocked") or []:
        why.append(f"a Component Worker reported contradicting rows: {item}")
    for item in evidence.get("forced_repeats") or []:
        why.append(f"a repeated print defect a contract row forces: {item}")
    if evidence.get("blocked_reports_open"):
        # A budget stop can land before the root has a turn to answer a fresh
        # report (Broken God attempt 16: opened 13:38, budget 13:41, answered
        # 13:44 after the resume). With nothing else pointing at the contract,
        # the one raise of a progressing attempt is that turn; a report still
        # open at the next stop is a contradiction.
        unanswered_for_budget = (
            not why
            and evidence.get("stop_category") == "budget"
            and not evidence.get("budget_raised")
            and progressing(evidence.get("progress"), evidence.get("previous_progress"))
        )
        if unanswered_for_budget:
            return {
                "class": "budget-progressing",
                "why": [
                    f"{evidence['blocked_reports_open']} Blocked Report(s) open when the budget ran out "
                    "and nothing else points at the contract: the resume gives the root its turn to answer"
                ],
            }
        why.append(f"{evidence['blocked_reports_open']} Blocked Report(s) open or waiting")
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
        f"in-run amendment {item.get('wish_id')}#{item.get('amendment')}: fold it into CONTRACT.md"
        for item in ledger.get("in_run_amendments") or []
        if item.get("folded") is not True
    ] + [
        f"#{issue['number']}: {issue['status']}"
        for issue in ledger.get("harness_issues") or []
        if issue.get("opened_by_loop") and issue.get("status") in ("open", "implementing")
    ]
    if pending:
        return {"action": "fix", "pending": pending, "why": [f"diagnosed {last['class']}"]}
    return {"action": "launch", "attempt": loop["attempt"] + 1, "source_commit": loop.get("source_commit"),
            "why": ["nothing is pending"]}


_FENCE = re.compile(r"```design-contract\s*\n(.*?)```", re.DOTALL)


def applied_amendments(status: dict) -> list[dict]:
    """The applied in-run Contract Amendments (ADR 0085) a run's
    `workshop status --json` lists, oldest first."""

    return [
        item for item in status.get("contract_amendments") or []
        if isinstance(item, dict) and item.get("kind") == "contract-amendment" and item.get("status") == "applied"
    ]


def _row_text(block: dict, row: str) -> list:
    if row.startswith("interface:"):
        return [item for item in block.get("interfaces") or []
                if isinstance(item, dict) and f"interface:{item.get('id')}" == row]
    return [item for index, item in enumerate(block.get("requirements") or [])
            if isinstance(item, dict) and (item.get("id") == row or f"requirements[{index}]" == row)]


def fold(contract_text: str, status: dict, attempt: int | None = None) -> dict:
    """Merge every applied in-run amendment of one run into a contract.

    Each change replaces its row's text in the `design-contract` block, by
    its exact JSON string, so the rest of the file keeps its bytes. A change
    already in the contract is skipped; one whose row no longer reads as the
    run quoted it is refused and left for a hand fold. Returns the new text,
    what was folded, skipped and refused, and the ledger entries to record.
    """

    match = _FENCE.search(contract_text)
    if match is None:
        raise ValueError("the contract has no design-contract block")
    raw = match.group(1)
    folded, skipped, refused, entries = [], [], [], []
    wish_id = status.get("product_id")
    for item in applied_amendments(status):
        label = f"{wish_id}#{item.get('amendment')}"
        changed = held = False
        for change in item.get("changes") or []:
            block = json.loads(raw)
            rows = _row_text(block, str(change.get("row")))
            if len(rows) == 1 and rows[0].get("text") == change.get("to"):
                continue
            if len(rows) != 1 or rows[0].get("text") != change.get("from"):
                refused.append(f"{label} {change.get('row')}: the row no longer reads as the run quoted it")
                held = True
                continue
            spellings = {json.dumps(change["from"]), json.dumps(change["from"], ensure_ascii=False)}
            found = [spelling for spelling in spellings if spelling in raw]
            if len(found) != 1 or raw.count(found[0]) != 1:
                refused.append(f"{label} {change.get('row')}: the text appears more than once; fold it by hand")
                held = True
                continue
            ascii_only = found[0] == json.dumps(change["from"])
            raw = raw.replace(found[0], json.dumps(change["to"], ensure_ascii=ascii_only))
            changed = True
        if not held:
            (folded if changed else skipped).append(label)
        entries.append({
            "attempt": attempt,
            "wish_id": wish_id,
            "amendment": item.get("amendment"),
            "rows": list(item.get("rows") or []),
            "changes": [{k: c.get(k) for k in ("row", "from", "to")} for c in item.get("changes") or []],
            "reviewer": (item.get("review") or {}).get("reviewer"),
            "contract_sha256": item.get("contract_sha256"),
            "amended_sha256": item.get("amended_sha256"),
            "folded": not held,
            "contract_version": None,
        })
    json.loads(raw)
    text = contract_text[: match.start(1)] + raw + contract_text[match.end(1):]
    return {"contract": text, "folded": folded, "already": skipped, "refused": refused, "entries": entries}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("command", choices=("check", "next", "classify", "fold"))
    parser.add_argument("path")
    parser.add_argument("status", nargs="?", help="fold: the run's `workshop status --json`")
    parser.add_argument("--out", help="fold: where the folded contract is written")
    parser.add_argument("--attempt", type=int, help="fold: the attempt the run was")
    args = parser.parse_args(argv)
    if args.command == "fold":
        if not args.status or not args.out:
            parser.error("fold needs CONTRACT.md, STATUS.json and --out")
        with open(args.path, encoding="utf-8") as handle:
            text = handle.read()
        with open(args.status, encoding="utf-8") as handle:
            result = fold(text, json.load(handle), args.attempt)
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(result.pop("contract"))
        print(json.dumps(result, indent=2))
        return 1 if result["refused"] else 0
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
