from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from alice.config import load_config, resolve_runtime_paths


class ConfigTests(unittest.TestCase):
    def override(self, value: dict[str, object]) -> Path:
        path = Path(self.directory.name) / "override.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_defaults_separate_model_and_adapter_environment(self) -> None:
        config = load_config()

        self.assertIn("model_allowed_environment", config["agents"])
        self.assertNotIn("allowed_environment", config["agents"])
        self.assertEqual(config["adapters"]["command_allowed_environment"], {})
        self.assertNotIn("factory_publish_command", config["adapters"])
        self.assertNotIn("artifacts", config["runtime"])
        self.assertNotIn("outbox", config["runtime"])

    def test_removed_knobs_are_rejected_instead_of_silently_ignored(self) -> None:
        removed = (
            {"runtime": {"artifacts": "elsewhere"}},
            {"agents": {"allowed_environment": ["PATH"]}},
            {"adapters": {"factory_publish_command": ["publisher"]}},
            {"quality": {"maximum_critical_exploits": 9}},
        )
        for value in removed:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "was removed"):
                    load_config(self.override(value))

    def test_adapter_only_environment_cannot_be_forwarded_to_model(self) -> None:
        path = self.override(
            {
                "agents": {
                    "model_allowed_environment": ["PATH", "CAD_SERVICE_TOKEN"]
                },
                "adapters": {
                    "command_allowed_environment": {
                        "cad": ["PATH", "CAD_SERVICE_TOKEN"]
                    }
                },
            }
        )

        with self.assertRaisesRegex(ValueError, "cannot be forwarded to the model"):
            load_config(path)

    def test_only_database_and_dedicated_codex_home_are_runtime_paths(self) -> None:
        config = resolve_runtime_paths(load_config(), self.directory.name)

        root = Path(self.directory.name).resolve()
        self.assertEqual(config["runtime"]["database"], str(root / "var/alice.sqlite3"))
        self.assertEqual(config["agents"]["codex"]["home"], str(root / "var/codex-home"))

    def test_invalid_runtime_numbers_fail_before_doctor_can_claim_ready(self) -> None:
        for value in (0, -1, float("inf"), True):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "runtime.poll_seconds"):
                    load_config(self.override({"runtime": {"poll_seconds": value}}))

    def test_publication_kill_switch_rejects_string_booleans(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "objective.auto_publish_when_eligible"
        ):
            load_config(
                self.override(
                    {"objective": {"auto_publish_when_eligible": "false"}}
                )
            )


if __name__ == "__main__":
    unittest.main()
