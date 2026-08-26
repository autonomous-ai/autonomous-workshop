import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workshop.bootstrap import configured_workshop, configured_workshop_tools
from workshop.errors import ContractError
from workshop.playtest.gameplay import FINITE_GAME_SIMULATOR_SOURCE
from workshop.workflow import Workshop, WorkshopTools


class ConfiguredWorkshopToolsTest(unittest.TestCase):
    @staticmethod
    def inventor_root(root):
        inventor = root / "alice"
        inventor.mkdir()
        (inventor / "TASTE.md").write_text(
            "---\n"
            "name: Alice Display Name\n"
            "description: Familiar games remade as personal objects.\n"
            "---\n"
            "# Taste\n\nFamiliar games remade as personal objects.\n",
            encoding="utf-8",
        )
        return inventor

    def test_application_factory_merges_bare_partial_and_custom_tools(self):
        explicit_invent = mock.Mock(name="explicit-invent")
        custom_make = mock.Mock(name="custom-make")
        custom_playtest = mock.Mock(name="custom-playtest")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            inventor = self.inventor_root(root)
            with mock.patch.dict(os.environ, {}, clear=True), mock.patch(
                "workshop.invent.agent.CodexInventor",
                side_effect=lambda: mock.Mock(name="shared-invent"),
            ), mock.patch(
                "workshop.make.agent.CodexMaker",
                side_effect=lambda **kwargs: mock.Mock(
                    name="shared-make",
                    game_simulator_source=kwargs.get("game_simulator_source"),
                ),
            ), mock.patch(
                "workshop.playtest.agent.LaneAwarePlaytester",
                side_effect=lambda: mock.Mock(name="shared-playtest"),
            ), mock.patch(
                "workshop.release.agent.RewardedRelease",
                side_effect=lambda writer: mock.Mock(
                    name="shared-release", site_writer=writer
                ),
            ):
                bare = configured_workshop(
                    inventor,
                    "classics-made-yours",
                    runtime_root=root / "bare-runtime",
                )
                partial = configured_workshop(
                    inventor,
                    "classics-made-yours",
                    tools=WorkshopTools(invent=explicit_invent),
                    runtime_root=root / "partial-runtime",
                )
                custom_make_workshop = configured_workshop(
                    inventor,
                    "classics-made-yours",
                    make=custom_make,
                    runtime_root=root / "custom-make-runtime",
                )
                custom_playtest_workshop = configured_workshop(
                    inventor,
                    "classics-made-yours",
                    make=custom_make,
                    playtest=custom_playtest,
                    runtime_root=root / "custom-playtest-runtime",
                )

        self.assertEqual(bare.inventor_id, "alice")
        self.assertIsNotNone(bare.tools.invent)
        self.assertIsNotNone(bare.tools.make)
        self.assertEqual(
            bare.tools.make.game_simulator_source,
            FINITE_GAME_SIMULATOR_SOURCE,
        )
        self.assertIsNotNone(bare.tools.playtest)
        self.assertIsNotNone(bare.tools.release)
        self.assertIs(partial.tools.invent, explicit_invent)
        self.assertIsNotNone(partial.tools.make)
        self.assertIsNotNone(partial.tools.playtest)
        self.assertIs(custom_make_workshop.make_job, custom_make)
        self.assertIsNotNone(custom_make_workshop.playtest_job)
        self.assertEqual(custom_make_workshop.customization_level, "custom-make")
        self.assertIs(custom_playtest_workshop.make_job, custom_make)
        self.assertIs(custom_playtest_workshop.playtest_job, custom_playtest)
        self.assertEqual(
            custom_playtest_workshop.customization_level, "custom-playtest"
        )

    def test_workshop_honors_explicit_shared_worker_disable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            inventor = self.inventor_root(root)
            with mock.patch.dict(
                os.environ, {"WORKSHOP_AGENT_WORKERS": "disabled"}, clear=True
            ):
                workshop = configured_workshop(
                    inventor,
                    "classics-made-yours",
                    runtime_root=root / "disabled-runtime",
                )
        self.assertIsNone(workshop.tools.invent)
        self.assertIsNone(workshop.tools.make)
        self.assertIsNone(workshop.tools.playtest)
        self.assertIsNone(workshop.tools.release)

    def test_workflow_constructor_never_calls_application_composition(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            inventor = self.inventor_root(root)
            with mock.patch(
                "workshop.bootstrap.configured_workshop_tools"
            ) as composer:
                workshop = Workshop(
                    inventor,
                    "classics-made-yours",
                    runtime_root=root / "explicit-runtime",
                )
        composer.assert_not_called()
        self.assertIsNone(workshop.tools.invent)
        self.assertIsNone(workshop.tools.make)
        self.assertIsNone(workshop.tools.playtest)
        self.assertIsNone(workshop.tools.release)

    def test_disabled_configuration_preserves_an_explicit_tool_set(self):
        explicit = WorkshopTools(make=mock.Mock(), deliver=mock.Mock())
        with mock.patch.dict(
            os.environ, {"WORKSHOP_AGENT_WORKERS": "disabled"}, clear=True
        ):
            selected = configured_workshop_tools(explicit)
        self.assertIs(selected, explicit)

    def test_shared_workers_are_on_by_default_without_an_environment_switch(self):
        invented = mock.Mock()
        made = mock.Mock()
        playtested = mock.Mock()
        rewarded = mock.Mock()
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch(
            "workshop.invent.agent.CodexInventor", return_value=invented
        ), mock.patch(
            "workshop.make.agent.CodexMaker", return_value=made
        ), mock.patch(
            "workshop.playtest.agent.LaneAwarePlaytester",
            return_value=playtested,
        ), mock.patch(
            "workshop.release.agent.RewardedRelease",
            return_value=rewarded,
        ) as rewarded_constructor:
            selected = configured_workshop_tools()
        self.assertIs(selected.invent, invented)
        self.assertIs(selected.make, made)
        self.assertIs(selected.playtest, playtested)
        rewarded_constructor.assert_called_once_with(None)
        self.assertIs(selected.release, rewarded)

    def test_legacy_invent_switch_cannot_disable_other_shared_defaults(self):
        explicit_make = mock.Mock()
        explicit_deliver = mock.Mock()
        invented = mock.Mock()
        playtested = mock.Mock()
        rewarded = mock.Mock()
        existing = WorkshopTools(make=explicit_make, deliver=explicit_deliver)
        with mock.patch.dict(
            os.environ,
            {"WORKSHOP_INVENT_WORKER": "codex"},
            clear=True,
        ), mock.patch(
            "workshop.invent.agent.CodexInventor",
            return_value=invented,
        ) as constructor, mock.patch(
            "workshop.playtest.agent.LaneAwarePlaytester",
            return_value=playtested,
        ), mock.patch(
            "workshop.release.agent.RewardedRelease",
            return_value=rewarded,
        ):
            selected = configured_workshop_tools(existing)
        constructor.assert_called_once_with()
        self.assertIs(selected.invent, invented)
        self.assertIs(selected.make, explicit_make)
        self.assertIs(selected.playtest, playtested)
        self.assertIs(selected.release, rewarded)
        self.assertIs(selected.deliver, explicit_deliver)

    def test_rejects_unknown_legacy_invent_mode(self):
        with mock.patch.dict(
            os.environ, {"WORKSHOP_INVENT_WORKER": "invent-only"}, clear=True
        ):
            with self.assertRaisesRegex(
                ContractError, "WORKSHOP_INVENT_WORKER must be codex or unset"
            ):
                configured_workshop_tools()

    def test_full_switch_installs_all_shared_workers_without_factory_secrets(self):
        invented = mock.Mock()
        made = mock.Mock()
        playtested = mock.Mock()
        rewarded = mock.Mock()
        with mock.patch.dict(
            os.environ,
            {"WORKSHOP_AGENT_WORKERS": "codex"},
            clear=True,
        ), mock.patch(
            "workshop.invent.agent.CodexInventor", return_value=invented
        ), mock.patch(
            "workshop.make.agent.CodexMaker", return_value=made
        ), mock.patch(
            "workshop.playtest.agent.LaneAwarePlaytester",
            return_value=playtested,
        ), mock.patch(
            "workshop.release.agent.RewardedRelease",
            return_value=rewarded,
        ) as rewarded_constructor:
            selected = configured_workshop_tools()
        self.assertIs(selected.invent, invented)
        self.assertIs(selected.make, made)
        self.assertIs(selected.playtest, playtested)
        rewarded_constructor.assert_called_once_with(None)
        self.assertIs(selected.release, rewarded)
        self.assertIsNone(selected.deliver)

    def test_full_switch_preserves_every_explicit_non_none_tool(self):
        explicit = WorkshopTools(
            invent=mock.Mock(),
            make=mock.Mock(),
            playtest=mock.Mock(),
            release=mock.Mock(),
            deliver=mock.Mock(),
        )
        with mock.patch.dict(
            os.environ,
            {
                "WORKSHOP_AGENT_WORKERS": "codex",
                # An explicit Release adapter means Factory credentials are
                # outside this helper's responsibility and must not be loaded.
                "FACTORY_USERNAME": "partial-is-deliberately-ignored",
            },
            clear=True,
        ), mock.patch(
            "workshop.invent.agent.CodexInventor"
        ) as invent_constructor, mock.patch(
            "workshop.make.agent.CodexMaker"
        ) as make_constructor, mock.patch(
            "workshop.playtest.agent.LaneAwarePlaytester"
        ) as playtest_constructor:
            selected = configured_workshop_tools(explicit)
        invent_constructor.assert_not_called()
        make_constructor.assert_not_called()
        playtest_constructor.assert_not_called()
        self.assertIs(selected.invent, explicit.invent)
        self.assertIs(selected.make, explicit.make)
        self.assertIs(selected.playtest, explicit.playtest)
        self.assertIs(selected.release, explicit.release)
        self.assertIs(selected.deliver, explicit.deliver)

    def test_factory_pair_builds_rewarded_release_on_shared_runtime_store(self):
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
                "workshop.invent.agent.CodexInventor", return_value=invented
            ), mock.patch(
                "workshop.make.agent.CodexMaker", return_value=made
            ), mock.patch(
                "workshop.playtest.agent.LaneAwarePlaytester",
                return_value=playtested,
            ), mock.patch(
                "workshop.runtime.store.InventorStore", return_value=store
            ) as store_constructor, mock.patch(
                "workshop.integrations.factory_agent.FactoryAgentReleaseWriter",
                return_value=writer,
            ) as writer_constructor, mock.patch(
                "workshop.release.agent.RewardedRelease",
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
        self.assertIs(selected.release, rewarded)

    def test_partial_factory_pair_fails_instead_of_silently_disabling_auth(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.dict(
            os.environ,
            {
                "WORKSHOP_AGENT_WORKERS": "codex",
                "FACTORY_USERNAME": "alice",
            },
            clear=True,
        ), mock.patch(
            "workshop.invent.agent.CodexInventor", return_value=mock.Mock()
        ), mock.patch(
            "workshop.make.agent.CodexMaker", return_value=mock.Mock()
        ), mock.patch(
            "workshop.playtest.agent.LaneAwarePlaytester",
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
            "workshop.invent.agent.CodexInventor", return_value=mock.Mock()
        ), mock.patch(
            "workshop.make.agent.CodexMaker", return_value=mock.Mock()
        ), mock.patch(
            "workshop.playtest.agent.LaneAwarePlaytester",
            return_value=mock.Mock(),
        ):
            with self.assertRaisesRegex(ContractError, "runtime_root must be absolute"):
                configured_workshop_tools(
                    inventor_id="alice",
                    runtime_root=Path("relative-runtime"),
                )

    def test_rejects_an_untyped_existing_value(self):
        with self.assertRaisesRegex(ContractError, "WorkshopTools"):
            configured_workshop_tools(object())

    def test_rejects_an_unknown_worker_mode(self):
        with mock.patch.dict(
            os.environ, {"WORKSHOP_AGENT_WORKERS": "sometimes"}, clear=True
        ), self.assertRaisesRegex(ContractError, "codex, disabled, or unset"):
            configured_workshop_tools()


if __name__ == "__main__":
    unittest.main()
