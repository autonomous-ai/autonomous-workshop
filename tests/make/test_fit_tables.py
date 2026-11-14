"""ADR 0105: an Approved Proof keeps the cadfits fit table it was approved with.

Contract:
- The vendored cadfits builds with the table ``WORKSHOP_FIT_TABLE`` names:
  unset is the current table, ``fits-legacy`` the one every Proof sealed
  before 2026-11-13 built with (slip 0.20, snug 0.10, default slip), and an
  unknown name refuses to import. Workshop's names are cadfits' names.
- An approval's table is its ``fit_table``; without one, the resync's LOCK
  hash means the current table and any other the legacy table. An unknown
  ``fit_table`` refuses.
- make_round pins a seeded run's approval table for itself and its
  children, and gives its caller's environment back; outside a seeded run
  it sets nothing.
- The host's seeded batch steps see the approval's table.
- The warm daemon socket, cadcache keys and cadgen closure hashes differ
  per pinned table and are unchanged when nothing is pinned.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.make import test_make_round as make_round_tests
from workshop.wish import fit_tables

REPO = Path(__file__).resolve().parents[2]
CAD_SCRIPTS = REPO / "src/workshop/make/skills/cad/scripts"
CADGEN_SRC = CAD_SCRIPTS / "packages/cadgen/src"
RESYNC_LOCK = "6cc66a4a370ad265c6e0ccda1ee44d99da6487adfac52a69f60b610adb43d62f"


def _cadfits(table: str | None, code: str) -> subprocess.CompletedProcess:
    env = {key: value for key, value in os.environ.items() if key != fit_tables.FIT_TABLE_ENV}
    if table is not None:
        env[fit_tables.FIT_TABLE_ENV] = table
    env["PYTHONPATH"] = os.pathsep.join([str(CAD_SCRIPTS), str(CADGEN_SRC), str(REPO / "src")])
    return subprocess.run([sys.executable, "-B", "-c", "import json, cadfits\n" + code],
                          env=env, capture_output=True, text=True, timeout=60)


class CadfitsTableTest(unittest.TestCase):
    def _values(self, table):
        done = _cadfits(table, "print(json.dumps([cadfits.FIT_TABLE, cadfits.DEFAULT_FIT,"
                               " cadfits.slot_for(1.0, 'slip'), sorted(cadfits.FIT_TABLES)]))")
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    def test_unset_builds_with_the_current_table(self):
        table, default, slot, names = self._values(None)
        self.assertEqual((table["slip"], table["snug"], default), (0.10, 0.05, "moving"))
        self.assertAlmostEqual(slot, 1.2)
        self.assertEqual(sorted(fit_tables.NAMES), names)
        self.assertEqual(self._values(fit_tables.CURRENT)[:3], [table, default, slot])

    def test_legacy_is_the_table_proofs_were_approved_with(self):
        table, default, slot, _names = self._values(fit_tables.LEGACY)
        self.assertEqual((table["press"], table["snug"], table["slip"], table["free"], default),
                         (-0.05, 0.10, 0.20, 0.40, "slip"))
        self.assertAlmostEqual(slot, 1.4)
        # A bought part's seat is cut as the old default cut it.
        self.assertEqual(table["clear"], 0.20)

    def test_a_default_argument_reads_the_pinned_table(self):
        done = _cadfits(fit_tables.LEGACY, "print(cadfits.mating_clearance())")
        self.assertEqual(done.stdout.strip(), "0.2", done.stderr)

    def test_an_unknown_table_refuses_to_import(self):
        done = _cadfits("fits-1999", "print('built')")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("names no fit table", done.stderr)
        self.assertNotIn("built", done.stdout)

    def test_the_self_check_passes_under_every_table(self):
        for table in (None, *fit_tables.NAMES):
            done = _cadfits(table, "raise SystemExit(cadfits._self_check())")
            self.assertEqual(done.returncode, 0, (table, done.stdout[-800:]))


class ApprovalTableTest(unittest.TestCase):
    def test_a_recorded_table_wins(self):
        for name in fit_tables.NAMES:
            self.assertEqual(fit_tables.approval_fit_table({"fit_table": name, "skills_lock_sha256": "0" * 64}),
                             name)

    def test_an_older_approval_is_placed_by_its_lock(self):
        self.assertEqual(fit_tables.approval_fit_table({"skills_lock_sha256": RESYNC_LOCK}), fit_tables.CURRENT)
        # The published Amsterdam tray's approval (2026-11-11).
        self.assertEqual(fit_tables.approval_fit_table(
            {"skills_lock_sha256": "d7cf817b7810" + "0" * 52}), fit_tables.LEGACY)
        self.assertEqual(fit_tables.approval_fit_table({}), fit_tables.LEGACY)

    def test_an_unknown_recorded_table_refuses(self):
        for bad in ("fits-1999", None, 3, ""):
            with self.assertRaises(ValueError):
                fit_tables.approval_fit_table({"fit_table": bad})

    def test_pin_replaces_whatever_was_set(self):
        environment = {fit_tables.FIT_TABLE_ENV: fit_tables.CURRENT}
        self.assertEqual(fit_tables.pin(environment, {}), fit_tables.LEGACY)
        self.assertEqual(environment[fit_tables.FIT_TABLE_ENV], fit_tables.LEGACY)

    def test_a_seal_records_the_table_it_built_with(self):
        self.assertEqual(fit_tables.sealing_fit_table({}), fit_tables.CURRENT)
        self.assertEqual(fit_tables.sealing_fit_table({fit_tables.FIT_TABLE_ENV: fit_tables.LEGACY}),
                         fit_tables.LEGACY)
        with self.assertRaises(ValueError):
            fit_tables.sealing_fit_table({fit_tables.FIT_TABLE_ENV: "fits-1999"})


class MakeRoundPinTest(unittest.TestCase):
    def setUp(self):
        self.module = make_round_tests.load_module()
        self.addCleanup(os.environ.pop, fit_tables.FIT_TABLE_ENV, None)
        os.environ.pop(fit_tables.FIT_TABLE_ENV, None)

    def test_a_seeded_run_pins_its_approval_table(self):
        self.module.seed_approval = lambda project: {"components": {}}
        self.assertEqual(self.module.pin_seed_fit_table(Path("cad")), fit_tables.LEGACY)
        self.assertEqual(os.environ[fit_tables.FIT_TABLE_ENV], fit_tables.LEGACY)
        self.module.seed_approval = lambda project: {"components": {}, "fit_table": fit_tables.CURRENT}
        self.assertEqual(self.module.pin_seed_fit_table(Path("cad")), fit_tables.CURRENT)

    def test_outside_a_seeded_run_nothing_is_pinned(self):
        self.module.seed_approval = lambda project: None
        self.assertIsNone(self.module.pin_seed_fit_table(Path("cad")))
        self.assertNotIn(fit_tables.FIT_TABLE_ENV, os.environ)

    def test_an_unreadable_approval_is_left_to_the_round(self):
        def unreadable(project):
            raise ValueError("seed/APPROVAL.json is not the approval MAKE-OPTIONS.json froze")
        self.module.seed_approval = unreadable
        self.assertIsNone(self.module.pin_seed_fit_table(Path("cad")))
        self.assertNotIn(fit_tables.FIT_TABLE_ENV, os.environ)

    def test_main_pins_for_its_work_and_gives_the_caller_its_environment_back(self):
        seen = []
        self.module.seed_approval = lambda project: {"components": {}}
        self.module.self_check = lambda: seen.append(os.environ.get(fit_tables.FIT_TABLE_ENV)) or 0
        os.environ[fit_tables.FIT_TABLE_ENV] = fit_tables.CURRENT
        # --self-check returns before the project is read: nothing pinned.
        self.assertEqual(self.module.main(["--self-check"]), 0)
        self.assertEqual(seen, [fit_tables.CURRENT])
        with tempfile.TemporaryDirectory() as tmp:
            self.module.identities_only = lambda args: seen.append(os.environ.get(fit_tables.FIT_TABLE_ENV)) or 0
            self.assertEqual(self.module.main([tmp, "--identities-only", "--contract", "C.md"]), 0)
        self.assertEqual(seen[-1], fit_tables.LEGACY)
        self.assertEqual(os.environ[fit_tables.FIT_TABLE_ENV], fit_tables.CURRENT)


class HostBatchEnvironmentTest(unittest.TestCase):
    def test_every_batch_step_sees_the_approval_table(self):
        from workshop.errors import StateConflict
        from workshop.workflow import seeded_batch_host as host

        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp)
            (run_root / "seed").mkdir()
            approval = run_root / "seed/APPROVAL.json"
            approval.write_text(json.dumps({"skills_lock_sha256": "d7" * 32}))
            self.assertEqual(host.environment(run_root)[fit_tables.FIT_TABLE_ENV], fit_tables.LEGACY)
            approval.write_text(json.dumps({"fit_table": fit_tables.CURRENT}))
            self.assertEqual(host.environment(run_root)[fit_tables.FIT_TABLE_ENV], fit_tables.CURRENT)
            for bad in (json.dumps({"fit_table": "fits-1999"}), "{"):
                approval.write_text(bad)
                with self.assertRaises(StateConflict):
                    host.environment(run_root)
            approval.unlink()
            with self.assertRaises(StateConflict):
                host.environment(run_root)


class BuildCacheKeyTest(unittest.TestCase):
    def setUp(self):
        sys.path[:0] = [str(CAD_SCRIPTS), str(CADGEN_SRC)]
        self.addCleanup(lambda: [sys.path.remove(p) for p in (str(CAD_SCRIPTS), str(CADGEN_SRC))])
        self.addCleanup(os.environ.pop, fit_tables.FIT_TABLE_ENV, None)
        os.environ.pop(fit_tables.FIT_TABLE_ENV, None)

    def _per_table(self, compute):
        unset = compute()
        values = {}
        for name in fit_tables.NAMES:
            with mock.patch.dict(os.environ, {fit_tables.FIT_TABLE_ENV: name}):
                values[name] = compute()
        return unset, values

    def test_the_cadgen_closure_hash_is_per_table(self):
        from cadgen._internal import source_hash

        pairs = [("part_body.step.py", "a" * 64), ("params.py", "b" * 64)]
        unset, values = self._per_table(lambda: source_hash._closure_hash_for_pairs(pairs))
        import hashlib
        expected = hashlib.sha256()
        for rel, digest in sorted(pairs):
            expected.update(rel.encode() + b"\0" + digest.encode() + b"\0")
        self.assertEqual(unset, expected.hexdigest(), "an unpinned closure keeps its recorded hash")
        self.assertEqual(len({unset, *values.values()}), 1 + len(fit_tables.NAMES))

    def test_the_cadcache_key_is_per_table(self):
        import cadcache

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "bodies.py").write_text("def build(item):\n    return None\n")
            unset, values = self._per_table(lambda: cadcache.cache_key(
                "bodies:build", "head", root=root, inputs=lambda item: "1"))
        self.assertEqual(len({unset, *values.values()}), 1 + len(fit_tables.NAMES))

    def test_the_warm_daemon_is_per_table(self):
        from cadgen_daemon import client

        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CADGEN_DAEMON_SOCKET", None)
            unset, values = self._per_table(client.socket_path)
        self.assertEqual(len({unset, *values.values()}), 1 + len(fit_tables.NAMES))


if __name__ == "__main__":
    unittest.main()
