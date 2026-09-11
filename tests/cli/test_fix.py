import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

from cli.main import main, parser
from workshop.errors import StateConflict
from workshop.wish import Wish


class FixCommandTest(unittest.TestCase):
    def test_prompt_file_and_run_controls_reach_host(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fix.txt"
            prompt = "Fix recessed dice pips.\nKeep dimensions.\n"
            path.write_text(prompt)
            wish = Wish.create("wish-new", prompt, context={"inventor_id": "mara-masque"})
            receipt = {"status": "waiting", "stage": "make", "product_id": "wish-new"}
            with patch("workshop.workflow.revision.prepare_revision", return_value=(wish, b"snapshot")) as prepare, patch("cli.main.start_native_run", return_value=receipt) as start, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                result = main(["fix", "toys/original", "--prompt-file", str(path),
                               "--model", "astra", "--effort", "high", "--max-tokens", "10000000",
                               "--turn-minutes", "45", "--json", "--strict"])
            self.assertEqual(result, 1)
            prepare.assert_called_once_with(Path("toys/original"), prompt)
            self.assertEqual(start.call_args.args, (wish,))
            options = start.call_args.kwargs
            self.assertEqual(options["effort"], "spark")
            self.assertEqual(options["revision_snapshot"], b"snapshot")
            self.assertEqual(options["manager_model"], "gpt-6-astra")
            self.assertEqual(options["manager_reasoning_effort"], "high")
            self.assertEqual(options["max_tokens"], 10000000)
            self.assertEqual(options["turn_seconds"], 2700)
            self.assertFalse(options["github_publish_requested"])

    def test_invalid_source_never_launches(self):
        with patch("workshop.workflow.revision.prepare_revision", side_effect=StateConflict("archive changed")), patch("cli.main.start_native_run") as start, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertNotEqual(main(["fix", "bad", "--prompt", "Fix"]), 0)
        start.assert_not_called()

    def test_requires_exactly_one_prompt(self):
        for arguments in (["fix", "toy"], ["fix", "toy", "--prompt", "Fix", "--prompt-file", "fix.txt"]):
            with self.subTest(arguments=arguments), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    parser().parse_args(arguments)
