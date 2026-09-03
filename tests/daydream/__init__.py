"""Daydream component tests."""

from pathlib import Path


def load_tests(loader, standard_tests, pattern):
    """Let ``python -m unittest tests.daydream`` run the whole package."""

    package = Path(__file__).resolve().parent
    standard_tests.addTests(
        loader.discover(
            start_dir=str(package),
            pattern=pattern or "test_*.py",
            top_level_dir=str(package.parents[1]),
        )
    )
    return standard_tests
