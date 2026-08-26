"""ABO's own offline checks, run from the repository suite.

`workshop check <inventor> --run` executes an inventor's declared checks, and
it now does so for an inventor built from a reviewed upstream snapshot as well
as for a local one. This runs them a second way, from CI's own suite, so ABO's
contracts are proved even if the discovery command is not the thing that ran.

It is also the check that keeps the imported harness honest: ABO's suite is
what proves the vendored tree imports cleanly with the non-ported modules
absent, that the gate is repointed at this repository's locked CAD skill, and
that the rules-versus-bill machinery still refuses what it is supposed to.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTOR_ROOT = ROOT / "inventors" / "abo"


class AboOfflineCheckTest(unittest.TestCase):
    def test_the_manifest_declares_the_checks_that_are_run_here(self):
        manifest = json.loads(
            (INVENTOR_ROOT / "inventor.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["source"]["kind"], "upstream-snapshot")
        self.assertEqual(
            manifest["checks"],
            [["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"]],
        )

    def test_abos_declared_checks_pass_with_no_credential_and_no_network(self):
        environment = dict(os.environ)
        paths = [str(ROOT / "src"), str(INVENTOR_ROOT)]
        if environment.get("PYTHONPATH"):
            paths.append(environment["PYTHONPATH"])
        environment["PYTHONPATH"] = os.pathsep.join(paths)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        # No model credential is placed in the environment, and nothing here
        # reaches a network, a printer, or a carrier.
        for name in (
            "ABO_PLAYTEST_BASE_URL",
            "ABO_PLAYTEST_API_KEY",
            "ABO_PLAYTEST_MODEL",
        ):
            environment.pop(name, None)
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
            cwd=str(INVENTOR_ROOT),
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            "ABO's offline checks failed:\n%s" % completed.stderr[-4000:],
        )


if __name__ == "__main__":
    unittest.main()
