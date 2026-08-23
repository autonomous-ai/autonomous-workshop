#!/usr/bin/env python3
"""Printability gate: trimesh mesh checks + optional OrcaSlicer CLI slice.

Usage: python3 gate.py <out_dir> [--no-slice]
Writes <out_dir>/gate.json and prints a one-line verdict.
Mesh/slice logic mirrors minimax-panda's evaluate.py so scores stay comparable.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MEASURE = Path.home() / ".claude" / "skills" / "cadcode" / "scripts" / "measure"
OVERHANG_FAIL_PCT = 50.0
# 0 = no limit (Tam 2026-08-11: print time is the buyer's concern for
# digital-download products; set per-run only if selling physical prints)
PRINT_MIN_MAX = int(os.environ.get("PRINT_MIN_MAX", "0") or "0")


def lint_code(out_dir: Path) -> list:
    """Graduated lessons enforced as hard checks — never advisory notes."""
    issues = []
    for name in ("main.py", "params.py"):
        p = out_dir / name
        if not p.is_file():
            continue
        src = p.read_text(encoding="utf-8", errors="ignore")
        # Lesson (Huggy 2026-08-11, GRADUATED): blanket fillet over every edge
        # direction of a box makes OCCT build spherical vertex-blends that
        # tessellate into phantom sliver bodies. Corner rounds belong in the
        # 2D profile (blocks/cadblocks.rounded_box), directional fillets after.
        if re.search(r"\.edges\(\s*\)\s*\.(fillet|chamfer)\(", src):
            issues.append(f"lint:{name}: blanket .edges().fillet/chamfer — use "
                          f"profile-baked corner rounds (blocks/cadblocks.rounded_box) "
                          f"or directional selectors ('|Z', '>Z')")
    return issues


def part_identity(out_dir: Path) -> tuple:
    """Check the STEP's own part labels against fe_parts/ and part_colors.json.

    The exported STEP already carries every part's name and colour as XCAF
    labels (cadpy writes them from the cq.Assembly), so it is the one artifact
    where part identity is not a naming convention. The viewer, though, is fed
    fe_parts/*.stl + part_colors.json keyed by filename — and a part the STEP
    knows about but those two do not ships as an unpainted white part. That is
    a silent defect: every render the panel looks at is generated from the
    assembly, not from the viewer's inputs.

    Returns (report, fails). A label the colourway never mentions is a fail; a
    part carrying no name at all (part_00, mesh-derived lanes) is reported and
    left alone.
    """
    steps = sorted(out_dir.glob("*.step"))
    if not steps or not MEASURE.is_dir():
        return {}, []
    uv = shutil.which("uv") or str(Path.home() / ".local" / "bin" / "uv")
    try:
        r = subprocess.run(
            [uv, "run", "--python", "3.12", "--with", "cadquery", "python3",
             str(MEASURE), str(steps[0])],
            capture_output=True, text=True, timeout=180, cwd=out_dir)
        payload = json.loads((r.stdout or "").strip().splitlines()[-1])
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}, []
    if not payload.get("ok"):
        return {"error": payload.get("error", {}).get("message", "measure failed")}, []

    labels = [p.get("name", "") for p in payload.get("parts", [])]
    report = {"step": steps[0].name, "n_labels": len(labels)}
    if len(labels) < 2:
        return report, []  # single-solid design: nothing to key

    anonymous = [n for n in labels if re.fullmatch(r"part_?\d+", n or "")]
    if anonymous:
        report["unnamed"] = len(anonymous)
    try:
        colors = json.loads((out_dir / "part_colors.json").read_text(encoding="utf-8"))
    except Exception:
        return report, []  # no colourway authored — publish ships white by design
    have = {str(k).removesuffix(".stl") for k in colors}
    missing = [n for n in labels if n and n not in have
               and re.sub(r"_\d+$", "", n) not in have]
    if missing:
        report["uncoloured"] = missing
        return report, [f"part_identity(STEP labels with no part_colors entry: "
                        f"{', '.join(missing[:6])} — these ship white)"]
    return report, []


def mesh_stats(stl_path: Path) -> dict:
    import trimesh
    import numpy as np

    m = trimesh.load(str(stl_path), force="mesh")
    areas = m.area_faces
    nz = m.face_normals[:, 2]
    overhang = float(areas[nz < -0.7071].sum() / areas.sum() * 100.0) if areas.sum() > 0 else 0.0
    try:
        bodies = len(m.split(only_watertight=False))
    except Exception:
        bodies = 1
    # Graduated lesson (eclipse-v2 2026-08-11, caught by printability lens):
    # a wide flat internal ceiling (sealed-chamber roof) prints as an
    # unsupported bridge and sails past the aggregate overhang%. What matters
    # is bridge SPAN, not area — a 16mm phone slot bridges fine, a 30mm chamber
    # roof sags. Cluster connected straight-down faces above the bed and
    # measure each patch's narrowest bounding width.
    import networkx as nx
    down_idx = np.where((nz < -0.95) &
                        (m.triangles_center[:, 2] > m.bounds[0][2] + 3.0))[0]
    max_span = 0.0
    if len(down_idx):
        sel = set(down_idx.tolist())
        g = nx.Graph((a, b) for a, b in m.face_adjacency
                     if a in sel and b in sel)
        g.add_nodes_from(down_idx.tolist())
        for comp in nx.connected_components(g):
            comp = list(comp)
            if areas[comp].sum() < 200:  # ignore trivial patches
                continue
            # local span = 2x the farthest any point of the patch sits from the
            # patch boundary (inscribed-circle diameter) — a 5mm-wide ring is a
            # 5mm bridge no matter its diameter; a 50mm chamber roof is 50mm.
            edges = np.sort(m.faces[comp][:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2), axis=1)
            uniq, cnt = np.unique(edges, axis=0, return_counts=True)
            bverts = np.unique(uniq[cnt == 1])
            if not len(bverts):
                continue
            bpts = m.vertices[bverts][:, :2]
            cpts = m.triangles_center[comp][:, :2]
            d = np.sqrt(((cpts[:, None, :] - bpts[None, :, :]) ** 2).sum(-1)).min(1)
            max_span = max(max_span, float(2.0 * d.max()))
    return {"watertight": bool(m.is_watertight), "volume_mm3": float(abs(m.volume)),
            "bodies": max(1, bodies), "overhang_pct": round(overhang, 2),
            "bridge_span_mm": round(max_span, 1),
            "bbox_mm": [round(x, 1) for x in (m.bounds[1] - m.bounds[0]).tolist()]}


def slice_stl(stl_path: Path) -> dict:
    """ORCA_PROFILE = "machine.json;process.json;filament.json" (full paths).
    OrcaSlicer 2.4 CLI has no -o; gcode lands in --outputdir as plate_*.gcode."""
    cli = os.environ.get("ORCASLICER_CLI", "").strip()
    profile = os.environ.get("ORCA_PROFILE", "").strip()
    if not cli or not profile:
        return {"sliced": None}
    parts = [p.strip() for p in profile.split(";") if p.strip()]
    if len(parts) != 3:
        return {"sliced": False, "slice_error": "ORCA_PROFILE needs machine;process;filament"}
    with tempfile.TemporaryDirectory() as td:
        cmd = [cli, "--load-settings", f"{parts[0]};{parts[1]}",
               "--load-filaments", parts[2],
               "--slice", "0", "--outputdir", td, str(stl_path)]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        except (OSError, subprocess.TimeoutExpired) as e:
            return {"sliced": False, "slice_error": str(e)[:200]}
        gcodes = sorted(Path(td).glob("*.gcode"))
        if r.returncode != 0 or not gcodes:
            err = (r.stderr or r.stdout)[-200:]
            rj = Path(td) / "result.json"
            if rj.is_file():
                try:
                    err = json.loads(rj.read_text()).get("error_string") or err
                except (OSError, ValueError):
                    pass
            return {"sliced": False, "slice_error": err}
        gcode = gcodes[0]
        out = {"sliced": True, "print_min": None, "filament_g": None}
        head = gcode.read_text(encoding="utf-8", errors="ignore")[:16000]
        t = re.search(r"(?:estimated printing time.*?=|total estimated time:|model printing time:)"
                      r"\s*(?:(\d+)h)?\s*(?:(\d+)m)?", head, re.I)
        if t:
            out["print_min"] = (int(t.group(1) or 0) * 60) + int(t.group(2) or 0)
        f = re.search(r"(?:filament used \[g\]\s*=|total filament weight \[g\]\s*:)\s*([\d.]+)", head, re.I)
        if f:
            out["filament_g"] = float(f.group(1))
        return out


def check_one(stl: Path, do_slice: bool, tag: str) -> tuple:
    """Mesh + slice checks for a single printable body. `tag` prefixes each
    failure so a multi-part report names the offending part."""
    st = {**mesh_stats(stl)}
    st.update(slice_stl(stl) if do_slice else {"sliced": None})
    fails = []
    if not st["watertight"]:
        fails.append(f"{tag}not_watertight")
    if st["bodies"] != 1:
        fails.append(f"{tag}bodies={st['bodies']}")
    if st["overhang_pct"] > OVERHANG_FAIL_PCT:
        fails.append(f"{tag}overhang={st['overhang_pct']}%")
    if st.get("bridge_span_mm", 0) > 25:
        fails.append(f"{tag}bridge_span={st['bridge_span_mm']}mm>25")
    if st.get("sliced") is False:
        fails.append(f"{tag}slice_failed")
    # Graduated lesson (draft-stack-dock 2026-08-12): the A1-mini profile
    # rejects footprints wider than 160mm even though the bed reads 180.
    fw, fd = st["bbox_mm"][0], st["bbox_mm"][1]
    if max(fw, fd) > 160:
        fails.append(f"{tag}footprint={fw}x{fd}>160")
    if PRINT_MIN_MAX > 0 and st.get("print_min") and st["print_min"] > PRINT_MIN_MAX:
        fails.append(f"{tag}print_time={st['print_min']}min>max{PRINT_MIN_MAX}")
    return st, fails


def main() -> int:
    out_dir = Path(sys.argv[1]).resolve()
    do_slice = "--no-slice" not in sys.argv
    # Multi-part designs are scored on the PARTS: each one prints alone, in its
    # own orientation, so body count and overhang measured on the assembled
    # pose would be meaningless. The assembled STL is a viewer artifact.
    parts = sorted((out_dir / "fe_parts").glob("*.stl"))
    meshes = parts or sorted(out_dir.glob("*.stl"))[:1]
    if not meshes:
        report = {"pass": False, "reason": "no_stl"}
    else:
        fails, per_part = [], {}
        for stl in meshes:
            st, f = check_one(stl, do_slice, f"{stl.name}: " if parts else "")
            per_part[stl.name] = st
            fails += f
        stats = list(per_part.values())
        report = {"stl": meshes[0].name, "n_parts": len(meshes),
                  "watertight": all(s["watertight"] for s in stats),
                  "bodies": max(s["bodies"] for s in stats),
                  "overhang_pct": max(s["overhang_pct"] for s in stats),
                  "bridge_span_mm": max(s.get("bridge_span_mm", 0) for s in stats),
                  "volume_mm3": sum(s["volume_mm3"] for s in stats),
                  "bbox_mm": max((s["bbox_mm"] for s in stats), key=max),
                  "sliced": (None if any(s.get("sliced") is None for s in stats)
                             else all(s.get("sliced") for s in stats)),
                  "print_min": sum(s.get("print_min") or 0 for s in stats) or None}
        if parts:
            report["parts"] = per_part
        # Refuse to score meshes older than the source that generated them.
        # Twice now (draft-stack-dock, 2026-08-12 and again 2026-08-13) a
        # repair session edited main.py, hit the `cad` wrapper's 30s default
        # --wall-clock-s, read the SANDBOX_TIMEOUT as "can't export right
        # now", and let the gate re-score a minutes-old mesh -- burning a
        # whole tier re-diagnosing an already-fixed defect. Prose guidance in
        # lessons.md did not stop the second occurrence, so it is mechanical
        # here: a timeout is not a build failure, retry `cad` with a larger
        # --wall-clock-s and re-export before trusting any verdict.
        src = out_dir / "main.py"
        oldest = min(m.stat().st_mtime for m in meshes)
        if src.is_file() and src.stat().st_mtime > oldest:
            stale_s = int(src.stat().st_mtime - oldest)
            report["stale_stl_s"] = stale_s
            fails.append(f"stale_stl(main.py {stale_s}s newer than exports; re-export)")
        fails += lint_code(out_dir)
        identity, identity_fails = part_identity(out_dir)
        if identity:
            report["part_identity"] = identity
        fails += identity_fails
        fc = out_dir / "fit_checks.py"
        if fc.is_file():
            r = subprocess.run([sys.executable, str(fc)], capture_output=True,
                               text=True, timeout=120, cwd=out_dir)
            report["fit_checks"] = "pass" if r.returncode == 0 else \
                (r.stdout + r.stderr)[-200:]
            if r.returncode != 0:
                fails.append("fit_check_failed")
        report["pass"] = not fails
        report["fails"] = fails
    (out_dir / "gate.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(("GATE PASS " if report["pass"] else "GATE FAIL ") + json.dumps(report))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
