import subprocess
import tempfile
import unittest
from pathlib import Path

from workshop.integrations.git import GitPushError, push_toy_directory


class GitHubPublicationTest(unittest.TestCase):
    def test_adds_commits_and_pushes_only_the_toy_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            remote = root / "remote.git"
            repository = root / "repository"
            subprocess.run(["git", "init", "--bare", str(remote)], check=True)
            subprocess.run(["git", "init", "-b", "main", str(repository)], check=True)

            def git(*arguments):
                return subprocess.run(
                    ["git", *arguments],
                    cwd=repository,
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()

            git("config", "user.name", "Workshop Test")
            git("config", "user.email", "workshop@example.test")
            git("remote", "add", "origin", str(remote))
            (repository / "README.md").write_text("# Workshop\n")
            (repository / "toys/alice-skyline").mkdir(parents=True)
            git("add", "README.md")
            git("commit", "-m", "Initial commit")
            git("push", "-u", "origin", "main")
            (repository / "toys/alice-skyline/README.md").write_text("# Skyline\n")
            (repository / "notes.txt").write_text("leave me staged\n")
            git("add", "notes.txt")

            path = push_toy_directory(
                repository,
                repository / "toys/alice-skyline",
                title="Skyline",
            )

            self.assertEqual(path, "toys/alice-skyline")
            self.assertEqual(git("rev-parse", "HEAD"), git("rev-parse", "origin/main"))
            self.assertEqual(git("diff", "--cached", "--name-only"), "notes.txt")
            self.assertEqual(
                git("show", "--format=", "--name-only", "HEAD"),
                "toys/alice-skyline/README.md",
            )

    def test_rebases_toy_commit_when_remote_advances_during_product_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            remote = root / "remote.git"
            repository = root / "repository"
            contributor = root / "contributor"
            subprocess.run(["git", "init", "--bare", str(remote)], check=True)
            subprocess.run(["git", "init", "-b", "main", str(repository)], check=True)

            def git(cwd, *arguments):
                return subprocess.run(
                    ["git", *arguments],
                    cwd=cwd,
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()

            git(repository, "config", "user.name", "Workshop Test")
            git(repository, "config", "user.email", "workshop@example.test")
            git(repository, "remote", "add", "origin", str(remote))
            (repository / "README.md").write_text("# Workshop\n")
            git(repository, "add", "README.md")
            git(repository, "commit", "-m", "Initial commit")
            git(repository, "push", "-u", "origin", "main")

            subprocess.run(
                ["git", "clone", "-b", "main", str(remote), str(contributor)],
                check=True,
                capture_output=True,
            )
            git(contributor, "config", "user.name", "Concurrent Builder")
            git(contributor, "config", "user.email", "builder@example.test")
            (contributor / "remote-note.txt").write_text("concurrent work\n")
            git(contributor, "add", "remote-note.txt")
            git(contributor, "commit", "-m", "Concurrent builder change")
            git(contributor, "push", "origin", "main")

            target = repository / "toys/alice-moonchase"
            target.mkdir(parents=True)
            (target / "README.md").write_text("# Moonchase\n")

            path = push_toy_directory(repository, target, title="Moonchase")

            self.assertEqual(path, "toys/alice-moonchase")
            self.assertEqual(
                git(repository, "rev-parse", "HEAD"),
                git(repository, "rev-parse", "origin/main"),
            )
            self.assertTrue((repository / "remote-note.txt").is_file())
            self.assertEqual(git(repository, "status", "--porcelain"), "")
            self.assertEqual(
                git(repository, "show", "--format=", "--name-only", "HEAD"),
                "toys/alice-moonchase/README.md",
            )

    def test_does_not_reconcile_remote_advance_through_unrelated_local_work(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            remote = root / "remote.git"
            repository = root / "repository"
            contributor = root / "contributor"
            subprocess.run(["git", "init", "--bare", str(remote)], check=True)
            subprocess.run(["git", "init", "-b", "main", str(repository)], check=True)

            def git(cwd, *arguments, check=True):
                return subprocess.run(
                    ["git", *arguments],
                    cwd=cwd,
                    check=check,
                    capture_output=True,
                    text=True,
                ).stdout.strip()

            git(repository, "config", "user.name", "Workshop Test")
            git(repository, "config", "user.email", "workshop@example.test")
            git(repository, "remote", "add", "origin", str(remote))
            (repository / "README.md").write_text("# Workshop\n")
            git(repository, "add", "README.md")
            git(repository, "commit", "-m", "Initial commit")
            git(repository, "push", "-u", "origin", "main")
            subprocess.run(
                ["git", "clone", "-b", "main", str(remote), str(contributor)],
                check=True,
                capture_output=True,
            )
            git(contributor, "config", "user.name", "Concurrent Builder")
            git(contributor, "config", "user.email", "builder@example.test")
            (contributor / "remote-note.txt").write_text("concurrent work\n")
            git(contributor, "add", "remote-note.txt")
            git(contributor, "commit", "-m", "Concurrent builder change")
            git(contributor, "push", "origin", "main")

            target = repository / "toys/alice-moonchase"
            target.mkdir(parents=True)
            (target / "README.md").write_text("# Moonchase\n")
            (repository / "builder-notes.txt").write_text("do not rewrite me\n")
            git(repository, "add", "builder-notes.txt")

            with self.assertRaisesRegex(GitPushError, "dirty checkout"):
                push_toy_directory(repository, target, title="Moonchase")

            self.assertEqual(
                git(repository, "diff", "--cached", "--name-only"),
                "builder-notes.txt",
            )
            self.assertEqual(
                git(repository, "show", "--format=", "--name-only", "HEAD"),
                "toys/alice-moonchase/README.md",
            )
            self.assertNotEqual(
                git(repository, "rev-parse", "HEAD"),
                git(repository, "rev-parse", "origin/main"),
            )


if __name__ == "__main__":
    unittest.main()
