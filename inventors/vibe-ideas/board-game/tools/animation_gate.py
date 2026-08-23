"""Freshness and approval gate for pre-table rule animations."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

VIDEO_REL = Path("animation/rules.mp4")
MANIFEST_REL = Path("animation/manifest.json")
REVIEW_REL = Path("review_animation.md")
SHA_RE = re.compile(r"^Video SHA256:\s*([0-9a-f]{64})$", re.IGNORECASE)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def evidence(idea_dir: Path) -> tuple[str | None, Path | None]:
    """Return (refusal reason, video path) for the animation gate."""
    idea = idea_dir / "idea.json"
    video = idea_dir / VIDEO_REL
    manifest_path = idea_dir / MANIFEST_REL
    review_path = idea_dir / REVIEW_REL
    if not video.is_file():
        return f"{VIDEO_REL} is missing", None
    if not manifest_path.is_file():
        return f"{MANIFEST_REL} is missing", None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return f"{MANIFEST_REL} is unreadable: {exc}", None
    if manifest.get("idea_sha256") != sha256(idea):
        return "animation manifest does not match the current idea.json", None
    video_hash = sha256(video)
    if manifest.get("video_sha256") != video_hash:
        return "animation manifest does not match animation/rules.mp4", None
    if not review_path.is_file():
        return f"{REVIEW_REL} is missing", None
    lines = [line.strip() for line in review_path.read_text(
        encoding="utf-8", errors="ignore").splitlines() if line.strip()]
    if not lines or lines[0].casefold() != "verdict: pass":
        return "board-game-lens-animation did not return Verdict: PASS", None
    reviewed_hash = next(
        (match.group(1).lower() for line in lines[1:]
         if (match := SHA_RE.match(line))), None)
    if reviewed_hash != video_hash:
        return "review_animation.md does not approve the current video hash", None
    return None, video
