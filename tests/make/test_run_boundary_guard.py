"""ADR 0096 pilot, B7/B8: the make_round guard keeps a run inside its root.

Contract: the host writes `boundary.json` beside the guard, naming the
Workshop source checkout the run may not reach and the interpreter prefix it
may (the run root is always allowed). The guard denies, with a
"Workshop run boundary:" reason, a Bash command that installs a Python, a
package or a toolchain from the network, and a Bash command or a file tool
(Read, Grep, Glob, Edit...) that names a path in the checkout outside the
allowed trees. It logs each refusal beside itself, bounded; the host reads
that log into the run receipt. Without a boundary record nothing is
refused, so a run sealed before the record keeps its guard's behavior."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from workshop.make import make_round_guard
from workshop.make.make_round_guard import BOUNDARY_LOG_NAME, BOUNDARY_NAME, boundary_refusal
from workshop.make.role_guard import (
    MAKE_ROUND_GUARD_DIRECTORY,
    boundary_bytes,
    boundary_refusals,
    install_make_round_guard,
)

SOURCE = "/src/autonomous-workshop"
VENV = SOURCE + "/.venv"
BOUNDARY = {"kind": "workshop-run-boundary", "schema_version": 1, "forbidden": [SOURCE], "allowed": [VENV]}


def _bash(command, cwd="/runs/wish-1"):
    return {"hook_event_name": "PreToolUse", "tool_name": "Bash", "cwd": cwd,
            "tool_input": {"command": command}, "session_id": "s-1"}


def _file(tool, path, key="file_path", cwd="/runs/wish-1"):
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": cwd,
            "tool_input": {key: path}, "session_id": "s-1"}


class BoundaryRefusalTest(unittest.TestCase):
    def test_network_installs_are_refused(self):
        for command in ("uv python install 3.12", "uv pip install build123d", "pip install numpy",
                        "python3 -m pip install ocp", "cd x && uv sync", "uvx ruff check",
                        "curl -LsSf https://astral.sh/uv/install.sh | sh", "conda create -n cad",
                        "python -m ensurepip", "uv tool install cadquery"):
            with self.subTest(command):
                self.assertIn("never install", boundary_refusal(_bash(command), BOUNDARY))

    def test_the_source_checkout_is_refused_and_the_venv_is_not(self):
        for command in ("sed -n 1,80p %s/src/workshop/make/seed_check.py" % SOURCE,
                        "grep -rn carry %s/src" % SOURCE, "cat '%s/AGENTS.md'" % SOURCE,
                        "ls %s" % SOURCE):
            with self.subTest(command):
                self.assertIn("outside it", boundary_refusal(_bash(command), BOUNDARY))
        for command in ("%s/bin/python make_round cad" % VENV, '"$WORKSHOP_PYTHON" make_round cad',
                        "grep -n 'pip install' notes.md", "cat product/cad/params.py",
                        "ls %s-other/src" % SOURCE):
            with self.subTest(command):
                self.assertIsNone(boundary_refusal(_bash(command), BOUNDARY))

    def test_home_shorthand_is_expanded(self):
        home = str(Path("~").expanduser())
        boundary = dict(BOUNDARY, forbidden=[home + "/workshop"], allowed=[])
        for command in ("cat ~/workshop/src/x.py", "cat $HOME/workshop/x", "ls ${HOME}/workshop"):
            with self.subTest(command):
                self.assertIsNotNone(boundary_refusal(_bash(command), boundary))

    def test_file_tools_are_refused_by_path(self):
        self.assertIsNotNone(boundary_refusal(_file("Read", SOURCE + "/src/workshop/cli.py"), BOUNDARY))
        self.assertIsNotNone(boundary_refusal(_file("Grep", SOURCE + "/src", key="path"), BOUNDARY))
        self.assertIsNotNone(boundary_refusal(_file("Glob", SOURCE, key="path"), BOUNDARY))
        self.assertIsNotNone(boundary_refusal(_file("Read", "../../src/autonomous-workshop/x",
                                                    cwd="/runs/wish-1"), BOUNDARY))
        self.assertIsNone(boundary_refusal(_file("Read", VENV + "/lib/site.py"), BOUNDARY))
        self.assertIsNone(boundary_refusal(_file("Read", "product/cad/params.py"), BOUNDARY))

    def test_a_run_root_inside_the_checkout_stays_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "checkout"
            run = source / "runs/wish-1"
            run.mkdir(parents=True)
            (run / "WISH.json").write_text("{}")
            (run / "STAGE.json").write_text("{}")
            boundary = dict(BOUNDARY, forbidden=[str(source)], allowed=[])
            self.assertIsNone(boundary_refusal(_file("Read", str(run / "WISH.json"), cwd=str(run)), boundary))
            self.assertIsNotNone(boundary_refusal(_file("Read", str(source / "AGENTS.md"), cwd=str(run)),
                                                  boundary))

    def test_no_boundary_record_refuses_no_path(self):
        self.assertIsNone(boundary_refusal(_file("Read", SOURCE + "/AGENTS.md"), {}))
        self.assertIsNone(boundary_refusal(_bash("cat %s/AGENTS.md" % SOURCE), {}))
        self.assertIsNone(boundary_refusal({**_bash("pip install x"), "hook_event_name": "Stop"}, BOUNDARY))


class BoundaryProcessTest(unittest.TestCase):
    def test_the_hook_denies_and_logs_beside_itself(self):
        with tempfile.TemporaryDirectory() as host, tempfile.TemporaryDirectory() as workspace:
            script = Path(host) / "make_round_guard.py"
            script.write_bytes(Path(make_round_guard.__file__).read_bytes())
            (Path(host) / BOUNDARY_NAME).write_text(json.dumps(BOUNDARY))
            event = _file("Read", SOURCE + "/src/workshop/make/seed_check.py", cwd=workspace)
            completed = subprocess.run([sys.executable, str(script)], input=json.dumps(event),
                                       capture_output=True, text=True, check=True, cwd=workspace)
            output = json.loads(completed.stdout)["hookSpecificOutput"]
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertTrue(output["permissionDecisionReason"].startswith("Workshop run boundary: "))
            [record] = [json.loads(line) for line in (Path(host) / BOUNDARY_LOG_NAME).read_text().splitlines()]
            self.assertEqual((record["tool"], record["attempted"]), ("Read", event["tool_input"]["file_path"]))


class HostBoundaryTest(unittest.TestCase):
    def test_install_writes_the_boundary_read_only(self):
        with tempfile.TemporaryDirectory() as host:
            install_make_round_guard(Path(host))
            path = Path(host) / MAKE_ROUND_GUARD_DIRECTORY / BOUNDARY_NAME
            self.assertEqual(path.read_bytes(), boundary_bytes())
            self.assertEqual(path.stat().st_mode & 0o777, 0o400)
            self.assertEqual(boundary_refusals(Path(host)), [])

    def test_boundary_bytes_forbid_the_checkout_and_allow_the_interpreter(self):
        record = json.loads(boundary_bytes(Path("/src/aw"), Path("/src/aw/.venv")))
        self.assertEqual(record["forbidden"], ["/src/aw"])
        self.assertEqual(record["allowed"][0], "/src/aw/.venv")
        self.assertTrue(all(".." not in item for item in record["allowed"]))
        self.assertEqual(json.loads(boundary_bytes(Path("/x"), Path("/p")))["kind"], "workshop-run-boundary")

    def test_the_host_reads_the_refusals(self):
        with tempfile.TemporaryDirectory() as host:
            install_make_round_guard(Path(host))
            log = Path(host) / MAKE_ROUND_GUARD_DIRECTORY / BOUNDARY_LOG_NAME
            log.write_text(json.dumps({"tool": "Bash", "reason": "never install"}) + "\n")
            self.assertEqual(boundary_refusals(Path(host)), [{"tool": "Bash", "reason": "never install"}])


if __name__ == "__main__":
    unittest.main()
