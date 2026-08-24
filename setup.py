"""Build package-owned Workshop data without duplicating its source trees."""

from pathlib import Path
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    """Copy canonical schemas and skills beside the installed Python package."""

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


setup(cmdclass={"build_py": build_py})
