"""design-a-toy Stage 3d: the travel-stop placement check (issue #99)."""

import importlib.util
import io
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
TOOL = REPOSITORY / ".claude" / "skills" / "design-a-toy" / "scripts" / "travel_stop.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("travel_stop_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


travel_stop = _load_tool()

BOX = [[-20, 0], [20, 0], [20, 40], [-20, 40]]
# A 15 long, 2 wide bar on a pivot at the box centre, opening counterclockwise
# from 30 degrees down to level: its upper edge leads at the open extreme.
BAR = {"name": "bar", "pivot": [0, 20], "travel": [-30, 0],
       "shapes": [{"polygon": [[0, 19], [15, 19], [15, 21], [0, 21]]}]}


def _box(x0, z0, x1, z1):
    return {"polygon": [[x0, z0], [x1, z0], [x1, z1], [x0, z1]]}


def _check(slice_changes=None, **changes):
    piece = {"name": "layer", "outline": BOX, "movers": [dict(BAR)]}
    piece.update(slice_changes or {})
    check = {
        "stop": "bar open", "host": "box", "plane": ["X", "Z"], "build": [0, -1],
        "slices": [piece],
        "overtravel_deg": 4, "clearance": 0.5, "min_thickness": 0.8, "overhang_deg": 45,
        "grid_mm": 0.5, "step_deg": 1,
    }
    check.update(changes)
    return check


class TravelStopTest(unittest.TestCase):
    def test_material_hanging_from_the_bed_over_the_lead_is_a_stop(self):
        report = travel_stop.run_check(_check())

        self.assertEqual(report["verdict"], "PASS", report["problems"])
        mover = report["slices"][0]["movers"][0]
        self.assertGreater(mover["site_mm2"], 0)
        x0, z0, x1, z1 = mover["site_box"]
        self.assertGreater(z0, 21.0)  # above the bar's upper edge plus clearance
        self.assertLess(z1, 22.5)  # within 4 degrees of the open extreme

    def test_an_opening_through_the_top_leaves_the_lead_unprintable(self):
        # The slot opens through the top, so nothing grows from the bed
        # down to the bar: the lead is free space but cannot print.
        report = travel_stop.run_check(_check({"keep_out": [_box(-20, 30, 20, 40)]}))

        self.assertEqual(report["verdict"], "FAIL")
        mover = report["slices"][0]["movers"][0]
        self.assertGreater(mover["lead_free_mm2"], 0)
        self.assertEqual(mover["site_mm2"], 0)
        self.assertIsNone(mover["gap_to_printable_mm"])
        self.assertIn("name another stop", report["problems"][0])

    def test_material_the_contract_already_prints_can_carry_the_stop(self):
        # A side wall the contract prints by other means, beside the lead.
        report = travel_stop.run_check(_check({
            "keep_out": [_box(-20, 30, 20, 40)],
            "anchors": [_box(16, 2, 20, 29)],
        }))

        self.assertEqual(report["verdict"], "PASS", report["problems"])
        self.assertGreater(report["slices"][0]["movers"][0]["site_box"][2], 12)

    def test_material_grows_no_steeper_than_the_overhang(self):
        # Only the bed's corner beyond x 17 is open; reaching the lead at
        # x 15 means growing 2 sideways while descending at most 45 degrees.
        report = travel_stop.run_check(_check({"keep_out": [_box(-20, 30, 17, 40)]}))
        self.assertEqual(report["verdict"], "PASS", report["problems"])
        site = report["slices"][0]["movers"][0]["site_box"]
        self.assertGreater(site[0], 5)  # nothing reaches the lead near the pivot

        steep = travel_stop.run_check(_check({"keep_out": [_box(-20, 30, 17, 40)]},
                                             overhang_deg=5))
        self.assertEqual(steep["verdict"], "FAIL")

    def test_a_lead_outside_the_outline_is_no_stop(self):
        # The host narrows to X 3 above Z 15, so the bar's lead (X 3 to 15,
        # Z 21 to 22) is outside it.
        outline = [[-20, 0], [20, 0], [20, 15], [3, 15], [3, 40], [-20, 40]]
        report = travel_stop.run_check(_check({"outline": outline}))

        self.assertEqual(report["verdict"], "FAIL")
        mover = report["slices"][0]["movers"][0]
        self.assertEqual(mover["lead_free_mm2"], 0)
        self.assertGreater(mover["lead_outside_outline_mm2"], 0)

    def test_a_stop_thinner_than_the_minimum_is_no_stop(self):
        # Built along the axis, so every free point rises from the bed; a
        # keep-out leaves 0.6 above the swept band at Z 21.5.
        thin = {"outline": [[0, 15], [20, 15], [20, 25], [0, 25]],
                "keep_out": [_box(0, 22.1, 20, 25)]}
        report = travel_stop.run_check(_check(thin, build="normal", grid_mm=0.1))
        self.assertEqual(report["verdict"], "FAIL")
        self.assertGreater(report["slices"][0]["movers"][0]["lead_free_mm2"], 0)

        report = travel_stop.run_check(_check(thin, build="normal", grid_mm=0.1, min_thickness=0.4))
        self.assertEqual(report["verdict"], "PASS", report["problems"])

    def test_a_mover_that_does_not_stop_blocks_space_but_has_no_lead(self):
        idle = dict(BAR, stops=False)
        report = travel_stop.run_check(_check({"movers": [idle]}))

        self.assertEqual(report["verdict"], "FAIL")
        self.assertEqual(report["slices"][0]["movers"], [])

    def test_the_closing_extreme_leads_with_the_other_edge(self):
        closing = dict(BAR, travel=[0, -30])
        # Printed from a bed at Z 0, a block rises under the closed bar.
        report = travel_stop.run_check(_check({"movers": [closing]}, build=[0, 1]))

        self.assertEqual(report["verdict"], "PASS", report["problems"])
        site = report["slices"][0]["movers"][0]["site_box"]
        self.assertLess(site[3], 20)  # below the pivot, under the closed bar

        # Printed from the top, the stop's bed-facing face would follow the
        # closed bar's 30 degree underside, a 60 degree overhang.
        report = travel_stop.run_check(_check({"movers": [closing]}))
        self.assertEqual(report["verdict"], "FAIL")

    def test_the_command_line_exits_one_on_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "check.json"
            path.write_text(json.dumps(_check({"keep_out": [_box(-20, 30, 20, 40)]})))
            with _quiet():
                self.assertEqual(travel_stop.main([str(path), "--map"]), 1)
            path.write_text(json.dumps(_check()))
            with _quiet():
                self.assertEqual(travel_stop.main([str(path)]), 0)


# Broken God at amend-k (attempt 17): the wings hinge on dowels in the spine
# housing's back wall at X +-16, Z 198.8 and open 35 degrees to the Display
# Pose; the housing prints upside down on its top face (Z 208.7), and its
# shoulder slots open through the top in front of the back wall. Sections are
# seen along Y in the X-Z plane, where a wing opening (wing#1 turning -35 to 0
# about +Y) is counterclockwise for wing#1 and clockwise for wing#2.
HINGE = (16.0, 198.8)


def _polar(radius, degrees):
    angle = math.radians(degrees)
    return [HINGE[0] + radius * math.cos(angle), HINGE[1] + radius * math.sin(angle)]


def _arc(radius, start, end, step=5):
    count = max(1, math.ceil(abs(end - start) / step))
    return [_polar(radius, start + (end - start) * i / count) for i in range(count + 1)]


def _mirror(polygon):
    return [[-x, z] for x, z in polygon][::-1]


def _blade_edge(angle, offset, distance):
    d = (math.cos(math.radians(angle)), math.sin(math.radians(angle)))
    return [HINGE[0] + distance * d[0] - offset * d[1], HINGE[1] + distance * d[1] + offset * d[0]]


# The sector layer (Y 11.8 to 17.1) of wing#1 in the Display Pose: the
# 24-tooth sector (tip radius 17.1) from its top end face round the spine
# side to its bottom end face (17.6, 183.1), the root sector's outer edge the
# run measured, then the root plate and the blades out past the housing, from
# blade 6's lower edge to blade 1's upper edge (the contract's blade table).
# The gaps between blades are filled: each is under 35 degrees wide, so the
# blade above sweeps it anyway.
WING_SECTOR = (
    _arc(17.1, 97.8, 275.8) + [_polar(14.3, 276.4)] + _arc(14.35, 276.4, 284)[1:]
    + [[19.66, 184.92], [20.13, 182.24], [22.0, 174.74], [22.65, 165.17]]
    + [_blade_edge(-46.6, -18.1, 90), _blade_edge(4.3, 21.8, 80), _blade_edge(4.3, 21.8, 0)]
)
# The boss layer (Y 7.8 to 11.8): a 14 hub, the pinion boss's toothed arc
# facing the pinion and the arm whose edge the run measured at X 17.4,
# Z 184.5 to 188.1; wing#2's plain boss is the mirror with a 13.75 rim.
BOSS_LEFT = [_polar(6.5, 215)] + _arc(17.1, 215, 268) + [_polar(14.4, 277), _polar(6.5, 277)]
BOSS_RIGHT = _mirror([_polar(6.5, 215)] + _arc(13.75, 215, 277) + [_polar(6.5, 277)])
HOUSING = [[-18.65, 208.7], [18.65, 208.7], [20.35, 206.7], [20.35, 180], [6.65, 142.7],
           [0.4, 133.3], [-0.4, 133.3], [-6.65, 142.7], [-20.35, 180], [-20.35, 206.7]]
# Below Z 170 the housing lies in front of the wing plane (R09).
HOUSING_SECTOR = [[-18.65, 208.7], [18.65, 208.7], [20.35, 206.7], [20.35, 180],
                  [16.93, 170.7], [-16.93, 170.7], [-20.35, 180], [-20.35, 206.7]]


def _hub(x):
    return {"circle": {"center": [x, 198.8], "radius": 7.0}}


def _wings(layer, travel):
    left, right = (
        ([{"polygon": WING_SECTOR}], [{"polygon": _mirror(WING_SECTOR)}]) if layer == "sector"
        else ([_hub(16), {"polygon": BOSS_LEFT}], [_hub(-16), {"polygon": BOSS_RIGHT}])
    )
    return [
        {"name": "wing#1", "pivot": [16, 198.8], "travel": list(travel), "shapes": left},
        {"name": "wing#2", "pivot": [-16, 198.8], "travel": [-a for a in travel], "shapes": right},
    ]


def _broken_god(extreme, layers=("boss", "sector")):
    travel = (-35, 0) if extreme == "open" else (0, -35)
    slices = {
        "boss": {"name": "boss layer Y 7.3 to 11.8", "outline": HOUSING,
                 "keep_out": [{"circle": {"center": [0, 180.9], "radius": 9.75}}],
                 "movers": _wings("boss", travel)},
        "sector": {"name": "sector layer Y 11.8 to 17.6", "outline": HOUSING_SECTOR,
                   "anchors": [{"circle": {"center": [0, 180.9], "radius": 5.9}}],
                   "movers": _wings("sector", travel)},
    }
    return {
        "stop": f"{extreme} extreme: hard stops on vertical housing faces (R03, wing-housing)",
        "host": "spine-housing", "stance": "upside down on its top face (Z 208.7)",
        "plane": ["X", "Z"], "build": [0, -1], "slices": [slices[k] for k in layers],
        "overtravel_deg": 4, "clearance": 0.5, "min_thickness": 0.8, "overhang_deg": 45,
        "grid_mm": 0.5, "step_deg": 1,
    }


class BrokenGodTravelStopTest(unittest.TestCase):
    def test_no_housing_stop_can_end_the_open_extreme(self):
        report = travel_stop.run_check(_broken_god("open"))

        self.assertEqual(report["verdict"], "FAIL")
        boss, sector = report["slices"]
        # The sector layer's opening lead lies outside the 40.7 outline.
        for mover in sector["movers"]:
            self.assertEqual(mover["lead_free_mm2"], 0)
            self.assertGreater(mover["lead_outside_outline_mm2"], 0)
        # The bosses' arm edges lead into free space that cannot print:
        # the hubs sweep the column between it and the bed.
        for mover in boss["movers"]:
            self.assertGreater(mover["lead_free_mm2"], 0)
            self.assertEqual(mover["site_mm2"], 0)
            self.assertGreater(mover["gap_to_printable_mm"], 5)

    def test_the_central_rib_can_end_the_closed_extreme(self):
        report = travel_stop.run_check(_broken_god("closed", layers=("boss",)))

        self.assertEqual(report["verdict"], "PASS", report["problems"])
        x0, z0, x1, z1 = report["slices"][0]["movers"][0]["site_box"]
        self.assertLess(abs(x0 + x1) / 2, 5)  # on the spine centreline
        self.assertGreater(z0, 198.8)  # above the sector mesh


class _quiet:
    def __enter__(self):
        self.saved = sys.stdout
        sys.stdout = io.StringIO()

    def __exit__(self, *exc):
        sys.stdout = self.saved
        return False


if __name__ == "__main__":
    unittest.main()
