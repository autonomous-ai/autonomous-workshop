"""ADR 0096: `make_round --identities-only` records an Approved Proof with
the code a component round runs.

Contract: outside a run, with `--contract`, it prints each Component's B-rep
identity, STEP sha256, imported Shared Helpers, contract rows hash and carry
key, and the assembly identity. The rows hash and carry key equal what a
component round computes in a run that sealed the same contract and images,
so a seeded run can carry the design's review. It refuses a run directory, a
Component that does not build, a missing reference, a geometry with no part
and a part with no geometry (exit 2), and it takes no round flag."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.make import test_make_round as make_round_tests
from tests.wish.test_design_contract import _block, _contract_text
from workshop.wish.design_contract import parse_design_contract

REFS = {"ref-01-antisol.png": b"whole", "ref-02-world-disc.png": b"disc"}


def contract_block():
    block = _block(schema_version=3, interfaces=[])
    block["references"][0]["camera"] = [30, 20]
    block["references"][1]["camera"] = [-45, 10]
    return block


class IdentitiesOnlyTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.module = make_round_tests.load_module()
        self.broken = set()
        self.design = self.root / "design"
        self.project = self.design / "proof"
        (self.project / "features").mkdir(parents=True)
        (self.project / "features/__init__.py").write_text("")
        (self.project / "features/rim.py").write_text("RIM = 2.0\n")
        (self.project / "part_world-disc.step.py").write_text(
            "from features.rim import RIM\ndef gen_step(): return 'disc'\n")
        for name, tag in REFS.items():
            (self.design / name).write_bytes(make_round_tests.png(tag))
        self.text = _contract_text(contract_block())
        self.contract = self.design / "CONTRACT.md"
        self.contract.write_text(self.text)

    def _fake(self, command, **kwargs):
        if Path(command[1]).name == "gen":
            source = Path(command[2])
            if source.name in self.broken:
                return subprocess.CompletedProcess(command, 1, "", "ValueError: broken\n")
            source.with_name(source.name[:-len(".py")]).write_bytes(source.read_bytes())
        return subprocess.CompletedProcess(command, 0, '{"ok":true}\n', "")

    def _main(self, project, *argv):
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err, \
                mock.patch.object(self.module, "skills_root", return_value=self.root), \
                mock.patch.object(self.module, "run", side_effect=self._fake):
            code = self.module.main([str(project), *argv])
        self.stdout, self.stderr = out.getvalue(), err.getvalue()
        return code

    def test_records_every_component_and_the_assembly(self):
        out = self.root / "identities.json"
        self.assertEqual(self._main(self.project, "--identities-only", "--contract", str(self.contract),
                                    "--out", str(out)), 0, self.stderr)
        document = json.loads(out.read_text())
        self.assertEqual(document, json.loads(self.stdout))
        self.assertEqual(document["contract_sha256"], hashlib.sha256(self.contract.read_bytes()).hexdigest())
        disc = document["components"]["world-disc"]
        step = (self.project / "part_world-disc.step").read_bytes()
        self.assertEqual(disc["step_sha256"], hashlib.sha256(step).hexdigest())
        self.assertEqual(disc["identity"], disc["step_sha256"])  # no identitySha256 from the fake gen
        self.assertIn("features/rim.py", disc["imported_helpers"])
        self.assertEqual(document["assembly_identity"], hashlib.sha256(
            json.dumps({"world-disc": disc["identity"]}, sort_keys=True).encode()).hexdigest())

    def test_rows_and_carry_key_equal_a_runs_component_round(self):
        self.assertEqual(self._main(self.project, "--identities-only", "--contract", str(self.contract)), 0,
                         self.stderr)
        disc = json.loads(self.stdout)["components"]["world-disc"]
        sealed = parse_design_contract(self.text).to_dict()
        run_project = make_round_tests.SealedReferenceTest._run_root(
            None, str(self.root / "run"), REFS, context={"design_contract": sealed}) \
            if (self.root / "run").mkdir() is None else None
        (run_project / "part_body.step.py").unlink()
        for path in self.project.rglob("*.py"):
            target = run_project / path.relative_to(self.project)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
        self.assertEqual(self.module.contract_rows(run_project, "world-disc"), disc["contract_rows"])
        refs, _report, errors = self.module.with_component_reference(run_project, "world-disc", [])
        self.assertEqual(errors, [])
        self.assertEqual(self.module.carry_key(disc["identity"], refs, run_project,
                                               disc["contract_rows"], []), disc["carry_key"])
        # A changed reference image changes the key; so does a changed row.
        (self.design / "ref-02-world-disc.png").write_bytes(make_round_tests.png(b"other"))
        self.assertEqual(self._main(self.project, "--identities-only", "--contract", str(self.contract)), 0)
        self.assertNotEqual(json.loads(self.stdout)["components"]["world-disc"]["carry_key"], disc["carry_key"])

    def test_refusals(self):
        self.broken.add("part_world-disc.step.py")
        self.assertEqual(self._main(self.project, "--identities-only", "--contract", str(self.contract)), 2)
        self.assertIn("does not build", self.stderr)
        self.broken.clear()
        (self.design / "ref-02-world-disc.png").unlink()
        self.assertEqual(self._main(self.project, "--identities-only", "--contract", str(self.contract)), 2)
        self.assertIn("is not beside the contract", self.stderr)
        (self.design / "ref-02-world-disc.png").write_bytes(make_round_tests.png(b"disc"))
        (self.project / "part_extra.step.py").write_text("def gen_step(): return 'x'\n")
        self.assertEqual(self._main(self.project, "--identities-only", "--contract", str(self.contract)), 2)
        self.assertIn("part_extra.step.py builds no Unique Geometry", self.stderr)
        (self.project / "part_extra.step.py").unlink()
        (self.project / "part_world-disc.step.py").rename(self.project / "disc.step.py")
        self.assertEqual(self._main(self.project, "--identities-only", "--contract", str(self.contract)), 2)
        self.assertIn("has no part_<id>.step.py", self.stderr)
        self.contract.write_text("no block")
        self.assertEqual(self._main(self.project, "--identities-only", "--contract", str(self.contract)), 2)

    def test_a_missing_geometry_part_refuses(self):
        block = contract_block()
        block["geometries"].append({"id": "sun", "name": "Sun", "count": 1, "extents_mm": [10, 10, 10],
                                    "wall_min_mm": 1.2})
        self.contract.write_text(_contract_text(block))
        self.assertEqual(self._main(self.project, "--identities-only", "--contract", str(self.contract)), 2)
        self.assertIn("no part_<id>.step.py for the contract's geometries: sun", self.stderr)

    def test_inside_a_run_refuses(self):
        (self.root / "run").mkdir()
        run_project = make_round_tests.SealedReferenceTest._run_root(None, str(self.root / "run"), REFS)
        self.assertEqual(self._main(run_project, "--identities-only", "--contract", str(self.contract)), 2)
        self.assertIn("outside a Workshop run", self.stderr)

    def test_usage_errors(self):
        for argv in (["--identities-only"],
                     ["--identities-only", "--contract", str(self.contract), "--component", "part_world-disc.step.py"],
                     ["--identities-only", "--contract", str(self.contract), "--shared-helpers"]):
            with self.subTest(argv=argv), self.assertRaises(SystemExit), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.module.main([str(self.project), *argv])


if __name__ == "__main__":
    unittest.main()
