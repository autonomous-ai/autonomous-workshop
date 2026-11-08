"""ADR 0096 Stage 5: seal_proof records the owner's approval of a Proof.

Contract: `seal` writes APPROVAL.json with make_round's identities, each
approved STEP copied into approved/ with its Parts' volume and bounding box,
the hashes it binds, and a manifest of the seed tree; `verify` passes on the
sealed tree and fails on a missing, extra or changed file or another
contract. Seal refuses a Proof without the installed print-details library,
without a passing Shared Helper freeze, with a helper changed since the
freeze or imported outside it, with a Critic that did not agree (unless the
owner approved its open lines), a STEP make_round did not build, and (beaver
pilot B2-B5) what final verification would reject: no passing print-gate
summary of every Component at the sealed nozzle over the current sources
with the Display-Pose and bed-datum checks, not exactly one `*_spec.md`, a
spec its format or numbers check fails, or a missing `measure/` audit."""

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


SEED_PRODUCT = {
    "schema_version": 1, "kind": "workshop-seed-product", "title": "Toy Box", "summary": "A box.",
    "concept": {"title": "Toy Box", "summary": "A box.", "interaction": "Lift the lid.",
                "envelope_mm": [20, 10, 5], "mechanisms": [], "components": []},
    "research": {"notes": "none"},
}


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
        SealProofTest._final_inputs(self)
        SealProofTest._check_inputs(self)
        self.design_contract = {}
        self.batch_calls = []
        self.batch_exit = {}

    def _check_inputs(self):
        """ADR 0098: what every seed carries for its checks."""
        (self.proof / "snap").mkdir(exist_ok=True)
        (self.proof / "snap/iso.png").write_bytes(b"iso")
        (self.proof / "snap/signature.png").write_bytes(b"signature")
        (self.proof / "SEED-PRODUCT.json").write_text(json.dumps(SEED_PRODUCT))

    def _batch_runner(self, argv, cwd, timeout):
        from workshop.make.seeded_batch import RunResult
        self.batch_calls.append(list(argv))
        for fragment, result in getattr(self, "batch_exit", {}).items():
            if any(fragment in item for item in argv):
                return result
        return RunResult(0, "ok")

    def _final_inputs(self, **changes):
        """What final verification needs (B2-B5): a passing print-gate
        summary over the current sources, one spec and the three audits."""
        (self.proof / "toy_spec.md").write_text("# spec\n")
        for name in self.module.AUDITS:
            (self.proof / name).write_text("print('ok')\n")
        summary = {"ok": True, "parts": ["body"], "nozzle": 0.4, "checks": list(self.module.REQUIRED_CHECKS),
                   "sources": self.module.geometry_sources(self.proof),
                   "print": {"body": {"verdict": "PASS"}}, "build": {"body": {"verdict": "PASS"}}}
        summary.update(changes)
        (self.proof / "measure/print-gates").mkdir(parents=True, exist_ok=True)
        (self.proof / self.module.PRINT_GATES).write_text(json.dumps(summary))

    def _record(self, proof, contract):
        return {"schema_version": 1, "contract_sha256": sha(contract), "assembly_identity": "asm",
                "components": {"body": {"identity": "B", "step_sha256": sha(proof / "part_body.step"),
                                        "imported_helpers": dict(self.imported),
                                        "contract_rows": "rows", "carry_key": "key"}}}

    def _seal(self, *extra):
        argv = ["seal", str(self.proof), "--contract", str(self.contract), "--checklist", str(self.checklist),
                "--nozzle", "0.4", "--approved-by", "owner", "--date", "2026-11-02", "--cost", "3.5", *extra]
        with mock.patch.object(self.module, "identities", side_effect=self._record), \
                mock.patch.object(self.module, "read_contract",
                                  side_effect=lambda path: getattr(self, "design_contract", {})), \
                mock.patch.object(self.module, "batch_runner", return_value=lambda *a: SealProofTest._batch_runner(self, *a)), \
                mock.patch.object(self.module, "run_spec_tool",
                                  side_effect=lambda proof, tool: SealProofTest._spec_tool(self, proof, tool)), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            code = self.module.main(argv)
        self.stderr = err.getvalue()
        return code

    def _spec_tool(self, proof, tool):
        return getattr(self, "spec_failure", {}).get(tool, (0, "ok"))

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
            "CONCEPT-CHECKLIST.md", "CRITIC.json", "SEED-PRODUCT.json", "approved/part_body.step",
            "features/print_details.py", "measure/check_fit.py", "measure/check_landmarks.py",
            "measure/check_spec.py", "params.py", "part_body.step.py", "snap/iso.png", "snap/signature.png",
            "toy_spec.md"])
        self.assertEqual(approval["schema_version"], 2)
        self.assertEqual(approval["check_inputs"], {name: approval["manifest"][name] for name in
                                                    ("SEED-PRODUCT.json", "snap/iso.png", "snap/signature.png")})
        self.assertEqual(approval["batch"]["ok"], True)
        self.assertEqual(approval["batch"]["record_sha256"], sha(self.proof / "measure/seeded-batch.json"))
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

    def test_seal_refuses_what_final_verification_would_reject(self):
        # Beaver pilot B2-B5: a Proof whose body self-intersects in its
        # Display Pose, whose eye sits below the bed, or that lacks the spec
        # and audits final verification reads, is never sealed.
        def unlink(name):
            return lambda: (self.proof / name).unlink()

        cases = {
            "no print-gate summary": unlink(str(self.module.PRINT_GATES)),
            "did not check datum, posed": lambda: self._final_inputs(
                checks=["build", "thickness", "overhang", "mesh"]),
            "covers nothing, not every Component": lambda: self._final_inputs(parts=[]),
            "nozzle 0.6, not 0.4": lambda: self._final_inputs(nozzle=0.6),
            "a source changed": lambda: self._final_inputs(sources={}),
            "failed for body": lambda: self._final_inputs(ok=False, print={"body": {"verdict": "FAIL"}}),
            "exactly one \\*_spec.md": unlink("toy_spec.md"),
            "measure/check_landmarks.py": unlink("measure/check_landmarks.py"),
        }
        for fragment, change in cases.items():
            with self.subTest(fragment):
                self.setUp()
                change()
                self.assertEqual(self._seal(), 1)
                self.assertRegex(self.stderr, fragment)
                self.assertFalse((self.proof / "APPROVAL.json").exists())
        self.setUp()
        (self.proof / "other_spec.md").write_text("# two\n")
        self.assertEqual(self._seal(), 1)
        self.assertIn("found 2", self.stderr)
        self.setUp()
        self.spec_failure = {"check_spec_numbers": (1, "S3 has no number")}
        self.assertEqual(self._seal(), 1)
        self.assertIn("check_spec_numbers fails on toy_spec.md: S3 has no number", self.stderr)

    def test_identities_come_from_make_round(self):
        done = mock.Mock(returncode=2, stdout="", stderr="make_round: part_body.step.py does not build")
        with mock.patch.object(self.module.subprocess, "run", return_value=done) as run:
            with self.assertRaises(self.module.Refusal) as caught:
                self.module.identities(self.proof, self.contract)
        command = run.call_args.args[0]
        self.assertEqual(command[1:], [str(self.module.MAKE_ROUND), str(self.proof), "--identities-only",
                                       "--contract", str(self.contract)])
        self.assertIn("does not build", str(caught.exception))


class SealCheckInputsTest(unittest.TestCase):
    """ADR 0098: the seal carries every check input and runs the batch."""

    _record = SealProofTest._record
    _seal = SealProofTest._seal
    _spec_tool = SealProofTest._spec_tool
    _final_inputs = SealProofTest._final_inputs

    def setUp(self):
        SealProofTest.setUp(self)

    def _inputs(self):
        with mock.patch.object(self.module, "read_contract", return_value=self.design_contract), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            code = self.module.main(["inputs", str(self.proof), "--contract", str(self.contract)])
        self.stdout = out.getvalue()
        return code

    def _motion_review(self, **changes):
        from workshop.make.seeded_batch import concept_sha256

        evidence = hashlib.sha256((self.proof / "snap/MOTION-EVIDENCE.json").read_bytes()).hexdigest()
        review = {"schema_version": 1, "evidence_sha256": evidence,
                  "concept_sha256": concept_sha256(SEED_PRODUCT["concept"]), "reviewer": "proof-critic-1",
                  "review_rounds": 1, "blind_motion_read": "The lid swings open.", "motion_matches_wish": True,
                  "simulation_not_physical_test": True, **changes}
        (self.proof / "snap/MOTION-REVIEW.json").write_text(json.dumps(review))

    def test_seal_refuses_a_missing_check_input_and_names_who_writes_it(self):
        (self.proof / "SEED-PRODUCT.json").unlink()
        self.assertEqual(self._seal(), 1)
        self.assertIn("lacks check inputs a seeded run needs: SEED-PRODUCT.json (written by the Proof", self.stderr)
        self.assertIn("seal_proof.py inputs", self.stderr)
        self.assertFalse((self.proof / "APPROVAL.json").exists())

    def test_a_moving_powered_contract_needs_its_motion_and_power_inputs(self):
        self.design_contract = {"interfaces": [{"id": "lid", "kind": "coupled"}], "electrical": {"paths": []}}
        self.assertEqual(self._seal(), 1)
        for name in ("measure/motion.json", "snap/MOTION-REVIEW.json", "snap/MOTION-EVIDENCE.json",
                     "snap/motion.gif", "measure/power.json", "measure/mounts.json",
                     "measure/bought-placements.json"):
            with self.subTest(name=name):
                self.assertIn(name, self.stderr)
        self.assertEqual(self._inputs(), 1)
        self.assertIn("ok      SEED-PRODUCT.json", self.stdout)
        self.assertIn("MISSING measure/motion.json  (moving; written by the Proof's motion manifest", self.stdout)
        for name in ("measure/motion.json", "measure/power.json", "measure/mounts.json",
                     "measure/bought-placements.json", "snap/MOTION-REVIEW.json", "snap/MOTION-EVIDENCE.json",
                     "snap/motion.gif"):
            (self.proof / name).write_text("{}")
        self.assertEqual(self._inputs(), 0, self.stdout)
        self._motion_review(reviewer="the owner (Approved Proof)")
        self.assertEqual(self._seal(), 1)
        self.assertIn("MOTION-REVIEW.json cannot be carried into a seeded run: reviewer must name the Proof Critic",
                      self.stderr)
        self._motion_review(concept_sha256="0" * 64)
        self.assertEqual(self._seal(), 1)
        self.assertIn("concept_sha256 is not SEED-PRODUCT.json's concept hash", self.stderr)
        self._motion_review()
        self.assertEqual(self._seal(), 0, self.stderr)
        approval = json.loads((self.proof / "APPROVAL.json").read_text())
        self.assertIn("measure/motion.json", approval["manifest"])
        self.assertIn("measure/power.json", approval["check_inputs"])
        ran = [" ".join(argv) for argv in self.batch_calls]
        for tool in ("check_motion", "check_power", "check_mount", "bought_model.py", "--build",
                     "--print-gates-only", "--shared-helpers", "--design --strict-fit",
                     "seeded_package check"):
            with self.subTest(tool=tool):
                self.assertTrue(any(tool in line for line in ran), ran)
        self.assertFalse(any("--component" in line or "stage_proposal" in line or "--seed-nonce" in line
                             for line in ran), "the design plan needs no run state")
        # Every Interface check on the Proof reads the contract file.
        self.assertTrue(all("--contract" in line for line in ran if "--interface" in line))

    def test_seal_refuses_a_malformed_seed_product(self):
        product = dict(SEED_PRODUCT, summary=" ")
        (self.proof / "SEED-PRODUCT.json").write_text(json.dumps(product))
        self.assertEqual(self._seal(), 1)
        self.assertIn("needs a nonempty summary", self.stderr)

    def test_seal_refuses_a_failing_batch_with_every_failure_in_its_words(self):
        from workshop.make.seeded_batch import RunResult

        self.design_contract = {"electrical": {"paths": []}}
        for name in ("measure/power.json", "measure/mounts.json", "measure/bought-placements.json"):
            (self.proof / name).write_text("{}")
        self.batch_exit = {"check_power": RunResult(1, "check_power: path led draws 40 mA over 20"),
                           "check_mount": RunResult(1, "check_mount: lead hole clashes with switch wire")}
        self.assertEqual(self._seal(), 1)
        self.assertIn("seeded batch fails on the Proof (check-failure)", self.stderr)
        self.assertIn("draws 40 mA over 20", self.stderr)
        self.assertIn("lead hole clashes with switch wire", self.stderr)
        self.assertFalse((self.proof / "APPROVAL.json").exists())

    def test_verify_names_the_reseal_path_for_an_old_approval(self):
        self.assertEqual(self._seal(), 0, self.stderr)
        approval = json.loads((self.proof / "APPROVAL.json").read_text())
        approval["schema_version"] = 1
        (self.proof / "APPROVAL.json").write_text(json.dumps(approval))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(self.module.main(["verify", str(self.proof)]), 1)
        self.assertIn("sealed before ADR 0098 is re-sealed", err.getvalue())


if __name__ == "__main__":
    unittest.main()
