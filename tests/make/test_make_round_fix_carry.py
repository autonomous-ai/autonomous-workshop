"""A fix run keeps what its source run proved (issues #175, #176, #177).

#175: a lock a round recorded on its STEP's bytes, before `gen` reported a
current export's B-rep, is read as the B-rep that round's own reproduction
build logged. #176: rows that differ from the reviewed rows only in colour
words are the rows the review judged. #177: the review packet states the
Component's sealed numbers, and the reviewer lists a reference drawn
otherwise as a Reference Conflict.
"""

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

from tests.make import test_make_round as rounds

load_module = rounds.load_module
REPOSITORY = Path(__file__).resolve().parents[2]

B_REP = "b" * 64
OTHER_B_REP = "c" * 64


def logged(log, command, code, stdout):
    """A command log as make_round's ``run`` writes it."""
    Path(log).parent.mkdir(parents=True, exist_ok=True)
    Path(log).write_text("$ %s\n(0.1s, exit %d)\n--- stdout\n%s\n--- stderr\n"
                         % (" ".join(map(str, command)), code, stdout), encoding="utf-8")


class FixRunCarryTest(unittest.TestCase):
    _run_root = rounds.SealedReferenceTest._run_root
    REFS = rounds.ContractComponentReviewTest.REFS
    POSED = rounds.ReferenceCameraRoundTest.POSED
    FACE = ("The face is a groove 0.6 wide on an arc of radius 0.65 from 30 to 150 degrees. "
            "It reads as a wink.")

    def setUp(self):
        # What each tool reports: gen's B-rep (None: a current export before
        # issue #165) and what the reproduction build logged.
        self.gen_brep = None
        self.reproduced = (0, B_REP)
        self.calls = []

    def _contract(self, schema=8):
        references = [{"file": "ref-01-whole.png", "shows": "assembly", "camera": [-60, 20]},
                      {"file": "ref-02-body.png", "shows": "geometry:body", "camera": [90, 15]}]
        geometries = [{"id": "body", "name": "Body", "count": 1, "extents_mm": [30, 20, 10],
                       "prose_sections": ["Body", "Body and base", "Everything"]},
                      {"id": "base", "name": "Base", "count": 1, "extents_mm": [80, 80, 10],
                       "prose_sections": ["Body and base", "Everything"]},
                      {"id": "wing", "name": "Wing", "count": 1, "extents_mm": [40, 10, 4],
                       "prose_sections": ["Everything"]}]
        requirements = [{"id": "R01", "scope": "assembly", "text": "The body stands on the base, in mint."},
                        {"id": "R02", "scope": "geometry:body", "text": "The body is one colour, translucent amber."}]
        interfaces = [{"id": "body-base", "kind": "static", "components": ["body", "base"],
                       "text": "The body's 3.7 mm shaft sits in a 3.9 mm socket."}]
        prose = [{"heading": "Body", "text": self.FACE},
                 {"heading": "Body and base", "text": "Both print in dark oak; the base is 80 wide."},
                 {"heading": "Everything", "text": "Shells left to right: dark blue, oak, translucent amber. "
                                                   "The frame is 12.4 tall."}]
        contract = {"schema_version": schema, "title": "Turtle", "references": references,
                    "geometries": geometries, "requirements": requirements, "interfaces": interfaces,
                    "prose": prose}
        return {"design_contract": contract}

    def _root(self, tmp, schema=8):
        project = self._run_root(tmp, self.REFS, context=self._contract(schema))
        (project / "part_body.step.py").write_text(self.POSED % 1)
        return project

    def _wish(self, project, change):
        path = rounds.module_run_root(project) / "WISH.json"
        wish = json.loads(path.read_text())
        change(wish["context"]["design_contract"])
        path.write_text(json.dumps(wish))

    def _fake_run(self, calls, faults=None):
        base = rounds.SealedReferenceTest._fake_run(self, calls, faults)

        def fake_run(command, **kwargs):
            tool = Path(command[1]).name
            log = kwargs.get("log")
            if tool == "gen":
                base(command, **kwargs)
                payload = {"ok": True}
                if self.gen_brep is not None:
                    payload["identitySha256"] = self.gen_brep
                stdout = json.dumps(payload) + "\n"
                logged(log, command, 0, stdout)
                return subprocess.CompletedProcess(command, 0, stdout, "")
            if tool == "reproduce_build":
                calls.append(command)
                code, identity = self.reproduced
                stdout = json.dumps({"identitySha256": identity}) + "\n" if identity else ""
                logged(log, command, code, stdout)
                return subprocess.CompletedProcess(command, code, stdout, "")
            return base(command, **kwargs)

        return fake_run

    def _main(self, module, project, argv):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as stderr, \
                mock.patch.object(module, "skills_root", return_value=project), \
                mock.patch.object(module, "run", side_effect=self._fake_run(self.calls)), \
                mock.patch.object(module, "read_freeze", return_value={"round": 1, "helpers": {}}), \
                mock.patch.object(module, "freeze_report", return_value={}):
            code = module.main([str(project), *argv])
        self.stderr = stderr.getvalue()
        return code

    def _component(self, module, project):
        code = self._main(module, project, ["--component", "part_body.step.py"])
        state = json.loads((project / "measure/component-rounds/body/make-round-state.json").read_text())
        summary = json.loads((project / ("measure/component-rounds/body/r%04d/summary.json"
                                         % state["round"])).read_text())
        return code, state, summary

    def _locked(self, module, project):
        """Round 1, locked by an agreeing review, the way gen reported it then."""
        _, _, summary = self._component(module, project)
        module.record_review(project, rounds.write_review(project, summary), "part_body.step.py")
        state = json.loads((project / "measure/component-rounds/body/make-round-state.json").read_text())
        self.assertEqual(state["policy"]["phase"], module.LOCKED)
        return state, summary

    # -- issue #175 -------------------------------------------------------

    def test_a_lock_on_step_bytes_carries_to_the_same_b_rep_built_now(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module = load_module()
            state, first = self._locked(module, project)
            step = hashlib.sha256((project / "part_body.step").read_bytes()).hexdigest()
            # Before #165: the lock recorded the STEP's bytes as the shape.
            self.assertEqual(state["policy"]["reviewed"]["identity"], step)
            self.assertEqual(first["identity"], step)

            self.gen_brep = B_REP
            # An Interface check reads the lock as the B-rep before any new round.
            _, reason = module.current_passing_component_round(project, "body", B_REP)
            self.assertEqual(reason, "")
            self.assertEqual(module.locked_at(project, "body", B_REP), "")
            self.assertIn("changed after its component pass", module.locked_at(project, "body", OTHER_B_REP))

            code, state, second = self._component(module, project)
            self.assertEqual(code, 0, self.stderr)
            self.assertEqual(second["identity"], B_REP)
            self.assertEqual(second["review"]["carried_from"], 1)
            self.assertEqual(second["visual"]["status"], "carried")
            self.assertEqual((second["shape_round"], second["unlock"], second["phase"]),
                             (False, [], module.LOCKED))
            reviewed = state["policy"]["reviewed"]
            self.assertEqual((reviewed["identity"], reviewed["step_identity"]), (B_REP, step))
            # It keeps carrying on the next unchanged rerun.
            code, _, third = self._component(module, project)
            self.assertEqual((code, third["review"]["carried_from"]), (0, 1))

    def test_a_lock_on_step_bytes_still_refuses_another_b_rep(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module = load_module()
            self._locked(module, project)
            self.gen_brep = OTHER_B_REP
            self.reproduced = (0, OTHER_B_REP)
            self.assertEqual(self._main(module, project, ["--component", "part_body.step.py"]), 2)
            self.assertIn("the Component is locked by an agreeing review of r0001", self.stderr)

    def test_no_migration_without_one_logged_b_rep(self):
        cases = {
            "reproduction failed": (1, None),
            "reproduction reported nothing": (0, None),
        }
        for name, reproduced in cases.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as tmp:
                project = self._root(tmp)
                module = load_module()
                self.gen_brep, self.reproduced = None, reproduced
                _, _, summary = self._component(module, project)
                module.record_review(project, rounds.write_review(project, summary), "part_body.step.py")
                self.gen_brep, self.reproduced = B_REP, (0, B_REP)
                self.assertIn("changed after its component pass", module.locked_at(project, "body", B_REP))
                self.assertEqual(self._main(module, project, ["--component", "part_body.step.py"]), 2)

    def test_step_byte_brep_reads_only_a_fallback_round_with_one_identity(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            round_dir = Path(tmp)
            gen, repro, bundle = (round_dir / name for name in
                                  ("gen-body.log", "reproduce-body.log", "brep-body.log"))
            self.assertIsNone(module.step_byte_brep(round_dir, "body"), "no gen log")
            logged(gen, ["python", "gen"], 0, '{"ok":true}')
            logged(repro, ["python", "reproduce_build"], 0, json.dumps({"identitySha256": B_REP}))
            self.assertEqual(module.step_byte_brep(round_dir, "body"), B_REP)
            logged(bundle, ["python", "brepbundle.py"], 0,
                   json.dumps({"brepBundle": {"builtIdentity": B_REP, "identity": B_REP}}))
            self.assertEqual(module.step_byte_brep(round_dir, "body"), B_REP)
            logged(bundle, ["python", "brepbundle.py"], 0,
                   json.dumps({"brepBundle": {"builtIdentity": OTHER_B_REP, "identity": OTHER_B_REP}}))
            self.assertIsNone(module.step_byte_brep(round_dir, "body"), "two identities")
            bundle.unlink()
            logged(gen, ["python", "gen"], 0, json.dumps({"ok": True, "identitySha256": OTHER_B_REP}))
            self.assertIsNone(module.step_byte_brep(round_dir, "body"), "gen built it: not a fallback")
            logged(gen, ["python", "gen"], 1, "")
            self.assertIsNone(module.step_byte_brep(round_dir, "body"), "gen failed")

    # -- issue #176 -------------------------------------------------------

    def _recolour(self, contract):
        contract["requirements"][1]["text"] = "The body is one colour, Brass."
        contract["prose"][1]["text"] = "Both print in jade; the base is 80 wide."
        contract["prose"][2]["text"] = ("Shells left to right: dark-blue, oak, brass. "
                                        "The frame is 12.4 tall.")

    def test_a_colour_only_contract_change_keeps_the_lock_and_carries(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module = load_module()
            self.gen_brep = B_REP
            state, first = self._locked(module, project)
            self._wish(project, self._recolour)
            self.assertNotEqual(module.contract_rows(project, "body"), first["contract_rows"])
            code, state, second = self._component(module, project)
            self.assertEqual(code, 0, self.stderr)
            self.assertEqual((second["review"]["carried_from"], second["unlock"], second["phase"]),
                             (1, [], module.LOCKED))
            self.assertTrue(second["rows_colour_only"])
            # The summary keeps the rows it delivered; the lock keeps the reviewed ones.
            self.assertEqual(second["contract_rows"], module.contract_rows(project, "body"))
            self.assertEqual(state["policy"]["reviewed"]["contract_rows"], first["contract_rows"])
            self.assertIn("rows changed only in colour words", module.render_summary(second))
            code, _, third = self._component(module, project)
            self.assertEqual((code, third["review"]["carried_from"]), (0, 1))

    def test_an_owner_colour_amendment_keeps_the_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module = load_module()
            self.gen_brep = B_REP
            self._locked(module, project)
            amendments = {"owner_amendments": [{"changes": [
                {"row": "prose:Everything", "scope": "prose", "from": "x",
                 "to": "Shells left to right: dark blue, oak, brass. The frame is 12.4 tall."}]}]}
            (rounds.module_run_root(project) / module.AMENDMENTS_NAME).write_text(json.dumps(amendments))
            code, _, second = self._component(module, project)
            self.assertEqual((code, second["review"]["carried_from"]), (0, 1))

    def test_a_change_beside_the_colour_unlocks_and_is_reviewed_again(self):
        changes = {
            "a sentence removed": lambda contract: contract["prose"][2].update(
                text="Shells left to right: dark blue, oak, brass."),
            "a word added": lambda contract: contract["prose"][1].update(
                text="Both print in jade; the base is 80 wide and glossy."),
            "a number moved": lambda contract: contract["prose"][0].update(
                text=self.FACE.replace("0.6 wide", "0.8 wide")),
        }
        for name, change in changes.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as tmp:
                project = self._root(tmp)
                module = load_module()
                self.gen_brep = B_REP
                self._locked(module, project)
                self._wish(project, change)
                code, _, second = self._component(module, project)
                self.assertEqual(code, 1, self.stderr)
                self.assertIsNone(second["review"])
                self.assertEqual(second["phase"], module.AWAITING)
                self.assertEqual([item["kind"] for item in second["unlock"]], ["contract-amendment"])
                self.assertNotIn("rows_colour_only", second)

    def test_old_rows_that_do_not_reproduce_the_recorded_hash_carry_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module = load_module()
            self.gen_brep = B_REP
            _, first = self._locked(module, project)
            summary_path = Path(first["out"]) / "summary.json"
            tampered = json.loads(summary_path.read_text())
            tampered["contract"]["prose"][0]["text"] = "Anything at all."
            summary_path.write_text(json.dumps(tampered))
            self._wish(project, self._recolour)
            code, _, second = self._component(module, project)
            self.assertEqual(code, 1)
            self.assertIsNone(second["review"])
            self.assertFalse(module.colour_only_rows(
                project, "body", {"round": 1, "contract_rows": first["contract_rows"]},
                project / "measure/component-rounds/body"))

    def test_colour_blind_masks_palette_names_in_any_spelling(self):
        module = load_module()
        self.assertEqual(module.colour_blind("Dark-Oak, translucent amber, MINT, #A3D9C3 and dark_blue"),
                         "<colour>, <colour>, <colour>, <colour> and <colour>")
        # A longer name wins, and a word inside another word is not a colour.
        self.assertEqual(module.colour_blind("dark oak shell; oaken; greenery"), "<colour> shell; oaken; greenery")
        self.assertEqual(module.colour_blind({"text": ["oak"], "n": 1}), {"text": ["<colour>"], "n": 1})

    # -- issue #177 -------------------------------------------------------

    def test_the_packet_states_the_components_own_sealed_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module = load_module()
            _, _, summary = self._component(module, project)
            packet = json.loads(Path(summary["visual"]["packet"]).read_text())
            expected = [
                {"section": "Body", "text": "The face is a groove 0.6 wide on an arc of radius 0.65 from 30 to "
                                            "150 degrees."},
                {"section": "Body and base", "text": "Both print in dark oak; the base is 80 wide."},
            ]
            # "Everything" is named by every geometry: the assembly's, not the body's.
            self.assertEqual(packet["contract"]["numbers"], expected)
            self.assertEqual(summary["contract"]["numbers"], expected)
            self.assertNotIn("It reads as a wink.", json.dumps(packet))
            self.assertIn("Reference Conflict, never a difference", summary["visual"]["detail"])
            self.assertIn("numbers 2 sealed number sentence(s)", module.render_summary(summary))

    def test_one_geometry_states_every_section_and_before_schema_8_none(self):
        module = load_module()
        contract = self._contract()["design_contract"]
        contract["geometries"] = contract["geometries"][:1]
        self.assertEqual(module.sealed_numbers(self._contract()["design_contract"], "wing"), [])
        self.assertEqual([item["section"] for item in module.sealed_numbers(contract, "body")],
                         ["Body", "Body and base", "Everything"])
        contract["schema_version"] = 7
        self.assertEqual(module.sealed_numbers(contract, "body"), [])

    def test_the_reviewer_lists_a_reference_drawn_against_a_sealed_number_as_a_conflict(self):
        reviewer = " ".join((REPOSITORY / "src/workshop/make/agents/component-reviewer.toml")
                            .read_text(encoding="utf-8").split())
        for required in (
            "A sealed number wins over the drawing (issue #177)",
            "`contract` may hold `numbers`",
            "that is a Reference Conflict, never a difference: quote the number in `contract`",
            "Judge the feature against the number, not the drawing",
            "Never ask a feature the contract sizes to be wider, longer, deeper, bolder or moved",
            "A feature built to its number does not make `matches_reference` false",
            "apart from every Reference Conflict you list",
        ):
            with self.subTest(required):
                self.assertIn(required, reviewer)
        self.assertNotIn("only settle what the reference cannot show", reviewer)


if __name__ == "__main__":
    unittest.main()
