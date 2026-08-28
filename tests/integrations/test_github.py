import subprocess
import tempfile
import unittest
from pathlib import Path

from workshop.integrations.git import push_toy_directory


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


if __name__ == "__main__":
    unittest.main()
