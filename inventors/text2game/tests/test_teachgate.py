#!/usr/bin/env python3
"""The teach floor, and the readers' prescription nobody was reading.

    python3 tests/test_teachgate.py

`teach` was a floor in DISCOVER only - scored on a one-sentence pitch, before a
rule existed - and `loop()` then exited on issue COUNTS, so a design read at
teach 4 exited exactly like one read at teach 9. Both games this pipeline has
shipped left phase 1 below the floor DISCOVER had enforced on them.
"""
import importlib.machinery
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
# the driver has no .py suffix, so import it by path
spec = importlib.util.spec_from_loader(
    "t2g", importlib.machinery.SourceFileLoader("t2g", str(HERE / "text2game")))
t2g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t2g)
import prompts  # noqa: E402


ROUNDS = [
    # the real three-round trace of `the-rounds`, 2026-08-20
    {"round": 1, "consistency_high": 0, "critic_high": 2, "referee_clean": True,
     "evaluate": {"teach": 8, "social": 2, "depth": 6}},
    {"round": 2, "consistency_high": 0, "critic_high": 3, "referee_clean": False,
     "evaluate": {"teach": 5, "social": 8, "depth": 7}},
    {"round": 3, "consistency_high": 2, "critic_high": 2, "referee_clean": False,
     "evaluate": {"teach": 4, "social": 9, "depth": 8}},
]


def snapshot_cases() -> list:
    """The loop keeps the last document; it has to SAY when that is the wrong one."""
    r = []

    def ok(name, cond, detail=""):
        print(f"  {'PASS' if cond else 'FAIL'}  {name}" + ("" if cond else f"  <- {detail}"))
        return cond

    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "gdd.md").write_text("round one rules\n", encoding="utf-8")
        (d / "components.json").write_text('[{"id":"a"}]', encoding="utf-8")
        t2g.snapshot_round(d, 1)
        (d / "gdd.md").write_text("round two rules, worse\n", encoding="utf-8")
        t2g.snapshot_round(d, 2)
        r.append(ok("each round's documents survive the next revise",
                    (d / "rounds" / "r1" / "gdd.md").read_text() == "round one rules\n"
                    and (d / "rounds" / "r2" / "gdd.md").read_text().startswith("round two")))
        r.append(ok("components.json is snapshotted too",
                    (d / "rounds" / "r1" / "components.json").is_file()))

        table = t2g.rounds_table(ROUNDS, 7, d)
        r.append(ok("the best round is named, and it is not the last",
                    "BEST: round 1" in table, table))
        r.append(ok("the table warns that disk holds a worse round",
                    "scored WORSE" in table and "round 3" in table, table))
        r.append(ok("gate counts are right: r1 misses only critic",
                    "r1  gates 3/4" in table and "r3  gates 0/4" in table, table))

        # a run that converges must NOT carry the warning
        good = [dict(ROUNDS[0], round=1),
                {"round": 2, "consistency_high": 0, "critic_high": 0,
                 "referee_clean": True, "evaluate": {"teach": 8, "social": 8}}]
        t2 = t2g.rounds_table(good, 7, d)
        r.append(ok("a converging run names the last round and adds no warning",
                    "BEST: round 2" in t2 and "scored WORSE" not in t2, t2))
        r.append(ok("an empty history returns nothing rather than a bare header",
                    t2g.rounds_table([], 7, d) == ""))

        # 2026-08-20: `precedent` printed BEST: round 3 and wrote
        # "best_round": 1. r1 and r3 both cleared 3 of 4 gates, the table
        # tie-broke on the evaluate sum and the verdict did not, and max()
        # returns the first maximum.
        tie = [{"round": 1, "consistency_high": 0, "critic_high": 3,
                "referee_clean": True, "evaluate": {"teach": 7, "depth": 6}},
               {"round": 2, "consistency_high": 0, "critic_high": 2,
                "referee_clean": False, "evaluate": {"teach": 7.5, "depth": 7}},
               {"round": 3, "consistency_high": 0, "critic_high": 1,
                "referee_clean": True, "evaluate": {"teach": 7, "depth": 8}}]
        b = t2g.best_round(tie, 7)
        tbl = t2g.rounds_table(tie, 7, d)
        r.append(ok("a gate tie breaks on the evaluate sum, not on round order",
                    b["round"] == 3, b.get("round")))
        r.append(ok("the printed table and best_round() cannot disagree",
                    f"BEST: round {b['round']}" in tbl, tbl))
    return r


def main() -> int:
    r = []

    # ---- below_floor ----------------------------------------------------
    for scores, want, why in (
            ({"teach": 4}, True,  "keep-the-light-relay's real score"),
            ({"teach": 6}, True,  "overcommit's real score"),
            ({"teach": 7}, False, "exactly the floor passes"),
            ({"teach": 8}, False, "above the floor"),
            ({}, False, "evaluate produced nothing - a broken checker, not a bad design"),
            (None, False, "no scores at all must not block the loop"),
            ({"depth": 2}, False, "other axes are not the floor"),
            ({"teach": 6.5}, True, "medians can be fractional")):
        got = t2g.below_floor(scores, 7)
        print(f"  {'PASS' if got == want else 'FAIL'}  below_floor({scores}) -> {got}  # {why}")
        r.append(got == want)

    # ---- one_change: the prose the median threw away --------------------
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "evaluate_r1_1.json").write_text(json.dumps(
            {"weakest": "teach", "one_change": "delete the double watches"}))
        (d / "evaluate_r1_2.json").write_text(json.dumps(
            {"weakest": "teach", "one_change": "delete the double watches"}))
        (d / "evaluate_r1_3.json").write_text(json.dumps(
            {"weakest": "elegance", "one_change": "merge the two dials"}))
        (d / "evaluate_r1_4.json").write_text("{ not json")
        got = t2g.one_change(d)
        ok = ("delete the double watches" in got and "merge the two dials" in got
              and got.count("delete the double watches") == 1)
        print(f"  {'PASS' if ok else 'FAIL'}  one_change dedupes and survives bad JSON")
        r.append(ok)
        ok = len(got.splitlines()) <= 3
        print(f"  {'PASS' if ok else 'FAIL'}  one_change caps at 3 lines for a telegram")
        r.append(ok)

    with tempfile.TemporaryDirectory() as td:
        got = t2g.one_change(Path(td))
        ok = "no one_change" in got
        print(f"  {'PASS' if ok else 'FAIL'}  no files -> a sentence, never an empty alarm")
        r.append(ok)

    # ---- the reviser must actually be handed the file -------------------
    s = prompts.revise(Path("/x"), 2)
    for probe in ("/x/evaluate.json", "evaluate_r2_*.json", "one_change",
                  "weakest", "spread"):
        ok = probe in s
        print(f"  {'PASS' if ok else 'FAIL'}  revise prompt names {probe!r}")
        r.append(ok)

    print("the todo prompt matches the real measuring CLI")

    def measure_contract():
        """The prompt hard-codes the switches; this catches it going stale.

        `precedent` 2026-08-20: the prompt named --gaps and nothing else, and
        todo.md came back citing ten switches that do not exist.
        """
        import re as _re
        import subprocess
        cli = Path("/root/text2cad/skills/cadcode/scripts/measure")
        if not cli.exists():
            return True, "measure CLI not installed - skipped"
        out = subprocess.run([sys.executable, str(cli), "--help"],
                             capture_output=True, text=True, timeout=60).stdout
        usage = out.split("\n", 1)[0]
        real = set(_re.findall(r"--[a-z-]+", usage)) - {"--help"}
        text = prompts.todo(HERE / "out")
        # ONLY the usage lines. The prose around them deliberately names the
        # ten switches a previous todo.md invented, as counter-examples.
        usage_lines = [ln for ln in text.splitlines()
                       if ln.strip().startswith("scripts/measure")]
        named = set(_re.findall(r"--[a-z-]+", " ".join(usage_lines)))
        missing, invented = real - named, named - real
        return (not missing and not invented,
                f"real={sorted(real)} missing={sorted(missing)} "
                f"invented={sorted(invented)}")
    _ok, _why = measure_contract()
    print(f"  {'PASS' if _ok else 'FAIL'}  the todo prompt names every real "
          f"switch and no invented one" + ("" if _ok else f"  <- {_why}"))
    r.append(_ok)

    # Every path the build prompt tells a bounded session to run must exist.
    # A moved file turns into "the tool was unavailable" inside a session that
    # cannot ask anyone, and the turns are gone.
    # Read the source, not a rendered prompt: build_group() needs a real run
    # directory and this check is about the literals, not about any one run.
    src = (HERE / "prompts.py").read_text(encoding="utf-8")
    for path in ("/root/text2cad/skills/cadcode/scripts/measure",
                 "/root/text2cad/gate.py",
                 "/root/text2cad/.venv/bin/python"):
        named = path in src
        exists = Path(path).exists()
        good = named and exists
        print(f"  {'PASS' if good else 'FAIL'}  build prompt names a real path: "
              f"{path}" + ("" if good else f"  <- named={named} exists={exists}"))
        r.append(good)

    # A repair session that re-exports only what it touched leaves older STLs
    # behind main.py, and the gate condemns the whole run on a timestamp.
    rt = prompts.repair_group(HERE / "out" / "precedent", "P", "issues") \
        if (HERE / "out" / "precedent").is_dir() else ""
    for name, needle in (
        ("repair is told to re-export everything, not just what it touched",
         "RE-EXPORT EVERYTHING"),
        ("repair is given the compile command", "scripts/cad"),
        ("repair is given the measure command", "--gaps"),
        ("repair is told scripts/gate does not exist", "not executables"),
    ):
        cond = needle in rt
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        r.append(cond)

    print("the referee knows what a campaign is")

    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "gdd.md").write_text("# G\n## Turn structure\nplayers take turns.\n",
                                  encoding="utf-8")
        plain = prompts.referee(d, 3)
        (d / "gdd.md").write_text("# G\n## Turn structure\nx\n"
                                  "## Legacy\na tab snaps off.\n", encoding="utf-8")
        camp = prompts.referee(d, 3)
        for name, cond, detail in (
            ("a game with no ## Legacy gets no campaign clause",
             "THIS IS A CAMPAIGN" not in plain, plain[-200:]),
            ("a game with ## Legacy is told one game IS the campaign",
             "THIS IS A CAMPAIGN" in camp, ""),
            ("and is told to count the supply to the last session",
             "components.json actually cover setup" in camp, ""),
            ("a supply shortfall is a MISSING INFO finding",
             "MISSING INFO finding" in camp, ""),
        ):
            print(f"  {'PASS' if cond else 'FAIL'}  {name}"
                  + ("" if cond else f"  <- {detail}"))
            r.append(cond)

    print("round snapshots")
    r.extend(snapshot_cases())

    # `ok` in this file is local to the nested case helpers, not to main().
    def chk(name, cond, detail=""):
        print(f"  {'PASS' if cond else 'FAIL'}  {name}"
              + ("" if cond else f"  <- {detail}"))
        return cond

    # --- the best round has to actually reach the disk -----------------------
    # coach-party 2026-08-20: r1 was 1,239 words with 1 machine high, r3 was
    # 1,989 with 3, the table printed "BEST: round 1", and phase 2 then built
    # from round 3. The note was accurate and nothing acted on it.
    def restore_swaps_a_worse_last_round():
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "rounds" / "r1").mkdir(parents=True)
            (d / "rounds" / "r1" / "gdd.md").write_text("short rules", encoding="utf-8")
            (d / "rounds" / "r1" / "components.json").write_text("[1]", encoding="utf-8")
            (d / "gdd.md").write_text("long rules", encoding="utf-8")
            (d / "components.json").write_text("[3]", encoding="utf-8")
            log = [{"round": 1, "consistency_high": 0, "critic_high": 1,
                    "referee_clean": True},
                   {"round": 3, "consistency_high": 1, "critic_high": 2,
                    "referee_clean": True}]
            note = t2g.restore_round(d, 1, log, 7)
            return (bool(note)
                    and (d / "gdd.md").read_text(encoding="utf-8") == "short rules"
                    and (d / "rounds" / "r3-discarded" / "gdd.md").read_text(
                        encoding="utf-8") == "long rules"), note
    r.append(chk("a last round with MORE machine highs is swapped out",
                *restore_swaps_a_worse_last_round()))

    def restore_leaves_an_equal_last_round():
        # Later revisions carry earlier fixes; do not lose them to a wobble in
        # three models' prose scores.
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "rounds" / "r1").mkdir(parents=True)
            (d / "rounds" / "r1" / "gdd.md").write_text("a", encoding="utf-8")
            (d / "rounds" / "r1" / "components.json").write_text("[1]", encoding="utf-8")
            (d / "gdd.md").write_text("b", encoding="utf-8")
            (d / "components.json").write_text("[3]", encoding="utf-8")
            log = [{"round": 1, "consistency_high": 0, "critic_high": 1,
                    "referee_clean": True},
                   {"round": 3, "consistency_high": 0, "critic_high": 1,
                    "referee_clean": True}]
            note = t2g.restore_round(d, 1, log, 7)
            return (note == ""
                    and (d / "gdd.md").read_text(encoding="utf-8") == "b"), note
    r.append(chk("an equal last round is left alone",
                *restore_leaves_an_equal_last_round()))

    def restore_refuses_a_partial_snapshot():
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "rounds" / "r1").mkdir(parents=True)
            (d / "rounds" / "r1" / "gdd.md").write_text("a", encoding="utf-8")
            (d / "gdd.md").write_text("b", encoding="utf-8")
            (d / "components.json").write_text("[3]", encoding="utf-8")
            log = [{"round": 1, "consistency_high": 0, "critic_high": 0,
                    "referee_clean": True},
                   {"round": 3, "consistency_high": 2, "critic_high": 0,
                    "referee_clean": True}]
            note = t2g.restore_round(d, 1, log, 7)
            # half a swap is a gdd that does not match its components
            return (note == ""
                    and (d / "gdd.md").read_text(encoding="utf-8") == "b"), note
    r.append(chk("a snapshot missing components.json is not half-restored",
                *restore_refuses_a_partial_snapshot()))

    r.append(chk("a dirty referee counts as a machine high",
                t2g.machine_highs({"consistency_high": 0, "critic_high": 0,
                                   "referee_clean": False}) == 1))

    # 2026-08-21, drop-in: exit 1 for "1910 words over budget" while the
    # RESTORED gdd on disk was 1222 - the verdict described the discarded
    # round. The restore path must re-measure the deterministic half and may
    # then exit clean.
    src = (HERE / "text2game").read_text(encoding="utf-8")
    r.append(chk("restore re-runs consistency on the files that ship",
                 "consistency_high_after_restore" in src
                 and src.index("consistency.check", src.index("restore_round("))
                 > 0))
    r.append(chk("a restore that clears every gate exits clean",
                 '"clean_via_restore"' in src
                 and "gates_of(best, teach_min)[1:]" in src))

    print(f"\n{sum(r)}/{len(r)} passed")
    return 0 if all(r) else 1


if __name__ == "__main__":
    sys.exit(main())
