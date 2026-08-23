from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_ROOT = Path(__file__).resolve().parents[3]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from cadgen_daemon.client import run_via_daemon


class WarmClientStdinTest(unittest.TestCase):
    def test_inspect_batch_stays_in_process_for_stdin(self) -> None:
        with patch.dict(os.environ, {"CADGEN_WARM": "1"}, clear=False):
            self.assertIsNone(run_via_daemon("inspect", ["batch"], os.getcwd()))

    def test_inspect_worker_stays_in_process_for_stdin(self) -> None:
        with patch.dict(os.environ, {"CADGEN_WARM": "1"}, clear=False):
            self.assertIsNone(run_via_daemon("inspect", ["worker"], os.getcwd()))


if __name__ == "__main__":
    unittest.main()
