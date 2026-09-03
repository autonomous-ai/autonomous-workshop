import hashlib
import json
import unittest
from datetime import datetime, timezone

from tests.daydream.support import (
    build_thesis_verdict_dict,
    sample_idea,
    sample_idea_dict,
    sample_novelty,
    sample_sealed,
    sample_thesis,
    sample_thesis_dict,
)
from workshop.daydream.contracts import (
    DAYDREAM_IDEA_KIND,
    DAYDREAM_SEAL_KIND,
    Idea,
    NoveltyNeighbor,
    NoveltyReport,
    PriorArt,
    SealedDaydream,
    TasteFit,
    canonical_json,
    generate_daydream_id,
    render_brief,
)
from workshop.errors import ContractError


class DaydreamIdTest(unittest.TestCase):
    def test_id_mirrors_wish_id_shape(self):
        moment = datetime(2026, 9, 2, 10, 15, 0, tzinfo=timezone.utc)
        self.assertEqual(
            generate_daydream_id(moment=moment, token="0badcafe"),
            "daydream-20260902-101500-0badcafe",
        )
        generated = generate_daydream_id()
        self.assertRegex(generated, r"^daydream-\d{8}-\d{6}-[0-9a-f]{8}$")

    def test_naive_moments_are_treated_as_utc(self):
        moment = datetime(2026, 9, 2, 10, 15, 0)
        self.assertTrue(
            generate_daydream_id(moment=moment, token="00000000").startswith(
                "daydream-20260902-101500-"
            )
        )

    def test_token_must_be_eight_lowercase_hex(self):
        for token in ("ABCDEF01", "abc", "0badcafe0", "0badcafg"):
            with self.subTest(token=token), self.assertRaises(ContractError):
                generate_daydream_id(token=token)


class IdeaTest(unittest.TestCase):
    def test_parse_round_trips_and_has_a_stable_identity(self):
        raw = sample_idea_dict()
        idea = Idea.parse(raw)
        self.assertEqual(idea.to_dict(), raw)
        self.assertEqual(idea.schema_version, 1)
        self.assertIsInstance(idea.prior_art, tuple)
        self.assertIsInstance(idea.keywords, tuple)
        self.assertEqual(
            idea.sha256,
            hashlib.sha256(canonical_json(raw).encode("utf-8")).hexdigest(),
        )
        self.assertEqual(idea.canonical_bytes(), canonical_json(raw).encode("utf-8"))
        self.assertEqual(Idea.parse(json.loads(json.dumps(idea.to_dict()))), idea)

    def test_unknown_and_missing_keys_are_named(self):
        raw = sample_idea_dict()
        raw["colour"] = "red"
        with self.assertRaisesRegex(ContractError, "colour"):
            Idea.parse(raw)
        raw = sample_idea_dict()
        del raw["why_it_is_new"]
        with self.assertRaisesRegex(ContractError, "why_it_is_new"):
            Idea.parse(raw)
        with self.assertRaises(ContractError):
            Idea.parse(["not", "an", "object"])

    def test_kind_and_schema_version_are_exact(self):
        raw = sample_idea_dict()
        raw["kind"] = "autonomous-workshop.wish"
        with self.assertRaisesRegex(ContractError, DAYDREAM_IDEA_KIND):
            Idea.parse(raw)
        raw = sample_idea_dict()
        raw["schema_version"] = 2
        with self.assertRaises(ContractError):
            Idea.parse(raw)

    def test_text_bounds_and_control_characters(self):
        cases = {
            "title": ("x" * 61, "two\nlines", "", "tab\there"),
            "one_liner": ("y" * 201, "a\nb"),
            "what_you_do": ("z" * 601, "bell\x07", "nul\x00"),
        }
        for key, values in cases.items():
            for value in values:
                raw = sample_idea_dict()
                raw[key] = value
                with self.subTest(key=key, value=value[:8]), self.assertRaises(
                    ContractError
                ):
                    Idea.parse(raw)
        raw = sample_idea_dict()
        raw["what_happens"] = "line one\nline two"
        self.assertEqual(Idea.parse(raw).what_happens, "line one\nline two")

    def test_parts_estimate_prior_art_and_keyword_bounds(self):
        for parts in (0, 13, True, "2", 2.0):
            raw = sample_idea_dict()
            raw["parts_estimate"] = parts
            with self.subTest(parts=parts), self.assertRaises(ContractError):
                Idea.parse(raw)
        raw = sample_idea_dict()
        raw["prior_art"] = raw["prior_art"][:1]
        with self.assertRaises(ContractError):
            Idea.parse(raw)
        raw = sample_idea_dict()
        raw["prior_art"] = raw["prior_art"] * 3
        with self.assertRaises(ContractError):
            Idea.parse(raw)
        raw = sample_idea_dict()
        raw["prior_art"] = "Jacob's ladder"
        with self.assertRaises(ContractError):
            Idea.parse(raw)
        for keywords in (
            ["one", "two"],
            ["k%d" % index for index in range(9)],
            ["ladder", "Bead", "click"],
            ["ladder", "ladder", "click"],
            ["ladder", "-bead", "click"],
            ["ladder", "b", "click"],
            "ladder bead click",
        ):
            raw = sample_idea_dict()
            raw["keywords"] = keywords
            with self.subTest(keywords=keywords), self.assertRaises(ContractError):
                Idea.parse(raw)


class PriorArtAndTasteFitTest(unittest.TestCase):
    def test_prior_art_bounds(self):
        PriorArt(name="n" * 80, how_this_differs="d" * 300)
        with self.assertRaises(ContractError):
            PriorArt(name="n" * 81, how_this_differs="d")
        with self.assertRaises(ContractError):
            PriorArt(name="n", how_this_differs="d" * 301)
        with self.assertRaises(ContractError):
            PriorArt(name="n", how_this_differs="line\nbreak")
        with self.assertRaisesRegex(ContractError, "unknown keys"):
            PriorArt.parse({"name": "n", "how_this_differs": "d", "url": "x"})
        entry = PriorArt.parse({"name": "n", "how_this_differs": "d"})
        self.assertEqual(entry.to_dict(), {"name": "n", "how_this_differs": "d"})

    def test_taste_fit_bounds(self):
        fit = TasteFit(honors=["a"], steers_clear_of=("b", "c"))
        self.assertEqual(fit.honors, ("a",))
        self.assertEqual(fit.to_dict(), {"honors": ["a"], "steers_clear_of": ["b", "c"]})
        with self.assertRaises(ContractError):
            TasteFit(honors=[], steers_clear_of=["b"])
        with self.assertRaises(ContractError):
            TasteFit(honors=["a"] * 6, steers_clear_of=["b"])
        with self.assertRaises(ContractError):
            TasteFit(honors=["a" * 201], steers_clear_of=["b"])
        with self.assertRaises(ContractError):
            TasteFit(honors="a", steers_clear_of=["b"])
        with self.assertRaises(ContractError):
            TasteFit.parse({"honors": ["a"]})


class CreativeThesisTest(unittest.TestCase):
    def test_v2_round_trips_and_exposes_legacy_read_views(self):
        raw = sample_thesis_dict()
        thesis = Idea.parse(raw)
        self.assertEqual(thesis.schema_version, 2)
        self.assertEqual(thesis.to_dict(), raw)
        self.assertEqual(Idea.parse(json.loads(json.dumps(raw))), thesis)
        self.assertEqual(thesis.what_you_do, raw["experience"]["action"])
        self.assertIn(raw["experience"]["payoff"], thesis.what_happens)
        self.assertEqual(thesis.held_form, raw["experience"]["physical_form"])
        self.assertEqual(thesis.before_after, raw["proof"]["observable"])
        self.assertEqual(thesis.opportunity.world_scan.signals[0].url, raw["opportunity"]["world_scan"]["signals"][0]["url"])
        self.assertEqual(thesis.proof.mode, "visual-state")

    def test_v2_requires_world_provenance_thesis_and_falsifiers(self):
        mutations = []
        raw = sample_thesis_dict()
        del raw["opportunity"]
        mutations.append(raw)
        raw = sample_thesis_dict()
        raw["opportunity"]["world_scan"]["signals"] = raw["opportunity"]["world_scan"]["signals"][:1]
        mutations.append(raw)
        raw = sample_thesis_dict()
        raw["opportunity"]["world_scan"]["signals"][0]["url"] = "file:///tmp/fake"
        mutations.append(raw)
        raw = sample_thesis_dict()
        raw["proof"]["kill_criteria"] = ["Only one"]
        mutations.append(raw)
        raw = sample_thesis_dict()
        raw["proof"]["mode"] = "vibes"
        mutations.append(raw)
        raw = sample_thesis_dict()
        raw["route_floor"] = "ultra"
        mutations.append(raw)
        for index, malformed in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(ContractError):
                Idea.parse(malformed)

    def test_adversarial_scalar_types_fail_as_contract_errors(self):
        for value in (True, 2.0, "2"):
            raw = sample_thesis_dict()
            raw["schema_version"] = value
            with self.subTest(field="schema_version", value=value), self.assertRaises(ContractError):
                Idea.parse(raw)
        raw = sample_thesis_dict()
        raw["keywords"] = ["valid", {"not": "hashable"}, "third"]
        with self.assertRaises(ContractError):
            Idea.parse(raw)
        raw = sample_thesis_dict()
        raw["keywords"] = ["gravity", "café", "rhythm"]
        with self.assertRaises(ContractError):
            Idea.parse(raw)
        raw = sample_thesis_dict()
        raw["title"] = "Delete\x7fme"
        with self.assertRaises(ContractError):
            Idea.parse(raw)

    def test_v2_brief_separates_dream_ownership_from_invent(self):
        brief = render_brief(sample_thesis(), inventor_name="Sample", inventor_id="sample")
        self.assertIn("Build this creative product thesis", brief)
        self.assertIn("Human tension:", brief)
        self.assertIn("Anti-generic signature:", brief)
        self.assertIn("Kill criteria:", brief)
        self.assertIn("Invent owns the exact mechanism", brief)


class RenderBriefTest(unittest.TestCase):
    def test_brief_is_exact_deterministic_text(self):
        idea = sample_idea()
        brief = render_brief(idea, inventor_name="Pico Press", inventor_id="pico-press")
        expected = (
            "Daydreamed by Pico Press (pico-press). Build this new toy.\n"
            "\n"
            "Title: Ladder Drop\n"
            "In one line: Flip a printed ladder and a captive bead clicks down every "
            "rung by gravity alone.\n"
            "What it looks like: A palm-sized wooden-looking ladder with a bead that "
            "lives inside its rails, round-shouldered like a toy from a rug.\n"
            "Before and after, as a render must show them: Before: the bead rests in "
            "the top cup of the upright ladder. After: the ladder is flipped and the "
            "bead rests in the cup at the other end.\n"
            "What you do: Hold the ladder upright, flip it end over end, and set it "
            "down.\n"
            "What happens: The bead tumbles rung by rung with an audible click at "
            "each step, then rests in a cup at the bottom until the next flip.\n"
            "Why it is new: The rungs are cams that hold the bead until the flip "
            "passes vertical, so the drop is paced by geometry rather than by "
            "chance.\n"
            "Closest existing things, and how this differs:\n"
            "- Jacob's ladder: No ribbons or flipping tiles; a single captive bead "
            "steps down fixed cam rungs.\n"
            "- Marble run: Nothing is assembled and the bead never leaves the body; "
            "the flip is the reset.\n"
            "Fits the Inventor's Taste by: Motion comes from geometry and gravity "
            "alone\n"
            "Steers clear of: Decorative objects with no repeatable interaction\n"
            "Printed parts (estimate): 2\n"
            "\n"
            "Match should bind Pico Press, who dreamed this, unless the Taste "
            "rejects the final concept."
        )
        self.assertEqual(brief, expected)
        self.assertEqual(
            render_brief(idea, inventor_name="Pico Press", inventor_id="pico-press"),
            brief,
        )

    def test_brief_rejects_invalid_inventor_identity(self):
        with self.assertRaises(ContractError):
            render_brief(sample_idea(), inventor_name="", inventor_id="pico-press")
        with self.assertRaises(ContractError):
            render_brief(sample_idea(), inventor_name="Pico", inventor_id="Pico Press")


class NoveltyReportTest(unittest.TestCase):
    def test_round_trip_and_ordering_rules(self):
        near = (
            NoveltyNeighbor(source="toys/a", title="A", similarity=0.4),
            NoveltyNeighbor(source="toys/b", title="B", similarity=0.1),
        )
        report = NoveltyReport(
            status="new", max_similarity=0.4, nearest=near, reason="nearest is A"
        )
        self.assertEqual(NoveltyReport.parse(report.to_dict()), report)
        with self.assertRaises(ContractError):
            NoveltyReport(
                status="new", max_similarity=0.4, nearest=near[::-1], reason="x"
            )
        with self.assertRaises(ContractError):
            NoveltyReport(status="new", max_similarity=0.3, nearest=near, reason="x")
        with self.assertRaises(ContractError):
            NoveltyReport(status="new", max_similarity=0.1, nearest=(), reason="x")
        with self.assertRaises(ContractError):
            NoveltyReport(status="maybe", max_similarity=0.0, nearest=(), reason="x")
        with self.assertRaises(ContractError):
            NoveltyReport(status="new", max_similarity=0.0, nearest=near * 2, reason="x")
        with self.assertRaises(ContractError):
            NoveltyNeighbor(source="toys/a", title="A", similarity=1.5)


class SealedDaydreamTest(unittest.TestCase):
    def test_round_trip_and_identity(self):
        sealed = sample_sealed()
        raw = sealed.to_dict()
        self.assertEqual(raw["kind"], DAYDREAM_SEAL_KIND)
        self.assertEqual(raw["schema_version"], 1)
        self.assertEqual(SealedDaydream.parse(json.loads(json.dumps(raw))), sealed)
        self.assertEqual(
            sealed.sha256,
            hashlib.sha256(canonical_json(raw).encode("utf-8")).hexdigest(),
        )
        self.assertEqual(sealed.session, {"status": "completed", "used_web_search": True})
        self.assertIsNot(sealed.session, raw["session"])

    def test_idea_sha256_and_brief_must_match_the_idea(self):
        with self.assertRaisesRegex(ContractError, "idea_sha256"):
            sample_sealed(idea_sha256="b" * 64)
        with self.assertRaisesRegex(ContractError, "brief"):
            sample_sealed(brief="Build something else.")
        with self.assertRaisesRegex(ContractError, "brief"):
            sample_sealed(inventor_name="Someone Else")

    def test_parse_rejects_unknown_keys_and_bad_fields(self):
        raw = sample_sealed().to_dict()
        raw["extra"] = 1
        with self.assertRaisesRegex(ContractError, "extra"):
            SealedDaydream.parse(raw)
        raw = sample_sealed().to_dict()
        raw["created_at"] = "2026-09-02 10:15:00"
        with self.assertRaises(ContractError):
            SealedDaydream.parse(raw)
        for field, value in (
            ("daydream_id", "wish-20260902-101500-0badcafe"),
            ("inventor_id", "Sample"),
            ("manager_id", "Codex!"),
            ("taste_sha256", "abc"),
            ("seed", {}),
            ("session", "completed"),
            ("kind", DAYDREAM_IDEA_KIND),
        ):
            with self.subTest(field=field), self.assertRaises(ContractError):
                sample_sealed(**{field: value})
        self.assertEqual(sample_novelty().status, "new")


if __name__ == "__main__":
    unittest.main()


class HeldFormTest(unittest.TestCase):
    def test_held_form_is_optional_and_absent_ideas_keep_their_identity(self):
        from tests.daydream.support import sample_idea_dict
        from workshop.daydream.contracts import Idea, render_brief

        with_form = sample_idea_dict()
        without = dict(with_form)
        del without["held_form"]
        parsed = Idea.parse(without)
        self.assertIsNone(parsed.held_form)
        self.assertNotIn("held_form", parsed.to_dict())
        self.assertEqual(Idea.parse(parsed.to_dict()), parsed)
        self.assertNotEqual(parsed.sha256, Idea.parse(with_form).sha256)
        brief = render_brief(Idea.parse(with_form), inventor_name="Sample", inventor_id="sample")
        self.assertIn("\nWhat it looks like: A palm-sized", brief)
        self.assertNotIn("What it looks like", render_brief(parsed, inventor_name="Sample", inventor_id="sample"))

    def test_held_form_is_bounded(self):
        from tests.daydream.support import sample_idea_dict
        from workshop.daydream.contracts import Idea
        from workshop.errors import ContractError

        raw = sample_idea_dict()
        raw["held_form"] = "x" * 241
        with self.assertRaisesRegex(ContractError, "held_form"):
            Idea.parse(raw)
        raw["held_form"] = "two\nlines"
        with self.assertRaisesRegex(ContractError, "held_form"):
            Idea.parse(raw)
        raw["held_form"] = ""
        with self.assertRaisesRegex(ContractError, "held_form"):
            Idea.parse(raw)


class VerdictTest(unittest.TestCase):
    def test_verdict_round_trip_and_bounds(self):
        from tests.daydream.support import build_verdict_dict, sample_sealed, sample_verdict
        from workshop.daydream.contracts import SealedDaydream, Verdict
        from workshop.errors import ContractError

        for decision in ("build", "dream-again"):
            verdict = sample_verdict(decision)
            self.assertEqual(Verdict.parse(verdict.to_dict()), verdict)
            sealed = sample_sealed(verdict=verdict)
            self.assertEqual(SealedDaydream.parse(sealed.to_dict()), sealed)
            self.assertEqual(sealed.to_dict()["verdict"]["decision"], decision)
        self.assertNotIn("verdict", sample_sealed().to_dict())
        bad = build_verdict_dict("dream-again")
        bad["risks"] = []
        with self.assertRaisesRegex(ContractError, "at least one risk"):
            Verdict.parse(bad)
        bad = build_verdict_dict()
        bad["checks"]["travel_is_large"] = False
        with self.assertRaisesRegex(ContractError, "build verdict requires every check"):
            Verdict.parse(bad)
        bad = build_verdict_dict()
        del bad["checks"]["worth_owning"]
        with self.assertRaisesRegex(ContractError, "checks must hold exactly"):
            Verdict.parse(bad)
        bad = build_verdict_dict()
        bad["checks"]["worth_owning"] = "yes"
        with self.assertRaisesRegex(ContractError, "must be true or false"):
            Verdict.parse(bad)
        self.assertEqual(
            sample_verdict("dream-again").failed_checks,
            ("moving_part_visible_in_both_states",),
        )
        self.assertEqual(sample_verdict("build").failed_checks, ())
        bad = build_verdict_dict()
        bad["confidence"] = 1.5
        with self.assertRaises(ContractError):
            Verdict.parse(bad)
        bad = build_verdict_dict()
        bad["decision"] = "maybe"
        with self.assertRaises(ContractError):
            Verdict.parse(bad)
        bad = build_verdict_dict()
        bad["extra"] = 1
        with self.assertRaisesRegex(ContractError, "unknown keys"):
            Verdict.parse(bad)

    def test_v2_verdict_is_conjunctive_and_hash_bound(self):
        from workshop.daydream.contracts import THESIS_VERDICT_CHECKS, Verdict

        raw = build_thesis_verdict_dict()
        verdict = Verdict.parse(raw)
        self.assertEqual(verdict.to_dict(), raw)
        self.assertEqual(tuple(verdict.checks), THESIS_VERDICT_CHECKS)
        self.assertEqual(verdict.failed_checks, ())
        for field, value in (
            ("daydream_id", "wish-20260902-101500-0badcafe"),
            ("idea_sha256", "abc"),
            ("taste_sha256", "abc"),
            ("route", "turbo"),
        ):
            malformed = build_thesis_verdict_dict()
            malformed[field] = value
            with self.subTest(field=field), self.assertRaises(ContractError):
                Verdict.parse(malformed)
        malformed = build_thesis_verdict_dict()
        malformed["checks"]["opportunity_grounded"] = False
        with self.assertRaisesRegex(ContractError, "build verdict requires every check"):
            Verdict.parse(malformed)
