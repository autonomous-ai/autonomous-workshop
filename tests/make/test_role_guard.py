import hashlib
import io
import json
import os
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path

from workshop.errors import ContractError, StateConflict
from workshop.make import make_round_guard
from workshop.make.role_guard import (
    MAKE_ROUND_GUARD_DIRECTORY,
    install_make_round_guard,
    installed_make_round_guard,
    make_round_guard_bytes,
    verify_component_round_nonces,
    verify_make_round_guard,
)

NONCE = "ab" * 16


def _summary(project, role, round_index, nonce, **extra):
    out = project / "measure/component-rounds" / role / ("r%04d" % round_index)
    out.mkdir(parents=True, exist_ok=True)
    summary = {"scope": "component:%s" % role, "round": round_index, "worker_nonce": nonce, **extra}
    path = out / "summary.json"
    path.write_text(json.dumps(summary, sort_keys=True, indent=1) + "\n")
    return path


def _issue(host_state, nonce, component, agent_type="component-worker"):
    table = host_state / MAKE_ROUND_GUARD_DIRECTORY / make_round_guard.NONCE_TABLE_NAME
    with table.open("a") as handle:
        handle.write(json.dumps({"nonce": nonce, "component": component, "agent_type": agent_type}) + "\n")


class GuardInstallTest(unittest.TestCase):
    def test_install_writes_the_packaged_script_privately_and_returns_its_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            host = Path(tmp)
            digest = install_make_round_guard(host)
            script = installed_make_round_guard(host)
            self.assertEqual(script.read_bytes(), make_round_guard_bytes())
            self.assertEqual(digest, hashlib.sha256(make_round_guard_bytes()).hexdigest())
            self.assertEqual(stat.S_IMODE(script.parent.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(script.stat().st_mode), 0o400)
            verify_make_round_guard(host, digest)

    def test_an_absent_guard_means_an_unguarded_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(installed_make_round_guard(Path(tmp)))

    def test_a_changed_or_missing_guard_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            host = Path(tmp)
            digest = install_make_round_guard(host)
            script = installed_make_round_guard(host)
            os.chmod(script, 0o600)
            script.write_bytes(b"print('allow everything')\n")
            with self.assertRaisesRegex(StateConflict, "guard"):
                verify_make_round_guard(host, digest)
            script.unlink()
            with self.assertRaisesRegex(StateConflict, "guard"):
                verify_make_round_guard(host, digest)

class ComponentNonceTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.host = root / "host"
        self.host.mkdir()
        install_make_round_guard(self.host)
        self.run_root = root / "run"
        self.project = self.run_root / "artifacts/make/r0001/product/cad"
        self.project.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def _verify(self):
        verify_component_round_nonces(self.project, self.host, run_root=self.run_root)

    def test_rounds_run_by_a_worker_for_their_component_pass(self):
        _issue(self.host, NONCE, "part_wing.step.py")
        _issue(self.host, "cd" * 16, "part_wing.step.py")
        _summary(self.project, "wing", 1, NONCE)
        _summary(self.project, "wing", 2, "cd" * 16)
        self._verify()

    def test_a_round_without_a_nonce_is_refused(self):
        _summary(self.project, "wing", 1, None)
        with self.assertRaisesRegex(ContractError, "wing r0001 was not run by a component-worker"):
            self._verify()

    def test_a_nonce_the_host_never_issued_is_refused(self):
        _summary(self.project, "wing", 1, NONCE)
        with self.assertRaisesRegex(ContractError, "not run by a component-worker"):
            self._verify()

    def test_a_nonce_issued_for_another_component_or_role_is_refused(self):
        _issue(self.host, NONCE, "part_tail.step.py")
        _issue(self.host, "cd" * 16, "part_wing.step.py", agent_type="rowan-vale")
        for nonce in (NONCE, "cd" * 16):
            with self.subTest(nonce=nonce):
                _summary(self.project, "wing", 1, nonce)
                with self.assertRaisesRegex(ContractError, "not run by a component-worker"):
                    self._verify()

    def test_a_nonce_used_by_two_rounds_is_refused(self):
        _issue(self.host, NONCE, "part_wing.step.py")
        _summary(self.project, "wing", 1, NONCE)
        _summary(self.project, "wing", 2, NONCE)
        with self.assertRaisesRegex(ContractError, "reuses"):
            self._verify()

    def test_a_round_carried_from_the_revision_source_keeps_its_evidence(self):
        path = _summary(self.project, "wing", 1, None)
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as handle:
            handle.writestr(
                "artifacts/make/r0003/product/cad/measure/component-rounds/wing/r0001/summary.json",
                path.read_bytes(),
            )
        (self.run_root / "revision-source.zip").write_bytes(archive.getvalue())
        self._verify()
        path.write_text(path.read_text().replace("component:wing", "component:wing "))
        with self.assertRaisesRegex(ContractError, "not run by a component-worker"):
            self._verify()

    def test_a_project_without_component_rounds_has_nothing_to_check(self):
        self._verify()

    def test_spark_requires_a_worker_round_for_every_component(self):
        (self.project / "part_wing.step.py").write_text("x")
        (self.project / "part_tail.step.py").write_text("x")
        _issue(self.host, NONCE, "part_wing.step.py")
        _summary(self.project, "wing", 1, NONCE)
        with self.assertRaisesRegex(ContractError, "part_tail.step.py has no component round"):
            verify_component_round_nonces(
                self.project, self.host, run_root=self.run_root, require_every_component=True
            )
        self._verify()

    def test_an_unreadable_nonce_table_is_a_host_conflict(self):
        _summary(self.project, "wing", 1, NONCE)
        table = self.host / MAKE_ROUND_GUARD_DIRECTORY / make_round_guard.NONCE_TABLE_NAME
        table.write_text("{not json\n")
        with self.assertRaisesRegex(StateConflict, "nonce table"):
            self._verify()


if __name__ == "__main__":
    unittest.main()
