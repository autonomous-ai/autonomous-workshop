#!/usr/bin/env python3
"""Fixtures for concept_video.py - the glue is tested before it costs a render.

The winner block below is copied verbatim from out/dead-stop/discover.md, the
first panel result this module was built against.

    python3 tests/test_concept_video.py
"""
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import concept_video  # noqa: E402

WINNER_BLOCK = """# Discover panel — 6 candidates, 3 judges

| candidate | lane | ... |

WINNER: dead-stop

You launch a workboat loaded with crates down the harbour so hard that the pilings stop it dead and the cargo keeps going — every crate that lands on the dock is yours until somebody else's spill knocks it off again.
Name: Dead Stop
Box face: Come in hot. The boat stops. The cargo doesn't.
First look: The stubby printed workboat sitting on its launch cradle with four crates stacked in its open hold, band already hooked.
Mechanism: banded hull launch into sprung piling jaws that arrest the boat and throw its loose cargo onto a shared dock — 7 parts.
Why nobody has this: Every launch game scores the thing you launched.
Seed: raw/2026-08-22-x-scrape.md — "boat docking"

PROMPT: Design a 7-design FDM box.
"""


def case(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  <- {detail}"))
    return ok


def main() -> int:
    r = []
    f = concept_video.fields(WINNER_BLOCK)
    r.append(case("winner block parses", f.get("slug") == "dead-stop"
                  and f.get("name") == "Dead Stop"
                  and f.get("box_face", "").startswith("Come in hot"), f))
    r.append(case("pitch is the unlabelled first line",
                  f.get("pitch", "").startswith("You launch a workboat"), f.get("pitch")))
    r.append(case("part count stripped off the mechanism",
                  f.get("mechanism", "").endswith("shared dock"), f.get("mechanism")))
    r.append(case("no winner -> no fields", concept_video.fields("# nothing") == {}))

    p = concept_video.build_prompt(f)
    r.append(case("prompt carries name, mechanism and pitch",
                  "Dead Stop" in p and "sprung piling jaws" in p
                  and "workboat loaded with crates" in p, p[:120]))
    r.append(case("prompt pins the FDM look and the soundscape",
                  "layer lines" in p and "soundscape" in p
                  and "Non-diegetic music" in p))
    bare = concept_video.build_prompt({"slug": "some-game"})
    r.append(case("missing fields degrade to the slug, not a crash",
                  "Some Game" in bare, bare[:80]))

    c = concept_video.caption(f)
    r.append(case("caption fits sendVideo's 1024-byte cap and keeps the command",
                  len(c.encode()) <= 1024 and "--slug dead-stop" in c, len(c.encode())))
    long_f = dict(f, pitch=f["pitch"] * 20)
    c2 = concept_video.caption(long_f)
    r.append(case("an over-long pitch is clipped, the command survives",
                  len(c2.encode()) <= 1024 and "--slug dead-stop" in c2,
                  len(c2.encode())))

    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "discover.md").write_text(WINNER_BLOCK, encoding="utf-8")
        (d / "concept_video.mp4").write_bytes(b"x")
        got = concept_video.run(d)  # must return without any network call
        r.append(case("existing artifact skips the render", got.name == "concept_video.mp4"))
        try:
            concept_video.run(Path(td) / "nope")
            r.append(case("missing discover.md raises", False))
        except (RuntimeError, FileNotFoundError):
            r.append(case("missing discover.md raises", True))

    print(f"\n{sum(r)}/{len(r)} passed")
    return 0 if all(r) else 1


if __name__ == "__main__":
    sys.exit(main())
