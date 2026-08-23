#!/usr/bin/env python3
"""Fixtures for the DISCOVER selection logic.

pick_winner() is plain Python precisely so it can be pinned down here: it is
the one place in the pipeline that decides what the day builds, and it had no
tests at all until 2026-08-20.

    python3 tests/test_discover.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import discover  # noqa: E402

# nov des bui cra tea res - alpha beats beta on raw score and loses to it once
# the catalogue says `legacy` has just won twice.
ALPHA = (8, 8, 8, 8, 8, 8)      # objective 40
BETA = (6, 7, 8, 7, 8, 7)       # objective 37


def cand(slug, name="Alpha", lane_fields=""):
    return (f"CANDIDATE: {slug}\n"
            f"NAME: {name}\n"
            f"PITCH: players do a thing and it is tense\n"
            f"BOX-FACE: one line a stranger reads in two seconds\n"
            f"FIRST-LOOK: the drum, and it is the only thing you see\n"
            f"GENRE: legacy\nPLAYERS: 2-4\nTIME: 45\n"
            f"MECHANISM: a named loop\nPARTS: 7\n"
            f"NEAREST: none — https://example.com/nothing\n"
            f"WHY-NOBODY-HAS-THIS: nobody built it\n"
            f'SEED: trends/2026-08-20-wiki-top.md — "a thing people read"\n'
            f"PROMPT: build {slug}\n{lane_fields}\n")


def panel(d: Path, cands: dict, scores: dict):
    """cands: {lane: [slug...]}, scores: {slug: 6-tuple}."""
    for lane, slugs in cands.items():
        (d / f"cand_{lane}.md").write_text(
            "\n".join(cand(s, name=s.title()) for s in slugs), encoding="utf-8")
    for i in (1, 2, 3):
        lines = [f"EXISTS {s} no none" for s in scores]
        lines += [f"SCORE {s} " + " ".join(str(x) for x in v)
                  for s, v in scores.items()]
        (d / f"judge_{i}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def winner_of(d: Path) -> str:
    text = (d / "discover.md").read_text(encoding="utf-8")
    return text.split("WINNER:", 1)[1].split("\n", 1)[0].strip()


def run(name, fn) -> bool:
    try:
        ok, detail = fn()
    except Exception as e:                                    # noqa: BLE001
        ok, detail = False, f"{type(e).__name__}: {e}"
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  <- {detail}"))
    return ok


def with_panel(shelf, cands, scores):
    """Run one panel against a given catalogue, in a throwaway directory."""
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        discover.CATALOG = d / "catalog.json"
        if shelf:
            discover.CATALOG.write_text(json.dumps(shelf), encoding="utf-8")
        panel(d, cands, scores)
        discover.pick_winner(d)
        return winner_of(d), (d / "discover.md").read_text(encoding="utf-8"), \
            json.loads(discover.CATALOG.read_text(encoding="utf-8"))


def main() -> int:
    # These cases assert exact objective totals ("rich (41)"), so they have to
    # run at the documented default weight and not at whatever the operator put
    # in .env for today's run - harness.load_env() has already read it by now.
    os.environ["TEACH_WEIGHT"] = "1"
    os.environ.update(NOVELTY_MIN="5", BUILDABLE_MIN="7", CRAFT="6", TEACH_MIN="7")
    real_catalog = discover.CATALOG
    r = []

    print("score parsing")

    def five_axis_scores():
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / "judge_1.md").write_text("SCORE old-game 8 7 7 6 9\n", encoding="utf-8")
            got = discover.parse_scores(d)["old-game"][0]
            return got == (8, 7, 7, 6, 9, 5), f"got {got}"
    r.append(run("a judge_*.md written before `resonance` reads as neutral 5",
                 five_axis_scores))

    def six_axis_scores():
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / "judge_1.md").write_text("SCORE new-game 8 7 7 6 9 3\n", encoding="utf-8")
            got = discover.parse_scores(d)["new-game"][0]
            return got == (8, 7, 7, 6, 9, 3), f"got {got}"
    r.append(run("six axes parse", six_axis_scores))

    print("\nthe catalogue")

    def streak():
        shelf = [{"slug": "a", "lane": "legacy"}, {"slug": "b", "lane": "family"},
                 {"slug": "c", "lane": "legacy"}, {"slug": "d", "lane": "legacy"}]
        return (discover.lane_streak("legacy", shelf) == 2
                and discover.lane_streak("family", shelf) == 0
                and discover.lane_streak("coop", shelf) == 0,
                f"legacy={discover.lane_streak('legacy', shelf)} "
                f"family={discover.lane_streak('family', shelf)}")
    r.append(run("streak counts only the most recent run of one lane", streak))

    def upsert():
        with tempfile.TemporaryDirectory() as t:
            discover.CATALOG = Path(t) / "catalog.json"
            discover.catalog_add("g", "legacy", "m")
            discover.catalog_add("g", "legacy", "m2")
            items = discover.catalog()
            return (len(items) == 1 and items[0]["mechanism"] == "m2",
                    f"got {items}")
    r.append(run("re-running a pick does not add the same game twice", upsert))

    print("\nlane rotation")

    def no_shelf():
        win, _, cat = with_panel([], {"legacy": ["alpha"], "family": ["beta"]},
                                 {"alpha": ALPHA, "beta": BETA})
        return (win == "alpha" and cat == [{"slug": "alpha", "lane": "legacy",
                                            "mechanism": "a named loop"}],
                f"winner {win}, catalogue {cat}")
    r.append(run("empty shelf: the best objective wins and is recorded", no_shelf))

    def one_repeat():
        win, _, _ = with_panel([{"slug": "x", "lane": "legacy"}],
                               {"legacy": ["alpha"], "family": ["beta"]},
                               {"alpha": ALPHA, "beta": BETA})
        return win == "alpha", f"winner {win}"
    r.append(run("one repeat costs 2 and a better candidate still wins its lane",
                 one_repeat))

    def two_repeats():
        win, text, _ = with_panel([{"slug": "x", "lane": "legacy"},
                                   {"slug": "y", "lane": "legacy"}],
                                  {"legacy": ["alpha"], "family": ["beta"]},
                                  {"alpha": ALPHA, "beta": BETA})
        return (win == "beta" and "−4" in text,
                f"winner {win}, penalty shown: {'−4' in text}")
    r.append(run("a third pick from the same lane loses to a weaker other lane",
                 two_repeats))

    def capped():
        """Four legacy games deep, the penalty is still 4 - a thumb on the
        scale, not a ban a lane can never come back from."""
        _, text, _ = with_panel([{"slug": s, "lane": "legacy"} for s in "wxyz"],
                                {"legacy": ["alpha"], "family": ["beta"]},
                                {"alpha": ALPHA, "beta": BETA})
        return "−4" in text and "−8" not in text, text.split("SHELF")[0][-300:]
    r.append(run("the penalty stops growing after LANE_PENALTY_CAP repeats",
                 capped))

    def idempotent():
        """The winner must not be penalised for its own catalogue entry."""
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            discover.CATALOG = d / "catalog.json"
            discover.CATALOG.write_text(json.dumps(
                [{"slug": "x", "lane": "legacy"}]), encoding="utf-8")
            panel(d, {"legacy": ["alpha"], "family": ["beta"]},
                  {"alpha": ALPHA, "beta": BETA})
            first = (discover.pick_winner(d), winner_of(d))[1]
            second = (discover.pick_winner(d), winner_of(d))[1]
            return first == second == "alpha", f"{first} then {second}"
    r.append(run("running pick_winner twice picks the same game", idempotent))

    print("\nwhat the buyer receives")

    def box_face():
        _, text, _ = with_panel([], {"legacy": ["alpha"]}, {"alpha": ALPHA})
        return (all(k in text for k in ("Name:", "Box face:", "First look:")),
                "discover.md is missing a buyer-facing line")
    r.append(run("the winner's name and box face reach discover.md", box_face))

    def missing_face():
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            discover.CATALOG = d / "catalog.json"
            (d / "cand_legacy.md").write_text(
                "CANDIDATE: bare\nPITCH: p\nGENRE: legacy\nPARTS: 7\n"
                "MECHANISM: m\nPROMPT: build bare\n", encoding="utf-8")
            for i in (1, 2, 3):
                (d / f"judge_{i}.md").write_text(
                    "EXISTS bare no none\nSCORE bare 8 8 8 8 8 8\n", encoding="utf-8")
            discover.pick_winner(d)
            text = (d / "discover.md").read_text(encoding="utf-8")
            return ("NOT WRITTEN" in text, "a candidate with no box face was "
                    "recorded as though it had one")
    r.append(run("a candidate that skipped the box face says so out loud",
                 missing_face))

    print("\nreading the table by name")

    def by_header():
        _, text, _ = with_panel([], {"legacy": ["alpha"], "family": ["beta"]},
                                {"alpha": ALPHA, "beta": BETA})
        rows = discover.table_rows(text)
        row = discover.table_row(text, "alpha")
        return (len(rows) == 2 and row["teach"] == "8" and row["lane"] == "legacy"
                and row["resonance"] == "8",
                f"{len(rows)} rows, alpha={row}")
    r.append(run("every column is addressable by its header name", by_header))

    def digest():
        _, text, _ = with_panel([], {"legacy": ["alpha"]}, {"alpha": ALPHA})
        d = discover.discover_digest(text)
        return ("3 judges" in d["scores"] and "resonance 8" in d["scores"],
                f"scores line: {d['scores']}")
    r.append(run("the digest reports the judge count, not the teach score", digest))

    discover.CATALOG = real_catalog
    print("uncontested fields")

    # 2026-08-20, from the real panel: `nightwinder` won on 29, the LOWEST of
    # six, because it was the only candidate clearing every floor. Four rivals
    # died on buildable>=7 and one on craft>=7, so the medians and the
    # objective decided nothing - and pick_winner said so nowhere, because
    # `given_up` was empty at full strictness and the warn block was if/elif.
    def one_survivor_is_flagged():
        LONE = (9, 6, 7, 7, 7, 2)      # clears every floor, objective 29
        RICH = (8, 9, 5, 9, 9, 9)      # objective 41, dies on buildable 5
        _, text, _ = with_panel([], {"legacy": ["lone"], "family": ["rich"]},
                                {"lone": LONE, "rich": RICH})
        after = text.split("UNCONTESTED", 1)[-1]
        return ("⚠ UNCONTESTED" in text and "rich (41)" in after
                and "WINNER: lone" in text), text[-800:]
    r.append(run("a field of one is UNCONTESTED, and names who outscored it",
                 one_survivor_is_flagged))

    def real_contest_is_not_flagged():
        A = (8, 9, 8, 8, 8, 8)         # objective 41
        B = (8, 7, 8, 8, 8, 7)         # objective 38, also clears everything
        _, text, _ = with_panel([], {"legacy": ["a"], "family": ["b"]},
                                {"a": A, "b": B})
        return ("⚠ UNCONTESTED" not in text and "WINNER: a" in text), text[-400:]
    r.append(run("two survivors is a contest and carries no warning",
                 real_contest_is_not_flagged))

    def warnings_accumulate():
        # Nobody clears buildable>=7, so it is relaxed to 6 - and then exactly
        # one candidate clears, because the other is under the teach floor that
        # never moves. Both facts have to be reported, not just the first.
        THIN = (8, 8, 6, 8, 8, 8)
        DEAD = (8, 8, 6, 8, 4, 8)
        _, text, _ = with_panel([], {"legacy": ["thin"], "family": ["dead"]},
                                {"thin": THIN, "dead": DEAD})
        return ("⚠ FLOORS RELAXED" in text and "⚠ UNCONTESTED" in text), text[-800:]
    r.append(run("a relaxed floor AND a field of one are both reported",
                 warnings_accumulate))

    print("the proposers are told the bars")

    # The prompt used to say "exactly two requirements, nothing more" and then
    # pick_winner removed candidates on four more. A floor the proposer cannot
    # see is a floor that gets walked into.
    def floors_reach_the_prompt():
        os.environ.update(NOVELTY_MIN="5", BUILDABLE_MIN="7", CRAFT="7", TEACH_MIN="7")
        t = discover.propose_prompt("aim", HERE / "out", [])
        want = ["buildable >= 7", "teach >= 7", "craft >= 7", "novelty >= 5"]
        missing = [w for w in want if w not in t]
        stale = "exactly two requirements, nothing more" in t
        return (not missing and not stale), f"missing {missing}, stale={stale}"
    r.append(run("every scored floor is named in the propose prompt",
                 floors_reach_the_prompt))

    def floors_track_the_env():
        # A prompt that hard-codes the numbers is the same bug one layer down.
        os.environ.update(BUILDABLE_MIN="9", TEACH_MIN="8")
        t = discover.propose_prompt("aim", HERE / "out", [])
        os.environ.update(BUILDABLE_MIN="7", TEACH_MIN="7")
        return ("buildable >= 9" in t and "teach >= 8" in t
                and "buildable >= 7" not in t), "prompt did not follow the env"
    r.append(run("the floors in the prompt follow the env, not a literal",
                 floors_track_the_env))

    # --- RUN_TONE: the axis-less target ------------------------------------
    def tone_is_off_by_default():
        os.environ.pop("RUN_TONE", None)
        return (discover.tone_block() == ""
                and "THIS RUN'S TONE" not in discover.propose_prompt(
                    "aim", HERE / "out", [])), "unset RUN_TONE still emitted a block"
    r.append(run("no RUN_TONE means no block at all", tone_is_off_by_default))

    def tone_reaches_proposers_and_judges():
        os.environ["RUN_TONE"] = "FUNNY - people should laugh"
        pro = discover.propose_prompt("aim", HERE / "out", [])
        jud = discover.judge_prompt(1, HERE / "out")
        return ("FUNNY - people should laugh" in pro
                and "FUNNY - people should laugh" in jud), "tone did not reach both"
    r.append(run("the tone reaches BOTH the proposers and the judges",
                 tone_reaches_proposers_and_judges))

    def tone_relaxes_nothing():
        # The whole failure mode: a tone read as permission to miss a floor.
        t = discover.propose_prompt("aim", HERE / "out", [])
        return ("relaxes NOTHING" in t and "buildable >= " in t), "floors lost"
    r.append(run("a tone directive never relaxes a floor", tone_relaxes_nothing))

    def tone_travels_to_the_reviser():
        # DISCOVER picking a funny game is worthless if 1.4 sands it off.
        import prompts
        g = HERE / "out" / "precedent"
        ok = all("THIS RUN'S TONE" in f(g) for f in
                 (prompts.gdd, lambda d: prompts.revise(d, 2)))
        # ...and it must stay out of the build side, which runs on lessons.md.
        leak = any("THIS RUN'S TONE" in f for f in
                   (prompts.mechanism(g), prompts.critic(g),
                    prompts.build_group(g, "t", "b", 3)))
        return (ok and not leak), f"gdd/revise={ok} leaked_into_build={leak}"
    r.append(run("the tone travels to the GDD and the reviser, not to BUILD",
                 tone_travels_to_the_reviser))
    os.environ.pop("RUN_TONE", None)

    def teach_weight_default_is_historical():
        os.environ.pop("TEACH_WEIGHT", None)
        src = (HERE / "discover.py").read_text(encoding="utf-8")
        return ('os.environ.get("TEACH_WEIGHT", "1")' in src
                and "teach_w * tea" in src), "objective is not weight-driven"
    r.append(run("TEACH_WEIGHT defaults to 1 and multiplies teach in the objective",
                 teach_weight_default_is_historical))

    print("single genre (operator 2026-08-21: physical/dexterity only)")

    def one_genre_three_angles():
        return (set(discover.PROPOSE_LANES) == {"aim", "stack", "time"},
                f"lanes are {sorted(discover.PROPOSE_LANES)}")
    r.append(run("the three lanes are physical angles, not genres",
                 one_genre_three_angles))

    def law_rides_both_prompts():
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            p = discover.propose_prompt("aim", d, [])
            j = discover.judge_prompt(1, d)
            need = ("ONE CAMERA SHOT", "NO hidden information", "TWO mechanisms")
            return (all(n in p and n in j for n in need),
                    "the genre law is missing from a prompt")
    r.append(run("the genre law rides the proposer AND the judge",
                 law_rides_both_prompts))

    print(f"\n{sum(r)}/{len(r)} passed")
    return 0 if all(r) else 1


if __name__ == "__main__":
    sys.exit(main())
