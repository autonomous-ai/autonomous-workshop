"""improve.py — Eve's self-improvement session.

Reads the reward ledger, finds where discounted reward is being lost, and
proposes a change to Eve's *own policy* (the thing that invents) aimed at that
loss. This is the RL eld of the system: the reward is evidence, the policy is
what changes, and the loop closes when the changed policy makes the next
episodes score higher.

Two inputs feed this one path (per DESIGN.md):
  * Loop C loss from the ledger (empirical);
  * Loop B lessons from the archivist (theoretical).
Both are gated by the same tier rule, mirroring vibe-ideas:

  DOC        lessons, notes            -> applied directly to loops/lessons.md
  CODE       gates, thresholds, prompts,
             agents, this module        -> branch + PR for a human to read
  FORBIDDEN  taste, threshold baseline,
             the ledger, the queue, .env-> never, by any path

A model never rewrites its own score: the ledger is read-only here, and
`audit()` is run first. If the ledger fails audit we refuse to improve at all,
because improving from a score that can be inflated teaches the wrong lesson.

Graduation: a lesson that has cost the pipeline twice MUST become code, and
every `[GRADUATED -> module.SYMBOL]` marker in lessons.md is verified against
the actual code by `graduation_check()` so a claim that stopped being true is
a failure, not a skip.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from .arch import propose as arch_propose
from .journal import open_journal
from .config import weights
from .reward import RewardLedger, audit

LESSONS_PATH = "loops/lessons.md"

# Modules a graduation marker may point at (module base name -> importable path).
GRADUATION_MODULES = {
    "queue": "eve.queue",
    "reward": "eve.reward",
    "gates": "eve.gates",
    "corpus": "eve.corpus",
    "arch": "eve.arch",
    "books": "eve.books",
    "playtest": "eve.playtest",
    "publish": "eve.publish",
    "meta": "eve.meta",
}

# Dominant loss component -> policy change + tier + target area.
# The key is the reward component where reward is being lost.
LOSS_POLICY = {
    "fun_pass": {
        "tier": "CODE",
        "target": "playtest",
        "lesson": ("fun is the load-bearing term; if it never fires no game "
                   "finishes. Prioritize rules that reach a real end state and "
                   "never give a dominant first player."),
    },
    "rules_pass": {
        "tier": "CODE",
        "target": "rules",
        "lesson": ("games are dying at the rules gate: keep the rulebook "
                   "within the complexity budget and prove the machinery "
                   "reaches an end before spending build time."),
    },
    "novelty_pass": {
        "tier": "CODE",
        "target": "ideator",
        "lesson": ("ideas are failing the novelty gate: the identity must be a "
                   "genuine 'like X plus Y' combination that is new against "
                   "the corpus, not a themed skin on an owned mechanic."),
    },
    "print_pass": {
        "tier": "CODE",
        "target": "brief",
        "lesson": ("games are failing the print/build gate: settle the bill, "
                   "the interfaces, and the bed plan in the brief so the build "
                   "does not discover a print defect that planning could have "
                   "caught."),
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def lessons_path(cfg) -> Path:
    return cfg.root / LESSONS_PATH


def read_lessons(cfg) -> list[str]:
    p = lessons_path(cfg)
    if not p.exists():
        return []
    return [l for l in p.read_text().splitlines() if l.strip()]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def dominant_loss(cfg, ledger: RewardLedger) -> dict:
    """Find the load-bearing loss: the positive term most often missing.

    Returns a record describing the loss so improve() can target a policy
    change at it. Only non-terminal games can still earn the positive stage
    terms, so we measure lost opportunity over the games still in play plus
    the penalties already spent.
    """
    games = {}
    for e in ledger._entries:
        games.setdefault(e.slug, {"penalties": 0.0, "won": set()})
        g = games[e.slug]
        if e.component in ("repair_fail", "rework", "dead_game"):
            g["penalties"] += e.value * (cfg.gamma ** e.step)
        else:
            g["won"].add(e.component)

    # Required positive terms every in-flight game must earn.
    required = ["novelty_pass", "rules_pass", "fun_pass", "print_pass"]
    loss = {}
    for _, g in games.items():
        for comp in required:
            if comp not in g["won"]:
                loss[comp] = loss.get(comp, 0.0) + weights(cfg).get(comp, 0.0)
    for _, g in games.items():
        loss["_penalties"] = loss.get("_penalties", 0.0) + g["penalties"]

    if not loss:
        return {"component": None, "magnitude": 0.0, "note": "no measurable loss yet"}

    best_component = max(loss, key=lambda k: loss[k])
    best = loss[best_component]
    if best_component == "_penalties":
        best_component = "penalties_spent"
    return {
        "component": best_component,
        "magnitude": round(best, 4),
        "loss_by_component": {k: round(v, 4) for k, v in loss.items()},
    }


def run(cfg, *, dry_run: bool = False, journal=None) -> dict:
    """Run one self-improvement session. Returns a plan/result dict.

    Never edits taste, the threshold baseline, the ledger, or the queue.
    `dry_run` reports what would change without writing it.
    """
    journal = journal or open_journal(cfg)
    result = {"audit": [], "loss": None, "doc_writes": [], "code_proposals": [],
              "skipped": [], "dry_run": dry_run}

    # 1. Never improve from an unverifiable score.
    problems = audit(cfg)
    result["audit"] = problems
    if problems:
        result["skipped"].append("audit failed; refusing to improve from an "
                                 "unverifiable ledger")
        journal.append("improve", outcome="blocked", reason="audit_failed")
        return result

    # 2. Find the dominant loss.
    ledger = RewardLedger(cfg, journal=journal)
    loss = dominant_loss(cfg, ledger)
    result["loss"] = loss

    # 3. Loop B feeds the same path: fold in any unapplied arch lessons.
    try:
        from . import arch
        for lesson in arch.lessons(cfg, unapplied_only=True):
            _record_doc_lesson(cfg, journal, f"[arch:{lesson['target_area']}] "
                                             + lesson["lesson"])
            arch.apply(cfg, lesson["id"])
            result["doc_writes"].append(f"applied arch lesson {lesson['id']}")
    except Exception as exc:  # Loop B must never take down a session
        result["skipped"].append(f"arch feed failed: {exc}")

    # 3b. Loop D (great-books study) feeds the same path: fold any unapplied
    #     book learnings in as doc lessons, same as Loop B. Reading about game
    #     design is a *theoretical* self-improvement input, distinct from the
    #     empirical loss Loop C reports; both land in the one policy.
    try:
        from . import books
        for lesson in books.unapplied_learnings(cfg):
            _record_doc_lesson(
                cfg, journal,
                f"[books:{lesson.get('target_area', 'design')}] "
                + lesson["learning"])
            books.apply_learning(cfg, lesson["id"])
            result["doc_writes"].append(f"applied book learning {lesson['id']}")
    except Exception as exc:  # Loop D must never take down a session
        result["skipped"].append(f"books feed failed: {exc}")

    # 4. Target the dominant loss with a policy change.
    comp = loss.get("component")
    mapping = LOSS_POLICY.get(comp)
    if comp is None:
        journal.append("improve", outcome="noop", reason="no_loss")
        result["skipped"].append("no dominant loss to target")
        return result
    if mapping is None:
        result["skipped"].append(f"loss '{comp}' has no mapped policy change")
        return result

    lesson_text = mapping["lesson"]
    repeat = _is_repeat(cfg, lesson_text)
    tier = "CODE" if (mapping["tier"] == "CODE" or repeat) else "DOC"

    if tier == "DOC":
        _record_doc_lesson(cfg, journal, lesson_text)
        result["doc_writes"].append(comp)
    else:
        # CODE tier: a human reads this before it enters the harness shape.
        pid = arch_propose(cfg, target_area=mapping["target"],
                           change=f"[loss:{comp}] {lesson_text}", tier="CODE")
        result["code_proposals"].append(pid)
        journal.append("improve", outcome="proposed", component=comp, tier="CODE",
                       proposal=pid)

    journal.append("improve", outcome="done", component=comp, tier=tier,
                   magnitude=loss["magnitude"])
    return result


def _is_repeat(cfg, lesson_text: str) -> bool:
    """A lesson already in lessons.md is a repeat; a repeat MUST graduate."""
    key = _normalize(lesson_text)
    return any(_normalize(l) == key for l in read_lessons(cfg) if not l.startswith("#"))


def _record_doc_lesson(cfg, journal, lesson_text: str) -> None:
    p = lessons_path(cfg)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("# Eve lessons — hard rules from real builds\n\n")
    # Normalize the ending so we can detect repeats.
    body = _normalize(lesson_text)
    if any(_normalize(l) == body for l in read_lessons(cfg) if not l.startswith("#")):
        return
    with open(p, "a") as fh:
        fh.write(f"- {lesson_text}\n")


def graduation_check(cfg) -> list[str]:
    """Verify every [GRADUATED -> module.SYMBOL] marker in lessons.md.

    A marker is a claim that a lesson has become code. If the symbol no longer
    exists, the claim rots silently: the lesson is out of the prompts because
    it 'graduated', and nothing enforces it. Returns problems (empty == clean).
    """
    import importlib
    problems = []
    pattern = re.compile(r"\[GRADUATED -> ([A-Za-z0-9_.]+)(?:\s*\|\s*[^]]+)?\]")
    for line in read_lessons(cfg):
        for m in pattern.finditer(line):
            target = m.group(1)
            if "." not in target:
                problems.append(f"marker target '{target}' must be module.SYMBOL")
                continue
            mod_name, symbol = target.rsplit(".", 1)
            import_path = GRADUATION_MODULES.get(mod_name)
            if import_path is None:
                problems.append(f"marker names unknown module '{mod_name}'")
                continue
            try:
                mod = importlib.import_module(import_path)
            except Exception as exc:
                problems.append(f"cannot import '{import_path}': {exc}")
                continue
            if not hasattr(mod, symbol):
                problems.append(f"marker '{target}' but {import_path} has no '{symbol}'")
    return problems
