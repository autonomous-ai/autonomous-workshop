#!/usr/bin/env python3
"""Fixtures for the phase 2/3 pure-Python core: scaffold, plates, storyboard, fit.

Every case is a failure the pipeline would otherwise only discover after
spending an hour of CAD or a plate of filament.

    python3 tests/test_phase23.py
"""
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import fit  # noqa: E402
import harness  # noqa: E402
import phase3  # noqa: E402
import plates  # noqa: E402
import scaffold  # noqa: E402
import storyboard  # noqa: E402

COMPS = [
    {"id": "plinth", "qty": 1, "role": "base", "class": "functional",
     "duty": "flat", "tolerance_mm": 0.3, "target_bbox_mm": [120, 120, 14],
     "mates_with": ["tower"]},
    {"id": "tower", "qty": 1, "role": "post", "class": "functional",
     "duty": "holds the disc", "tolerance_mm": 0.25,
     "target_bbox_mm": [52, 52, 88], "mates_with": ["plinth", "beam_disc"]},
    {"id": "beam_disc", "qty": 1, "role": "beam", "class": "functional",
     "duty": "snaps", "tolerance_mm": 0.2, "target_bbox_mm": [64, 64, 6],
     "mates_with": ["tower"]},
    {"id": "ship", "qty": 12, "role": "ship", "class": "functional",
     "duty": "falls through the port", "tolerance_mm": 0.4,
     "target_bbox_mm": [10, 10, 14], "mates_with": []},
]

GDD = """# G

## Turn structure

Phases run in this order.

**1. Watch.** The active keeper clicks `lamp` down past the 3 lugs of
`relay_socket`. Until it is seated, no component may be moved.

**2. Sweep.** Spend charge 1 click at a time, turning `winder_dial` back 1
detent per charge, rotating `beam_disc` 30 degrees.

**3. Relay.** Pass `lamp` to the keeper on the left.

## Action economy

Numbers here.

## Legacy

Snapping a facet off `beam_disc` removes 60 degrees of reach permanently.

## Edge cases

Ties.
"""

RESULTS = []


def ok(name, cond, detail=""):
    RESULTS.append(cond)
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + ("" if cond else f"  <- {detail}"))


def tmpdir(comps=None, gdd=None) -> Path:
    d = Path(tempfile.mkdtemp())
    (d / "components.json").write_text(json.dumps(COMPS if comps is None else comps),
                                       encoding="utf-8")
    (d / "gdd.md").write_text(GDD if gdd is None else gdd, encoding="utf-8")
    return d


def test_scaffold():
    d = tmpdir()
    written = scaffold.generate(d)
    ok("scaffold writes one stub per design", len(written) == 4, written)
    src = (d / "parts" / "tower.py").read_text(encoding="utf-8")
    ok("stub carries the contract numbers as constants",
       "TOL = 0.25" in src and "BBOX = (52, 52, 88)" in src, src[:200])
    ok("stub records mates", '"plinth"' in src and '"beam_disc"' in src)
    idx = json.loads((d / "parts_index.json").read_text(encoding="utf-8"))
    ok("parts_index covers every design", set(idx) == {c["id"] for c in COMPS})
    (d / "parts" / "tower.py").write_text("# a real build\n", encoding="utf-8")
    again = scaffold.generate(d)
    ok("rerun never clobbers a real build", "tower" not in again and
       (d / "parts" / "tower.py").read_text(encoding="utf-8") == "# a real build\n")


def test_plates():
    plan = plates.layout(COMPS, 256, 256)
    good = [p for p in plan if not p.get("error")]
    ok("every design placed", len(good) == len(plan), plan)
    ship = [p for p in good if p["designs"] == ["ship"]]
    ok("all 12 ships land on ONE plate",
       len(ship) == 1 and ship[0]["pieces"] == 12, ship)
    ok("no piece overhangs the bed",
       all(s["x"] + s["w"] <= 256 and s["y"] + s["h"] <= 256
           for p in good for s in p.get("slots", [])))
    ok("one design never shares a plate with another",
       all(len(p["designs"]) == 1 for p in good))
    huge = [dict(COMPS[0], id="mega", target_bbox_mm=[400, 400, 10])]
    bad = plates.layout(huge, 256, 256)
    ok("a part too big for the bed is reported, not silently dropped",
       bad[0].get("error") and "mega" in bad[0]["error"], bad)


def test_storyboard():
    d = tmpdir()
    sb = storyboard.build(d, 3)
    titles = [b["title"] for b in sb["beats"]]
    ok("beats come from Turn structure in order",
       titles[:2] == ["Watch", "Sweep"], titles)
    ok("the irreversible act is always the last beat",
       titles[-1] == "Legacy", titles)
    ok("beats carry the component ids they show",
       "lamp" in sb["beats"][0]["parts"], sb["beats"][0])
    ok("durations match the beat count", len(sb["durations"]) == len(sb["beats"]))
    d2 = tmpdir(gdd=GDD.replace("## Legacy", "## NoLegacy"))
    sb2 = storyboard.build(d2, 3)
    ok("a game with no Legacy section still produces beats",
       len(sb2["beats"]) >= 2, sb2["beats"])


def test_fit():
    comps = {c["id"]: c for c in COMPS}
    tight = {"pairs": [{"a": "tower_1", "b": "beam_disc_1", "gap_mm": 0.05,
                        "overlap_mm3": 0.0}]}
    codes = {i["code"] for i in fit.judge(tight, comps)}
    ok("a mate tighter than its contract fails", "too-tight" in codes, codes)

    over = {"pairs": [{"a": "tower_1", "b": "plinth_1", "gap_mm": None,
                       "overlap_mm3": 16.5}]}
    codes = {i["code"] for i in fit.judge(over, comps)}
    ok("interference above the fuzz floor fails", "interference" in codes, codes)

    fuzz = {"pairs": [{"a": "tower_1", "b": "plinth_1", "gap_mm": 0.3,
                       "overlap_mm3": 1.2}]}
    codes = {i["code"] for i in fit.judge(fuzz, comps)}
    ok("mating fuzz below 2mm3 is not an interference",
       "interference" not in codes, codes)

    loose = {"pairs": [{"a": "tower_1", "b": "beam_disc_1", "gap_mm": 1.4,
                        "overlap_mm3": 0.0}]}
    got = [i for i in fit.judge(loose, comps) if i["code"] == "too-loose"]
    ok("a sloppy mate warns but does not block",
       got and got[0]["severity"] == "warn", got)

    nonmate = {"pairs": [{"a": "ship_1", "b": "plinth_1", "gap_mm": 0.01,
                          "overlap_mm3": 0.0}]}
    codes = {i["code"] for i in fit.judge(nonmate, comps)}
    ok("parts that are not declared mates are not judged on clearance",
       "too-tight" not in codes, codes)


TODO_MD = """# build order

### Phase 1 - Cabin core
parts: `cabin`
exit criteria: bbox

### Phase 2 - Tower stack
parts: `tower`, `beam_disc`
exit criteria: gaps

### Phase 3 - Ships
parts: `ship`
exit criteria: drop test
"""


def test_gate_feedback():
    rep = {"parts": {"cabin.stl": {}, "beam_disc.stl": {}, "ship.stl": {}},
           "fails": ["beam_disc.stl: not watertight (2 bodies)",
                     "ship.stl: overhang 71% exceeds 60%"],
           "pass": False}
    bad = phase3.failing_parts(rep)
    ok("failing parts are read off the gate report",
       set(bad) == {"beam_disc", "ship"}, bad)

    clean = phase3.failing_parts({"parts": {"cabin.stl": {}}, "fails": [], "pass": True})
    ok("a passing gate names nobody", clean == [], clean)

    d = tmpdir()
    (d / "todo.md").write_text(TODO_MD, encoding="utf-8")
    owners = phase3.groups_owning(d, bad)
    ok("failing parts map back to the groups that built them",
       owners == [2, 3], owners)
    ok("a part in no group yields no owner",
       phase3.groups_owning(d, ["ghost"]) == [], "expected []")
    ok("no todo.md means no guess",
       phase3.groups_owning(Path(tempfile.mkdtemp()), bad) == [])


def test_model_routing():
    import os
    os.environ["BUILD_MODEL"] = "claude-opus-5"
    ok("a job name resolves to its configured model",
       harness.model_for("build") == "claude-opus-5", harness.model_for("build"))
    # This used to assert the BUG: run labels carry a hyphen, BUILD-G3_MODEL is
    # not a settable env name, and a caller passing the LABEL silently got
    # sonnet. It cost phase 2 and 3 their configured models once, and phase 1's
    # revise-r1/r2 a second time (run.json: sonnet, .env: opus). model_for now
    # normalises the label through job_of, so the two call sites that pass the
    # job name by hand are belt-and-braces rather than the only defence.
    ok("a hyphenated run label DOES pick up the job's model",
       harness.model_for("build-g3") == "claude-opus-5",
       harness.model_for("build-g3"))
    src = (HERE / "phase2.py").read_text(encoding="utf-8")
    ok("phase 2 passes the JOB name for the build model",
       'model=harness.model_for("build")' in src)
    ok("phase 2 passes the JOB name for the repair model",
       'model=harness.model_for("repair")' in src)


def main() -> int:
    for name, fn in (("scaffold", test_scaffold), ("plates", test_plates),
                     ("storyboard", test_storyboard), ("fit", test_fit),
                     ("gate feedback", test_gate_feedback),
                     ("model routing", test_model_routing)):
        print(f"{name}:")
        fn()
    # 2026-08-20 `precedent`: coherence returned 4/10 for "the gate and
    # evidence_hopper collapse into one continuous petrol-blue shell" and
    # "verdict_pan is difficult to separate from the charcoal bench". Both
    # pairs were given one hex by art_direction.md, and nothing looked until
    # every group had been built.
    import phase2 as _p2
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "art_direction.md").write_text(
            "## Palette\n"
            "| `bench_half` | `#343B40` | matte charcoal |\n"
            "| `verdict_pan` | `#343B40` | matte charcoal |\n"
            "| `gate` | `#1F5963` | matte petrol |\n", encoding="utf-8")
        (d / "components.json").write_text(json.dumps([
            {"id": "bench_half", "mates_with": ["verdict_pan", "bench_half"]},
            {"id": "verdict_pan", "mates_with": ["bench_half"]},
            {"id": "gate", "mates_with": ["bench_half"]},
        ]), encoding="utf-8")
        got = _p2.palette_collisions(d)
        pairs = {frozenset((a, b)) for a, b, _, _ in got}
        cases = [
            ("two mating parts sharing a hex are reported",
             frozenset(("bench_half", "verdict_pan")) in pairs),
            ("a part mating with a copy of ITSELF is not a collision",
             frozenset(("bench_half",)) not in pairs and len(got) == 1),
            ("mating parts with different hexes are not reported",
             frozenset(("gate", "bench_half")) not in pairs),
            ("a mating collision is labelled as mating",
             got and got[0][3] == "mates"),
        ]
        for name, cond in cases:
            print(f"  {'PASS' if cond else 'FAIL'}  {name}" + ("" if cond else f"  <- {got}"))
            RESULTS.append(cond)
        # coach-party 2026-08-20: `through_hut` and `bell_ratchet_church` never
        # touch, were given one hex on purpose to "bind the architecture", and
        # the lens returned 3/10 because two blue buildings are two blue
        # buildings in a photograph. mates_with is not what makes it a failure.
        (d / "art_direction.md").write_text(
            "## Palette\n"
            "| `through_hut` | `#183B56` | ink blue |\n"
            "| `bell_ratchet_church` | `#183B56` | ink blue |\n"
            "| `street_tile` | `#AEB8C2` | stone grey |\n", encoding="utf-8")
        (d / "components.json").write_text(json.dumps([
            {"id": "through_hut", "mates_with": ["street_tile"]},
            {"id": "bell_ratchet_church", "mates_with": ["street_tile"]},
            {"id": "street_tile", "mates_with": ["through_hut"]},
        ]), encoding="utf-8")
        far = _p2.palette_collisions(d)
        for name, cond in (
                ("two NON-touching parts sharing a hex are reported too",
                 {frozenset((a, b)) for a, b, _, _ in far}
                 == {frozenset(("through_hut", "bell_ratchet_church"))}),
                ("and are labelled as seen together, not mating",
                 bool(far) and far[0][3] == "seen together"),
                ("no art_direction.md yields nothing",
                 _p2.palette_collisions(Path(td) / "nope") == []),):
            print(f"  {'PASS' if cond else 'FAIL'}  {name}")
            RESULTS.append(cond)

    # art_direction picked one hex per id and had never been shown which ids
    # touch, then argued in its own doc that repetition was deliberate. The
    # lens returned 4/10 for the pairs that collapsed. Both were arguing about
    # pairs neither had seen.
    import prompts as _pr
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "gdd.md").write_text("# G\n", encoding="utf-8")
        (d / "components.json").write_text(json.dumps([
            {"id": "bench_half", "mates_with": ["verdict_pan", "bench_half"]},
            {"id": "verdict_pan", "mates_with": ["bench_half"]},
        ]), encoding="utf-8")
        first = _pr.art_direction(d)
        ok("art_direction is shown which different parts touch",
           "bench_half <-> verdict_pan" in first, first[:200])
        ok("a part mating with a copy of itself is not listed",
           "bench_half <-> bench_half" not in first)
        ok("no previous verdict means no feedback block",
           "PREVIOUS PALETTE" not in first)

        (d / "lens_coherence.md").write_text(
            "VERDICT: 4/10\nthe verdict_pan is difficult to separate from the "
            "charcoal bench\n", encoding="utf-8")
        again = _pr.art_direction(d)
        ok("a rerun is handed the verdict it failed on",
           "PREVIOUS PALETTE" in again and "4/10" in again)
        ok("and is told to fix it rather than re-argue it",
           "Do not re-argue it" in again)

    print("storyboard beats + slice numbers")
    TURNS = """# G

## Turn structure

Each game has 4 rounds, each with these 3 phases.

%s

## Win/lose

x
"""
    INSIDE = ("**1. Coach spill.** The `coach_dispenser` opens.\n\n"
              "**2. Village work.** Players spend a `villager_pawn`.\n\n"
              "**3. Bell.** Advance the `bell_ratchet_church`.\n")
    OUTSIDE = ("1. **Coach spill.** The `coach_dispenser` opens.\n\n"
               "2. **Village work.** Players spend a `villager_pawn`.\n\n"
               "3. **Bell.** Advance the `bell_ratchet_church`.\n")
    for label, body in (("number inside the bold", INSIDE),
                        ("number outside the bold", OUTSIDE)):
        got = [b["title"] for b in storyboard.turn_beats(TURNS % body)]
        ok(f"turn beats parse with the {label}",
           got == ["Coach spill", "Village work", "Bell"], got)

    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        # No `## Legacy` section: the slot reserved for the irreversible beat
        # has nothing to put in it, and used to swallow a real turn phase.
        (d / "gdd.md").write_text(TURNS % OUTSIDE, encoding="utf-8")
        sb = storyboard.build(d, 3)
        ok("a game with no Legacy section still gets all 3 beats",
           [b["title"] for b in sb["beats"]] == ["Coach spill", "Village work", "Bell"],
           [b["title"] for b in sb["beats"]])
        ok("beats carry the parts the camera must show",
           sb["beats"][0]["parts"] == ["coach_dispenser"], sb["beats"][0]["parts"])

        # A print kit for a PRINTING pipeline has to carry what the box costs.
        (d / "components.json").write_text("[]", encoding="utf-8")
        (d / "slice_report.json").write_text(json.dumps({
            "total_grams": 1111.9, "total_print_time": "96h42m",
            "spool_1kg_pct": 111.2, "failed": [{"part": "coach_dispenser"}],
            "profile": "/root/printspecs/petg.ini",
            "slicer": "/usr/bin/prusa-slicer"}), encoding="utf-8")
        k = phase3.kit(d, [], [])
        ok("the kit reports measured filament and print time",
           "1111.9g" in k and "96h42m" in k and "111.2%" in k)
        ok("a part that would not slice is named in the kit",
           "DID NOT SLICE" in k and "coach_dispenser" in k)
        (d / "slice_report.json").unlink()
        ok("no slice report just omits the section, it does not crash",
           "What the whole box costs" not in phase3.kit(d, [], []))

    print(f"\n{sum(RESULTS)}/{len(RESULTS)} passed")
    return 0 if all(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
