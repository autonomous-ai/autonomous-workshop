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



REVIEWER = "a1f355b61d99918ed"
OTHER = "a7740f58e37677176"


class ComponentReviewerBindingTest(unittest.TestCase):
    """Issue #77: a recorded Component Review is admitted only from the
    Component's one proven Component Reviewer."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.host = root / "host"
        self.host.mkdir()
        install_make_round_guard(self.host)
        self.run_root = root / "run"
        self.project = self.run_root / "artifacts/make/r0001/product/cad"
        self.project.mkdir(parents=True)
        self.nonces = 0
        self.addCleanup(self._tmp.cleanup)

    def _log(self, name, record):
        with (self.host / MAKE_ROUND_GUARD_DIRECTORY / name).open("a") as handle:
            handle.write(json.dumps(record) + "\n")

    def _start(self, agent_id=REVIEWER, agent_type="component-reviewer"):
        self._log(make_round_guard.SUBAGENT_LOG_NAME, {"agent_id": agent_id, "agent_type": agent_type})

    def _reviewed_round(self, round_index, reviewer=REVIEWER, *, carried=False):
        """A worker's round with a packet of four images and a recorded review."""
        self.nonces += 1
        nonce = "%032x" % self.nonces
        _issue(self.host, nonce, "part_wing.step.py")
        out = self.project / "measure/component-rounds/wing" / ("r%04d" % round_index)
        visual = out / "visual"
        visual.mkdir(parents=True)
        images = {}
        for name in ("front", "top", "iso"):
            path = visual / (name + ".png")
            path.write_bytes(b"%s %d" % (name.encode(), round_index))
            images[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        compare = visual / "compare-00.png"
        compare.write_bytes(b"compare %d" % round_index)
        packet = {"images": images, "comparisons": {
            str(compare): {"label": "geometry:wing", "sha256": hashlib.sha256(compare.read_bytes()).hexdigest()}}}
        packet_path = out / "visual-packet.json"
        packet_path.write_text(json.dumps(packet))
        review = {"reviewer": reviewer, "agrees": True, "reason": "matches", "round": round_index}
        if carried:
            review["carried_from"] = round_index - 1
        _summary(self.project, "wing", round_index, nonce, review=review, visual={
            "status": "reviewed", "packet": str(packet_path),
            "packet_sha256": hashlib.sha256(packet_path.read_bytes()).hexdigest()})
        return [*images, str(compare)]

    def _read(self, paths, agent_id=REVIEWER, agent_type="component-reviewer", content=None):
        for path in paths:
            digest = hashlib.sha256(content if content is not None else Path(path).read_bytes()).hexdigest()
            self._log(make_round_guard.READ_LOG_NAME, {
                "agent_id": agent_id, "agent_type": agent_type, "path": path, "sha256": digest})

    def _verify(self, bind=True):
        verify_component_round_nonces(
            self.project, self.host, run_root=self.run_root, bind_reviewers=bind)

    def test_a_review_by_the_started_reviewer_that_read_every_image_passes(self):
        self._start()
        self._read(self._reviewed_round(1))
        self._read(self._reviewed_round(2))
        self._verify()

    def test_a_reviewer_the_runtime_never_started_as_a_component_reviewer_is_refused(self):
        for agent_type in (None, "general-purpose"):
            with self.subTest(agent_type=agent_type):
                self.setUp()
                if agent_type is not None:
                    self._start(agent_type=agent_type)
                self._read(self._reviewed_round(1))
                with self.assertRaisesRegex(ContractError, "not a component-reviewer this run started"):
                    self._verify()

    def test_a_reviewer_that_missed_an_image_or_read_other_bytes_is_refused(self):
        for fault in ("missed", "other bytes", "other agent", "other type"):
            with self.subTest(fault=fault):
                self.setUp()
                self._start()
                paths = self._reviewed_round(1)
                if fault == "missed":
                    self._read(paths[:3])
                elif fault == "other bytes":
                    self._read(paths[:3])
                    self._read(paths[3:], content=b"an earlier compare image")
                elif fault == "other agent":
                    self._start(OTHER)
                    self._read(paths, agent_id=OTHER)
                else:
                    self._read(paths, agent_type="component-worker")
                with self.assertRaisesRegex(ContractError, "did not read"):
                    self._verify()

    def test_a_review_naming_a_second_reviewer_for_the_component_is_refused(self):
        self._start()
        self._start(OTHER)
        self._read(self._reviewed_round(1))
        self._read(self._reviewed_round(2, OTHER), agent_id=OTHER)
        with self.assertRaisesRegex(ContractError, "comes from its one reviewer"):
            self._verify()

    def test_a_reviewer_that_is_not_an_agent_id_is_refused(self):
        self._reviewed_round(1, "component-reviewer")
        with self.assertRaisesRegex(ContractError, "native agent id"):
            self._verify()

    def test_a_changed_packet_is_refused(self):
        self._start()
        paths = self._reviewed_round(1)
        self._read(paths)
        (self.project / "measure/component-rounds/wing/r0001/visual-packet.json").write_text("{}")
        with self.assertRaisesRegex(ContractError, "packet is missing or changed"):
            self._verify()

    def test_a_carried_review_is_judged_on_its_original_round(self):
        self._start()
        self._read(self._reviewed_round(1))
        self._reviewed_round(2, carried=True)
        self._verify()

    def test_a_run_that_does_not_bind_reviewers_keeps_its_frozen_rules(self):
        self._reviewed_round(1, "fresh-reviewer")
        self._verify(bind=False)

    def test_an_unreadable_evidence_log_is_a_host_conflict(self):
        self._read(self._reviewed_round(1))
        (self.host / MAKE_ROUND_GUARD_DIRECTORY / make_round_guard.SUBAGENT_LOG_NAME).write_text("{not json\n")
        with self.assertRaisesRegex(StateConflict, "subagent log"):
            self._verify()


if __name__ == "__main__":
    unittest.main()
