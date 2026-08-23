"""L0 meta loop — the weekly self-improvement session, leashed in code.

The one sentence that decides everything: every self-improving system that
failed, failed by editing its own judge (DGM removed its hallucination
markers — docs/research/self-improvement-landscape.md). So the improver
agent PROPOSES writes and this module DISPOSES, against the allowlist that
lives in harness/integrity.py — which is itself on the FORBIDDEN list, so
the leash cannot be renegotiated from inside a session.

The enforcement ladder, all in Python, none in prompts (vibe-ideas:
"budgets live in code, not prompts"):

1. Evidence block built HERE from the actual ledgers — the agent works
   only from what the harness hands it ("a change with no evidence behind
   it is a preference", text2cad improve.py).
2. The agent returns a JSON list of proposed writes [{path, content}].
3. ONE forbidden path rejects the ENTIRE session — zero writes applied,
   logged loudly. Partial application would let a poisoned session buy
   its doc-tier half ("a pipeline that can edit TASTE.md can talk itself
   into anything").
4. Allowlisted (doc-tier) writes apply with .bak copies kept; anything
   else is CODE tier and is written to knowledge/PROPOSALS.md as a
   diff-to-review — never applied, never silently dropped.
5. The full test suite must pass after apply or EVERY write reverts —
   no partial credit for a change that broke the checks proving it safe.
6. Nothing here commits to git — the integrator owns commits; this module
   appends its session report to knowledge/improve-log.md instead.

Stdlib only, Python 3.9. No env reads at import time (CONTRACTS §6).
"""

import fnmatch
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone

from harness import agents, bandit, integrity, ledger, queue

AGENT = "bob-improver"

# How much recent ledger the improver sees. 20 rows ≈ the last few games'
# scored events — enough to spot a pattern, small enough that the pack
# stays evidence, not archive (Reflexion's buffer works because it is
# short; same reason lessons.md caps at ~30).
LEDGER_TAIL_ROWS = 20

# Suffix for the backup copies kept during apply. Removed on success,
# consumed by the revert on failure.
BAK_SUFFIX = ".improve-bak"

IMPROVE_LOG = os.path.join("knowledge", "improve-log.md")
PROPOSALS = os.path.join("knowledge", "PROPOSALS.md")
LESSONS = os.path.join("knowledge", "lessons.md")


def _home():
    return os.environ.get("BOB_HOME") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _now():
    return datetime.now(timezone.utc)


def _atomic_write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "{}.tmp.{}".format(path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _read(path):
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Path authority — the leash, enforced here, defined in harness/integrity.py
# ---------------------------------------------------------------------------

def _match(rel, pattern):
    """Same glob semantics as integrity.improve_write_allowed: '**' means
    'this directory and everything under it'. Duplicated deliberately —
    integrity exports only the allow decision, and the forbidden/code-tier
    split needs the raw FORBIDDEN match too."""
    if pattern.endswith("/**"):
        root = pattern[:-3]
        return rel == root or rel.startswith(root + "/")
    return fnmatch.fnmatch(rel, pattern)


def _normalize(path):
    """Repo-relative forward-slash path, or None when the path tries to
    escape the repo (absolute, drive-rooted, or any '..' component).
    An escape attempt is treated as FORBIDDEN — an improver that writes
    outside BOB_HOME has no auditor at all."""
    rel = str(path).replace(os.sep, "/")
    while rel.startswith("./"):
        rel = rel[2:]
    if not rel or rel.startswith("/") or rel.startswith("~"):
        return None
    if any(part == ".." for part in rel.split("/")):
        return None
    return rel


def _is_forbidden(rel):
    return any(_match(rel, p) for p in integrity.FORBIDDEN)


# ---------------------------------------------------------------------------
# Evidence pack — built in code, from the real ledgers
# ---------------------------------------------------------------------------

def _open_lessons_count():
    """Lessons whose bracket header carries OPEN (lessons.md contract:
    `- [cause · phase · date · cost · status]`, status OPEN | GRADUATED).
    This tally IS the engineering backlog the improver prioritizes."""
    n = 0
    for line in _read(os.path.join(_home(), LESSONS)).splitlines():
        stripped = line.strip()
        if stripped.startswith("- [") and "OPEN" in stripped.split("]")[0]:
            n += 1
    return n


def _build_evidence():
    """The evidence pack, assembled from the actual state files — never
    from the agent's own claims about them (self-reported evidence is the
    self-scored reward problem wearing a different hat)."""
    try:
        games = queue.load().get("games", {})
        state_counts = dict(Counter(
            g.get("state", "?") for g in games.values()))
    except Exception as e:  # a broken queue is itself evidence
        state_counts = {"error": "queue unreadable: {}".format(e)}

    try:
        tail = ledger.rows()[-LEDGER_TAIL_ROWS:]
    except Exception as e:
        tail = [{"error": "ledger unreadable: {}".format(e)}]

    try:
        arms = bandit.arms()
    except Exception as e:
        arms = {"error": "bandit unreadable: {}".format(e)}

    return {
        "queue_state_counts": state_counts,
        "ledger_tail": tail,
        "open_lessons": _open_lessons_count(),
        "bandit_arms": arms,
    }


# ---------------------------------------------------------------------------
# Reply parsing
# ---------------------------------------------------------------------------

def _parse_writes(text):
    """The agent's reply must be (or contain) a JSON list of
    {path, content} dicts. Three attempts, strictest first; None means
    unusable — the session then applies nothing rather than guessing at
    what the improver meant (a guessed write is an unaudited write)."""
    candidates = [text]
    if "```" in text:
        # take fenced blocks, ```json or bare
        for chunk in text.split("```")[1::2]:
            if chunk.startswith("json"):
                chunk = chunk[4:]
            candidates.append(chunk)
    start, end = text.find("["), text.rfind("]")
    if start != -1 and end > start:
        candidates.append(text[start:end + 1])

    for cand in candidates:
        try:
            data = json.loads(cand.strip())
        except ValueError:
            continue
        if not isinstance(data, list):
            continue
        writes = []
        ok = True
        for item in data:
            if (isinstance(item, dict)
                    and isinstance(item.get("path"), str)
                    and isinstance(item.get("content"), str)):
                writes.append({"path": item["path"],
                               "content": item["content"]})
            else:
                ok = False
                break
        if ok:
            return writes
    return None


# ---------------------------------------------------------------------------
# Apply / revert
# ---------------------------------------------------------------------------

def _apply_write(rel, content, applied):
    """Write one file with a revert record. The .bak copy is made BEFORE
    the write and only deleted after the suite passes — a crash between
    apply and verify leaves the .bak on disk as the recovery breadcrumb."""
    abs_path = os.path.join(_home(), rel)
    record = {"rel": rel, "abs": abs_path, "existed": os.path.exists(abs_path)}
    if record["existed"]:
        shutil.copy2(abs_path, abs_path + BAK_SUFFIX)
    _atomic_write(abs_path, content)
    applied.append(record)


def _revert_all(applied):
    """Undo every applied write from its .bak (or remove a created file).
    Reverse order so a file written twice in one session lands back on
    its ORIGINAL content, not an intermediate."""
    for record in reversed(applied):
        bak = record["abs"] + BAK_SUFFIX
        if record["existed"] and os.path.exists(bak):
            os.replace(bak, record["abs"])
        else:
            try:
                os.remove(record["abs"])
            except OSError:
                pass
            try:
                os.remove(bak)
            except OSError:
                pass


def _cleanup_baks(applied):
    for record in applied:
        try:
            os.remove(record["abs"] + BAK_SUFFIX)
        except OSError:
            pass


def _run_suite():
    """Run the full test suite; (ok, tail_of_output). Module-level so
    tests monkeypatch it (running the real suite from inside the suite
    would recurse). A BOB_HOME without a tests/ dir passes vacuously —
    that is a fresh install, not a failure."""
    home = _home()
    if not os.path.isdir(os.path.join(home, "tests")):
        return True, "no tests/ dir under BOB_HOME — suite skipped"
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests",
             "-q"],
            cwd=home, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, timeout=1800)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, "suite runner failed: {}".format(e)
    return proc.returncode == 0, (proc.stdout or "")[-4000:]


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _log_session(lines):
    """Append the session report to knowledge/improve-log.md. This file is
    harness telemetry (written by code, never proposed by the agent), so
    it sits outside the allowlist question entirely."""
    path = os.path.join(_home(), IMPROVE_LOG)
    existing = _read(path)
    if existing and not existing.endswith("\n"):
        existing += "\n"
    stamp = _now().strftime("%Y-%m-%d %H:%M UTC")
    body = "\n## Session {}\n\n{}\n".format(
        stamp, "\n".join("- " + l for l in lines))
    _atomic_write(path, existing + body)


def _loud(msg):
    """Rejections must be impossible to miss in the tick log — a leash
    that yanks silently teaches nobody anything."""
    sys.stderr.write("IMPROVE REJECTED: {}\n".format(msg))


# ---------------------------------------------------------------------------
# The session
# ---------------------------------------------------------------------------

def improve():
    """One improve session per CONTRACTS §2 (meta loop row).

    Contract: improve() -> None; the returned summary dict is a superset
    for tests and `bob improve`'s status line. Never commits to git —
    the integrator owns commits.
    """
    evidence = _build_evidence()
    prompt = "".join([
        _prompt_text(),
        "\n## Evidence pack (assembled by the harness — work ONLY from "
        "this)\n\n```json\n",
        json.dumps(evidence, indent=2, default=str),
        "\n```\n",
        "\n## Output rule (harness contract)\n\nReturn ONLY a JSON list "
        "of proposed writes: [{\"path\": \"<repo-relative>\", "
        "\"content\": \"<full new file content>\"}]. The harness enforces "
        "your write authority in code: doc-tier paths apply, code-tier "
        "paths become PROPOSALS.md entries, one forbidden path voids the "
        "whole session. An empty list [] is a legal session.\n",
    ])

    try:
        result = agents.run_agent(AGENT, prompt)
        text = result.text or ""
    except agents.QuotaExhausted:
        raise  # driver sets quota_until; never retry into the wall
    except agents.AgentError as e:
        _log_session(["session FAILED before any write: {}".format(e)])
        return {"outcome": "agent_error", "applied": 0}

    writes = _parse_writes(text)
    if writes is None:
        _log_session(["session produced no parseable write list — "
                      "nothing applied (reply head: {!r})".format(
                          text[:200])])
        return {"outcome": "unparseable", "applied": 0}

    # --- classify, forbidden check FIRST over the whole list ------------
    doc_tier, code_tier, forbidden = [], [], []
    for w in writes:
        rel = _normalize(w["path"])
        if rel is None or _is_forbidden(rel):
            forbidden.append(w["path"])
        elif integrity.improve_write_allowed(rel):
            doc_tier.append({"path": rel, "content": w["content"]})
        else:
            code_tier.append({"path": rel, "content": w["content"]})

    if forbidden:
        # One forbidden path voids EVERYTHING — including the doc-tier
        # writes riding alongside it. Revert semantics with zero applied:
        # the cheapest revert is the one that never happens.
        msg = ("session proposed FORBIDDEN path(s) {} — entire session "
               "rejected, zero writes applied (integrity.FORBIDDEN, "
               "enforced in code)".format(forbidden))
        _loud(msg)
        _log_session(["REJECTED: " + msg,
                      "{} doc-tier and {} code-tier writes discarded with "
                      "it".format(len(doc_tier), len(code_tier))])
        return {"outcome": "rejected_forbidden", "applied": 0,
                "forbidden": forbidden}

    # --- apply doc tier; divert code tier to PROPOSALS.md ----------------
    applied = []
    report = []
    try:
        for w in doc_tier:
            _apply_write(w["path"], w["content"], applied)
            report.append("applied (doc-tier): {}".format(w["path"]))

        if code_tier:
            block_parts = []
            stamp = _now().strftime("%Y-%m-%d")
            for i, w in enumerate(code_tier, 1):
                block_parts.append(
                    "\n## P-{}-improve-{}: code-tier write to {}\n"
                    "Evidence: proposed by the improve session of {} — "
                    "see knowledge/improve-log.md\n"
                    "Tier: CODE (never auto-applied; a human reviews)\n"
                    "```\n{}\n```\n".format(
                        stamp, i, w["path"], stamp, w["content"]))
                report.append(
                    "diverted (code-tier → PROPOSALS.md): {}".format(
                        w["path"]))
            proposals_path = os.path.join(_home(), PROPOSALS)
            existing = _read(proposals_path)
            if existing and not existing.endswith("\n"):
                existing += "\n"
            # Through _apply_write so a suite failure reverts the
            # proposals append together with everything else.
            _apply_write(PROPOSALS, existing + "".join(block_parts),
                         applied)
    except OSError as e:
        _revert_all(applied)
        _log_session(["session FAILED mid-apply ({}) — all {} writes "
                      "reverted".format(e, len(applied))])
        return {"outcome": "apply_error", "applied": 0}

    # --- suite must pass or everything reverts ---------------------------
    suite_ok, suite_out = _run_suite()
    if not suite_ok:
        _revert_all(applied)
        _log_session(report + [
            "SUITE FAILED after apply — ALL {} writes reverted (no "
            "partial credit for a change that broke the checks proving "
            "it safe)".format(len(applied)),
            "suite tail: {!r}".format(suite_out[-500:])])
        return {"outcome": "reverted_suite_failure", "applied": 0,
                "reverted": len(applied)}

    _cleanup_baks(applied)
    if not report:
        report = ["empty session: agent proposed no writes (a legal "
                  "result — no evidence, no change)"]
    report.append("suite green; nothing committed (integrator owns git)")
    _log_session(report)
    return {"outcome": "ok", "applied": len(doc_tier),
            "proposals": len(code_tier)}


def _prompt_text():
    for base in (_home(), _repo_root()):
        p = os.path.join(base, ".claude", "agents", AGENT + ".md")
        content = _read(p)
        if content:
            return content
    return ""
