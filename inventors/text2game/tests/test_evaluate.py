#!/usr/bin/env python3
"""The design-score trend that loop() steers on.

    python3 tests/test_evaluate.py

The scores themselves are an LLM's opinion of a document and are not worth
much alone. The DELTA is what the loop could not see before: issue counts fall
whether the design improved or the reviewer simply tired. Everything below is
about the delta being right, and about a missing or malformed evaluate.json
costing a signal rather than the run.
"""
import importlib.machinery
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import prompts  # noqa: E402

# the driver has no .py suffix, so spec_from_file_location cannot guess a
# loader for it and returns None - name the loader explicitly
spec = importlib.util.spec_from_loader(
    "t2g", importlib.machinery.SourceFileLoader("t2g", str(HERE / "text2game")))
t2g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t2g)


def ok(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + ("" if cond else f"  <- {detail}"))
    return bool(cond)


def scores(**kw):
    base = dict.fromkeys(prompts.DIMENSIONS, 5)
    base.update(kw)
    return base


def write_eval(d: Path, obj):
    (d / "evaluate.json").write_text(json.dumps(obj), encoding="utf-8")


def main() -> int:
    r = []

    print("evaluation() - reading what the phase wrote")
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        r.append(ok("no file -> empty, not a crash", t2g.evaluation(d) == {}))

        write_eval(d, {"round": 1, "scores": scores(teach=8)})
        got = t2g.evaluation(d)
        r.append(ok("scores are read", got.get("teach") == 8, got))
        r.append(ok("all seven dimensions", len(got) == 7, got))

        (d / "evaluate.json").write_text("{not json", encoding="utf-8")
        r.append(ok("malformed json costs a signal, not the run",
                    t2g.evaluation(d) == {}))

        # A model that invents a dimension must not widen the vocabulary, and a
        # string where a number belongs must not reach the arithmetic.
        write_eval(d, {"scores": dict(scores(), vibes=9, depth="high")})
        got = t2g.evaluation(d)
        r.append(ok("an invented dimension is dropped", "vibes" not in got, got))
        r.append(ok("a non-numeric score is dropped", "depth" not in got, got))

    print("\ntrend() - the direction, which is the whole point")
    total, per = t2g.trend([])
    r.append(ok("no history -> no trend", total is None))
    total, per = t2g.trend([scores()])
    r.append(ok("one round -> no trend yet", total is None))

    total, per = t2g.trend([scores(depth=5, teach=5), scores(depth=7, teach=6)])
    r.append(ok("improvement is positive", total == 3, (total, per))) 
    r.append(ok("per-dimension deltas", per["depth"] == 2 and per["teach"] == 1, per))

    total, per = t2g.trend([scores(elegance=8), scores(elegance=4)])
    r.append(ok("a revise that hurts reads negative", total == -4, (total, per)))

    total, per = t2g.trend([scores(), {}])
    r.append(ok("a round that produced nothing -> no trend", total is None))

    # A dimension the later round dropped must not be counted as a fall to zero.
    total, per = t2g.trend([scores(), {"depth": 6}])
    r.append(ok("only shared dimensions are compared", total == 1, (total, per)))

    print("\nevaluate_round - median of REPS reads, and the disagreement")
    import os
    os.environ["EVALUATE_REPS"] = "3"
    calls = []

    def fake_phase(name, prompt, out_dir, turns, run_log, **kw):
        """Stand in for the agent: write the file the prompt asked for."""
        dest = prompt.split("WRITE ")[1].split()[0].rsplit("/", 1)[-1]
        calls.append(dest)
        (Path(out_dir) / dest).write_text(json.dumps(
            {"scores": FAKE[len(calls) - 1]}), encoding="utf-8")
        return ""

    real = t2g.harness.run_phase
    t2g.harness.run_phase = fake_phase
    try:
        # the real measurement that motivated this: social 2/4/7, teach 4/5/6
        FAKE = [scores(social=2, teach=4, depth=7),
                scores(social=4, teach=5, depth=7),
                scores(social=7, teach=6, depth=6)]
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            med, spread = t2g.evaluate_round(d, 1, {})
            r.append(ok("three reads were run", len(calls) == 3, calls))
            r.append(ok("replicates do not clobber each other",
                        len(set(calls)) == 3, calls))
            r.append(ok("median, not the first read", med["social"] == 4, med))
            r.append(ok("median of teach", med["teach"] == 5, med))
            r.append(ok("spread is kept", spread["social"] == 5, spread))
            r.append(ok("an agreed dimension has no spread",
                        spread["tension"] == 0, spread))
            # evaluate.json is the artifact everything downstream reads
            saved = json.loads((d / "evaluate.json").read_text())
            r.append(ok("saved scores are the median",
                        saved["scores"]["social"] == 4, saved["scores"]))
            r.append(ok("every raw read is kept", len(saved["runs"]) == 3))
            r.append(ok("evaluation() reads the median",
                        t2g.evaluation(d)["social"] == 4))

        # a replicate that writes nothing must cost a read, not the round
        calls.clear()
        FAKE = [scores(depth=6), scores(depth=8), scores(depth=8)]
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)

            def flaky(name, prompt, out_dir, turns, run_log, **kw):
                dest = prompt.split("WRITE ")[1].split()[0].rsplit("/", 1)[-1]
                calls.append(dest)
                if len(calls) == 1:
                    return ""            # died without writing
                (Path(out_dir) / dest).write_text(json.dumps(
                    {"scores": FAKE[len(calls) - 1]}), encoding="utf-8")
                return ""

            t2g.harness.run_phase = flaky
            med, spread = t2g.evaluate_round(d, 2, {})
            r.append(ok("a dead replicate costs one read, not the round",
                        med.get("depth") == 8, med))
            r.append(ok("reps records what actually landed",
                        json.loads((d / "evaluate.json").read_text())["reps"] == 2))
    finally:
        t2g.harness.run_phase = real

    print("\nbriefing - the phase 1 alert a human actually reads")
    DISCOVER = """# Discover panel - 6 candidates, 3 judges

| candidate | lane | parts | novelty | desire | buildable | craft | teach | resonance | score | votes | mechanism |
|---|---|---|---|---|---|---|---|---|---|---|---|
| overcommit | legacy | 7 | 8 | 6 | 7 | 8 | 6 | 7 | 34 | 3 | tipping tray |
| storm-share | family | 7 | 7 | 6 | 8 | 6 | 8 | 5 | 33 | 3 | sleeved pledge |
| blind-bone-dig | coop | 7 | 8 | 7 | 7 | 6 | 6 | 4 | 30 | 3 | touch-ID draft |

WINNER: overcommit

A crew feeds a shared tray more work than it can hold.
Name: Overcommit
Box face: Feed the machine more than it can hold, and live with what breaks.
First look: the tipping tray, already loaded and already leaning.
Mechanism: blind-hopper draft into a tipping tray - 7 parts.
Why nobody has this: a slot you cannot earn back needs a one-way printed wedge.

PROMPT: build it
"""
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "discover.md").write_text(DISCOVER, encoding="utf-8")
        (d / "gdd.md").write_text("word " * 1496, encoding="utf-8")
        v = {"referee_clean": True, "consistency_high": 0, "critic_high": 2,
             "evaluate": scores(teach=6), "evaluate_spread": {"social": 4}}
        b = t2g.briefing(d, "overcommit", v, [{"qty": 4}, {"qty": 40}])
        # The column mapping is the whole risk here: reading one column left
        # still produces plausible numbers, so it has to be pinned to values
        # checked against the table above by hand. Since 2026-08-20 the columns
        # are addressed by HEADER NAME, which is what makes that class of bug
        # impossible rather than merely tested for.
        r.append(ok("winner's score is the objective pick_winner ranked on",
                    "score 34" in b, b))
        r.append(ok("winner's teach is teach, not craft",
                    "score 34, teach 6, resonance 7" in b, b))
        r.append(ok("a rival's numbers are its own",
                    "storm-share (lane family): 33, teach 8, resonance 5" in b, b))
        r.append(ok("the name and the box line lead the briefing",
                    b.index("Box face:") < b.index("Co che:"), b[:400]))
        r.append(ok("the object the game is sold on is named",
                    "First look: the tipping tray" in b, b[:400]))
        r.append(ok("the pitch is included", "shared tray" in b))
        r.append(ok("why nobody has it is included", "one-way printed wedge" in b))
        r.append(ok("rules length is reported", "1496 tu" in b, b[-300:]))
        r.append(ok("parts are counted", "2 thiet ke, 44 manh" in b, b[-300:]))
        r.append(ok("reader disagreement is surfaced", "social" in b.split("bat dong")[-1]))
        r.append(ok("it says what happens next", "PHASE 2" in b))

    # keep-the-light-relay and the two games after it were picked before the
    # table had a `score` column. Their discover.md still has to brief.
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        old = DISCOVER.replace(
            "| candidate | lane | parts | novelty | desire | buildable | craft |"
            " teach | resonance | score | votes | mechanism |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|\n"
            "| overcommit | legacy | 7 | 8 | 6 | 7 | 8 | 6 | 7 | 34 | 3 | tipping tray |\n"
            "| storm-share | family | 7 | 7 | 6 | 8 | 6 | 8 | 5 | 33 | 3 | sleeved pledge |\n"
            "| blind-bone-dig | coop | 7 | 8 | 7 | 7 | 6 | 6 | 4 | 30 | 3 | touch-ID draft |",
            "| candidate | lane | parts | novelty | desire | buildable | craft |"
            " teach | votes | mechanism |\n"
            "|---|---|---|---|---|---|---|---|---|---|\n"
            "| overcommit | legacy | 7 | 8 | 6 | 7 | 8 | 6 | 3 | tipping tray |\n"
            "| storm-share | family | 7 | 7 | 6 | 8 | 6 | 8 | 3 | sleeved pledge |")
        (d / "discover.md").write_text(old, encoding="utf-8")
        (d / "gdd.md").write_text("word " * 10, encoding="utf-8")
        b = t2g.briefing(d, "overcommit", {"referee_clean": True}, [])
        # 6+7+8+6, and resonance reads as 0 because that table has no such column
        r.append(ok("a discover.md written before `score` still briefs",
                    "score 27" in b, b))

    print("\nprompts.evaluate")
    with tempfile.TemporaryDirectory() as t:
        p = prompts.evaluate(Path(t), 2)
        r.append(ok("names every dimension",
                    all(f'"{d}"' in p for d in prompts.DIMENSIONS)))
        r.append(ok("carries the round", "round 2" in p))
        r.append(ok("writes where it is told",
                    "evaluate_r2_1.json" in prompts.evaluate(Path(t), 2,
                                                            "evaluate_r2_1.json")))
        # It scores the document; the pitch is what DISCOVER already scored, and
        # re-reading it here would just re-litigate the panel's decision.
        r.append(ok("does not reopen the seed", "seed.md" not in p))
        r.append(ok("demands evidence, not a number", "evidence" in p))

        # `one_change` is an INSTRUCTION the reviser is told to apply, so a
        # reader blind to the medium can burn a whole round. Measured on
        # coach-party r1: "add a one-card walkthrough", in a pipeline with no
        # cards. Scoring stays blind; only the prescription is constrained.
        r.append(ok("the prescription knows there are no cards",
                    "no cards" in p and "FDM" in p and "engraved text" in p))
        r.append(ok("scoring is still blind to the taste guide",
                    "Do not read the taste" in p and "seed.md" not in p))
        r.append(ok("the constraint sits AFTER the scoring rubric",
                    p.index("SCORE WHAT IS THERE") < p.index("IS AN INSTRUCTION")))
        # The one that cost two rounds: the rubric scores teach 4 as "a
        # reference stays open", and four of six reads then prescribed exactly
        # that as the fix for teach.
        r.append(ok("a player aid is named as the wrong fix for teach",
                    "player aid" in p and "REMOVING RULES" in p))
        rev = prompts.revise(Path(t), 2)
        r.append(ok("the reviser may refuse an unprintable one_change",
                    "cannot print" in rev))

    print(f"\n{sum(r)}/{len(r)} passed")
    return 0 if all(r) else 1


if __name__ == "__main__":
    sys.exit(main())
