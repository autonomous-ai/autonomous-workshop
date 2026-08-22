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
        self.assertIs(config["adapters"]["text2game"]["enabled"], False)
        self.assertEqual(config["adapters"]["text2game"]["command"], [])

    def test_removed_knobs_are_rejected_instead_of_silently_ignored(self) -> None:
        removed = (
            {"runtime": {"artifacts": "elsewhere"}},
            {"agents": {"allowed_environment": ["PATH"]}},
            {"adapters": {"factory_publish_command": ["publisher"]}},
            {"adapters": {"text2game": {"uv_binary": "/usr/bin/uv"}}},
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

    def test_runtime_owned_paths_are_resolved_under_the_selected_root(self) -> None:
        config = resolve_runtime_paths(load_config(), self.directory.name)

        root = Path(self.directory.name).resolve()
        self.assertEqual(config["runtime"]["database"], str(root / "var/alice.sqlite3"))
        self.assertEqual(config["agents"]["codex"]["home"], str(root / "var/codex-home"))
        self.assertEqual(
            config["adapters"]["text2game"]["work_root"],
            str(root / "var/text2game-runs"),
        )
        self.assertEqual(config["adapters"]["text2game"]["repo"], "")

    def test_enabled_text2game_requires_pinned_inputs_and_no_second_cad_adapter(self) -> None:
        with self.assertRaisesRegex(ValueError, "enabled text2game adapter requires"):
            load_config(self.override({"adapters": {"text2game": {"enabled": True}}}))

        with self.assertRaisesRegex(ValueError, "cannot both be enabled"):
            load_config(
                self.override(
                    {
                        "adapters": {
                            "text2game": {
                                "enabled": True,
                                "repo": "/tmp/text2game",
                                "commit": "a" * 40,
                                "vibe_workspace": "/tmp/vibe",
                                "command": ["/usr/bin/python3"],
                                "text2cad_repo": "/tmp/text2cad",
                                "text2cad_commit": "b" * 40,
                                "cad_python": "/tmp/text2cad/.venv/bin/python",
                                "slicer_binary": "/usr/bin/prusa-slicer",
                                "slicer_profile": "/tmp/petg.ini",
                                "codex_binary": "/usr/bin/codex",
                                "codex_home": "/tmp/codex-home",
                                "git_binary": "/usr/bin/git",
                                "calibration_profile": "/tmp/profile.json",
                                "printer_target": {"printer_id": "printer-1"},
                            },
                            "cad_command": ["cad"],
                        }
                    }
                )
            )

    def test_text2game_environment_is_never_forwarded_to_the_model(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be forwarded to the model"):
            load_config(
                self.override(
                    {
                        "agents": {
                            "model_allowed_environment": ["PATH", "CAD_SERVICE_TOKEN"]
                        },
                        "adapters": {
                            "text2game": {
                                "allowed_environment": ["PATH", "CAD_SERVICE_TOKEN"]
                            }
                        },
                    }
                )
            )

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

    def test_publication_kill_switch_is_off_by_default(self) -> None:
        config = load_config()

        self.assertIs(config["objective"]["auto_publish_when_eligible"], False)

    def test_enabled_page_builder_requires_reviewed_source_and_binary_pins(self) -> None:
        with self.assertRaisesRegex(ValueError, "enabled page_builder requires"):
            load_config(
                self.override(
                    {
                        "adapters": {
                            "page_builder": {
                                "enabled": True,
                                "allowed_project_hosts": ["cdn.example.invalid"],
                            }
                        }
                    }
                )
            )

        configured = load_config(
            self.override(
                {
                    "adapters": {
                        "page_builder": {
                            "enabled": True,
                            "workspace": "/srv/vibe",
                            "workspace_commit": "a" * 40,
                            "operator_command": [
                                "/srv/vibe/.venv/bin/python",
                                "/srv/vibe/board-game/tools/publish.py",
                            ],
                            "interpreter_sha256": "b" * 64,
                            "operator_sha256": "c" * 64,
                            "operator_dependency_sha256": {
                                "animation_gate.py": "d" * 64,
                                "journal.py": "e" * 64,
                                "telegram.py": "f" * 64,
                            },
                            "publishdesign_sha256": "1" * 64,
                            "publishdesign_preflight_receipt": "/secure/page-builder-preflight.json",
                            "publishdesign_preflight_sha256": "3" * 64,
                            "git_binary": "/usr/bin/git",
                            "diagnostic_design_id": "private-diagnostic-draft",
                            "diagnostic_owner_id": "2" * 24,
                            "allowed_project_hosts": ["cdn.example.invalid"],
                        }
                    }
                }
            )
        )
        self.assertEqual(
            configured["adapters"]["page_builder"]["workspace_commit"],
            "a" * 40,
        )


if __name__ == "__main__":
    unittest.main()
