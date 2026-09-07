"""Make lessons: classification, vault rows, the product page, and the read path."""

from __future__ import annotations

import unittest

from workshop.errors import ContractError
from workshop.invent.vault import Vault
from workshop.make.vault_lessons import (
    MAX_MAKE_LESSONS,
    build_make_rows,
    classify_make_failure,
    gamevault_make_design,
    gamevault_make_rows,
    make_lessons,
)


def node(kind, name, *, definition="Does one thing.", relations=None, notes=""):
    return {
        "type": kind,
        "name": name,
        "frontmatter": {"type": kind, "name": name, "created": "2026-09-07", "source": "agent", "status": "seeded"},
        "definition": definition,
        "relations": relations or {},
        "notes": notes,
    }


def vault():
    return Vault(
        {
            "mechanisms/rubber-band-motor": node(
                "mechanism",
                "Rubber Band Motor",
                relations={"risks": ["anti-patterns/fiddly-reset", "anti-patterns/physics-untested"]},
            ),
            "anti-patterns/fiddly-reset": node(
                "anti-pattern",
                "Fiddly Reset",
                relations={"mitigated-by": ["rule-patterns/external-knob", "rule-patterns/service-pins"]},
                notes="- [x:1] low: harvested reset complaint.\n- [wish-a#r0002-reset] high, survived 1 round(s): knob buried under the hood.\n",
            ),
            "anti-patterns/physics-untested": node("anti-pattern", "Physics Untested"),
            "anti-patterns/likeness-wall": node(
                "anti-pattern",
                "Likeness Wall",
                notes="- [wish-b#r0001-likeness] high, survived 18 round(s): IoU 0.688 against a 0.90 floor.\n",
            ),
            "anti-patterns/idle-player": node(
                "anti-pattern", "Idle Player", notes="- [bgg:1] low: a board-game row.\n"
            ),
            "rule-patterns/external-knob": node("rule-pattern", "External Knob"),
            "rule-patterns/service-pins": node("rule-pattern", "Service Pins"),
        }
    )


class ClassifyTest(unittest.TestCase):
    def test_protocol_codes_and_unmatched_failures_are_not_lessons(self):
        for code in ("make-contract-invalid", "make-artifact-invalid", "make-part-colours-missing"):
            self.assertIsNone(classify_make_failure(code, "thickness is fine"))
        self.assertIsNone(classify_make_failure("make-something", "no known failure words"))
        with self.assertRaises(ContractError):
            classify_make_failure("", "x")

    def test_failure_classes_map_to_anti_patterns(self):
        cases = {
            ("make-need", "likeness re-review rejects the boots: IoU 0.69 below 0.90"): "likeness-wall",
            ("make-token-budget-stop", "stopped at the product token cap"): "unbounded-repair-loop",
            ("cad-thickness", "wall thickness under 0.8 mm on the axle"): "underbuilt-shell",
            ("cad-overlap", "band anchor intersects the hood"): "sealed-volume-overlap",
            ("cad-motion", "the drive cycle jams at 60 degrees"): "unswept-drive-cycle",
            ("cad-overhang", "unsupported overhang on the bill"): "support-dependent-geometry",
            ("cad-preflight", "feature below process resolution for a 0.4 mm nozzle"): "feature-below-process-resolution",
        }
        for (code, text), slug in cases.items():
            with self.subTest(code=code):
                self.assertEqual(classify_make_failure(code, text), "anti-patterns/" + slug)


class RowsTest(unittest.TestCase):
    def test_rows_keep_only_design_failures_and_carry_provenance(self):
        rows = build_make_rows(
            "wish-a",
            3,
            [
                {"code": "make-contract-invalid", "finding": "wall thickness", "evidence_class": "deterministic-host-gate"},
                {"code": "make-need", "finding": "Likeness IoU 0.69 below 0.90.", "evidence_class": "codex-authored-need"},
                {"code": "cad-gate", "finding": "wall thickness under minimum", "change": "thickened", "evidence_class": "deterministic-cad-gate", "severity": "improve"},
            ],
            ["mechanisms/rubber-band-motor"],
        )
        self.assertEqual([row["code"] for row in rows], ["make-need", "cad-gate"])
        self.assertEqual(rows[0]["symptom"], "anti-patterns/likeness-wall")
        self.assertEqual((rows[0]["weight"], rows[1]["weight"]), (2, 3))
        self.assertEqual(rows[0]["ref"], "wish-a#r3:make-need")
        self.assertEqual(rows[1]["mechanisms"], ["mechanisms/rubber-band-motor"])
        vault_rows = gamevault_make_rows(rows)
        self.assertEqual(vault_rows[0]["id"], "r0003-make-need")
        self.assertEqual(vault_rows[0]["source"], "workshop-make")
        self.assertEqual((vault_rows[0]["severity"], vault_rows[1]["severity"]), ("high", "medium"))
        self.assertEqual(vault_rows[1]["fix_tried"], "thickened")

    def test_rows_reject_malformed_input(self):
        with self.assertRaises(ContractError):
            build_make_rows("bad slug", 1, [], [])
        with self.assertRaises(ContractError):
            build_make_rows("wish-a", 0, [], [])
        with self.assertRaises(ContractError):
            build_make_rows("wish-a", 1, [{"code": "x", "finding": ""}], [])
        with self.assertRaises(ContractError):
            build_make_rows("wish-a", 1, [{"code": "make-need", "finding": "likeness", "severity": "note"}], [])

    def test_design_page_carries_a_make_verdict(self):
        rows = gamevault_make_rows(
            build_make_rows("wish-a", 2, [{"code": "make-need", "finding": "Likeness IoU 0.69."}], [])
        )
        design = gamevault_make_design(
            "wish-a", 2, concept={"title": "Duck", "summary": "A wind-up duck."},
            mechanisms=["mechanisms/rubber-band-motor"], verdict="make-waiting", rows=rows,
        )
        self.assertEqual(design["verdict"], "make-waiting")
        self.assertEqual(design["exhibits"], ["anti-patterns/likeness-wall"])
        self.assertEqual(design["lessons"], ["Likeness IoU 0.69."])
        self.assertEqual(design["scores"], {})
        with self.assertRaises(ContractError):
            gamevault_make_design("wish-a", 2, concept={}, mechanisms=[], verdict="pass", rows=[])


class LessonsTest(unittest.TestCase):
    def test_lessons_follow_mechanism_risks_then_make_classes(self):
        lessons = make_lessons(vault(), {"mechanisms": ["rubber-band-motor"]})
        self.assertEqual(
            [(item["anti_pattern"], item["ref"]) for item in lessons],
            [
                ("anti-patterns/fiddly-reset", "wish-a#r0002-reset"),
                ("anti-patterns/fiddly-reset", "x:1"),
                ("anti-patterns/likeness-wall", "wish-b#r0001-likeness"),
            ],
        )
        self.assertEqual(lessons[0]["fixes"], ["rule-patterns/external-knob", "rule-patterns/service-pins"])
        self.assertEqual(lessons[0]["lesson"], "high, survived 1 round(s): knob buried under the hood.")

    def test_lessons_without_a_concept_or_vault_stay_bounded(self):
        self.assertEqual(make_lessons(None, {"mechanisms": ["rubber-band-motor"]}), [])
        only_classes = make_lessons(vault(), None)
        self.assertEqual([item["anti_pattern"] for item in only_classes], ["anti-patterns/likeness-wall"])
        self.assertEqual(len(make_lessons(vault(), {"mechanisms": ["rubber-band-motor"]}, limit=1)), 1)
        self.assertEqual(make_lessons(vault(), {"mechanisms": "not a list"}), only_classes)
        self.assertLessEqual(MAX_MAKE_LESSONS, 10)
        with self.assertRaises(ContractError):
            make_lessons(vault(), None, limit=0)


if __name__ == "__main__":
    unittest.main()
