import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from inventor_workshop.cli import main
from inventor_workshop.manager import TasteFit, create_shortlist


class WorkshopWishProfileSubprocessTest(unittest.TestCase):
    def test_wish_uses_manager_engine_without_profile_and_waits_on_shared_research(self):
        repository = Path(__file__).resolve().parents[1]
        canonical_profile = repository / "inventors" / "alice"

        class FakeSemanticManager:
            judge_identity = "fixture-semantic-manager"
            judge_version = "1.0.0"
            judge_config_sha256 = "a" * 64

            def retrieve(self, context):
                return create_shortlist(
                    context,
                    ("alice",),
                    retriever=self.judge_identity,
                    retriever_version=self.judge_version,
                    rationale="Alice preserves a known game's rules while making its pieces personal.",
                )

            def judge(self, context):
                finalist = context.finalists[0]
                return (
                    TasteFit(
                        inventor_id="alice",
                        taste_sha256=finalist.taste.sha256,
                        score=97,
                        accepted=True,
                        explanation="Alice preserves the game and makes the physical set belong to this Wish.",
                    ),
                )

        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            copied_profile = temporary_root / "inventors" / "alice"
            copied_profile.mkdir(parents=True)
            for name in ("TASTE.md", "inventor.json", "profile.py"):
                shutil.copy2(canonical_profile / name, copied_profile / name)

            marker = temporary_root / "shared-research-called.json"
            profile_marker = temporary_root / "profile-executed"
            (copied_profile / "profile.py").write_text(
                "from pathlib import Path\n"
                "Path(%r).write_text('profile must not execute')\n"
                % str(profile_marker),
                encoding="utf-8",
            )

            def offline_research(provider, context):
                del provider
                marker.write_text(
                    json.dumps(
                        {
                            "lane": context.blueprint.lane,
                            "taste_sha256": context.taste.sha256,
                            "wish": context.wish.to_dict(),
                        },
                        sort_keys=True,
                    ),
                    encoding="utf-8",
                )
                from inventor_workshop.agent_invent import InventResearchUnavailable

                raise InventResearchUnavailable(
                    "deterministic offline research boundary"
                )

            output = StringIO()
            objective = "a moonlit chess set shaped by Linh's mountain memories"
            with mock.patch(
                "inventor_workshop.cli.CodexSemanticManager",
                return_value=FakeSemanticManager(),
            ), mock.patch(
                "inventor_workshop.agent_invent.PublicHTTPResearchProvider.__call__",
                new=offline_research,
            ), mock.patch.dict(
                os.environ, {"WORKSHOP_AGENT_WORKERS": "codex"}, clear=False
            ), redirect_stdout(output):
                exit_code = main(
                    (
                        "wish",
                        objective,
                        "--root",
                        str(temporary_root),
                        "--json",
                    )
                )

            self.assertEqual(exit_code, 0)
            receipt = json.loads(output.getvalue())
            result = receipt["result"]
            self.assertEqual(receipt["wish"]["objective"], objective)
            self.assertEqual(receipt["wish"]["context"], {"source": "workshop-cli"})
            self.assertEqual(receipt["match"]["inventor_id"], "alice")
            self.assertEqual(result["status"], "waiting")
            self.assertEqual(result["job"], "invent")
            self.assertEqual(
                [need["capability"] for need in result["needs"]],
                ["source-backed-design-research"],
            )
            self.assertIn("research provider", result["needs"][0]["reason"])
            self.assertIn("trusted research provider", result["needs"][0]["instructions"])
            self.assertNotIn("alice", result["needs"][0]["capability"])
            self.assertEqual(
                result["manager_assignment"]["assignment_sha256"],
                receipt["assignment_sha256"],
            )
            self.assertEqual(
                result["manager_assignment"]["decision_sha256"],
                receipt["match"]["decision_sha256"],
            )
            self.assertFalse(profile_marker.exists())

            observed = json.loads(marker.read_text(encoding="utf-8"))
            self.assertEqual(observed["wish"], receipt["wish"])
            self.assertEqual(observed["lane"], "classics-made-yours")
            self.assertRegex(observed["taste_sha256"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
