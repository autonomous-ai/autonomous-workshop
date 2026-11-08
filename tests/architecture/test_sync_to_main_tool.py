"""Issue #244: `tools/sync-to-main.sh` writes no marker inside a toy archive.

Contract: a worktree's untracked toys/, toys-spec/ and inbox/ files are
copied into the main checkout; the line naming the source worktree goes to
the top directory's ledger (`toys/.synced-from`), never inside a toy
directory, whose files are an exact-bytes archive `workshop fix` checks
against its manifest. A marker an older version left inside a toy
directory is moved to the ledger, even when nothing is copied. In the main
checkout itself the tool does nothing."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from workshop.release.public_archive import build_public_archive_manifest

TOOL = Path(__file__).resolve().parents[2] / "tools" / "sync-to-main.sh"


def _git(cwd: Path, *args: str) -> str:
    environment = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
                   "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
                   "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
                          env=environment).stdout


@unittest.skipUnless(shutil.which("git") and shutil.which("rsync"), "needs git and rsync")
class SyncToMainTest(unittest.TestCase):
    def setUp(self):
        base = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.main = base / "main"
        self.main.mkdir()
        _git(self.main, "init", "-q", "-b", "main")
        (self.main / ".gitignore").write_text("toys/\ntoys-spec/\ninbox/\n")
        _git(self.main, "add", ".gitignore")
        _git(self.main, "commit", "-q", "-m", "init")
        self.worktree = base / "builder"
        _git(self.main, "worktree", "add", "-q", "--detach", str(self.worktree))

    def sync(self, cwd: Path) -> subprocess.CompletedProcess:
        result = subprocess.run(["bash", str(TOOL)], cwd=cwd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def _archive(self, root: Path) -> Path:
        toy = root / "toys/sunset-slider"
        (toy / "cad").mkdir(parents=True)
        (toy / "cad/part_body.step").write_bytes(b"ISO-10303-21;\n")
        (toy / "README.md").write_text("# Sunset Slider\n")
        manifest = build_public_archive_manifest(toy)
        (toy / "MANIFEST.json").write_text(json.dumps([entry.path for entry in manifest.entries]))
        return toy

    def test_the_copied_toy_archive_gains_no_file_and_the_ledger_names_the_source(self):
        source = self._archive(self.worktree)
        before = build_public_archive_manifest(source)
        (self.worktree / "toys-spec/sunset-slider").mkdir(parents=True)
        (self.worktree / "toys-spec/sunset-slider/contract.md").write_text("contract\n")
        result = self.sync(self.worktree)
        self.assertIn("copied 4 file(s) from builder", result.stderr)
        copied = self.main / "toys/sunset-slider"
        self.assertFalse((copied / ".synced-from").exists())
        self.assertEqual(build_public_archive_manifest(copied).artifact_sha256, before.artifact_sha256)
        self.assertFalse((self.main / "toys-spec/sunset-slider/.synced-from").exists())
        for top, directory in (("toys", "toys/sunset-slider"), ("toys-spec", "toys-spec/sunset-slider")):
            stamp, name, named = (self.main / top / ".synced-from").read_text().split()
            self.assertEqual((name, named), ("builder", directory))
        # The ledger is never copied back or synced as a toy file.
        self.assertEqual(self.sync(self.worktree).stderr, "")

    def test_an_older_marker_inside_a_toy_moves_to_the_ledger(self):
        old = self.main / "toys/beaver-coasters"
        old.mkdir(parents=True)
        (old / "part.step").write_bytes(b"x")
        (old / ".synced-from").write_text("2026-10-28T09:55:56Z contract-image-mismatch\n"
                                          "2026-10-29T10:00:00Z other-worktree\n")
        (self.main / "toys/.synced-from").write_text("2026-10-27T08:00:00Z first\n")
        self.sync(self.worktree)  # nothing to copy, and the move still runs
        self.assertFalse((old / ".synced-from").exists())
        self.assertEqual((old / "part.step").read_bytes(), b"x")
        self.assertEqual((self.main / "toys/.synced-from").read_text().splitlines(), [
            "2026-10-27T08:00:00Z first",
            "2026-10-28T09:55:56Z contract-image-mismatch toys/beaver-coasters",
            "2026-10-29T10:00:00Z other-worktree toys/beaver-coasters",
        ])

    def test_the_main_checkout_itself_is_left_alone(self):
        old = self.main / "toys/beaver-coasters"
        old.mkdir(parents=True)
        (old / ".synced-from").write_text("2026-10-28T09:55:56Z contract-image-mismatch\n")
        self.sync(self.main)
        self.assertTrue((old / ".synced-from").exists())
        self.assertFalse((self.main / "toys/.synced-from").exists())


if __name__ == "__main__":
    unittest.main()
