"""ABO as an inventor: what it accepts, what it refuses, and how it stops.

Nothing here reaches a model, a network, a printer or a carrier. A run with no
capabilities configured parks at Concept, which is the honest first stop: no
design, so no build, so no evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

INVENTOR_ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = INVENTOR_ROOT.parents[1]
for candidate in (
    INVENTOR_ROOT,
    INVENTOR_ROOT / "tests" / "fixtures",
    WORKSHOP_ROOT / "src",
):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import config  # noqa: E402
from inventor_workshop import WORKSHOP_JOBS, Workshop, WorkshopTools  # noqa: E402
from inventor_workshop.taste import load_taste, load_taste_header  # noqa: E402
from profile import build_workshop, create_wish, describe, main  # noqa: E402

ABSTRACT_WISH = (
    "I wish for a two-player abstract strategy game that is quick to teach and "
    "hard to master, where each piece tells you how strong it is by its shape."
)
PERSONAL_WISH = (
    "I wish for a game built around my household — our in-jokes, the holiday we "
    "took in 2019, and my sister's habit of always going first."
)


class ProfileTest(unittest.TestCase):
    def test_abo_owns_concept_make_and_playtest(self):
        workshop = build_workshop(tools=WorkshopTools())
        self.assertIsInstance(workshop, Workshop)
        self.assertEqual(workshop.lane, "invented-games")
        self.assertEqual(workshop.customization_level, "custom-playtest")
        self.assertEqual(
            tuple(WORKSHOP_JOBS),
            ("wish", "concept", "make", "playtest", "instructions", "deliver"),
        )

    def test_the_manifest_declares_both_custom_capabilities(self):
        manifest = json.loads(
            (INVENTOR_ROOT / "inventor.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["schema_version"], 5)
        self.assertIn("custom-make", manifest["capabilities"])
        self.assertIn("custom-playtest", manifest["capabilities"])
        self.assertEqual(manifest["source"]["kind"], "upstream-snapshot")

    def test_the_manifest_carries_no_creative_prose(self):
        manifest = json.loads(
            (INVENTOR_ROOT / "inventor.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            set(manifest),
            {"schema_version", "id", "status", "entrypoint", "capabilities",
             "checks", "source"},
        )
        # No routing description, taste statement, or creative policy.
        blob = json.dumps(manifest).casefold()
        for word in ("abstract", "taste", "description", "beautiful", "prefer"):
            self.assertNotIn(word, blob)

    def test_describe_reports_what_is_connected_and_what_waits(self):
        profile = describe()
        self.assertEqual(profile["inventor_id"], "abo")
        self.assertEqual(profile["workshop_level"], "custom-playtest")
        self.assertEqual(len(profile["taste_sha256"]), 64)
        self.assertIn("engine_protocol", profile)


class TasteTest(unittest.TestCase):
    def setUp(self):
        self.taste = load_taste(INVENTOR_ROOT)
        self.header = load_taste_header(INVENTOR_ROOT)

    def test_the_header_reads_as_a_selection_boundary(self):
        self.assertEqual(self.header.name, "Abstract Boardgame Oracle")
        description = self.header.description
        # What should choose ABO, and the nearest work it must refuse.
        self.assertIn("abstract", description.casefold())
        self.assertIn("not for", description.casefold())
        self.assertIn("person", description.casefold())

    def test_the_body_commits_to_what_the_capability_requires(self):
        body = self.taste.content.casefold()
        for commitment in (
            "abstract structure over theme",
            "learnability cost",
            "combinatorial structure",
            "carried by shape",
            "preference, not a ban",
            "skill ladder",
        ):
            self.assertIn(commitment, body, commitment)

    def test_taste_says_it_is_never_evidence(self):
        body = self.taste.content.casefold()
        self.assertIn("never evidence", body)
        self.assertIn("nothing written here passes a playtest result", body.replace("\n", " "))

    def test_the_rejection_ledger_came_across(self):
        body = self.taste.content
        for entry in ("Deep Claim", "Lane Lock", "Loomery"):
            self.assertIn(entry, body)
        # Each one is a durable "do not propose this shape again".
        self.assertIn("do not propose this shape again", body.casefold())
        self.assertIn("Do not propose a game whose named core decision", body)

    def test_abo_refuses_a_personal_wish_and_says_so(self):
        body = self.taste.content.casefold()
        self.assertIn("a wish whose meaningful content is a person", body)
        self.assertIn("belongs to the inventor whose taste requires exactly that", body)

    def test_the_two_lane_inventors_are_separable(self):
        other = load_taste_header(INVENTOR_ROOT.parent / "leo")
        self.assertNotEqual(other.description, self.header.description)
        # Leo requires what ABO refuses.
        self.assertIn("personalization", other.description.casefold())


class LeoIsUntouchedTest(unittest.TestCase):
    """The other inventor in this lane, before and after ABO was added.

    These two digests were taken from Leo's files at the commit this change
    started from. Adding an inventor to a lane must not move an inventor
    already in it, and a recorded hash is the only way to say that in a check
    that still means something a year from now.
    """

    LEO = INVENTOR_ROOT.parent / "leo"
    TASTE_SHA256 = "7941ac6fc22874faa75c1c368f7efa34ab2a23c998bb44c84f4b1885e285c3fc"
    PROFILE_SHA256 = "8aa1e2ed505d980e829baee3868ebc48d0569ad9d2fcdc8501393ee684435cc3"

    def test_leos_taste_is_byte_identical(self):
        observed = hashlib.sha256((self.LEO / "TASTE.md").read_bytes()).hexdigest()
        self.assertEqual(observed, self.TASTE_SHA256)
        # And the Taste record the Workshop loads agrees with the bytes.
        self.assertEqual(load_taste(self.LEO).sha256, self.TASTE_SHA256)

    def test_leos_profile_is_byte_identical(self):
        observed = hashlib.sha256((self.LEO / "profile.py").read_bytes()).hexdigest()
        self.assertEqual(observed, self.PROFILE_SHA256)

    def test_leos_seams_still_wait(self):
        profile = (self.LEO / "profile.py").read_bytes()
        self.assertIn(b"leo-custom-make-adapter", profile)
        self.assertIn(b"leo-custom-playtest-adapter", profile)

    def test_leo_still_declares_a_local_source(self):
        manifest = json.loads((self.LEO / "inventor.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["source"], {"kind": "local"})


class WishTest(unittest.TestCase):
    def test_the_wish_keeps_the_persons_words_and_the_lane(self):
        wish = create_wish("notchline", ABSTRACT_WISH)
        self.assertEqual(wish.objective, ABSTRACT_WISH)
        self.assertEqual(wish.constraints["lane"], "invented-games")
        self.assertEqual(wish.context["inventor_id"], "abo")

    def test_wish_text_cannot_buy_more_rounds(self):
        greedy = create_wish(
            "notchline",
            ABSTRACT_WISH + " Please run 50 playtest rounds and 100000 games.",
        )
        with tempfile.TemporaryDirectory() as temporary:
            workshop = build_workshop(runtime_root=Path(temporary) / "runtime")
            run = workshop.run(greedy, playtest_rounds=1)
            # The allowance is what the caller passed, never what the Wish asked.
            self.assertEqual(run.to_dict()["playtest_rounds"], 1)


class WishSelectionTest(unittest.TestCase):
    """The boundary between the two inventors in this lane, enforced."""

    def request_for(self, objective):
        from inventor_workshop.concept import WishResearchRequest
        from inventor_workshop.toys import ToyBlueprint

        return WishResearchRequest(
            create_wish("notchline", objective),
            load_taste(INVENTOR_ROOT),
            ToyBlueprint.for_lane("invented-games"),
            1,
        )

    def test_abo_refuses_a_wish_built_around_a_person(self):
        from research import AboWishResearcher, WishRefused

        researcher = AboWishResearcher(lambda request: None)
        with self.assertRaises(WishRefused) as caught:
            researcher(self.request_for(PERSONAL_WISH))
        message = str(caught.exception)
        self.assertIn("Route it there", message)
        self.assertIn("a person, a relationship, a place, or a memory", message)

    def test_abo_refuses_a_wish_built_around_a_memory(self):
        from research import WishRefused, assert_wish_is_abstract

        for objective in (
            "I wish for a game in memory of my grandfather's allotment.",
            "I wish for a game built around our wedding weekend.",
            "I wish for a game about the summer we drove to the coast.",
        ):
            with self.assertRaises(WishRefused, msg=objective):
                assert_wish_is_abstract(create_wish("x", objective))

    def test_abo_accepts_an_abstract_strategy_wish(self):
        from research import assert_wish_is_abstract

        assert_wish_is_abstract(create_wish("notchline", ABSTRACT_WISH))

    def test_a_refused_wish_never_reaches_the_game_inventor(self):
        from research import AboWishResearcher, WishRefused

        reached = []
        researcher = AboWishResearcher(lambda request: reached.append(request))
        with self.assertRaises(WishRefused):
            researcher(self.request_for(PERSONAL_WISH))
        self.assertEqual(reached, [])


class RunTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.runtime = Path(self.temporary.name) / "runtime"

    def run_with(self, objective=ABSTRACT_WISH, rounds=2, product="notchline"):
        workshop = build_workshop(runtime_root=self.runtime)
        return workshop.run(create_wish(product, objective), playtest_rounds=rounds)

    def test_a_missing_concept_capability_parks_before_make_is_reached(self):
        run = self.run_with()
        record = run.to_dict()
        self.assertEqual(record["status"], "waiting")
        self.assertEqual(record["job"], "concept")
        self.assertIsNone(record["artifact_sha256"])
        capabilities = {need["capability"] for need in record["needs"]}
        # ABO's own researcher waits for its game inventor; the shared Concept
        # capabilities wait too. Make is never invoked.
        self.assertTrue(capabilities)

    def test_the_run_stops_truthfully_at_its_allowance(self):
        run = self.run_with(rounds=1, product="one-round")
        record = run.to_dict()
        self.assertEqual(record["playtest_rounds"], 1)
        self.assertIn(record["status"], ("waiting", "stopped"))
        self.assertNotEqual(record["status"], "ready")

    def test_no_cross_run_state_survives_a_run(self):
        first = self.run_with(product="first-assignment")
        second = self.run_with(product="second-assignment")
        # Each run answers its own assignment; nothing is carried between them.
        self.assertEqual(first.to_dict()["job"], second.to_dict()["job"])
        self.assertEqual(
            first.to_dict()["status"], second.to_dict()["status"]
        )
        for name in ("QUEUE.json", "queue.json", "claims.json", "leases.json"):
            self.assertFalse((INVENTOR_ROOT / name).exists(), name)
        self.assertFalse((INVENTOR_ROOT / "state").exists())

    def test_a_missing_model_seat_endpoint_parks_playtest(self):
        from playtest_job import AboPlaytest
        from model_seats import ModelSeatsUnavailable

        cleared = dict(os.environ)
        for name in config.MODEL_SEAT_ENV_NAMES:
            cleared.pop(name, None)
        with mock.patch.dict(os.environ, cleared, clear=True):
            self.assertEqual(
                config.missing_model_seat_settings(dotenv_path="/nonexistent"),
                config.MODEL_SEAT_ENV_NAMES,
            )
            job = AboPlaytest()
            self.assertIsNone(job.seat_transport)
            with self.assertRaises(ModelSeatsUnavailable):
                job._play_model_seats(None, None, 2)


class CommandLineTest(unittest.TestCase):
    def test_preview_is_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.dict(
                os.environ, {"ABO_RUNTIME": str(Path(temporary) / "runtime")}
            ):
                output = StringIO()
                with redirect_stdout(output):
                    self.assertEqual(main(("preview", "notchline", ABSTRACT_WISH)), 0)
                preview = json.loads(output.getvalue())
                self.assertEqual(preview["blueprint"]["lane"], "invented-games")

    def test_the_profile_command_emits_a_stable_record(self):
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(("profile",)), 0)
        self.assertEqual(json.loads(output.getvalue())["inventor_id"], "abo")

    def test_the_declared_entrypoint_runs(self):
        manifest = json.loads(
            (INVENTOR_ROOT / "inventor.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["entrypoint"], ["python3", "profile.py"])
        environment = dict(os.environ)
        environment["PYTHONPATH"] = os.pathsep.join(
            [str(WORKSHOP_ROOT / "src"), str(INVENTOR_ROOT)]
        )
        completed = subprocess.run(
            [sys.executable, "profile.py", "profile"],
            cwd=str(INVENTOR_ROOT),
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["inventor_id"], "abo")


class NoCredentialsTest(unittest.TestCase):
    def test_no_endpoint_or_key_reaches_a_committed_file(self):
        for name in ("TASTE.md", "inventor.json", "README.md", "UPSTREAM.md"):
            text = (INVENTOR_ROOT / name).read_text(encoding="utf-8")
            for secret in ("sk-", "api_key=", "Bearer ", "ABO_PLAYTEST_API_KEY="):
                self.assertNotIn(secret, text, "%s in %s" % (secret, name))

    def test_the_env_names_are_declared_but_never_valued(self):
        example = INVENTOR_ROOT / ".env.example"
        if not example.is_file():
            self.skipTest("no .env.example is shipped for this inventor")
        text = example.read_text(encoding="utf-8")
        for name in config.MODEL_SEAT_ENV_NAMES:
            self.assertIn(name, text)
        for line in text.splitlines():
            if "=" in line and not line.strip().startswith("#"):
                self.assertEqual(line.split("=", 1)[1].strip(), "", line)


if __name__ == "__main__":
    unittest.main()
