"""Build the installed snapshot of the repository's inventor catalog."""

from pathlib import Path
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    """Copy the narrow runnable inventor catalog beside the installed package."""

    def run(self):
        super().run()
        project = Path(__file__).resolve().parent
        source_skills = project / "src" / "workshop" / "make" / "skills"
        built_skills = Path(self.build_lib) / "workshop" / "make" / "skills"
        for source in source_skills.rglob("*"):
            if source.is_file() and not source.is_symlink():
                built = built_skills / source.relative_to(source_skills)
                if built.is_file():
                    shutil.copymode(source, built)
        destination = (
            Path(self.build_lib)
            / "workshop"
            / "contributors"
            / "_catalog"
            / "inventors"
        )
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True)
        for inventor_id in ("alice", "bob", "eve", "ivy", "leo"):
            source = project / "inventors" / inventor_id
            target = destination / inventor_id
            target.mkdir()
            for filename in ("TASTE.md", "inventor.json", "profile.py"):
                shutil.copy2(source / filename, target / filename)


setup(cmdclass={"build_py": build_py})
