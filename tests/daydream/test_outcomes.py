import json
import stat
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tests.daydream.support import sample_sealed
from workshop.daydream.native import wish_from_daydream
from workshop.daydream.outcomes import (
    OutcomeSummary,
    RunOutcomeMemory,
    outcome_path,
    read_outcomes,
    remember_resumed_outcome,
    remember_run_outcome,
    render_outcome_summary_markdown,
    render_outcomes_markdown,
    summarize_outcomes,
)
from workshop.errors import ContractError
from workshop.wish import Wish


MOMENT = datetime(2026, 9, 3, 8, 0, 0, tzinfo=timezone.utc)


class OutcomeMemoryTest(unittest.TestCase):
    def test_receipt_is_allowlisted_hash_bound_and_rendered_as_fact(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = (Path(temporary) / "home").resolve()
            wish = wish_from_daydream(sample_sealed(), wish_id="wish-outcome-one")
            receipt = {
                "product_id": "wish-outcome-one",
                "effort": "quest",
                "manager": "codex",
                "status": "complete",
                "stage": "release",
                "revision": 4,
                "round": 2,
                "wish_sha256": "a" * 64,
                "checkpoint_sha256": "b" * 64,
                "publication": {
                    "status": "public",
                    "verified": True,
                    "design_id": "factory-design-one",
                    "slug": "ladder-drop",
                    "page_url": "https://factory.invalid/private-path",
                },
                "lineage": {
                    "schema_version": 1,
                    "wish_id": "wish-outcome-one",
                    "wish_sha256": "a" * 64,
                    "origin": {
                        "source": "workshop-daydream",
                        "inventor_id": "sample",
                        "daydream_id": wish.context["daydream_id"],
                        "idea_sha256": wish.context["idea_sha256"],
                        "daydream_sha256": wish.context.get("daydream_sha256"),
                        "provenance_sha256": wish.context.get("provenance_sha256"),
                        "route": wish.context.get("route"),
                    },
                    "invented": {
                        "wish_sha256": "a" * 64,
                        "concept_sha256": "c" * 64,
                        "invented_sha256": "d" * 64,
                    },
                    "made": {
                        "wish_sha256": "a" * 64,
                        "invented_sha256": "d" * 64,
                        "made_sha256": "e" * 64,
                        "product_artifact_sha256": "f" * 64,
                    },
                    "playtested": None,
                    "release": {
                        "release_sha256": "1" * 64,
                        "made_sha256": "e" * 64,
                        "playtested_sha256": "2" * 64,
                        "product_artifact_sha256": "f" * 64,
                    },
                },
                "needs": ["Verify the tactile response on the next physical revision."],
                "session": {"untrusted_prose": "must not enter memory"},
            }
            self.assertTrue(
                remember_run_outcome(wish, receipt=receipt, moment=MOMENT, home=home)
            )
            path = outcome_path("sample", home=home)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            outcomes = read_outcomes(path)
            self.assertEqual(len(outcomes), 1)
            outcome = outcomes[0]
            self.assertEqual(outcome.route, "quest")
            self.assertEqual(outcome.run_status, "complete")
            self.assertEqual(outcome.publication_status, "public")
            self.assertEqual(outcome.concept_sha256, "c" * 64)
            self.assertEqual(outcome.made_sha256, "e" * 64)
            self.assertEqual(outcome.release_sha256, "1" * 64)
            self.assertEqual(outcome.factory_design_id, "factory-design-one")
            self.assertEqual(outcome.factory_slug, "ladder-drop")
            self.assertEqual(
                outcome.needs,
                ("Verify the tactile response on the next physical revision.",),
            )
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn("session", raw)
            self.assertNotIn("page_url", raw)
            self.assertEqual(RunOutcomeMemory.parse(raw), outcome)
            self.assertIn(
                "host-observed facts, not Judge predictions",
                render_outcomes_markdown(outcomes),
            )
            rendered = render_outcomes_markdown(outcomes)
            self.assertIn("Exact lineage: concept=cccccccccccc", rendered)
            self.assertIn("Observed run need: Verify the tactile response", rendered)
            raw["stage"] = "make"
            with self.assertRaisesRegex(ContractError, "event_sha256"):
                RunOutcomeMemory.parse(raw)

    def test_schema_one_remains_readable_without_v2_lineage(self):
        legacy = RunOutcomeMemory(
            schema_version=1,
            daydream_id="daydream-20260903-080000-00000001",
            idea_sha256="a" * 64,
            wish_id="wish-legacy",
            recorded_at="2026-09-03T03:08:00Z",
            result="receipt",
            route="spark",
            manager="codex",
            run_status="complete",
            stage="release",
            revision=1,
            round=1,
            wish_sha256="b" * 64,
            checkpoint_sha256="c" * 64,
            publication_status="public",
            publication_verified=True,
            error_type=None,
            error_detail=None,
        )
        self.assertEqual(RunOutcomeMemory.parse(legacy.to_dict()), legacy)

    def test_resume_uses_host_verified_origin_and_direct_wish_is_ignored(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = (Path(temporary) / "home").resolve()
            wish = wish_from_daydream(sample_sealed(), wish_id="wish-resumed")
            receipt = {
                "product_id": wish.product_id,
                "wish_sha256": "a" * 64,
                "effort": "spark",
                "manager": "codex",
                "status": "complete",
                "stage": "release",
                "revision": 3,
                "round": 1,
                "checkpoint_sha256": "b" * 64,
                "publication": {"status": "public", "verified": True},
                "lineage": {
                    "schema_version": 1,
                    "wish_id": wish.product_id,
                    "wish_sha256": "a" * 64,
                    "origin": {
                        "source": "workshop-daydream",
                        "inventor_id": wish.context["inventor_id"],
                        "daydream_id": wish.context["daydream_id"],
                        "idea_sha256": wish.context["idea_sha256"],
                        "daydream_sha256": wish.context.get("daydream_sha256"),
                        "provenance_sha256": wish.context.get("provenance_sha256"),
                        "route": wish.context.get("route"),
                    },
                    "invented": None,
                    "made": None,
                    "playtested": None,
                    "release": None,
                },
            }
            self.assertTrue(remember_resumed_outcome(receipt, moment=MOMENT, home=home))
            self.assertEqual(len(read_outcomes(outcome_path("sample", home=home))), 1)
            receipt["lineage"] = {**receipt["lineage"], "origin": None}
            self.assertFalse(remember_resumed_outcome(receipt, moment=MOMENT, home=home))

    def test_error_is_distinct_and_direct_user_wish_is_not_recorded(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = (Path(temporary) / "home").resolve()
            wish = wish_from_daydream(sample_sealed(), wish_id="wish-outcome-two")
            self.assertTrue(
                remember_run_outcome(
                    wish,
                    error=RuntimeError("native turn ended before a receipt"),
                    route="spark",
                    manager="codex",
                    moment=MOMENT,
                    home=home,
                )
            )
            outcome = read_outcomes(outcome_path("sample", home=home))[0]
            self.assertEqual(outcome.result, "error")
            self.assertEqual(outcome.error_type, "RuntimeError")
            self.assertIn("ended before a receipt", render_outcomes_markdown((outcome,)))
            direct = Wish.create("wish-direct", "a person-authored Wish")
            self.assertFalse(
                remember_run_outcome(
                    direct,
                    receipt={"status": "complete"},
                    moment=MOMENT,
                    home=home,
                )
            )


def _event(wish_id, *, result="receipt", route="spark", run_status="complete",
           stage="release", publication_status=None, daydream_id=None,
           recorded_at="2026-09-03T08:00:00Z"):
    error = result != "receipt"
    return RunOutcomeMemory(
        daydream_id=daydream_id or "daydream-20260902-101500-0badcafe",
        idea_sha256="a" * 64,
        wish_id=wish_id,
        recorded_at=recorded_at,
        result=result,
        route=route,
        manager="codex",
        run_status=None if error else run_status,
        stage=None if error else stage,
        revision=None,
        round=None,
        wish_sha256=None,
        checkpoint_sha256=None,
        publication_status=None if error else publication_status,
        publication_verified=None if error else (publication_status == "public"),
        error_type="RuntimeError" if error else None,
        error_detail="the session ended" if error else None,
    )


class OutcomeSummaryTest(unittest.TestCase):
    def test_summary_counts_each_run_by_its_latest_event(self):
        second_idea = "daydream-20260903-090000-0badf00d"
        third_idea = "daydream-20260903-100000-0badbeef"
        events = (
            # One idea, one run, published.
            _event("wish-one", publication_status="public"),
            # Second idea: interrupted first, then a resume receipt failed at Make.
            _event("wish-two", result="interrupted", daydream_id=second_idea),
            _event("wish-two", run_status="failed", stage="make", daydream_id=second_idea,
                   recorded_at="2026-09-03T09:00:00Z"),
            # Second idea built again on Forge and published.
            _event("wish-two-again", route="forge", publication_status="public",
                   daydream_id=second_idea),
            # Third idea: the build session died without a receipt.
            _event("wish-three", result="error", daydream_id=third_idea),
            # Third idea rebuilt and now waiting for a manual Release step.
            _event("wish-three-again", run_status="waiting", stage="release",
                   daydream_id=third_idea),
        )
        summary = summarize_outcomes(events)
        self.assertEqual(summary.theses, 3)
        self.assertEqual(summary.runs, 5)
        self.assertEqual(summary.published, 2)
        self.assertEqual(summary.receipts, (("failed", "make", 1), ("waiting", "release", 1)))
        self.assertEqual(summary.errors, 1)
        self.assertEqual(summary.interrupted, 0)
        self.assertEqual(summary.by_route, (("forge", 1, 1), ("spark", 4, 1)))
        self.assertEqual(
            summary.to_dict()["by_route"],
            [
                {"route": "forge", "runs": 1, "published": 1},
                {"route": "spark", "runs": 4, "published": 1},
            ],
        )
        rendered = render_outcomes_markdown(events)
        self.assertIn("host-observed facts, not Judge predictions", rendered)
        self.assertIn(
            "- 3 theses reached 5 runs: 2 published, 1 failed at make, "
            "1 waiting at release, 1 errored.",
            rendered,
        )
        self.assertIn("- By route: forge 1 runs, 1 published; spark 4 runs, 1 published.", rendered)
        self.assertLess(rendered.index("Yield so far"), rendered.index("Every recorded event"))
        self.assertLess(rendered.index("Every recorded event"), rendered.index("wish-one"))

    def test_empty_log_has_no_yield_section_and_rejects_foreign_items(self):
        self.assertEqual(summarize_outcomes(()), OutcomeSummary(0, 0, 0, (), 0, 0, ()))
        self.assertEqual(render_outcome_summary_markdown(summarize_outcomes(())), "")
        self.assertNotIn("Yield so far", render_outcomes_markdown(()))
        with self.assertRaisesRegex(ContractError, "RunOutcomeMemory"):
            summarize_outcomes(({"wish_id": "wish"},))


if __name__ == "__main__":
    unittest.main()
