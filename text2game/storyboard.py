#!/usr/bin/env python3
"""gdd.md `## Turn structure` -> storyboard.json, the how-to video's script.

text2cad's howto.json is hand-written per product, which is why the relay's
first video was directed at a concept image before any STL existed. A board
game already states its own beats: the turn phases ARE the shots, in order, and
the Legacy section is the closing beat because it is the thing that cannot be
undone. Deriving them means the video cannot drift from the rules.

    ./storyboard.py <out_dir> [--beats 3]
"""
import json
import re
import sys
from pathlib import Path

# fl2va renders 3 beats per clip; more than that is a second clip, not a longer
# one. Measured on the gateway 2026-08-17: ~161s per render.
DURATIONS = [12, 10, 6]


def turn_beats(gdd: str) -> list:
    """Bold-numbered phases inside ## Turn structure, in document order."""
    m = re.search(r"^## Turn structure\s*$(.*?)(?=^## )", gdd, re.M | re.S)
    if not m:
        return []
    # Two shapes, because both are ordinary markdown and the GDD prompt pins
    # neither: `**1. Coach spill.**` (number inside the bold) and
    # `1. **Coach spill.**` (a numbered list item with a bold title).
    # coach-party 2026-08-20 wrote the second, this function required the
    # first, and it returned [] - which phase 3 printed as "beats: []" and
    # carried on, so the game shipped with no how-to video and nothing said a
    # word about why.
    beats = []
    body_stop = r"(?=^\s*(?:\*\*)?\d+\.|\Z)"
    found = re.findall(r"^\s*\*\*(\d+)\.\s*([^*]+?)\.?\*\*(.*?)" + body_stop,
                       m.group(1), re.S | re.M)
    if not found:
        found = re.findall(r"^\s*(\d+)\.\s*\*\*([^*]+?)\.?\*\*(.*?)" + body_stop,
                           m.group(1), re.S | re.M)
    for num, title, body in found:
        text = " ".join(body.split())
        parts = re.findall(r"`([a-z0-9_]+)`", body)
        beats.append({"n": int(num), "title": title.strip(),
                      "action": text[:400], "parts": sorted(set(parts))})
    return beats


def legacy_beat(gdd: str) -> dict:
    m = re.search(r"^## Legacy\s*$(.*?)(?=^## )", gdd, re.M | re.S)
    if not m:
        return {}
    body = " ".join(m.group(1).split())
    return {"n": 99, "title": "Legacy", "action": body[:400],
            "parts": sorted(set(re.findall(r"`([a-z0-9_]+)`", m.group(1))))}


def build(out_dir: Path, n_beats: int = 3) -> dict:
    gdd = (out_dir / "gdd.md").read_text(encoding="utf-8")
    beats = turn_beats(gdd)
    legacy = legacy_beat(gdd)
    # The last beat is always the irreversible one: a video of a legacy game
    # that never shows the irreversible act has not shown the game. But only
    # reserve that slot when there IS one - coach-party 2026-08-20 is a co-op
    # with no `## Legacy` section, and holding the slot open for a beat that
    # does not exist threw away a real turn phase, so a 3-phase round shipped
    # a 2-beat video that stops before the bell.
    chosen = (beats[:max(0, n_beats - 1)] + [legacy]) if legacy else beats[:n_beats]
    return {
        "source": "gdd.md ## Turn structure + ## Legacy",
        "durations": DURATIONS[:len(chosen)],
        "out": "howto_game.mp4",
        "beats": [{"beat": i + 1, "title": b["title"], "parts": b["parts"],
                   "action": b["action"]} for i, b in enumerate(chosen)],
        "caption": "",
    }


def main() -> int:
    out_dir = Path(sys.argv[1]).resolve()
    n = int(sys.argv[sys.argv.index("--beats") + 1]) if "--beats" in sys.argv else 3
    sb = build(out_dir, n)
    (out_dir / "storyboard.json").write_text(json.dumps(sb, indent=2), encoding="utf-8")
    for b in sb["beats"]:
        print(f"  beat {b['beat']}  {b['title']:<12} parts={b['parts']}")
    return 0 if sb["beats"] else 1


if __name__ == "__main__":
    sys.exit(main())
