#!/usr/bin/env python3
"""Slice every printed part to real gcode, filament and time.

    ./slice_parts.py out/<slug>

The pipeline promised `*.gcode` and shipped none. gate.py only slices when
ORCASLICER_CLI is set and is written for OrcaSlicer's argument shape; this box
has PrusaSlicer. With the variable unset the gate returns `"sliced": null` and
says nothing, so a run could report `[gate] pass=True` with no gcode anywhere
and nothing in the log looked wrong.

Numbers here are measured by the slicer over the real mesh, never estimated:
the same rule text2cad states for print specs. qty comes from components.json,
so the totals are for a whole box rather than one of each.
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path
import os
import shutil

SLICER = os.environ.get("SLICER_BIN") or shutil.which("prusa-slicer") \
    or "/usr/bin/prusa-slicer"
# The PETG profile ships IN the repo (profiles/petg.ini, 2026-08-22) so a fresh
# clone slices the same way this box does; SLICER_PROFILE overrides it.
PROFILE = Path(os.environ.get("SLICER_PROFILE")
               or Path(__file__).resolve().parent / "profiles" / "petg.ini")

GRAMS = re.compile(r"^; total filament used \[g\] = ([\d.]+)", re.M)
TIME = re.compile(r"^; estimated printing time \(normal mode\) = (.+)$", re.M)


def seconds(s: str) -> int:
    """'1h 9m 49s' -> 4189. PrusaSlicer omits units that are zero."""
    tot = 0
    for n, unit in re.findall(r"(\d+)([dhms])", s):
        tot += int(n) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[unit]
    return tot


def hhmm(sec: float) -> str:
    h, m = divmod(int(sec) // 60, 60)
    return f"{h}h{m:02d}m" if h else f"{m}m"


def quantities(out_dir: Path) -> dict:
    try:
        c = json.loads((out_dir / "components.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    c = c.get("components", c) if isinstance(c, dict) else c
    return {x["id"]: int(x.get("qty", 1)) for x in c if isinstance(x, dict) and "id" in x}


def slice_all(out_dir: Path) -> dict:
    if not Path(SLICER).exists():
        raise SystemExit(f"ABORT: {SLICER} not installed")
    if not PROFILE.exists():
        raise SystemExit(f"ABORT: profile {PROFILE} not found")
    dst = out_dir / "gcode"
    dst.mkdir(exist_ok=True)
    qty = quantities(out_dir)
    rows, failed = [], []

    for stl in sorted((out_dir / "fe_parts").glob("*.stl")):
        pid = stl.stem
        gco = dst / f"{pid}.gcode"
        t0 = time.time()
        r = subprocess.run([SLICER, "--export-gcode", "--load", str(PROFILE),
                            "--output", str(gco), str(stl)],
                           capture_output=True, text=True, timeout=1800)
        if r.returncode != 0 or not gco.exists():
            # A part that will not slice is the one fact a print kit must carry:
            # it is the part nobody can make.
            failed.append({"part": pid,
                           "error": (r.stderr or r.stdout).strip()[-200:]})
            print(f"  FAIL {pid}: {(r.stderr or r.stdout).strip()[-120:]}", flush=True)
            continue
        head = gco.read_text(encoding="utf-8", errors="replace")
        g = GRAMS.search(head)
        t = TIME.search(head)
        n = qty.get(pid, 1)
        row = {"part": pid, "qty": n,
               "grams_each": float(g.group(1)) if g else None,
               "seconds_each": seconds(t.group(1)) if t else None,
               "slice_wall_s": round(time.time() - t0, 1)}
        row["grams_total"] = round(row["grams_each"] * n, 2) if row["grams_each"] else None
        row["seconds_total"] = row["seconds_each"] * n if row["seconds_each"] else None
        rows.append(row)
        print(f"  {pid:20} x{n:<3} {row['grams_each']:6.2f}g  "
              f"{hhmm(row['seconds_each'] or 0)} each", flush=True)

    tot_g = sum(r["grams_total"] or 0 for r in rows)
    tot_s = sum(r["seconds_total"] or 0 for r in rows)
    report = {"parts": rows, "failed": failed,
              "total_grams": round(tot_g, 1), "total_seconds": tot_s,
              "total_print_time": hhmm(tot_s),
              "spool_1kg_pct": round(tot_g / 10, 1),
              "profile": str(PROFILE), "slicer": SLICER}
    (out_dir / "slice_report.json").write_text(json.dumps(report, indent=2),
                                               encoding="utf-8")
    print(f"\n  BOX TOTAL: {tot_g:.0f}g PETG ({tot_g/10:.0f}% of a 1kg spool), "
          f"{hhmm(tot_s)} of printing", flush=True)
    if failed:
        print(f"  {len(failed)} part(s) DID NOT SLICE: "
              f"{[f['part'] for f in failed]}", flush=True)
    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    slice_all(Path(sys.argv[1]).resolve())
