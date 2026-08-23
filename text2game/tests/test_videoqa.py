#!/usr/bin/env python3
"""The gate on generated clips.

    python3 tests/test_videoqa.py

Every case is a way the gate could wave through the thing it exists to catch.
"""
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import harness  # noqa: E402
import prompts  # noqa: E402
import qa_clips  # noqa: E402

R = []


def ok(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + ("" if cond else f"  <- {detail}"))
    R.append(cond)


def main() -> int:
    PASS = {"verdict": "PASS", "same_parts": True, "same_count": True,
            "same_size": True, "possible_places": True, "right_action": True}
    ok("a clean verdict passes", not qa_clips.failed(PASS))

    # The one that matters: coach-party's clip LOOKED good and bred pawns.
    # A judge that writes PASS next to same_count false has contradicted
    # itself, and the specific field is the half that was actually measured.
    ok("PASS next to a false check still fails",
       qa_clips.failed({**PASS, "same_count": False}))
    for k in qa_clips.CHECKS:
        ok(f"a false {k} fails on its own", qa_clips.failed({**PASS, k: False}))
    ok("a FAIL verdict fails even with every check true",
       qa_clips.failed({**PASS, "verdict": "FAIL"}))
    ok("a missing verdict is a failure, not a pass", qa_clips.failed({}))
    # A judge that answered nothing must not read as a clean bill of health -
    # same shape as palette_collisions reporting "none" off zero colours.
    ok("an absent check does not count as true",
       not qa_clips.failed({"verdict": "PASS"}), "unknown checks are not asserted")

    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        ok("no rules anywhere yields an empty map", qa_clips.rules_for(d) == {})
        (d / "howto.json").write_text(json.dumps({"caption": "one beat"}),
                                      encoding="utf-8")
        ok("the caption is the fallback rule",
           qa_clips.rules_for(d) == {"*": "one beat"}, qa_clips.rules_for(d))
        (d / "howto_beats.json").write_text(json.dumps({"b1": "five spill"}),
                                            encoding="utf-8")
        ok("per-beat rules win over the caption",
           qa_clips.rules_for(d).get("b1") == "five spill", qa_clips.rules_for(d))
        (d / "howto_beats.json").write_text("{ broken", encoding="utf-8")
        ok("a broken rules file falls back instead of crashing",
           qa_clips.rules_for(d) == {"*": "one beat"}, qa_clips.rules_for(d))

        t = prompts.video_qa(d, "howto_b1_qa.png", "Exactly 5 visitors spill.")
        ok("the judge is told the rule", "Exactly 5 visitors spill." in t)
        # Match on the property, not on where the prose happens to wrap.
        flat = " ".join(t.split())
        ok("the judge is told the first cell is the reference",
           "FIRST cell is the REFERENCE" in flat
           and "the quantity the box actually contains" in flat, flat[:160])
        ok("the judge is asked all five questions",
           all(q in t for q in ("SAME PARTS", "SAME COUNT", "SAME SIZE",
                                "POSSIBLE PLACES", "RIGHT ACTION")))
        ok("counting is not allowed to be approximate",
           'about right' in t and "that is a fail" in t)
        ok("photoreal is explicitly not a defence", "not a defence" in t)
        ok("the verdict lands beside the sheet", "howto_b1_qa.json" in t)
        # The judge burned 21 turns and $0.68 on one clip and wrote nothing,
        # so the gate had no verdict to act on. DISCOVER's judges have carried
        # the same instruction since a panel died the same way.
        # Twice this judge spent every turn looking and wrote nothing - 21
        # turns then 31, $2.10 for two verdicts that never existed. Raising
        # the cap only bought more looking, so the file is now the FIRST
        # action and gets refined, instead of being perfect and absent.
        ok("writing the verdict is the judge's first instruction",
           t.index("VERY FIRST ACTION") < 200, t.index("VERY FIRST ACTION"))
        ok("and it is reminded again at the end",
           "partial evidence beats silence" in t)
    # The judge reasons in colour WORDS and inverted two of them on
    # 2026-08-21, calling the chartreuse villagers "visitors" and the ivory
    # visitors "villagers". Six of its nine findings were then about the wrong
    # pieces. The reference cell shows which colours exist, not which id each
    # one belongs to, so the mapping is stated.
    with tempfile.TemporaryDirectory() as td2:
        d2 = Path(td2)
        (d2 / "part_colors.json").write_text(json.dumps(
            {"visitor_pawn.stl": "#F1E9D7", "villager_pawn.stl": "#D7F23A"}),
            encoding="utf-8")
        (d2 / "art_direction.md").write_text(
            "- `visitor_pawn` - `#F1E9D7` - matte warm-ivory PLA.\n"
            "- `villager_pawn` - `#D7F23A` - matte fluorescent-chartreuse PLA.\n",
            encoding="utf-8")
        lt = prompts.video_qa(d2, "s_qa.png", "r")
        ok("the judge is told which id each colour belongs to",
           "WHICH COLOUR IS WHICH PART" in lt and "visitor_pawn" in lt)
        ok("and gets the colour WORD, not only the hex",
           "warm-ivory" in lt and "chartreuse" in lt, lt[lt.find("WHICH"):][:200])
        ok("no part_colors.json just omits the legend, it does not crash",
           "WHICH COLOUR IS WHICH PART" not in prompts.video_qa(Path(td), "s.png", "r"))
    # And a judge that still writes nothing must read as FAIL, never as clean.
    ok("a silent judge is a failure",
       qa_clips.failed({"verdict": "FAIL",
                        "issues": ["the judge wrote no verdict"]}))

    # The judge has to be able to SEE. codex is text-only here, claude is not.
    harness.load_env()
    ok("the QA job routes to a provider that can look at images",
       harness.provider_for("video_qa") == "claude",
       harness.provider_for("video_qa"))

    # An unrecognised flag used to fall straight through and re-run the whole
    # gate - three vision calls, about $1.60. `--help` did exactly that once.
    import subprocess
    for argv, want_rc, want_text in (
            (["--help"], 0, "Gate every generated"),
            ([], 2, "Gate every generated"),
            (["out/coach-party", "--nope"], 2, "unknown option")):
        r = subprocess.run([sys.executable, str(HERE / "qa_clips.py")] + argv,
                           capture_output=True, text=True, timeout=60,
                           cwd=str(HERE))
        ok(f"{argv or '(no args)'} stops early with rc={want_rc}",
           r.returncode == want_rc and want_text in r.stdout,
           f"rc={r.returncode} {r.stdout[:80]}")

    print(f"\n{sum(R)}/{len(R)} passed")
    return 0 if all(R) else 1


if __name__ == "__main__":
    sys.exit(main())
