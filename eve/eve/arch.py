"""Loop B — the multi-agent architecture study (the archivist).

Studies the science and engineering of multi-agent systems continuously
(Anthropic's engineering material — *How we built our multi-agent research
system*, *Effective harnesses for long-running agents*, *Demystifying evals
for AI agents* — plus evals, RL, and agent-harness literature) and turns them
into lessons that change Eve's *own* harness, prompts, agent roles, and eval
methodology.

This is Eve's second-order learner: Loop C learns from empirical loss, Loop B
learns from theory. Both feed the same improvement path, and Loop B's whole
job is that Eve does not stay a fixed pipeline. Lessons carry a tier so the
improvement gate (DOC / CODE / FORBIDDEN) is decided by the same rule the
self-improvement session uses everywhere.

State (sources studied + the lesson log) lives in loops/arch/state.json.
Recording a source/lesson is deterministic; no model writes here.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .journal import open_journal

SCHEMA_VERSION = 1

# Tiers mirror improve.py: they decide who may apply a change.
TIERS = {"DOC", "CODE", "FORBIDDEN"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _state(cfg) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated": _now(),
        "sources": [],          # {title, url, read_at}
        "lessons": [],          # {id, source, lesson, target_area, tier, at, applied}
        "proposals": [],        # CODE-tier change proposals awaiting a human
    }


def _ensure(cfg) -> dict:
    cfg.arch_state.parent.mkdir(parents=True, exist_ok=True)
    if not cfg.arch_state.exists():
        cfg.arch_state.write_text(json.dumps(_state(cfg), indent=2))
    return json.loads(cfg.arch_state.read_text())


def load(cfg) -> dict:
    return _ensure(cfg)


def save(cfg, state: dict) -> None:
    state["updated"] = _now()
    cfg.arch_state.parent.mkdir(parents=True, exist_ok=True)
    cfg.arch_state.write_text(json.dumps(state, indent=2))


def _slugify(text: str, n: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:n] or "lesson"


def record_source(cfg, *, title: str, url: str = "") -> bool:
    """Add a studied source (deduped by title). Returns True if new."""
    state = _ensure(cfg)
    if any(s.get("title") == title for s in state["sources"]):
        return False
    state["sources"].append({"title": title, "url": url, "read_at": _now()})
    save(cfg, state)
    open_journal(cfg).append("arch_source", title=title)
    return True


def record_lesson(cfg, *, source: str, lesson: str, target_area: str,
                  tier: str = "DOC", url: str = "", journal=None) -> str:
    """Log one architecture lesson. Dedupes by content (normalized).

    `tier` decides who may apply it (DOC direct, CODE branch+PR, FORBIDDEN
    never). Returns the lesson id (stable, deduped).
    """
    if tier not in TIERS:
        raise ValueError(f"unknown tier {tier!r}; expected one of {sorted(TIERS)}")
    state = _ensure(cfg)
    key = re.sub(r"\s+", " ", lesson.strip().lower())
    for ex in state["lessons"]:
        if re.sub(r"\s+", " ", ex.get("lesson", "").strip().lower()) == key:
            return ex["id"]
    lid = f"{_slugify(target_area)}-{len(state['lessons']) + 1}"
    state["lessons"].append({
        "id": lid, "source": source, "url": url, "lesson": lesson,
        "target_area": target_area, "tier": tier, "applied": False, "at": _now(),
    })
    save(cfg, state)
    (journal or open_journal(cfg)).append(
        "arch_lesson", id=lid, source=source, tier=tier, target_area=target_area)
    return lid


def lessons(cfg, unapplied_only: bool = False) -> list[dict]:
    state = _ensure(cfg)
    out = [l for l in state["lessons"]]
    if unapplied_only:
        out = [l for l in out if not l.get("applied")]
    return out


def apply(cfg, lesson_id: str) -> bool:
    """Mark a lesson as applied to Eve's policy (Loop B -> feed into improve)."""
    state = _ensure(cfg)
    for l in state["lessons"]:
        if l["id"] == lesson_id:
            l["applied"] = True
            save(cfg, state)
            open_journal(cfg).append("arch_apply", id=lesson_id)
            return True
    return False


def propose(cfg, *, target_area: str, change: str, tier: str = "CODE") -> str:
    """Raise a CODE-tier change proposal for a human reader (branch + PR)."""
    if tier not in TIERS:
        raise ValueError(f"unknown tier {tier!r}")
    state = _ensure(cfg)
    pid = f"{_slugify(target_area)}-{len(state['proposals']) + 1}"
    state["proposals"].append({
        "id": pid, "target_area": target_area, "change": change,
        "tier": tier, "at": _now(), "status": "open",
    })
    save(cfg, state)
    open_journal(cfg).append("arch_propose", id=pid, tier=tier)
    return pid
