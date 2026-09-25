from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PACKAGE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cadgen._internal.generation import (
    _built_shape_identity,
    _installed_toolchain_versions,
)


class BuiltShapeIdentityTest(unittest.TestCase):
    """`_built_shape_identity` never reads a shape reloaded from STEP (ADR 0073)."""

    def test_none_for_a_result_with_no_fresh_scene(self):
        self.assertIsNone(_built_shape_identity(None))
        self.assertIsNone(_built_shape_identity(SimpleNamespace(scene=None)))
        self.assertIsNone(
            _built_shape_identity(SimpleNamespace(scene=SimpleNamespace()))
        )

    def test_none_when_the_compound_has_no_wrapped_shape(self):
        result = SimpleNamespace(
            scene=SimpleNamespace(source_compound=SimpleNamespace())
        )
        self.assertIsNone(_built_shape_identity(result))

    def test_hashes_the_wrapped_shape_a_fresh_build_produced(self):
        sentinel_shape = object()
        result = SimpleNamespace(
            scene=SimpleNamespace(
                source_compound=SimpleNamespace(wrapped=sentinel_shape)
            )
        )
        with patch(
            "cadgen.inspection_runtime.shape_identity", return_value="f" * 64
        ) as mocked:
            self.assertEqual(_built_shape_identity(result), "f" * 64)
        mocked.assert_called_once_with(sentinel_shape)


class InstalledToolchainVersionsTest(unittest.TestCase):
    """The seal names the exact installed build123d/cadquery-ocp versions."""

    def test_reads_both_pinned_distributions(self):
        def fake_version(name):
            return {"build123d": "0.11.1", "cadquery-ocp": "7.9.3.1.1"}[name]

        with patch("importlib.metadata.version", side_effect=fake_version):
            self.assertEqual(
                _installed_toolchain_versions(),
                {"build123d": "0.11.1", "cadquery_ocp": "7.9.3.1.1"},
            )


if __name__ == "__main__":
    unittest.main()
