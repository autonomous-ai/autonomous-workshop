"""`workshop resume --refresh-tools` lists what it changes before it writes (#107)."""
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.invent.fake_gamevault import install_fake_gamevault
from tests.workflow.test_resume_motion import MotionLauncher
from workshop.runtime.package_data import product_run_domain_skill_roots
from workshop.wish import Wish
import workshop.workflow.native_run as host


class RefreshToolsListingTest(unittest.TestCase):
    def setUp(self):
        install_fake_gamevault(self)
        self.temp = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.home = self.temp / "home"
        self.home.mkdir()
        self.enterContext(mock.patch.dict(os.environ, {"WORKSHOP_HOME": str(self.home)}, clear=True))
        self.enterContext(mock.patch.object(host, "_source_checkout_root", return_value=None))
        self.launcher = MotionLauncher()
        self.enterContext(mock.patch.object(host, "CodexNativeSessionLauncher", return_value=self.launcher))
        self.product_id = "refresh-listing-fixture"
        host.start_native_run(Wish.create(self.product_id, "a small mechanical toy"))
        self.paths = host.native_run_paths(self.product_id)

    def home_state(self):
        return {
            path: (path.read_bytes(), path.stat().st_mode)
            for path in sorted(self.home.rglob("*"))
            if path.is_file() and not path.is_symlink()
        }

    def edited_install(self):
        """A copy of this install whose cad and make-round trees differ."""
        roots = {}
        for name, root in product_run_domain_skill_roots().items():
            copy = self.temp / "install" / name
            shutil.copytree(root, copy)
            roots[name] = copy
        with (roots["cad"] / "SKILL.md").open("ab") as handle:
            handle.write(b"\nA corrected line.\n")
        (roots["make-round"] / "NOTES.md").write_bytes(b"new helper notes\n")
        return roots

    def test_dry_run_lists_every_change_and_writes_nothing(self):
        roots = self.edited_install()
        with mock.patch.object(host, "product_run_domain_skill_roots", return_value=roots):
            state = self.home_state()
            preview = host.refresh_native_run_tools(
                self.product_id, reason="workshop resume --refresh-tools", dry_run=True
            )
            self.assertEqual(self.home_state(), state)
            self.assertEqual(preview["action"], "tools-would-change")
            self.assertIs(preview["dry_run"], True)
            self.assertEqual(
                set(preview["changed_paths"]),
                {".agents/skills/cad/SKILL.md", ".agents/skills/make-round/NOTES.md"},
            )
            by_path = {item["path"]: item for item in preview["changes"]}
            added = by_path[".agents/skills/make-round/NOTES.md"]
            self.assertIsNone(added["previous_sha256"])
            self.assertIsNotNone(added["sha256"])
            changed = by_path[".agents/skills/cad/SKILL.md"]
            self.assertNotEqual(changed["previous_sha256"], changed["sha256"])

            applied = host.refresh_native_run_tools(
                self.product_id, reason="workshop resume --refresh-tools"
            )
            self.assertEqual(applied["action"], "tools-refreshed")
            self.assertIs(applied["dry_run"], False)
            self.assertEqual(applied["changes"], preview["changes"])

            again = host.refresh_native_run_tools(
                self.product_id, reason="workshop resume --refresh-tools", dry_run=True
            )
            self.assertEqual(again["action"], "tools-current")
            self.assertEqual(again["changes"], [])


if __name__ == "__main__":
    unittest.main()
