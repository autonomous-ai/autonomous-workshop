import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from inventor_workshop.jobs import Invented, Made
from inventor_workshop.workshop import Workshop, WorkshopTools


ROOT = Path(__file__).resolve().parents[1]


def load_profile(inventor_id):
    path = ROOT / "inventors" / inventor_id / "profile.py"
    spec = importlib.util.spec_from_file_location(
        "canonical_profile_%s" % inventor_id, path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_fixture(context):
    context.workspace.mkdir(parents=True)
    (context.workspace / "product.txt").write_text(
        "exact fixture bytes\n", encoding="utf-8"
    )
    return Made.from_root(
        context.workspace,
        {
            "title": "Fixture plaything",
            "summary": "A fixture used only to reach the typed Playtest seam.",
            "lane": context.blueprint.lane,
        },
    )


def invent_fixture(context):
    wish_sha256 = hashlib.sha256(
        json.dumps(
            context.wish.to_dict(), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    return Invented(
        wish_sha256,
        context.taste.sha256,
        context.blueprint.lane,
        {
            "title": "Fixture concept",
            "summary": "A chosen industrial-design direction for contract tests.",
        },
        95,
        90,
    )
class CanonicalInventorProfileTest(unittest.TestCase):
    def test_five_profiles_select_the_five_plaything_lanes_and_three_levels(self):
        expected = {
            "alice": ("classics-made-yours", "taste-only"),
            "bob": ("moving-machines", "custom-make"),
            "eve": ("little-worlds", "taste-only"),
            "ivy": ("holdable-science", "taste-only"),
            "leo": ("invented-games", "custom-playtest"),
        }
        for inventor_id, (lane, level) in expected.items():
            with self.subTest(inventor_id=inventor_id):
                profile = load_profile(inventor_id)
                workshop = profile.build_workshop()
                self.assertIsInstance(workshop, Workshop)
                self.assertEqual(workshop.lane, lane)
                self.assertEqual(workshop.customization_level, level)
                described = profile.describe()
                self.assertEqual(described["inventor_id"], inventor_id)
                self.assertEqual(described["lane"], lane)
                self.assertEqual(described["workshop_level"], level)
                self.assertEqual(len(described["taste_sha256"]), 64)
                self.assertEqual(len(described["blueprint_sha256"]), 64)

    def test_every_profile_creates_a_taste_bound_shared_workshop_preview(self):
        for inventor_id in ("alice", "bob", "eve", "ivy", "leo"):
            with self.subTest(inventor_id=inventor_id):
                profile = load_profile(inventor_id)
                wish = profile.create_wish(
                    "%s-first" % inventor_id,
                    "I wish for a small playful object with a memorable interaction.",
                )
                workshop = profile.build_workshop()
                preview = workshop.preview(wish)
                self.assertEqual(preview["wish"], wish.to_dict())
                self.assertEqual(preview["taste"]["sha256"], workshop.taste.sha256)
                self.assertEqual(preview["blueprint"]["lane"], workshop.lane)

    def test_unconfigured_profiles_wait_at_their_real_invent_boundary(self):
        for inventor_id in ("alice", "bob", "eve", "ivy", "leo"):
            with self.subTest(inventor_id=inventor_id), tempfile.TemporaryDirectory() as temporary:
                profile = load_profile(inventor_id)
                workshop = profile.build_workshop(runtime_root=Path(temporary))
                wish = profile.create_wish(
                    "%s-wait" % inventor_id,
                    "I wish for a truthful first Workshop run.",
                )
                result = workshop.run(wish, playtest_rounds=3)
                self.assertEqual(result.status, "waiting")
                self.assertEqual(result.job, "invent")
                self.assertEqual(result.playtest_rounds, 3)
                self.assertEqual(
                    [need.capability for need in result.needs],
                    ["industrial-design-inventor"],
                )

    def test_profile_cli_passes_the_checked_playtest_allowance_to_workshop(self):
        for inventor_id in ("alice", "bob", "eve", "ivy", "leo"):
            with self.subTest(inventor_id=inventor_id):
                profile = load_profile(inventor_id)
                workshop = mock.Mock()
                workshop.run.return_value.to_dict.return_value = {"status": "waiting"}
                with mock.patch.object(
                    profile, "build_workshop", return_value=workshop
                ), redirect_stdout(io.StringIO()):
                    self.assertEqual(
                        profile.main(
                            (
                                "run",
                                "%s-rounds" % inventor_id,
                                "I wish for a bounded Playtest loop.",
                                "--playtest-rounds",
                                "7",
                            )
                        ),
                        0,
                    )
                self.assertEqual(workshop.run.call_args.kwargs, {"playtest_rounds": 7})

    def test_direct_inventor_cli_generates_the_product_id(self):
        for inventor_id in ("alice", "bob", "eve", "ivy", "leo"):
            with self.subTest(inventor_id=inventor_id):
                profile = load_profile(inventor_id)
                workshop = mock.Mock()
                workshop.run.return_value.to_dict.return_value = {"status": "waiting"}
                with mock.patch.object(
                    profile, "build_workshop", return_value=workshop
                ), redirect_stdout(io.StringIO()):
                    self.assertEqual(
                        profile.main(
                            (
                                "run",
                                "I wish for a toy without naming its folder first.",
                            )
                        ),
                        0,
                    )
                wish = workshop.run.call_args.args[0]
                self.assertRegex(
                    wish.product_id, r"^wish-\d{8}-\d{6}-[0-9a-f]{8}$"
                )
                self.assertEqual(
                    wish.objective,
                    "I wish for a toy without naming its folder first.",
                )

    def test_playtest_allowance_is_not_accepted_as_wish_text(self):
        for inventor_id in ("alice", "bob", "eve", "ivy", "leo"):
            with self.subTest(inventor_id=inventor_id):
                profile = load_profile(inventor_id)
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    profile.main(
                        (
                            "wish",
                            "%s-wish" % inventor_id,
                            "I wish for extra loops.",
                            "--playtest-rounds",
                            "100",
                        )
                    )

    def test_leo_owns_playtest_while_bob_uses_the_shared_default(self):
        leo = load_profile("leo")
        bob = load_profile("bob")
        for profile, capability in (
            (leo, "leo-custom-playtest-adapter"),
            (bob, "agent-playtest"),
        ):
            with self.subTest(inventor_id=profile.PROFILE["inventor_id"]), tempfile.TemporaryDirectory() as temporary:
                workshop = profile.build_workshop(
                    tools=WorkshopTools(invent=invent_fixture),
                    make=make_fixture,
                    runtime_root=Path(temporary),
                )
                wish = profile.create_wish(
                    "%s-playtest" % profile.PROFILE["inventor_id"],
                    "I wish to reach the correct Playtest owner.",
                )
                result = workshop.run(wish, playtest_rounds=2)
                self.assertEqual(result.job, "playtest")
                self.assertEqual(result.status, "waiting")
                self.assertEqual(result.needs[0].capability, capability)

    def test_leo_waits_for_his_ai_playtest_adapter(self):
        leo = load_profile("leo")
        with tempfile.TemporaryDirectory() as temporary:
            workshop = leo.build_workshop(
                tools=WorkshopTools(invent=invent_fixture),
                make=make_fixture,
                runtime_root=Path(temporary),
            )
            wish = leo.create_wish(
                "agent-gate", "I wish for an original duel for our table."
            )
            result = workshop.run(wish, playtest_rounds=2)
        self.assertEqual(
            [need.capability for need in result.needs],
            ["leo-custom-playtest-adapter"],
        )

    def test_every_taste_enforces_wish_uniqueness_and_cool_over_twee(self):
        for inventor_id in ("alice", "bob", "eve", "ivy", "leo"):
            with self.subTest(inventor_id=inventor_id):
                taste = (
                    ROOT / "inventors" / inventor_id / "TASTE.md"
                ).read_text(encoding="utf-8")
                self.assertIn("could not have been bought before this Wish", taste)
                self.assertIn("Cool beats cute or twee", taste)

    def test_alice_preserves_known_rules_and_is_judged_as_an_object(self):
        alice = load_profile("alice")
        described = alice.describe()
        self.assertEqual(described["rules"], "known and preserved")
        self.assertEqual(described["judged_as"], "customized physical object")


if __name__ == "__main__":
    unittest.main()
