"""Host side of in-run Contract Amendments (ADR 0085).

Where a Contract Contradiction's smallest fix changes nothing a sealed
reference image shows, the Workshop Manager may propose a Contract Amendment
with the run-local ``make_round --propose-amendment`` instead of stopping on a
need. A fresh Contract Reviewer confirms it, and ``make_round
--record-amendment-review`` records that verdict. Both events are appended
to the CAD project's ``measure/contract-amendments.jsonl``.

The host trusts none of that ledger's conclusions. Before it accepts Make it
replays every event against the Design Contract ``WISH.json`` sealed: each
proposal must name the contract hash the applied amendments before it leave,
and each change the row text as it then reads; each amendment needs a
recorded review; a status is derived from the reviewer's verdict (the rows
contradict, the change is the smallest, no reference shows it), never read;
and the packet the reviewer judged must hold every sealed reference by its
sealed hash. In a run that binds reviewers (Claude Code), the reviewer must
be a ``contract-reviewer`` the runtime started, fresh to this amendment,
that read every sealed reference image. ``WISH.json`` and the images keep
their bytes. The Make gate receipt then records each amendment by hash: the
old and new row text, the reviewer's record and the contract hash before and
after. Nothing here judges an amendment or writes one.

Issue #96 amends ADR 0085 with one Smaller Retry: when the only earlier
amendment quoting the same rows was refused because the reviewer found a
smaller change (the rows contradict, no reference shows it, ``smallest`` is
false), the Manager may propose once more with the same rows, each change
the refused change's ``from`` with only deletions applied, to another fresh
reviewer. Any other proposal quoting rows an earlier amendment quoted is
refused here.

Issue #100 adds the Owner Contract Amendment: when a run stops on a Contract
Contradiction need, the owner may answer it on resume (``workshop resume
--amend-contract CONTRACT.md``) with the amended contract file instead of a
new attempt. The host diffs that file against the contract the run reads
now and refuses anything beyond requirement text, Interface text and prose;
the run keeps its sealed name line. It records the change by hash beside
``WISH.json`` (the run root's ``CONTRACT-AMENDMENTS.json``) and in its own
host-correction ledger. Rounds read the owner's rows after every applied
in-run amendment, and in-run amendments close: the replay before Make
acceptance refuses one numbered after the owner's first amendment.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from workshop.errors import ContractError

AMENDMENT_LEDGER_NAME = "contract-amendments.jsonl"
MAX_AMENDMENT_LEDGER_BYTES = 1024 * 1024
MAX_AMENDMENT_PACKET_BYTES = 256 * 1024
MAX_AMENDMENT_ROWS = 8
MAX_AMENDMENT_CHANGES = 4
MAX_AMENDMENT_TEXT = 4000
MAX_AMENDMENT_REASON = 1000
GEOMETRY_SCOPE = "geometry:"
INTERFACE_ROW = "interface:"
# Names that identify the Workshop Manager; kept in step with make_round.
MANAGER_NAMES = frozenset({"workshop-manager", "manager", "workshop manager"})
_VERDICT_KEYS = frozenset({"contradiction", "smallest", "visible_in", "references_checked", "reason"})
_SHA256 = re.compile(r"[0-9a-f]{64}")
_MAKE_ATTEMPTS = ("artifacts", "make")
_INSTANCE = re.compile(r"^(.+)#[1-9][0-9]*$")
# Issue #100: a run's make_round and Make finalizer apply an Owner Contract
# Amendment only when they carry this marker (kept in step with both).
OWNER_AMENDMENTS_MARKER = b"workshop-owner-contract-amendments-v1"
OWNER_AMENDMENT_KIND = "owner-contract-amendment"
# The round's name line build-a-toy prepends to the contract it seals; the
# run keeps the one it sealed.
NAME_LINE = re.compile(r"Name this (?:toy|revision) exactly: [^\n]*")
_FENCE = re.compile(r"```design-contract\s*\n(.*?)```", re.DOTALL)
_PROSE_BLOCK = "```design-contract\n(the design-contract block)\n```"


def contract_digest(contract: Mapping[str, Any]) -> str:
    """sha256 of a Design Contract's canonical JSON."""

    return hashlib.sha256(
        json.dumps(contract, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _text(value: Any, maximum: int) -> bool:
    return isinstance(value, str) and 1 <= len(value.strip()) <= maximum


def _apply(contract: Mapping[str, Any], changes: Sequence[Mapping[str, Any]], label: str) -> dict:
    """``contract`` with each change's row text replaced; refuses a change
    that names no requirement or Interface text, or quotes it wrongly."""

    amended = json.loads(json.dumps(contract))
    for change in changes:
        row = change["row"]
        if row.startswith(INTERFACE_ROW):
            items = [
                item for item in amended.get("interfaces") or ()
                if isinstance(item, dict) and INTERFACE_ROW + str(item.get("id")) == row
                and isinstance(item.get("text"), str)
            ]
            scope = row
        else:
            items = [
                item for index, item in enumerate(amended.get("requirements") or ())
                if isinstance(item, dict)
                and (item.get("id") == row or "requirements[%d]" % index == row)
            ]
            scope = items[0].get("scope") if len(items) == 1 else None
        if len(items) != 1 or items[0].get("text") != change["from"] or change["scope"] != scope:
            raise ContractError(
                "%s changes %s, which is not a requirement or Interface text that reads as "
                "it quotes; a reference, a geometry and an Interface's other fields are "
                "beyond an in-run amendment" % (label, row)
            )
        items[0]["text"] = change["to"]
    return amended


def _squash_rows(rows: Sequence[str]) -> list[str]:
    return sorted(" ".join(row.split()) for row in rows)


def deletions_only(old: str, new: str) -> bool:
    """``new`` is ``old`` with only deletions applied: strictly shorter, a
    character subsequence of ``old``, and every word of ``new`` a word of
    ``old`` in the same order, so no word is added or respelled."""

    if not isinstance(old, str) or not isinstance(new, str) or len(new) >= len(old):
        return False
    characters = iter(old)
    if not all(character in characters for character in new):
        return False
    words = iter(re.findall(r"\w+", old))
    return all(word in words for word in re.findall(r"\w+", new))


def retry_refusal(
    earlier: Sequence[Mapping[str, Any]], rows: Sequence[str], changes: Sequence[Mapping[str, Any]]
) -> tuple[Optional[int], Optional[str]]:
    """``(retry_of, refusal)`` for a proposal quoting ``rows`` after the
    ``earlier`` amendments (issue #96). ``retry_of`` is the refused
    amendment a Smaller Retry follows, or None when no earlier amendment
    quotes the same rows; ``refusal`` says why the proposal may not be made,
    or is None. Kept in step with make_round."""

    same = [item for item in earlier if _squash_rows(item["rows"]) == _squash_rows(rows)]
    if not same:
        return None, None
    first = same[0]
    number = first["amendment"]
    if len(same) > 1:
        return number, (
            "Contract Amendments %s already quote these rows; a contradiction gets one Smaller "
            "Retry at most, so the run stops on the need"
            % ", ".join(str(item["amendment"]) for item in same)
        )
    verdict = (first.get("review") or {}).get("verdict") or {}
    if first.get("status") != "refused" or not (
        verdict.get("contradiction") is True
        and verdict.get("smallest") is False
        and not verdict.get("visible_in")
    ):
        return number, (
            "Contract Amendment %d already quotes these rows and was %s; only a refusal that "
            "names a smaller change (contradiction true, nothing visible, smallest false) "
            "allows one Smaller Retry" % (number, first.get("status"))
        )
    refused = {change["row"]: change for change in first["changes"]}
    for change in changes:
        before = refused.get(change["row"])
        if before is None or before["from"] != change["from"]:
            return number, (
                "a Smaller Retry of Contract Amendment %d changes only rows it changed, from "
                "the same text; %s is not one" % (number, change["row"])
            )
        if not deletions_only(change["from"], change["to"]):
            return number, (
                "a Smaller Retry of Contract Amendment %d only deletes words from %s's text; "
                "%r adds or respells text" % (number, change["row"], change["to"][:80])
            )
    if {change["row"]: change["to"] for change in changes} == {
        row: change["to"] for row, change in refused.items()
    }:
        return number, (
            "a Smaller Retry of Contract Amendment %d repeats the refused change" % number
        )
    return number, None


def _roles(entries: Any) -> set[str]:
    roles = set()
    for entry in entries if isinstance(entries, list) else ():
        if isinstance(entry, str):
            match = _INSTANCE.fullmatch(entry)
            roles.add(match.group(1) if match else entry)
    return roles


def _affects(contract: Mapping[str, Any], changes: Sequence[Mapping[str, Any]]) -> list[str]:
    every = {
        item["id"] for item in contract.get("geometries") or ()
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    affected: set[str] = set()
    for change in changes:
        if change["row"].startswith(INTERFACE_ROW):
            for item in contract.get("interfaces") or ():
                if isinstance(item, dict) and INTERFACE_ROW + str(item.get("id")) == change["row"]:
                    affected |= _roles(item.get("components"))
        elif isinstance(change["scope"], str) and change["scope"].startswith(GEOMETRY_SCOPE):
            affected.add(change["scope"][len(GEOMETRY_SCOPE):])
        else:
            affected |= every
    return sorted(affected)


def replay_contract_amendments(
    content: str, contract: Mapping[str, Any], *, wish_sha256: Optional[str] = None
) -> list[dict[str, Any]]:
    """Every amendment in one ledger, oldest first, replayed against the
    sealed ``contract``. Each is ``proposed``, ``applied`` or ``refused``;
    raises ``ContractError`` for a ledger that does not replay."""

    amendments: list[dict[str, Any]] = []
    current: Mapping[str, Any] = contract
    for line in content.splitlines():
        try:
            event = json.loads(line)
        except ValueError as exc:
            raise ContractError("a Contract Amendment event is not JSON") from exc
        if not isinstance(event, dict):
            raise ContractError("a Contract Amendment event is not an object")
        kind, number = event.get("event"), event.get("amendment")
        if type(number) is not int or not _text(event.get("at"), 64):
            raise ContractError("a Contract Amendment event has no number or time")
        label = "Contract Amendment %d" % number
        if wish_sha256 is not None and event.get("wish_sha256") != wish_sha256:
            raise ContractError("%s is not bound to this run's Wish" % label)
        if kind == "proposal":
            if number != len(amendments) + 1 or any(
                item["status"] == "proposed" for item in amendments
            ):
                raise ContractError("%s is out of order" % label)
            rows, changes = event.get("rows"), event.get("changes")
            if (
                not isinstance(rows, list)
                or not 2 <= len(rows) <= MAX_AMENDMENT_ROWS
                or not all(_text(row, MAX_AMENDMENT_TEXT) for row in rows)
                or not isinstance(changes, list)
                or not 1 <= len(changes) <= MAX_AMENDMENT_CHANGES
                or not all(
                    isinstance(change, dict)
                    and set(change) == {"row", "scope", "from", "to"}
                    and _text(change["row"], 200)
                    and isinstance(change["from"], str)
                    and _text(change["to"], MAX_AMENDMENT_TEXT)
                    for change in changes
                )
                or len({change["row"] for change in changes}) != len(changes)
                or not _text(event.get("reason"), MAX_AMENDMENT_TEXT)
                or not isinstance(event.get("packet"), str)
                or not (
                    isinstance(event.get("packet_sha256"), str)
                    and _SHA256.fullmatch(event["packet_sha256"])
                )
                or not (event.get("report") is None or type(event.get("report")) is int)
            ):
                raise ContractError("%s is invalid" % label)
            before = contract_digest(current)
            if event.get("contract_sha256") != before:
                raise ContractError(
                    "%s was proposed against contract %s, but the sealed contract and the "
                    "amendments applied before it make %s"
                    % (label, str(event.get("contract_sha256"))[:12], before[:12])
                )
            retry_of, refusal = retry_refusal(amendments, rows, changes)
            if refusal is not None:
                raise ContractError("%s: %s" % (label, refusal))
            if event.get("retry_of") != retry_of:
                raise ContractError(
                    "%s names retry_of %r, but the ledger makes it %r"
                    % (label, event.get("retry_of"), retry_of)
                )
            amended = _apply(current, changes, label)
            if event.get("amended_sha256") != contract_digest(amended):
                raise ContractError("%s names the wrong amended contract hash" % label)
            amendments.append({
                "kind": "contract-amendment",
                "amendment": number,
                "status": "proposed",
                "rows": list(rows),
                "changes": [
                    {key: change[key] for key in ("row", "from", "to")} for change in changes
                ],
                "reason": event["reason"],
                "report": event.get("report"),
                "retry_of": retry_of,
                "affects": _affects(current, changes),
                "packet": event["packet"],
                "packet_sha256": event["packet_sha256"],
                "contract_sha256": before,
                "amended_sha256": event["amended_sha256"],
                "proposed_at": event["at"],
                "review": None,
                "_amended": amended,
            })
            continue
        if kind != "review":
            raise ContractError("unknown Contract Amendment event %r" % (kind,))
        if number != len(amendments) or amendments[-1]["status"] != "proposed":
            raise ContractError("%s is not awaiting review" % label)
        item = amendments[-1]
        verdict = event.get("verdict")
        if (
            not isinstance(verdict, dict)
            or set(verdict) != _VERDICT_KEYS
            or type(verdict["contradiction"]) is not bool
            or type(verdict["smallest"]) is not bool
            or not isinstance(verdict["visible_in"], list)
            or not all(isinstance(name, str) for name in verdict["visible_in"])
            or not isinstance(verdict["references_checked"], list)
            or not all(isinstance(name, str) for name in verdict["references_checked"])
            or not _text(verdict["reason"], MAX_AMENDMENT_REASON)
            or not _text(event.get("reviewer"), 200)
        ):
            raise ContractError("the review of %s is invalid" % label)
        item["review"] = {
            "reviewer": event["reviewer"].strip(), "verdict": verdict, "at": event["at"],
        }
        agrees = (
            verdict["contradiction"] is True
            and verdict["smallest"] is True
            and not verdict["visible_in"]
        )
        item["status"] = "applied" if agrees else "refused"
        if agrees:
            current = item["_amended"]
    return amendments


def _read_ledger(ledger: Path) -> str:
    try:
        identity = ledger.lstat()
        if not stat.S_ISREG(identity.st_mode) or identity.st_size > MAX_AMENDMENT_LEDGER_BYTES:
            raise ValueError("not a bounded regular file")
        return ledger.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError) as exc:
        raise ContractError("the Contract Amendment ledger is invalid: %s" % exc) from exc


def read_amendment_ledger(ledger: Path) -> str:
    """One Contract Amendment ledger's text, refusing anything but a bounded
    regular file."""

    return _read_ledger(Path(ledger))


def _record(item: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if not key.startswith("_")}


def verify_contract_amendments(
    project: Path,
    *,
    contract: Optional[Mapping[str, Any]],
    wish_sha256: str,
    references: Mapping[str, tuple[Path, str]],
    blocked_reports: Sequence[Mapping[str, Any]] = (),
    reviewer_check: Optional[Any] = None,
    owner_amendments: Sequence[Mapping[str, Any]] = (),
) -> list[dict[str, Any]]:
    """Refuse Make output whose Contract Amendments do not replay; return
    every amendment, applied or refused, as the Make gate receipt records it,
    then every owner amendment the host recorded (issue #100), which closes
    in-run amendments after the number the ledger had reached.

    ``references`` maps each sealed reference file to its run path and sealed
    sha256. ``blocked_reports`` are the run's Blocked Reports: one cleared by
    an amendment needs that applied amendment to name it. ``reviewer_check``,
    in a run that binds reviewers, is called with ``(reviewer, images, label)``
    and refuses a reviewer the runtime cannot prove.
    """

    ledger = Path(project) / "measure" / AMENDMENT_LEDGER_NAME
    amendments: list[dict[str, Any]] = []
    if ledger.exists() or ledger.is_symlink():
        if contract is None:
            raise ContractError("a Contract Amendment needs a run sealed with a Design Contract")
        amendments = replay_contract_amendments(
            _read_ledger(ledger), contract, wish_sha256=wish_sha256
        )
    if owner_amendments and contract is None:
        raise ContractError("an owner amendment needs a run sealed with a Design Contract")
    refusal = owner_closure_refusal(amendments, owner_amendments)
    if refusal is not None:
        raise ContractError(refusal)
    seen_reviewers: dict[str, int] = {}
    images = {
        os.path.realpath(path): digest for path, digest in references.values()
    }
    for item in amendments:
        label = "Contract Amendment %d" % item["amendment"]
        if item["review"] is None:
            raise ContractError(
                "%s has no recorded review; a fresh contract-reviewer confirms it with "
                "make_round --record-amendment-review, or the run stops on a need" % label
            )
        packet_path = Path(item["packet"])
        try:
            if packet_path.is_symlink() or not packet_path.is_file() or (
                packet_path.stat().st_size > MAX_AMENDMENT_PACKET_BYTES
            ):
                raise ValueError("not a bounded regular file")
            content = packet_path.read_bytes()
            if hashlib.sha256(content).hexdigest() != item["packet_sha256"]:
                raise ValueError("changed")
            packet = json.loads(content)
            shown = {
                entry["file"]: (os.path.realpath(entry["path"]), entry["sha256"])
                for entry in packet["references"]
            }
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise ContractError("%s's reviewed packet is missing or changed" % label) from exc
        sealed = {
            name: (os.path.realpath(path), digest) for name, (path, digest) in references.items()
        }
        if shown != sealed:
            raise ContractError(
                "%s's packet does not show every sealed reference by its sealed hash" % label
            )
        verdict = item["review"]["verdict"]
        if set(verdict["references_checked"]) != set(sealed) or not set(
            verdict["visible_in"]
        ) <= set(sealed):
            raise ContractError(
                "%s's review does not account for every sealed reference" % label
            )
        reviewer = item["review"]["reviewer"]
        if reviewer.lower() in MANAGER_NAMES:
            raise ContractError("%s was confirmed by the Workshop Manager itself" % label)
        if reviewer in seen_reviewers:
            raise ContractError(
                "%s names reviewer %s, who already reviewed Contract Amendment %d; each "
                "amendment needs a fresh reader" % (label, reviewer, seen_reviewers[reviewer])
            )
        seen_reviewers[reviewer] = item["amendment"]
        if reviewer_check is not None:
            reviewer_check(reviewer, images, label)
    by_number = {item["amendment"]: item for item in amendments}
    for report in blocked_reports:
        for answer in report.get("answers") or ():
            if answer.get("kind") != "amendment":
                continue
            item = by_number.get(answer.get("amendment"))
            if (
                item is None
                or item["status"] != "applied"
                or item["report"] != report.get("report")
                or item["amended_sha256"] != answer.get("amended_sha256")
            ):
                raise ContractError(
                    "Blocked Report %s is cleared by Contract Amendment %s, which is not an "
                    "applied amendment naming it" % (report.get("report"), answer.get("amendment"))
                )
    return [_record(item) for item in amendments] + [dict(item) for item in owner_amendments]


def owner_contract_changes(
    current: Mapping[str, Any], amended: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Each requirement and Interface text the owner's ``amended`` contract
    changes against the ``current`` one, as ``{"row", "scope", "from",
    "to"}``, requirements first, in contract order (issue #100).

    Refuses, naming every difference at once, a change to anything else: the
    schema, title, Inventor, envelope, a reference or its camera, a geometry,
    a requirement's id, scope or order, and an Interface's id, kind,
    Components, envelope, poses or yielding side.
    """

    errors: list[str] = []
    changes: list[dict[str, Any]] = []
    for key in sorted(set(current) | set(amended)):
        if key in ("requirements", "interfaces"):
            continue
        if current.get(key) != amended.get(key):
            errors.append("it changes %s" % key)
    old_rows = [item for item in current.get("requirements") or () if isinstance(item, dict)]
    new_rows = [item for item in amended.get("requirements") or () if isinstance(item, dict)]
    if [(item.get("id"), item.get("scope")) for item in old_rows] != [
        (item.get("id"), item.get("scope")) for item in new_rows
    ]:
        errors.append("it adds, removes, reorders or rescopes a requirement")
    else:
        for index, (old, new) in enumerate(zip(old_rows, new_rows)):
            if old.get("text") != new.get("text"):
                changes.append({
                    "row": old.get("id") if isinstance(old.get("id"), str) else "requirements[%d]" % index,
                    "scope": old.get("scope"), "from": old.get("text"), "to": new.get("text"),
                })
    if ("interfaces" in current) != ("interfaces" in amended):
        errors.append("it adds or removes the Interfaces section")
    old_faces = [item for item in current.get("interfaces") or () if isinstance(item, dict)]
    new_faces = [item for item in amended.get("interfaces") or () if isinstance(item, dict)]
    if [item.get("id") for item in old_faces] != [item.get("id") for item in new_faces]:
        errors.append("it adds, removes or reorders an Interface")
    else:
        for old, new in zip(old_faces, new_faces):
            other = sorted(
                key for key in set(old) | set(new) if key != "text" and old.get(key) != new.get(key)
            )
            if other:
                errors.append("it changes Interface %s's %s" % (old.get("id"), ", ".join(other)))
            elif old.get("text") != new.get("text"):
                row = INTERFACE_ROW + str(old.get("id"))
                changes.append({"row": row, "scope": row, "from": old.get("text"), "to": new.get("text")})
    if errors:
        raise ContractError(
            "an owner amendment changes only requirement text, Interface text and prose; "
            "the amended contract %s. Reference images, geometries and an Interface's other "
            "fields stay sealed: relaunch to change them" % "; ".join(errors)
        )
    return changes


def owner_affects(contract: Mapping[str, Any], changes: Sequence[Mapping[str, Any]]) -> list[str]:
    """The Components whose own contract rows an owner amendment changes: the
    geometry a requirement is scoped to, and every Component an Interface
    joins. An assembly row is no Component's row; the assembly round, the
    blind review and the final verification read it."""

    affected: set[str] = set()
    for change in changes:
        if change["row"].startswith(INTERFACE_ROW):
            for item in contract.get("interfaces") or ():
                if isinstance(item, dict) and INTERFACE_ROW + str(item.get("id")) == change["row"]:
                    affected |= _roles(item.get("components"))
        elif isinstance(change["scope"], str) and change["scope"].startswith(GEOMETRY_SCOPE):
            affected.add(change["scope"][len(GEOMETRY_SCOPE):])
    return sorted(affected)


def apply_owner_amendments(
    contract: Mapping[str, Any], owners: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """``contract`` with every owner amendment's row texts set, in order;
    refuses a row the contract does not have. Kept in step with make_round."""

    amended = json.loads(json.dumps(contract))
    for owner in owners:
        for change in owner.get("changes") or ():
            row = change["row"]
            if row.startswith(INTERFACE_ROW):
                items = [
                    item for item in amended.get("interfaces") or ()
                    if isinstance(item, dict) and INTERFACE_ROW + str(item.get("id")) == row
                ]
            else:
                items = [
                    item for index, item in enumerate(amended.get("requirements") or ())
                    if isinstance(item, dict)
                    and (item.get("id") == row or "requirements[%d]" % index == row)
                ]
            if len(items) != 1:
                raise ContractError("an owner amendment changes %s, which the contract does not have" % row)
            items[0]["text"] = change["to"]
    return amended


def _prose(objective: str) -> list[str]:
    return _FENCE.sub(lambda _match: _PROSE_BLOCK, objective).splitlines()


def owner_objective(
    sealed_objective: str, current_objective: str, amended_text: str
) -> tuple[Optional[str], Optional[str]]:
    """``(objective, prose_diff)`` for an owner's amended contract file.

    A run sealed by ``workshop wish --contract`` holds the whole contract as
    its objective: the amended objective is the file with the run's sealed
    name line in place of its own (``Name this toy exactly: ...``), and
    ``prose_diff`` the unified diff of the prose outside the design-contract
    block against ``current_objective``, or None when the prose is
    unchanged. A correction run's objective is its brief and holds no
    contract prose: both are None, and only the block's rows are amended.
    """

    if _FENCE.search(sealed_objective) is None:
        return None, None
    sealed_first = sealed_objective.split("\n", 1)[0]
    amended_first = amended_text.split("\n", 1)[0]
    if NAME_LINE.fullmatch(sealed_first):
        if NAME_LINE.fullmatch(amended_first):
            objective = sealed_first + amended_text[len(amended_first):]
        else:
            objective = sealed_first + "\n\n" + amended_text
    elif NAME_LINE.fullmatch(amended_first):
        raise ContractError(
            "the amended contract opens with a name line, but this run sealed none; a run "
            "keeps the name it was sealed with"
        )
    else:
        objective = amended_text
    diff = "\n".join(
        difflib.unified_diff(
            _prose(current_objective), _prose(objective), "sealed", "amended", n=1, lineterm=""
        )
    )
    return objective, diff or None


def contract_in_effect(
    contract: Mapping[str, Any],
    amendments: Sequence[Mapping[str, Any]],
    owners: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """The sealed ``contract`` with every applied in-run amendment of one
    replayed ledger, then every owner amendment: what the rounds read."""

    current: Mapping[str, Any] = contract
    for item in amendments:
        if item["status"] == "applied":
            current = item["_amended"]
    return apply_owner_amendments(current, owners)


def owner_closure_refusal(
    amendments: Sequence[Mapping[str, Any]], owners: Sequence[Mapping[str, Any]]
) -> Optional[str]:
    """Why a ledger may not stand beside the owner amendments, or None: the
    owner's first amendment closes in-run amendments after the number the
    ledger had reached then (issue #100)."""

    if not owners:
        return None
    closed = owners[0]["in_run_amendments"]
    late = [item["amendment"] for item in amendments if item["amendment"] > closed]
    if late:
        return (
            "Contract Amendment %d was proposed after the owner amended the contract; owner "
            "amendment 1 closed in-run amendments after amendment %d" % (late[0], closed)
        )
    return None


def run_contract_amendments(
    run_root: Path, *, contract: Optional[Mapping[str, Any]], wish_sha256: Optional[str]
) -> list[dict[str, Any]]:
    """Every Contract Amendment of every Make attempt in a run workspace,
    oldest attempt first, for the run report and the outer loop that folds
    them back. A ledger that does not replay is listed as invalid rather than
    hidden; an amendment still awaiting review is listed as proposed."""

    attempts = Path(run_root).joinpath(*_MAKE_ATTEMPTS)
    if not attempts.is_dir():
        return []
    listed: list[dict[str, Any]] = []
    for attempt in sorted(attempts.glob("r[0-9][0-9][0-9][0-9]")):
        product = attempt / "product"
        if product.is_symlink() or not product.is_dir():
            continue
        for ledger in sorted(product.rglob(AMENDMENT_LEDGER_NAME)):
            if ledger.parent.name != "measure":
                continue
            where = {
                "kind": "contract-amendment",
                "attempt": attempt.name,
                "ledger": ledger.relative_to(run_root).as_posix(),
            }
            try:
                if contract is None:
                    raise ContractError("no sealed Design Contract")
                replayed = replay_contract_amendments(
                    _read_ledger(ledger), contract, wish_sha256=wish_sha256
                )
            except ContractError:
                listed.append({**where, "status": "invalid"})
                continue
            listed.extend({**where, **_record(item)} for item in replayed)
    return listed


__all__ = [
    "AMENDMENT_LEDGER_NAME",
    "NAME_LINE",
    "OWNER_AMENDMENTS_MARKER",
    "OWNER_AMENDMENT_KIND",
    "apply_owner_amendments",
    "contract_digest",
    "contract_in_effect",
    "deletions_only",
    "owner_affects",
    "owner_closure_refusal",
    "owner_contract_changes",
    "owner_objective",
    "read_amendment_ledger",
    "replay_contract_amendments",
    "retry_refusal",
    "run_contract_amendments",
    "verify_contract_amendments",
]
