from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import model

assert len(model.PART_KEYS) == 30
assert model.DRIVER_D == 10.51
assert model.PILOT_D == 7.0
assert model.TENDER_D == 7.59
assert abs((model.JOURNAL_DIAMETER - model.AXLE_DIAMETER) - 0.4) < 1e-9
assert abs((model.HOOK_OPENING - model.BAR_DIAMETER) - 0.4) < 1e-9
assert max(model.DRIVER_X) - min(model.DRIVER_X) == 33.0
for key in model.PART_KEYS:
    shape = model.printable_part(key)
    assert len(shape.solids()) == 1, key
    box = shape.bounding_box()
    assert abs(box.min.Z) < 0.001, key
    assert box.size.X <= 200 and box.size.Y <= 200, key
print("PASS: 30 one-shell bed-normalized parts; wheel/journal and hook/bar datums preserved")
