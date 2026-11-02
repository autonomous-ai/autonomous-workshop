"""ADR 0096 Stage 5: seal_proof records the owner's approval of a Proof.

Contract: `seal` writes APPROVAL.json with make_round's identities, each
approved STEP copied into approved/ with its Parts' volume and bounding box,
the hashes it binds, and a manifest of the seed tree; `verify` passes on the
sealed tree and fails on a missing, extra or changed file or another
contract. Seal refuses a Proof without the installed print-details library,
without a passing Shared Helper freeze, with a helper changed since the
freeze or imported outside it, with a Critic that did not agree (unless the
owner approved its open lines), and a STEP make_round did not build."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import build123d as bd

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".claude/skills/design-a-toy/scripts/seal_proof.py"
LIBRARY = ROOT / "src/workshop/make/skills/print-details/scripts/print_details.py"


def load():
    spec = importlib.util.spec_from_file_location("seal_proof_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SealProofTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.module = load()
        self.design = self.root / "design"
        self.proof = self.design / "proof"
        (self.proof / "features").mkdir(parents=True)
        (self.proof / "measure").mkdir()
        (self.proof / "features/print_details.py").write_bytes(LIBRARY.read_bytes())
        (self.proof / "params.py").write_text("PEG_D = 4.0  # wiki: joints-and-fits\nassert PEG_D >= 3\n")
        (self.proof / "part_body.step.py").write_text("from params import PEG_D\n")
        box = bd.Box(20, 10, 5)
        box.label = "body"
        bd.export_step(bd.Compound(children=[box]), str(self.proof / "part_body.step"))
        (self.proof / "part_body.step.log").write_text("build log")
        self.helpers = {"params.py": sha(self.proof / "params.py"),
                        "features/print_details.py": sha(self.proof / "features/print_details.py")}
        (self.proof / "measure/shared-helpers-freeze.json").write_text(json.dumps({"helpers": self.helpers}))
        (self.proof / "CRITIC.json").write_text(json.dumps({"schema_version": 1, "verdict": "agree"}))
        self.contract = self.design / "CONTRACT.md"
        self.contract.write_text("# Toy\n")
        self.checklist = self.design / "CONCEPT-CHECKLIST.md"
        self.checklist.write_text("| id | trait |\n| T1 | round |\n")
        self.imported = {"params.py": self.helpers["params.py"]}

    def _record(self, proof, contract):
        return {"schema_version": 1, "contract_sha256": sha(contract), "assembly_identity": "asm",
                "components": {"body": {"identity": "B", "step_sha256": sha(proof / "part_body.step"),
                                        "imported_helpers": dict(self.imported),
                                        "contract_rows": "rows", "carry_key": "key"}}}

    def _seal(self, *extra):
        argv = ["seal", str(self.proof), "--contract", str(self.contract), "--checklist", str(self.checklist),
                "--nozzle", "0.4", "--approved-by", "owner", "--date", "2026-11-02", "--cost", "3.5", *extra]
        with mock.patch.object(self.module, "identities", side_effect=self._record), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            code = self.module.main(argv)
        self.stderr = err.getvalue()
        return code

    def _verify(self, *extra):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            code = self.module.main(["verify", str(self.proof), *extra])
        self.stderr = err.getvalue()
        return code

    def test_seal_writes_the_approval_and_verify_passes(self):
        self.assertEqual(self._seal(), 0, self.stderr)
        approval = json.loads((self.proof / "APPROVAL.json").read_text())
        body = approval["components"]["body"]
        self.assertEqual(body["carry_key"], "key")
        self.assertEqual(body["approved_step"], "approved/part_body.step")
        self.assertEqual((self.proof / "approved/part_body.step").read_bytes(),
                         (self.proof / "part_body.step").read_bytes())
        self.assertAlmostEqual(body["parts"]["body"]["volume_mm3"], 1000.0, places=1)
        box = body["parts"]["body"]["bbox_mm"]
        self.assertEqual([round(box[3] - box[0], 3), round(box[4] - box[1], 3), round(box[5] - box[2], 3)],
                         [20.0, 10.0, 5.0])
        self.assertEqual(approval["contract_sha256"], sha(self.contract))
        self.assertEqual(approval["checklist_sha256"], sha(self.checklist))
        self.assertEqual((self.proof / "CONCEPT-CHECKLIST.md").read_bytes(), self.checklist.read_bytes())
        self.assertEqual(approval["print_details_sha256"], sha(LIBRARY))
        self.assertEqual(approval["skills_lock_sha256"], sha(ROOT / "src/workshop/make/skills/LOCK.json"))
        self.assertEqual((approval["nozzle_mm"], approval["approved_by"], approval["date"],
                          approval["design_cost_units"]), (0.4, "owner", "2026-11-02", 3.5))
        self.assertEqual(sorted(approval["manifest"]), [
            "CONCEPT-CHECKLIST.md", "CRITIC.json", "approved/part_body.step", "features/print_details.py",
            "params.py", "part_body.step.py"])
        self.assertEqual(approval["critic"]["verdict"], "agree")
        self.assertEqual(self._verify("--contract", str(self.contract)), 0, self.stderr)
        # Evidence under measure/ is not part of the seed.
        (self.proof / "measure/notes.txt").write_text("x")
        self.assertEqual(self._verify(), 0, self.stderr)

    def test_verify_refuses_a_manifest_mismatch(self):
        self.assertEqual(self._seal(), 0, self.stderr)
        (self.proof / "params.py").write_text("PEG_D = 5.0\n")
        (self.proof / "extra.py").write_text("")
        (self.proof / "CRITIC.json").unlink()
        self.assertEqual(self._verify(), 1)
        for line in ("changed: params.py", "extra: extra.py", "missing: CRITIC.json"):
            with self.subTest(line=line):
                self.assertIn(line, self.stderr)
        other = self.design / "OTHER.md"
        other.write_text("# Other\n")
        self.assertEqual(self._verify("--contract", str(other)), 1)
        self.assertIn("not the sealed contract_sha256", self.stderr)

    def test_verify_refuses_a_tampered_manifest_and_a_symlink(self):
        self.assertEqual(self._seal(), 0, self.stderr)
        approval = json.loads((self.proof / "APPROVAL.json").read_text())
        approval["manifest"]["params.py"] = "0" * 64
        (self.proof / "APPROVAL.json").write_text(json.dumps(approval))
        self.assertEqual(self._verify(), 1)
        self.assertIn("does not hash to manifest_sha256", self.stderr)
        (self.proof / "link.py").symlink_to(self.proof / "params.py")
        self.assertEqual(self._verify(), 1)
        self.assertIn("is a symlink", self.stderr)

    def test_seal_refuses_a_proof_not_written_as_make_writes(self):
        (self.proof / "features/print_details.py").write_text("edited")
        self.assertEqual(self._seal(), 1)
        self.assertIn("differs from the library", self.stderr)
        (self.proof / "features/print_details.py").unlink()
        self.assertEqual(self._seal(), 1)
        self.assertIn("is not installed", self.stderr)
        (self.proof / "features/print_details.py").write_bytes(LIBRARY.read_bytes())
        (self.proof / "params.py").write_text("PEG_D = 4.5\n")
        self.assertEqual(self._seal(), 1)
        self.assertIn("Shared Helper params.py changed since it froze", self.stderr)
        (self.proof / "measure/shared-helpers-freeze.json").unlink()
        self.assertEqual(self._seal(), 1)
        self.assertIn("no passing Shared Helper freeze", self.stderr)
        self.assertFalse((self.proof / "APPROVAL.json").exists())

    def test_seal_refuses_a_helper_outside_the_freeze(self):
        (self.proof / "joints.py").write_text("FIT = 0.2\n")
        self.imported["joints.py"] = sha(self.proof / "joints.py")
        self.assertEqual(self._seal(), 1)
        self.assertIn("imports joints.py, which no passing Shared Helper freeze covers", self.stderr)

    def test_seal_refuses_a_critic_that_did_not_agree_unless_the_owner_approved(self):
        (self.proof / "CRITIC.json").write_text(json.dumps({"verdict": "differences"}))
        self.assertEqual(self._seal(), 1)
        self.assertIn("--open-lines-approved", self.stderr)
        self.assertEqual(self._seal("--open-lines-approved"), 0, self.stderr)
        approval = json.loads((self.proof / "APPROVAL.json").read_text())
        self.assertEqual(approval["critic"], {"sha256": sha(self.proof / "CRITIC.json"),
                                              "verdict": "differences", "open_lines_approved": True})
        (self.proof / "CRITIC.json").unlink()
        self.assertEqual(self._seal(), 1)
        self.assertIn("no readable CRITIC.json", self.stderr)

    def test_seal_refuses_a_step_make_round_did_not_build(self):
        record = self._record
        def stale(proof, contract):
            document = record(proof, contract)
            document["components"]["body"]["step_sha256"] = "0" * 64
            return document
        self._record = stale
        self.assertEqual(self._seal(), 1)
        self.assertIn("part_body.step is not the STEP make_round built", self.stderr)

    def test_seal_refuses_another_checklist_already_in_the_proof(self):
        (self.proof / "CONCEPT-CHECKLIST.md").write_text("other")
        self.assertEqual(self._seal(), 1)
        self.assertIn("already holds another checklist", self.stderr)

    def test_identities_come_from_make_round(self):
        done = mock.Mock(returncode=2, stdout="", stderr="make_round: part_body.step.py does not build")
        with mock.patch.object(self.module.subprocess, "run", return_value=done) as run:
            with self.assertRaises(self.module.Refusal) as caught:
                self.module.identities(self.proof, self.contract)
        command = run.call_args.args[0]
        self.assertEqual(command[1:], [str(self.module.MAKE_ROUND), str(self.proof), "--identities-only",
                                       "--contract", str(self.contract)])
        self.assertIn("does not build", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
