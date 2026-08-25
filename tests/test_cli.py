import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import inventor_workshop
from inventor_workshop.cli import (
    _inventor_process_environment,
    _publish_inventor_draft,
    _run_inventor,
    main,
    parser,
)
from inventor_workshop.manager import TasteFit, create_shortlist
from inventor_workshop.models import Receipt


class CliTest(unittest.TestCase):
    def test_selected_inventor_receives_only_its_factory_username(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assignment = SimpleNamespace(
                entrypoint=("python3", "profile.py"),
                wish=SimpleNamespace(product_id="wish-one", objective="A tiny world"),
                playtest_rounds=4,
                decision=SimpleNamespace(
                    selected=SimpleNamespace(
                        card=SimpleNamespace(inventor_id="eve", root=root)
                    )
                ),
            )
            observed = {}

            def runner(command, **kwargs):
                observed["command"] = command
                observed.update(kwargs)
                return subprocess.CompletedProcess(command, 0, stdout='{"status":"waiting"}')

            with mock.patch.dict(
                "os.environ", {"FACTORY_PASSWORD": "fixture-password"}, clear=False
            ):
                result = _run_inventor(assignment, runner=runner)

            self.assertEqual(result["status"], "waiting")
            self.assertEqual(observed["env"]["FACTORY_USERNAME"], "eve")
            self.assertEqual(observed["env"]["FACTORY_PASSWORD"], "fixture-password")
            self.assertEqual(observed["env"]["WORKSHOP_AGENT_WORKERS"], "codex")
            self.assertNotIn("fixture-password", observed["command"])

    def test_worker_environment_without_factory_secret_has_no_partial_login(self):
        with mock.patch.dict(
            "os.environ", {"FACTORY_USERNAME": "wrong-account"}, clear=True
        ):
            environment = _inventor_process_environment("alice")
        self.assertNotIn("FACTORY_USERNAME", environment)
        self.assertNotIn("FACTORY_PASSWORD", environment)
        self.assertEqual(environment["WORKSHOP_AGENT_WORKERS"], "codex")

    def test_explicit_publish_uses_the_exact_durable_draft(self):
        page_url = "https://www.autonomous.ai/factory/product/pocket-duel"
        draft = Receipt.from_design(
            {
                "id": "design-pocket-duel",
                "slug": "pocket-duel",
                "owner_id": "owner-alice",
                "root_id": "design-pocket-duel",
                "current_history_id": "history-one",
                "published_history_id": None,
                "status": "draft",
                "project_url": "https://cdn.autonomous.ai/projects/history-one/",
                "listing": None,
            },
            "f" * 64,
            "a" * 64,
        )
        draft_value = draft.to_dict()
        draft_value["details"] = {**draft_value["details"], "page_url": page_url}
        draft = Receipt.from_dict(draft_value)
        public_value = draft.to_dict()
        public_value["status"] = "public"
        public_value["published_history_id"] = "history-one"
        public = Receipt.from_dict(public_value)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assignment = SimpleNamespace(
                wish=SimpleNamespace(product_id="wish-one"),
                decision=SimpleNamespace(
                    selected=SimpleNamespace(
                        card=SimpleNamespace(inventor_id="alice", root=root)
                    )
                ),
            )
            store = mock.Mock()
            store.latest_publish_intent.return_value = {
                "receipt": draft.to_dict()
            }
            session = object()
            transition = mock.Mock()
            transition.publish.return_value = public
            with mock.patch.dict(
                "os.environ", {"FACTORY_PASSWORD": "fixture-password"}, clear=True
            ):
                publication = _publish_inventor_draft(
                    assignment,
                    {"page_url": page_url, "artifact_sha256": "a" * 64},
                    store_factory=mock.Mock(return_value=store),
                    session_factory=mock.Mock(return_value=session),
                    transition_factory=mock.Mock(return_value=transition),
                )
        transition.publish.assert_called_once_with(draft)
        self.assertEqual(publication["status"], "public")
        self.assertTrue(publication["verified"])
        self.assertEqual(publication["page_url"], page_url)

    def test_publish_waits_truthfully_until_instructions_has_a_draft(self):
        assignment = SimpleNamespace(
            wish=SimpleNamespace(product_id="wish-one"),
            decision=SimpleNamespace(
                selected=SimpleNamespace(
                    card=SimpleNamespace(inventor_id="alice", root=Path.cwd())
                )
            ),
        )
        publication = _publish_inventor_draft(assignment, {"job": "make"})
        self.assertEqual(publication["status"], "waiting")
        self.assertIn("Instructions", publication["reason"])

    def test_wish_is_the_simple_customer_command(self):
        root = Path(__file__).resolve().parents[1]

        class FakeSemanticManager:
            judge_identity = "fixture-description-matcher"
            judge_version = "1.0.0"
            judge_config_sha256 = "a" * 64

            def retrieve(self, context):
                return create_shortlist(
                    context,
                    ("bob",),
                    retriever="fixture-description-matcher",
                    retriever_version="1.0.0",
                    rationale="Bob turns a playful movement into a real mechanism.",
                )

            def judge(self, context):
                finalist = context.finalists[0]
                return (
                    TasteFit(
                        inventor_id="bob",
                        taste_sha256=finalist.taste.sha256,
                        score=94,
                        accepted=True,
                        explanation=(
                            "Bob turns a playful movement into a real mechanism."
                        ),
                    ),
                )

        output = StringIO()
        with mock.patch(
            "inventor_workshop.cli.CodexSemanticManager",
            return_value=FakeSemanticManager(),
        ), mock.patch(
            "inventor_workshop.cli._run_inventor",
            return_value={
                "status": "waiting",
                "job": "make",
                "needs": [
                    {
                        "job": "make",
                        "capability": "mechanical-designer",
                        "reason": "The mechanical designer is not connected yet.",
                        "instructions": "Connect it.",
                    }
                ],
            },
        ), redirect_stdout(output):
            result = main(
                (
                    "wish",
                    "a",
                    "wind-up",
                    "version",
                    "of",
                    "my",
                    "dog",
                    "--root",
                    str(root),
                    "--json",
                )
            )
        self.assertEqual(result, 0)
        receipt = json.loads(output.getvalue())
        self.assertRegex(
            receipt["wish"]["product_id"],
            r"^wish-\d{8}-\d{6}-[0-9a-f]{8}$",
        )
        self.assertEqual(
            receipt["wish"]["objective"], "a wind-up version of my dog"
        )
        self.assertEqual(receipt["match"]["inventor_id"], "bob")
        self.assertEqual(receipt["match"]["score"], 94)
        self.assertEqual(receipt["result"]["status"], "waiting")

    def test_source_version_matches_project_metadata(self):
        project = Path(__file__).resolve().parents[1] / "pyproject.toml"
        in_project = False
        declared = None
        for raw_line in project.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line == "[project]":
                in_project = True
                continue
            if in_project and line.startswith("["):
                break
            if in_project and line.startswith("version = "):
                declared = line.removeprefix("version = ").strip('"')
                break
        self.assertEqual(declared, inventor_workshop.__version__)

    def test_workshop_is_the_canonical_cli_name(self):
        self.assertEqual(parser().prog, "workshop")
        project = (
            Path(__file__).resolve().parents[1] / "pyproject.toml"
        ).read_text(encoding="utf-8")
        self.assertIn('inventor-workshop = "inventor_workshop.cli:main"', project)
        self.assertIn('workshop = "inventor_workshop.cli:main"', project)
        self.assertNotIn("inventor-core =", project)

    def test_audit_does_not_create_or_validate_a_missing_database(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "missing.sqlite"
            with redirect_stderr(StringIO()):
                result = main(("audit-state", str(database), "typo"))
            self.assertEqual(result, 2)
            self.assertFalse(database.exists())

    def test_new_places_an_inventor_in_the_repository_collection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "inventors").mkdir()
            with redirect_stdout(StringIO()):
                result = main(
                    (
                        "new",
                        "word-games",
                        "--name",
                        "Ada",
                        "--niche",
                        "printable word games",
                        "--lane",
                        "invented-games",
                        "--level",
                        "taste-only",
                        "--root",
                        str(root),
                    )
                )
            self.assertEqual(result, 0)
            self.assertTrue((root / "inventors/word-games/inventor.json").is_file())
            self.assertFalse(
                (root / "inventors/word-games/src/word_games/inventor.py").exists()
            )

    def test_new_accepts_the_inventor_collection_as_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            with redirect_stdout(StringIO()):
                result = main(
                    (
                        "new",
                        "deduction-games",
                        "--name",
                        "Ada",
                        "--niche",
                        "printable deduction games",
                        "--lane",
                        "invented-games",
                        "--level",
                        "custom-make",
                        "--root",
                        str(collection),
                    )
                )
            self.assertEqual(result, 0)
            self.assertTrue((collection / "deduction-games/inventor.json").is_file())
            hook = collection / "deduction-games/src/deduction_games/inventor.py"
            self.assertIn("def make(", hook.read_text(encoding="utf-8"))
            self.assertNotIn("def playtest(", hook.read_text(encoding="utf-8"))

    def test_inventors_lists_taste_identity_not_legacy_manifest_prose(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            with redirect_stdout(StringIO()):
                result = main(
                    (
                        "new",
                        "science-toys",
                        "--name",
                        "Ada",
                        "--niche",
                        "personal orbit models",
                        "--lane",
                        "holdable-science",
                        "--root",
                        str(collection),
                    )
                )
            self.assertEqual(result, 0)

            output = StringIO()
            with redirect_stdout(output):
                result = main(("inventors", "--root", str(collection), "--json"))
            self.assertEqual(result, 0)
            records = json.loads(output.getvalue())
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["id"], "science-toys")
            self.assertEqual(records[0]["name"], "Ada")
            self.assertEqual(records[0]["status"], "experimental")
            self.assertIn("personal orbit models", records[0]["description"])
            manifest = json.loads(
                (collection / "science-toys/inventor.json").read_text(encoding="utf-8")
            )
            self.assertNotIn("name", manifest)
            self.assertNotIn("niche", manifest)
            self.assertNotIn("summary", manifest)
            self.assertNotIn("autonomy", manifest)

    def test_new_help_is_lane_and_level_not_legacy_template(self):
        command = parser()
        subcommands = next(
            action for action in command._actions if hasattr(action, "choices") and action.choices
        )
        help_text = subcommands.choices["new"].format_help()
        self.assertIn("--lane", help_text)
        self.assertIn("classics-made-yours", help_text)
        self.assertIn("invented-games", help_text)
        self.assertIn("moving-machines", help_text)
        self.assertIn("holdable-science", help_text)
        self.assertIn("little-worlds", help_text)
        for old_lane in (
            "games-puzzles",
            "table-game",
            "desk-toy",
            "model-character",
            "puzzle-keepsake",
        ):
            self.assertNotIn(old_lane, help_text)
        self.assertIn("--level", help_text)
        self.assertIn("taste-only", help_text)
        self.assertIn("custom-make", help_text)
        self.assertIn("custom-playtest", help_text)
        self.assertNotIn("--template", help_text)
        self.assertNotIn("physical-product", help_text)

    def test_hidden_legacy_template_maps_to_invented_games(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            with redirect_stdout(StringIO()):
                result = main(
                    (
                        "new",
                        "legacy-games",
                        "--name",
                        "Ada",
                        "--niche",
                        "printable games",
                        "--template",
                        "board-game",
                        "--root",
                        str(collection),
                    )
                )
            self.assertEqual(result, 0)
            manifest = (collection / "legacy-games/inventor.json").read_text(
                encoding="utf-8"
            )
            self.assertIn('"invented-games"', manifest)

    def test_new_requires_a_toy_lane(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            error = StringIO()
            with redirect_stderr(error):
                result = main(
                    (
                        "new",
                        "missing-lane",
                        "--name",
                        "Ada",
                        "--niche",
                        "printable games",
                        "--root",
                        str(collection),
                    )
                )
            self.assertEqual(result, 2)
            self.assertIn("inventor lane must be one of", error.getvalue())

    def test_skills_command_exposes_canonical_workshop_tools(self):
        skills_root = Path(__file__).resolve().parents[1] / "skills"
        output = StringIO()
        with redirect_stdout(output):
            result = main(("skills", "list", "--root", str(skills_root)))
        self.assertEqual(result, 0)
        self.assertIn("product-to-cad", output.getvalue())
        output = StringIO()
        with redirect_stdout(output):
            result = main(("skills", "path", "--root", str(skills_root)))
        self.assertEqual(result, 0)
        self.assertEqual(Path(output.getvalue().strip()), skills_root.resolve())


if __name__ == "__main__":
    unittest.main()
