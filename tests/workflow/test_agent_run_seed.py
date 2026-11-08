"""ADR 0096: a run seeded from an Approved Proof seals the Proof under seed/.

Contract: `AgentRun.create(seed=, seed_files=)` materializes every seed file
read-only under `seed/`, outside the ordinary input budget, and freezes the
seed's two hashes in `MAKE-OPTIONS.json` schema 3. A resume rewrite keeps the
seed, so no resume adds or drops it. A changed seed file, an APPROVAL.json
that is not the frozen one, seed files without a frozen seed, a seed without
files and a path outside seed/ all refuse."""

from __future__ import annotations

import hashlib
import json
import stat
import unittest

from tests.workflow import test_agent_run as base
from workshop.errors import ContractError, StateConflict
from workshop.workflow.agent_run import AgentRun, _make_options_bytes

APPROVAL = b'{"schema_version":1}\n'
FILES = {
    "APPROVAL.json": APPROVAL,
    "part_body.step.py": b"def gen_step(): return 'b'\n",
    "approved/part_body.step": b"ISO-10303-21;\n",
}


def frozen(approval=APPROVAL):
    return {"approval_sha256": hashlib.sha256(approval).hexdigest(), "manifest_sha256": "a" * 64}


class SeededAgentRunTest(unittest.TestCase):
    setUp = base.AgentRunTest.setUp
    create = base.AgentRunTest.create

    def test_seed_files_are_sealed_read_only_and_frozen_in_make_options(self):
        run = self.create(seed=frozen(), seed_files=FILES)
        root = self.run_root / "seed"
        for name, content in FILES.items():
            path = root / name
            self.assertEqual(path.read_bytes(), content)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o400)
            self.assertIn("seed/" + name, run.snapshot().input_sha256s)
        self.assertEqual(stat.S_IMODE(root.stat().st_mode), 0o500)
        self.assertEqual(stat.S_IMODE((root / "approved").stat().st_mode), 0o500)
        options = json.loads((self.run_root / "MAKE-OPTIONS.json").read_bytes())
        self.assertEqual(options, {"schema_version": 3, "check_motion": False, "seed": frozen()})

    def test_carry_unchanged_rides_beside_the_seed(self):
        # A seeded correction: carry_unchanged needs a revision source, so
        # the options bytes are checked directly.
        options = json.loads(_make_options_bytes(check_motion=False, carry_unchanged=True, seed=frozen()))
        self.assertEqual(options["schema_version"], 3)
        self.assertIs(options["carry_unchanged"], True)
        self.assertEqual(options["seed"], frozen())

    def test_a_resume_rewrite_keeps_the_seed(self):
        run = self.create(seed=frozen(), seed_files=FILES)
        run.refresh_domain_skill_tools({}, reason="operator resume", check_motion=True)
        options = json.loads((self.run_root / "MAKE-OPTIONS.json").read_bytes())
        self.assertEqual((options["schema_version"], options["check_motion"], options["seed"]),
                         (3, True, frozen()))
        reopened = AgentRun.open(self.run_root, host_state_root=self.host_state_root)
        self.assertIn("seed/APPROVAL.json", reopened.snapshot().input_sha256s)

    def test_a_tool_refresh_rebinds_a_frozen_batch_and_keeps_check_motion(self):
        """Issue #244: a run froze its seeded batch tool, so a harness fix
        to it could never reach the run; the operator's refresh rebinds it
        with the other host tools. check_motion and the seed stay."""
        batched = {**frozen(), "batch": {"tool_sha256": "b" * 64}}
        run = self.create(seed=batched, seed_files=FILES, check_motion=True)
        changes = run.refresh_domain_skill_tools({}, reason="workshop resume --refresh-tools",
                                                 seed_batch_tool_sha256="c" * 64, dry_run=True)
        self.assertEqual([item["path"] for item in changes], ["MAKE-OPTIONS.json"])
        self.assertEqual(json.loads((self.run_root / "MAKE-OPTIONS.json").read_bytes())["seed"], batched)
        run.refresh_domain_skill_tools({}, reason="workshop resume --refresh-tools",
                                       seed_batch_tool_sha256="c" * 64)
        options = json.loads((self.run_root / "MAKE-OPTIONS.json").read_bytes())
        self.assertEqual(options, {"schema_version": 4, "check_motion": True,
                                   "seed": {**frozen(), "batch": {"tool_sha256": "c" * 64}}})
        reopened = AgentRun.open(self.run_root, host_state_root=self.host_state_root)
        self.assertIn("MAKE-OPTIONS.json", reopened.snapshot().input_sha256s)
        # The same tool again changes nothing.
        self.assertEqual(run.refresh_domain_skill_tools({}, reason="workshop resume --refresh-tools",
                                                        seed_batch_tool_sha256="c" * 64), ())

    def test_a_tool_refresh_never_adds_a_batch(self):
        for seed in (frozen(), None):
            with self.subTest(seeded=seed is not None):
                self.setUp()
                run = self.create(**({"seed": seed, "seed_files": FILES} if seed else {}))
                before = (self.run_root / "MAKE-OPTIONS.json").read_bytes()
                self.assertEqual(run.refresh_domain_skill_tools(
                    {}, reason="workshop resume --refresh-tools", seed_batch_tool_sha256="c" * 64), ())
                self.assertEqual((self.run_root / "MAKE-OPTIONS.json").read_bytes(), before)

    def test_a_malformed_batch_tool_hash_is_refused(self):
        run = self.create(seed={**frozen(), "batch": {"tool_sha256": "b" * 64}}, seed_files=FILES)
        with self.assertRaises(ContractError):
            run.refresh_domain_skill_tools({}, reason="workshop resume --refresh-tools",
                                           seed_batch_tool_sha256="not-a-hash")

    def test_a_changed_seed_file_is_refused(self):
        run = self.create(seed=frozen(), seed_files=FILES)
        path = self.run_root / "seed/part_body.step.py"
        path.parent.chmod(0o700)
        path.chmod(0o600)
        path.write_bytes(b"def gen_step(): return 'other'\n")
        with self.assertRaises(StateConflict):
            run.snapshot()

    def test_an_approval_other_than_the_frozen_one_refuses_before_materializing(self):
        with self.assertRaisesRegex(ContractError, "not the frozen approval"):
            self.create(seed=frozen(b"other"), seed_files=FILES)
        self.assertFalse(self.run_root.exists())

    def test_seed_and_files_come_together(self):
        for kwargs in ({"seed": frozen()}, {"seed_files": FILES}, {"seed": frozen(), "seed_files": {}}):
            with self.subTest(kwargs=sorted(kwargs)), self.assertRaises(ContractError):
                self.create(**kwargs)
            self.assertFalse(self.run_root.exists())

    def test_a_seed_freezes_exactly_two_hashes(self):
        for seed in ({"approval_sha256": frozen()["approval_sha256"]},
                     dict(frozen(), extra="b" * 64),
                     dict(frozen(), manifest_sha256="short")):
            with self.subTest(seed=sorted(seed)), self.assertRaises(ContractError):
                self.create(seed=seed, seed_files=FILES)

    def test_a_seed_path_outside_seed_is_refused(self):
        for name in ("../escape.py", "/abs.py"):
            files = dict(FILES, **{name: b"x"})
            with self.subTest(name=name), self.assertRaises(ContractError):
                self.create(seed=frozen(), seed_files=files)
            self.assertFalse(self.run_root.exists())

    def test_seed_files_without_a_frozen_seed_are_refused(self):
        run = self.create(seed=frozen(), seed_files=FILES)
        payload = run._load()
        options = b'{"check_motion":false,"schema_version":1}'
        path = self.run_root / "MAKE-OPTIONS.json"
        path.chmod(0o600)
        path.write_bytes(options)
        path.chmod(0o400)
        inputs = [dict(item, sha256=hashlib.sha256(options).hexdigest(), size=len(options))
                  if item["path"] == "MAKE-OPTIONS.json" else item for item in payload["inputs"]]
        with self.assertRaises(StateConflict):
            run._write_next(payload, dict(payload, inputs=inputs))
            run.snapshot()


if __name__ == "__main__":
    unittest.main()
