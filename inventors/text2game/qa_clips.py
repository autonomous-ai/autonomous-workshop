#!/usr/bin/env python3
"""Gate every generated how-to clip against the parts and against the rule.

    ./qa_clips.py out/<slug>              # judge, report, change nothing
    ./qa_clips.py out/<slug> --regen      # and re-roll each FAIL once

Until 2026-08-21 there was no gate on the video at all. A clip came off the
gateway, somebody looked at a frame, and it shipped. Pulling four frames out of
coach-party beat 1 afterwards found the coach turning from a closed box into an
open cage, more than the five visitors the rules spill, pawns growing through
the clip, and pieces settling where nothing could roll to.

Shape of the loop is the content pipeline's image QA, which has been doing this
for months: judge the artifact against its reference, regenerate ONCE with the
judge's own words as feedback, then stop and flag rather than burn the budget.

The rule each beat is meant to show comes from howto_beats.json:

    {"b1": "Exactly 5 visitors spill ...", "b2": "...", "b3": "..."}

falling back to howto.json's caption. A judge with no rule can only check the
parts, so it says so instead of pretending it checked the action.

Kill switch: VIDEO_QA=off.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness  # noqa: E402
import prompts  # noqa: E402

RENDER_PY = os.environ.get("RENDER_PY") or harness.text2cad_py()
GEN = harness.text2cad_dir() / "gen_howto_video.py"
CHECKS = ("same_parts", "same_count", "same_size", "possible_places",
          "right_action")


def rules_for(out_dir: Path) -> dict:
    f = out_dir / "howto_beats.json"
    if f.is_file():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    spec = out_dir / "howto.json"
    if spec.is_file():
        try:
            cap = json.loads(spec.read_text(encoding="utf-8")).get("caption", "")
            if cap:
                return {"*": cap}
        except json.JSONDecodeError:
            pass
    return {}


def build_sheet(clip: Path, ref: Path) -> Path:
    """Frames + reference into one image, in the interpreter that has PIL."""
    r = subprocess.run([RENDER_PY, str(HERE / "video_qa.py"), str(clip),
                        str(ref), "-n", "5"],
                       capture_output=True, text=True, timeout=600)
    dst = clip.with_name(f"{clip.stem}_qa.png")
    if not dst.is_file():
        raise SystemExit(f"sheet failed for {clip.name}: "
                         f"{(r.stdout + r.stderr)[-300:]}")
    return dst


def judge(out_dir: Path, sheet: Path, rule: str, run_log: dict) -> dict:
    verdict_f = sheet.with_suffix(".json")
    if verdict_f.exists():
        verdict_f.unlink()
    harness.run_phase(f"video_qa-{sheet.stem}",
                      prompts.video_qa(out_dir, sheet.name, rule),
                      out_dir, 30, run_log)
    if not verdict_f.is_file():
        return {"verdict": "FAIL", "issues": ["the judge wrote no verdict"],
                "fix": ""}
    try:
        return json.loads(verdict_f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {"verdict": "FAIL", "issues": [f"unreadable verdict: {e}"],
                "fix": ""}


def failed(v: dict) -> bool:
    """A clip fails on the verdict OR on any single check being false.

    Both, because a judge that writes PASS next to `same_count: false` has
    contradicted itself and the checks are the part that is specific.
    """
    return (str(v.get("verdict", "")).upper() != "PASS"
            or any(v.get(k) is False for k in CHECKS))


def regen(out_dir: Path, beat: str, fix: str) -> bool:
    """Re-roll one clip with the judge's fix appended, reusing its frame.

    The i2i still is not what went wrong - the motion is - and re-rolling it
    would change the object between beats for no reason. gen_howto_video.py
    takes --reuse-frame precisely for this.
    """
    frame = out_dir / f"howto_{beat}_frame.png"
    spec_f = out_dir / "howto.json"
    if not (frame.is_file() and spec_f.is_file() and GEN.exists()):
        return False
    spec = json.loads(spec_f.read_text(encoding="utf-8"))
    spec["out"] = f"howto_{beat}.mp4"
    spec["video_prompt"] = (spec.get("video_prompt", "").rstrip()
                            + "\n\nTHE LAST ATTEMPT WAS REJECTED. " + fix)
    spec_f.write_text(json.dumps(spec, indent=1), encoding="utf-8")
    url = subprocess.run(
        [RENDER_PY, "-c",
         f"import sys;sys.path.insert(0,'{harness.text2cad_dir()}');"
         "import importlib.machinery as m,importlib.util as u;"
         f"l=m.SourceFileLoader('g','{GEN}');"
         "s=u.spec_from_loader('g',l);o=u.module_from_spec(s);l.exec_module(o);"
         f"from pathlib import Path;print(o.upload_cdn(Path('{frame}')))"],
        capture_output=True, text=True, timeout=300)
    m = re.search(r"https?://\S+", url.stdout)
    if not m:
        print(f"  [{beat}] regen: could not upload the frame", flush=True)
        return False
    r = subprocess.run([str(GEN), out_dir.name, "--dir", str(out_dir),
                        "--reuse-frame", m.group(0)],
                       capture_output=True, text=True, timeout=1800)
    return "saved" in (r.stdout or "")


KNOWN_FLAGS = {"--regen"}


def main() -> int:
    args = sys.argv[1:]
    if not args or any(a in ("-h", "--help") for a in args):
        print(__doc__)
        return 0 if args else 2
    # An unrecognised flag used to fall through and re-run the whole gate,
    # which is three vision calls and about $1.60. `--help` did exactly that.
    unknown = [a for a in args if a.startswith("-") and a not in KNOWN_FLAGS]
    if unknown:
        print(f"unknown option(s): {' '.join(unknown)}\n")
        print(__doc__)
        return 2
    harness.load_env()
    if os.environ.get("VIDEO_QA", "").lower() == "off":
        print("VIDEO_QA=off - skipping the gate")
        return 0
    positional = [a for a in args if not a.startswith("-")]
    if not positional:
        print("no run directory given\n")
        print(__doc__)
        return 2
    out_dir = Path(positional[0]).resolve()
    do_regen = "--regen" in args
    rules, run_log, rows = rules_for(out_dir), {}, []

    clips = sorted(out_dir.glob("howto_b*.mp4"))
    if not clips:
        print(f"no howto_b*.mp4 in {out_dir}")
        return 1

    for clip in clips:
        beat = clip.stem.replace("howto_", "")
        ref = out_dir / "renders" / f"beat_{beat}.png"
        if not ref.is_file():
            ref = out_dir / "renders" / "staged.png"
        rule = rules.get(beat) or rules.get("*") or (
            "NO RULE RECORDED for this beat - judge the PARTS only and set "
            "right_action to true, saying in issues that you could not check "
            "the action.")
        v = judge(out_dir, build_sheet(clip, ref), rule, run_log)
        bad = failed(v)
        if bad and do_regen and v.get("fix"):
            print(f"  [{beat}] FAIL - re-rolling once with the judge's fix",
                  flush=True)
            if regen(out_dir, beat, v["fix"]):
                v = judge(out_dir, build_sheet(clip, ref), rule, run_log)
                v["regenerated"] = True
                bad = failed(v)
        rows.append((beat, v, bad))

    print("\nVIDEO QA")
    for beat, v, bad in rows:
        marks = " ".join(f"{k.split('_')[-1]}"
                         f"{'ok' if v.get(k) else 'NO'}" for k in CHECKS)
        print(f"  {beat}  {'FAIL' if bad else 'pass'}  {marks}"
              + ("  (re-rolled)" if v.get("regenerated") else ""))
        for i in (v.get("issues") or [])[:3]:
            print(f"        - {i}")
    n_bad = sum(1 for _, _, b in rows if b)
    (out_dir / "video_qa.json").write_text(
        json.dumps({"clips": {b: v for b, v, _ in rows}, "failed": n_bad},
                   indent=2), encoding="utf-8")
    if n_bad:
        harness.telegram(f"text2game {out_dir.name}: video QA failed on "
                         f"{n_bad}/{len(rows)} clip(s) - "
                         + "; ".join(f"{b}: {(v.get('issues') or ['?'])[0]}"
                                     for b, v, bad in rows if bad)[:600])
    return 1 if n_bad else 0


if __name__ == "__main__":
    sys.exit(main())
