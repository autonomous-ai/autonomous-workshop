#!/usr/bin/env python3
"""Does the built STEP honour the clearances phase 1 promised?

`components.json` is a contract: every part declared `tolerance_mm`, the
clearance its job survives, before any geometry existed. This reads the B-rep
back with cadcode's scripts/measure and holds the build to it.

Measured, not eyeballed - the likeness lens judges looks, this judges fit.
scripts/measure emits {"ok":true,"parts":[...],"pairs":[{"a","b","gap_mm",
"overlap_mm3"}]}.

    ./fit.py <out_dir> <assembled.step>
"""
import json
import os
import subprocess
import sys
from pathlib import Path
import harness

# Two solids sharing a mating face register a tiny overlap that is modelling
# fuzz, not interference. text2cad settled on the same floor in cadpy/checks.py.
FUZZ_MM3 = 2.0


def contract(out_dir: Path) -> dict:
    data = json.loads((out_dir / "components.json").read_text(encoding="utf-8"))
    comps = data if isinstance(data, list) else data.get("components", [])
    return {c["id"]: c for c in comps}


def _match(label: str, ids) -> str:
    """STEP labels carry suffixes (beam_disc_1); map back to a contract id."""
    low = (label or "").lower()
    hits = [i for i in ids if i in low]
    return max(hits, key=len) if hits else ""


def judge(measure_json: dict, comps: dict) -> list:
    """-> issues. A pair is checked against the TIGHTER of the two tolerances."""
    issues = []
    ids = list(comps)
    for row in measure_json.get("pairs", []):
        a, b = _match(row.get("a"), ids), _match(row.get("b"), ids)
        if not a or not b or a == b:
            continue
        mates = a in (comps[b].get("mates_with") or []) or \
            b in (comps[a].get("mates_with") or [])
        overlap = row.get("overlap_mm3") or 0.0
        gap = row.get("gap_mm")
        if overlap > FUZZ_MM3:
            issues.append({"severity": "high", "code": "interference",
                           "pair": [a, b],
                           "message": f"{a} and {b} interpenetrate by "
                                      f"{overlap}mm3 (fuzz floor {FUZZ_MM3})"})
            continue
        if not mates:
            continue
        tol = min(comps[a]["tolerance_mm"], comps[b]["tolerance_mm"])
        if gap is None:
            issues.append({"severity": "high", "code": "no-gap",
                           "pair": [a, b],
                           "message": f"{a}<->{b} are declared mates but measure "
                                      f"found no clearance between them"})
        elif gap < tol * 0.5:
            issues.append({"severity": "high", "code": "too-tight",
                           "pair": [a, b],
                           "message": f"{a}<->{b} gap {gap}mm, contract says "
                                      f"{tol}mm - it will not assemble"})
        elif gap > tol * 3:
            issues.append({"severity": "warn", "code": "too-loose",
                           "pair": [a, b],
                           "message": f"{a}<->{b} gap {gap}mm against a {tol}mm "
                                      f"contract - the fit will feel sloppy"})
    for cid, c in comps.items():
        if (c.get("mates_with") or []) and not any(
                cid in i["pair"] for i in issues) and not any(
                cid in (_match(r.get("a"), ids), _match(r.get("b"), ids))
                for r in measure_json.get("pairs", [])):
            issues.append({"severity": "warn", "code": "unmeasured",
                           "pair": [cid, ""],
                           "message": f"{cid} declares mates but no pair "
                                      f"involving it was near enough to measure"})
    return issues


def main() -> int:
    out_dir, step = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
    cmd = os.environ.get(
        "MEASURE_CMD",
        "uv run --python 3.12 --with cadquery python3 "
        f"{harness.text2cad_dir()}/skills/cadcode/scripts/measure").split()
    r = subprocess.run(cmd + [str(step), "--gaps"], capture_output=True,
                       text=True, timeout=900)
    try:
        data = json.loads(r.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        print(f"fit: measure produced no JSON: {r.stderr[-300:]}")
        return 2
    if not data.get("ok"):
        print(f"fit: measure failed: {data.get('error')}")
        return 2
    issues = judge(data, contract(out_dir))
    (out_dir / "fit.json").write_text(json.dumps(issues, indent=2), encoding="utf-8")
    for i in issues:
        print(f"  [{i['severity']:4}] {i['code']}: {i['message']}")
    highs = [i for i in issues if i["severity"] == "high"]
    print(f"fit: {len(highs)} high, {len(issues) - len(highs)} warn")
    return 1 if highs else 0


if __name__ == "__main__":
    sys.exit(main())
