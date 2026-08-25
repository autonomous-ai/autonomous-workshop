import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from inventor_workshop.agent_invent import configured_workshop_tools
from inventor_workshop.errors import ContractError
from inventor_workshop.workshop import WorkshopTools


class ConfiguredWorkshopToolsTest(unittest.TestCase):
    def test_disabled_configuration_preserves_an_explicit_tool_set(self):
        explicit = WorkshopTools(make=mock.Mock(), deliver=mock.Mock())
        with mock.patch.dict(os.environ, {}, clear=True):
            selected = configured_workshop_tools(explicit)
        self.assertIs(selected, explicit)

    def test_legacy_switch_adds_only_missing_invent(self):
        explicit_make = mock.Mock()
        explicit_deliver = mock.Mock()
        invented = mock.Mock()
        existing = WorkshopTools(make=explicit_make, deliver=explicit_deliver)
        with mock.patch.dict(
            os.environ,
            {"WORKSHOP_INVENT_WORKER": "codex"},
            clear=True,
        ), mock.patch(
            "inventor_workshop.agent_invent.CodexInventor",
            return_value=invented,
        ) as constructor:
            selected = configured_workshop_tools(existing)
        constructor.assert_called_once_with()
        self.assertIs(selected.invent, invented)
        self.assertIs(selected.make, explicit_make)
        self.assertIsNone(selected.playtest)
        self.assertIsNone(selected.instructions)
        self.assertIs(selected.deliver, explicit_deliver)

    def test_full_switch_installs_all_shared_workers_without_factory_secrets(self):
        invented = mock.Mock()
        made = mock.Mock()
        playtested = mock.Mock()
        with mock.patch.dict(
            os.environ,
            {"WORKSHOP_AGENT_WORKERS": "codex"},
            clear=True,
        ), mock.patch(
            "inventor_workshop.agent_invent.CodexInventor", return_value=invented
        ), mock.patch(
            "inventor_workshop.agent_make.CodexMaker", return_value=made
        ), mock.patch(
            "inventor_workshop.agent_playtest.LaneAwarePlaytester",
            return_value=playtested,
        ):
            selected = configured_workshop_tools()
        self.assertIs(selected.invent, invented)
        self.assertIs(selected.make, made)
        self.assertIs(selected.playtest, playtested)
        self.assertIsNone(selected.instructions)
        self.assertIsNone(selected.deliver)

    def test_full_switch_preserves_every_explicit_non_none_tool(self):
        explicit = WorkshopTools(
            invent=mock.Mock(),
            make=mock.Mock(),
            playtest=mock.Mock(),
            instructions=mock.Mock(),
            deliver=mock.Mock(),
        )
        with mock.patch.dict(
            os.environ,
            {
                "WORKSHOP_AGENT_WORKERS": "codex",
                # An explicit Instructions adapter means Factory credentials are
                # outside this helper's responsibility and must not be loaded.
                "FACTORY_USERNAME": "partial-is-deliberately-ignored",
            },
            clear=True,
        ), mock.patch(
            "inventor_workshop.agent_invent.CodexInventor"
        ) as invent_constructor, mock.patch(
            "inventor_workshop.agent_make.CodexMaker"
        ) as make_constructor, mock.patch(
            "inventor_workshop.agent_playtest.LaneAwarePlaytester"
        ) as playtest_constructor:
            selected = configured_workshop_tools(explicit)
        invent_constructor.assert_not_called()
        make_constructor.assert_not_called()
        playtest_constructor.assert_not_called()
        self.assertIs(selected.invent, explicit.invent)
        self.assertIs(selected.make, explicit.make)
        self.assertIs(selected.playtest, explicit.playtest)
        self.assertIs(selected.instructions, explicit.instructions)
        self.assertIs(selected.deliver, explicit.deliver)

    def test_factory_pair_builds_rewarded_instructions_on_shared_runtime_store(self):
        invented = mock.Mock()
        made = mock.Mock()
        playtested = mock.Mock()
        store = mock.Mock()
        writer = mock.Mock()
        rewarded = mock.Mock()
        with tempfile.TemporaryDirectory() as temporary:
            runtime_root = Path(temporary).resolve() / "alice-runtime"
            with mock.patch.dict(
                os.environ,
                {
                    "WORKSHOP_AGENT_WORKERS": "codex",
                    "FACTORY_USERNAME": "alice",
                    "FACTORY_PASSWORD": "test-only-password",
                },
                clear=True,
            ), mock.patch(
                "inventor_workshop.agent_invent.CodexInventor", return_value=invented
            ), mock.patch(
                "inventor_workshop.agent_make.CodexMaker", return_value=made
            ), mock.patch(
                "inventor_workshop.agent_playtest.LaneAwarePlaytester",
                return_value=playtested,
            ), mock.patch(
                "inventor_workshop.store.InventorStore", return_value=store
            ) as store_constructor, mock.patch(
                "inventor_workshop.factory_agent.FactoryAgentInstructionsWriter",
                return_value=writer,
            ) as writer_constructor, mock.patch(
                "inventor_workshop.agent_instructions.RewardedInstructions",
                return_value=rewarded,
            ) as rewarded_constructor:
                selected = configured_workshop_tools(
                    inventor_id="alice",
                    runtime_root=runtime_root,
                )

        store_constructor.assert_called_once_with(runtime_root / "workshop.sqlite3")
        writer_args = writer_constructor.call_args.args
        self.assertEqual(writer_args[:2], (store, "alice"))
        self.assertEqual(writer_args[2].username, "alice")
        self.assertEqual(
            repr(writer_args[2]),
            "FactoryAgentCredentials(username=<redacted>, password=<redacted>)",
        )
        rewarded_constructor.assert_called_once_with(writer)
        self.assertIs(selected.instructions, rewarded)

    def test_partial_factory_pair_fails_instead_of_silently_disabling_auth(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.dict(
            os.environ,
            {
                "WORKSHOP_AGENT_WORKERS": "codex",
                "FACTORY_USERNAME": "alice",
            },
            clear=True,
        ), mock.patch(
            "inventor_workshop.agent_invent.CodexInventor", return_value=mock.Mock()
        ), mock.patch(
            "inventor_workshop.agent_make.CodexMaker", return_value=mock.Mock()
        ), mock.patch(
            "inventor_workshop.agent_playtest.LaneAwarePlaytester",
            return_value=mock.Mock(),
        ):
            with self.assertRaisesRegex(
                ContractError,
                "username/password must be configured together",
            ):
                configured_workshop_tools(
                    inventor_id="alice",
                    runtime_root=Path(temporary).resolve(),
                )

    def test_factory_configuration_requires_absolute_runtime_root(self):
        with mock.patch.dict(
            os.environ,
            {
                "WORKSHOP_AGENT_WORKERS": "codex",
                "FACTORY_USERNAME": "alice",
                "FACTORY_PASSWORD": "test-only-password",
            },
            clear=True,
        ), mock.patch(
            "inventor_workshop.agent_invent.CodexInventor", return_value=mock.Mock()
        ), mock.patch(
            "inventor_workshop.agent_make.CodexMaker", return_value=mock.Mock()
        ), mock.patch(
            "inventor_workshop.agent_playtest.LaneAwarePlaytester",
            return_value=mock.Mock(),
        ):
            with self.assertRaisesRegex(ContractError, "runtime_root must be absolute"):
                configured_workshop_tools(
                    inventor_id="alice",
                    runtime_root=Path("relative-runtime"),
                )

    def test_rejects_an_untyped_existing_value(self):
        with mock.patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(
            ContractError,
            "WorkshopTools",
        ):
            configured_workshop_tools(object())


if __name__ == "__main__":
    unittest.main()
