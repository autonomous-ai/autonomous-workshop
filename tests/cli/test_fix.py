import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

from cli.main import main, parser
from workshop.errors import StateConflict
from workshop.wish import Wish

from tests.cli.test_cli import _contract_block, _contract_text


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


class FixContractCommandTest(unittest.TestCase):
    """``workshop fix --contract`` (issue #52, ADR 0072 Delivery 2)."""

    def test_a_well_formed_contract_seals_into_the_correction_and_freezes_contract_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            contract_path = Path(directory) / "CONTRACT.md"
            contract_path.write_text(_contract_text(), encoding="utf-8")
            prompt = "Widen the sun den."
            receipt = {"status": "waiting", "stage": "make", "product_id": "wish-new"}

            def fake_prepare_revision(source, prompt_arg, **kwargs):
                context = {"inventor_id": "mara-masque"}
                design_contract = kwargs.get("design_contract")
                if design_contract is not None:
                    context["design_contract"] = design_contract
                return Wish.create("wish-new", prompt_arg, context=context), b"snapshot"

            stdout = io.StringIO()
            with patch(
                "workshop.workflow.revision.prepare_revision",
                side_effect=fake_prepare_revision,
            ) as prepare, patch(
                "cli.main.start_native_run", return_value=receipt
            ), redirect_stdout(stdout), redirect_stderr(io.StringIO()):
                result = main(
                    ["fix", "toys/original", "--prompt", prompt,
                     "--contract", str(contract_path)]
                )
            self.assertEqual(result, 0)
            self.assertEqual(prepare.call_args.args, (Path("toys/original"), prompt))
            sealed_contract = prepare.call_args.kwargs["design_contract"]
            self.assertEqual(sealed_contract["title"], "Antisol")
            self.assertIn("Contract Mode: sealed", stdout.getvalue())

    def test_a_contract_that_does_not_parse_refuses_and_starts_no_run(self):
        with tempfile.TemporaryDirectory() as directory:
            contract_path = Path(directory) / "CONTRACT.md"
            contract_path.write_text("# Antisol\n\nno fenced block here\n", encoding="utf-8")
            with patch("workshop.workflow.revision.prepare_revision") as prepare, patch(
                "cli.main.start_native_run"
            ) as start, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as stderr:
                result = main(
                    ["fix", "toys/original", "--prompt", "Widen the sun den.",
                     "--contract", str(contract_path)]
                )
            self.assertEqual(result, 2)
            prepare.assert_not_called()
            start.assert_not_called()
            self.assertIn("design contract", stderr.getvalue())

    def test_a_contract_over_every_limit_names_every_failure_at_once(self):
        with tempfile.TemporaryDirectory() as directory:
            contract_path = Path(directory) / "CONTRACT.md"
            block = _contract_block(title="", inventor="")
            block["requirements"] = [
                {"id": "R%02d" % index, "scope": "assembly", "text": "Requirement %d." % index}
                for index in range(1, 18)
            ]
            contract_path.write_text(_contract_text(block), encoding="utf-8")
            with patch("workshop.workflow.revision.prepare_revision") as prepare, patch(
                "cli.main.start_native_run"
            ) as start, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as stderr:
                result = main(
                    ["fix", "toys/original", "--prompt", "Widen the sun den.",
                     "--contract", str(contract_path)]
                )
            self.assertEqual(result, 2)
            prepare.assert_not_called()
            start.assert_not_called()
            message = stderr.getvalue()
            self.assertIn("title", message)
            self.assertIn("inventor", message)
            self.assertIn("at most 16 assembly", message)

    def test_a_correction_without_contract_is_unchanged(self):
        wish = Wish.create(
            "wish-new", "Widen the sun den.", context={"inventor_id": "mara-masque"}
        )
        receipt = {"status": "waiting", "stage": "make", "product_id": "wish-new"}
        stdout = io.StringIO()
        with patch(
            "workshop.workflow.revision.prepare_revision",
            return_value=(wish, b"snapshot"),
        ) as prepare, patch(
            "cli.main.start_native_run", return_value=receipt
        ), redirect_stdout(stdout), redirect_stderr(io.StringIO()):
            result = main(
                ["fix", "toys/original", "--prompt", "Widen the sun den."]
            )
        self.assertEqual(result, 0)
        prepare.assert_called_once_with(Path("toys/original"), "Widen the sun den.")
        self.assertNotIn("Contract Mode", stdout.getvalue())
