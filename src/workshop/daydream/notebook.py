"""The persistent per-Inventor notebook of theses, feedback, and outcomes."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from workshop.daydream._files import append_private_line, read_regular_bytes
from workshop.daydream.catalog import PriorWork
from workshop.daydream.contracts import (
    MAX_ONE_LINER_CHARS,
    MAX_TITLE_CHARS,
    MAX_VERDICT_TEXT_CHARS,
    THESIS_V2_VERDICT_CHECKS,
    THESIS_VERDICT_CHECKS,
    Idea,
    LearningTrace,
    Verdict,
    bounded_line,
    bounded_paragraph,
    canonical_json,
    require_created_at,
    require_daydream_id,
)
from workshop.errors import ContractError
from workshop._validation import require_sha256


NOTEBOOK_STATUSES = ("dreamed", "rejected", "judged")
NOTEBOOK_ENTRY_KIND = "autonomous-workshop.daydream-memory"
MAX_NOTEBOOK_BYTES = 8 * 1024 * 1024
MAX_NOTEBOOK_LINE_BYTES = 32 * 1024
DEFAULT_NOTEBOOK_LIMIT = 200
_ENTRY_V1_KEYS = frozenset(
    ("daydream_id", "created_at", "title", "one_liner", "idea_sha256", "status")
)
_ENTRY_V2_KEYS = _ENTRY_V1_KEYS | frozenset(
    ("schema_version", "kind", "structure", "judge", "rejection_reason")
)
_ENTRY_V3_KEYS = _ENTRY_V2_KEYS | frozenset(("learning",))
_STRUCTURE_KEYS = frozenset(
    (
        "physical_opportunity",
        "action",
        "response",
        "payoff",
        "anti_generic_signature",
        "sha256",
    )
)
_JUDGE_KEYS = frozenset(("decision", "failed_checks", "confidence", "advice"))


@dataclass(frozen=True)
class StructuralTrace:
    """Exact experience-level trace; its hash is not a semantic novelty score."""

    physical_opportunity: str
    action: str
    response: str
    payoff: str
    anti_generic_signature: str

    def __post_init__(self) -> None:
        for name in (
            "physical_opportunity",
            "action",
            "response",
            "payoff",
            "anti_generic_signature",
        ):
            bounded_paragraph(getattr(self, name), "memory structure %s" % name, 600)

    @classmethod
    def from_idea(cls, idea: Idea) -> "StructuralTrace":
        if not isinstance(idea, Idea) or idea.schema_version not in (2, 3):
            raise ContractError("structural memory requires a schema-v2 or v3 Idea")
        assert idea.opportunity is not None
        assert idea.experience is not None
        return cls(
            physical_opportunity=idea.opportunity.physical_opportunity,
            action=idea.experience.action,
            response=idea.experience.response,
            payoff=idea.experience.payoff,
            anti_generic_signature=idea.experience.anti_generic_signature,
        )

    @property
    def sha256(self) -> str:
        return hashlib.sha256(
            canonical_json(self._content_dict()).encode("utf-8")
        ).hexdigest()

    def _content_dict(self) -> Dict[str, str]:
        return {
            "physical_opportunity": self.physical_opportunity,
            "action": self.action,
            "response": self.response,
            "payoff": self.payoff,
            "anti_generic_signature": self.anti_generic_signature,
        }

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "StructuralTrace":
        if not isinstance(raw, Mapping) or set(raw) != _STRUCTURE_KEYS:
            raise ContractError(
                "memory structure keys must be exactly %s" % sorted(_STRUCTURE_KEYS)
            )
        trace = cls(**{name: raw[name] for name in _STRUCTURE_KEYS if name != "sha256"})
        require_sha256(raw["sha256"], "memory structure sha256")
        if trace.sha256 != raw["sha256"]:
            raise ContractError("memory structure sha256 does not match its exact content")
        return trace

    def to_dict(self) -> Dict[str, str]:
        value = self._content_dict()
        value["sha256"] = self.sha256
        return value


@dataclass(frozen=True)
class JudgeMemory:
    """A retired Judge prediction retained only for historical readability."""

    decision: str
    failed_checks: tuple[str, ...]
    confidence: float
    advice: str

    def __post_init__(self) -> None:
        if self.decision not in ("build", "dream-again"):
            raise ContractError("memory judge decision must be build or dream-again")
        checks = tuple(self.failed_checks)
        if (
            len(set(checks)) != len(checks)
            or any(
                name not in set(THESIS_V2_VERDICT_CHECKS) | set(THESIS_VERDICT_CHECKS)
                for name in checks
            )
        ):
            raise ContractError(
                "memory judge failed_checks contain unknown or repeated checks"
            )
        if self.decision == "build" and checks:
            raise ContractError("memory build decision cannot retain failed checks")
        if self.decision == "dream-again" and not checks:
            raise ContractError("memory dream-again decision must retain failed checks")
        object.__setattr__(self, "failed_checks", tuple(sorted(checks)))
        if isinstance(self.confidence, bool) or not isinstance(
            self.confidence, (int, float)
        ):
            raise ContractError("memory judge confidence must be a number from 0 to 1")
        confidence = float(self.confidence)
        if confidence != confidence or not 0.0 <= confidence <= 1.0:
            raise ContractError("memory judge confidence must be a number from 0 to 1")
        object.__setattr__(self, "confidence", confidence)
        bounded_line(self.advice, "memory judge advice", MAX_VERDICT_TEXT_CHARS)

    @classmethod
    def from_verdict(cls, verdict: Verdict) -> "JudgeMemory":
        if not isinstance(verdict, Verdict) or verdict.schema_version not in (2, 3):
            raise ContractError("new Judge memory requires a schema-v2 or v3 Verdict")
        return cls(
            decision=verdict.decision,
            failed_checks=verdict.failed_checks,
            confidence=verdict.confidence,
            advice=verdict.advice,
        )

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "JudgeMemory":
        if not isinstance(raw, Mapping) or set(raw) != _JUDGE_KEYS:
            raise ContractError("memory judge keys must be exactly %s" % sorted(_JUDGE_KEYS))
        failed = raw["failed_checks"]
        if isinstance(failed, str) or not isinstance(failed, Sequence):
            raise ContractError("memory judge failed_checks must be a list")
        return cls(
            decision=raw["decision"],
            failed_checks=tuple(failed),
            confidence=raw["confidence"],
            advice=raw["advice"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "failed_checks": list(self.failed_checks),
            "confidence": self.confidence,
            "advice": self.advice,
        }


@dataclass(frozen=True)
class NotebookEntry:
    """One remembered thesis, preserving historical schema-v1 entries."""

    daydream_id: str
    created_at: str
    title: str
    one_liner: str
    idea_sha256: str
    status: str
    schema_version: int = 1
    structure: StructuralTrace | None = None
    judge: JudgeMemory | None = None
    rejection_reason: str | None = None
    learning: tuple[LearningTrace, ...] = ()

    def __post_init__(self) -> None:
        require_daydream_id(self.daydream_id, "notebook daydream_id")
        require_created_at(self.created_at, "notebook created_at")
        bounded_line(self.title, "notebook title", MAX_TITLE_CHARS)
        bounded_line(self.one_liner, "notebook one_liner", MAX_ONE_LINER_CHARS)
        require_sha256(self.idea_sha256, "notebook idea_sha256")
        if self.status not in NOTEBOOK_STATUSES:
            raise ContractError("notebook status must be one of %s" % (NOTEBOOK_STATUSES,))
        if self.schema_version == 1:
            if any(
                value is not None
                for value in (self.structure, self.judge, self.rejection_reason)
            ) or self.learning:
                raise ContractError("notebook schema 1 cannot carry thesis memory")
            return
        if self.schema_version not in (2, 3) or not isinstance(
            self.structure, StructuralTrace
        ):
            raise ContractError("notebook schema 2 or 3 requires a structural trace")
        if isinstance(self.learning, (str, Mapping)) or not isinstance(
            self.learning, Sequence
        ):
            raise ContractError("notebook learning must be a list")
        learning = tuple(self.learning)
        if len(learning) > 5 or any(
            not isinstance(entry, LearningTrace) for entry in learning
        ):
            raise ContractError(
                "notebook learning must contain at most 5 LearningTrace entries"
            )
        if len({entry.daydream_id for entry in learning}) != len(learning):
            raise ContractError("notebook learning cannot repeat a prior daydream_id")
        if self.schema_version == 2 and learning:
            raise ContractError("notebook schema 2 cannot carry learning traces")
        object.__setattr__(self, "learning", learning)
        if self.judge is not None and not isinstance(self.judge, JudgeMemory):
            raise ContractError("notebook judge must be JudgeMemory or null")
        if self.rejection_reason is not None:
            bounded_paragraph(self.rejection_reason, "notebook rejection_reason", 1_000)
        if self.status == "rejected" and self.rejection_reason is None:
            raise ContractError("rejected notebook memory requires its rejection reason")
        if self.status != "rejected" and self.rejection_reason is not None:
            raise ContractError("only rejected notebook memory may carry a rejection reason")
        if self.status == "rejected" and self.judge is not None:
            raise ContractError("novelty-rejected memory cannot carry a Judge prediction")
        if self.status == "judged" and (
            self.judge is None or self.judge.decision != "dream-again"
        ):
            raise ContractError("judged notebook memory requires a dream-again prediction")
        if (
            self.judge is not None
            and self.judge.decision == "dream-again"
            and self.status != "judged"
        ):
            raise ContractError("dream-again memory must have judged status")

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "NotebookEntry":
        if not isinstance(raw, Mapping):
            raise ContractError("notebook entry must be a JSON object")
        version = raw.get("schema_version", 1)
        if type(version) is not int or version not in (1, 2, 3):
            raise ContractError("notebook schema_version must be 1, 2, or 3")
        expected = (
            _ENTRY_V1_KEYS
            if version == 1
            else _ENTRY_V2_KEYS
            if version == 2
            else _ENTRY_V3_KEYS
        )
        if set(raw) != expected:
            raise ContractError("notebook entry keys must be exactly %s" % sorted(expected))
        if version >= 2 and raw["kind"] != NOTEBOOK_ENTRY_KIND:
            raise ContractError("notebook entry kind must be %s" % NOTEBOOK_ENTRY_KIND)
        return cls(
            daydream_id=raw["daydream_id"],
            created_at=raw["created_at"],
            title=raw["title"],
            one_liner=raw["one_liner"],
            idea_sha256=raw["idea_sha256"],
            status=raw["status"],
            schema_version=version,
            structure=StructuralTrace.parse(raw["structure"]) if version >= 2 else None,
            judge=(
                JudgeMemory.parse(raw["judge"])
                if version >= 2 and raw["judge"] is not None
                else None
            ),
            rejection_reason=raw.get("rejection_reason"),
            learning=tuple(
                LearningTrace.parse(entry) for entry in raw.get("learning", ())
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        value: Dict[str, Any] = {
            "daydream_id": self.daydream_id,
            "created_at": self.created_at,
            "title": self.title,
            "one_liner": self.one_liner,
            "idea_sha256": self.idea_sha256,
            "status": self.status,
        }
        if self.schema_version >= 2:
            assert self.structure is not None
            value.update(
                {
                    "schema_version": self.schema_version,
                    "kind": NOTEBOOK_ENTRY_KIND,
                    "structure": self.structure.to_dict(),
                    "judge": self.judge.to_dict() if self.judge is not None else None,
                    "rejection_reason": self.rejection_reason,
                }
            )
            if self.schema_version == 3:
                value["learning"] = [entry.to_dict() for entry in self.learning]
        return value

    @property
    def sha256(self) -> str:
        """Hash the exact durable memory record referenced by later theses."""

        return hashlib.sha256(canonical_json(self.to_dict()).encode("utf-8")).hexdigest()


def append_notebook_entry(path: Path, entry: NotebookEntry) -> None:
    """Append one JSONL record to the owner-only notebook, creating it if absent."""

    if not isinstance(entry, NotebookEntry):
        raise ContractError("append_notebook_entry requires a NotebookEntry")
    line = (canonical_json(entry.to_dict()) + "\n").encode("utf-8")
    if len(line) > MAX_NOTEBOOK_LINE_BYTES:
        raise ContractError("daydream notebook entry exceeds its byte bound")
    append_private_line(Path(path), line, label="daydream notebook")


def _parse_line(line: bytes) -> NotebookEntry | None:
    if not line.strip() or len(line) > MAX_NOTEBOOK_LINE_BYTES:
        return None
    try:
        raw = json.loads(line.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        return None
    if not isinstance(raw, dict):
        return None
    try:
        return NotebookEntry.parse(raw)
    except ContractError:
        return None


def read_notebook(
    path: Path, *, limit: int = DEFAULT_NOTEBOOK_LIMIT
) -> tuple[NotebookEntry, ...]:
    """Return the last ``limit`` well-formed entries; malformed lines are skipped."""

    if type(limit) is not int or limit < 1:
        raise ContractError("notebook limit must be a positive integer")
    try:
        payload = read_regular_bytes(
            Path(path), maximum=MAX_NOTEBOOK_BYTES, label="daydream notebook"
        )
    except FileNotFoundError:
        return ()
    entries = [
        entry
        for entry in (_parse_line(line) for line in payload.split(b"\n"))
        if entry is not None
    ]
    return tuple(entries[-limit:])


def unresolved_actionable_entries(
    entries: Sequence[NotebookEntry],
) -> tuple[NotebookEntry, ...]:
    """Return rejected memories no later thesis has explicitly dispositioned."""

    positions = {entry.daydream_id: index for index, entry in enumerate(entries)}
    addressed = {
        trace.daydream_id
        for index, entry in enumerate(entries)
        for trace in entry.learning
        if entry.schema_version == 3
        if positions.get(trace.daydream_id, index) < index
    }
    return tuple(
        entry
        for entry in entries
        if entry.status in ("rejected", "judged") and entry.daydream_id not in addressed
    )


def render_notebook_markdown(entries: Sequence[NotebookEntry]) -> str:
    """Render the notebook the Inventor reads so it never repeats itself."""

    lines = ["# Your notebook (ideas you already had — do not repeat)", ""]
    if not entries:
        lines.append("(empty: this is your first daydream)")
    unresolved = unresolved_actionable_entries(entries)
    actionable_ids = {entry.daydream_id for entry in unresolved}
    newest_actionable_id = (
        unresolved[-1].daydream_id if unresolved else None
    )
    for entry in entries:
        if not isinstance(entry, NotebookEntry):
            raise ContractError("render_notebook_markdown requires NotebookEntry items")
        lines.append(
            "- **%s** (%s, %s, %s): %s"
            % (entry.title, entry.daydream_id, entry.status, entry.created_at, entry.one_liner)
        )
        lines.append("  - Exact memory sha256: `%s`" % entry.sha256)
        if entry.daydream_id == newest_actionable_id:
            lines.append(
                "  - **Required next:** cite this id and exact memory sha256 in "
                "`learning`, then mark it `repaired` or `abandoned`."
            )
        elif entry.daydream_id in actionable_ids:
            lines.append(
                "  - **Older unresolved:** cite this only when the new thesis repairs "
                "or abandons its direction; never repeat its failed promise."
            )
        if entry.structure is not None:
            lines.append(
                "  - Structure `%s`: %s -> %s -> %s"
                % (
                    entry.structure.sha256[:12],
                    " ".join(entry.structure.action.split()),
                    " ".join(entry.structure.response.split()),
                    " ".join(entry.structure.payoff.split()),
                )
            )
            lines.append(
                "  - Anti-generic signature: %s"
                % " ".join(entry.structure.anti_generic_signature.split())
            )
        if entry.judge is not None:
            lines.append(
                "  - Retired Judge prediction (historical; ignored): %s (%.2f); "
                "failed: %s; advice: %s"
                % (
                    entry.judge.decision,
                    entry.judge.confidence,
                    ", ".join(entry.judge.failed_checks) or "none",
                    entry.judge.advice,
                )
            )
        if entry.rejection_reason is not None:
            lines.append("  - Deterministic novelty rejection: %s" % entry.rejection_reason)
        for trace in entry.learning:
            lines.append(
                "  - Learning closure for %s (%s): %s"
                % (trace.daydream_id, trace.disposition, trace.response)
            )
    return "\n".join(lines) + "\n"


def prior_work_from_notebook(entries: Sequence[NotebookEntry]) -> tuple[PriorWork, ...]:
    """Treat every remembered idea as prior work for the novelty lint."""

    selected = []
    for entry in entries:
        if not isinstance(entry, NotebookEntry):
            raise ContractError("prior_work_from_notebook requires NotebookEntry items")
        selected.append(
            PriorWork(
                source="notebook:%s" % entry.daydream_id,
                title=entry.title,
                summary=entry.one_liner,
            )
        )
    return tuple(selected)


__all__ = [
    "DEFAULT_NOTEBOOK_LIMIT",
    "MAX_NOTEBOOK_BYTES",
    "NOTEBOOK_STATUSES",
    "JudgeMemory",
    "NotebookEntry",
    "StructuralTrace",
    "append_notebook_entry",
    "prior_work_from_notebook",
    "read_notebook",
    "render_notebook_markdown",
    "unresolved_actionable_entries",
]
