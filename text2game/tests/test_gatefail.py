"""Does a failing gate actually stop phase 3 before it slices anything?

    python3 tests/test_gatefail.py

The unit tests cover failing_parts/groups_owning. This exercises the WIRING:
gate() is stubbed to fail, and the run must return early with the rebuild
instruction and without writing plates.json.
"""
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import harness  # noqa: E402
import phase3  # noqa: E402

d = Path(tempfile.mkdtemp())
(d / "components.json").write_text(json.dumps([
    {"id": "beam_disc", "qty": 1, "role": "r", "class": "functional", "duty": "d",
     "tolerance_mm": 0.2, "target_bbox_mm": [64, 64, 6], "mates_with": []},
    {"id": "ship", "qty": 12, "role": "r", "class": "functional", "duty": "d",
     "tolerance_mm": 0.4, "target_bbox_mm": [10, 10, 14], "mates_with": []}]),
    encoding="utf-8")
(d / "todo.md").write_text(
    "### Phase 1 - Cabin\nparts: `cabin`\n\n"
    "### Phase 2 - Tower\nparts: `beam_disc`\n\n"
    "### Phase 3 - Ships\nparts: `ship`\n", encoding="utf-8")
(d / "gdd.md").write_text("## Turn structure\n\n**1. Go.** move `ship`.\n\n## Legacy\n\nsnap\n",
                          encoding="utf-8")

phase3.gate = lambda out_dir: {
    "pass": False, "parts": {"beam_disc.stl": {}, "ship.stl": {}},
    "fails": ["beam_disc.stl: not watertight (2 bodies)",
              "ship.stl: overhang 71% exceeds 60%"]}
harness.telegram = lambda text: print(f"  [telegram] {text.splitlines()[0]}")

rep = phase3.run(d, {})

checks = [
    ("returned early with the failing parts",
     rep.get("failing_parts") == ["beam_disc", "ship"]),
    ("named the groups that built them", rep.get("rebuild_groups") == [2, 3]),
    ("did NOT slice: no plates.json", not (d / "plates.json").exists()),
    ("did NOT write a print kit", not (d / "print_kit.md").exists()),
    ("did NOT build a storyboard", not (d / "storyboard.json").exists()),
    ("wrote phase3.json anyway", (d / "phase3.json").exists()),
]
for name, okv in checks:
    print(f"  {'PASS' if okv else 'FAIL'}  {name}")
sys.exit(0 if all(o for _, o in checks) else 1)
