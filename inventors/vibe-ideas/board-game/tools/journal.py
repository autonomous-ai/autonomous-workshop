#!/usr/bin/env python3
"""Keep complete local pipeline history and send one kind of journal notice.

Routine events recorded with ``append`` are written only to
``board-game/.journal_log.jsonl`` for ``dashboard.py``. The journal Telegram
channel receives only ``rules_ready``: the proposal, its approved rule
animation, and a link to the completed replay/playtest website.

    python3 board-game/tools/journal.py append <slug> --kind gate \
        --by gate.py --summary "RULES PASS"
    python3 board-game/tools/journal.py rules_ready <slug>

For a rework, ``pipeline_queue.py`` saves the immediately previous idea before
the ideator changes it. ``rules_ready`` uses that snapshot to label the
iteration. Repeating ``rules_ready`` for an unchanged ``idea.json`` is
deduplicated.

Nothing in the pipeline may read the local journal log. It has exactly one
reader: ``dashboard.py``. This keeps narrative history from becoming another
input agents learn to optimise.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import animation_gate  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
IDEAS = REPO_ROOT / "board-game" / "ideas"
JOURNAL_LOG = REPO_ROOT / "board-game" / ".journal_log.jsonl"
SNAPSHOT_NAME = ".idea_before_rework.json"
NOTICE_NAME = ".rules_ready_notice.json"
MESSAGE_LIMIT = 3200
BLOCK_TEXT_LIMIT = 2400

KINDS = {
    "proposed": "the idea was invented",
    "gate": "a deterministic checker ran",
    "rework": "the idea changed in response to something",
    "clarify": "ambiguity was removed without touching the mechanics",
    "brief": "dimensions were chosen",
    "draft": "the first real geometry",
    "build": "the full build",
    "repair": "a repair round",
    "lens": "a review lens gave a verdict",
    "owner": "you decided something",
    "state": "the pipeline moved it",
    "note": "anything else worth remembering",
    "rules_ready": "the rules passed every pre-table gate",
}


def record(slug: str, kind: str, by: str, summary: str,
           body: str, title: str, at: str) -> None:
    """Append one untruncated entry for the dashboard only."""
    JOURNAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({
        "at": at, "slug": slug, "kind": kind, "by": by,
        "title": title or slug, "summary": summary.strip(), "body": body.strip(),
    })
    with JOURNAL_LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def append(slug: str, kind: str, by: str, summary: str,
           body: str = "", title: str = "") -> None:
    """Record routine history locally. This function never sends Telegram."""
    now = datetime.now(timezone.utc)
    record(slug, kind, by, summary, body, title, now.isoformat())


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(value: Any) -> str:
    if isinstance(value, dict) and "text" in value:
        value = value["text"]
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def _same(left: Any, right: Any) -> bool:
    return json.dumps(left, sort_keys=True, ensure_ascii=False) == json.dumps(
        right, sort_keys=True, ensure_ascii=False)


def _escaped_segments(value: Any) -> list[str]:
    """Escape and split without dropping content or cutting an HTML entity."""
    segments: list[str] = []
    current = ""
    for character in _text(value):
        escaped = html.escape(character)
        if current and len(current) + len(escaped) > BLOCK_TEXT_LIMIT:
            segments.append(current)
            current = escaped
        else:
            current += escaped
    segments.append(current)
    return segments


def _blocks(label: str, value: Any, previous: Any,
            is_rework: bool) -> list[str]:
    changed = is_rework and not _same(value, previous)
    rendered = []
    for index, segment in enumerate(_escaped_segments(value), start=1):
        suffix = f" (continued {index})" if index > 1 else ""
        content = f"{html.escape(label + suffix)}\n{segment}"
        rendered.append(f"<b>{content}</b>" if changed else content)
    return rendered


def _indexed(previous: dict, section: str, index: int) -> Any:
    values = (previous.get("rules") or {}).get(section) or []
    return values[index] if index < len(values) else None


def _phase_label(is_rework: bool, rework_number: int | None,
                 disposition: str | None) -> str:
    """`INITIAL PROPOSAL`, `CLARIFY n/3`, or `REWORK n/3`.

    The number is the round within its own kind of budget, so the denominator
    follows the disposition: a clarify round is `n/CLARIFY_BUDGET`, a rework
    round is `n/REWORK_BUDGET`. Both are imported lazily because
    `pipeline_queue` imports this module and a top-level import back would be
    circular.
    """
    if not is_rework:
        return "INITIAL PROPOSAL"
    from pipeline_queue import CLARIFY_BUDGET, REWORK_BUDGET
    budget = CLARIFY_BUDGET if disposition == "clarify" else REWORK_BUDGET
    label = "CLARIFY" if disposition == "clarify" else "REWORK"
    suffix = f" {rework_number}/{budget}" if rework_number else ""
    return f"{label}{suffix}"


def render_rules_ready(idea: dict, previous: dict | None = None,
                       rework_number: int | None = None,
                       disposition: str | None = None) -> list[str]:
    """Render self-contained HTML chunks, bolding changed rework blocks."""
    is_rework = previous is not None
    title = _text(idea.get("title") or idea.get("slug") or "Untitled")
    slug = _text(idea.get("slug") or "unknown")
    phase = _phase_label(is_rework, rework_number, disposition)
    blocks = [
        f"<b>RULES READY FOR TABLE</b>\n{html.escape(title)} "
        f"({html.escape(slug)})\n{phase}",
    ]
    blocks.extend(_blocks(
        "CONCEPT", idea.get("concept", ""),
        previous.get("concept") if previous else None, is_rework))
    blocks.extend(_blocks(
        "PLAYERS", idea.get("players", {}),
        previous.get("players") if previous else None, is_rework))
    if "action_types" in idea:
        blocks.extend(_blocks(
            "ACTION TYPES", idea["action_types"],
            previous.get("action_types") if previous else None, is_rework))

    rules = idea.get("rules") or {}
    for section in ("setup", "turn", "end"):
        current = rules.get(section) or []
        prior = ((previous.get("rules") or {}).get(section) or []
                 if previous else [])
        for index, value in enumerate(current):
            blocks.extend(_blocks(
                f"{section.upper()} {index + 1}", value,
                _indexed(previous, section, index) if previous else None,
                is_rework))
        if is_rework and len(prior) > len(current):
            for index in range(len(current), len(prior)):
                blocks.extend(_blocks(
                    f"REMOVED {section.upper()} {index + 1}",
                    prior[index], None, True))

    if "win" in rules:
        old_win = (previous.get("rules") or {}).get("win") if previous else None
        blocks.extend(_blocks("WIN", rules["win"], old_win, is_rework))

    current_components = [
        {"name": value.get("name"), "qty": value.get("qty")}
        for value in idea.get("components", [])
    ]
    prior_components = [
        {"name": value.get("name"), "qty": value.get("qty")}
        for value in (previous or {}).get("components", [])
    ]
    blocks.extend(_blocks(
        "COMPONENT BILL", current_components, prior_components, is_rework))

    chunks: list[str] = []
    current = ""
    for block in blocks:
        candidate = block if not current else current + "\n\n" + block
        if current and len(candidate) > MESSAGE_LIMIT:
            chunks.append(current)
            current = block
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def render_video_caption(idea: dict, previous: dict | None = None,
                         rework_number: int | None = None,
                         disposition: str | None = None,
                         site_url: str = "") -> str:
    """Render the one Telegram post: proposal, video caption, and site link."""
    phase = _phase_label(previous is not None, rework_number, disposition)
    title = html.escape(_text(idea.get("title") or idea.get("slug") or "Untitled"))
    slug = html.escape(_text(idea.get("slug") or "unknown"))
    prefix = f"<b>BOARD GAME PROPOSAL</b>\n{title} ({slug})\n{phase}\n\n"
    escaped_url = html.escape(site_url, quote=True)
    suffix = ("\n\nRule animation attached.\n"
              f'<a href="{escaped_url}">Replay simulation / playtest</a>')
    budget = max(0, 1000 - len(prefix) - len(suffix))
    escaped = ""
    truncated = False
    for character in _text(idea.get("concept", "")):
        token = html.escape(character)
        if len(escaped) + len(token) > max(0, budget - 3):
            truncated = True
            break
        escaped += token
    if truncated:
        escaped = escaped.rstrip() + "..."
    return prefix + escaped + suffix


def playtest_site_url(idea_dir: Path) -> str:
    """Return the generated website's absolute local file URI."""
    return (idea_dir / "playtest" / "site" / "index.html").resolve().as_uri()


def pretable_gate_failure(idea_dir: Path, idea: dict) -> str | None:
    """Return why this iteration is not eligible for a journal notification."""
    import rules_check

    findings = rules_check.check(idea)
    if findings:
        return f"rules_check has {len(findings)} finding(s)"

    idea_path = idea_dir / "idea.json"
    review_path = idea_dir / "review_rules.md"
    if not review_path.is_file():
        return "review_rules.md is missing"
    if review_path.stat().st_mtime < idea_path.stat().st_mtime:
        return "review_rules.md is older than idea.json"
    first_line = next(
        (line.strip() for line in review_path.read_text(
            encoding="utf-8", errors="ignore").splitlines() if line.strip()), "")
    if first_line.casefold() != "verdict: pass":
        return "board-game-lens-rules did not return Verdict: PASS"

    playtest_path = idea_dir / "playtest.json"
    if not playtest_path.is_file():
        return "playtest.json is missing"
    if playtest_path.stat().st_mtime < idea_path.stat().st_mtime:
        return "playtest.json is older than idea.json"
    if _read_json(playtest_path).get("pass") is not True:
        return "playtest.py did not pass"
    animation_failure, _ = animation_gate.evidence(idea_dir)
    if animation_failure:
        return animation_failure
    site = idea_dir / "playtest" / "site"
    index_path = site / "index.html"
    data_path = site / "data.json"
    if not index_path.is_file() or not data_path.is_file():
        return "playtest website is missing; run table_run.py first"
    if min(index_path.stat().st_mtime, data_path.stat().st_mtime) < idea_path.stat().st_mtime:
        return "playtest website is older than idea.json"
    if not (_read_json(data_path).get("runs") or []):
        return "playtest website contains no replay runs"
    return None


def cmd_append(args) -> int:
    body = args.body or ""
    if args.body_file:
        source = Path(args.body_file)
        if source.is_file():
            detail = source.read_text(encoding="utf-8", errors="ignore")
            body = (body + "\n\n" + detail).strip() if body else detail
    append(args.slug, args.kind, args.by, args.summary, body, args.title or "")
    return 0


def cmd_rules_ready(args) -> int:
    import telegram

    idea_dir = IDEAS / args.slug
    idea_path = idea_dir / "idea.json"
    if not idea_path.is_file():
        raise SystemExit(f"missing idea: {idea_path}")
    idea = _read_json(idea_path)
    failed = pretable_gate_failure(idea_dir, idea)
    if failed:
        raise SystemExit(
            f"refusing rules-ready Telegram for {args.slug}: {failed}")
    digest = _digest(idea_path)
    marker_path = idea_dir / NOTICE_NAME
    snapshot_path = idea_dir / SNAPSHOT_NAME
    snapshot = _read_json(snapshot_path) if snapshot_path.is_file() else {}
    previous = snapshot.get("idea")
    rework_number = snapshot.get("rework_number")
    disposition = snapshot.get("disposition")
    _, video = animation_gate.evidence(idea_dir)
    video_digest = animation_gate.sha256(video)
    if marker_path.is_file():
        marker = _read_json(marker_path)
        if (marker.get("idea_sha256") == digest
                and marker.get("video_sha256") == video_digest):
            print(f"{args.slug}: rules-ready Telegram already sent for this iteration")
            return 0

    telegram.load_env()
    site_url = playtest_site_url(idea_dir)
    caption = render_video_caption(
        idea, previous, rework_number, disposition, site_url)
    chat = os.environ.get("TELEGRAM_CHAT_JOURNAL", "").strip()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not (token and chat):
        print("--- journal Telegram not configured; rules-ready notice is here ---")
        print(f"[video] {video}")
        print(caption)
        return 0
    telegram.send(caption, video=video, chat=chat, parse_mode="HTML")

    now = datetime.now(timezone.utc)
    marker = {
        "idea_sha256": digest,
        "video_sha256": video_digest,
        "sent_at": now.isoformat(),
        "message_count": 1,
    }
    marker_path.write_text(json.dumps(marker, indent=2), encoding="utf-8")
    record(args.slug, "rules_ready", "rules_gate",
           "proposal, rule animation, and playtest site sent to journal Telegram",
           "", idea.get("title", args.slug), now.isoformat())
    print(f"{args.slug}: sent rules-ready Telegram (1 message)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("append", help="record one local dashboard event")
    p.add_argument("slug")
    p.add_argument("--kind", required=True, choices=sorted(KINDS))
    p.add_argument("--by", required=True,
                   help="who acted: an agent name, a tool name, or 'owner'")
    p.add_argument("--summary", required=True, help="one line, in plain words")
    p.add_argument("--title", help="the game's name")
    p.add_argument("--body", help="optional detail recorded verbatim")
    p.add_argument("--body-file", help="file whose contents become the detail")
    p.set_defaults(fn=cmd_append)

    p = sub.add_parser(
        "rules_ready", help="send passed rules to the journal Telegram channel")
    p.add_argument("slug")
    p.set_defaults(fn=cmd_rules_ready)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
