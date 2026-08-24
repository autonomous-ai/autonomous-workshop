from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PACKAGE_ROOT / "src"
SCRIPTS_ROOT = Path(__file__).resolve().parents[3]
INSPECT_ROOT = SCRIPTS_ROOT / "inspect"
for path in (SRC_ROOT, INSPECT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import cadgen
from inspect_refs.cli import inspect_command_result


class InspectBatchDispatchTest(unittest.TestCase):
    def test_validate_dispatches_to_validity_api(self) -> None:
        inspect_validity = Mock(return_value={"ok": True, "findings": []})
        fake = types.ModuleType("cadgen.validity")
        fake.inspect_validity = inspect_validity

        with patch.dict(sys.modules, {"cadgen.validity": fake}), patch.object(
            cadgen, "validity", fake, create=True
        ):
            exit_code, result = inspect_command_result(
                ["validate", "<name>.step.py", "--refs", "o1.1,o1.2", "--allow-open"]
            )

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        inspect_validity.assert_called_once_with(
            "<name>.step.py",
            refs=["o1.1", "o1.2"],
            allow_open=True,
            check_self_intersection=True,
        )

    def test_interfere_dispatches_to_interference_api(self) -> None:
        inspect_interference = Mock(return_value={"ok": True, "clashes": []})
        fake = types.ModuleType("cadgen.interference")
        fake.DEFAULT_TOLERANCE_MM3 = 0.01
        fake.inspect_interference = inspect_interference

        with patch.dict(sys.modules, {"cadgen.interference": fake}), patch.object(
            cadgen, "interference", fake, create=True
        ):
            exit_code, result = inspect_command_result(
                ["interfere", "<name>.step.py", "--refs", "o1.1,o1.2", "--max-pairs", "7"]
            )

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        inspect_interference.assert_called_once_with(
            "<name>.step.py",
            refs=["o1.1", "o1.2"],
            tolerance=0.01,
            max_pairs=7,
        )


if __name__ == "__main__":
    unittest.main()
