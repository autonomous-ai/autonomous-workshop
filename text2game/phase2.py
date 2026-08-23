"""PHASE 2 - assets. One bounded session per todo.md group, not one giant build.

text2cad builds a whole assembly in a single 250-turn session. On 2026-08-18
that session died at 5174s with "Prompt is too long - automatic compaction
failed", and on 08-13 the kernel OOM-killed a 15.4GB boolean chain and took the
cycle with it. Thirteen parts in one session repeats both. Here each group from
todo.md gets its own session, its own turn budget, and its own repair loop, so
one bad group costs a group and not a night.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import fit
import harness
import prompts
import scaffold

HERE = Path(__file__).resolve().parent
TEXT2CAD = Path(os.environ.get("TEXT2CAD_DIR", "/root/text2cad"))


def groups(out_dir: Path) -> list:
    """The `### Phase N - name` blocks todo.md wrote, in order."""
    md = (out_dir / "todo.md").read_text(encoding="utf-8")
    found = re.findall(r"^###\s+(.+?)\s*$(.*?)(?=^###\s|\Z)", md, re.M | re.S)
    return [{"title": t.strip(), "body": b.strip(),
             "parts": sorted(set(re.findall(r"`([a-z0-9_]+)`", b)))}
            for t, b in found]


def concept(out_dir: Path) -> None:
    """Get the concept image - INHERIT it before generating a new one.

    It is a NOTE for the coherence lens, not the thing the lens scores against:
    it was drawn from a one-line pitch before the game had rules or a part list.

    concept_image.py builds its prompt from the `PROMPT:` line of discover.md,
    and t2i is stochastic: running it again produces a DIFFERENT picture from
    the same pitch. If the panel already made one when it picked this game,
    that image is the one a human looked at, so it is the anchor. Generating a
    fresh one would have the lens chase a concept nobody approved.

    Per-part concept images are NOT generated: concept_image.py renders one
    product. Wiring per-part imagegen is phase 2 v2, not something to fake here.
    """
    dst = out_dir / "concept.png"
    if dst.exists():
        return
    inherited = TEXT2CAD / "out" / out_dir.name / "concept.png"
    if inherited.is_file():
        dst.write_bytes(inherited.read_bytes())
        print(f"[concept] inherited the approved image from {inherited}", flush=True)
        return
    script = TEXT2CAD / "concept_image.py"
    if not script.exists():
        return
    r = subprocess.run([sys.executable, str(script), str(out_dir)],
                       capture_output=True, text=True, timeout=600,
                       env=harness.phase_env())
    print(f"[concept] {'ok' if (out_dir / 'concept.png').exists() else 'skipped'}"
          f" {r.stdout.strip()[-120:]}", flush=True)


RENDER_PY = os.environ.get("RENDER_PY") or harness.text2cad_py()


def sync_part_colors(out_dir: Path) -> int:
    """Rewrite part_colors.json from the locked palette. Returns how many moved.

    The chain from a colour decision to a picture is
    art_direction.md -> parts/<id>.py COLOR_HEX -> part_colors.json -> the
    render -> the coherence lens, and only the build agents ever wrote the
    third link. Rewriting the palette therefore changed nothing a human could
    see.

    Measured 2026-08-20 on `precedent`: art_direction was re-run to fix a 4/10,
    the palette changed on all nine ids, and part_colors.json still held the
    hexes from 14:10. The lens scored the OLD colours a second time, off a
    freshly-made render, and returned 4/10 again - which reads exactly like the
    new palette having failed.
    """
    ad, pc = out_dir / "art_direction.md", out_dir / "part_colors.json"
    if not ad.is_file():
        return 0
    palette = palette_of(out_dir)
    if not palette:
        print("  WARNING: art_direction.md exists and no `id`/`#hex` pair "
              "parsed out of it - part_colors.json left alone and the render "
              "will use whatever it already held.", flush=True)
        return 0
    try:
        cur = json.loads(pc.read_text(encoding="utf-8")) if pc.is_file() else {}
    except json.JSONDecodeError:
        cur = {}
    moved = 0
    for key in list(cur):
        pid = key[:-4] if key.endswith(".stl") else key
        want = palette.get(pid)
        if want and cur[key].upper() != want.upper():
            cur[key], moved = want, moved + 1
    for pid, hexv in palette.items():          # ids the build never wrote
        if f"{pid}.stl" not in cur and pid not in cur:
            cur[f"{pid}.stl"], moved = hexv, moved + 1
    if moved:
        pc.write_text(json.dumps(cur, indent=2) + "\n", encoding="utf-8")
    return moved


def stage_render(out_dir: Path) -> None:
    """stage.json -> renders/staged.png, the frame the lens actually judges.

    Wrapped like render_assembly: a staging miss costs the run a better picture
    and must never cost it the run. If this produces nothing, prompts.coherence
    falls back to the assembled contact sheet on its own.
    """
    script = HERE / "stage.py"
    if not script.exists():
        return
    r = subprocess.run([RENDER_PY, str(script), str(out_dir)],
                       capture_output=True, text=True, timeout=1800)
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    lines = [ln for ln in out.splitlines() if ln.strip()]
    for ln in lines:
        if "WARNING" in ln or "Traceback" in ln:
            print(f"[stage] {ln.strip()[:200]}", flush=True)
    png = out_dir / "renders" / "staged.png"
    print(f"[stage] {'ok' if png.exists() else 'FAILED'} "
          f"{lines[-1][:110] if lines else ''}", flush=True)


def render_assembly(out_dir: Path) -> None:
    """Draw the assembled game before the lens is asked to look at it.

    Nothing called render_assembly.py. phase3 only checks whether the image
    EXISTS, to decide about the video. So `coherence` - the visual gate, the
    one that stops a run under COHERENCE_MIN - scored whatever picture happened
    to be on disk.

    Measured 2026-08-20 on `precedent`: the render was from 14:11, the palette
    was rewritten at 14:42 to fix the 4/10 the lens had just given it, and a
    rerun would have judged the old colours and returned 4/10 again. The
    renderer also needs trimesh, which the pipeline venv does not have and
    text2cad's does - so it failed silently by never being called at all.
    """
    script = HERE / "render_assembly.py"
    if not script.exists():
        return
    moved = sync_part_colors(out_dir)
    if moved:
        print(f"[render] part_colors.json was stale - {moved} colour(s) "
              f"re-synced from art_direction.md", flush=True)
    r = subprocess.run([RENDER_PY, str(script), str(out_dir)],
                       capture_output=True, text=True, timeout=1800)
    png = out_dir / "renders" / "assembled.png"
    out = (r.stdout or "") + (r.stderr or "")
    lines = [ln for ln in out.strip().splitlines() if ln.strip()]
    # Every WARNING, not just the last line. render_assembly.py prints its
    # missing-colour warning BEFORE the solid count, and `splitlines()[-1]`
    # threw it away - so the one alarm built to catch "the palette did not
    # survive" was swallowed by the log line meant to report it. coach-party
    # 2026-08-20: 40 solids drawn grey, no warning anywhere, coherence 3/10.
    for ln in lines:
        if "WARNING" in ln or "Traceback" in ln:
            print(f"[render] {ln.strip()[:200]}", flush=True)
    print(f"[render] {'ok' if png.exists() else 'FAILED'} "
          f"{lines[-1][:110] if lines else ''}", flush=True)


def palette_of(out_dir: Path) -> dict:
    r"""{id: "#RRGGBB"} from art_direction.md, whatever shape it wrote it in.

    Both readers of this file used to require a markdown TABLE row:

        re.findall(r"^\| `([a-z0-9_]+)` \| `(#[0-9A-Fa-f]{6})`", ...)

    coach-party 2026-08-20 re-ran art_direction and it wrote a BULLET list -
    "- `through_hut` - `#176F68` - matte deep-petrol PLA." - which is a
    perfectly good answer to a prompt that never pinned the shape. Both
    regexes returned {} and both failed silently in the worst possible
    direction: sync_part_colors moved nothing, so the render drew the OLD
    palette, and palette_collisions reported "none" - a clean bill of health
    from a function that had parsed zero colours.

    So: id and hex, in backticks, on one line, in that order. Table, bullet or
    prose. And an EMPTY result is a parse failure to be shouted about, never a
    palette with no problems - that is the caller's job below.
    """
    f = out_dir / "art_direction.md"
    if not f.is_file():
        return {}
    out = {}
    for line in f.read_text(encoding="utf-8").splitlines():
        m = re.search(r"`([a-z0-9_]+)`[^`]{0,12}`(#[0-9A-Fa-f]{6})`", line)
        if m and m.group(1) not in out:
            out[m.group(1)] = m.group(2)
    return out


def palette_collisions(out_dir: Path) -> list:
    """DIFFERENT component ids given the same hex in art_direction.md.

    The coherence lens asks whether a player can tell the parts apart at a
    glance, and it asks at the END of phase 2 - after every group is built.
    On `precedent` 2026-08-20 it came back 4/10: "the gate and evidence_hopper
    collapse into one continuous petrol-blue shell", "the verdict_pan is
    difficult to separate from the charcoal bench". Both pairs were assigned
    identical hexes by art_direction.md itself, six colours across nine parts.

    Two copies of the SAME part clipping together should share a colour, so
    self-pairs are not collisions. Two DIFFERENT parts sharing one are.

    This used to check only pairs that declare each other in `mates_with`,
    because touching parts merging into one silhouette was the failure that
    had been measured. coach-party 2026-08-20 produced the other half:
    `through_hut` and `bell_ratchet_church` never touch, were deliberately
    given one hex to "bind the architecture together", and the lens returned
    3/10 for exactly that. The lens is looking at a PHOTOGRAPH. Nothing in a
    photograph knows which parts mate, so neither does this check any more -
    mating pairs are still reported first, because they are worse.
    """
    cj = out_dir / "components.json"
    if not (out_dir / "art_direction.md").is_file() or not cj.is_file():
        return []
    color = palette_of(out_dir)
    try:
        comps = json.loads(cj.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(comps, dict):
        comps = comps.get("components", [])
    ids = [c.get("id") for c in comps if c.get("id")]
    mating = set()
    for c in comps:
        a = c.get("id")
        for b in c.get("mates_with") or []:
            if a != b:
                mating.add(frozenset((a, b)))
    out, seen = [], set()
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            key = frozenset((a, b))
            if a == b or key in seen or not color.get(a):
                continue
            seen.add(key)
            if color.get(a) == color.get(b):
                out.append((a, b, color[a], "mates" if key in mating else "seen together"))
    # touching parts merging is the worse failure, so it is reported first
    out.sort(key=lambda t: t[3] != "mates")
    return out


def step_path(out_dir: Path) -> Path:
    steps = sorted((out_dir).glob("*.step")) + sorted((out_dir).glob("*.stp"))
    return steps[0] if steps else out_dir / "assembled.step"


def measure_group(out_dir: Path, parts: list) -> list:
    """Contract check, scoped to the parts this group just built."""
    step = step_path(out_dir)
    if not step.exists():
        return [{"severity": "high", "code": "no-step", "pair": ["", ""],
                 "message": f"{step.name} was not exported"}]
    cmd = os.environ.get("MEASURE_CMD",
                         f"uv run --python 3.12 --with cadquery python3 "
                         f"{TEXT2CAD}/skills/cadcode/scripts/measure").split()
    r = subprocess.run(cmd + [str(step), "--gaps"], capture_output=True,
                       text=True, timeout=1800, env=harness.phase_env())
    try:
        data = json.loads(r.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return [{"severity": "high", "code": "measure-failed", "pair": ["", ""],
                 "message": f"measure produced no JSON: {r.stderr[-200:]}"}]
    if not data.get("ok"):
        return [{"severity": "high", "code": "measure-failed", "pair": ["", ""],
                 "message": str(data.get("error"))[:200]}]
    issues = fit.judge(data, fit.contract(out_dir))
    return [i for i in issues if not parts or set(i["pair"]) & set(parts)]


def gate_group(out_dir: Path, parts: list) -> list:
    """Printability for the parts just built. Mesh-only - phase 3 does the slice.

    Phase 2 used to repair on FIT alone, which is only half the question: a part
    can mate perfectly at 0.3mm and still be unprintable - non-manifold, two
    bodies, a 70 percent overhang, a bridge nothing can span. Those failures
    used to survive every group and only surface in phase 3, after all 13 parts
    were built, with no path back except a full rebuild.
    """
    g = TEXT2CAD / "gate.py"
    if not g.exists():
        return []
    subprocess.run([harness.text2cad_py(), str(g),
                    str(out_dir), "--no-slice"], capture_output=True, text=True,
                   timeout=1800, env=harness.phase_env())
    f = out_dir / "gate.json"
    if not f.exists():
        return []
    try:
        rep = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    issues = []
    for fail in rep.get("fails") or []:
        text = fail if isinstance(fail, str) else json.dumps(fail)
        owner = next((p for p in parts if p in text), "")
        if parts and not owner:
            continue                      # another group's problem, not ours
        issues.append({"severity": "high", "code": "unprintable",
                       "pair": [owner, ""], "message": text[:200]})
    return issues


def run(out_dir: Path, run_log: dict, max_repairs: int = 2,
        only: list = None) -> dict:
    print("\n== PHASE 2: assets", flush=True)
    # Say which model does what, out loud. The per-group run labels carry a
    # hyphen (build-g1), so BUILD-G1_MODEL was never a settable env name and
    # every group silently fell through to the sonnet default - on the single
    # hardest task in the pipeline.
    print("[models] " + " ".join(harness.plan(j) for j in
          ("art_direction", "build", "repair", "coherence")), flush=True)
    for f in ("gdd.md", "components.json", "todo.md"):
        if not (out_dir / f).exists():
            print(f"ABORT: phase 2 needs {f} from phase 1", flush=True)
            raise SystemExit(3)

    if not (out_dir / "art_direction.md").exists():
        harness.run_phase("art_direction", prompts.art_direction(out_dir),
                          out_dir, 25, run_log)
    concept(out_dir)

    # Before a single part is built: two DIFFERENT parts sharing a hex read as
    # one object in the lens photograph, and the lens only says so an hour
    # later. Touching makes it worse; it is not what makes it true.
    if not palette_of(out_dir):
        msg = ("[palette] WARNING: no colours parsed from art_direction.md - "
               "the collision check is BLIND, not clean.")
        print(msg, flush=True)
        harness.telegram(f"text2game {out_dir.name}: {msg}")
    for a, b, hexv, how in palette_collisions(out_dir):
        msg = (f"[palette] {a} and {b} are both {hexv} ({how}) - they will "
               f"read as one part. art_direction.md owns this.")
        print(msg, flush=True)
        harness.telegram(f"text2game {out_dir.name}: {msg}")

    written = scaffold.generate(out_dir)
    print(f"[scaffold] {len(written)} stub(s): {', '.join(written) or '(none new)'}",
          flush=True)

    gs = groups(out_dir)
    if not gs:
        print("ABORT: todo.md has no ### Phase blocks", flush=True)
        raise SystemExit(3)
    print(f"[groups] {len(gs)}: " + ", ".join(g["title"][:24] for g in gs), flush=True)

    turns = int(os.environ.get("BUILD_TURNS", "120"))
    report = {"groups": [], "sculptural": []}
    for n, g in enumerate(gs, 1):
        if only and n not in only:
            print(f"[build-g{n}] {g['title']}: skipped (--groups)", flush=True)
            continue
        name = f"build-g{n}"
        harness.run_phase(name, prompts.build_group(out_dir, g["title"], g["body"],
                                                    len(gs)),
                          out_dir, turns, run_log, timeout_s=10800,
                          model=harness.model_for("build"))
        issues = measure_group(out_dir, g["parts"]) + gate_group(out_dir, g["parts"])
        attempt = 0
        while [i for i in issues if i["severity"] == "high"] and attempt < max_repairs:
            attempt += 1
            txt = "\n".join(f"- [{i['severity']}] {i['code']}: {i['message']}"
                            for i in issues if i["severity"] == "high")
            harness.run_phase(f"repair-g{n}-{attempt}",
                              prompts.repair_group(out_dir, g["title"], txt),
                              out_dir, turns // 2, run_log, timeout_s=7200,
                              model=harness.model_for("repair"))
            issues = measure_group(out_dir, g["parts"]) + gate_group(out_dir, g["parts"])
        highs = [i for i in issues if i["severity"] == "high"]
        report["groups"].append({"group": g["title"], "parts": g["parts"],
                                 "repairs": attempt, "high": len(highs),
                                 "issues": issues})
        print(f"[{name}] {g['title']}: {len(highs)} high after {attempt} repair(s)",
              flush=True)
        if highs:
            # Later groups mate with this one. Building on a broken interface
            # multiplies the error instead of isolating it.
            report["stopped_at"] = g["title"]
            harness.confirm(
                f"phase 2 stopped at group '{g['title']}'",
                f"{max_repairs} repairs did not clear it. Later groups mate with "
                f"this one, so building on it multiplies the error:\n"
                + "\n".join(f"- {i['message'][:140]}" for i in highs[:4]),
                "loosen the contract number, rebuild this group with a bigger "
                "budget, or drop the part")
            break

    comps = fit.contract(out_dir)
    report["sculptural"] = [i for i, c in comps.items() if c.get("class") == "sculptural"]
    if report["sculptural"]:
        print(f"[sculptural] {len(report['sculptural'])} part(s) route to "
              f"TRELLIS: {report['sculptural']} - NOT WIRED YET, they will be "
              f"missing from the assembly", flush=True)

    # The visual gate is COHERENCE, not likeness: the anchor is the art
    # direction this pipeline derived from the rules and the part list, not the
    # t2i picture drawn from a one-line pitch before either existed. A pitch
    # drawing must not be able to block a build that satisfies the contract.
    if not report.get("stopped_at") and (out_dir / "art_direction.md").exists():
        # Where each piece GOES, before drawing the picture the lens scores.
        # Without it the lens is handed assembled.step's build coordinates and
        # asked whether they read as one product; on coach-party that was four
        # tiles never clipped into a square and four huts in a row beside the
        # board, and 3/10 was the correct answer to the question asked.
        harness.run_phase("stage", prompts.stage_layout(out_dir), out_dir, 25,
                          run_log)
        report["staged"] = (out_dir / "stage.json").is_file()
        if report["staged"]:
            stage_render(out_dir)
        render_assembly(out_dir)
        harness.run_phase("coherence", prompts.coherence(out_dir), out_dir, 20, run_log)
        body = (out_dir / "lens_coherence.md").read_text(encoding="utf-8") \
            if (out_dir / "lens_coherence.md").exists() else ""
        m = re.search(r"VERDICT:\s*([0-9.]+)\s*/\s*10", body)
        report["coherence"] = float(m.group(1)) if m else None
        c = re.search(r"^CONCEPT:\s*(\w+)", body, re.M)
        report["concept_drift"] = c.group(1).lower() if c else None   # note only
        floor = float(os.environ.get("COHERENCE_MIN", "6"))
        report["coherence_fail"] = (report["coherence"] is None
                                    or report["coherence"] < floor)
        if report["coherence_fail"]:
            harness.telegram(
                f"text2game {out_dir.name}: coherence {report['coherence']}/10 "
                f"below {floor} - the box does not read as one product yet")

    (out_dir / "phase2.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
