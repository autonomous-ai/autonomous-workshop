#!/usr/bin/env python3
"""The publish gate, tested offline (no API calls, no money).

Guards the rule that one-way-newsreel broke on 2026-08-16: a product ships only
when the gate passes AND every expected lens actually returned a verdict AND
none of them failed. The dangerous case is the third assertion — an empty panel
used to read as a clean one.
"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

# text2cad has no .py suffix; load it as a module without executing main().
spec = importlib.util.spec_from_loader(
    "t2c", importlib.machinery.SourceFileLoader("t2c", str(HERE / "text2cad")))
t2c = importlib.util.module_from_spec(spec)
sys.modules["t2c"] = t2c
spec.loader.exec_module(t2c)

ALL = ["printability", "fidelity", "likeness", "sellability"]
PASS_ALL = {x: "PASS 8/10 fine" for x in ALL}
fails = []


def check(name, got, want):
    if got == want:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}: got {got!r}, want {want!r}")
        fails.append(name)


print("ship_decision")
ship, unjudged, failing = t2c.ship_decision(True, PASS_ALL, ALL)
check("gate pass + all lenses pass -> ship", (ship, unjudged, failing), (True, [], []))

ship, unjudged, _ = t2c.ship_decision(False, PASS_ALL, ALL)
check("gate fail -> no ship", ship, False)

panel = dict(PASS_ALL, fidelity="FAIL 3/10 wrong silhouette")
ship, _, failing = t2c.ship_decision(True, panel, ALL)
check("a failing lens -> no ship", (ship, len(failing)), (False, 1))

# the regression: the panel died, so its verdicts are simply absent
ship, unjudged, failing = t2c.ship_decision(True, {}, ALL)
check("empty panel -> no ship", ship, False)
check("empty panel -> all lenses unjudged", unjudged, ALL)
check("empty panel -> reports no false failures", failing, [])

partial = {"printability": "PASS 8/10", "fidelity": "PASS 7/10"}
ship, unjudged, _ = t2c.ship_decision(True, partial, ALL)
check("panel killed halfway -> no ship", ship, False)
check("panel killed halfway -> names what is missing",
      unjudged, ["likeness", "sellability"])

# a run with no approved concept legitimately skips the likeness lens
no_like = [x for x in ALL if x != "likeness"]
ship, unjudged, _ = t2c.ship_decision(True, {x: "PASS 9/10" for x in no_like}, no_like)
check("no concept -> likeness not required", (ship, unjudged), (True, []))

# a lens seeded as "did not run" must count as failing, never as silence
seeded = dict(PASS_ALL, likeness="FAIL did not run")
ship, unjudged, failing = t2c.ship_decision(True, seeded, ALL)
check("seeded 'did not run' -> no ship", ship, False)
check("seeded 'did not run' -> counted as a failure", len(failing), 1)


print("\nautoloop publish parsing")
sys.path.insert(0, str(HERE))
import autoloop  # noqa: E402


def parse(line):
    """Mirror of the DONE-line parse in autoloop.main()."""
    return "ship=YES" in line


check("ship=YES publishes",
      parse("== DONE slug: gate=PASS ship=YES | PANEL printability:PASS"), True)
check("ship=NO does not publish",
      parse("== DONE slug: gate=PASS ship=NO | PANEL printability:FAIL"), False)
check("gate=PASS alone is not enough",
      parse("== DONE slug: gate=PASS ship=NO | ?"), False)


print("\npostmortem reads the pipeline's own decision")
spec2 = importlib.util.spec_from_file_location("pm", HERE / "postmortem.py")
pm = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(pm)

with tempfile.TemporaryDirectory() as td:
    d = Path(td) / "out" / "fake-run"
    d.mkdir(parents=True)
    (d / "run.json").write_text(json.dumps({
        "slug": "fake-run",
        "build": {"cost_usd": 1.0, "wall_s": 60, "num_turns": 10,
                  "max_turns": 60, "is_error": False},
        "lens-printability": {"cost_usd": 0.5, "wall_s": 30, "num_turns": 70,
                              "max_turns": 70, "is_error": True},
        "gate": {"pass": True, "fails": [], "n_parts": 5},
        "panel": {},
        "ship": False,
        "unjudged_lenses": ALL,
    }))
    pm.OUT = Path(td) / "out"
    a = pm.analyze("fake-run")
    check("unshipped run is not reported as SHIPPED", a["result"] != "SHIPPED", True)
    check("names the lens that ran and said nothing", a["no_verdict"], ["printability"])
    check("counts the starved phase", a["capped"], ["lens-printability"])

print()
if fails:
    print(f"{len(fails)} FAILED: {', '.join(fails)}")
    sys.exit(1)
print("all ship-gate tests passed")
