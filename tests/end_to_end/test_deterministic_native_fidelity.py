import hashlib
import json
import os
import shutil
import stat
import tempfile
import unittest
import zipfile
from io import BytesIO
from email.parser import BytesParser
from email.policy import default as email_policy
from pathlib import Path
from unittest import mock

from tests.invent.fake_gamevault import E2E_NODES, FakeGameVaultTransport, install_fake_gamevault
from workshop.errors import ArtifactError, StateConflict, WorkshopError
from workshop.integrations.factory import (
    FACTORY_PROJECT_PDF_MANUAL_FILENAME,
    FACTORY_TOY_CATEGORY_SLUG,
    FactoryProjectFileResponse,
    HttpResponse,
)
from workshop.make.native_gate import (
    NATIVE_CAD_FULL_TIER,
    NATIVE_CAD_VERIFIER_MODE,
)
from workshop.make.native import NativeMade
from workshop.release.native import NativeRelease
from workshop.wish import Wish
from workshop.workflow import AgentRun, WORKSHOP_EFFORTS
from workshop.workflow.effort import EFFORT_ROUTE_CAPABILITY_PATH
from workshop.workflow.native_run import (
    native_run_paths,
    resume_native_run,
    start_native_run,
)
from tests.end_to_end.deterministic_codex import manual_pdf as _manual_pdf
from tests.end_to_end.deterministic_fidelity import (
    CANONICAL_ROUTES,
    DECLARED_REPAIR_EDGES,
    DECLARED_WAIT_RESUME,
    assert_native_ownership,
    assert_phase_proofs,
    assert_topology_coverage,
)
from tests.end_to_end.fidelity_policy import (
    deterministic_e2e_paths,
    fidelity_policy_violations,
)


_FIXTURE_CODEX = Path(__file__).with_name("deterministic_codex.py")


def _canonical_json(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _login_response():
    return HttpResponse(
        200,
        {"Content-Type": "application/json"},
        _canonical_json(
            {
                "access_token": "deterministic-access-token",
                "token_type": "Bearer",
                "expires_in": 31_536_000,
                "user": {"id": "owner-alice", "username": "alice"},
            }
        ),
    )


def _multipart_values(content_type, body):
    message = BytesParser(policy=email_policy).parsebytes(
        ("Content-Type: %s\r\nMIME-Version: 1.0\r\n\r\n" % content_type).encode()
        + body
    )
    result = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if isinstance(name, str):
            result.setdefault(name, []).append(part.get_payload(decode=True))
    return result


class _DeterministicFactoryTransport:
    """Stateful remote double at the outbound HTTP boundary only."""

    def __init__(
        self,
        product_id,
        *,
        strand_first_import_readback=False,
        lose_first_import_response=False,
        lose_first_promotion_response=False,
    ):
        self.product_id = product_id
        self.strand_first_import_readback = strand_first_import_readback
        self.lose_first_import_response = lose_first_import_response
        self.lose_first_promotion_response = lose_first_promotion_response
        self.calls = []
        self.imports = 0
        self.promotions = 0
        self.public = False
        self._strand_pending = False
        self.manual = _manual_pdf()
        self.authenticated_requests = True
        self.import_category = None
        self.import_has_cad = False
        self.import_has_manual = False

    def design(self):
        return {
            "id": "design-deterministic",
            "slug": self.product_id,
            "owner_id": "owner-alice",
            "root_id": "design-deterministic",
            "current_history_id": "history-deterministic-1",
            "published_history_id": (
                "history-deterministic-1" if self.public else None
            ),
            "status": "public" if self.public else "draft",
            "project_url": (
                "https://cdn.autonomous.ai/projects/history-deterministic-1/"
            ),
            "origin": "import",
            "title": "Orbit Dog Draughts",
            "description": "A compact printable orbital draughts set.",
            "tags": ["toy"],
            "category": {"slug": FACTORY_TOY_CATEGORY_SLUG},
            "author": {"id": "owner-alice"},
            "use_case": None,
            "story_blocks": [],
            "thumbnail_urls": ["https://cdn.autonomous.ai/cover.webp"],
            "listing": (
                {
                    "active": True,
                    "price_cents": 2400,
                    "currency": "usd",
                    "sku": "ORBIT-DOG-001",
                }
                if self.public
                else None
            ),
        }

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append((method, url, dict(headers), body, timeout))
        if url.endswith("/auth/agent/login"):
            return _login_response()
        self.authenticated_requests = self.authenticated_requests and (
            headers.get("Authorization") == "Bearer deterministic-access-token"
        )
        if url.endswith("/designs/import"):
            self.imports += 1
            values = _multipart_values(headers.get("Content-Type", ""), body or b"")
            categories = values.get("category", [])
            self.import_category = (
                categories[0].decode("utf-8") if len(categories) == 1 else None
            )
            files = values.get("file")
            if files and len(files) == 1:
                with zipfile.ZipFile(BytesIO(files[0])) as archive:
                    names = set(archive.namelist())
                    self.import_has_manual = "MANUAL.pdf" in names
                    self.import_has_cad = any(
                        name.lower().endswith((".step", ".stl")) for name in names
                    )
            self._strand_pending = self.strand_first_import_readback
            if self.lose_first_import_response and self.imports == 1:
                raise OSError("deterministic import response loss")
            return HttpResponse(201, {}, _canonical_json(self.design()))
        if method == "GET" and "/designs/" in url:
            if self._strand_pending:
                self._strand_pending = False
                raise OSError("deterministic readback interruption")
            return HttpResponse(200, {}, _canonical_json(self.design()))
        if method == "POST" and url.endswith("/publish"):
            self.promotions += 1
            self.public = True
            if self.lose_first_promotion_response and self.promotions == 1:
                raise OSError("deterministic promotion response loss")
            return HttpResponse(200, {}, b"{}")
        raise AssertionError("unexpected Factory request: %s %s" % (method, url))

    def project_file(self, method, url, headers, body, timeout):
        self.calls.append((method, url, dict(headers), body, timeout))
        if (
            method != "GET"
            or not url.endswith("/" + FACTORY_PROJECT_PDF_MANUAL_FILENAME)
            or body is not None
        ):
            raise AssertionError("unexpected Factory project-file request")
        return FactoryProjectFileResponse(
            200, {"Content-Type": "application/pdf"}, self.manual
        )


@unittest.skipUnless(
    os.environ.get("WORKSHOP_RUN_DETERMINISTIC_E2E") == "1",
    "run through the required deterministic-e2e CI gate",
)
class DeterministicNativeFidelityTest(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        install_fake_gamevault(self, FakeGameVaultTransport(E2E_NODES))
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.home = self.root / "workshop-home"
        self.binary = self.root / "bin/codex"
        self.binary.parent.mkdir()
        shutil.copyfile(_FIXTURE_CODEX, self.binary)
        self.binary.chmod(0o700)

    def _environment(self, *, home=None, credentials=True):
        home = self.home if home is None else Path(home)
        environment = {
            "PATH": os.environ.get("PATH", os.defpath),
            "HOME": str(home.parent / "native-home"),
            "CODEX_HOME": str(home.parent / "native-codex-home"),
            "WORKSHOP_HOME": str(home),
            "WORKSHOP_CODEX_BIN": str(self.binary),
        }
        if credentials:
            environment.update(
                {
                    "FACTORY_USERNAME": "alice",
                    "FACTORY_PASSWORD": "deterministic-host-secret",
                }
            )
        return environment

    @staticmethod
    def _wish(product_id):
        return Wish.create(
            product_id,
            "Build a pocket draughts set inspired by my orbit-loving dog.",
            constraints={"audience": "14+", "manufacture": "not-authorized"},
            context={"source": "required-deterministic-e2e"},
        )

    def _run(self, product_id, transport, *, effort="forge", home=None, credentials=True):
        self.addCleanup(self._remove_projection, product_id)
        with mock.patch.dict(
            os.environ,
            self._environment(home=home, credentials=credentials),
            clear=True,
        ), mock.patch(
            "workshop.workflow.native_run._FACTORY_TRANSPORT",
            transport,
        ), mock.patch(
            "workshop.workflow.native_run._FACTORY_PROJECT_FILE_TRANSPORT",
            transport.project_file,
        ):
            try:
                return start_native_run(self._wish(product_id), effort=effort)
            except WorkshopError as exc:
                paths = native_run_paths(product_id)
                diagnostic = paths.workspace / "authored/runtime-error.json"
                if diagnostic.is_file():
                    raise WorkshopError(
                        "%s; deterministic runtime: %s"
                        % (exc, diagnostic.read_text(encoding="utf-8"))
                    ) from exc
                raise

    def _resume(self, product_id, transport, *, home=None, credentials=True):
        with mock.patch.dict(
            os.environ,
            self._environment(home=home, credentials=credentials),
            clear=True,
        ), mock.patch(
            "workshop.workflow.native_run._FACTORY_TRANSPORT",
            transport,
        ), mock.patch(
            "workshop.workflow.native_run._FACTORY_PROJECT_FILE_TRANSPORT",
            transport.project_file,
        ):
            return resume_native_run(product_id)

    def _paths(self, product_id, *, home=None):
        with mock.patch.dict(
            os.environ,
            self._environment(home=home),
            clear=True,
        ):
            return native_run_paths(product_id)

    @staticmethod
    def _trace(paths):
        return [
            json.loads(line)
            for line in (paths.workspace / "authored/runtime-trace.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]

    def _remove_projection(self, product_id):
        repository = Path(__file__).resolve().parents[2]
        shutil.rmtree(repository / ("toys/alice-%s" % product_id), ignore_errors=True)

    def _assert_proof_deletion_mutations(self, paths, effort):
        checkpoint = AgentRun.open(
            paths.workspace, host_state_root=paths.host_state
        ).snapshot()
        targets = [
            (phase, paths.workspace / artifact.path)
            for phase, artifacts in checkpoint.stage_artifacts.items()
            for artifact in artifacts
        ]
        targets.extend(
            (
                path.stem.rsplit("-", 1)[-1],
                path,
            )
            for path in sorted((paths.host_state / "gates").glob("*.json"))
        )
        targets.extend(
            (path.parent.name, path)
            for path in sorted((paths.host_state / "evidence").glob("*/*.json"))
        )
        targets.extend(
            (
                ("release", paths.host_state / "release-effect.json"),
                ("release", paths.host_state / "factory-effects.sqlite3"),
            )
        )
        for phase, target in targets:
            with self.subTest(effort=effort, removed=str(target)):
                content = target.read_bytes()
                mode = stat.S_IMODE(target.stat().st_mode)
                target.unlink()
                try:
                    with self.assertRaisesRegex(AssertionError, "(?i)" + phase):
                        assert_phase_proofs(paths, effort=effort)
                finally:
                    target.write_bytes(content)
                    target.chmod(mode)

        wish_path = paths.workspace / "WISH.json"
        wish_bytes = wish_path.read_bytes()
        wish_mode = stat.S_IMODE(wish_path.stat().st_mode)
        wish_path.chmod(0o600)
        wish_path.write_bytes(wish_bytes + b"\n")
        try:
            with self.assertRaisesRegex(AssertionError, "Wish"):
                assert_phase_proofs(paths, effort=effort)
        finally:
            wish_path.write_bytes(wish_bytes)
            wish_path.chmod(wish_mode)

        checkpoint_path = paths.host_state / "agent-run.json"
        checkpoint_bytes = checkpoint_path.read_bytes()
        checkpoint_mode = stat.S_IMODE(checkpoint_path.stat().st_mode)
        raw = json.loads(checkpoint_bytes)
        mutations = []
        changed_effort = dict(raw, effort="quest" if effort != "quest" else "forge")
        mutations.append(("Wish", changed_effort))
        changed_capability = json.loads(checkpoint_bytes)
        capability = next(
            item
            for item in changed_capability["inputs"]
            if item["path"] == EFFORT_ROUTE_CAPABILITY_PATH
        )
        capability["sha256"] = "0" * 64
        mutations.append(("Wish", changed_capability))
        mutations.append(("Release", dict(raw, status="active")))
        for phase, changed in mutations:
            with self.subTest(effort=effort, changed=phase):
                checkpoint_path.write_bytes(_canonical_json(changed))
                try:
                    with self.assertRaisesRegex(AssertionError, phase):
                        assert_phase_proofs(paths, effort=effort)
                finally:
                    checkpoint_path.write_bytes(checkpoint_bytes)
                    checkpoint_path.chmod(checkpoint_mode)

    def _assert_completed_route(self, product_id, effort, paths, receipt, transport):
        expected_stages = list(WORKSHOP_EFFORTS[effort].enabled_stages)
        self.assertEqual(
            (receipt["stage"], receipt["status"]),
            ("release", "complete"),
            receipt,
        )
        self.assertIn(receipt["action"], {"started", "published-release"})
        self.assertEqual(receipt["effort"], effort)
        self.assertTrue(transport.public)
        self.assertTrue(transport.authenticated_requests)
        self.assertEqual(transport.import_category, FACTORY_TOY_CATEGORY_SLUG)
        self.assertTrue(transport.import_has_cad)
        self.assertTrue(transport.import_has_manual)
        checkpoint = AgentRun.open(
            paths.workspace, host_state_root=paths.host_state
        ).snapshot()
        self.assertEqual((checkpoint.stage, checkpoint.status), ("release", "complete"))
        self.assertEqual(checkpoint.effort, effort)
        self.assertEqual(
            set(checkpoint.stage_artifacts), {"wish", *expected_stages}
        )
        self.assertNotIn("match", checkpoint.stage_artifacts)
        self.assertNotIn("concept", checkpoint.stage_artifacts)
        self.assertNotIn("deliver", checkpoint.stage_artifacts)

        trace = self._trace(paths)
        self.assertEqual([item["stage"] for item in trace], expected_stages)
        self.assertEqual(
            [item["resume"] for item in trace],
            [False] + [True] * (len(expected_stages) - 1),
        )
        self.assertTrue(all(item["forbidden_environment"] == [] for item in trace))
        self.assertTrue(all("--enable" in item["argv"] for item in trace))
        self.assertTrue(all("--ignore-user-config" in item["argv"] for item in trace))
        self.assertTrue(all("--strict-config" in item["argv"] for item in trace))
        self.assertTrue(all("--ephemeral" not in item["argv"] for item in trace))
        self.assertTrue(
            all(
                any("workspace_roots" in argument for argument in item["argv"])
                for item in trace
            )
        )

        session = json.loads(
            (paths.host_state / "codex-session.json").read_text(encoding="utf-8")
        )
        self.assertEqual(session["thread_id"], "00000000-0000-4000-8000-000000000001")
        self.assertEqual(session["permission_profile"], "workshop-product-run")
        self.assertNotIn("deterministic-host-secret", json.dumps(session))

        expected_cad_stages = ["make"]
        if effort == "quest":
            expected_cad_stages.append("playtest")
        expected_cad_stages.append("release")
        made = NativeMade.from_mapping(
            json.loads(
                (paths.workspace / checkpoint.stage_artifacts["make"][0].path)
                .read_text(encoding="utf-8")
            )
        )
        cad_evidence = []
        for stage in expected_cad_stages:
            evidence_path = paths.host_state / "evidence" / stage / "r0001-cad-gate.json"
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            cad_evidence.append(evidence)
            self.assertTrue(evidence["passed"])
            self.assertEqual(evidence["verification_tier"], NATIVE_CAD_FULL_TIER)
            self.assertEqual(evidence["verifier_mode"], NATIVE_CAD_VERIFIER_MODE)
            self.assertFalse(evidence["legacy_full_tier_compatibility"])
            self.assertIn("--fresh", evidence["command"])
            self.assertIn("--exports", evidence["command"])
            self.assertIn("--strict-fit", evidence["command"])
            self.assertEqual(evidence["made_sha256"], made.made_sha256)
            self.assertEqual(
                evidence["product_artifact_sha256"],
                made.product_manifest.artifact_sha256,
            )
            self.assertEqual(stat.S_IMODE(evidence_path.stat().st_mode), 0o600)
        self.assertEqual(
            {item["evidence_stage"] for item in cad_evidence},
            set(expected_cad_stages),
        )

        release_effect = json.loads(
            (paths.host_state / "release-effect.json").read_text(encoding="utf-8")
        )
        manual_sha256 = hashlib.sha256(transport.manual).hexdigest()
        self.assertEqual(release_effect["publication_status"], "public")
        self.assertEqual(release_effect["manual_sha256"], manual_sha256)
        self.assertEqual(
            release_effect["receipt"]["details"]["manual_readback_sha256"],
            manual_sha256,
        )
        self.assertFalse((paths.workspace / "agent-outcome.json").exists())
        self.assertFalse((paths.workspace / "STAGE.json").stat().st_mode & 0o222)

        creative_stage = "make" if effort == "spark" else "invent"
        creative_names = {
            Path(item.path).name
            for item in checkpoint.stage_artifacts[creative_stage]
        }
        self.assertTrue({"assignment.json", "invented.json"} <= creative_names)
        release = NativeRelease.from_mapping(
            json.loads(
                (paths.workspace / checkpoint.stage_artifacts["release"][0].path)
                .read_text(encoding="utf-8")
            )
        )
        self.assertEqual(release.schema_version, 2 if effort == "quest" else 3)
        if effort == "quest":
            self.assertIn("playtest", checkpoint.stage_artifacts)
            self.assertFalse(
                (paths.workspace / "artifacts/release/package/PLAYTEST-NOT-RUN.json").exists()
            )
        else:
            self.assertNotIn("playtest", checkpoint.stage_artifacts)
            omission = paths.workspace / "artifacts/release/package/PLAYTEST-NOT-RUN.json"
            self.assertTrue(omission.is_file())
            self.assertEqual(release.product["playtest_status"], "not-run")

        gates = sorted((paths.host_state / "gates").glob("*.json"))
        self.assertEqual(len(gates), len(expected_stages) + 1)
        self.assertEqual(
            [path.stem.split("-", 1)[1] for path in gates],
            ["wish", *expected_stages],
        )
        assert_phase_proofs(paths, effort=effort)
        return checkpoint

    def test_canonical_effort_routes_are_repeatable_and_leave_durable_proof(self):
        self.assertEqual(
            {stage for route in WORKSHOP_EFFORTS.values() for stage in route.enabled_stages},
            {"invent", "make", "playtest", "release"},
            "the external fixture must be extended when production activates a stage",
        )
        for effort in WORKSHOP_EFFORTS:
            identities = []
            for repetition in range(2):
                with self.subTest(effort=effort, repetition=repetition):
                    product_id = "deterministic-%s-repeatable" % effort
                    home = self.root / ("home-%s-%d" % (effort, repetition))
                    transport = _DeterministicFactoryTransport(
                        product_id,
                        strand_first_import_readback=(effort == "forge" and repetition == 0),
                    )
                    receipt = self._run(
                        product_id, transport, effort=effort, home=home
                    )
                    if receipt["status"] == "waiting":
                        receipt = self._resume(product_id, transport, home=home)
                    paths = self._paths(product_id, home=home)
                    checkpoint = self._assert_completed_route(
                        product_id, effort, paths, receipt, transport
                    )
                    if repetition == 0:
                        self._assert_proof_deletion_mutations(paths, effort)
                    identities.append(
                        {
                            stage: [(item.path, item.sha256) for item in artifacts]
                            for stage, artifacts in checkpoint.stage_artifacts.items()
                        }
                    )
                    if effort == "forge" and repetition == 0:
                        self.assertEqual(
                            transport.imports,
                            1,
                            "ambiguous import was retried blindly",
                        )
                    self._remove_projection(product_id)
            self.assertEqual(identities[0], identities[1])

    def test_stale_finalizer_proposal_is_rejected_by_the_host(self):
        product_id = "deterministic-stale-proposal"
        transport = _DeterministicFactoryTransport(product_id)
        with self.assertRaisesRegex(StateConflict, "checkpoint"):
            self._run(product_id, transport, effort="forge")
        self.assertEqual(transport.calls, [])
        checkpoint = AgentRun.open(
            self._paths(product_id).workspace,
            host_state_root=self._paths(product_id).host_state,
        ).snapshot()
        self.assertEqual((checkpoint.stage, checkpoint.status), ("invent", "active"))

    def test_invent_rejects_invalid_authored_selection_research_and_context(self):
        scenarios = (
            "invent-unavailable",
            "invent-ranking",
            "invent-research",
            "invent-concept",
            "invent-physical",
            "invent-source-tamper",
        )
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                product_id = "deterministic-%s" % scenario
                transport = _DeterministicFactoryTransport(product_id)
                with self.assertRaises(WorkshopError):
                    self._run(product_id, transport, effort="forge")
                paths = self._paths(product_id)
                checkpoint = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                ).snapshot()
                self.assertEqual(checkpoint.stage, "invent")
                self.assertNotIn("make", checkpoint.stage_artifacts)
                self.assertEqual(transport.calls, [])

    def test_post_finalizer_artifact_tamper_is_rejected_before_cad_or_factory(self):
        product_id = "deterministic-artifact-tamper"
        transport = _DeterministicFactoryTransport(product_id)
        with self.assertRaises((ArtifactError, StateConflict)):
            self._run(product_id, transport)
        paths = self._paths(product_id)
        self.assertEqual(transport.calls, [])
        self.assertEqual(list((paths.host_state / "evidence").glob("**/*")), [])
        checkpoint = AgentRun.open(
            paths.workspace, host_state_root=paths.host_state
        ).snapshot()
        self.assertEqual((checkpoint.stage, checkpoint.status), ("make", "active"))

    def test_playtest_rejects_stale_missing_mismatched_and_tampered_evidence(self):
        scenarios = (
            "playtest-stale-made",
            "playtest-conflicting-binding",
            "playtest-missing-evidence",
            "playtest-mismatched-verdict",
            "playtest-over-budget",
            "playtest-evidence-tamper",
        )
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                product_id = "deterministic-%s" % scenario
                transport = _DeterministicFactoryTransport(product_id)
                with self.assertRaises(WorkshopError):
                    self._run(product_id, transport, effort="quest")
                paths = self._paths(product_id)
                checkpoint = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                ).snapshot()
                self.assertEqual(checkpoint.stage, "playtest")
                self.assertNotIn("release", checkpoint.stage_artifacts)
                self.assertEqual(transport.calls, [])

    def test_quest_accepts_rich_playtest_configs_bound_to_current_made(self):
        product_id = "deterministic-playtest-rich-config"
        transport = _DeterministicFactoryTransport(product_id)

        receipt = self._run(product_id, transport, effort="quest")

        self.assertEqual(receipt["status"], "complete")
        checkpoint = AgentRun.open(
            self._paths(product_id).workspace,
            host_state_root=self._paths(product_id).host_state,
        ).snapshot()
        self.assertEqual((checkpoint.stage, checkpoint.status), ("release", "complete"))
        self.assertIn("playtest", checkpoint.stage_artifacts)

    def test_completed_resume_retries_failed_public_example_projection(self):
        product_id = "deterministic-public-example-retry"
        transport = _DeterministicFactoryTransport(product_id)
        target = Path(__file__).resolve().parents[2] / (
            "toys/alice-%s" % product_id
        )

        target.mkdir(parents=True)
        (target / "collision.txt").write_text(
            "pre-existing public example collision\n",
            encoding="utf-8",
        )
        completed = self._run(product_id, transport, effort="forge")

        self.assertEqual(completed["status"], "complete")
        self.assertEqual(completed["publication"]["public_example"]["status"], "error")
        self.assertTrue((target / "collision.txt").is_file())

        shutil.rmtree(target)

        reconciled = self._resume(product_id, transport)

        self.assertEqual(reconciled["status"], "complete")
        self.assertEqual(reconciled["action"], "reconciled-public-example")
        self.assertEqual(
            reconciled["publication"]["public_example"],
            {
                "status": "materialized",
                "path": "toys/alice-%s" % product_id,
            },
        )
        self.assertTrue(target.is_dir())

    def test_quest_rejection_invalidates_and_repairs_through_the_same_session(self):
        product_id = "deterministic-quest-repair"
        transport = _DeterministicFactoryTransport(product_id)
        receipt = self._run(product_id, transport, effort="quest")
        paths = self._paths(product_id)
        self.assertEqual(receipt["status"], "complete")
        self.assertEqual(
            [item["stage"] for item in self._trace(paths)],
            ["invent", "make", "playtest", "make", "playtest", "release"],
        )
        checkpoint = AgentRun.open(
            paths.workspace, host_state_root=paths.host_state
        ).snapshot()
        self.assertEqual(checkpoint.round_index, 2)
        self.assertEqual(checkpoint.invalidated_stages, ())
        for stage in ("make", "playtest"):
            self.assertTrue(
                (paths.host_state / "evidence" / stage / "r0001-cad-gate.json").is_file()
            )
            self.assertTrue(
                (paths.host_state / "evidence" / stage / "r0002-cad-gate.json").is_file()
            )
        self._remove_projection(product_id)

    def test_quest_fundamental_revision_returns_to_invent_with_prior_lineage(self):
        product_id = "deterministic-quest-invent-revision"
        transport = _DeterministicFactoryTransport(product_id)
        receipt = self._run(product_id, transport, effort="quest")
        paths = self._paths(product_id)
        self.assertEqual(receipt["status"], "complete")
        self.assertEqual(
            [item["stage"] for item in self._trace(paths)],
            ["invent", "make", "playtest", "invent", "make", "playtest", "release"],
        )
        checkpoint = AgentRun.open(
            paths.workspace, host_state_root=paths.host_state
        ).snapshot()
        self.assertEqual(checkpoint.round_index, 2)
        self.assertTrue(
            any("r0002" in item.path for item in checkpoint.stage_artifacts["invent"])
        )
        assert_phase_proofs(
            paths,
            effort="quest",
            expected_trace=(
                "invent", "make", "playtest", "invent", "make", "playtest", "release"
            ),
        )
        self._remove_projection(product_id)

    def test_authored_cad_rejection_repairs_at_the_same_checkpoint(self):
        product_id = "deterministic-cad-repair"
        transport = _DeterministicFactoryTransport(product_id)
        receipt = self._run(product_id, transport, effort="forge")
        paths = self._paths(product_id)
        self.assertEqual(receipt["status"], "complete")
        make_turns = [item for item in self._trace(paths) if item["stage"] == "make"]
        self.assertEqual(len(make_turns), 2)
        self.assertEqual(
            make_turns[0]["checkpoint_sha256"], make_turns[1]["checkpoint_sha256"]
        )
        self.assertNotEqual(
            make_turns[0]["subject_sha256"], make_turns[1]["subject_sha256"]
        )
        rejection = paths.host_state / "cad-gate-rejections" / (
            make_turns[0]["checkpoint_sha256"] + ".json"
        )
        self.assertTrue(rejection.is_file())
        self.assertEqual(json.loads(rejection.read_text())["stage"], "make")
        assert_phase_proofs(
            paths,
            effort="forge",
            expected_trace=("invent", "make", "make", "release"),
        )
        self._remove_projection(product_id)

    def test_missing_credentials_resume_without_an_extra_native_turn(self):
        product_id = "deterministic-credential-resume"
        transport = _DeterministicFactoryTransport(product_id)
        waiting = self._run(product_id, transport, credentials=False)
        paths = self._paths(product_id)
        trace_before = self._trace(paths)
        self.assertEqual((waiting["stage"], waiting["status"]), ("release", "waiting"))
        self.assertIn("Factory credentials", " ".join(waiting["needs"]))
        self.assertEqual(transport.calls, [])
        completed = self._resume(product_id, transport)
        self.assertEqual(completed["status"], "complete")
        self.assertEqual(self._trace(paths), trace_before)
        self._remove_projection(product_id)

    def test_tampered_factory_effect_state_fails_closed(self):
        product_id = "deterministic-effect-tamper"
        transport = _DeterministicFactoryTransport(product_id)
        waiting = self._run(product_id, transport, credentials=False)
        self.assertEqual(waiting["status"], "waiting")
        paths = self._paths(product_id)
        effect = paths.host_state / "release-effect.json"
        effect.write_bytes(b'{"schema_version":3,"kind":"tampered"}\n')
        effect.chmod(0o600)
        with self.assertRaises(WorkshopError):
            self._resume(product_id, transport)
        self.assertEqual(transport.calls, [])

        proposal_product_id = "deterministic-pending-proposal-tamper"
        proposal_transport = _DeterministicFactoryTransport(proposal_product_id)
        waiting = self._run(
            proposal_product_id,
            proposal_transport,
            credentials=False,
        )
        self.assertEqual(waiting["status"], "waiting")
        proposal_paths = self._paths(proposal_product_id)
        proposal = proposal_paths.host_state / "release-effect-wait.json"
        pending = json.loads(proposal.read_bytes())
        pending["outcome"]["artifacts"][0]["sha256"] = "0" * 64
        proposal.write_bytes(_canonical_json(pending))
        with self.assertRaises(WorkshopError):
            self._resume(proposal_product_id, proposal_transport)
        checkpoint = AgentRun.open(
            proposal_paths.workspace,
            host_state_root=proposal_paths.host_state,
        ).snapshot()
        self.assertNotEqual(checkpoint.status, "complete")
        self.assertEqual(proposal_transport.calls, [])

    def test_release_validation_rejects_corrupt_false_or_tampered_packages_before_factory(self):
        scenarios = (
            "release-corrupt-pdf",
            "release-active-pdf",
            "release-false-claim",
            "release-package-tamper",
        )
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                product_id = "deterministic-%s" % scenario
                transport = _DeterministicFactoryTransport(product_id)
                with self.assertRaises(WorkshopError):
                    self._run(product_id, transport, effort="forge")
                paths = self._paths(product_id)
                checkpoint = AgentRun.open(
                    paths.workspace, host_state_root=paths.host_state
                ).snapshot()
                self.assertEqual(checkpoint.stage, "release")
                self.assertNotEqual(checkpoint.status, "complete")
                self.assertEqual(transport.calls, [])

    def test_factory_response_loss_reconciles_without_duplicate_effects(self):
        scenarios = (
            ("import", {"lose_first_import_response": True}),
            ("promotion", {"lose_first_promotion_response": True}),
        )
        for name, options in scenarios:
            with self.subTest(name=name):
                product_id = "deterministic-%s-response-loss" % name
                transport = _DeterministicFactoryTransport(product_id, **options)
                try:
                    first = self._run(product_id, transport)
                except WorkshopError:
                    first = {"status": "waiting"}
                completed = first
                for unused in range(3):
                    if completed["status"] == "complete":
                        break
                    completed = self._resume(product_id, transport)
                self.assertEqual(
                    completed["status"],
                    "complete",
                    {"receipt": completed, "calls": transport.calls},
                )
                self.assertEqual(transport.imports, 1)
                self.assertEqual(transport.promotions, 1)
                self._remove_projection(product_id)

    def test_fidelity_test_uses_only_external_runtime_and_transport_doubles(self):
        violations = []
        for path in deterministic_e2e_paths():
            violations.extend(
                fidelity_policy_violations(
                    path.read_text(encoding="utf-8"), filename=path.name
                )
            )
        self.assertEqual(violations, [])

        forbidden = (
            "from unittest import mock\nmock.patch('workshop.workflow.native_run.verify_native_made_cad')\n",
            "def scenario(monkeypatch):\n    monkeypatch.setattr(object, 'x', 1)\n",
            "run(stage_evaluator=lambda value: value)\n",
            "run(release_writer=lambda value: value)\n",
            (
                "from pathlib import Path\n"
                "class CrossingTransport:\n"
                "    def __call__(self):\n"
                "        Path('host-state/gate.json').write_bytes(b'x')\n"
            ),
        )
        for source in forbidden:
            with self.subTest(source=source):
                self.assertTrue(fidelity_policy_violations(source, filename="mutation.py"))
        allowed = (
            "from unittest import mock\n"
            "mock.patch('workshop.workflow.native_run._FACTORY_TRANSPORT', transport)\n"
        )
        self.assertEqual(fidelity_policy_violations(allowed, filename="allowed.py"), ())

    def test_topology_guard_names_route_repair_and_wait_drift(self):
        assert_topology_coverage()
        route_mutation = dict(CANONICAL_ROUTES)
        route_mutation["spark"] = ("invent", "make", "release")
        mutations = (
            ({"routes": route_mutation}, "route:spark"),
            (
                {"repair_edges": DECLARED_REPAIR_EDGES - {("playtest", "invent")}},
                "repair:playtest->invent",
            ),
            ({"wait_resume": DECLARED_WAIT_RESUME - {"release"}}, "wait-resume:release"),
        )
        for keywords, diagnostic in mutations:
            with self.subTest(diagnostic=diagnostic), self.assertRaisesRegex(
                AssertionError, diagnostic
            ):
                assert_topology_coverage(**keywords)

    def test_phase_and_ownership_guards_name_the_owning_failure(self):
        valid = ({
            "kind": "autonomous-workshop.deterministic-e2e-turn",
            "stage": "make",
            "checkpoint_sha256": "0" * 64,
            "subject_sha256": "1" * 64,
            "stage_packet_sha256": "2" * 64,
            "prompt_sha256": "3" * 64,
            "stage_read_only": True,
            "source_paths": ["STAGE.json"],
            "agent_writes": ["artifacts/make/r0001/made.json"],
            "source_writes": [],
            "finalizer_writes": ["artifacts/make/r0001/made.json"],
            "workspace_before_sha256": "4" * 64,
            "workspace_after_sha256": "5" * 64,
            "finalizer": {"arguments": ["make"], "returncode": 0},
            "forbidden_environment": [],
            "forbidden_paths_visible": [],
        },)
        assert_native_ownership(valid)
        crossed = (dict(valid[0], agent_writes=["host-state/gates/make.json"]),)
        with self.assertRaisesRegex(AssertionError, "ownership drift: make"):
            assert_native_ownership(crossed)
        incomplete = (dict(valid[0]),)
        incomplete[0].pop("finalizer")
        with self.assertRaisesRegex(AssertionError, "ownership drift: make"):
            assert_native_ownership(incomplete)


if __name__ == "__main__":
    unittest.main()
