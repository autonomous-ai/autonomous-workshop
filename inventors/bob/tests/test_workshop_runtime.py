import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from harness import workshop_runtime


class TestRepositoryWorkshopSource(unittest.TestCase):
    def test_nested_monorepo_layout_resolves_workshop(self):
        repository_root = Path(__file__).resolve().parents[3]
        self.assertEqual(
            workshop_runtime._repository_source(),
            repository_root / "workshop" / "src",
        )

    def test_bob_skill_links_resolve_to_the_shared_workshop(self):
        bob_root = Path(__file__).resolve().parents[1]
        repository_root = bob_root.parents[1]
        for name in ("cad", "step-parts"):
            link = bob_root / "skills" / name
            self.assertTrue(link.is_symlink(), name)
            self.assertEqual(
                link.resolve(strict=True),
                (repository_root / "workshop" / "skills" / name).resolve(strict=True),
            )
            self.assertTrue((link / "SKILL.md").is_file(), name)


class TestStrictWorkshopSourcePin(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.pinned = root / "pinned"
        package = self.pinned / "inventor_workshop"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        self.untrusted = root / "site-packages" / "inventor_workshop"
        self.untrusted.mkdir(parents=True)
        (self.untrusted / "__init__.py").write_text("", encoding="utf-8")
        self.previous_source = os.environ.get("BOB_WORKSHOP_SRC")
        self.previous_foundation_source = os.environ.pop(
            "BOB_FOUNDATION_SRC", None
        )
        self.previous_legacy_source = os.environ.pop("BOB_CORE_SRC", None)
        os.environ["BOB_WORKSHOP_SRC"] = str(self.pinned)
        self.previous_modules = {
            name: module
            for name, module in sys.modules.items()
            if name == "inventor_workshop"
            or name.startswith("inventor_workshop.")
        }
        for name in self.previous_modules:
            del sys.modules[name]

    def tearDown(self):
        for name in tuple(sys.modules):
            if name == "inventor_workshop" or name.startswith(
                "inventor_workshop."
            ):
                del sys.modules[name]
        sys.modules.update(self.previous_modules)
        if self.previous_source is None:
            os.environ.pop("BOB_WORKSHOP_SRC", None)
        else:
            os.environ["BOB_WORKSHOP_SRC"] = self.previous_source
        os.environ.pop("BOB_CORE_SRC", None)
        os.environ.pop("BOB_FOUNDATION_SRC", None)
        if self.previous_foundation_source is not None:
            os.environ["BOB_FOUNDATION_SRC"] = self.previous_foundation_source
        if self.previous_legacy_source is not None:
            os.environ["BOB_CORE_SRC"] = self.previous_legacy_source
        self.temporary.cleanup()

    def test_preimported_site_package_fails_closed_without_reload(self):
        cached = types.ModuleType("inventor_workshop")
        cached.__file__ = str(self.untrusted / "__init__.py")
        cached.__path__ = [str(self.untrusted)]
        sys.modules["inventor_workshop"] = cached

        with mock.patch.object(
            workshop_runtime.importlib, "import_module"
        ) as importer:
            with self.assertRaises(
                workshop_runtime.WorkshopUnavailable
            ) as caught:
                workshop_runtime.require_workshop()

        self.assertIn("outside BOB_WORKSHOP_SRC", str(caught.exception))
        importer.assert_not_called()
        self.assertIs(sys.modules["inventor_workshop"], cached)

    def test_legacy_source_is_an_explicit_fallback(self):
        os.environ.pop("BOB_WORKSHOP_SRC")
        os.environ["BOB_CORE_SRC"] = str(self.pinned)
        self.assertEqual(
            workshop_runtime._configured_source(), self.pinned.resolve()
        )

    def test_foundation_source_is_an_explicit_fallback(self):
        os.environ.pop("BOB_WORKSHOP_SRC")
        os.environ["BOB_FOUNDATION_SRC"] = str(self.pinned)
        self.assertEqual(
            workshop_runtime._configured_source(), self.pinned.resolve()
        )

    def test_new_and_legacy_sources_must_not_disagree(self):
        other = Path(self.temporary.name) / "other"
        other.mkdir()
        os.environ["BOB_CORE_SRC"] = str(other)
        with self.assertRaises(workshop_runtime.WorkshopUnavailable) as caught:
            workshop_runtime._configured_source()
        self.assertIn("disagree", str(caught.exception))


class TestCanonicalWorkshopSurface(unittest.TestCase):
    def test_adapter_exposes_v03_words(self):
        runtime = workshop_runtime.require_workshop()
        for name in (
            "pack_artifact", "inspect_pack", "Clockwork", "ShopDoor",
            "Sender", "Stamp", "load_taste",
        ):
            self.assertTrue(getattr(runtime, name), name)


if __name__ == "__main__":
    unittest.main()
