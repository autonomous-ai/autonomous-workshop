"""`tools/build_worktree.py` makes a light worktree: code without every toy.

Contract: the new worktree checks out every tracked file except those under
toys/, toys-spec/ and inbox/ (toys/README.md stays, so toys/ exists); it
copies from the main checkout only the named inputs and, for a seed source,
exactly APPROVAL.json plus the files `seed_manifest` lists, at the same
relative paths with their modification times. The main checkout is never
made sparse. Inputs outside those directories, a seed without an approval
and an existing destination are refused; --dry-run creates nothing."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from workshop.wish.seed import manifest_sha256, seed_manifest

TOOL = Path(__file__).resolve().parents[2] / "tools" / "build_worktree.py"
ENVIRONMENT = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
               "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
                          env=ENVIRONMENT).stdout


def _write(path: Path, text: str = "x\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


@unittest.skipUnless(shutil.which("git"), "needs git")
class BuildWorktreeTest(unittest.TestCase):
    def setUp(self):
        self.base = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.main = self.base / "main"
        _write(self.main / ".gitignore", "/toys/*\n!/toys/README.md\n/toys-spec/*\n/inbox/\n")
        _write(self.main / "src/code.py", "print('hi')\n")
        _write(self.main / "toys/README.md", "# toys\n")
        _write(self.main / "toys/old-archive/big.step", "tracked toy\n")
        _write(self.main / "toys-spec/old-design/NOTES.md", "tracked spec\n")
        _git(self.main, "init", "-q", "-b", "main")
        _git(self.main, "add", ".")
        _git(self.main, "add", "-f", "toys/old-archive/big.step", "toys-spec/old-design/NOTES.md")
        _git(self.main, "commit", "-q", "-m", "init")
        spec = self.main / "toys-spec/beaver"
        self.contract = _write(spec / "CONTRACT.md", "contract\n")
        self.ref = _write(spec / "ref-01-beaver.png", "png\n")
        _write(spec / "ref-02-unused.png", "not named\n")
        _write(spec / "NOTES.md", "design notes\n")
        _write(self.main / "toys/other-toy/README.md", "other\n")
        _write(self.main / "inbox/owner.pdf", "owner\n")
        self.proof = spec / "proof"
        _write(self.proof / "APPROVAL.json", "{}\n")
        _write(self.proof / "CONTRACT.md", "contract\n")
        _write(self.proof / "features/body.py", "body\n")
        _write(self.proof / "approved/body.step", "approved\n")
        _write(self.proof / "measure/cache.json", "evidence\n")
        _write(self.proof / "model.step", "rebuilt\n")
        os.utime(self.ref, (1_000_000_000, 1_000_000_000))
        self.destination = self.base / "build"

    def run_tool(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(TOOL), *args], cwd=self.main, capture_output=True,
                              text=True, env=ENVIRONMENT)

    def files(self, root: Path) -> set:
        return {path.relative_to(root).as_posix() for path in root.rglob("*")
                if path.is_file() and ".git" not in path.relative_to(root).parts}

    def test_the_worktree_holds_code_and_only_the_named_inputs(self):
        result = self.run_tool(str(self.destination), "--at", "main", "--input", str(self.contract),
                               "--input", str(self.ref), "--seed-source", str(self.proof))
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        seed = {"toys-spec/beaver/proof/%s" % name
                for name in ["APPROVAL.json", *seed_manifest(self.proof)]}
        self.assertEqual(seed, {"toys-spec/beaver/proof/APPROVAL.json",
                                "toys-spec/beaver/proof/CONTRACT.md",
                                "toys-spec/beaver/proof/features/body.py",
                                "toys-spec/beaver/proof/approved/body.step"})
        inputs = {"toys-spec/beaver/CONTRACT.md", "toys-spec/beaver/ref-01-beaver.png"}
        self.assertEqual(set(report["copied"]), inputs | seed)
        self.assertEqual(self.files(self.destination),
                         {".gitignore", "src/code.py", "toys/README.md"} | inputs | seed)
        copied_proof = self.destination / "toys-spec/beaver/proof"
        self.assertEqual(manifest_sha256(seed_manifest(copied_proof)),
                         manifest_sha256(seed_manifest(self.proof)))
        self.assertEqual((self.destination / "toys-spec/beaver/ref-01-beaver.png").stat().st_mtime,
                         1_000_000_000)
        self.assertEqual(_git(self.destination, "status", "--short"), "")
        self.assertNotEqual(self._config("core.sparseCheckout"), "true")
        self.assertEqual(self._config("core.sparseCheckout", self.destination), "true")
        self.assertTrue((self.main / "toys/old-archive/big.step").is_file())

    def _config(self, key: str, cwd: Path = None) -> str:
        return subprocess.run(["git", "config", "--get", key], cwd=cwd or self.main,
                              capture_output=True, text=True, env=ENVIRONMENT).stdout.strip()

    def test_a_directory_input_copies_that_toy_only(self):
        result = self.run_tool(str(self.destination), "--at", "main", "-b", "light",
                               "--input", str(self.main / "toys/other-toy"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.files(self.destination),
                         {".gitignore", "src/code.py", "toys/README.md", "toys/other-toy/README.md"})
        self.assertEqual(_git(self.destination, "branch", "--show-current").strip(), "light")

    def test_dry_run_creates_nothing(self):
        result = self.run_tool(str(self.destination), "--at", "main", "--dry-run",
                               "--input", str(self.contract))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["copied"], ["toys-spec/beaver/CONTRACT.md"])
        self.assertFalse(self.destination.exists())

    def test_refusals(self):
        outside = _write(self.base / "elsewhere.md")
        for args in (["--input", str(outside)],
                     ["--input", str(self.main / "src/code.py")],
                     ["--input", str(self.main / "toys-spec/beaver/missing.png")],
                     ["--seed-source", str(self.main / "toys-spec/beaver")]):
            result = self.run_tool(str(self.destination), "--at", "main", *args)
            self.assertEqual(result.returncode, 2, args)
            self.assertIn("build_worktree:", result.stderr)
            self.assertFalse(self.destination.exists())
        self.destination.mkdir()
        result = self.run_tool(str(self.destination), "--at", "main")
        self.assertEqual(result.returncode, 2)
        self.assertIn("already exists", result.stderr)


if __name__ == "__main__":
    unittest.main()
