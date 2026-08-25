"""Build package-owned Workshop data without duplicating its source trees."""

from pathlib import Path
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    """Copy canonical Workshop data beside the installed Python package."""

    def run(self):
        super().run()
        project = Path(__file__).resolve().parent
        destination = Path(self.build_lib) / "inventor_workshop" / "_data"
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True)
        shutil.copytree(
            project / "skills",
            destination / "skills",
            ignore=shutil.ignore_patterns(
                "__pycache__", ".pytest_cache", ".DS_Store", "*.pyc", "*.pyo"
            ),
        )
        schemas = destination / "schemas"
        schemas.mkdir()
        for source in sorted((project / "schemas").glob("*.json")):
            shutil.copy2(source, schemas / source.name)
        inventors = destination / "inventors"
        inventors.mkdir()
        for inventor_id in ("alice", "bob", "eve", "ivy", "leo"):
            source = project / "inventors" / inventor_id
            target = inventors / inventor_id
            target.mkdir()
            for filename in ("TASTE.md", "inventor.json", "profile.py"):
                shutil.copy2(source / filename, target / filename)


setup(cmdclass={"build_py": build_py})
