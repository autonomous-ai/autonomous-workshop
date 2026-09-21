"""The correction carry policy is frozen at run creation and costs nothing when off.

The policy only ever changes what a Make round may CARRY FORWARD from the
source archive. Three properties matter more than the flag and are the reason
these tests exist: a run that cannot carry must produce byte identical frozen
options to a run started before the policy existed, a motion rebind on resume
must not silently drop the policy a run was created under, and a run created
while the policy was opt-in -- which wrote the field as `quick_fix` -- must
still read as carrying.
"""
import contextlib
import json
from pathlib import Path
import runpy
import shutil
import sys
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[2]
SCRIPTS = REPOSITORY / "src/workshop/make/skills/cad/scripts"
sys.path.insert(0, str(REPOSITORY / "src"))

from workshop.errors import ContractError, StateConflict  # noqa: E402
from workshop.workflow.agent_run import (  # noqa: E402
    _frozen_carry_unchanged,
    _make_options_bytes,
)


def _legacy_bytes(check_motion):
    """Exactly what the host wrote before the carry policy existed."""
    return json.dumps(
        {"schema_version": 1, "check_motion": check_motion},
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


class FrozenOptionBytesTest(unittest.TestCase):
    def test_a_run_that_cannot_carry_keeps_the_pre_policy_bytes(self):
        # A new option must not move the checkpoint hash of every ordinary run.
        for check_motion in (False, True):
            self.assertEqual(
                _make_options_bytes(check_motion=check_motion, carry_unchanged=False),
                _legacy_bytes(check_motion),
            )

    def test_carrying_declares_its_own_schema(self):
        for check_motion in (False, True):
            payload = json.loads(
                _make_options_bytes(check_motion=check_motion, carry_unchanged=True)
            )
            self.assertEqual(payload, {
                "schema_version": 2,
                "check_motion": check_motion,
                "carry_unchanged": True,
            })

    def test_non_boolean_options_are_refused(self):
        with self.assertRaises(ContractError):
            _make_options_bytes(check_motion=False, carry_unchanged="true")
        with self.assertRaises(ContractError):
            _make_options_bytes(check_motion=1, carry_unchanged=False)


class FrozenQuickFixReadbackTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def write(self, payload):
        (self.root / "MAKE-OPTIONS.json").write_text(
            json.dumps(payload, sort_keys=True, separators=(",", ":"))
        )

    def test_absent_options_read_as_declined(self):
        self.assertFalse(_frozen_carry_unchanged(self.root))

    def test_schema_one_reads_as_declined(self):
        self.write({"schema_version": 1, "check_motion": True})
        self.assertFalse(_frozen_carry_unchanged(self.root))

    def test_schema_two_round_trips(self):
        for choice in (False, True):
            self.write({"schema_version": 2, "check_motion": False,
                        "carry_unchanged": choice})
            self.assertIs(_frozen_carry_unchanged(self.root), choice)

    def test_a_resume_rebind_preserves_the_selection(self):
        # `workshop resume --check-motion` rewrites this file. The operator
        # is created under the policy once, and a later motion rebind is not
        # an opportunity to revoke it.
        self.write({"schema_version": 2, "check_motion": False,
                    "carry_unchanged": True})
        rebound = _make_options_bytes(
            check_motion=True, carry_unchanged=_frozen_carry_unchanged(self.root),
        )
        self.assertEqual(json.loads(rebound), {
            "schema_version": 2, "check_motion": True, "carry_unchanged": True,
        })

    def test_the_original_field_name_still_reads_as_carrying(self):
        # Corrections created while the policy was opt-in wrote `quick_fix`.
        # Step 11 of the Antisol chain is one, and it must not silently stop
        # carrying if it is resumed after the rename.
        self.write({"schema_version": 2, "check_motion": False,
                    "quick_fix": True})
        self.assertTrue(_frozen_carry_unchanged(self.root))

    def test_a_corrupt_selection_is_refused_rather_than_assumed(self):
        self.write({"schema_version": 2, "check_motion": False,
                    "carry_unchanged": "yes"})
        with self.assertRaises(StateConflict):
            _frozen_carry_unchanged(self.root)


class ToolSidePolicyTest(unittest.TestCase):
    """The reader the CAD and make-round tools actually call."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def materialize(self, payload):
        (self.root / ".workshop-product-run-root").write_text("fixture product run")
        scripts = self.root / ".agents/skills/cad/scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SCRIPTS / "motion_policy.py", scripts / "motion_policy.py")
        if payload is not None:
            (self.root / "MAKE-OPTIONS.json").write_text(
                json.dumps(payload, sort_keys=True, separators=(",", ":"))
            )
        return runpy.run_path(str(scripts / "motion_policy.py"))

    def test_standalone_tools_never_carry(self):
        module = runpy.run_path(str(SCRIPTS / "motion_policy.py"))
        self.assertFalse(module["carry_unchanged"]())

    def test_older_runs_read_as_declined(self):
        for payload in (None, {"schema_version": 1, "check_motion": False},
                        {"schema_version": 1, "check_motion": True}):
            module = self.materialize(payload)
            with contextlib.chdir(self.root.parent):
                self.assertFalse(module["carry_unchanged"]())

    def test_the_carry_policy_is_read_independently_of_motion(self):
        for check_motion in (False, True):
            for quick in (False, True):
                module = self.materialize({
                    "schema_version": 2,
                    "check_motion": check_motion,
                    "carry_unchanged": quick,
                })
                with contextlib.chdir(self.root.parent):
                    self.assertIs(module["enabled"](), check_motion)
                    self.assertIs(module["carry_unchanged"](), quick)

    def test_a_schema_two_document_missing_its_selection_is_refused(self):
        module = self.materialize({"schema_version": 2, "check_motion": False})
        with contextlib.chdir(self.root.parent):
            for name in ("enabled", "carry_unchanged"):
                with self.assertRaisesRegex(ValueError, "invalid frozen Make options"):
                    module[name]()

    def test_the_tool_reads_the_original_field_name_too(self):
        module = self.materialize({"schema_version": 2, "check_motion": False,
                                   "quick_fix": True})
        with contextlib.chdir(self.root.parent):
            self.assertTrue(module["carry_unchanged"]())
            self.assertTrue(module["quick_fix"]())

    def test_both_carry_field_names_at_once_are_refused(self):
        module = self.materialize({"schema_version": 2, "check_motion": False,
                                   "carry_unchanged": True, "quick_fix": True})
        with contextlib.chdir(self.root.parent):
            with self.assertRaisesRegex(ValueError, "invalid frozen Make options"):
                module["carry_unchanged"]()

    def test_an_unknown_schema_is_refused_rather_than_guessed(self):
        module = self.materialize({"schema_version": 3, "check_motion": False,
                                   "carry_unchanged": True})
        with contextlib.chdir(self.root.parent):
            with self.assertRaisesRegex(ValueError, "invalid frozen Make options"):
                module["carry_unchanged"]()


if __name__ == "__main__":
    unittest.main()
