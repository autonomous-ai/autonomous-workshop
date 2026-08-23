#!/usr/bin/env python3
"""Per-cycle postmortem: turn run.json into something a human can act on.

    ./postmortem.py <slug>          write out/<slug>/postmortem.md + ledger row
    ./postmortem.py --all           backfill every run in out/
    ./postmortem.py --lessons       tally lessons.md by cause and status
    ./postmortem.py <slug> --telegram   also send the summary to the DM

run.json holds the raw truth (per-phase cost/turns/wall time, gate numbers,
lens verdicts) but nobody can read it after a 6-hour cycle and say WHERE the
money went or WHY the product failed. This renders that, and — more usefully —
attributes the failure to one of the same `cause` categories lessons.md uses,
so recurring causes become countable instead of anecdotal.

Everything here is derived deterministically from run.json + gate.json. No LLM
call, no API key, so it always runs — including on a cycle that died because
the key was exhausted.
"""
import json
import re
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
LEDGER = HERE / "CYCLES.md"

# Signals in gate fails / lens verdicts -> (cause, what to do about it). Order
# matters: the first match wins, so put the specific patterns first.
# Mirrors LENSES in text2cad. A panel is only meaningful if every lens actually
# returned a verdict — see `missing_lenses` below for why this list must exist.
LENSES = ["printability", "fidelity", "likeness", "sellability"]

CAUSE_RULES = [
    ("stale_stl", "discipline", "the STL was older than main.py — a repair ended without re-exporting"),
    ("not_watertight", "kernel", "OCCT emitted broken/sliver facets — look for two cut boundaries meeting"),
    ("bodies=", "kernel", "pieces did not fuse — overlap every union by >=1mm, or a fillet made phantom bodies"),
    ("bridge_span", "printability", "an unsupported internal ceiling — tent the cavity roof or add hidden ribs"),
    ("overhang", "printability", "too much unsupported material for unattended FDM"),
    ("slice", "printability", "the slicer refused it — usually the 160x160 usable-bed limit"),
    ("fit_check", "assembly", "a mock/interface check failed — verify the mock still matches params.py"),
    ("FAIL no output", "harness", "a reviewer agent CRASHED — no geometry cause, it needs a retry"),
    ("out of turns", "budget", "a phase hit its turn cap — it was starved, not wrong"),
    ("likeness", "fidelity", "the build does not read as the approved concept"),
    ("fidelity", "fidelity", "geometry drifted from brief.md features/dimensions"),
    ("sellability", "discover", "the product itself is not wanted — a selection problem, not a build one"),
    ("printability", "printability", "the printability lens rejected it"),
]


def money(run: dict) -> list:
    return [(k, v) for k, v in run.items()
            if isinstance(v, dict) and "cost_usd" in v]


def classify(fails: list) -> list:
    """Map every failure string to (cause, direction). Deduped, order kept."""
    hits, seen = [], set()
    for f in fails:
        for pat, cause, fix in CAUSE_RULES:
            if pat.lower() in str(f).lower():
                if (cause, fix) not in seen:
                    seen.add((cause, fix))
                    hits.append((cause, fix, str(f)))
                break
    return hits


def analyze(slug: str) -> dict:
    """Everything both the report and the ledger row are derived from.

    One function so a cycle can never be summarised two different ways.
    """
    run = json.loads((OUT / slug / "run.json").read_text(encoding="utf-8"))
    gate = run.get("gate") or {}
    panel = run.get("panel") or {}
    phases = money(run)

    # An is_error phase is either OUT OF TURNS (budget too small for the task —
    # raise the cap or narrow the job) or a real agent CRASH (retry). They need
    # opposite fixes, so never report them as one number. Runs from before
    # max_turns was logged cannot be told apart at all; say so rather than
    # guessing — a confident wrong label is worse than an honest unknown.
    capped = [k for k, v in phases if v.get("is_error") and v.get("max_turns")
              and (v.get("num_turns") or 0) >= v["max_turns"]]
    crashed = [k for k, v in phases if v.get("is_error") and v.get("max_turns")
               and k not in capped]
    unknown = [k for k, v in phases if v.get("is_error") and not v.get("max_turns")]

    gate_fails = list(gate.get("fails") or [])
    lens_fails = [f"lens:{k} {v}" for k, v in panel.items() if not str(v).startswith("PASS")]
    milestone = run.get("build_milestone")
    # The milestone counts as a signal even on a run that went on to ship: a
    # cycle can pass its gate while the mid-build likeness check was silently
    # useless, and that is exactly the kind of thing a green result hides.
    signals = gate_fails + lens_fails
    if milestone and str(milestone).startswith("FAIL"):
        signals.append(f"build-milestone likeness {milestone}")
    signals += [f"{k} out of turns" for k in capped]

    # An ABSENT lens verdict is not a passing one. `panel` lists only lenses
    # that RETURNED, so a jury that died leaves it empty — which naively reads
    # as "no failures" and calls an untested product clean (one-way-newsreel
    # shipped exactly that way: gate PASS, zero verdicts, no panel key).
    # The lens set grew over time (3 lenses, later 4), so compare against what
    # this run actually attempted rather than today's list, and separate the
    # two ways a verdict goes missing — they mean different things.
    attempted = {re.sub(r"#\\d+$", "", k)[len("lens-"):].removesuffix("-retry")
                 for k in run if k.startswith("lens-")}
    returned = set(panel)
    no_verdict = sorted(attempted - returned)          # ran, died, said nothing
    # Only blame a lens for not starting when the panel demonstrably broke down
    # mid-way. A run whose every attempted lens returned judged the product as
    # completely as its pipeline version could — older versions had three
    # lenses, and marking those short is just noise.
    never_started = sorted(set(LENSES) - attempted - returned) if no_verdict else []
    missing = no_verdict + never_started

    # Runs from the current pipeline record their own publish decision; trust
    # it rather than recomputing, so the report can never disagree with what
    # actually happened. `unjudged_lenses` is the pipeline's own accounting.
    if run.get("unjudged_lenses") is not None:
        never_started = [x for x in run["unjudged_lenses"] if x not in no_verdict]
        missing = no_verdict + never_started

    aborted = run.get("build_aborted")
    # A cycle that never reached the gate is INCOMPLETE, not FAILED — scratch
    # dirs and killed runs would otherwise read as product failures.
    result = ("ABORTED" if aborted else
              "SHIPPED" if run.get("ship") else
              "FAILED" if gate and (not gate.get("pass") or lens_fails) else
              "GATE PASS / NO PANEL" if gate and not attempted and not returned else
              "GATE PASS / UNJUDGED" if gate and missing else
              "SHIPPED" if gate else "INCOMPLETE")
    return {
        "run": run, "gate": gate, "panel": panel, "phases": phases,
        "capped": capped, "crashed": crashed, "unknown": unknown,
        "retries": [k for k, _ in phases if k.endswith("-retry")],
        "repairs": [k for k, _ in phases if k.startswith("repair")],
        "total": sum(v.get("cost_usd") or 0 for _, v in phases),
        "wall": sum(v.get("wall_s") or 0 for _, v in phases),
        "burned": sum(v.get("cost_usd") or 0 for k, v in phases
                      if v.get("is_error") or k.endswith("-retry")
                      or k.startswith("repair")),
        "gate_fails": gate_fails, "lens_fails": lens_fails,
        "milestone": milestone, "aborted": aborted, "missing_lenses": missing,
        "no_verdict": no_verdict, "never_started": never_started,
        "judged": sorted(returned),
        "causes": classify(signals), "result": result,
    }


def render(slug: str) -> str:
    a = analyze(slug)
    gate, phases, causes = a["gate"], a["phases"], a["causes"]
    capped, crashed, unknown = a["capped"], a["crashed"], a["unknown"]
    retries, repairs = a["retries"], a["repairs"]
    total, wall, burned = a["total"], a["wall"], a["burned"]
    gate_fails, lens_fails = a["gate_fails"], a["lens_fails"]
    milestone, aborted = a["milestone"], a["aborted"]
    L = []
    L.append(f"# Postmortem — {slug}")
    L.append("")
    if a["run"].get("seed"):
        L.append(f"**Seed:** {a['run']['seed']}")
        L.append("")
    L.append(f"**Result:** {a['result']}"
             f" · **cost ${total:.2f}** · **{wall / 3600:.1f}h** · "
             f"{len(phases)} phases")
    if aborted:
        L.append("")
        L.append(f"**Run aborted:** {aborted}")
    L.append("")

    # 1. WHERE THE MONEY WENT — the question run.json never answers directly.
    L.append("## Where the money went")
    L.append("")
    L.append("| phase | $ | min | turns | |")
    L.append("|---|---:|---:|---:|---|")
    for k, v in sorted(phases, key=lambda kv: -(kv[1].get("cost_usd") or 0)):
        flag = ("OUT OF TURNS" if k in capped else "CRASHED" if k in crashed
                else "errored (cap not logged)" if k in unknown
                else "retry" if k.endswith("-retry")
                else "repair" if k.startswith("repair") else "")
        turns = f"{v.get('num_turns') or 0}" + (f"/{v['max_turns']}" if v.get("max_turns") else "")
        L.append(f"| {k} | {v.get('cost_usd') or 0:.2f} | {(v.get('wall_s') or 0) / 60:.0f} "
                 f"| {turns} | {flag} |")
    L.append(f"| **total** | **{total:.2f}** | **{wall / 60:.0f}** | | |")
    L.append("")
    if burned:
        pct = burned / total * 100 if total else 0
        L.append(f"**${burned:.2f} ({pct:.0f}%) went to rework** — "
                 f"{len(repairs)} repair round(s), {len(retries)} retry, "
                 f"{len(crashed) + len(unknown)} error(s), {len(capped)} out of turns.")
        L.append("")
        if capped:
            L.append(f"- **out of turns:** {', '.join(capped)} — these did not fail, "
                     "they ran out of room. Raise the cap or cut the task down; "
                     "retrying at the same budget just buys the same wall.")
        if crashed:
            L.append(f"- **crashed:** {', '.join(crashed)} — died below the turn cap, "
                     "so this is a transient agent failure, not the design.")
        if unknown:
            L.append(f"- **errored:** {', '.join(unknown)} — this run predates "
                     "`max_turns` logging, so starved-vs-crashed cannot be told apart "
                     "here. Compare `num_turns` against the cap in text2cad by hand.")
        L.append("")

    # 2. WHAT BROKE, AND WHAT KIND OF PROBLEM IT IS
    L.append("## What broke")
    L.append("")
    if milestone:
        L.append(f"- mid-build likeness milestone: `{milestone}`")
    for f in gate_fails:
        L.append(f"- gate: `{f}`")
    for f in lens_fails:
        L.append(f"- {f}")
    if not (milestone or gate_fails or lens_fails or a["missing_lenses"]):
        L.append("- nothing — gate and every lens passed on the first pass.")
    L.append("")

    if a["missing_lenses"]:
        L.append("## Never judged")
        L.append("")
        if a["no_verdict"]:
            L.append(f"- **ran but returned nothing:** {', '.join(a['no_verdict'])} "
                     "— the lens started and died, so it was paid for and produced "
                     "no opinion.")
        if a["never_started"]:
            L.append(f"- **never started:** {', '.join(a['never_started'])} — the run "
                     "ended before these were reached.")
        if a["judged"]:
            L.append(f"- judged normally: {', '.join(a['judged'])}")
        L.append("")
        L.append("**The deterministic gate (mesh, slicer, fit-checks) is the only thing "
                 "that cleared this build.** Nothing checked whether it reads as the "
                 "approved concept or whether anyone would want it — an empty panel is "
                 "an UNTESTED product, not a clean one.")
        L.append("")

    if causes:
        L.append("## Root cause and direction")
        L.append("")
        for cause, fix, sig in causes:
            L.append(f"- **{cause}** — {fix}  \n  <sub>from `{sig[:110]}`</sub>")
        L.append("")
        heads = {c for c, _, _ in causes}
        advice = []
        if "harness" in heads:
            advice.append("A crash is not a product problem: it cost money without "
                          "testing the design. If this cause repeats, fix the orchestrator, "
                          "never the geometry.")
        if "kernel" in heads:
            advice.append("Kernel failures are the known OCCT weak spot (fillet blends, "
                          "boundary-on-boundary slivers). Check `blocks/BLOCKS.md` for a "
                          "golden block before hand-building the shape again.")
        if "brief" in heads or "fidelity" in heads:
            advice.append("This traces back upstream: the brief or the concept, not the "
                          "build. Repair rounds cannot fix a spec that contradicts itself — "
                          "tighten BRIEF instead of buying more repair tiers.")
        if "printability" in heads:
            advice.append("Printability rejections are cheap to prevent at brief time: "
                          "envelope <=160x160, no flat sealed ceiling wider than the safe "
                          "bridge span.")
        if "budget" in heads:
            advice.append("A starved phase is the cheapest failure to fix and the "
                          "easiest to misread as a bad build — check the turn cap "
                          "before touching anything the phase produced.")
        if "discover" in heads:
            advice.append("The product was the problem, not the CAD. Money spent past "
                          "DISCOVER on a candidate nobody wants is the most expensive kind "
                          "of waste in this pipeline.")
        if len(repairs) >= 2:
            advice.append(f"{len(repairs)} repair rounds on one part: whatever recurred here "
                          "should GRADUATE into a gate check or a golden block, not another "
                          "lessons.md paragraph.")
        if advice:
            L.append("**What to do about it**")
            L.append("")
            for a in advice:
                L.append(f"- {a}")
            L.append("")

    # 3. THE PRODUCT ITSELF — what actually came out, if anything did.
    if gate:
        L.append("## The product")
        L.append("")
        bbox = gate.get("bbox_mm") or []
        L.append(f"- {gate.get('n_parts') or '?'} printed parts, "
                 f"bbox {'x'.join(str(int(b)) for b in bbox) if bbox else '?'} mm")
        if gate.get("print_min"):
            L.append(f"- print time {gate['print_min'] / 60:.1f} h"
                     + (f", {gate['volume_mm3'] / 1000:.0f} cm3 of filament"
                        if gate.get("volume_mm3") else ""))
        L.append(f"- watertight: {gate.get('watertight')}, bodies: {gate.get('bodies')}, "
                 f"overhang {gate.get('overhang_pct')}%, bridge span {gate.get('bridge_span_mm')}mm")
        L.append("")
    L.append(f"<sub>generated from `out/{slug}/run.json` by postmortem.py</sub>")
    return "\n".join(L) + "\n"


def ledger_row(slug: str) -> str:
    a = analyze(slug)
    cause = ", ".join(sorted({c for c, _, _ in a["causes"]})) or "—"
    return (f"| {slug} | {a['result']} | ${a['total']:.2f} | "
            f"{a['gate'].get('n_parts') or '—'} | {len(a['repairs'])} | {cause} | "
            f"[postmortem](out/{slug}/postmortem.md) |")


def rebuild_ledger() -> None:
    rows = []
    for d in sorted(OUT.iterdir()):
        # `_`-prefixed dirs are scratch/harness tests, not product cycles.
        if d.name.startswith("_"):
            continue
        if (d / "postmortem.md").is_file() and (d / "run.json").is_file():
            try:
                rows.append(ledger_row(d.name))
            except Exception as e:  # noqa: BLE001 — a malformed run must not kill the ledger
                rows.append(f"| {d.name} | (unreadable run.json: {e}) | | | | | |")
    LEDGER.write_text(
        "# text2cad cycle ledger\n\n"
        "One row per build cycle, newest last. `cause` uses the same vocabulary as\n"
        "lessons.md — a cause that keeps showing up here is where the pipeline is\n"
        "actually losing money.\n\n"
        "Regenerate with `./postmortem.py --all`. The linked postmortems live under\n"
        "`out/`, which is gitignored, so they exist only on the box that ran the\n"
        "cycle — this table is the part that travels.\n\n"
        "| product | result | cost | parts | repairs | cause | |\n"
        "|---|---|---:|---:|---:|---|---|\n" + "\n".join(rows) + "\n",
        encoding="utf-8")


def lessons_tally() -> str:
    f = HERE / "lessons.md"
    if not f.is_file():
        return "no lessons.md"
    import re
    tags = re.findall(r"(?m)^- \[([^\]]+)\]", f.read_text(encoding="utf-8"))
    by_cause, open_by_cause = {}, {}
    for t in tags:
        parts = [p.strip() for p in t.split("·")]
        for c in parts[0].split(","):
            c = c.strip()
            by_cause[c] = by_cause.get(c, 0) + 1
            if not parts[-1].startswith("GRADUATED"):
                open_by_cause[c] = open_by_cause.get(c, 0) + 1
    L = [f"{len(tags)} lessons\n", f"{'cause':<14}{'total':>6}{'still open':>12}"]
    for c, n in sorted(by_cause.items(), key=lambda kv: -kv[1]):
        L.append(f"{c:<14}{n:>6}{open_by_cause.get(c, 0):>12}")
    L.append("\nA cause with many STILL OPEN entries is the next thing to engineer.")
    return "\n".join(L)


def telegram(text: str) -> None:
    env = {}
    f = HERE / ".env"
    if f.is_file():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"')
    tok = os.environ.get("TELEGRAM_BOT_TOKEN") or env.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TELEGRAM_CHAT_DM") or env.get("TELEGRAM_CHAT_DM", "")
    if tok and chat:
        subprocess.run(["curl", "-s", "-o", "/dev/null",
                        f"https://api.telegram.org/bot{tok}/sendMessage",
                        "-d", f"chat_id={chat}", "--data-urlencode", f"text={text}"],
                       timeout=30, check=False)


def write(slug: str) -> Path:
    p = OUT / slug / "postmortem.md"
    p.write_text(render(slug), encoding="utf-8")
    return p


def summary_line(slug: str) -> str:
    """The few-line version that fits a Telegram alert.

    Built from analyze(), never by scraping the rendered markdown — the report's
    own bullets are prose and parsing them back out produced garbage causes.
    """
    a = analyze(slug)
    causes = list(dict.fromkeys(c for c, _, _ in a["causes"]))
    broke = ([f"milestone {a['milestone']}"] if a["milestone"]
             and str(a["milestone"]).startswith("FAIL") else []) \
        + ([f"NO VERDICT from {len(a['missing_lenses'])} lenses: "
            + ", ".join(a["missing_lenses"])] if a["missing_lenses"] else []) \
        + a["gate_fails"] + a["lens_fails"]
    rework = (f"\nrework ${a['burned']:.2f} of ${a['total']:.2f}"
              f" ({len(a['repairs'])} repair, {len(a['capped'])} out of turns,"
              f" {len(a['crashed']) + len(a['unknown'])} error)"
              if a["burned"] else "")
    return (f"postmortem {slug}\n"
            f"{a['result']} · ${a['total']:.2f} · {a['wall'] / 3600:.1f}h"
            + rework
            + (f"\ncause: {', '.join(causes)}" if causes else "")
            + ("\n" + "\n".join(f"· {str(b)[:150]}" for b in broke[:3]) if broke else "")
            + f"\nfull: out/{slug}/postmortem.md")


def main() -> int:
    args = [a for a in sys.argv[1:]]
    if "--lessons" in args:
        print(lessons_tally())
        return 0
    if "--all" in args:
        n = 0
        for d in sorted(OUT.iterdir()):
            if (d / "run.json").is_file():
                try:
                    write(d.name)
                    n += 1
                except Exception as e:  # noqa: BLE001
                    print(f"skip {d.name}: {e}")
        rebuild_ledger()
        print(f"wrote {n} postmortems + {LEDGER}")
        return 0
    slugs = [a for a in args if not a.startswith("-")]
    if not slugs:
        print(__doc__)
        return 1
    slug = slugs[0]
    if not (OUT / slug / "run.json").is_file():
        print(f"no out/{slug}/run.json")
        return 1
    p = write(slug)
    rebuild_ledger()
    print(f"wrote {p}")
    print()
    print(render(slug))
    if "--telegram" in args:
        telegram(summary_line(slug))
    return 0


if __name__ == "__main__":
    sys.exit(main())
