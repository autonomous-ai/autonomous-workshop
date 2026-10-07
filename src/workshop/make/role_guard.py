"""Host side of the make_round guard (ADR 0080).

A new run's host state holds the guard hook, ``make_round_guard.py``, and the
nonce table it appends to, outside the run workspace. The native launchers
register that exact script as a ``PreToolUse`` hook whenever it is installed;
a frozen run has none and launches unchanged. At Make acceptance the host
refuses any Component round whose recorded worker nonce it did not issue to a
``component-worker`` for that Component. In a run that binds reviewers
(issue #77, Claude Code) the same check refuses any recorded Component Review
whose reviewer is not a ``component-reviewer`` the runtime started, did not
read every image of the reviewed packet, or differs from the Component's
earlier reviewers.

On Claude Code, which runs without a sandbox, this is tamper-resistant, not
tamper-proof: an agent can reach host state with its own tools. Nothing here
spawns, schedules or judges an agent.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import zipfile
from importlib import resources
from pathlib import Path
from typing import Optional

from workshop.errors import ContractError, StateConflict
from workshop.make.make_round_guard import (
    NONCE_TABLE_NAME,
    READ_LOG_NAME,
    SUBAGENT_LOG_NAME,
)
from workshop.make.role_agents import COMPONENT_REVIEWER, COMPONENT_WORKER, CONTRACT_REVIEWER
from workshop.runtime.make_round_hook import (
    MAKE_ROUND_GUARD_DIRECTORY,
    MAKE_ROUND_GUARD_MANAGER_IDS,
    MAKE_ROUND_GUARD_SCRIPT,
    REVIEWER_BINDING_MANAGER_IDS,
    installed_make_round_guard,
)

MAX_NONCE_TABLE_BYTES = 8 * 1024 * 1024
MAX_EVIDENCE_LOG_BYTES = 32 * 1024 * 1024
MAX_PACKET_BYTES = 1024 * 1024
# The native agent id a Claude Code subagent carries (issue #77); kept in step
# with ``REVIEWER_ID_FORMATS`` in make_round.
REVIEWER_ID = re.compile(r"[0-9a-f]{17}")
# Kept in step with ``REVISION_INPUT`` in ``workshop.workflow.revision``; the
# make package does not import the workflow package.
REVISION_SOURCE = "revision-source.zip"
_COMPONENT_ROUNDS = ("measure", "component-rounds")
# Issue #113: the sealed run input that tells make_round the run has the
# guard, so a component round without a worker nonce fails at once. It lives
# in the read-only ``.agents`` tree. Kept in step with ``GUARD_MARKER`` in
# make_round, which only checks that it exists.
MAKE_ROUND_GUARD_MARKER = ".agents/MAKE-ROUND-GUARD.json"
_COMPONENT_STATE = "make-round-state.json"


def _component_source(role: str) -> str:
    return "part_%s.step.py" % role


def make_round_guard_bytes() -> bytes:
    """The packaged guard hook's exact bytes."""

    return resources.files("workshop.make").joinpath(MAKE_ROUND_GUARD_SCRIPT).read_bytes()


def make_round_guard_marker_bytes() -> bytes:
    """Canonical bytes of the sealed marker of a guarded run (issue #113)."""

    return json.dumps(
        {"kind": "workshop-make-round-guard", "schema_version": 1, "worker_nonce": "required"},
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def install_make_round_guard(host_state_root: Path) -> str:
    """Materialize the guard into fresh host state; return its sha256."""

    content = make_round_guard_bytes()
    directory = Path(host_state_root) / MAKE_ROUND_GUARD_DIRECTORY
    directory.mkdir(mode=0o700)
    os.chmod(directory, 0o700)
    script = directory / MAKE_ROUND_GUARD_SCRIPT
    descriptor = os.open(str(script), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    try:
        os.write(descriptor, content)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.chmod(script, 0o400)
    return hashlib.sha256(content).hexdigest()


def verify_make_round_guard(host_state_root: Path, expected_sha256: str) -> Path:
    """Refuse a guard that is missing or differs from the bytes the run sealed."""

    script = installed_make_round_guard(host_state_root)
    if script is None:
        raise StateConflict("the run's make_round guard is missing")
    if hashlib.sha256(script.read_bytes()).hexdigest() != expected_sha256:
        raise StateConflict("the run's make_round guard differs from its sealed bytes")
    return script


def _guard_records(host_state_root: Path, name: str, limit: int, label: str) -> list[dict]:
    """Every record of one host-side guard log; an absent log has none."""

    table = Path(host_state_root) / MAKE_ROUND_GUARD_DIRECTORY / name
    if not table.exists() and not table.is_symlink():
        return []
    try:
        identity = table.lstat()
        if not stat.S_ISREG(identity.st_mode) or identity.st_size > limit:
            raise ValueError("not a bounded regular file")
        records = []
        for line in table.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError("invalid record")
            records.append(record)
    except (OSError, UnicodeError, ValueError) as exc:
        raise StateConflict("the make_round guard %s is invalid" % label) from exc
    return records


def _issued_worker_nonces(host_state_root: Path) -> dict[str, str]:
    """Nonce -> the Component source it was issued to a worker for."""

    issued: dict[str, str] = {}
    for record in _guard_records(
        host_state_root, NONCE_TABLE_NAME, MAX_NONCE_TABLE_BYTES, "nonce table"
    ):
        if not isinstance(record.get("nonce"), str):
            raise StateConflict("the make_round guard nonce table is invalid")
        if record.get("agent_type") == COMPONENT_WORKER and isinstance(
            record.get("component"), str
        ):
            issued[record["nonce"]] = record["component"]
    return issued


def _started_reviewers(host_state_root: Path, role: str = COMPONENT_REVIEWER) -> set[str]:
    """Agent ids the runtime started as ``role``."""

    return {
        record["agent_id"]
        for record in _guard_records(
            host_state_root, SUBAGENT_LOG_NAME, MAX_EVIDENCE_LOG_BYTES, "subagent log"
        )
        if record.get("agent_type") == role
        and isinstance(record.get("agent_id"), str)
    }


def _reviewer_reads(
    host_state_root: Path, role: str = COMPONENT_REVIEWER
) -> dict[str, set[tuple[str, str]]]:
    """Agent id -> every ``(resolved path, sha256)`` a reviewer of ``role`` read."""

    reads: dict[str, set[tuple[str, str]]] = {}
    for record in _guard_records(
        host_state_root, READ_LOG_NAME, MAX_EVIDENCE_LOG_BYTES, "reviewer read log"
    ):
        if (
            record.get("agent_type") == role
            and isinstance(record.get("agent_id"), str)
            and isinstance(record.get("path"), str)
            and isinstance(record.get("sha256"), str)
        ):
            reads.setdefault(record["agent_id"], set()).add(
                (record["path"], record["sha256"])
            )
    return reads


def _packet_images(summary: dict, label: str) -> dict[str, str]:
    """Resolved path -> sha256 of every image a reviewed round's packet shows:
    its sheet and each comparison image."""

    visual = summary.get("visual")
    packet_path = visual.get("packet") if isinstance(visual, dict) else None
    packet_sha256 = visual.get("packet_sha256") if isinstance(visual, dict) else None
    if not isinstance(packet_path, str) or not isinstance(packet_sha256, str):
        raise ContractError("Component round %s has a review but no visual packet" % label)
    path = Path(packet_path)
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_PACKET_BYTES:
            raise ValueError("not a bounded regular file")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != packet_sha256:
            raise ValueError("changed")
        packet = json.loads(content)
        images = dict(packet["images"])
        for image, item in dict(packet.get("comparisons") or {}).items():
            images[image] = item["sha256"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ContractError(
            "Component round %s's reviewed visual packet is missing or changed" % label
        ) from exc
    if not images or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in images.items()
    ):
        raise ContractError("Component round %s's reviewed visual packet is invalid" % label)
    return {os.path.realpath(key): value for key, value in images.items()}


def _verify_component_reviews(
    reviewed: list[tuple[str, str, dict]], host_state_root: Path
) -> None:
    """Refuse a recorded Component Review no proven Component Reviewer made
    (issue #77): its reviewer id must be a ``component-reviewer`` the runtime
    started, that agent must have read every image of the reviewed packet with
    the packet's exact bytes, and every review of a Component names one id."""

    if not reviewed:
        return
    started = _started_reviewers(host_state_root)
    reads = _reviewer_reads(host_state_root)
    bound: dict[str, tuple[str, str]] = {}
    for role, label, summary in reviewed:
        reviewer = summary["review"].get("reviewer")
        if not isinstance(reviewer, str) or REVIEWER_ID.fullmatch(reviewer) is None:
            raise ContractError(
                "Component round %s's review does not name its reviewer by native "
                "agent id; record the component-reviewer's id" % label
            )
        earlier = bound.setdefault(role, (reviewer, label))
        if earlier[0] != reviewer:
            raise ContractError(
                "Component round %s's review names reviewer %s, but %s was reviewed "
                "by %s; every review of a Component comes from its one reviewer"
                % (label, reviewer, earlier[1], earlier[0])
            )
        if reviewer not in started:
            raise ContractError(
                "Component round %s's review names %s, which is not a "
                "component-reviewer this run started" % (label, reviewer)
            )
        seen = reads.get(reviewer, set())
        for image, digest in sorted(_packet_images(summary, label).items()):
            if (image, digest) not in seen:
                raise ContractError(
                    "Component round %s's reviewer %s did not read %s as the "
                    "packet holds it; a review must judge the packet it names"
                    % (label, reviewer, os.path.basename(image))
                )


def contract_reviewer_check(host_state_root: Path):
    """A check refusing a Contract Amendment review no proven Contract
    Reviewer made (ADR 0085): ``(reviewer, images, label)`` -> None. The
    reviewer must be named by native agent id, be a ``contract-reviewer``
    the runtime started, and have read every sealed reference image with its
    sealed bytes."""

    started: Optional[set[str]] = None
    reads: Optional[dict[str, set[tuple[str, str]]]] = None

    def check(reviewer: str, images: dict[str, str], label: str) -> None:
        nonlocal started, reads
        if REVIEWER_ID.fullmatch(reviewer) is None:
            raise ContractError(
                "%s's review does not name its reviewer by native agent id; record the "
                "contract-reviewer's id" % label
            )
        if started is None:
            started = _started_reviewers(host_state_root, CONTRACT_REVIEWER)
            reads = _reviewer_reads(host_state_root, CONTRACT_REVIEWER)
        if reviewer not in started:
            raise ContractError(
                "%s's review names %s, which is not a contract-reviewer this run started"
                % (label, reviewer)
            )
        seen = (reads or {}).get(reviewer, set())
        for image, digest in sorted(images.items()):
            if (image, digest) not in seen:
                raise ContractError(
                    "%s's reviewer %s did not read %s as it was sealed; a review must "
                    "check every sealed reference" % (label, reviewer, os.path.basename(image))
                )

    return check


def _carried_summaries(run_root: Path) -> set[str]:
    """sha256 of every Component round summary the revision source sealed."""

    archive_path = Path(run_root) / REVISION_SOURCE
    if archive_path.is_symlink() or not archive_path.is_file():
        return set()
    digests = set()
    try:
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                parts = info.filename.split("/")
                if (
                    parts[-1] == "summary.json"
                    and _COMPONENT_ROUNDS[-1] in parts
                    and not info.is_dir()
                ):
                    digests.add(hashlib.sha256(archive.read(info)).hexdigest())
    except (OSError, zipfile.BadZipFile) as exc:
        raise StateConflict("the sealed revision source is unreadable") from exc
    return digests


def _missing_round_summaries(rounds: Path) -> list[str]:
    """Every Component round its ``make-round-state.json`` records with no
    ``summary.json`` in the product tree (issue #113).

    A Component's state records its latest round; every round up to it
    wrote a summary, and a refused round records nothing. A summary moved
    out of the tree hides that round from the nonce check, so it is missing
    evidence, never a round to skip.
    """

    missing = []
    states = sorted(rounds.glob("*/" + _COMPONENT_STATE)) if rounds.is_dir() else []
    for state_path in states:
        role = state_path.parent.name
        try:
            if state_path.is_symlink() or not state_path.is_file():
                raise ValueError("not a regular file")
            state = json.loads(state_path.read_text(encoding="utf-8"))
            latest = state.get("round") if isinstance(state, dict) else None
            if type(latest) is not int or latest < 0:
                raise ValueError("no round")
        except (OSError, UnicodeError, ValueError) as exc:
            raise ContractError(
                "the %s of Component %s is invalid" % (_COMPONENT_STATE, role)
            ) from exc
        missing.extend(
            "%s r%04d" % (role, number)
            for number in range(1, latest + 1)
            if not (state_path.parent / ("r%04d" % number) / "summary.json").is_file()
        )
    return missing


def verify_component_round_nonces(
    project: Path,
    host_state_root: Path,
    *,
    run_root: Path,
    require_every_component: bool = False,
    bind_reviewers: bool = False,
) -> None:
    """Refuse a Component round no ``component-worker`` ran (ADR 0080).

    Every round a Component's ``make-round-state.json`` records must have
    its ``summary.json`` (issue #113), and every round summary under
    ``measure/component-rounds`` must carry a nonce
    the guard issued to a worker for that Component, each used by one round
    only. A summary whose exact bytes the revision source sealed was carried
    forward by a correction and keeps the evidence it already had. With
    ``require_every_component`` (component-first Spark Make) every
    ``part_<id>.step.py`` must also have at least one such round. With
    ``bind_reviewers`` every review recorded on a round (not carried forward
    from an earlier one) must come from the Component's one proven
    Component Reviewer (issue #77).
    """

    rounds = Path(project).joinpath(*_COMPONENT_ROUNDS)
    missing = _missing_round_summaries(rounds)
    if missing:
        raise ContractError(
            "Component round %s is recorded in make-round-state.json but its "
            "summary.json is missing from the product tree; keep every round's "
            "evidence where make_round wrote it, or have a component-worker rerun "
            "that Component's round" % ", ".join(missing)
        )
    summaries = (
        sorted(rounds.glob("*/r[0-9][0-9][0-9][0-9]/summary.json"))
        if rounds.is_dir() else []
    )
    if require_every_component:
        covered = {path.parent.parent.name for path in summaries}
        for source in sorted(Path(project).glob("part_*.step.py")):
            role = source.name[len("part_"):-len(".step.py")]
            if role not in covered:
                raise ContractError(
                    "%s has no component round; have its component-worker run one"
                    % source.name
                )
    if not summaries:
        return
    issued = _issued_worker_nonces(host_state_root)
    carried: Optional[set[str]] = None
    used: dict[str, str] = {}
    reviewed: list[tuple[str, str, dict]] = []
    for path in summaries:
        role = path.parent.parent.name
        label = "%s %s" % (role, path.parent.name)
        content = path.read_bytes()
        try:
            summary = json.loads(content)
        except ValueError as exc:
            raise ContractError("Component round %s summary is not JSON" % label) from exc
        nonce = summary.get("worker_nonce") if isinstance(summary, dict) else None
        review = summary.get("review") if isinstance(summary, dict) else None
        if isinstance(nonce, str) and issued.get(nonce) == _component_source(role):
            if nonce in used:
                raise ContractError(
                    "Component round %s reuses the worker nonce of %s" % (label, used[nonce])
                )
            used[nonce] = label
            if bind_reviewers and isinstance(review, dict) and not review.get("carried_from"):
                if carried is None:
                    carried = _carried_summaries(run_root)
                if hashlib.sha256(content).hexdigest() not in carried:
                    reviewed.append((role, label, summary))
            continue
        if carried is None:
            carried = _carried_summaries(run_root)
        if hashlib.sha256(content).hexdigest() in carried:
            continue
        raise ContractError(
            "Component round %s was not run by a component-worker: its worker "
            "nonce is missing or was not issued for %s. Have a "
            "component-worker rerun that Component's round."
            % (label, _component_source(role))
        )
    _verify_component_reviews(reviewed, host_state_root)


__all__ = [
    "MAKE_ROUND_GUARD_DIRECTORY",
    "MAKE_ROUND_GUARD_MANAGER_IDS",
    "MAKE_ROUND_GUARD_MARKER",
    "MAKE_ROUND_GUARD_SCRIPT",
    "REVIEWER_BINDING_MANAGER_IDS",
    "contract_reviewer_check",
    "install_make_round_guard",
    "installed_make_round_guard",
    "make_round_guard_bytes",
    "make_round_guard_marker_bytes",
    "verify_component_round_nonces",
    "verify_make_round_guard",
]
