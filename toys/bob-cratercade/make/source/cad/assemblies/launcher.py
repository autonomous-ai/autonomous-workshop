"""Launcher placements only. Root owns hardware instances and global stance."""
from build123d import Pos
from parts import launcher_housing, launcher_rod, launcher_guide_cap, launcher_band_guard, launcher_anchor
import params as p


def components(pull=0.0, service=False, anchor_index=0):
    assert 0 <= pull <= p.LAUNCH_TRAVEL
    assert 0 <= anchor_index < len(p.LAUNCH_ANCHOR_Y)
    items = [
        ("launcher_housing", launcher_housing.build(), "slategray", {"role": "stationary", "printable": True}),
        ("launcher_rod", Pos(0, -pull, 0) * launcher_rod.build(), "orangered", {"role": "slider", "axis": [0, -1, 0], "travel_mm": p.LAUNCH_TRAVEL, "printable": True}),
        ("launcher_anchor", Pos(p.LAUNCH_BAND_X, p.LAUNCH_ANCHOR_Y[anchor_index], 0) * launcher_anchor.build(), "orange", {"role": "stationary", "printable": True}),
    ]
    if not service:
        items += [
            ("launcher_guide_cap", launcher_guide_cap.build(), "lightgray", {"role": "stationary", "printable": True}),
            ("launcher_band_guard", launcher_band_guard.build(), "lightgray", {"role": "stationary", "printable": True}),
        ]
    return items
