import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from workshop.workflow.native_run import (
    native_run_paths,
    resume_native_run,
    start_native_run,
)
from workshop.errors import ArtifactError
from workshop.invent.native import InventedV2
from workshop.make.native import NativeMade
from workshop.match.native import NativeMatchAssignment
from workshop.playtest.native import NativePlaytested
from workshop.release.native import NativeRelease
from workshop.runtime import Receipt
from workshop.wish import Wish
from workshop.workflow import AgentRun


_OBSERVED_AT = "2026-08-26T00:00:00+00:00"
_PAGE_URL = "https://www.autonomous.ai/factory/product/orbit-dog"
_COVER_URL = "https://cdn.autonomous.ai/products/orbit-dog/cover.webp"
_SESSION_CHECKPOINT = b'{"session_id":"fixture-native-session"}\n'


def _canonical_json(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_json(value))


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(content):
    return hashlib.sha256(content).hexdigest()


class _SessionOutcome:
    def __init__(self, arguments):
        self.arguments = dict(arguments)

    def to_dict(self):
        return {
            "status": "completed",
            "session": {
                "product_id": self.arguments["product_id"],
                "wish_sha256": self.arguments["wish_sha256"],
                "constitution_sha256": self.arguments["constitution_sha256"],
                "checkpoint_sha256": "c" * 64,
            },
            "used_web_search": False,
        }


class _OneSessionProductAgent:
    """A deterministic stand-in for one resumed native Codex session."""

    def __init__(self):
        self.starts = []
        self.resumes = []
        self.stage_packets = []
        self.finalizer_commands = []

    @staticmethod
    def _checkpoint(arguments):
        path = Path(arguments["host_state_root"]) / "codex-session.json"
        path.write_bytes(_SESSION_CHECKPOINT)
        os.chmod(path, 0o600)

    @staticmethod
    def _assert_public_arguments(arguments):
        rendered = repr(arguments)
        if "FACTORY" in rendered or "fixture-host-secret" in rendered:
            raise AssertionError("host effect authority reached the native launcher")

    def _run_finalizer(self, run_root, *arguments):
        script = (
            run_root
            / ".agents"
            / "skills"
            / "autonomous-workshop"
            / "scripts"
            / "stage_proposal.py"
        )
        command = (
            sys.executable,
            str(script),
            "--run-root",
            str(run_root),
            *arguments,
        )
        self.finalizer_commands.append(command)
        completed = subprocess.run(
            command,
            cwd=str(run_root),
            env={"PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1"},
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(
                "stage proposal failed (%s): %s"
                % (completed.returncode, completed.stderr)
            )
        result = json.loads(completed.stdout)
        if result["outcome_path"] != "agent-outcome.json":
            raise AssertionError("finalizer did not author the compact proposal")

    def _author_match(self, run_root, stage):
        personas = stage["inputs"]["persona_catalog"]["personas"]
        ids = [entry["inventor_id"] for entry in personas]
        if ids != sorted(ids) or "alice" not in ids:
            raise AssertionError("fixture received a non-canonical persona catalog")
        ranking = [
            {
                "inventor_id": inventor_id,
                "rationale": (
                    "Alice best preserves known draughts rules while making the "
                    "physical set structurally specific to the Wish."
                    if inventor_id == "alice"
                    else "%s is a valid specialist, but another lane fits less directly."
                    % inventor_id.title()
                ),
            }
            for inventor_id in (["alice"] + [item for item in ids if item != "alice"])
        ]
        source = "authored/match.json"
        _write_json(
            run_root / source,
            {"selected_inventor_id": "alice", "ranking": ranking},
        )
        self._run_finalizer(run_root, "match", "--source", source)

    def _author_invent(self, run_root, stage):
        assignment = stage["inputs"]["assignment"]
        if assignment["selected_inventor_id"] != "alice":
            raise AssertionError("Invent did not receive the accepted Match assignment")
        source = "authored/invent.json"
        _write_json(
            run_root / source,
            {
                "concept": {
                    "title": "Orbit Dog Draughts",
                    "summary": (
                        "A pocket draughts set whose concentric board, opposing orbit "
                        "packs, and king pieces turn the requested dog into the geometry "
                        "of a familiar public-domain game."
                    ),
                    "signature_decision": (
                        "Every playable square is an orbital waypoint and each side uses "
                        "a distinct dog-pack silhouette without changing draughts rules."
                    ),
                },
                "research": {
                    "rules_basis": "English draughts movement remains unchanged.",
                    "sources": [
                        {
                            "title": "English draughts rules reference",
                            "url": "https://www.fmjd.org/",
                            "use": "Known-rule baseline only",
                        }
                    ],
                    "safety_boundary": "Ages 14+; small parts are explicitly identified.",
                },
            },
        )
        self._run_finalizer(run_root, "invent", "--source", source)

    def _author_make(self, run_root, stage):
        inputs = stage["inputs"]
        product_root_value = inputs["product_root"]
        product_root = run_root / product_root_value
        (product_root / "cad" / "project").mkdir(parents=True)
        (product_root / "validation").mkdir()
        wish = _read_json(run_root / "WISH.json")
        product = {
            "schema_version": 1,
            "product_id": stage["product_id"],
            "slug": stage["product_id"],
            "title": "Orbit Dog Draughts",
            "summary": (
                "A compact, printable draughts set with orbital waypoints and two "
                "tactile dog-pack piece families."
            ),
            "description": (
                "A Wish-specific public-domain classic with unchanged play. Invented by Alice"
            ),
            "lane": "classics-made-yours",
            "wish": wish,
            "inventor": {"id": "alice", "name": "Alice"},
            "components": ["folding orbital board", "24 pack pieces", "storage sleeve"],
            "instructions": (
                "Set up and play English draughts normally; the orbital graphic changes "
                "the object, never the rules."
            ),
            "limitations": [
                "Digitally verified prototype; no claim of physical manufacture or delivery."
            ],
        }
        _write_json(product_root / "product.json", product)
        _write_json(
            product_root / "project.json",
            {"id": stage["product_id"], "name": product["title"]},
        )
        (product_root / "wish.json").write_bytes((run_root / "WISH.json").read_bytes())
        (product_root / "assembled.step").write_bytes(
            b"ISO-10303-21;\nHEADER;ENDSEC;\nDATA;ENDSEC;\nEND-ISO-10303-21;\n"
        )
        (product_root / "assembled.stl").write_bytes(
            b"solid orbit_dog\nendsolid orbit_dog\n"
        )
        (product_root / "cad" / "project" / "build.py").write_text(
            "def build():\n    return 'orbit-dog-draughts'\n",
            encoding="utf-8",
        )
        _write_json(
            product_root / "validation" / "cad-verification.json",
            {
                "schema_version": 1,
                "validator": "materialized-cad-final",
                "validator_version": "1.0.0",
                "passed": True,
                "checks": ["fresh-export", "strict-fit", "printable-mesh"],
            },
        )
        for required in inputs["required_root_files"]:
            if not (product_root / required).is_file():
                raise AssertionError("Make omitted a host-required root file")
        self._run_finalizer(
            run_root,
            "make",
            "--product-root",
            product_root_value,
            "--cad-project-path",
            "cad/project",
            "--cad-verification-path",
            "validation/cad-verification.json",
        )

    def _author_playtest(self, run_root, stage):
        inputs = stage["inputs"]
        evidence_root_value = inputs["evidence_root"]
        evidence_root = run_root / evidence_root_value
        checks = []
        for check_id in inputs["required_check_ids"]:
            config_ref = "configs/%s.json" % check_id
            evidence_ref = "results/%s.json" % check_id
            _write_json(
                evidence_root / config_ref,
                {
                    "schema_version": 1,
                    "check_id": check_id,
                    "seed": 17,
                    "artifact_sha256": inputs["made"]["product_manifest"][
                        "artifact_sha256"
                    ],
                },
            )
            _write_json(
                evidence_root / evidence_ref,
                {
                    "schema_version": 1,
                    "check_id": check_id,
                    "passed": True,
                    "finding": "The exact sealed revision passed %s." % check_id,
                },
            )
            checks.append(
                {
                    "check_id": check_id,
                    "passed": True,
                    "evaluator": "independent-fixture-judge",
                    "evaluator_version": "1.0.0",
                    "config_ref": config_ref,
                    "evidence_ref": evidence_ref,
                    "observed_at": _OBSERVED_AT,
                    "observations": {
                        "evidence_class": "deterministic-digital-check",
                        "claims": ["The sealed revision passed %s." % check_id],
                        "artifact_bound": True,
                    },
                }
            )
        source = "authored/playtest.json"
        _write_json(
            run_root / source,
            {"checks": checks, "feedback": [], "verdict": "pass"},
        )
        self._run_finalizer(
            run_root,
            "playtest",
            "--source",
            source,
            "--evidence-root",
            evidence_root_value,
        )

    def _author_release(self, run_root, stage):
        inputs = stage["inputs"]
        made = inputs["made"]
        playtested = inputs["playtested"]
        if playtested.get("kind") != "autonomous-workshop.playtested":
            raise AssertionError("Release did not receive the full Playtest contract")
        binding = inputs["playtested_artifact"]
        if binding["playtested_sha256"] != playtested["playtested_sha256"]:
            raise AssertionError("Release Playtest contract and artifact binding differ")
        claims = {}
        for check in playtested["checks"]:
            observations = check["observations"]
            claims[check["check_id"]] = {
                "passed": check["passed"],
                "evidence_class": observations["evidence_class"],
                "claims": observations["claims"],
                "evidence_ref": check["evidence_ref"],
                "evidence_sha256": check["evidence_sha256"],
                "evaluator": check["evaluator"],
                "evaluator_version": check["evaluator_version"],
            }
        package_root_value = inputs["package_root"]
        package_root = run_root / package_root_value
        package_root.mkdir(parents=True, exist_ok=True)
        (package_root / "MANUAL.md").write_text(
            "# Orbit Dog Draughts\n\n"
            "## What arrives\n\nA board, two tactile piece families, and a sleeve.\n\n"
            "## Set up and play\n\nUse standard English draughts setup and rules. "
            "The orbital waypoints are the playable dark squares.\n\n"
            "## Care and safety\n\nFor ages 14+. Keep the small pieces away from "
            "young children.\n",
            encoding="utf-8",
        )
        _write_json(
            package_root / "product.json",
            {
                "schema_version": 2,
                "kind": "workshop.release-package",
                "status": "facts-ready",
                "title": made["product"]["title"],
                "summary": made["product"]["summary"],
                "lane": made["product"]["lane"],
                "wish": _read_json(run_root / "WISH.json")["objective"],
                "product_artifact_sha256": made["product_manifest"][
                    "artifact_sha256"
                ],
                "playtest_evidence_artifact_sha256": playtested[
                    "evidence_manifest"
                ]["artifact_sha256"],
                "claims": claims,
                "factory_enrichment": {
                    "copy_owner": "factory",
                    "media_owner": "factory",
                    "status": "pending",
                },
            },
        )
        self._run_finalizer(
            run_root,
            "release",
            "--package-root",
            package_root_value,
        )

    def _turn(self, arguments):
        self._assert_public_arguments(arguments)
        run_root = Path(arguments["run_root"])
        stage_path = run_root / "STAGE.json"
        if stat.S_IMODE(stage_path.stat().st_mode) & 0o222:
            raise AssertionError("native session received a writable STAGE.json")
        stage = _read_json(stage_path)
        if stage["product_id"] != arguments["product_id"]:
            raise AssertionError("STAGE product identity differs from the session")
        if stage["stage"] not in arguments["prompt"]:
            raise AssertionError("native prompt does not identify the current stage")
        self.stage_packets.append(stage)
        getattr(self, "_author_%s" % stage["stage"])(run_root, stage)
        return _SessionOutcome(arguments)

    def start(self, **arguments):
        self.starts.append(dict(arguments))
        if self.starts or self.resumes:
            if len(self.starts) != 1 or self.resumes:
                raise AssertionError("one product run may start only one native session")
        self._checkpoint(arguments)
        return self._turn(arguments)

    def resume(self, **arguments):
        self.resumes.append(dict(arguments))
        if len(self.starts) != 1:
            raise AssertionError("resume must continue the already-started session")
        checkpoint = Path(arguments["host_state_root"]) / "codex-session.json"
        if checkpoint.read_bytes() != _SESSION_CHECKPOINT:
            raise AssertionError("resume did not use the original native session checkpoint")
        return self._turn(arguments)


class _FactoryEffects:
    def __init__(self):
        self.secret = "fixture-host-secret"
        self.credentials_value = SimpleNamespace(
            username="alice", password=self.secret
        )
        self.credential_requests = []
        self.writer_calls = []
        self.session_calls = []
        self.publish_calls = []
        self.registered_products = []

    def credentials(self, inventor_id):
        self.credential_requests.append(inventor_id)
        return self.credentials_value

    def writer(self, store, inventor_id, credentials):
        self.writer_calls.append((store, inventor_id, credentials))
        products = store.list_products()
        if len(products) != 1 or products[0]["stage"] != "release":
            raise AssertionError(
                "native Release must register its durable product before publishing"
            )
        self.registered_products.append(products[0])
        fixture = self

        def write(context, root, manifest):
            fixture.writer_calls.append((context, root, manifest))
            if not (Path(root) / "MANUAL.md").is_file():
                raise AssertionError("Factory effect did not receive the verified manual")
            return Receipt(
                pack_sha256=_sha256(b"fixture-model-handoff"),
                artifact_sha256=context.made.artifact_sha256,
                design_id="design-orbit-dog",
                slug="orbit-dog",
                owner_id="owner-alice",
                root_id="design-orbit-dog",
                current_history_id="history-orbit-dog-1",
                published_history_id=None,
                status="draft",
                project_url="https://cdn.autonomous.ai/projects/orbit-dog-1/",
                observed_at=_OBSERVED_AT,
                details={
                    "release_sha256": manifest.artifact_sha256,
                    "page_url": _PAGE_URL,
                    "cover_url": _COVER_URL,
                },
            )

        return write

    def session(self, credentials):
        self.session_calls.append(credentials)
        return SimpleNamespace(credentials=credentials)

    def transition(self, session):
        fixture = self

        class PublicTransition:
            def publish(self, draft):
                fixture.publish_calls.append((session, draft))
                return Receipt(
                    pack_sha256=draft.pack_sha256,
                    artifact_sha256=draft.artifact_sha256,
                    design_id=draft.design_id,
                    slug=draft.slug,
                    owner_id=draft.owner_id,
                    root_id=draft.root_id,
                    current_history_id=draft.current_history_id,
                    published_history_id=draft.current_history_id,
                    status="public",
                    project_url=draft.project_url,
                    observed_at=_OBSERVED_AT,
                    details=dict(draft.details),
                    listing_active=True,
                    listing_price_cents=2400,
                    listing_currency="USD",
                    listing_sku="ORBIT-DOG-001",
                )

        return PublicTransition()


class NativeFullRunTest(unittest.TestCase):
    def test_release_credential_wait_is_durable_and_resumes_same_session(self):
        launcher = _OneSessionProductAgent()
        effects = _FactoryEffects()

        def verify_cad(made, **arguments):
            return SimpleNamespace(
                passed=True,
                receipt_sha256=_sha256(made.made_sha256.encode("ascii")),
                verifier_sha256=arguments["expected_verifier_sha256"],
            )

        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            wish = Wish.create(
                "orbit-dog-credential-wait",
                "Build a pocket draughts set inspired by my orbit-loving dog.",
                constraints={"audience": "14+", "manufacture": "not-authorized"},
                context={"source": "native-release-credential-wait-test"},
            )
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "workshop.workflow.native_run.verify_native_made_cad",
                side_effect=verify_cad,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryAgentReleaseWriter",
                side_effect=effects.writer,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryAgentSession",
                side_effect=effects.session,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryPublicTransition",
                side_effect=effects.transition,
            ):
                waiting = start_native_run(wish, publish_requested=True)
                paths = native_run_paths(wish.product_id)
                run = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                )
                waiting_checkpoint = run.snapshot()

                self.assertEqual(waiting["status"], "waiting")
                self.assertEqual(waiting["stage"], "release")
                self.assertEqual(waiting["native_turns"], 5)
                self.assertEqual(waiting["publication"]["status"], "not-created")
                self.assertEqual(len(waiting["needs"]), 1)
                self.assertIn("missing or malformed", waiting["needs"][0])
                self.assertEqual(waiting_checkpoint.status, "waiting")
                self.assertEqual(waiting_checkpoint.stage, "release")
                self.assertFalse((paths.workspace / "agent-outcome.json").exists())
                self.assertFalse((paths.host_state / "release-effect.json").exists())
                wait_path = paths.host_state / "release-effect-wait.json"
                self.assertTrue(wait_path.is_file())
                self.assertEqual(stat.S_IMODE(wait_path.stat().st_mode), 0o600)
                wait_document = _read_json(wait_path)
                self.assertEqual(
                    wait_document["waiting_checkpoint_sha256"],
                    waiting_checkpoint.checkpoint_sha256,
                )
                first_release_packet = launcher.stage_packets[-1]
                self.assertEqual(first_release_packet["stage"], "release")
                first_call_count = len(launcher.starts) + len(launcher.resumes)

                os.environ["FACTORY_PASSWORD"] = effects.secret
                still_waiting = resume_native_run(
                    wish.product_id, publish_requested=True
                )
                self.assertEqual(still_waiting["status"], "waiting")
                self.assertEqual(still_waiting["stage"], "release")
                self.assertEqual(still_waiting["native_turns"], 0)
                self.assertEqual(
                    still_waiting["action"], "waiting-for-factory-credentials"
                )
                self.assertEqual(
                    still_waiting["checkpoint_sha256"],
                    waiting_checkpoint.checkpoint_sha256,
                )
                self.assertEqual(
                    len(launcher.starts) + len(launcher.resumes), first_call_count
                )

                os.environ["FACTORY_USERNAME"] = "alice"
                completed_release = resume_native_run(
                    wish.product_id, publish_requested=True
                )
                final_checkpoint = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                ).snapshot()

            self.assertEqual(completed_release["status"], "waiting")
            self.assertEqual(completed_release["stage"], "deliver")
            self.assertEqual(completed_release["native_turns"], 1)
            self.assertEqual(completed_release["publication"]["status"], "public")
            self.assertTrue(completed_release["publication"]["verified"])
            self.assertEqual(final_checkpoint.stage, "deliver")
            self.assertEqual(final_checkpoint.status, "waiting")
            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(len(launcher.resumes), 5)
            self.assertEqual(
                [packet["stage"] for packet in launcher.stage_packets],
                ["match", "invent", "make", "playtest", "release", "release"],
            )
            second_release_packet = launcher.stage_packets[-1]
            self.assertNotEqual(
                first_release_packet["checkpoint_sha256"],
                second_release_packet["checkpoint_sha256"],
            )
            self.assertEqual(
                first_release_packet["subject_sha256"],
                second_release_packet["subject_sha256"],
            )
            self.assertEqual(len(launcher.finalizer_commands), 6)
            self.assertEqual(len(effects.writer_calls), 2)
            self.assertEqual(len(effects.publish_calls), 1)
            self.assertFalse((paths.host_state / "release-effect-wait.json").exists())
            self.assertTrue((paths.host_state / "release-effect.json").is_file())
            self.assertIn("release", final_checkpoint.stage_artifacts)
            for root in (paths.workspace, paths.host_state):
                for path in root.rglob("*"):
                    if path.is_file():
                        self.assertNotIn(
                            effects.secret.encode("utf-8"), path.read_bytes()
                        )

    def test_one_native_session_runs_every_stage_and_host_seals_the_release(self):
        launcher = _OneSessionProductAgent()
        effects = _FactoryEffects()
        cad_calls = []

        def verify_cad(made, **arguments):
            cad_calls.append((made, dict(arguments)))
            return SimpleNamespace(
                passed=True,
                receipt_sha256=_sha256(
                    (made.made_sha256 + str(len(cad_calls))).encode("ascii")
                ),
                verifier_sha256=arguments["expected_verifier_sha256"],
            )

        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            wish = Wish.create(
                "orbit-dog",
                "Build a pocket draughts set inspired by my orbit-loving dog.",
                constraints={"audience": "14+", "manufacture": "not-authorized"},
                context={"source": "native-full-run-test"},
            )
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "workshop.workflow.native_run.verify_native_made_cad",
                side_effect=verify_cad,
            ), mock.patch(
                "workshop.workflow.native_run._factory_credentials",
                side_effect=effects.credentials,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryAgentReleaseWriter",
                side_effect=effects.writer,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryAgentSession",
                side_effect=effects.session,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryPublicTransition",
                side_effect=effects.transition,
            ):
                receipt = start_native_run(wish, publish_requested=True)
                paths = native_run_paths(wish.product_id)
                run = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                )
                checkpoint = run.snapshot()

            self.assertEqual(receipt["status"], "waiting")
            self.assertEqual(receipt["stage"], "deliver")
            self.assertEqual(receipt["native_turns"], 5)
            self.assertEqual(receipt["publication"]["status"], "public")
            self.assertTrue(receipt["publication"]["verified"])
            self.assertEqual(receipt["publication"]["page_url"], _PAGE_URL)
            self.assertEqual(checkpoint.stage, "deliver")
            self.assertEqual(checkpoint.status, "waiting")

            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(len(launcher.resumes), 4)
            self.assertEqual(
                [packet["stage"] for packet in launcher.stage_packets],
                ["match", "invent", "make", "playtest", "release"],
            )
            self.assertEqual(len(launcher.finalizer_commands), 5)
            self.assertEqual(
                len({packet["checkpoint_sha256"] for packet in launcher.stage_packets}),
                5,
            )
            session_calls = launcher.starts + launcher.resumes
            for field in (
                "product_id",
                "wish_sha256",
                "constitution_sha256",
                "run_root",
                "host_state_root",
            ):
                self.assertEqual(
                    {str(arguments[field]) for arguments in session_calls},
                    {str(session_calls[0][field])},
                )
            for arguments in session_calls:
                self.assertNotIn(effects.secret, repr(arguments))
                self.assertNotIn("FACTORY", repr(arguments))

            release_packet = launcher.stage_packets[-1]
            self.assertEqual(
                release_packet["inputs"]["playtested"]["kind"],
                "autonomous-workshop.playtested",
            )
            self.assertEqual(
                release_packet["inputs"]["playtested_artifact"][
                    "playtested_sha256"
                ],
                release_packet["inputs"]["playtested"]["playtested_sha256"],
            )

            self.assertEqual(len(cad_calls), 2)
            self.assertEqual(cad_calls[0][0].made_sha256, cad_calls[1][0].made_sha256)
            verifier_path = paths.workspace / ".agents/skills/cad/scripts/verify_project"
            verifier_sha256 = _sha256(verifier_path.read_bytes())
            for made, arguments in cad_calls:
                self.assertEqual(arguments["run_root"], paths.workspace)
                self.assertEqual(arguments["host_state_root"], paths.host_state)
                self.assertEqual(
                    arguments["expected_verifier_sha256"], verifier_sha256
                )
                self.assertEqual(made.product["title"], "Orbit Dog Draughts")

            self.assertEqual(effects.credential_requests, ["alice"])
            self.assertEqual(len(effects.writer_calls), 2)
            self.assertIs(effects.writer_calls[0][2], effects.credentials_value)
            self.assertEqual(len(effects.registered_products), 1)
            self.assertEqual(
                effects.registered_products[0]["artifact_sha256"],
                release_packet["inputs"]["made"]["product_manifest"][
                    "artifact_sha256"
                ],
            )
            self.assertEqual(len(effects.session_calls), 1)
            self.assertEqual(len(effects.publish_calls), 1)
            self.assertTrue(effects.publish_calls[0][1].is_verified_draft)

            effect_path = paths.host_state / "release-effect.json"
            self.assertEqual(stat.S_IMODE(effect_path.stat().st_mode), 0o600)
            effect = _read_json(effect_path)
            publication = Receipt.from_dict(effect["receipt"])
            self.assertEqual(effect["publication_status"], "public")
            self.assertTrue(publication.is_verified_public)
            self.assertEqual(publication.details["page_url"], _PAGE_URL)

            expected_paths = {
                "wish": {"artifacts/wish/wish.json"},
                "match": {"artifacts/match/assignment.json"},
                "invent": {"artifacts/invent/invented.json"},
                "make": {
                    "artifacts/make/r0001/made.json",
                    "artifacts/make/r0001/product/product.json",
                    "artifacts/make/r0001/product/project.json",
                    "artifacts/make/r0001/product/assembled.step",
                    "artifacts/make/r0001/product/assembled.stl",
                    "artifacts/make/r0001/product/cad/project/build.py",
                    "artifacts/make/r0001/product/validation/cad-verification.json",
                },
                "playtest": {
                    "artifacts/playtest/r0001/playtested.json",
                    "artifacts/playtest/r0001/evidence/results/agent-playtest.json",
                    "artifacts/playtest/r0001/evidence/results/classic-rules-test.json",
                    "artifacts/playtest/r0001/evidence/results/mechanical-test.json",
                    "artifacts/playtest/r0001/evidence/results/print-test.json",
                },
                "release": {
                    "artifacts/release/release.json",
                    "artifacts/release/package/MANUAL.md",
                    "artifacts/release/package/product.json",
                },
            }
            for stage, required in expected_paths.items():
                sealed = {artifact.path for artifact in checkpoint.stage_artifacts[stage]}
                self.assertTrue(required <= sealed, (stage, required - sealed))
                for artifact in checkpoint.stage_artifacts[stage]:
                    self.assertEqual(
                        _sha256((paths.workspace / artifact.path).read_bytes()),
                        artifact.sha256,
                    )

            assignment = NativeMatchAssignment.from_mapping(
                _read_json(paths.workspace / checkpoint.stage_artifacts["match"][0].path)
            )
            invented = InventedV2.from_mapping(
                _read_json(paths.workspace / checkpoint.stage_artifacts["invent"][0].path)
            )
            made = NativeMade.from_mapping(
                _read_json(paths.workspace / checkpoint.stage_artifacts["make"][0].path)
            )
            playtested = NativePlaytested.from_mapping(
                _read_json(paths.workspace / checkpoint.stage_artifacts["playtest"][0].path)
            )
            release = NativeRelease.from_mapping(
                _read_json(paths.workspace / checkpoint.stage_artifacts["release"][0].path)
            )
            invented.assert_context(assignment)
            made.assert_context(assignment, invented, expected_round=1)
            release.validate_package_tree(paths.workspace, made, playtested)

            tamper_targets = (
                (
                    paths.workspace / "artifacts/make/r0001/product/assembled.stl",
                    lambda: made.validate_product_tree(paths.workspace),
                ),
                (
                    paths.workspace
                    / "artifacts/playtest/r0001/evidence/results/agent-playtest.json",
                    lambda: playtested.validate_evidence_tree(paths.workspace, made),
                ),
                (
                    paths.workspace / "artifacts/release/package/MANUAL.md",
                    lambda: release.validate_package_tree(
                        paths.workspace, made, playtested
                    ),
                ),
            )
            for target, validator in tamper_targets:
                original = target.read_bytes()
                target.write_bytes(original + b"tampered")
                with self.assertRaises(ArtifactError):
                    validator()
                target.write_bytes(original)
                validator()

            for root in (paths.workspace, paths.host_state):
                for path in root.rglob("*"):
                    if path.is_file():
                        self.assertNotIn(effects.secret.encode("utf-8"), path.read_bytes())

            gates = sorted(path.name for path in (paths.host_state / "gates").iterdir())
            self.assertEqual(
                gates,
                [
                    "0000-wish.json",
                    "0001-match.json",
                    "0002-invent.json",
                    "0003-make.json",
                    "0004-playtest.json",
                    "0005-release.json",
                ],
            )
            make_gate = _read_json(paths.host_state / "gates/0003-make.json")
            playtest_gate = _read_json(paths.host_state / "gates/0004-playtest.json")
            release_gate = _read_json(paths.host_state / "gates/0005-release.json")
            self.assertTrue(make_gate["evidence"]["checks"]["cad_verification_passed"])
            self.assertTrue(
                playtest_gate["evidence"]["checks"]["cad_verification_passed"]
            )
            self.assertEqual(
                release_gate["evidence"]["checks"]["publication_status"],
                "public",
            )


if __name__ == "__main__":
    unittest.main()
