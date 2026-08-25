import importlib
import os
import sys
import tempfile
import unittest
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest import mock

from inventor_workshop.scaffold import scaffold_inventor
from inventor_workshop.workshop import WorkshopTools

ROOT = Path(__file__).resolve().parents[1]
INVENTOR_IDS = ("alice", "bob", "eve", "ivy", "leo")
COMMON_STAGE_FIELDS = (
    ("invent_job", "invent"),
    ("make_job", "make"),
    ("playtest_job", "playtest"),
    ("instructions_job", "instructions"),
    ("deliver_job", "deliver"),
)


def load_profile(inventor_id):
    path = ROOT / "inventors" / inventor_id / "profile.py"
    spec = importlib.util.spec_from_file_location(
        "shared_engine_profile_%s" % inventor_id,
        path,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class _Worker:
    """Callable identity marker; no model, filesystem, or network work occurs."""

    def __init__(self, stage):
        self.stage = stage

    def __call__(self, context):  # pragma: no cover - binding tests never execute it
        raise AssertionError("%s worker should only be bound" % self.stage)


class SharedEngineMatrixTest(unittest.TestCase):
    def setUp(self):
        self.shared = {
            stage: _Worker("shared-%s" % stage)
            for _, stage in COMMON_STAGE_FIELDS
        }

    @contextmanager
    def shared_engine(self):
        """Install deterministic stand-ins at every common component seam."""

        with ExitStack() as stack:
            stack.enter_context(
                mock.patch.dict(
                    os.environ,
                    {"WORKSHOP_AGENT_WORKERS": "codex"},
                    clear=True,
                )
            )
            stack.enter_context(
                mock.patch(
                    "inventor_workshop.agent_invent.CodexInventor",
                    return_value=self.shared["invent"],
                )
            )
            stack.enter_context(
                mock.patch(
                    "inventor_workshop.agent_make.CodexMaker",
                    return_value=self.shared["make"],
                )
            )
            stack.enter_context(
                mock.patch(
                    "inventor_workshop.agent_playtest.LaneAwarePlaytester",
                    return_value=self.shared["playtest"],
                )
            )
            stack.enter_context(
                mock.patch(
                    "inventor_workshop.agent_instructions.RewardedInstructions",
                    return_value=self.shared["instructions"],
                )
            )
            stack.enter_context(
                mock.patch(
                    "inventor_workshop.workshop.DefaultDeliver",
                    return_value=self.shared["deliver"],
                )
            )
            yield

    def assert_stage_bindings(self, workshop, expected):
        observed = {
            stage: getattr(workshop, attribute)
            for attribute, stage in COMMON_STAGE_FIELDS
        }
        self.assertEqual(set(observed), set(expected))
        for stage, worker in expected.items():
            with self.subTest(stage=stage):
                self.assertIs(observed[stage], worker)

    def test_all_five_inventors_inherit_every_common_stage(self):
        with tempfile.TemporaryDirectory() as temporary, self.shared_engine():
            runtime_base = Path(temporary).resolve()
            for inventor_id in INVENTOR_IDS:
                with self.subTest(inventor_id=inventor_id):
                    workshop = load_profile(inventor_id).build_workshop(
                        runtime_root=runtime_base / inventor_id
                    )
                    self.assert_stage_bindings(workshop, self.shared)
                    self.assertEqual(workshop.customization_level, "taste-only")

    def test_explicit_component_set_wins_for_every_inventor(self):
        custom = {
            stage: _Worker("explicit-%s" % stage)
            for _, stage in COMMON_STAGE_FIELDS
        }
        tools = WorkshopTools(**custom)
        with tempfile.TemporaryDirectory() as temporary, self.shared_engine():
            runtime_base = Path(temporary).resolve()
            for inventor_id in INVENTOR_IDS:
                with self.subTest(inventor_id=inventor_id):
                    workshop = load_profile(inventor_id).build_workshop(
                        tools=tools,
                        runtime_root=runtime_base / inventor_id,
                    )
                    self.assert_stage_bindings(workshop, custom)

    def test_profile_level_custom_make_and_playtest_override_shared_workers(self):
        custom_make = _Worker("bob-custom-make")
        custom_leo_make = _Worker("leo-custom-make")
        custom_leo_playtest = _Worker("leo-custom-playtest")
        with tempfile.TemporaryDirectory() as temporary, self.shared_engine():
            runtime_base = Path(temporary).resolve()
            bob = load_profile("bob").build_workshop(
                make=custom_make,
                runtime_root=runtime_base / "bob",
            )
            leo = load_profile("leo").build_workshop(
                make=custom_leo_make,
                playtest=custom_leo_playtest,
                runtime_root=runtime_base / "leo",
            )

        self.assertIs(bob.invent_job, self.shared["invent"])
        self.assertIs(bob.make_job, custom_make)
        self.assertIs(bob.playtest_job, self.shared["playtest"])
        self.assertIs(bob.instructions_job, self.shared["instructions"])
        self.assertIs(bob.deliver_job, self.shared["deliver"])
        self.assertEqual(bob.customization_level, "custom-make")

        self.assertIs(leo.invent_job, self.shared["invent"])
        self.assertIs(leo.make_job, custom_leo_make)
        self.assertIs(leo.playtest_job, custom_leo_playtest)
        self.assertIs(leo.instructions_job, self.shared["instructions"])
        self.assertIs(leo.deliver_job, self.shared["deliver"])
        self.assertEqual(leo.customization_level, "custom-playtest")

    def test_new_inventor_scaffolds_only_replace_the_declared_seams(self):
        cases = (
            ("taste-only", "matrix-taste"),
            ("custom-make", "matrix-make"),
            ("custom-playtest", "matrix-playtest"),
        )
        with tempfile.TemporaryDirectory() as temporary, self.shared_engine():
            root = Path(temporary).resolve()
            for level, inventor_id in cases:
                with self.subTest(level=level):
                    destination = scaffold_inventor(
                        root,
                        inventor_id,
                        "Matrix %s" % level,
                        "deterministic contract toys",
                        lane="moving-machines",
                        level=level,
                    )
                    package = inventor_id.replace("-", "_")
                    source_root = str(destination / "src")
                    sys.path.insert(0, source_root)
                    try:
                        importlib.invalidate_caches()
                        module = importlib.import_module(package + ".__main__")
                        workshop = module.build_workshop(
                            runtime_root=root / (inventor_id + "-runtime")
                        )
                    finally:
                        sys.path.remove(source_root)
                        for name in tuple(sys.modules):
                            if name == package or name.startswith(package + "."):
                                del sys.modules[name]

                    self.assertIs(workshop.invent_job, self.shared["invent"])
                    self.assertIs(
                        workshop.make_job,
                        self.shared["make"]
                        if level == "taste-only"
                        else module.CUSTOM_MAKE,
                    )
                    self.assertIs(
                        workshop.playtest_job,
                        module.CUSTOM_PLAYTEST
                        if level == "custom-playtest"
                        else self.shared["playtest"],
                    )
                    self.assertIs(
                        workshop.instructions_job, self.shared["instructions"]
                    )
                    self.assertIs(workshop.deliver_job, self.shared["deliver"])
                    self.assertEqual(workshop.customization_level, level)


if __name__ == "__main__":
    unittest.main()
