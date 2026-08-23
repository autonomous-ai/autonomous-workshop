#!/usr/bin/env python3
"""Compare a run's phases against the historical baseline, phase by phase.

The postmortem answers "what went wrong in THIS run". This answers the question
that actually improves the pipeline: "is this phase behaving the way it always
behaves, or is today different?" A phase that costs 3x its median, or that has
hit its turn cap in 7 of the last 15 runs, is a tuning target — and neither fact
is visible from a single run.json.

Usage:
    ./phasecompare.py                 # newest run vs every earlier run
    ./phasecompare.py <slug>          # a specific run vs every OTHER run
    ./phasecompare.py --baseline      # just the baseline table, no current run
    ./phasecompare.py <slug> --journal logs/x.md   # also append a timestamped snapshot
"""
import json
import re
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"

# scalar run.json keys that are not phases
NOT_A_PHASE = {"slug", "mode", "trends", "prompt", "seed", "gate", "panel",
               "ship", "unjudged_lenses", "build_milestone", "build_aborted",
               "arbitrated", "escalated"}

# `max_turns` only started riding in run.json at commit 42e82d7. Every earlier
# run therefore has no recorded cap, and a naive `num_turns >= max_turns` test
# reports a flat 0/N cap-hit rate across the whole history — which reads as
# "nothing was ever starved" when starvation is exactly what we are hunting.
# These are the literal caps those runs actually ran under, read out of
# 42e82d7^:text2cad, so historical starvation stays measurable.
FALLBACK_CAPS = {
    "propose": 24, "judge": 10, "brief": 16, "draft": 45, "draft2": 45,
    "build": 60,          # --auto path ran BUILD_TURNS // 2, and every cycle is --auto
    "build2": 60, "build-likeness-check": 20,
    "lens-likeness": 20, "lens": 45, "repair": 50, "arbitration": 50,
}


def starved(name: str, e: dict):
    """(is_starved, known) — did this phase end because it ran out of turns?

    `subtype` says so outright when the run recorded it. Older runs did not, so
    they fall back to "errored AND at the cap it ran under" — the error flag is
    load-bearing: num_turns counts messages, not agent turns, so a healthy phase
    routinely reports MORE turns than its cap (judge-2 came back 19/10, clean).
    Without the is_error gate this test calls every busy phase starved.
    """
    sub = e.get("subtype")
    if sub:
        return sub == "error_max_turns", True
    if not e.get("is_error"):
        return False, True
    cap, _ = cap_for(name, e)
    nt = e.get("num_turns")
    if not (cap and nt):
        return False, False  # errored, but we cannot tell why
    return nt >= cap, True


def cap_for(name: str, e: dict):
    """(cap, inferred) — the recorded cap, else the literal this run ran under.

    An inferred cap is only trustworthy if the run respected it. The caps moved
    several times before they were recorded, so a phase reporting MORE turns
    than the literal we guessed simply ran under a different, older limit — and
    guessing again would invent starvation that never happened. Return None in
    that case so the row counts as "cap unknown" instead of a false positive.
    """
    if e.get("max_turns"):
        return e["max_turns"], False
    f = family(name)
    cap = FALLBACK_CAPS.get(f)
    if cap is None:
        for prefix, key in (("propose-", "propose"), ("judge-", "judge"), ("lens-", "lens")):
            if f.startswith(prefix):
                cap = FALLBACK_CAPS[key]
                break
    if cap is None:
        return None, False
    # The CLI reports the turn it was cut off ON, so a starved phase lands at
    # cap + 1 — verified across three phases with three different caps
    # (draft 46/45, repair 51/50, build 121/120 and 61/60, all is_error=True).
    # Anything ABOVE cap + 1 ran under a limit we guessed wrong, so drop it.
    if (e.get("num_turns") or 0) > cap + 1:
        return None, False
    return cap, True


def phases_of(run: dict) -> dict:
    """The phase entries only — a dict value carrying wall_s is a phase record."""
    return {k: v for k, v in run.items()
            if k not in NOT_A_PHASE and isinstance(v, dict) and "wall_s" in v}


def family(name: str) -> str:
    """Collapse retries and numbered attempts so a phase compares to itself.

    repair1/repair2/repair3 are the same phase with different budgets spent;
    lens-fidelity-retry is the fidelity lens running a second time. Without
    this, every run invents new phase names and nothing ever has a baseline.
    """
    # run_phase keeps earlier attempts as "<name>#2", "<name>#3" so their cost
    # is not lost; they are the same phase and belong in the same family.
    n = re.sub(r"#\d+$", "", name).removesuffix("-retry")
    if n.startswith("repair"):
        return "repair"
    if n.startswith("build-likeness-check"):
        return "build-likeness-check"
    return n


def load_runs() -> dict:
    runs = {}
    for rj in sorted(OUT.glob("*/run.json")):
        try:
            runs[rj.parent.name] = json.loads(rj.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
    return runs


def baseline(runs: dict, exclude: str = "") -> dict:
    """Per-phase-family stats across every run except `exclude`."""
    acc = {}
    for slug, run in runs.items():
        if slug == exclude:
            continue
        for name, e in phases_of(run).items():
            f = acc.setdefault(family(name), {"wall": [], "turns": [], "cost": [],
                                              "starved": 0, "errored": 0, "n": 0,
                                              "capped_cost": 0.0, "runs": set(),
                                              "by_model": {}})
            f["n"] += 1
            f["runs"].add(slug)
            # The same phase on opus and on sonnet are different animals — brief
            # runs ~13m on opus and ~2m on sonnet, so a pooled median compares a
            # run against a mixture it never belonged to. Keep a per-model split
            # and prefer it whenever there is enough of it to mean anything.
            m = f["by_model"].setdefault(e.get("model") or "?", {"wall": [], "turns": [], "cost": []})
            if not starved(name, e)[0]:
                for key, val in (("wall", e.get("wall_s")), ("turns", e.get("num_turns")),
                                 ("cost", e.get("cost_usd"))):
                    if val:
                        m[key].append(val)
            # A starved phase was CUT OFF, so its wall time and turn count
            # measure when we killed it, not how long the work takes. Today's
            # completed draft got flagged "2.0x SLOW" against a median built
            # from seven drafts that all died at the cap — comparing finished
            # work against corpses. Keep them out of the medians; the cap-hit
            # column still counts them.
            hit, _known = starved(name, e)
            if not hit:
                if e.get("wall_s"):
                    f["wall"].append(e["wall_s"])
                if e.get("cost_usd"):
                    f["cost"].append(e["cost_usd"])
            nt = e.get("num_turns")
            if nt and not hit:
                f["turns"].append(nt)
            if e.get("is_error"):
                f["errored"] += 1
            hit, known = starved(name, e)
            if known:
                f["known"] = f.get("known", 0) + 1
                if hit:
                    f["starved"] += 1
                    f["capped_cost"] += e.get("cost_usd") or 0
    return acc


def med(xs):
    return statistics.median(xs) if xs else None


def fmt(x, unit=""):
    if x is None:
        return "—"
    if unit == "$":
        return f"${x:,.2f}"
    if unit == "m":
        return f"{x / 60:.0f}m"
    return f"{x:,.0f}"


def ratio(cur, base):
    if not cur or not base:
        return ""
    r = cur / base
    if r >= 2.0:
        return f"  {r:.1f}x SLOW"
    if r <= 0.5:
        return f"  {r:.1f}x fast"
    return f"  {r:.1f}x"


def flags(name: str, e: dict) -> str:
    hit, known = starved(name, e)
    if hit:
        return "STARVED"
    if e.get("is_error"):
        return "CRASH" if known else "ERR (cause unknown)"
    return ""


def print_baseline(base: dict) -> None:
    print(f"{'phase':<24} {'runs':>5} {'med turns':>10} {'cap-hit':>8} {'err':>5} "
          f"{'med wall':>9} {'med cost':>9} {'burnt at cap':>13}")
    print("-" * 92)
    tot_capped = 0.0
    for name in sorted(base, key=lambda k: -base[k]["n"]):
        b = base[name]
        known = b.get("known", 0)
        starve = f"{b['starved']}/{known}" if known else "cap ?"
        tot_capped += b["capped_cost"]
        print(f"{name:<24} {len(b['runs']):>5} {fmt(med(b['turns'])):>10} "
              f"{starve:>8} {b['errored']:>5} {fmt(med(b['wall']), 'm'):>9} "
              f"{fmt(med(b['cost']), '$'):>9} "
              f"{(fmt(b['capped_cost'], '$') if b['capped_cost'] else '—'):>13}")
    print("-" * 92)
    print(f"{'spent on phases that hit their cap':<58} {fmt(tot_capped, '$'):>9}")
    print("\ncap-hit uses the recorded max_turns, falling back to the literal cap "
          "that run\nactually used (pre-42e82d7 runs did not record one).")


def compare(slug: str, run: dict, base: dict) -> list:
    """Rows for the current run against the baseline. Returns notable findings."""
    ph = phases_of(run)
    findings = []
    print(f"{'phase':<24} {'turns':>9} {'wall':>7} {'cost':>8}  "
          f"{"vs baseline (median)":<40} flag")
    print("-" * 92)
    total = 0.0
    for name, e in ph.items():
        b = base.get(family(name), {})
        nt = e.get("num_turns")
        mt, _ = cap_for(name, e)
        turns = f"{nt or '—'}/{mt or '—'}"
        cost = e.get("cost_usd") or 0
        total += cost
        # compare against the same model where the sample supports it
        same = (b.get("by_model") or {}).get(e.get("model") or "?", {})
        use, tag = (same, e.get("model", "").replace("claude-", "")) \
            if len(same.get("wall", [])) >= 3 else (b, "all")
        bw, bt = med(use.get("wall", [])), med(use.get("turns", []))
        vs = f"[{tag}] turns {fmt(bt)}, wall {fmt(bw, 'm')}{ratio(e.get('wall_s'), bw)}"
        fl = flags(name, e)
        print(f"{name:<24} {turns:>9} {fmt(e.get('wall_s'), 'm'):>7} "
              f"{fmt(cost, '$'):>8}  {vs:<40} {fl}")
        if "STARVED" in fl:
            findings.append(f"{name}: hit its {mt}-turn cap — budget failure, not a crash "
                            f"(historically {b.get('starved', 0)}/{b.get('n', 0)} runs)")
        elif "CRASH" in fl:
            findings.append(f"{name}: errored at {nt}/{mt} turns — a real crash, retry candidate")
        if e.get("wall_s") and bw and e["wall_s"] / bw >= 2.0:
            findings.append(f"{name}: {e['wall_s'] / bw:.1f}x slower than its median")
    print("-" * 92)
    print(f"{'TOTAL':<24} {'':>9} {'':>7} {fmt(total, '$'):>8}")

    gate, panel = run.get("gate") or {}, run.get("panel") or {}
    if gate:
        print(f"\ngate: {'PASS' if gate.get('pass') else 'FAIL'}"
              + (f" — {', '.join(gate.get('fails') or [])}" if gate.get("fails") else ""))
    if panel:
        print("panel: " + "  ".join(
            f"{k}:{'PASS' if str(v).startswith('PASS') else 'FAIL'}" for k, v in panel.items()))
    if "ship" in run:
        print(f"ship: {'YES' if run['ship'] else 'NO'}"
              + (f" — unjudged: {', '.join(run.get('unjudged_lenses') or [])}"
                 if run.get("unjudged_lenses") else ""))
    if run.get("seed"):
        print(f"seed: {run['seed']}")
    return findings


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    journal = None
    if "--journal" in sys.argv:
        journal = Path(sys.argv[sys.argv.index("--journal") + 1])

    runs = load_runs()
    if not runs:
        print("no runs in out/")
        return 1

    if "--baseline" in sys.argv:
        print("BASELINE — every run in out/\n")
        print_baseline(baseline(runs))
        return 0

    slug = args[0] if args else max(
        runs, key=lambda s: (OUT / s / "run.json").stat().st_mtime)
    run = runs[slug]
    base = baseline(runs, exclude=slug)

    header = (f"== {slug} vs baseline of {len(runs) - 1} earlier runs "
              f"— {time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(header + "\n")
    findings = compare(slug, run, base)
    if findings:
        print("\nNOTABLE")
        for f in findings:
            print(f"  - {f}")

    if journal:
        journal.parent.mkdir(parents=True, exist_ok=True)
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            print(header + "\n")
            findings = compare(slug, run, base)
            if findings:
                print("\nNOTABLE")
                for f in findings:
                    print(f"  - {f}")
        with journal.open("a", encoding="utf-8") as fh:
            fh.write("\n```\n" + buf.getvalue() + "```\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
