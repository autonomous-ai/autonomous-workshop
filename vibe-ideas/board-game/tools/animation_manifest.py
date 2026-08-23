#!/usr/bin/env python3
"""Write the hash-bound metadata for a rendered rule animation."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from animation_gate import MANIFEST_REL, VIDEO_REL, sha256


def probe(video: Path) -> dict:
    command = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=codec_name,width,height,r_frame_rate,pix_fmt",
        "-of", "json", str(video),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise SystemExit(f"ffprobe failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("idea_dir", type=Path)
    parser.add_argument("video", type=Path)
    args = parser.parse_args()
    idea_dir = args.idea_dir.resolve()
    video = args.video.resolve()
    expected = (idea_dir / VIDEO_REL).resolve()
    if video != expected:
        raise SystemExit(f"final video must be {expected}")
    idea = idea_dir / "idea.json"
    if not idea.is_file() or not video.is_file():
        raise SystemExit("idea.json and animation/rules.mp4 must both exist")
    metadata = probe(video)
    stream = (metadata.get("streams") or [{}])[0]
    output = {
        "idea_sha256": sha256(idea),
        "video_sha256": sha256(video),
        "video": str(VIDEO_REL),
        "codec": stream.get("codec_name"),
        "width": stream.get("width"),
        "height": stream.get("height"),
        "fps": stream.get("r_frame_rate"),
        "pixel_format": stream.get("pix_fmt"),
        "duration_seconds": float((metadata.get("format") or {}).get("duration", 0)),
        "size_bytes": int((metadata.get("format") or {}).get("size", 0)),
    }
    target = idea_dir / MANIFEST_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
