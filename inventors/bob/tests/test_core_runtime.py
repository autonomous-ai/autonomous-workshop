import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from harness import core_runtime


class TestRepositoryCoreSource(unittest.TestCase):
    def test_nested_monorepo_layout_resolves_foundation(self):
        repository_root = Path(__file__).resolve().parents[3]
        self.assertEqual(
            core_runtime._repository_source(),
            repository_root / "foundation" / "src",
        )


class TestStrictCoreSourcePin(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.pinned = root / "pinned"
        package = self.pinned / "inventor_core"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        self.untrusted = root / "site-packages" / "inventor_core"
        self.untrusted.mkdir(parents=True)
        (self.untrusted / "__init__.py").write_text("", encoding="utf-8")
        self.previous_source = os.environ.get("BOB_CORE_SRC")
        os.environ["BOB_CORE_SRC"] = str(self.pinned)
        self.previous_modules = {
            name: module
            for name, module in sys.modules.items()
            if name == "inventor_core" or name.startswith("inventor_core.")
        }
        for name in self.previous_modules:
            del sys.modules[name]

    def tearDown(self):
        for name in tuple(sys.modules):
            if name == "inventor_core" or name.startswith("inventor_core."):
                del sys.modules[name]
        sys.modules.update(self.previous_modules)
        if self.previous_source is None:
            os.environ.pop("BOB_CORE_SRC", None)
        else:
            os.environ["BOB_CORE_SRC"] = self.previous_source
        self.temporary.cleanup()

    def test_preimported_site_package_fails_closed_without_reload(self):
        cached = types.ModuleType("inventor_core")
        cached.__file__ = str(self.untrusted / "__init__.py")
        cached.__path__ = [str(self.untrusted)]
        sys.modules["inventor_core"] = cached

        with mock.patch.object(core_runtime.importlib, "import_module") as importer:
            with self.assertRaises(core_runtime.CoreUnavailable) as caught:
                core_runtime.require_core()

        self.assertIn("outside BOB_CORE_SRC", str(caught.exception))
        importer.assert_not_called()
        self.assertIs(sys.modules["inventor_core"], cached)


if __name__ == "__main__":
    unittest.main()
