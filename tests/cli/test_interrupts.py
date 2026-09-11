"""Operator interruption is reported only after the command has unwound."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

from cli.main import main
from workshop.errors import WorkshopError


class InterruptPresentationTests(unittest.TestCase):
    def test_wish_and_resume_unwind_before_reporting_interrupt(self):
        for command, native_call in (
            (("wish", "a mechanical toy"), "start_native_run"),
            (("resume", "wish-one"), "resume_native_run"),
        ):
            for options in ((), ("--json",)):
                with self.subTest(command=command[0], options=options):
                    events = []

                    class ErrorOutput(StringIO):
                        def write(self, text):
                            if text.startswith("workshop: interrupted."):
                                events.append("interruption reported")
                            return super().write(text)

                    def interrupted_host(*args, **kwargs):
                        try:
                            raise KeyboardInterrupt("private native detail")
                        finally:
                            events.append("host cleanup complete")

                    stdout, stderr = StringIO(), ErrorOutput()
                    with mock.patch("cli.main." + native_call, side_effect=interrupted_host), \
                            redirect_stdout(stdout), redirect_stderr(stderr):
                        code = main((*command, *options))
                    self.assertEqual(code, 130)
                    self.assertEqual(events, ["host cleanup complete", "interruption reported"])
                    self.assertNotIn("Traceback", stderr.getvalue())
                    self.assertNotIn("private native detail", stderr.getvalue())
                    if options:
                        self.assertEqual(stdout.getvalue(), "")
                    if command[0] == "wish":
                        self.assertIn("If the Wish was saved", stderr.getvalue())
                    else:
                        self.assertIn("workshop resume wish-one", stderr.getvalue())

    def test_wish_interrupted_before_persistence_does_not_claim_a_saved_run(self):
        stderr = StringIO()
        with mock.patch("cli.main.load_wish_references", side_effect=KeyboardInterrupt), \
                mock.patch("cli.main.start_native_run") as start, \
                redirect_stdout(StringIO()), redirect_stderr(stderr):
            self.assertEqual(main(("wish", "one toy", "--json")), 130)
        start.assert_not_called()
        self.assertEqual(stderr.getvalue(),
                         "workshop: interrupted. If the Wish was saved, continue it with: "
                         "workshop resume WISH_ID\n")

    def test_resume_command_quotes_the_exact_supplied_id(self):
        stderr = StringIO()
        with mock.patch("cli.main.resume_native_run", side_effect=KeyboardInterrupt), \
                redirect_stdout(StringIO()), redirect_stderr(stderr):
            self.assertEqual(main(("resume", "wish with spaces", "--json")), 130)
        self.assertIn("workshop resume 'wish with spaces'", stderr.getvalue())

    def test_interruption_during_parsing_has_no_run_claim(self):
        stderr = StringIO()
        with mock.patch("cli.main.parser", side_effect=KeyboardInterrupt), redirect_stderr(stderr):
            self.assertEqual(main(), 130)
        self.assertEqual(stderr.getvalue(), "workshop: interrupted.\n")

    def test_non_run_command_has_no_resume_guidance(self):
        stderr = StringIO()
        with mock.patch("cli.main.native_run_status", side_effect=KeyboardInterrupt), \
                redirect_stderr(stderr):
            self.assertEqual(main(("status", "wish-one")), 130)
        self.assertEqual(stderr.getvalue(), "workshop: interrupted.\n")

    def test_subprocess_exits_130_without_traceback_or_json_receipt(self):
        script = """from unittest import mock
from cli.main import main
with mock.patch('cli.main.resume_native_run', side_effect=KeyboardInterrupt):
    raise SystemExit(main(('resume', 'wish-one', '--json')))
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 130, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("workshop: interrupted.", result.stderr)
        self.assertIn("workshop resume wish-one", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertNotIn("KeyboardInterrupt", result.stderr)

    def test_other_exceptions_keep_the_existing_exit_and_propagation_contract(self):
        for error in (WorkshopError("refused"), OSError("unavailable"),
                      ValueError("invalid"), KeyError("missing")):
            with self.subTest(error=type(error).__name__):
                stderr = StringIO()
                with mock.patch("cli.main.resume_native_run", side_effect=error), \
                        redirect_stdout(StringIO()), redirect_stderr(stderr):
                    self.assertEqual(main(("resume", "wish-one")), 2)
                self.assertEqual(stderr.getvalue(), "workshop: %s\n" % error)
        for error in (RuntimeError("unexpected bug"), SystemExit(23)):
            with self.subTest(error=type(error).__name__):
                with mock.patch("cli.main.resume_native_run", side_effect=error), \
                        redirect_stdout(StringIO()), redirect_stderr(StringIO()), \
                        self.assertRaises(type(error)) as raised:
                    main(("resume", "wish-one"))
                self.assertIs(raised.exception, error)


if __name__ == "__main__":
    unittest.main()
