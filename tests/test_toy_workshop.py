import hashlib
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.deliver import DefaultDeliver
from inventor_workshop.docs import DefaultDocs, REQUIRED_PRODUCT_IMAGES
from inventor_workshop.errors import ContractError
from inventor_workshop.jobs import Delivered, Feedback, Made, Playtested
from inventor_workshop.make import Wish
from inventor_workshop.models import PlaytestResult
from inventor_workshop.playtest import Playtest
from inventor_workshop.runtime import Runtime
from inventor_workshop.workshop import Workshop, WorkshopTools


CONFIG_SHA256 = "c" * 64


class ToyWorkshopTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.inventor = self.root / "elf"
        self.inventor.mkdir()
        (self.inventor / "TASTE.md").write_text(
            "# Taste\n\nSmall playthings with one surprising interaction.\n",
            encoding="utf-8",
        )
        self.runtime = self.root / "runtime"

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def make_job(context):
        artifact = context.workspace / "artifact"
        artifact.mkdir(parents=True)
        (artifact / "toy.step").write_text(
            "round %d\n" % context.round, encoding="utf-8"
        )
        (artifact / "instructions.md").write_text(
            "Spin it and discover the hidden rhythm.\n", encoding="utf-8"
        )
        return Made.from_root(
            artifact,
            {
                "title": "Rhythm Top",
                "summary": "A pocket top that reveals a changing beat.",
                "lane": context.blueprint.lane,
                "instructions": "Spin, listen, and try to repeat the rhythm.",
                "components": ["one spinning top"],
                "limitations": ["Fixture evidence is not a physical print."],
            },
        )

    @staticmethod
    def playtest_job(context):
        evidence = context.workspace / "simulation.json"
        evidence.parent.mkdir(parents=True)
        passed = context.round >= 2
        evidence.write_text(
            '{"passed":%s}\n' % str(passed).lower(), encoding="utf-8"
        )
        evidence_manifest = build_artifact_manifest(
            context.workspace, created_at="content-addressed"
        )
        result = PlaytestResult.create(
            "mechanism-cycle",
            passed,
            context.made.artifact_sha256,
            {
                "evidence_class": "deterministic-fixture",
                "claims": ["The fixture mechanism completed its bounded cycle."],
            },
            "workshop-test-mechanism",
            "1.0.0",
            CONFIG_SHA256,
            "simulation.json",
            hashlib.sha256(evidence.read_bytes()).hexdigest(),
        )
        feedback = ()
        if not passed:
            feedback = (
                Feedback(
                    "cycle-too-short",
                    "mechanics",
                    "improve",
                    "The first rhythm ends too quickly.",
                    "Add a second beat before the mechanism resets.",
                    ("simulation.json",),
                ),
            )
        return Playtested(
            Playtest(
                context.made.artifact_manifest,
                (result,),
                evidence_manifest=evidence_manifest,
            ),
            feedback,
        )

    @staticmethod
    def passing_playtest(context):
        evidence = context.workspace / "simulation.json"
        evidence.parent.mkdir(parents=True)
        evidence.write_text('{"passed":true}\n', encoding="utf-8")
        manifest = build_artifact_manifest(
            context.workspace, created_at="content-addressed"
        )
        result = PlaytestResult.create(
            "mechanism-cycle",
            True,
            context.made.artifact_sha256,
            {
                "evidence_class": "deterministic-fixture",
                "claims": ["The fixture mechanism completed its bounded cycle."],
            },
            "workshop-test-mechanism",
            "1.0.0",
            CONFIG_SHA256,
            "simulation.json",
            hashlib.sha256(evidence.read_bytes()).hexdigest(),
        )
        return Playtested(
            Playtest(
                context.made.artifact_manifest,
                (result,),
                evidence_manifest=manifest,
            )
        )

    @staticmethod
    def media_maker(context):
        images = context.workspace / "images"
        images.mkdir(parents=True)
        result = {}
        for role in REQUIRED_PRODUCT_IMAGES:
            path = images / (role + ".png")
            path.write_bytes(("fixture %s\n" % role).encode("utf-8"))
            result[role] = path.relative_to(context.workspace).as_posix()
        return result

    @staticmethod
    def fulfiller(context):
        return Delivered(
            context.made.artifact_sha256,
            context.docs.docs_sha256,
            "USPS",
            "Priority Mail",
            "9400100000000000000000",
            "handed-off",
            "2026-08-23T12:00:00+00:00",
            {
                "print_receipt": {"fixture": "print"},
                "qa_receipt": {"fixture": "qa"},
                "packing_receipt": {"fixture": "packing"},
                "carrier_receipt": {"fixture": "handoff"},
            },
        )

    def complete_tools(self, playtest=None):
        return WorkshopTools(
            make=self.make_job,
            playtest=playtest or self.playtest_job,
            docs=DefaultDocs(self.media_maker),
            deliver=DefaultDeliver(self.fulfiller),
        )

    def test_taste_only_elf_runs_shared_feedback_loop_to_deliver(self):
        workshop = Workshop(
            self.inventor,
            "desk-toy",
            tools=self.complete_tools(),
            runtime_root=self.runtime,
        )
        self.assertEqual(workshop.customization_level, "taste-only")
        result = workshop.run(Wish.create("rhythm-top", "A delightful desk spinner"))
        self.assertEqual((result.status, result.job, result.round), ("delivered", "deliver", 2))
        self.assertEqual(result.playtest_rounds, 4)
        self.assertIsNotNone(result.delivery)
        state = Runtime(self.runtime / "workshop.sqlite3")
        self.assertTrue(state.verify_event_chain("rhythm-top"))
        transitions = [event["to_stage"] for event in state.events("rhythm-top")]
        self.assertEqual(
            transitions,
            ["wish", "make", "playtest", "make", "playtest", "docs", "deliver", "deliver"],
        )

    def test_three_levels_are_explicit_and_playtest_requires_make(self):
        taste_only = Workshop(
            self.inventor,
            "desk-toy",
            tools=self.complete_tools(self.passing_playtest),
            runtime_root=self.root / "taste-runtime",
        )
        custom_make = Workshop(
            self.inventor,
            "desk-toy",
            tools=WorkshopTools(
                playtest=self.passing_playtest,
                docs=DefaultDocs(self.media_maker),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            make=self.make_job,
            runtime_root=self.root / "make-runtime",
        )
        custom_playtest = Workshop(
            self.inventor,
            "desk-toy",
            tools=WorkshopTools(
                docs=DefaultDocs(self.media_maker),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            make=self.make_job,
            playtest=self.passing_playtest,
            runtime_root=self.root / "playtest-runtime",
        )
        self.assertEqual(
            (
                taste_only.customization_level,
                custom_make.customization_level,
                custom_playtest.customization_level,
            ),
            ("taste-only", "custom-make", "custom-playtest"),
        )
        with self.assertRaisesRegex(ContractError, "requires custom Make"):
            Workshop(
                self.inventor,
                "desk-toy",
                playtest=self.passing_playtest,
                runtime_root=self.root / "invalid-runtime",
            )

    def test_missing_shared_make_waits_without_fabricating_a_product(self):
        workshop = Workshop(
            self.inventor,
            "model-character",
            runtime_root=self.runtime,
        )
        result = workshop.run(
            Wish.create("tiny-friend", "A tiny desk companion"),
            playtest_rounds=2,
        )
        self.assertEqual((result.status, result.job, result.round), ("waiting", "make", 1))
        self.assertEqual(result.playtest_rounds, 2)
        self.assertEqual(result.needs[0].capability, "model-and-cad-maker")
        state = Runtime(self.runtime / "workshop.sqlite3")
        self.assertTrue(state.verify_event_chain("tiny-friend"))
        self.assertIsNone(state.get_product("tiny-friend")["artifact_sha256"])
        self.assertEqual(state.get_product("tiny-friend")["metadata"]["playtest_rounds"], 2)

    def test_each_wish_can_buy_a_different_bounded_round_allowance(self):
        two_rounds = Workshop(
            self.inventor,
            "desk-toy",
            tools=self.complete_tools(),
            runtime_root=self.root / "two-round-runtime",
        )
        result = two_rounds.run(
            Wish.create("small-tier", "A small playtest allowance"),
            playtest_rounds=2,
        )
        self.assertEqual((result.status, result.round, result.playtest_rounds), ("delivered", 2, 2))

        one_round = Workshop(
            self.inventor,
            "desk-toy",
            tools=self.complete_tools(),
            runtime_root=self.root / "one-round-runtime",
        )
        held = one_round.run(
            Wish.create("smallest-tier", "One chance to improve"),
            playtest_rounds=1,
        )
        self.assertEqual(
            (held.status, held.job, held.round, held.playtest_rounds),
            ("stopped", "playtest", 1, 1),
        )
        self.assertIsNone(held.docs_sha256)
        self.assertIsNone(held.delivery)

        with self.assertRaisesRegex(ContractError, "from 1 to 100"):
            Workshop(
                self.inventor,
                "desk-toy",
                tools=self.complete_tools(),
                runtime_root=self.root / "invalid-round-runtime",
            ).run(
                Wish.create("bad-tier", "An invalid allowance"),
                playtest_rounds=0,
            )

    def test_preview_preserves_wish_taste_and_playful_rule(self):
        workshop = Workshop(
            self.inventor,
            "desk-toy",
            runtime_root=self.runtime,
        )
        preview = workshop.preview(Wish.create("cable-whale", "A cable holder"))
        self.assertEqual(preview["blueprint"]["lane"], "desk-toy")
        self.assertEqual(preview["taste"]["sha256"], workshop.taste.sha256)
        self.assertIn("playful version", preview["brief"]["utility_rule"])


if __name__ == "__main__":
    unittest.main()
