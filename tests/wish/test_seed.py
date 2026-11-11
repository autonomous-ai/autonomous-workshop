"""ADR 0096 Phase 2: the host validates an Approved Proof before it seeds a run.

Contract: `validate_seed` accepts the directory `seal_proof.py seal` wrote and
refuses a missing or unknown APPROVAL.json, another contract, a manifest
that does not hash, a missing, extra or changed file, a symlink, a path
outside the directory, a CRITIC.json or CONCEPT-CHECKLIST.md that is absent
or not the approved one, a geometry without an approved Component (or the
reverse), an approved STEP that is not the sealed one, and no approver or
date. `copy_seed` copies exactly the approval and its manifest."""

from __future__ import annotations

import hashlib
import json
import unittest

from tests.skills import test_seal_proof as seal_tests
from workshop.errors import ContractError
from workshop.wish.seed import copy_seed, manifest_sha256, seed_manifest, validate_seed


sha = seal_tests.sha


class SeedValidationTest(unittest.TestCase):
    _record = seal_tests.SealProofTest._record
    _seal = seal_tests.SealProofTest._seal

    def setUp(self):
        seal_tests.SealProofTest.setUp(self)
        self.assertEqual(self._seal(), 0, self.stderr)
        self.approval_path = self.proof / "APPROVAL.json"
        self.digest = sha(self.contract)

    def _validate(self, ids=("body",)):
        return validate_seed(self.proof, ids, self.digest)

    def _refused(self, fragment, ids=("body",)):
        with self.assertRaises(ContractError) as caught:
            self._validate(ids)
        self.assertIn(fragment, str(caught.exception))

    def _edit(self, change):
        approval = json.loads(self.approval_path.read_text())
        change(approval)
        self.approval_path.write_text(json.dumps(approval))

    def _remanifest(self, approval):
        approval["manifest_sha256"] = manifest_sha256(approval["manifest"])

    def test_the_sealed_proof_validates(self):
        seed = self._validate()
        self.assertEqual(seed.approval_sha256, sha(self.approval_path))
        self.assertEqual(seed.frozen(), {"approval_sha256": seed.approval_sha256,
                                         "manifest_sha256": seed.manifest_sha256})
        self.assertEqual((seed.approved_by, seed.date), ("owner", "2026-11-02"))
        self.assertEqual(seed.components["body"]["carry_key"], "key")
        self.assertEqual(dict(seed.files), seed_manifest(self.proof))

    def test_approval_file_refusals(self):
        with self.assertRaises(ContractError) as caught:
            validate_seed(self.proof, ("body",), "0" * 64)
        self.assertIn("sealed for another contract", str(caught.exception))
        self._edit(lambda a: a.update(schema_version=5))
        self._refused("schema_version 5 is not 2, 3 or 4")
        self.approval_path.write_text("{")
        self._refused("does not parse")
        self.approval_path.unlink()
        self._refused("has no APPROVAL.json")
        with self.assertRaises(ContractError):
            validate_seed(self.root / "nowhere", ("body",), self.digest)

    def test_manifest_refusals(self):
        (self.proof / "params.py").write_text("PEG_D = 9\n")
        self._refused("changed file(s) against the approval's manifest: params.py")
        (self.proof / "params.py").write_text("PEG_D = 4.0  # wiki: joints-and-fits\nassert PEG_D >= 3\n")
        (self.proof / "stray.py").write_text("")
        self._refused("extra file(s) against the approval's manifest: stray.py")
        (self.proof / "stray.py").unlink()
        (self.proof / "CRITIC.json").rename(self.root / "CRITIC.json")
        self._refused("missing file(s) against the approval's manifest: CRITIC.json")
        (self.root / "CRITIC.json").rename(self.proof / "CRITIC.json")
        (self.proof / "link.py").symlink_to(self.proof / "params.py")
        self._refused("link.py is a symlink")
        (self.proof / "link.py").unlink()
        self._edit(lambda a: a["manifest"].update({"params.py": "0" * 64}))
        self._refused("does not hash to manifest_sha256")

    def test_a_path_outside_the_directory_refuses(self):
        def escape(approval):
            approval["manifest"]["../outside.py"] = "0" * 64
            self._remanifest(approval)
        self._edit(escape)
        self._refused("is outside the seed directory")

    def test_critic_and_checklist_must_be_the_approved_ones(self):
        self._edit(lambda a: a["critic"].update(sha256="1" * 64))
        self._refused("CRITIC.json is not the one the owner approved")
        self.assertEqual(self._seal(), 0, self.stderr)
        def drop(approval):
            del approval["manifest"]["CONCEPT-CHECKLIST.md"]
            self._remanifest(approval)
        self._edit(drop)
        (self.proof / "CONCEPT-CHECKLIST.md").unlink()
        self._refused("has no CONCEPT-CHECKLIST.md")

    def test_component_refusals(self):
        self._refused("geometries have no approved Component: wing", ids=("body", "wing"))
        self._refused("Components the contract does not declare: body", ids=())
        self._edit(lambda a: a["components"]["body"].update(step_sha256="2" * 64))
        self._refused("approved STEP is not the one sealed")
        self.assertEqual(self._seal(), 0, self.stderr)
        self._edit(lambda a: a["components"]["body"].update(approved_step="approved/other.step"))
        self._refused("has no approved STEP in the manifest")
        self.assertEqual(self._seal(), 0, self.stderr)
        self._edit(lambda a: a["components"]["body"].pop("carry_key"))
        self._refused("component body has no carry_key")

    def test_a_schema_2_seal_without_assembly_renders_still_validates(self):
        """ADR 0102's 2026-11-11 amendment: existing seals keep the reference look."""
        def older(approval):
            approval["schema_version"] = 2
            approval.pop("contract_images")
        self._edit(older)
        seed = self._validate()
        self.assertIsNone(seed.assembly_renders)
        self.assertIsNone(seed.contract_images)

    def test_contract_image_refusals(self):
        """ADR 0103: a schema 4 seal's contract images."""
        record = {"file": "ref-01-assembly.png", "kind": "reference", "shows": "assembly",
                  "camera": [90, 15], "sha256": "4" * 64}
        guide = {"file": "guide-01-body.png", "kind": "guide", "shows": "the back", "views": [[180, 0]],
                 "sha256": "5" * 64}
        self._edit(lambda a: a.update(contract_images=[record, guide]))
        self.assertEqual(len(self._validate().contract_images), 2)
        contract = {"references": [{"file": "ref-01-assembly.png", "shows": "assembly", "camera": [90, 15]}],
                    "guides": [{"file": "guide-01-body.png", "shows": "the back"}]}
        validate_seed(self.proof, ("body",), self.digest, contract)
        contract["references"][0]["camera"] = [0, 0]
        with self.assertRaisesRegex(ContractError, "not the contract's references at their cameras"):
            validate_seed(self.proof, ("body",), self.digest, contract)
        for fragment, images in (
            ("has no Reference Camera", [dict(record, camera=None)]),
            ("records no camera", [dict(guide, views=[])]),
            ("invalid contract image", [dict(record, sha256="x")]),
            ("invalid contract image", [dict(record, file="../ref-01-assembly.png")]),
            ("records no contract_images", None),
        ):
            with self.subTest(fragment):
                self._edit(lambda a: a.update(contract_images=images))
                self._refused(fragment)

    def test_a_launch_passes_exactly_the_sealed_renders(self):
        from workshop.wish.seed import check_launch_images
        record = {"file": "ref-01-assembly.png", "kind": "reference", "shows": "assembly",
                  "camera": [90, 15], "sha256": "4" * 64}
        self._edit(lambda a: a.update(contract_images=[record]))
        seed = self._validate()
        check_launch_images(seed, {"ref-01-assembly.png": "4" * 64})
        # The archived design-time AI image has other bytes.
        with self.assertRaisesRegex(ContractError, "never reads a design-time image"):
            check_launch_images(seed, {"ref-01-assembly.png": "9" * 64})
        with self.assertRaisesRegex(ContractError, "were not passed"):
            check_launch_images(seed, {})
        # An older seal records none and checks none.
        check_launch_images(validate_seed.__globals__["SeedApproval"](**{**seed.__dict__, "contract_images": None}),
                            {"ref-01-assembly.png": "9" * 64})

    def test_assembly_render_refusals(self):
        render = "approved/assembly/az90_el15.png"
        (self.proof / "approved/assembly").mkdir()
        (self.proof / render).write_bytes(b"render")

        def with_render(**item):
            def change(approval):
                approval["schema_version"] = 3
                approval.pop("contract_images", None)
                approval["manifest"][render] = sha(self.proof / render)
                self._remanifest(approval)
                approval["assembly_renders"] = [{"file": render, "camera": [90, 15],
                                                 "sha256": sha(self.proof / render), **item}]
            return change
        self._edit(with_render())
        self.assertEqual(self._validate().assembly_renders[0]["camera"], [90.0, 15.0])
        contract = {"references": [{"file": "ref-01-assembly.png", "shows": "assembly", "camera": [0, 0]}]}
        with self.assertRaisesRegex(ContractError, "not at the contract's assembly Reference Cameras"):
            validate_seed(self.proof, ("body",), self.digest, contract)
        for fragment, change in (
            ("not named for its camera", with_render(camera=[0, 0])),
            ("not in the manifest as sealed", with_render(sha256="3" * 64)),
            ("invalid assembly render", with_render(extra=1)),
            ("records no assembly_renders", lambda a: a.pop("assembly_renders")),
        ):
            with self.subTest(fragment):
                self._edit(change)
                self._refused(fragment)

    def test_approver_and_date_are_required(self):
        self._edit(lambda a: a.update(approved_by=" "))
        self._refused("names no approved_by")
        self.assertEqual(self._seal(), 0, self.stderr)
        self._edit(lambda a: a.update(date="yesterday"))
        self._refused("is not YYYY-MM-DD")

    def test_copy_seed_copies_exactly_the_approval_and_manifest(self):
        seed = self._validate()
        (self.proof / "measure/evidence.txt").write_text("not seeded")
        target = self.root / "run/seed"
        copy_seed(seed, self.proof, target)
        self.assertEqual(seed_manifest(target), dict(seed.files))
        self.assertEqual(hashlib.sha256((target / "APPROVAL.json").read_bytes()).hexdigest(), seed.approval_sha256)
        self.assertFalse((target / "measure/evidence.txt").exists())
        self.assertEqual(sorted(path.name for path in (target / "measure").iterdir()),
                         ["check_fit.py", "check_landmarks.py", "check_spec.py"])
        self.assertEqual(validate_seed(target, ("body",), self.digest), seed)
        with self.assertRaises(ContractError):
            copy_seed(seed, self.proof, target)


class CheckInputsRefusalTest(unittest.TestCase):
    """ADR 0098 owner decision 2 (option b): a new launch refuses an Approved
    Proof without the check inputs its contract needs, naming each and the
    re-seal path."""

    _record = seal_tests.SealProofTest._record
    _seal = seal_tests.SealProofTest._seal
    MOVING = {"interfaces": [{"id": "lid", "kind": "coupled"}]}

    def setUp(self):
        seal_tests.SealProofTest.setUp(self)
        self.assertEqual(self._seal(), 0, self.stderr)
        self.approval_path = self.proof / "APPROVAL.json"
        self.digest = sha(self.contract)

    def _refusal(self, contract=None):
        with self.assertRaises(ContractError) as caught:
            validate_seed(self.proof, ("body",), self.digest, contract)
        return str(caught.exception)

    def _legacy(self):
        """What seal_proof wrote before ADR 0098: schema 1, no check inputs."""
        approval = json.loads(self.approval_path.read_text())
        approval["schema_version"] = 1
        del approval["check_inputs"], approval["batch"]
        self.approval_path.write_text(json.dumps(approval))

    def test_an_approval_sealed_before_adr_0098_is_refused_naming_inputs_and_reseal(self):
        self._legacy()
        (self.proof / "SEED-PRODUCT.json").unlink()
        message = self._refusal(self.MOVING)
        self.assertIn("sealed before ADR 0098", message)
        for name in ("SEED-PRODUCT.json", "measure/motion.json", "snap/MOTION-REVIEW.json"):
            with self.subTest(name=name):
                self.assertIn(name, message)
        self.assertNotIn("snap/iso.png", message, "a present input is not named missing")
        self.assertIn("Re-seal it through design-a-toy", message)
        self.assertIn("seal_proof.py inputs %s" % self.proof, message)
        self.assertIn("continue it with `workshop resume`", message)

    def test_a_legacy_approval_with_every_file_present_still_names_what_it_lacks(self):
        self._legacy()
        message = self._refusal()
        self.assertIn("SEED-PRODUCT.json", message)
        self.assertIn("Re-seal it through design-a-toy", message)

    def test_a_current_approval_must_record_every_input_its_contract_needs(self):
        validate_seed(self.proof, ("body",), self.digest, {})
        message = self._refusal(self.MOVING)
        self.assertIn("does not record the check inputs its contract needs: measure/motion.json", message)
        self.assertIn("Re-seal it through design-a-toy", message)

    def test_a_check_input_must_be_sealed_in_the_manifest(self):
        approval = json.loads(self.approval_path.read_text())
        approval["check_inputs"]["SEED-PRODUCT.json"] = "0" * 64
        self.approval_path.write_text(json.dumps(approval))
        self.assertIn("check input SEED-PRODUCT.json is not in the manifest as sealed", self._refusal())

    def test_an_approval_without_a_passing_batch_is_refused(self):
        approval = json.loads(self.approval_path.read_text())
        approval["batch"]["ok"] = False
        self.approval_path.write_text(json.dumps(approval))
        self.assertIn("no passing seeded batch dry run", self._refusal())

    def test_the_check_inputs_are_part_of_the_seed_tree(self):
        (self.proof / "measure/motion.json").write_text("{}")
        (self.proof / "measure/round-notes.json").write_text("{}")
        files = seed_manifest(self.proof)
        self.assertIn("measure/motion.json", files)
        self.assertNotIn("measure/round-notes.json", files)


if __name__ == "__main__":
    unittest.main()
