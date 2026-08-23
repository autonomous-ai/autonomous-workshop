"""PHASE 3 - print. Gate, fit, plates, rulebook, video, kit.

Ends by handing a human a printed kit and a list of what to watch for. That is
not modesty: GameGrammar is right that no algorithm simulates four people at a
table, so the last gate is a physical playtest and the pipeline's job is to
arrive there with the open questions written down instead of buried.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import fit
import harness
import plates
import prompts
import slice_parts
import storyboard

HERE = Path(__file__).resolve().parent
TEXT2CAD = Path(os.environ.get("TEXT2CAD_DIR", "/root/text2cad"))


def failing_parts(gate_report: dict) -> list:
    """Which STLs the gate named. gate.py writes failures with the file in them."""
    names = list((gate_report.get("parts") or {}).keys())
    bad = []
    for fail in gate_report.get("fails") or []:
        text = fail if isinstance(fail, str) else json.dumps(fail)
        for n in names:
            stem = n.rsplit(".", 1)[0]
            if (n in text or stem in text) and stem not in bad:
                bad.append(stem)
    return bad


def groups_owning(out_dir: Path, parts: list) -> list:
    """Map failing parts back to the todo.md group numbers that built them."""
    md = out_dir / "todo.md"
    if not md.is_file() or not parts:
        return []
    blocks = re.findall(r"^###\s+(.+?)\s*$(.*?)(?=^###\s|\Z)",
                        md.read_text(encoding="utf-8"), re.M | re.S)
    owners = []
    for i, (_, body) in enumerate(blocks, 1):
        ids = set(re.findall(r"`([a-z0-9_]+)`", body))
        if ids & set(parts) and i not in owners:
            owners.append(i)
    return owners


def gate(out_dir: Path) -> dict:
    """text2cad's gate.py, unmodified - it already scores PARTS, not assemblies."""
    g = TEXT2CAD / "gate.py"
    if not g.exists():
        return {"pass": None, "error": f"gate.py not found at {g}"}
    r = subprocess.run([harness.text2cad_py(), str(g),
                        str(out_dir)] + (["--no-slice"] if os.environ.get(
                            "NO_SLICE") else []),
                       capture_output=True, text=True, timeout=3600,
                       env=harness.phase_env())
    lines = [ln for ln in ((r.stdout or "") + (r.stderr or "")).splitlines()
             if ln.strip()]
    # Not splitlines()[-1]. The render log did exactly that and swallowed the
    # one warning built to catch a 40-solids-grey palette; gate.py reports a
    # failed slice the same way, above its verdict line.
    for ln in lines[:-1]:
        if any(k in ln for k in ("WARNING", "Traceback", "slice", "SLICE")):
            print(f"  gate: {ln.strip()[:200]}", flush=True)
    print(lines[-1][:200] if lines else "gate: no output", flush=True)
    f = out_dir / "gate.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else \
        {"pass": False, "error": (r.stderr or r.stdout)[-300:]}


def open_questions(out_dir: Path) -> list:
    """What the automated gates waived. The playtest kit's real payload.

    A referee finding nobody fixed and a `medium` the reviser refused are the
    two places a rules bug survives to the table. They go on paper WITH the kit.
    """
    qs = []
    ref = out_dir / "referee.md"
    if ref.exists():
        body = ref.read_text(encoding="utf-8")
        m = re.search(r"^## Findings\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
        for kind, text in re.findall(r"^###\s*(\w[\w ]*)\s*$(.*?)(?=^###|\Z)",
                                     m.group(1) if m else "", re.M | re.S):
            qs.append({"from": "referee", "kind": kind.strip(),
                       "text": " ".join(text.split())[:240]})
    crit = out_dir / "critic.json"
    if crit.exists():
        try:
            for i in json.loads(crit.read_text(encoding="utf-8")):
                if i.get("severity") in ("medium", "low"):
                    qs.append({"from": "critic", "kind": i["severity"],
                               "text": f"{i.get('issue', '')} (fix suggested: "
                                       f"{i.get('fix', '')})"[:240]})
        except json.JSONDecodeError:
            pass
    fitf = out_dir / "fit.json"
    if fitf.exists():
        try:
            for i in json.loads(fitf.read_text(encoding="utf-8")):
                if i["severity"] == "warn":
                    qs.append({"from": "fit", "kind": i["code"], "text": i["message"]})
        except json.JSONDecodeError:
            pass
    return qs


def kit(out_dir: Path, plan: list, qs: list) -> str:
    comps = fit.contract(out_dir)
    lines = ["# Print kit", "", "## Plates, in print order", ""]
    for p in plan:
        if p.get("error"):
            lines.append(f"- **UNPLACEABLE** - {p['error']}")
            continue
        cid = p["designs"][0]
        c = comps.get(cid, {})
        lines.append(f"- **Plate {p['plate']}** - `{cid}` x{p['pieces']}  "
                     f"({c.get('target_bbox_mm')}mm, tol {c.get('tolerance_mm')}mm)")
    sr = out_dir / "slice_report.json"
    if sr.is_file():
        try:
            r = json.loads(sr.read_text(encoding="utf-8"))
            lines += ["", "## What the whole box costs to print", "",
                      f"Measured by {r.get('slicer')} over the real meshes with "
                      f"`{r.get('profile')}` - never estimated.", "",
                      f"- **{r.get('total_grams')}g** of PETG "
                      f"({r.get('spool_1kg_pct')}% of a 1kg spool)",
                      f"- **{r.get('total_print_time')}** of printing"]
            bad = [x.get("part") for x in (r.get("failed") or [])]
            if bad:
                lines.append(f"- **{len(bad)} part(s) DID NOT SLICE**: "
                             + ", ".join(f"`{b}`" for b in bad))
        except (json.JSONDecodeError, AttributeError):
            pass
    lines += ["", "## Assembly order", ""]
    # A part is assembled after everything it mates with that came earlier;
    # the mates_with graph already says this, so do not restate it by hand.
    done, order = set(), []
    for _ in range(len(comps) + 1):
        for cid, c in comps.items():
            if cid in done:
                continue
            if all(m in done for m in (c.get("mates_with") or []) if m in comps):
                order.append(cid)
                done.add(cid)
    for i, cid in enumerate(order, 1):
        m = comps[cid].get("mates_with") or []
        lines.append(f"{i}. `{cid}`" + (f" - mates with {', '.join(m)}" if m else ""))
    lines += ["", "## Watch for these at the table", "",
              "These were found by the automated checks and NOT fixed. They are",
              "the reason a physical playtest is the last gate.", ""]
    lines += [f"- **{q['from']}/{q['kind']}** - {q['text']}" for q in qs] or \
             ["- nothing waived; every finding was resolved"]
    # The `table` provenance slot (weight 4 in evidence.jsonl) reserved since
    # 2026-08-20 finally gets its source: a filled-in table_notes.md next to
    # this kit, harvested like any critic.json but outranking every one.
    sig = next((cid for cid, c in comps.items() if c.get("signature") is True),
               None)
    lines += ["", "## Table notes - the last gate", "",
              "Machines checked the documents; only four people can check the",
              "game. After the first night, write `table_notes.md` next to this",
              "kit - one `- symptom_id: what was seen` bullet per finding, ids",
              "from mechanisms.md. `./harvest.py` reads it at weight 4, above",
              "every check in this kit. Ask at least:", ""]
    if sig:
        lines.append(f"- did the `{sig}` move feel worth repeating, or did the "
                     f"table feel nothing? (`unsatisfying_action`)")
    lines += ["- did packing up take longer than a round? (`fiddly_reset`)",
              "- did anyone reopen the rules after turn 1? (`teach_overrun`)",
              "- was any piece homeless when the box closed? (`homeless_part`)"]
    return "\n".join(lines) + "\n"


def run(out_dir: Path, run_log: dict) -> dict:
    print("\n== PHASE 3: print", flush=True)
    print("[models] " + " ".join(harness.plan(j) for j in
          ("rulebook", "video_spec")), flush=True)
    report = {}

    report["gate"] = gate(out_dir)
    print(f"[gate] pass={report['gate'].get('pass')}", flush=True)
    if report["gate"].get("pass") is False:
        # Slicing unprintable geometry produces a print kit for parts that
        # cannot be printed - a worse outcome than stopping, because it looks
        # finished. Phase 3 never repairs geometry; it names what to rebuild.
        bad = failing_parts(report["gate"])
        owners = groups_owning(out_dir, bad)
        report["failing_parts"] = bad
        report["rebuild_groups"] = owners
        msg = (f"text2game {out_dir.name}: GATE FAIL on {', '.join(bad) or 'the assembly'}"
               f"\nrebuild group(s) {owners or '?'}:"
               f"\n  ./text2game --slug {out_dir.name} --phase 2"
               + (f" --groups {','.join(str(o) for o in owners)}" if owners else ""))
        print("\n" + msg, flush=True)
        harness.confirm(f"{out_dir.name}: GATE FAIL - the parts are not printable",
                        msg, "approve the rebuild command above, or ship without "
                        "those parts")
        (out_dir / "phase3.json").write_text(json.dumps(report, indent=2),
                                             encoding="utf-8")
        return report

    step = sorted(out_dir.glob("*.step")) + sorted(out_dir.glob("*.stp"))
    if step:
        rc = subprocess.run([sys.executable, str(HERE / "fit.py"), str(out_dir),
                             str(step[0])], capture_output=True, text=True,
                            timeout=1800, env=harness.phase_env())
        print(rc.stdout.strip()[-400:], flush=True)
        report["fit_ok"] = rc.returncode == 0
    else:
        report["fit_ok"] = None
        print("[fit] no STEP to measure", flush=True)

    comps = json.loads((out_dir / "components.json").read_text(encoding="utf-8"))
    comps = comps if isinstance(comps, list) else comps.get("components", [])
    plan = plates.layout(comps, float(os.environ.get("BED_X", "256")),
                         float(os.environ.get("BED_Y", "256")))
    (out_dir / "plates.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    report["plates"] = len([p for p in plan if not p.get("error")])
    report["unplaceable"] = [p["designs"][0] for p in plan if p.get("error")]
    print(f"[plates] {report['plates']} plates, "
          f"{len(report['unplaceable'])} unplaceable", flush=True)

    # slice_parts.py has existed, with 13 passing tests, and NOTHING CALLED IT.
    # Its own docstring says why it was written: "The pipeline promised
    # *.gcode and shipped none ... a run could report [gate] pass=True with no
    # gcode anywhere and nothing in the log looked wrong." gate.py only slices
    # when ORCASLICER_CLI is set and is written for OrcaSlicer's argument
    # shape; this box has PrusaSlicer, so the gate returns "sliced": null and
    # says nothing. A print kit with no filament weight and no print time is
    # not a print kit.
    #
    # Wrapped, because a missing slicer must never cost a run its product -
    # the numbers are the last thing added and the first thing to do without.
    report["slice"] = None
    try:
        report["slice"] = slice_parts.slice_all(out_dir)
    except SystemExit as e:
        print(f"[slice] SKIPPED: {e}", flush=True)
    except Exception as e:                       # noqa: BLE001
        print(f"[slice] FAILED: {type(e).__name__}: {e}", flush=True)

    harness.run_phase("rulebook", prompts.rulebook(out_dir), out_dir, 40, run_log)

    sb = storyboard.build(out_dir, 3)
    (out_dir / "storyboard.json").write_text(json.dumps(sb, indent=2), encoding="utf-8")
    if not sb["beats"]:
        msg = ("[storyboard] WARNING: no beats parsed from gdd.md "
               "'## Turn structure' - there will be NO how-to video. This is a "
               "parser miss, not a game with no turns.")
        print(msg, flush=True)
        harness.telegram(f"text2game {out_dir.name}: {msg}")
    else:
        print(f"[storyboard] beats: {[b['title'] for b in sb['beats']]}", flush=True)
    if (out_dir / "renders" / "assembled.png").exists():
        harness.run_phase("video_spec", prompts.video_spec(out_dir), out_dir, 25,
                          run_log)
        report["howto_spec"] = (out_dir / "howto.json").exists()
    else:
        # The relay's first video was directed at a concept image because no
        # render existed. Not again: no render, no video.
        print("[video] no assembled render - skipping, a how-to of parts that "
              "do not exist is the mistake this phase was written to avoid",
              flush=True)
        report["howto_spec"] = False

    qs = open_questions(out_dir)
    (out_dir / "print_kit.md").write_text(kit(out_dir, plan, qs), encoding="utf-8")
    report["open_questions"] = len(qs)
    (out_dir / "phase3.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Bank this run's lessons into the design vault - the write half of the
    # loop whose read half is the critic's vault leads. Event-driven because
    # this box runs no cron and no timers; deterministic (harvest rows ->
    # wiki nodes, zero LLM calls); and never worth killing a finished run
    # over. Kill switch: VAULT_INGEST=off.
    if os.environ.get("VAULT_INGEST", "").lower() != "off":
        ing = (Path(os.environ.get("GAMEVAULT", "/root/gamevault"))
               / "vault_ingest.py")
        try:
            if ing.is_file():
                r = subprocess.run([sys.executable, str(ing), str(out_dir)],
                                   capture_output=True, text=True, timeout=180)
                for ln in (r.stdout + r.stderr).strip().splitlines():
                    print(f"  [vault] {ln}", flush=True)
                report["vault_ingest"] = r.returncode == 0
            else:
                print(f"  WARNING: no vault ingester at {ing} - this run's "
                      f"lessons are not banked", flush=True)
        except Exception as e:                       # never kill a phase
            print(f"  WARNING: vault ingest failed ({type(e).__name__}: {e})",
                  flush=True)
    return report
