from pathlib import Path
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    def run(self):
        super().run()
        project = Path(__file__).resolve().parent
        destination = Path(self.build_lib) / "one_decision_games" / "_identity"
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True)
        for filename in ("inventor.json", "TASTE.md"):
            shutil.copy2(project / filename, destination / filename)


setup(cmdclass={"build_py": build_py})
