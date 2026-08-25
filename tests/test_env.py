"""``load_dotenv`` and the ``from_env`` classmethods it feeds.

``load_dotenv`` mutates ``os.environ`` directly (it matches the convention
already used by ``inventors/bob/bob.py``), so every test here restores the
environment afterward.
"""

import base64
import json
import os
import tempfile
import unittest
from pathlib import Path

from inventor_workshop._http import HttpResponse
from inventor_workshop.concept_artist_openrouter import (
    ENV_OPENROUTER_API_BASE,
    ENV_OPENROUTER_API_KEY,
    ENV_OPENROUTER_IMAGE_MODEL,
    OpenRouterConceptArtist,
)
from inventor_workshop.concept_explode_inspector import (
    ENV_EXPLODE_INSPECTOR_API_KEY,
    ENV_EXPLODE_INSPECTOR_BASE_URL,
    ENV_EXPLODE_INSPECTOR_MODEL,
    OpenAICompatibleExplodeInspector,
)
from inventor_workshop.env import load_dotenv
from inventor_workshop.errors import ContractError


_TRACKED_ENV_NAMES = (
    ENV_OPENROUTER_API_KEY,
    ENV_OPENROUTER_IMAGE_MODEL,
    ENV_OPENROUTER_API_BASE,
    ENV_EXPLODE_INSPECTOR_BASE_URL,
    ENV_EXPLODE_INSPECTOR_API_KEY,
    ENV_EXPLODE_INSPECTOR_MODEL,
)


class EnvTestCase(unittest.TestCase):
    """Snapshots and restores the tracked environment variables per test."""

    def setUp(self):
        self._snapshot = {
            name: os.environ.get(name) for name in _TRACKED_ENV_NAMES
        }
        for name in _TRACKED_ENV_NAMES:
            os.environ.pop(name, None)
        self.temporary = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.temporary.name)

    def tearDown(self):
        os.chdir(self.cwd)
        self.temporary.cleanup()
        for name, value in self._snapshot.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


class LoadDotenvTest(EnvTestCase):
    def test_missing_file_is_silently_ignored(self):
        load_dotenv("does-not-exist.env")  # must not raise

    def test_populates_environment_from_key_value_lines(self):
        Path(".env").write_text(
            "# a comment\n\nFOO=bar\nQUOTED=\"has spaces\"\n", encoding="utf-8"
        )
        load_dotenv()
        self.assertEqual(os.environ.get("FOO"), "bar")
        self.assertEqual(os.environ.get("QUOTED"), "has spaces")
        del os.environ["FOO"]
        del os.environ["QUOTED"]

    def test_a_real_environment_variable_is_never_overwritten(self):
        os.environ["FOO"] = "real-value"
        Path(".env").write_text("FOO=from-file\n", encoding="utf-8")
        try:
            load_dotenv()
            self.assertEqual(os.environ["FOO"], "real-value")
        finally:
            del os.environ["FOO"]


class OpenRouterConceptArtistFromEnvTest(EnvTestCase):
    def test_requires_api_key(self):
        with self.assertRaises(ContractError):
            OpenRouterConceptArtist.from_env()

    def test_reads_key_from_dotenv_file(self):
        Path(".env").write_text(
            "OPENROUTER_API_KEY=dotenv-key\nOPENROUTER_IMAGE_MODEL=custom-model\n",
            encoding="utf-8",
        )
        artist = OpenRouterConceptArtist.from_env(
            transport=lambda *a, **k: HttpResponse(200, {}, b"{}")
        )
        self.assertEqual(artist._api_key, "dotenv-key")
        self.assertEqual(artist._model, "custom-model")

    def test_real_environment_variable_wins_over_dotenv_file(self):
        Path(".env").write_text("OPENROUTER_API_KEY=dotenv-key\n", encoding="utf-8")
        os.environ[ENV_OPENROUTER_API_KEY] = "real-key"
        artist = OpenRouterConceptArtist.from_env()
        self.assertEqual(artist._api_key, "real-key")

    def test_overrides_take_precedence_over_environment(self):
        os.environ[ENV_OPENROUTER_API_KEY] = "env-key"
        os.environ[ENV_OPENROUTER_IMAGE_MODEL] = "env-model"
        artist = OpenRouterConceptArtist.from_env(model="explicit-model")
        self.assertEqual(artist._model, "explicit-model")


class OpenAICompatibleExplodeInspectorFromEnvTest(EnvTestCase):
    def test_requires_all_three_variables(self):
        with self.assertRaises(ContractError) as ctx:
            OpenAICompatibleExplodeInspector.from_env()
        message = str(ctx.exception)
        self.assertIn(ENV_EXPLODE_INSPECTOR_BASE_URL, message)
        self.assertIn(ENV_EXPLODE_INSPECTOR_API_KEY, message)
        self.assertIn(ENV_EXPLODE_INSPECTOR_MODEL, message)

    def test_reads_all_three_from_dotenv_file(self):
        Path(".env").write_text(
            "CONCEPT_EXPLODE_INSPECTOR_BASE_URL=https://vision.example/v1\n"
            "CONCEPT_EXPLODE_INSPECTOR_API_KEY=inspector-key\n"
            "CONCEPT_EXPLODE_INSPECTOR_MODEL=vision-model\n",
            encoding="utf-8",
        )
        inspector = OpenAICompatibleExplodeInspector.from_env()
        self.assertEqual(inspector._base_url, "https://vision.example/v1")
        self.assertEqual(inspector._api_key, "inspector-key")
        self.assertEqual(inspector._model, "vision-model")


if __name__ == "__main__":
    unittest.main()
