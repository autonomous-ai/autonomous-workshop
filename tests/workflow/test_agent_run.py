import hashlib
import json
import os
import shutil
import stat
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

import workshop.workflow.agent_run as agent_run_module
from workshop.contributors.extensions import fingerprint_extension_skill
from workshop.errors import ArtifactError, ContractError, StateConflict, TransitionError
from workshop.runtime.agent_assets import parse_inventor_custom_agent_bytes
from workshop.runtime.managers import manager_project_bytes, manager_spec
from workshop.workflow import (
    AgentArtifact,
    AgentOutcome,
    AgentRun,
    DeterministicGateReceipt,
)


EVIDENCE_SHA256 = "e" * 64


def canonical_wish(product_id, objective, references=None):
    document = {
        "schema_version": 1,
        "product_id": product_id,
        "objective": objective,
        "constraints": {},
        "context": {"source": "agent-run-test"},
    }
    if references:
        document["references"] = list(references)
    return json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def reference_fixture(index, slug, content, media_type="image/png"):
    extension = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[media_type]
    return {
        "name": "ref-%02d-%s.%s" % (index, slug, extension),
        "sha256": hashlib.sha256(content).hexdigest(),
        "media_type": media_type,
        "size": len(content),
        "width": 640,
        "height": 480,
    }


class AgentRunTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.product_run_constitution = (
            self.root / "source" / ".agents" / "product-run" / "AGENTS.md"
        )
        self.skill = self.root / "skill"
        self.product_run_constitution.parent.mkdir(parents=True)
        self.skill.mkdir()
        self.product_run_constitution.write_bytes(b"# Product run constitution\n")
        (self.skill / "SKILL.md").write_bytes(b"# Workshop skill\n")
        references = self.skill / "references"
        references.mkdir()
        (references / "make-playtest.md").write_bytes(b"exact gate guidance\n")
        (references / "release-terminal-v1.md").write_bytes(
            b"terminal Release capability\n"
        )
        self.run_root = self.root / "run"
        self.host_state_root = self.root / "host-state"
        self.product_id = "wish-run-1"
        self.wish_bytes = canonical_wish(
            self.product_id, "Make a clockwork moon."
        )

    def create(self, *, max_rounds=4, **kwargs):
        return AgentRun.create(
            self.run_root,
            host_state_root=self.host_state_root,
            product_id=self.product_id,
            wish_bytes=self.wish_bytes,
            product_run_constitution_source=self.product_run_constitution,
            skill_root=self.skill,
            max_rounds=max_rounds,
            **kwargs,
        )

    def artifact(self, run, stage, name=None, content=None):
        name = name or (stage + ".json")
        content = content or ('{"stage":"%s"}\n' % stage).encode("utf-8")
        relative = "artifacts/%s/%s" % (stage, name)
        path = run.run_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return AgentArtifact(relative, hashlib.sha256(content).hexdigest())

    def write_inventor(self, source_root, inventor_id):
        inventor = source_root / inventor_id
        skill_name = inventor_id + "-inventor"
        skill = inventor / "skills" / skill_name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\n"
            "name: %s\n"
            "description: %s's exact native specialist workflow.\n"
            "---\n"
            "# %s\nApply this Inventor's Taste to bounded delegated work.\n"
            % (skill_name, inventor_id.title(), inventor_id.title()),
            encoding="utf-8",
        )
        fingerprint = fingerprint_extension_skill(
            skill.resolve(), expected_name=skill_name
        )
        (inventor / "inventor.json").write_text(
            json.dumps(
                {
                    "schema_version": 8,
                    "id": inventor_id,
                    "status": "experimental",
                    "source": {"kind": "local"},
                    "extensions": [
                        {
                            "kind": "codex-skill",
                            "name": skill_name,
                            "path": "skills/" + skill_name,
                            "artifact_sha256": fingerprint.artifact_sha256,
                        }
                    ],
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (inventor / "TASTE.md").write_text(
            "---\nname: %s\ndescription: Exact %s products.\n---\n"
            % (inventor_id.title(), inventor_id),
            encoding="utf-8",
        )

    def outcome(self, run, stage, transition, *, name=None, content=None):
        return AgentOutcome(
            stage=stage,
            status="ready",
            artifacts=(self.artifact(run, stage, name=name, content=content),),
            proposed_transition=transition,
        )

    def gate(self, run, outcome, *, passed=True, subject=None):
        return DeterministicGateReceipt(
            stage=outcome.stage,
            gate_id=outcome.stage + "-deterministic-gate",
            passed=passed,
            subject_sha256=subject or run.expected_gate_subject_sha256(),
            outcome_sha256=outcome.sha256,
            evidence_sha256=EVIDENCE_SHA256,
        )

    def advance(self, run, stage, transition, *, name=None, content=None, passed=True):
        outcome = self.outcome(
            run, stage, transition, name=name, content=content
        )
        return run.apply_outcome(outcome, gate=self.gate(run, outcome, passed=passed))

    def reach_playtest(self, run):
        for stage, transition in (
            ("wish", "match"),
            ("match", "invent"),
            ("invent", "make"),
            ("make", "playtest"),
        ):
            self.advance(run, stage, transition)

    def test_create_materializes_exact_private_immutable_inputs(self):
        run = self.create()
        checkpoint = run.snapshot()

        self.assertEqual(checkpoint.stage, "wish")
        self.assertEqual(checkpoint.status, "active")
        self.assertEqual(checkpoint.product_id, self.product_id)
        self.assertEqual(
            checkpoint.wish_sha256,
            hashlib.sha256(self.wish_bytes).hexdigest(),
        )
        expected = {
            ".workshop-product-run-root": b"autonomous-workshop-product-run\n",
            "WISH.json": self.wish_bytes,
            "AGENTS.md": b"# Product run constitution\n",
            "MANAGER.json": manager_project_bytes(manager_spec("codex")),
            ".agents/skills/autonomous-workshop/SKILL.md": b"# Workshop skill\n",
            ".agents/skills/autonomous-workshop/references/make-playtest.md": (
                b"exact gate guidance\n"
            ),
            ".agents/skills/autonomous-workshop/references/release-terminal-v1.md": (
                b"terminal Release capability\n"
            ),
        }
        self.assertEqual(stat.S_IMODE(run.run_root.stat().st_mode), 0o700)
        self.assertEqual(
            stat.S_IMODE(run.host_state_root.stat().st_mode),
            0o700,
        )
        self.assertEqual(
            stat.S_IMODE((run.host_state_root / "agent-run.json").stat().st_mode),
            0o600,
        )
        self.assertFalse((run.run_root / ".workshop").exists())
        checkpoint_document = json.loads(
            (run.host_state_root / "agent-run.json").read_text(encoding="utf-8")
        )
        self.assertEqual(checkpoint_document["schema_version"], 3)
        self.assertEqual(checkpoint_document["manager_id"], "codex")
        self.assertEqual(checkpoint.manager_id, "codex")
        self.assertEqual(checkpoint.manager_model, "gpt-6-astra")
        self.assertEqual(checkpoint.manager_reasoning_effort, "medium")
        self.assertEqual(checkpoint.inventor_roster, ())
        for relative, content in expected.items():
            path = run.run_root / relative
            self.assertEqual(path.read_bytes(), content)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o400)
            self.assertEqual(
                checkpoint.input_sha256s[relative], hashlib.sha256(content).hexdigest()
            )

    def test_input_file_capacity_accepts_exact_bound_and_refuses_one_more(self):
        probe = self.create()
        initial_count = len(probe.snapshot().input_sha256s)
        for index in range(agent_run_module.MAX_AGENT_INPUT_FILES - initial_count):
            (self.skill / "references" / ("extra-%04d.md" % index)).write_bytes(b"guidance\n")
        self.run_root = self.root / "at-bound"
        self.host_state_root = self.root / "at-bound-host"
        run = self.create()
        checkpoint = run.snapshot()
        self.assertEqual(len(checkpoint.input_sha256s), 512)
        self.assertEqual(AgentRun.open(
            run.run_root, host_state_root=run.host_state_root,
            expected_checkpoint_sha256=checkpoint.checkpoint_sha256,
        ).snapshot(), checkpoint)
        (self.skill / "references" / "one-too-many.md").write_bytes(b"guidance\n")
        self.run_root = self.root / "over-bound"
        self.host_state_root = self.root / "over-bound-host"
        with self.assertRaisesRegex(ArtifactError, "too many input files"):
            self.create()
        self.assertFalse(self.run_root.exists())
        self.assertFalse(self.host_state_root.exists())

    def test_larger_file_capacity_preserves_total_input_byte_limit(self):
        half = b"guide\n" * (agent_run_module.MAX_AGENT_INPUT_BYTES // 12 + 1)
        for name in ("first.md", "second.md"):
            (self.skill / "references" / name).write_bytes(half)
        with self.assertRaisesRegex(ArtifactError, "total byte limit"):
            self.create()
        self.assertFalse(self.run_root.exists())
        self.assertFalse(self.host_state_root.exists())

    def test_create_materializes_wish_references_read_only_with_their_own_budget(self):
        big = b"\x89PNG" + b"\0" * (5 * 1024 * 1024)
        small = b"\xff\xd8\xff" + b"\0" * 64
        references = (
            reference_fixture(1, "side", big),
            reference_fixture(2, "front", small, "image/jpeg"),
        )
        wish_bytes = canonical_wish(self.product_id, "A photographed toy.", references)
        files = {"ref-01-side.png": big, "ref-02-front.jpg": small}

        run = AgentRun.create(
            self.run_root,
            host_state_root=self.host_state_root,
            product_id=self.product_id,
            wish_bytes=wish_bytes,
            wish_reference_files=files,
            product_run_constitution_source=self.product_run_constitution,
            skill_root=self.skill,
        )
        checkpoint = run.snapshot()

        references_root = run.run_root / "wish-references"
        self.assertEqual(stat.S_IMODE(references_root.stat().st_mode), 0o500)
        for name, content in files.items():
            path = references_root / name
            self.assertEqual(path.read_bytes(), content)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o400)
            self.assertEqual(
                checkpoint.input_sha256s["wish-references/%s" % name],
                hashlib.sha256(content).hexdigest(),
            )
        # 5 MiB of image rides above the 4 MiB constitution-and-skill budget.
        self.assertGreater(len(big), agent_run_module.MAX_AGENT_INPUT_BYTES)
        reopened = AgentRun.open(
            run.run_root,
            host_state_root=run.host_state_root,
            expected_checkpoint_sha256=checkpoint.checkpoint_sha256,
        )
        self.assertEqual(reopened.snapshot(), checkpoint)

    def test_wish_reference_files_must_match_the_wish_exactly(self):
        content = b"\x89PNG" + b"\0" * 32
        references = (reference_fixture(1, "side", content),)
        wish_bytes = canonical_wish(self.product_id, "A photographed toy.", references)
        cases = (
            (None, "must match the references"),
            ({}, "must match the references"),
            ({"ref-01-side.png": content, "ref-02-front.png": content}, "must match"),
            ({"ref-01-side.png": content + b"x"}, "differ from the Wish"),
            ({"ref-01-side.png": "text"}, "differ from the Wish"),
            ("ref-01-side.png", "map reference names to bytes"),
        )
        for files, message in cases:
            with self.subTest(files=type(files).__name__), self.assertRaisesRegex(
                ContractError, message
            ):
                AgentRun.create(
                    self.run_root,
                    host_state_root=self.host_state_root,
                    product_id=self.product_id,
                    wish_bytes=wish_bytes,
                    wish_reference_files=files,
                    product_run_constitution_source=self.product_run_constitution,
                    skill_root=self.skill,
                )
            self.assertFalse(self.run_root.exists())
        with self.assertRaisesRegex(ContractError, "must match the references"):
            AgentRun.create(
                self.run_root,
                host_state_root=self.host_state_root,
                product_id=self.product_id,
                wish_bytes=canonical_wish(self.product_id, "No pictures."),
                wish_reference_files={"ref-01-side.png": content},
                product_run_constitution_source=self.product_run_constitution,
                skill_root=self.skill,
            )

    def test_wish_reference_tampering_and_removal_are_detected(self):
        content = b"\x89PNG" + b"\0" * 32
        references = (reference_fixture(1, "side", content),)
        run = AgentRun.create(
            self.run_root,
            host_state_root=self.host_state_root,
            product_id=self.product_id,
            wish_bytes=canonical_wish(self.product_id, "A photographed toy.", references),
            wish_reference_files={"ref-01-side.png": content},
            product_run_constitution_source=self.product_run_constitution,
            skill_root=self.skill,
        )
        path = run.run_root / "wish-references" / "ref-01-side.png"
        os.chmod(path.parent, 0o700)
        os.chmod(path, 0o600)
        path.write_bytes(content[:-1] + b"\x01")
        os.chmod(path, 0o400)
        with self.assertRaisesRegex(StateConflict, "immutable input bytes changed"):
            run.snapshot()
        path.unlink()
        with self.assertRaisesRegex(ArtifactError, "cannot be opened"):
            run.snapshot()

    def test_create_freezes_the_selected_manager(self):
        run = self.create(manager_id="grok")
        checkpoint = run.snapshot()
        self.assertEqual(checkpoint.manager_id, "grok")
        payload = json.loads(
            (run.run_root / "MANAGER.json").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["manager_id"], "grok")
        self.assertEqual(payload["agent_directory"], ".grok/agents")
        self.assertEqual(checkpoint.manager_model, "grok-4.6")
        self.assertIsNone(checkpoint.manager_reasoning_effort)

    def test_create_freezes_selected_model_and_reasoning_effort(self):
        run = self.create(
            manager_id="codex",
            manager_model="astra",
            manager_reasoning_effort="high",
        )
        checkpoint = run.snapshot()
        self.assertEqual(checkpoint.manager_model, "gpt-6-astra")
        self.assertEqual(checkpoint.manager_reasoning_effort, "high")
        payload = json.loads(
            (run.run_root / "MANAGER.json").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(payload["model"], "gpt-6-astra")
        self.assertEqual(payload["reasoning_effort"], "high")

    def test_create_rejects_an_unknown_manager(self):
        with self.assertRaises(ContractError):
            self.create(manager_id="not-a-runtime")

    def test_reopen_after_create(self):
        run = self.create()
        checkpoint = run.snapshot()
        reopened = AgentRun.open(
            run.run_root,
            host_state_root=run.host_state_root,
            expected_checkpoint_sha256=checkpoint.checkpoint_sha256,
        )
        self.assertEqual(reopened.snapshot(), checkpoint)

    def test_refresh_domain_skill_tools_rebinds_manifest_and_records(self):
        cad = self.root / "cad-skill"
        (cad / "scripts").mkdir(parents=True)
        (cad / "SKILL.md").write_bytes(b"# CAD skill\n")
        checker = cad / "scripts" / "check_fit"
        checker.write_bytes(b"#!/bin/sh\nexit 1\n")
        checker.chmod(0o755)
        obsolete = cad / "scripts" / "obsolete.py"
        obsolete.write_bytes(b"print('old')\n")
        run = self.create(domain_skill_roots={"cad": cad})
        before = run.snapshot()

        # A source that already matches the run changes nothing.
        self.assertEqual(run.refresh_domain_skill_tools({"cad": cad}, reason="same"), ())
        self.assertEqual(run.snapshot(), before)
        self.assertFalse((run.host_state_root / "host-corrections.jsonl").exists())

        # The host corrects the tool, adds a helper, and retires a file. A
        # skill the run never carried is not introduced.
        checker.write_bytes(b"#!/bin/sh\nexit 0\n")
        (cad / "scripts" / "helper.py").write_bytes(b"print('new')\n")
        obsolete.unlink()
        changes = run.refresh_domain_skill_tools(
            {"cad": cad, "absent": cad}, reason="corrected checker"
        )
        self.assertEqual(
            {item["path"] for item in changes},
            {
                ".agents/skills/cad/scripts/check_fit",
                ".agents/skills/cad/scripts/helper.py",
                ".agents/skills/cad/scripts/obsolete.py",
            },
        )
        by_path = {item["path"]: item for item in changes}
        corrected = hashlib.sha256(b"#!/bin/sh\nexit 0\n").hexdigest()
        self.assertEqual(by_path[".agents/skills/cad/scripts/check_fit"]["sha256"], corrected)
        self.assertEqual(by_path[".agents/skills/cad/scripts/check_fit"]["mode"], 0o500)
        self.assertIsNone(by_path[".agents/skills/cad/scripts/obsolete.py"]["sha256"])
        self.assertIsNone(by_path[".agents/skills/cad/scripts/helper.py"]["previous_sha256"])

        after = run.snapshot()
        self.assertEqual(after.revision, before.revision + 1)
        self.assertNotEqual(after.checkpoint_sha256, before.checkpoint_sha256)
        self.assertEqual(after.stage, before.stage)
        self.assertEqual(after.round_index, before.round_index)
        self.assertEqual(after.input_sha256s[".agents/skills/cad/scripts/check_fit"], corrected)
        self.assertIn(".agents/skills/cad/scripts/helper.py", after.input_sha256s)
        self.assertNotIn(".agents/skills/cad/scripts/obsolete.py", after.input_sha256s)
        self.assertEqual(after.input_sha256s["WISH.json"], before.input_sha256s["WISH.json"])

        target = run.run_root / ".agents/skills/cad/scripts/check_fit"
        self.assertEqual(target.read_bytes(), b"#!/bin/sh\nexit 0\n")
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o500)
        helper = run.run_root / ".agents/skills/cad/scripts/helper.py"
        self.assertEqual(stat.S_IMODE(helper.stat().st_mode), 0o400)
        self.assertFalse((run.run_root / ".agents/skills/cad/scripts/obsolete.py").exists())
        for directory in (".agents", ".agents/skills", ".agents/skills/cad/scripts"):
            self.assertEqual(
                stat.S_IMODE((run.run_root / directory).stat().st_mode), 0o500, directory
            )
        self.assertFalse((run.run_root / ".agents/skills/absent").exists())

        ledger = run.host_state_root / "host-corrections.jsonl"
        self.assertEqual(stat.S_IMODE(ledger.stat().st_mode), 0o600)
        lines = ledger.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["correction"], "domain-skill-refresh")
        self.assertEqual(record["reason"], "corrected checker")
        self.assertEqual(record["previous_checkpoint_sha256"], before.checkpoint_sha256)
        self.assertEqual(record["checkpoint_sha256"], after.checkpoint_sha256)
        self.assertEqual(len(record["changes"]), 3)

        reopened = AgentRun.open(
            run.run_root,
            host_state_root=run.host_state_root,
            expected_checkpoint_sha256=after.checkpoint_sha256,
        )
        self.assertEqual(reopened.snapshot(), after)

        # The refreshed bytes are bound: a later edit is still tampering.
        os.chmod(run.run_root / ".agents/skills/cad/scripts", 0o700)
        os.chmod(target, 0o700)
        target.write_bytes(b"#!/bin/sh\nexit 2\n")
        os.chmod(target, 0o500)
        with self.assertRaises(StateConflict):
            reopened.snapshot()

        with self.assertRaises(ContractError):
            run.refresh_domain_skill_tools({"cad": cad}, reason="")

    def test_token_review_refresh_is_allowlisted_and_preserves_workflow(self):
        marker = self.skill / "references/token-budget-v1.md"
        marker.write_bytes(b"old token rules\n")
        run = self.create()
        before = run.snapshot()
        marker.write_bytes(b"token-only rules\n")
        (self.skill / "SKILL.md").write_bytes(b"unrelated instruction change\n")
        changes = run.refresh_domain_skill_tools(
            {}, reason="remove review spending cap", token_budget_skill_root=self.skill
        )
        self.assertEqual([c["path"] for c in changes],
                         [".agents/skills/autonomous-workshop/references/token-budget-v1.md"])
        after = run.snapshot()
        self.assertEqual(after.product_id, before.product_id)
        self.assertEqual(after.stage, before.stage)
        self.assertEqual(after.input_sha256s[".agents/skills/autonomous-workshop/SKILL.md"],
                         before.input_sha256s[".agents/skills/autonomous-workshop/SKILL.md"])

    def test_create_materializes_custom_agent_roster_and_executable_skills(self):
        cad = self.root / "cad-skill"
        (cad / "scripts").mkdir(parents=True)
        (cad / "SKILL.md").write_bytes(b"# CAD skill\n")
        checker = cad / "scripts" / "check_fit"
        checker.write_bytes(b"#!/bin/sh\nexit 0\n")
        checker.chmod(0o755)

        inventor_source = self.root / "inventors"
        alice = inventor_source / "alice"
        alice.mkdir(parents=True)
        inventor_skill = alice / "skills" / "alice-inventor"
        (inventor_skill / "scripts").mkdir(parents=True)
        (inventor_skill / "SKILL.md").write_text(
            "---\n"
            "name: alice-inventor\n"
            "description: Alice's exact native specialist workflow.\n"
            "---\n"
            "# Alice\nApply Alice's Taste to bounded delegated work.\n",
            encoding="utf-8",
        )
        custom_tool = inventor_skill / "scripts" / "custom_tool"
        custom_tool.write_bytes(b"#!/bin/sh\nexit 0\n")
        custom_tool.chmod(0o755)
        fingerprint = fingerprint_extension_skill(
            inventor_skill.resolve(), expected_name="alice-inventor"
        )
        (alice / "inventor.json").write_text(
            json.dumps(
                {
                    "schema_version": 8,
                    "id": "alice",
                    "status": "experimental",
                    "source": {"kind": "local"},
                    "extensions": [
                        {
                            "kind": "codex-skill",
                            "name": "alice-inventor",
                            "path": "skills/alice-inventor",
                            "artifact_sha256": fingerprint.artifact_sha256,
                        }
                    ],
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (alice / "TASTE.md").write_text(
            "---\nname: Alice\ndescription: Exact classics.\n---\n",
            encoding="utf-8",
        )

        run = self.create(
            domain_skill_roots={"cad": cad},
            inventor_source_root=inventor_source,
        )
        checkpoint = run.snapshot()
        expected_modes = {
            ".codex/agents/alice.toml": 0o400,
            ".agents/skills/cad/SKILL.md": 0o400,
            ".agents/skills/cad/scripts/check_fit": 0o500,
            ".agents/skills/alice-inventor/SKILL.md": 0o400,
            ".agents/skills/alice-inventor/scripts/custom_tool": 0o500,
        }
        for relative, mode in expected_modes.items():
            path = run.run_root / relative
            self.assertIn(relative, checkpoint.input_sha256s)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), mode)
        self.assertFalse((run.run_root / "catalog").exists())
        self.assertEqual(
            stat.S_IMODE((run.run_root / ".codex").stat().st_mode),
            0o500,
        )
        self.assertEqual(
            stat.S_IMODE((run.run_root / ".codex" / "agents").stat().st_mode),
            0o500,
        )
        agent_file = run.run_root / ".codex" / "agents" / "alice.toml"
        agent = tomllib.loads(agent_file.read_text(encoding="utf-8"))
        self.assertEqual(
            set(agent), {"name", "description", "developer_instructions"}
        )
        self.assertEqual(agent["name"], "alice")
        instructions = agent["developer_instructions"]
        self.assertIn("AUTONOMOUS_WORKSHOP_EXACT_MANIFEST", instructions)
        self.assertIn("AUTONOMOUS_WORKSHOP_EXACT_TASTE", instructions)
        self.assertIn("AUTONOMOUS_WORKSHOP_EXACT_SKILLS", instructions)
        self.assertIn("Exact classics.", instructions)
        self.assertNotIn("catalog/inventors", instructions)
        self.assertIn(".agents/skills/alice-inventor/SKILL.md", instructions)
        self.assertIn("bounded", instructions)
        self.assertIn("Workshop Manager", instructions)
        self.assertIn("Do not advance", instructions)
        self.assertIn("Do not perform external effects", instructions)
        binding = parse_inventor_custom_agent_bytes(agent_file.read_bytes())
        self.assertEqual(binding.inventor_id, "alice")
        self.assertEqual(binding.skills[0].name, "alice-inventor")
        self.assertEqual(binding.skills[0].artifact_sha256, fingerprint.artifact_sha256)
        self.assertEqual(len(checkpoint.inventor_roster), 1)
        self.assertEqual(dict(checkpoint.inventor_roster[0]), binding.to_host_dict())
        checkpoint_document = json.loads(
            (run.host_state_root / "agent-run.json").read_text(encoding="utf-8")
        )
        self.assertEqual(checkpoint_document["schema_version"], 3)
        self.assertEqual(
            checkpoint_document["inventor_roster"], [binding.to_host_dict()]
        )

        agent_file.chmod(0o600)
        with self.assertRaisesRegex(StateConflict, "immutable input mode"):
            run.snapshot()
        agent_file.chmod(0o400)
        run.snapshot()

        run_checker = run.run_root / ".agents/skills/cad/scripts/check_fit"
        run_checker.chmod(0o400)
        with self.assertRaisesRegex(StateConflict, "immutable input mode"):
            run.snapshot()

    def test_creation_rejects_legacy_schema_seven_inventor_source(self):
        inventor_source = self.root / "inventors"
        alice = inventor_source / "alice"
        alice.mkdir(parents=True)
        (alice / "inventor.json").write_text(
            json.dumps(
                {
                    "schema_version": 7,
                    "id": "alice",
                    "status": "experimental",
                    "source": {"kind": "local"},
                    "extensions": [],
                }
            ),
            encoding="utf-8",
        )
        (alice / "TASTE.md").write_text("# Alice\n", encoding="utf-8")

        with self.assertRaisesRegex(ArtifactError, "schema_version 8"):
            self.create(inventor_source_root=inventor_source)
        self.assertFalse(self.run_root.exists())

    def test_creation_can_pin_the_exact_materialized_inventor(self):
        inventor_source = self.root / "inventors"
        self.write_inventor(inventor_source, "alice")
        self.write_inventor(inventor_source, "bob")

        run = self.create(
            inventor_source_root=inventor_source,
            required_inventor_id="bob",
        )
        checkpoint = run.snapshot()

        self.assertEqual(
            [item["inventor_id"] for item in checkpoint.inventor_roster],
            ["bob"],
        )
        self.assertTrue((run.run_root / ".codex/agents/bob.toml").is_file())
        self.assertTrue(
            (run.run_root / ".agents/skills/bob-inventor/SKILL.md").is_file()
        )
        self.assertFalse((run.run_root / ".codex/agents/alice.toml").exists())
        self.assertFalse((run.run_root / ".agents/skills/alice-inventor").exists())

    def test_creation_rejects_an_unavailable_required_inventor(self):
        inventor_source = self.root / "inventors"
        self.write_inventor(inventor_source, "alice")

        with self.assertRaisesRegex(
            ArtifactError, "required Inventor is unavailable: bob"
        ):
            self.create(
                inventor_source_root=inventor_source,
                required_inventor_id="bob",
            )
        self.assertFalse(self.run_root.exists())

    def test_creation_rejects_an_unsafe_required_inventor_id(self):
        inventor_source = self.root / "inventors"
        self.write_inventor(inventor_source, "alice")

        with self.assertRaisesRegex(ContractError, "lowercase hyphenated"):
            self.create(
                inventor_source_root=inventor_source,
                required_inventor_id="../alice",
            )
        self.assertFalse(self.run_root.exists())

    def test_creation_requires_explicit_product_run_constitution_source(self):
        repository_agents = self.root / "AGENTS.md"
        repository_agents.write_bytes(b"# Builder-only repository guidance\n")

        with self.assertRaisesRegex(ContractError, "product-run constitution"):
            AgentRun.create(
                self.run_root,
                host_state_root=self.host_state_root,
                product_id="wish-run-wrong-constitution",
                wish_bytes=canonical_wish(
                    "wish-run-wrong-constitution", "Exact Wish"
                ),
                product_run_constitution_source=repository_agents,
                skill_root=self.skill,
            )
        self.assertFalse(self.run_root.exists())

    def test_creation_requires_canonical_wish_bound_to_product_id(self):
        pretty = json.dumps(
            json.loads(canonical_wish("canonical-wish", "Exact Wish")),
            indent=2,
        ).encode("utf-8")
        with self.assertRaisesRegex(ContractError, "canonical encoding"):
            AgentRun.create(
                self.run_root,
                host_state_root=self.host_state_root,
                product_id="canonical-wish",
                wish_bytes=pretty,
                product_run_constitution_source=self.product_run_constitution,
                skill_root=self.skill,
            )
        with self.assertRaisesRegex(ContractError, "product_id does not match"):
            AgentRun.create(
                self.run_root,
                host_state_root=self.host_state_root,
                product_id="expected-product",
                wish_bytes=canonical_wish("other-product", "Exact Wish"),
                product_run_constitution_source=self.product_run_constitution,
                skill_root=self.skill,
            )
        with self.assertRaisesRegex(ArtifactError, "credential"):
            AgentRun.create(
                self.run_root,
                host_state_root=self.host_state_root,
                product_id="private-wish",
                wish_bytes=canonical_wish(
                    "private-wish", "Use api_key=definitely-not-agent-data"
                ),
                product_run_constitution_source=self.product_run_constitution,
                skill_root=self.skill,
            )
        self.assertFalse(self.run_root.exists())
        self.assertFalse(self.host_state_root.exists())

    def test_creation_rejects_existing_root_and_symlinked_skill_input(self):
        self.run_root.mkdir()
        with self.assertRaises(StateConflict):
            self.create()

        other_run = self.root / "other-run"
        target = self.root / "outside.md"
        target.write_text("outside", encoding="utf-8")
        (self.skill / "linked.md").symlink_to(target)
        with self.assertRaisesRegex(ArtifactError, "regular file|symlink"):
            AgentRun.create(
                other_run,
                host_state_root=self.root / "other-host-state",
                product_id="wish-run-2",
                wish_bytes=canonical_wish("wish-run-2", "Exact Wish"),
                product_run_constitution_source=self.product_run_constitution,
                skill_root=self.skill,
            )
        self.assertFalse(other_run.exists())

    def test_host_state_is_external_and_bound_against_copy_or_wrong_roots(self):
        with self.assertRaisesRegex(ContractError, "must not overlap"):
            AgentRun.create(
                self.run_root,
                host_state_root=self.root,
                product_id="overlapping-roots",
                wish_bytes=canonical_wish("overlapping-roots", "Exact Wish"),
                product_run_constitution_source=self.product_run_constitution,
                skill_root=self.skill,
            )
        self.assertFalse(self.run_root.exists())

        run = self.create()
        copied_run = self.root / "copied-run"
        copied_host = self.root / "copied-host-state"
        shutil.copytree(run.run_root, copied_run)
        shutil.copytree(run.host_state_root, copied_host)

        with self.assertRaisesRegex(StateConflict, "another root"):
            AgentRun.open(copied_run, host_state_root=run.host_state_root)
        with self.assertRaisesRegex(StateConflict, "another host-state root"):
            AgentRun.open(run.run_root, host_state_root=copied_host)

        host_alias = self.root / "host-state-alias"
        host_alias.symlink_to(run.host_state_root, target_is_directory=True)
        with self.assertRaisesRegex(ContractError, "real directories"):
            AgentRun.open(run.run_root, host_state_root=host_alias)

    def test_only_exact_host_gate_receipt_advances_the_lifecycle(self):
        run = self.create()
        outcome = self.outcome(run, "wish", "match")
        with self.assertRaisesRegex(TransitionError, "host deterministic gate"):
            run.apply_outcome(outcome)
        self.assertEqual(run.snapshot().stage, "wish")

        wrong_subject = self.gate(run, outcome, subject="a" * 64)
        with self.assertRaisesRegex(TransitionError, "not bound"):
            run.apply_outcome(outcome, gate=wrong_subject)
        self.assertEqual(run.snapshot().stage, "wish")

        checkpoint = run.apply_outcome(outcome, gate=self.gate(run, outcome))
        self.assertEqual(checkpoint.stage, "match")
        self.assertIn("wish", checkpoint.stage_artifacts)

        forged = outcome.to_dict()
        forged["self_score"] = 100
        with self.assertRaisesRegex(ContractError, "fields"):
            AgentOutcome.from_mapping(forged)

    def test_predecessor_gate_must_match_the_accepted_checkpoint_history(self):
        run = self.create()
        for stage, transition in (
            ("wish", "match"),
            ("match", "invent"),
            ("invent", "make"),
        ):
            self.advance(run, stage, transition)
        before_make = run.snapshot()
        outcome = self.outcome(run, "make", "playtest")
        gate = self.gate(run, outcome)
        run.apply_outcome(outcome, gate=gate)

        run.assert_predecessor_gate_accepted(
            gate,
            gate_checkpoint_sha256=before_make.checkpoint_sha256,
        )

        forged = DeterministicGateReceipt(
            stage=gate.stage,
            gate_id=gate.gate_id,
            passed=gate.passed,
            subject_sha256=gate.subject_sha256,
            outcome_sha256=gate.outcome_sha256,
            evidence_sha256="f" * 64,
        )
        with self.assertRaisesRegex(StateConflict, "accepted predecessor"):
            run.assert_predecessor_gate_accepted(
                forged,
                gate_checkpoint_sha256=before_make.checkpoint_sha256,
            )

    def test_host_gate_can_bind_full_subject_and_seal_a_verified_tree(self):
        run = self.create()
        outcome = self.outcome(run, "wish", "match")
        tree_file = self.artifact(
            run,
            "wish",
            name="product/notes.txt",
            content=b"exact gated bytes\n",
        )
        full_subject = "f" * 64
        gate = self.gate(run, outcome, subject=full_subject)

        checkpoint = run.apply_outcome(
            outcome,
            gate=gate,
            gate_subject_sha256=full_subject,
            additional_artifacts=(tree_file,),
        )

        self.assertEqual(
            [item.path for item in checkpoint.stage_artifacts["wish"]],
            [outcome.artifacts[0].path, tree_file.path],
        )
        (run.run_root / tree_file.path).write_bytes(b"changed\n")
        with self.assertRaisesRegex(StateConflict, "sealed agent artifact changed"):
            run.snapshot()

    def test_additional_gate_artifacts_are_bounded_and_stage_scoped(self):
        run = self.create()
        outcome = self.outcome(run, "wish", "match")
        wrong_stage = self.artifact(run, "match", name="wrong.txt")
        gate = self.gate(run, outcome)
        with self.assertRaisesRegex(ArtifactError, "must live under artifacts/wish"):
            run.apply_outcome(
                outcome,
                gate=gate,
                additional_artifacts=(wrong_stage,),
            )

        duplicate = outcome.artifacts[0]
        with self.assertRaisesRegex(ArtifactError, "paths must be unique"):
            run.apply_outcome(
                outcome,
                gate=gate,
                additional_artifacts=(duplicate,),
            )

    def test_complete_lifecycle_uses_one_bounded_host_checkpoint(self):
        run = self.create()
        for stage, transition in (
            ("wish", "match"),
            ("match", "invent"),
            ("invent", "make"),
            ("make", "playtest"),
            ("playtest", "release"),
            ("release", "complete"),
        ):
            checkpoint = self.advance(run, stage, transition)

        self.assertTrue(checkpoint.complete)
        self.assertEqual(checkpoint.stage, "release")
        self.assertEqual(checkpoint.round_index, 1)
        self.assertEqual(set(checkpoint.stage_artifacts), set(
            ("wish", "match", "invent", "make", "playtest", "release")
        ))
        with self.assertRaises(TransitionError):
            run.apply_outcome(
                AgentOutcome(
                    stage="release",
                    status="failed",
                    needs=("already complete",),
                )
            )

    def test_direct_release_marker_skips_playtest_without_fabricating_a_gate(self):
        marker = self.skill / "references" / "direct-release-v1.md"
        marker.write_bytes(b"direct Release capability\n")
        run = self.create()

        for stage, transition in (
            ("wish", "match"),
            ("match", "invent"),
            ("invent", "make"),
            ("make", "release"),
            ("release", "complete"),
        ):
            checkpoint = self.advance(run, stage, transition)

        self.assertTrue(checkpoint.complete)
        self.assertEqual(checkpoint.stage, "release")
        self.assertNotIn("playtest", checkpoint.stage_artifacts)
        self.assertEqual(
            set(checkpoint.stage_artifacts),
            {"wish", "match", "invent", "make", "release"},
        )

    def test_effort_routes_pass_through_optional_stages_without_artifacts(self):
        marker = self.skill / "references" / "effort-routes-v1.md"
        marker.write_bytes(b"selectable effort routes\n")
        routes = {
            "spark": (("wish", "make"), ("make", "release"), ("release", "complete")),
            "forge": (
                ("wish", "invent"),
                ("invent", "make"),
                ("make", "release"),
                ("release", "complete"),
            ),
            "quest": (
                ("wish", "invent"),
                ("invent", "make"),
                ("make", "playtest"),
                ("playtest", "release"),
                ("release", "complete"),
            ),
        }
        for effort, transitions in routes.items():
            with self.subTest(effort=effort):
                run_root = self.root / effort
                host_root = self.root / (effort + "-host")
                run = AgentRun.create(
                    run_root,
                    host_state_root=host_root,
                    product_id=self.product_id + "-" + effort,
                    wish_bytes=canonical_wish(
                        self.product_id + "-" + effort,
                        "Make a clockwork moon.",
                    ),
                    product_run_constitution_source=self.product_run_constitution,
                    skill_root=self.skill,
                    effort=effort,
                )
                checkpoint = run.snapshot()
                self.assertEqual(checkpoint.effort, effort)
                for stage, transition in transitions:
                    outcome = self.outcome(run, stage, transition)
                    checkpoint = run.apply_outcome(
                        outcome, gate=self.gate(run, outcome)
                    )
                self.assertTrue(checkpoint.complete)
                self.assertEqual(
                    set(checkpoint.stage_artifacts),
                    {stage for stage, unused in transitions},
                )

    def test_capable_forge_make_can_return_to_invent_with_failed_gate(self):
        references = self.skill / "references"
        (references / "effort-routes-v1.md").write_bytes(
            b"selectable effort routes\n"
        )
        (references / "make-invent-revision-v1.md").write_bytes(
            b"evidence-bound Make to Invent revision\n"
        )
        run = self.create(max_rounds=3, effort="forge")
        self.advance(run, "wish", "invent")
        self.advance(run, "invent", "make")
        prior_invent = run.snapshot().stage_artifacts["invent"]

        revision = self.outcome(
            run,
            "make",
            "invent",
            name="r0001/invent-revision-request.json",
            content=b'{"result":"sealed-concept-unbuildable"}\n',
        )
        checkpoint = run.apply_outcome(
            revision,
            gate=self.gate(run, revision, passed=False),
        )

        self.assertEqual((checkpoint.stage, checkpoint.round_index), ("invent", 2))
        self.assertEqual(checkpoint.stage_artifacts["invent"], prior_invent)
        self.assertEqual(checkpoint.stage_artifacts["make"], revision.artifacts)
        self.assertEqual(
            checkpoint.invalidated_stages,
            ("invent", "make", "playtest", "release"),
        )

        revised_invent = self.outcome(
            run,
            "invent",
            "make",
            name="r0002/invented.json",
            content=b'{"concept":"revised"}\n',
        )
        checkpoint = run.apply_outcome(
            revised_invent,
            gate=self.gate(run, revised_invent),
        )
        self.assertEqual((checkpoint.stage, checkpoint.round_index), ("make", 2))
        self.assertNotIn("make", checkpoint.stage_artifacts)
        self.assertEqual(
            checkpoint.invalidated_stages,
            ("make", "playtest", "release"),
        )

    def test_make_to_invent_requires_frozen_capability_and_invent_stage(self):
        references = self.skill / "references"
        (references / "effort-routes-v1.md").write_bytes(
            b"selectable effort routes\n"
        )
        old_forge = self.create(effort="forge")
        self.advance(old_forge, "wish", "invent")
        self.advance(old_forge, "invent", "make")
        proposal = self.outcome(old_forge, "make", "invent")
        with self.assertRaisesRegex(TransitionError, "frozen capable"):
            old_forge.apply_outcome(
                proposal, gate=self.gate(old_forge, proposal, passed=False)
            )

        (references / "make-invent-revision-v1.md").write_bytes(
            b"evidence-bound Make to Invent revision\n"
        )
        spark = AgentRun.create(
            self.root / "spark-run",
            host_state_root=self.root / "spark-host",
            product_id="spark-no-invent",
            wish_bytes=canonical_wish("spark-no-invent", "Make a quick toy."),
            product_run_constitution_source=self.product_run_constitution,
            skill_root=self.skill,
            effort="spark",
        )
        self.advance(spark, "wish", "make")
        spark_proposal = self.outcome(spark, "make", "invent")
        with self.assertRaisesRegex(TransitionError, "frozen capable"):
            spark.apply_outcome(
                spark_proposal,
                gate=self.gate(spark, spark_proposal, passed=False),
            )

    def test_make_to_invent_cannot_exceed_shared_round_budget(self):
        references = self.skill / "references"
        (references / "effort-routes-v1.md").write_bytes(
            b"selectable effort routes\n"
        )
        (references / "make-invent-revision-v1.md").write_bytes(
            b"evidence-bound Make to Invent revision\n"
        )
        run = self.create(max_rounds=1, effort="forge")
        self.advance(run, "wish", "invent")
        self.advance(run, "invent", "make")
        proposal = self.outcome(run, "make", "invent")
        with self.assertRaisesRegex(TransitionError, "budget"):
            run.apply_outcome(
                proposal, gate=self.gate(run, proposal, passed=False)
            )
        self.assertEqual((run.snapshot().stage, run.snapshot().round_index), ("make", 1))

    def test_new_run_cannot_propose_the_obsolete_deliver_transition(self):
        run = self.create()
        for stage, transition in (
            ("wish", "match"),
            ("match", "invent"),
            ("invent", "make"),
            ("make", "playtest"),
            ("playtest", "release"),
        ):
            self.advance(run, stage, transition)

        outcome = self.outcome(run, "release", "deliver")
        with self.assertRaisesRegex(TransitionError, "complete the Workshop"):
            run.apply_outcome(outcome, gate=self.gate(run, outcome))
        self.assertEqual(run.snapshot().stage, "release")

    def test_token_budget_revisions_survive_legacy_round_and_history_caps(self):
        references = self.skill / "references"
        (references / "token-budget-v1.md").write_bytes(b"token allowance\n")
        (references / "effort-routes-v1.md").write_bytes(b"routes\n")
        (references / "make-invent-revision-v1.md").write_bytes(b"revisions\n")
        run = self.create(max_rounds=1, effort="forge")
        self.advance(run, "wish", "invent")
        self.advance(run, "invent", "make")
        for _ in range(10):
            proposal = self.outcome(run, "make", "invent")
            run.apply_outcome(proposal, gate=self.gate(run, proposal, passed=False))
            self.advance(run, "invent", "make")
        checkpoint = run.snapshot()
        self.assertEqual(checkpoint.round_index, 11)
        self.assertEqual(checkpoint.max_rounds, 1)
        self.assertEqual(checkpoint.stage, "make")

    def test_token_run_host_growth_has_no_aggregate_artifact_or_checkpoint_cap(self):
        references = self.skill / "references"
        (references / "token-budget-v1.md").write_bytes(b"token allowance\n")
        (references / "effort-routes-v1.md").write_bytes(b"routes\n")
        run = self.create(effort="spark")
        self.advance(run, "wish", "make")
        outcome = self.outcome(run, "make", "release")
        parts = tuple(
            self.artifact(run, "make", name="part-%04d.txt" % index, content=b"safe\n")
            for index in range(513)
        )
        with patch.object(agent_run_module, "MAX_AGENT_REFERENCED_BYTES", 10), patch.object(
            agent_run_module, "MAX_AGENT_CHECKPOINT_BYTES", 1024
        ):
            checkpoint = run.apply_outcome(
                outcome, gate=self.gate(run, outcome), additional_artifacts=parts
            )
            self.assertEqual(checkpoint.stage, "release")
            reopened = AgentRun.open(run.run_root, host_state_root=run.host_state_root)
            self.assertEqual(reopened.snapshot().checkpoint_sha256, checkpoint.checkpoint_sha256)
            self.assertGreater((run.host_state_root / "agent-run.json").stat().st_size, 1024)
            (run.run_root / parts[0].path).write_bytes(b"changed\n")
            with self.assertRaisesRegex(StateConflict, "sealed agent artifact changed"):
                reopened.snapshot()

    def test_non_token_run_keeps_legacy_host_growth_caps(self):
        run = self.create()
        outcome = self.outcome(run, "wish", "match")
        extra = self.artifact(run, "wish", name="extra.txt", content=b"safe\n")
        gate = self.gate(run, outcome)
        with patch.object(agent_run_module, "MAX_HOST_SEALED_ARTIFACTS_PER_GATE", 0):
            with self.assertRaisesRegex(ArtifactError, "too many artifacts"):
                run.apply_outcome(outcome, gate=gate, additional_artifacts=(extra,))
        with patch.object(agent_run_module, "MAX_AGENT_REFERENCED_BYTES", 1):
            with self.assertRaisesRegex(ArtifactError, "total limit"):
                run.apply_outcome(outcome, gate=gate)
        with patch.object(agent_run_module, "MAX_AGENT_CHECKPOINT_BYTES", 1):
            with self.assertRaisesRegex(StateConflict, "byte limit"):
                run.snapshot()

    def test_token_run_keeps_per_file_and_credential_safety_checks(self):
        (self.skill / "references" / "token-budget-v1.md").write_bytes(b"token allowance\n")
        run = self.create()
        outcome = self.outcome(run, "wish", "match", content=b"regular artifact\n")
        gate = self.gate(run, outcome)
        with patch.object(agent_run_module, "MAX_AGENT_ARTIFACT_BYTES", 1):
            with self.assertRaisesRegex(ArtifactError, "byte limit"):
                run.apply_outcome(outcome, gate=gate)
        secret = self.outcome(run, "wish", "match", content=b"FACTORY_PASSWORD=must-not-seal\n")
        with self.assertRaisesRegex(ArtifactError, "credential"):
            run.apply_outcome(secret, gate=self.gate(run, secret))

    def test_adopted_token_budget_uses_verified_host_authority_without_new_inputs(self):
        from workshop.workflow import native_run as host
        from workshop.workflow.budgets import LifetimeBudget
        from tests.workflow.test_token_budget import observation

        references = self.skill / "references"
        (references / "lifetime-budgets-v1.md").write_bytes(b"legacy lifetime budget\n")
        (references / "effort-routes-v1.md").write_bytes(b"routes\n")
        (references / "make-invent-revision-v1.md").write_bytes(b"revisions\n")
        run = self.create(max_rounds=1, effort="forge")
        self.advance(run, "wish", "invent")
        self.advance(run, "invent", "make")
        checkpoint = run.snapshot()
        inputs_before = dict(checkpoint.input_sha256s)
        paths = host.NativeRunPaths(workspace=run.run_root, host_state=run.host_state_root)
        previous = LifetimeBudget()
        host._save_lifetime_budget(paths, checkpoint, previous)
        with patch.object(host, "_read_product_token_usage", return_value=observation(100)):
            host._adopt_token_budget(paths, checkpoint, 1_000_000)
        adopted = host._open_budgeted_agent_run(paths)
        self.assertTrue(adopted.snapshot().token_budgeted)
        self.assertNotIn(host.TOKEN_BUDGET_CAPABILITY_PATH, adopted.snapshot().input_sha256s)
        with patch.object(agent_run_module, "MAX_AGENT_CHECKPOINT_BYTES", 1024), patch.object(
            agent_run_module, "MAX_AGENT_REFERENCED_BYTES", 1
        ), patch.object(agent_run_module, "MAX_HOST_SEALED_ARTIFACTS_PER_GATE", 0):
            for index in range(10):
                proposal = self.outcome(adopted, "make", "invent")
                extra = self.artifact(adopted, "make", name="adopted-%d.txt" % index)
                adopted.apply_outcome(proposal, gate=self.gate(adopted, proposal, passed=False), additional_artifacts=(extra,))
                self.advance(adopted, "invent", "make")
            adopted = host._open_budgeted_agent_run(paths)
            self.assertEqual(adopted.snapshot().round_index, 11)
        self.assertEqual(dict(adopted.snapshot().input_sha256s), inputs_before)
        budget = host._load_lifetime_budget(paths, adopted.snapshot())
        self.assertEqual(budget.previous_budget, previous.to_dict())
        self.assertEqual(budget.to_dict()["used_tokens"], 110)
        ledger = paths.host_state / "native-budget.json"
        encoded = ledger.read_bytes()
        invalid = json.loads(encoded)
        invalid["wish_sha256"] = "f" * 64
        ledger.write_text(json.dumps(invalid))
        with self.assertRaisesRegex(StateConflict, "binding"):
            host._open_budgeted_agent_run(paths)
        ledger.write_bytes(encoded)
        ledger.unlink()
        with self.assertRaisesRegex(StateConflict, "unavailable"):
            host._open_budgeted_agent_run(paths)

    def test_an_unselected_boundary_is_absent_from_the_checkpoint(self):
        run = self.create()
        checkpoint = run.snapshot()
        self.assertIsNone(checkpoint.turn_seconds)
        self.assertFalse(checkpoint.turn_untimed)
        payload = json.loads(
            (run.host_state_root / "agent-run.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("turn_seconds", payload)

    def test_a_selected_boundary_survives_reopen(self):
        run = self.create(turn_seconds=3 * 60 * 60)
        checkpoint = run.snapshot()
        self.assertEqual(checkpoint.turn_seconds, 3 * 60 * 60)
        self.assertFalse(checkpoint.turn_untimed)
        reopened = AgentRun.open(
            run.run_root,
            host_state_root=run.host_state_root,
            expected_checkpoint_sha256=checkpoint.checkpoint_sha256,
        )
        self.assertEqual(reopened.snapshot(), checkpoint)

    def test_an_untimed_selection_is_distinct_from_no_selection(self):
        run = self.create(turn_untimed=True)
        checkpoint = run.snapshot()
        self.assertTrue(checkpoint.turn_untimed)
        self.assertIsNone(checkpoint.turn_seconds)
        payload = json.loads(
            (run.host_state_root / "agent-run.json").read_text(encoding="utf-8")
        )
        self.assertIn("turn_seconds", payload)
        self.assertIsNone(payload["turn_seconds"])

    def test_an_invalid_boundary_is_refused_before_any_run_exists(self):
        for kwargs in (
            {"turn_seconds": 59},
            {"turn_seconds": agent_run_module.MAX_NATIVE_TURN_SECONDS + 1},
            {"turn_seconds": 60.0},
            {"turn_seconds": True},
            {"turn_untimed": "yes"},
            {"turn_seconds": 600, "turn_untimed": True},
        ):
            with self.subTest(**kwargs), self.assertRaises(ContractError):
                self.create(**kwargs)
            self.assertFalse(self.run_root.exists())

    def test_a_tampered_boundary_is_refused_on_reopen(self):
        run = self.create(turn_seconds=7_200)
        checkpoint_path = run.host_state_root / "agent-run.json"
        payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        payload.pop("checkpoint_sha256")
        payload["turn_seconds"] = agent_run_module.MAX_NATIVE_TURN_SECONDS + 1
        agent_run_module.AgentRun._write_checkpoint_file(checkpoint_path, payload)
        with self.assertRaisesRegex(StateConflict, "native turn boundary is invalid"):
            AgentRun.open(run.run_root, host_state_root=run.host_state_root)

    def test_rebinding_replaces_the_boundary_and_keeps_the_lifecycle(self):
        run = self.create(turn_seconds=1_800)
        before = run.snapshot()
        after = run.rebind_turn_boundary(turn_untimed=True)
        self.assertTrue(after.turn_untimed)
        self.assertIsNone(after.turn_seconds)
        self.assertEqual(after.revision, before.revision + 1)
        self.assertEqual(after.stage, before.stage)
        self.assertEqual(after.status, before.status)
        self.assertEqual(after.max_rounds, before.max_rounds)
        self.assertEqual(after.round_index, before.round_index)
        exact = run.rebind_turn_boundary(turn_seconds=5_400)
        self.assertEqual(exact.turn_seconds, 5_400)
        self.assertFalse(exact.turn_untimed)

    def test_rebinding_to_the_same_boundary_writes_no_revision(self):
        run = self.create(turn_seconds=1_800)
        before = run.snapshot()
        self.assertEqual(
            run.rebind_turn_boundary(turn_seconds=1_800).revision, before.revision
        )

    def test_rebinding_refuses_an_invalid_boundary(self):
        run = self.create()
        for kwargs in (
            {"turn_seconds": 59},
            {"turn_seconds": agent_run_module.MAX_NATIVE_TURN_SECONDS + 1},
            {"turn_seconds": 600, "turn_untimed": True},
            {"turn_untimed": "yes"},
        ):
            with self.subTest(**kwargs), self.assertRaises(ContractError):
                run.rebind_turn_boundary(**kwargs)
        self.assertIsNone(run.snapshot().turn_seconds)

    def test_effort_checkpoint_rejects_a_disabled_active_stage(self):
        marker = self.skill / "references" / "effort-routes-v1.md"
        marker.write_bytes(b"selectable effort routes\n")
        run = AgentRun.create(
            self.run_root,
            host_state_root=self.host_state_root,
            product_id=self.product_id,
            wish_bytes=self.wish_bytes,
            product_run_constitution_source=self.product_run_constitution,
            skill_root=self.skill,
            effort="spark",
        )
        checkpoint_path = run.host_state_root / "agent-run.json"
        value = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        value.pop("checkpoint_sha256")
        value["stage"] = "invent"
        agent_run_module.AgentRun._write_checkpoint_file(checkpoint_path, value)

        with self.assertRaisesRegex(StateConflict, "disabled by its frozen effort"):
            AgentRun.open(run.run_root, host_state_root=run.host_state_root)

    def test_wait_is_resumable_but_failure_is_terminal_and_neither_advances(self):
        waiting_run = self.create()
        waiting = AgentOutcome(
            stage="wish",
            status="waiting",
            needs=("customer-choice-required",),
        )
        checkpoint = waiting_run.apply_outcome(waiting)
        self.assertEqual((checkpoint.stage, checkpoint.status), ("wish", "waiting"))
        self.assertEqual(checkpoint.needs, ("customer-choice-required",))
        resumed = waiting_run.resume()
        self.assertEqual(resumed.status, "active")
        self.assertEqual(resumed.needs, ())
        self.advance(waiting_run, "wish", "match")

        failed_run = AgentRun.create(
            self.root / "failed-run",
            host_state_root=self.root / "failed-host-state",
            product_id="wish-run-failed",
            wish_bytes=canonical_wish("wish-run-failed", "Another Wish"),
            product_run_constitution_source=self.product_run_constitution,
            skill_root=self.skill,
        )
        failed = AgentOutcome(
            stage="wish", status="failed", needs=("contract-invalid",)
        )
        checkpoint = failed_run.apply_outcome(failed)
        self.assertEqual((checkpoint.stage, checkpoint.status), ("wish", "failed"))
        self.assertEqual(checkpoint.needs, ("contract-invalid",))
        with self.assertRaises(TransitionError):
            failed_run.resume()
        with self.assertRaises(TransitionError):
            failed_run.apply_outcome(self.outcome(failed_run, "wish", "match"))

    def test_invent_only_advances_to_make_and_upstream_is_match(self):
        run = self.create()
        for stage, transition in (
            ("wish", "match"),
            ("match", "invent"),
        ):
            self.advance(run, stage, transition)
        self.assertEqual(run.snapshot().stage, "invent")
        outcome = self.outcome(run, "invent", "playtest")
        with self.assertRaisesRegex(TransitionError, "illegal lifecycle transition"):
            run.apply_outcome(outcome, gate=self.gate(run, outcome))
        self.assertEqual(run.snapshot().stage, "invent")
        checkpoint = self.advance(run, "invent", "make")
        self.assertEqual(checkpoint.stage, "make")

    def test_invent_proposal_bound_to_a_stale_checkpoint_or_subject_is_refused(self):
        run = self.create()
        for stage, transition in (
            ("wish", "match"),
            ("match", "invent"),
        ):
            self.advance(run, stage, transition)
        outcome = self.outcome(run, "invent", "make")
        wrong_subject = self.gate(run, outcome, subject="a" * 64)
        with self.assertRaisesRegex(TransitionError, "not bound"):
            run.apply_outcome(outcome, gate=wrong_subject)
        self.assertEqual(run.snapshot().stage, "invent")

    def test_failed_playtest_returns_to_new_make_and_consumes_round(self):
        run = self.create(max_rounds=2)
        self.reach_playtest(run)
        first_make = run.snapshot().stage_artifacts["make"][0]

        failed_playtest = self.outcome(run, "playtest", "make")
        checkpoint = run.apply_outcome(
            failed_playtest, gate=self.gate(run, failed_playtest, passed=False)
        )
        self.assertEqual((checkpoint.stage, checkpoint.round_index), ("make", 2))
        self.assertEqual(
            checkpoint.invalidated_stages,
            ("playtest", "release"),
        )
        self.assertEqual(
            checkpoint.stage_artifacts["playtest"][0], failed_playtest.artifacts[0]
        )

        support = self.artifact(
            run,
            "make",
            name="round-02-support.json",
            content=b'{"revision":2}\n',
        )
        second_make = AgentOutcome(
            stage="make",
            status="ready",
            artifacts=(first_make, support),
            proposed_transition="playtest",
        )
        checkpoint = run.apply_outcome(second_make, gate=self.gate(run, second_make))
        self.assertEqual(checkpoint.stage_artifacts["make"][0], first_make)
        self.assertEqual(len(checkpoint.stage_artifacts["make"]), 2)
        self.assertEqual(
            checkpoint.invalidated_stages,
            ("playtest", "release"),
        )
        second_failure = self.outcome(
            run,
            "playtest",
            "make",
            name="round-02.json",
            content=b'{"result":"improve"}\n',
        )
        with self.assertRaisesRegex(TransitionError, "budget"):
            run.apply_outcome(
                second_failure, gate=self.gate(run, second_failure, passed=False)
            )
        self.assertEqual(run.snapshot().stage, "playtest")

    def test_concept_feedback_returns_to_invent_and_consumes_shared_round(self):
        run = self.create(max_rounds=3)
        self.reach_playtest(run)
        before = run.snapshot()
        prior_invent = before.stage_artifacts["invent"]
        prior_make = before.stage_artifacts["make"]

        failed_playtest = self.outcome(
            run,
            "playtest",
            "invent",
            name="concept-failure.json",
            content=b'{"result":"revise-concept"}\n',
        )
        checkpoint = run.apply_outcome(
            failed_playtest,
            gate=self.gate(run, failed_playtest, passed=False),
        )

        self.assertEqual((checkpoint.stage, checkpoint.round_index), ("invent", 2))
        self.assertEqual(
            checkpoint.invalidated_stages,
            ("invent", "make", "playtest", "release"),
        )
        self.assertEqual(checkpoint.stage_artifacts["invent"], prior_invent)
        self.assertEqual(checkpoint.stage_artifacts["make"], prior_make)
        self.assertEqual(
            checkpoint.stage_artifacts["playtest"][0],
            failed_playtest.artifacts[0],
        )

        revised_invent = self.outcome(
            run,
            "invent",
            "make",
            name="revision-02.json",
            content=b'{"concept":"revised"}\n',
        )
        checkpoint = run.apply_outcome(
            revised_invent,
            gate=self.gate(run, revised_invent),
        )

        self.assertEqual((checkpoint.stage, checkpoint.round_index), ("make", 2))
        self.assertEqual(
            checkpoint.stage_artifacts["invent"],
            revised_invent.artifacts,
        )
        self.assertNotIn("make", checkpoint.stage_artifacts)
        self.assertNotIn("playtest", checkpoint.stage_artifacts)
        self.assertEqual(
            checkpoint.invalidated_stages,
            ("make", "playtest", "release"),
        )

    def test_concept_revision_cannot_exceed_shared_round_budget(self):
        run = self.create(max_rounds=1)
        self.reach_playtest(run)
        failed_playtest = self.outcome(run, "playtest", "invent")

        with self.assertRaisesRegex(TransitionError, "budget"):
            run.apply_outcome(
                failed_playtest,
                gate=self.gate(run, failed_playtest, passed=False),
            )
        self.assertEqual(run.snapshot().stage, "playtest")

    def test_host_gate_can_seal_a_product_file_larger_than_16_mib(self):
        run = self.create()
        for stage, transition in (
            ("wish", "match"),
            ("match", "invent"),
            ("invent", "make"),
        ):
            self.advance(run, stage, transition)

        outcome = self.outcome(run, "make", "playtest")
        relative = "artifacts/make/r0001/product/renders/large.png"
        large = run.run_root / relative
        large.parent.mkdir(parents=True, exist_ok=True)
        with large.open("wb") as stream:
            stream.seek(17 * 1024 * 1024 - 1)
            stream.write(b"\0")
        artifact = AgentArtifact(relative, hashlib.sha256(large.read_bytes()).hexdigest())

        checkpoint = run.apply_outcome(
            outcome,
            gate=self.gate(run, outcome),
            additional_artifacts=(artifact,),
        )

        self.assertEqual(checkpoint.stage, "playtest")
        self.assertIn(relative, {item.path for item in checkpoint.stage_artifacts["make"]})

    def test_four_round_cad_history_can_exceed_64_mib_but_not_128_mib(self):
        run = self.create(max_rounds=4)
        mib = 1024 * 1024
        former_limit = 64 * mib
        cumulative_limit = 128 * mib
        simulated_sizes = {}
        read_artifact = agent_run_module._read_relative_regular

        def read_with_simulated_size(root, relative):
            content, actual_size = read_artifact(root, relative)
            return content, simulated_sizes.get(relative.as_posix(), actual_size)

        def sized_outcome(stage, transition, name, size):
            artifact = self.artifact(
                run,
                stage,
                name=name,
                content=(name + "\n").encode("utf-8"),
            )
            simulated_sizes[artifact.path] = size
            return AgentOutcome(
                stage=stage,
                status="ready",
                artifacts=(artifact,),
                proposed_transition=transition,
            )

        def apply_sized(stage, transition, name, size, *, passed=True):
            outcome = sized_outcome(stage, transition, name, size)
            return run.apply_outcome(
                outcome,
                gate=self.gate(run, outcome, passed=passed),
            )

        def sealed_bytes():
            document = json.loads(
                (run.host_state_root / "agent-run.json").read_text(encoding="utf-8")
            )
            return sum(item["size"] for item in document["sealed_artifacts"])

        # Keep the fixture disk-small while exercising the real cumulative budget;
        # every simulated artifact remains within the real 95 MiB per-file limit.
        with patch.object(
            agent_run_module,
            "_read_relative_regular",
            side_effect=read_with_simulated_size,
        ):
            for stage, transition in (
                ("wish", "match"),
                ("match", "invent"),
                ("invent", "make"),
            ):
                self.advance(run, stage, transition)

            for round_index in range(1, 5):
                apply_sized(
                    "make",
                    "playtest",
                    "round-%02d-model.step" % round_index,
                    9 * mib,
                )
                final_round = round_index == 4
                checkpoint = apply_sized(
                    "playtest",
                    "release" if final_round else "make",
                    "round-%02d-evidence.json" % round_index,
                    9 * mib,
                    passed=final_round,
                )

            four_round_total = sealed_bytes()
            self.assertEqual(
                (checkpoint.stage, checkpoint.round_index), ("release", 4)
            )
            self.assertGreater(four_round_total, former_limit)
            self.assertLess(four_round_total, cumulative_limit)

            remaining = cumulative_limit - four_round_total
            release_artifacts = []
            while remaining:
                size = min(16 * mib, remaining)
                name = "package-part-%02d.dat" % (len(release_artifacts) + 1)
                artifact = self.artifact(
                    run,
                    "release",
                    name=name,
                    content=(name + "\n").encode("utf-8"),
                )
                simulated_sizes[artifact.path] = size
                release_artifacts.append(artifact)
                remaining -= size

            release = AgentOutcome(
                stage="release",
                status="ready",
                artifacts=tuple(release_artifacts),
                proposed_transition="complete",
            )
            checkpoint = run.apply_outcome(release, gate=self.gate(run, release))
            self.assertEqual(checkpoint.stage, "release")
            self.assertTrue(checkpoint.complete)
            self.assertEqual(sealed_bytes(), cumulative_limit)
            self.assertLessEqual(max(simulated_sizes.values()), 16 * mib)

    def test_passing_playtest_cannot_return_to_make_and_failure_cannot_advance(self):
        run = self.create()
        self.reach_playtest(run)
        revise = self.outcome(run, "playtest", "make")
        with self.assertRaisesRegex(TransitionError, "passing Playtest"):
            run.apply_outcome(revise, gate=self.gate(run, revise, passed=True))

        advance = self.outcome(
            run,
            "playtest",
            "release",
            name="passing.json",
            content=b'{"passed":true}\n',
        )
        with self.assertRaisesRegex(TransitionError, "failed deterministic gate"):
            run.apply_outcome(advance, gate=self.gate(run, advance, passed=False))
        self.assertEqual(run.snapshot().stage, "playtest")

    def test_artifact_paths_hashes_links_credentials_and_effect_receipts_fail_closed(self):
        run = self.create()
        content = b'{"ok":true}\n'
        valid = self.artifact(run, "wish", content=content)
        with self.assertRaises(ContractError):
            AgentArtifact("artifacts/wish/../escape.json", valid.sha256)
        with self.assertRaisesRegex(ArtifactError, "hash"):
            run.validate_outcome(
                AgentOutcome(
                    stage="wish",
                    status="ready",
                    artifacts=(AgentArtifact(valid.path, "a" * 64),),
                    proposed_transition="match",
                )
            )

        linked = run.run_root / "artifacts" / "wish" / "linked.json"
        linked.symlink_to(run.run_root / "AGENTS.md")
        with self.assertRaises(ArtifactError):
            run.validate_outcome(
                AgentOutcome(
                    stage="wish",
                    status="ready",
                    artifacts=(
                        AgentArtifact(
                            "artifacts/wish/linked.json",
                            hashlib.sha256(b"# Product run constitution\n").hexdigest(),
                        ),
                    ),
                    proposed_transition="match",
                )
            )

        credential = b'api_key="definitely-not-agent-data"\n'
        with self.assertRaisesRegex(ArtifactError, "credential"):
            run.validate_outcome(
                self.outcome(
                    run,
                    "wish",
                    "match",
                    name="credential.txt",
                    content=credential,
                )
            )
        with self.assertRaisesRegex(ArtifactError, "effect receipts"):
            run.validate_outcome(
                self.outcome(
                    run,
                    "wish",
                    "match",
                    name="factory-receipt.json",
                )
            )

    def test_input_checkpoint_and_sealed_artifact_tampering_is_detected(self):
        run = self.create()
        self.advance(run, "wish", "match")
        artifact = run.snapshot().stage_artifacts["wish"][0]
        artifact_path = run.run_root / artifact.path
        artifact_path.write_bytes(b"changed\n")
        with self.assertRaisesRegex(StateConflict, "sealed agent artifact"):
            run.snapshot()

        input_run = AgentRun.create(
            self.root / "input-run",
            host_state_root=self.root / "input-host-state",
            product_id="input-run",
            wish_bytes=canonical_wish("input-run", "Immutable Wish"),
            product_run_constitution_source=self.product_run_constitution,
            skill_root=self.skill,
        )
        wish = input_run.run_root / "WISH.json"
        os.chmod(wish, 0o600)
        wish.write_bytes(b"Changed Wish")
        with self.assertRaisesRegex(StateConflict, "immutable input"):
            input_run.snapshot()

        checkpoint_run = AgentRun.create(
            self.root / "checkpoint-run",
            host_state_root=self.root / "checkpoint-host-state",
            product_id="checkpoint-run",
            wish_bytes=canonical_wish("checkpoint-run", "Checkpoint Wish"),
            product_run_constitution_source=self.product_run_constitution,
            skill_root=self.skill,
        )
        checkpoint_path = checkpoint_run.host_state_root / "agent-run.json"
        value = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        value["stage"] = "deliver"
        checkpoint_path.write_text(json.dumps(value), encoding="utf-8")
        os.chmod(checkpoint_path, 0o600)
        with self.assertRaisesRegex(StateConflict, "digest"):
            checkpoint_run.snapshot()

    def test_stale_host_and_oversized_or_private_outcome_are_rejected(self):
        run = self.create()
        stale = AgentRun.open(
            run.run_root,
            host_state_root=run.host_state_root,
            expected_checkpoint_sha256=run.snapshot().checkpoint_sha256,
        )
        self.advance(run, "wish", "match")
        with self.assertRaisesRegex(StateConflict, "changed since"):
            stale.snapshot()

        with self.assertRaises(ContractError):
            AgentOutcome(
                stage="match",
                status="waiting",
                needs=("x" * 1_025,),
            )
        with self.assertRaisesRegex(ArtifactError, "credential"):
            AgentOutcome(
                stage="match",
                status="waiting",
                needs=("password=not-allowed-in-agent-output",),
            )


if __name__ == "__main__":
    unittest.main()