import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.contribution_rpc import (
    ISOLATION_CAPABILITY,
    ContributionHookClient,
    ContributionIsolationContext,
    MacOSSandboxIsolation,
)
from inventor_workshop.errors import ArtifactError, ContractError
from inventor_workshop.jobs import Invented, Made, MakeContext, PlaytestContext, WaitingFor
from inventor_workshop.make import Wish
from inventor_workshop.scaffold import scaffold_inventor
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint


def canonical_json(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def addressed(value, digest_key):
    document = dict(value)
    document[digest_key] = hashlib.sha256(canonical_json(document)).hexdigest()
    return document


def response_for(request, **values):
    return addressed(
        {
            "schema_version": 1,
            "kind": "workshop.contribution-hook-response",
            "stage": request["stage"],
            "request_sha256": request["request_sha256"],
            **values,
        },
        "response_sha256",
    )


def write_response(path, value):
    path.write_bytes(canonical_json(value) + b"\n")
    os.chmod(path, 0o600)


def trusted_test_isolation(command, context):
    """Portable injection seam for trusted fixture hooks, never production."""

    if not isinstance(context, ContributionIsolationContext):
        raise AssertionError("fixture isolation requires a typed context")
    return tuple(command)


class ContributionRpcTest(unittest.TestCase):
    def fixture(self, temporary, *, level="custom-make", inventor_id="custom-worker"):
        root = Path(temporary).resolve()
        inventor = scaffold_inventor(
            root,
            inventor_id,
            "Custom Worker",
            "mechanical surprises with one playful motion",
            lane="moving-machines",
            level=level,
        )
        hook = inventor / "hook.py"
        hook.write_text("raise SystemExit(1)\n", encoding="utf-8")
        wish = Wish.create(
            "tiny-custom-toy",
            "A tiny hand-cranked creature that waves hello",
        )
        taste = load_taste(inventor)
        blueprint = ToyBlueprint.for_lane("moving-machines")
        wish_sha256 = hashlib.sha256(canonical_json(wish.to_dict())).hexdigest()
        invented = Invented(
            wish_sha256,
            taste.sha256,
            blueprint.lane,
            {
                "title": "Hello Crank",
                "summary": "A chosen industrial-design direction for a waving toy.",
            },
            95,
            90,
        )
        attempt = root / "attempt"
        attempt.mkdir(mode=0o700)
        os.chmod(attempt, 0o700)
        context = MakeContext(
            wish,
            taste,
            blueprint,
            invented,
            1,
            attempt / "workspace",
            (),
            2,
            inventor_id,
        )
        return inventor, hook, context

    @staticmethod
    def fake_runner(action):
        def run(command, *, cwd, env, timeout):
            request_path = Path(command[3])
            response_path = Path(command[4])
            request = json.loads(request_path.read_text(encoding="utf-8"))
            action(
                request,
                response_path,
                Path(cwd),
                dict(env),
                tuple(command),
            )
            return subprocess.CompletedProcess(list(command), 0)

        return run

    def test_unsupported_host_returns_typed_isolation_need_before_runner_or_rpc_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor, _, context = self.fixture(temporary)
            runner = mock.Mock(
                side_effect=AssertionError("custom code must not run without isolation")
            )
            client = ContributionHookClient(
                inventor,
                "custom-make",
                runner=runner,
            )
            with mock.patch("inventor_workshop.contribution_rpc.sys.platform", "linux"):
                with self.assertRaises(WaitingFor) as caught:
                    client.make(context)
            self.assertEqual(len(caught.exception.needs), 1)
            need = caught.exception.needs[0]
            self.assertEqual((need.job, need.capability), ("make", ISOLATION_CAPABILITY))
            self.assertIn("disabled", need.reason)
            self.assertIn("never bypass", need.instructions)
            runner.assert_not_called()
            self.assertEqual(tuple(context.workspace.parent.iterdir()), ())

    def test_injected_isolation_adapter_wraps_only_the_exact_stage_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor, _, context = self.fixture(temporary)
            observed = {}

            def isolation(command, isolation_context):
                observed["base"] = tuple(command)
                observed["context"] = isolation_context
                return ("fixture-isolator", *tuple(command))

            def runner(command, *, cwd, env, timeout):
                del env, timeout
                self.assertEqual(command[0], "fixture-isolator")
                base = command[1:]
                request_path = Path(base[3])
                response_path = Path(base[4])
                request = json.loads(request_path.read_text(encoding="utf-8"))
                write_response(
                    response_path,
                    response_for(
                        request,
                        status="waiting",
                        needs=[
                            {
                                "job": "make",
                                "capability": "fixture-wait",
                                "reason": "The isolated fixture deliberately waits.",
                                "instructions": "Resume the exact isolated stage.",
                            }
                        ],
                    ),
                )
                return subprocess.CompletedProcess(list(command), 0)

            client = ContributionHookClient(
                inventor,
                "custom-make",
                runner=runner,
                isolation=isolation,
            )
            with self.assertRaises(WaitingFor):
                client.make(context)
            self.assertEqual(
                observed["base"][0], str(Path(os.sys.executable).resolve(strict=True))
            )
            self.assertEqual(observed["base"][2], "make")
            isolation_context = observed["context"]
            self.assertIsInstance(isolation_context, ContributionIsolationContext)
            self.assertEqual(isolation_context.workspace, context.workspace)
            self.assertIsNone(isolation_context.product_root)

    def test_macos_profile_is_deny_default_and_does_not_grant_inventor_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor, _, context = self.fixture(temporary)
            profiles = []

            def probe(command, **kwargs):
                del kwargs
                profiles.append(command[2])
                return subprocess.CompletedProcess(command, 0)

            adapter = MacOSSandboxIsolation(probe_runner=probe)

            def sandbox_runner(command, *, cwd, env, timeout):
                del cwd, env, timeout
                self.assertEqual(command[:2], ("/usr/bin/sandbox-exec", "-p"))
                base = command[3:]
                request_path = Path(base[3])
                response_path = Path(base[4])
                request = json.loads(request_path.read_text(encoding="utf-8"))
                write_response(
                    response_path,
                    response_for(
                        request,
                        status="waiting",
                        needs=[
                            {
                                "job": "make",
                                "capability": "profile-inspected",
                                "reason": "The isolation profile was inspected.",
                                "instructions": "Keep the exact profile.",
                            }
                        ],
                    ),
                )
                return subprocess.CompletedProcess(list(command), 0)

            with mock.patch.object(
                adapter,
                "_trusted_executable",
                return_value=Path("/usr/bin/sandbox-exec"),
            ):
                client = ContributionHookClient(
                    inventor,
                    "custom-make",
                    runner=sandbox_runner,
                    isolation=adapter,
                )
                with self.assertRaises(WaitingFor):
                    client.make(context)
            self.assertEqual(len(profiles), 1)
            profile = profiles[0]
            self.assertIn("(deny default)", profile)
            self.assertIn("(deny network*)", profile)
            self.assertNotIn(
                "(subpath %s)" % json.dumps(str(inventor)), profile
            )
            self.assertNotIn(str(inventor / "toys"), profile)
            self.assertNotIn(str(inventor / ".workshop"), profile)
            self.assertIn(str(inventor / "hook.py"), profile)
            self.assertIn(str(inventor / "inventor.json"), profile)
            self.assertIn(str(inventor / "TASTE.md"), profile)
            write_clause = profile.split("(allow file-write*", 1)[1]
            self.assertIn(str(context.workspace), write_clause)
            self.assertIn("response.json", write_clause)
            self.assertNotIn(str(inventor), write_clause)

    def test_failed_macos_probe_returns_typed_need_and_never_runs_hook(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor, _, context = self.fixture(temporary)
            adapter = MacOSSandboxIsolation(
                probe_runner=lambda command, **kwargs: subprocess.CompletedProcess(
                    command, 71
                )
            )
            runner = mock.Mock(
                side_effect=AssertionError("failed isolation must not run custom code")
            )
            with mock.patch.object(
                adapter,
                "_trusted_executable",
                return_value=Path("/usr/bin/sandbox-exec"),
            ):
                client = ContributionHookClient(
                    inventor,
                    "custom-make",
                    runner=runner,
                    isolation=adapter,
                )
                with self.assertRaises(WaitingFor) as caught:
                    client.make(context)
            self.assertEqual(
                caught.exception.needs[0].capability, ISOLATION_CAPABILITY
            )
            runner.assert_not_called()
            self.assertEqual(tuple(context.workspace.parent.iterdir()), ())

    def test_real_macos_sandbox_blocks_inventor_state_write_read_and_network(self):
        required = os.environ.get("WORKSHOP_REQUIRE_MACOS_ISOLATION_TEST") == "1"
        if os.sys.platform != "darwin" or not Path("/usr/bin/sandbox-exec").is_file():
            if required:
                self.fail("required macOS contribution isolation is unavailable")
            self.skipTest("macOS sandbox-exec is not installed")
        with tempfile.TemporaryDirectory() as temporary:
            inventor, hook, context = self.fixture(temporary)
            toys = inventor / "toys"
            toys.mkdir()
            (toys / "unbound-secret.txt").write_text(
                "must not enter custom output\n", encoding="utf-8"
            )
            marker = inventor / ".workshop-worker-escaped"
            hook.write_text(
                """from pathlib import Path
import json
import socket

from inventor_workshop.contribution_rpc import contribution_hook_main
from inventor_workshop.jobs import Made

ROOT = Path(__file__).resolve().parent

def make(context):
    observations = {}
    try:
        (ROOT / ".workshop-worker-escaped").write_text("bad", encoding="utf-8")
    except OSError:
        observations["manager_write"] = "blocked"
    else:
        observations["manager_write"] = "allowed"
    try:
        (ROOT / "toys" / "unbound-secret.txt").read_text(encoding="utf-8")
    except OSError:
        observations["toys_read"] = "blocked"
    else:
        observations["toys_read"] = "allowed"
    try:
        connection = socket.socket()
        connection.settimeout(0.2)
        connection.connect(("127.0.0.1", 9))
    except PermissionError:
        observations["network"] = "blocked"
    except OSError:
        observations["network"] = "allowed"
    else:
        observations["network"] = "allowed"
        connection.close()
    context.workspace.mkdir(mode=0o700)
    (context.workspace / "isolation.json").write_text(
        json.dumps(observations, sort_keys=True), encoding="utf-8"
    )
    return Made.from_root(
        context.workspace,
        {
            "title": "Isolated Hook",
            "summary": "A hook whose OS authority was tested.",
            "lane": context.blueprint.lane,
        },
    )

raise SystemExit(contribution_hook_main(ROOT, make=make))
""",
                encoding="utf-8",
            )
            try:
                made = ContributionHookClient(inventor, "custom-make").make(
                    context
                )
            except WaitingFor as waiting:
                if any(
                    need.capability == ISOLATION_CAPABILITY
                    for need in waiting.needs
                ):
                    if required:
                        self.fail(
                            "required macOS contribution isolation probe did not pass"
                        )
                    self.skipTest(
                        "the enclosing test runner does not permit a nested macOS sandbox"
                    )
                raise
            self.assertFalse(marker.exists())
            observed = json.loads(
                (made.artifact_root / "isolation.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                observed,
                {
                    "manager_write": "blocked",
                    "network": "blocked",
                    "toys_read": "blocked",
                },
            )

    def test_real_make_child_gets_only_minimal_environment_and_exact_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor, hook, context = self.fixture(temporary)
            hook.write_text(
                """from pathlib import Path
import json
import os

from inventor_workshop.contribution_rpc import contribution_hook_main
from inventor_workshop.jobs import Made, MakeContext

ROOT = Path(__file__).resolve().parent

def make(context: MakeContext) -> Made:
    context.workspace.mkdir(mode=0o700)
    (context.workspace / "environment.json").write_text(
        json.dumps(dict(os.environ), sort_keys=True), encoding="utf-8"
    )
    (context.workspace / "context.json").write_text(
        json.dumps(
            {
                "type": type(context).__name__,
                "wish": context.wish.to_dict(),
                "invented": context.invented.to_dict(),
                "lane": context.blueprint.lane,
                "round": context.round,
                "playtest_rounds": context.playtest_rounds,
                "inventor_id": context.inventor_id,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return Made.from_root(
        context.workspace,
        {
            "title": "Hello Crank",
            "summary": "A printable waving mechanism.",
            "lane": context.blueprint.lane,
        },
    )

raise SystemExit(contribution_hook_main(ROOT, make=make))
""",
                encoding="utf-8",
            )
            secrets = {
                "FACTORY_PASSWORD": "do-not-cross-factory",
                "OPENAI_API_KEY": "do-not-cross-openai",
                "AWS_SECRET_ACCESS_KEY": "do-not-cross-cloud",
                "WORKSHOP_SHOP_TOKEN": "do-not-cross-shop",
                "UNRELATED_SECRET": "do-not-cross-unrelated",
            }
            with mock.patch.dict(os.environ, secrets, clear=False):
                made = ContributionHookClient(
                    inventor,
                    "custom-make",
                    isolation=trusted_test_isolation,
                ).make(context)

            self.assertIsInstance(made, Made)
            self.assertEqual(made.artifact_root, context.workspace)
            observed_environment = json.loads(
                (made.artifact_root / "environment.json").read_text(encoding="utf-8")
            )
            for name, value in secrets.items():
                self.assertNotIn(name, observed_environment)
                self.assertNotIn(value, canonical_json(observed_environment).decode())
            self.assertTrue(
                set(observed_environment).issubset(
                    {
                        "LANG",
                        "LC_ALL",
                        "PATH",
                        "PYTHONHASHSEED",
                        "PYTHONNOUSERSITE",
                        "PYTHONPATH",
                        "PYTHONSAFEPATH",
                        "PYTHONDONTWRITEBYTECODE",
                        # macOS injects this process-local text encoding hint
                        # even when execve receives an otherwise exact env.
                        "__CF_USER_TEXT_ENCODING",
                    }
                ),
                sorted(observed_environment),
            )
            observed_context = json.loads(
                (made.artifact_root / "context.json").read_text(encoding="utf-8")
            )
            self.assertEqual(observed_context["type"], "MakeContext")
            self.assertEqual(observed_context["wish"], context.wish.to_dict())
            self.assertEqual(observed_context["invented"], context.invented.to_dict())
            self.assertEqual(observed_context["inventor_id"], "custom-worker")
            request = (context.workspace.parent / "contribution-rpc/request.json").read_text(
                encoding="utf-8"
            )
            self.assertFalse(any(name in request or value in request for name, value in secrets.items()))

    def test_real_worker_returns_only_typed_waiting_for_current_stage(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor, hook, context = self.fixture(temporary)
            hook.write_text(
                """from pathlib import Path
from inventor_workshop.contribution_rpc import contribution_hook_main
from inventor_workshop.jobs import Need, WaitingFor

ROOT = Path(__file__).resolve().parent

def make(context):
    raise WaitingFor(Need(
        "make",
        "custom-bearing-design",
        "The custom bearing geometry is not implemented yet.",
        "Implement the exact bearing and return a typed Made artifact.",
    ))

raise SystemExit(contribution_hook_main(ROOT, make=make))
""",
                encoding="utf-8",
            )
            with self.assertRaises(WaitingFor) as caught:
                ContributionHookClient(
                    inventor,
                    "custom-make",
                    isolation=trusted_test_isolation,
                ).make(context)
            self.assertEqual(len(caught.exception.needs), 1)
            self.assertEqual(caught.exception.needs[0].job, "make")
            self.assertEqual(
                caught.exception.needs[0].capability, "custom-bearing-design"
            )

    def test_real_playtest_child_returns_typed_artifact_bound_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor, hook, make_context = self.fixture(
                temporary, level="custom-playtest"
            )
            product_root = Path(temporary).resolve() / "product"
            product_root.mkdir()
            (product_root / "toy.txt").write_text("exact product bytes\n", encoding="utf-8")
            made = Made.from_root(
                product_root,
                {
                    "title": "Hello Crank",
                    "summary": "The exact custom product under test.",
                    "lane": "moving-machines",
                },
            )
            playtest_attempt = Path(temporary).resolve() / "playtest-attempt"
            playtest_attempt.mkdir(mode=0o700)
            os.chmod(playtest_attempt, 0o700)
            context = PlaytestContext(
                make_context.wish,
                make_context.taste,
                make_context.blueprint,
                1,
                made,
                playtest_attempt / "workspace",
                2,
            )
            hook.write_text(
                """from pathlib import Path
import hashlib
import json

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.contribution_rpc import contribution_hook_main
from inventor_workshop.jobs import Playtested
from inventor_workshop.models import PlaytestResult
from inventor_workshop.playtest import Playtest

ROOT = Path(__file__).resolve().parent

def playtest(context):
    context.workspace.mkdir(mode=0o700)
    relative = "ai-players/custom-motion.json"
    path = context.workspace / relative
    path.parent.mkdir()
    evidence = {
        "evidence_class": "ai-simulation",
        "artifact_sha256": context.made.artifact_sha256,
        "finding": "The waving motion completes without a simulated jam.",
    }
    payload = json.dumps(evidence, sort_keys=True) + "\\n"
    path.write_text(payload, encoding="utf-8")
    result = PlaytestResult.create(
        "custom-motion",
        True,
        context.made.artifact_sha256,
        evidence,
        "custom-ai-player",
        "1.0.0",
        "f" * 64,
        relative,
        hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    )
    evidence_manifest = build_artifact_manifest(
        context.workspace, created_at="content-addressed"
    )
    return Playtested(
        Playtest(
            context.made.artifact_manifest,
            (result,),
            evidence_manifest=evidence_manifest,
        )
    )

raise SystemExit(contribution_hook_main(ROOT, playtest=playtest))
""",
                encoding="utf-8",
            )
            playtested = ContributionHookClient(
                inventor,
                "custom-playtest",
                isolation=trusted_test_isolation,
            ).playtest(context)
            self.assertEqual(
                playtested.evidence.artifact_sha256, made.artifact_sha256
            )
            self.assertEqual(
                playtested.evidence.results[0].inspection_id, "custom-motion"
            )
            self.assertTrue(playtested.evidence.results[0].passed)
            playtested.evidence.assert_valid()

    def test_manager_rejects_path_escape_descriptor(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor, _, context = self.fixture(temporary)
            outside = context.workspace.parent.parent / "outside"
            outside.mkdir()
            (outside / "toy.txt").write_text("outside\n", encoding="utf-8")

            def attack(request, response_path, cwd, env, command):
                del cwd, env, command
                write_response(
                    response_path,
                    response_for(
                        request,
                        status="result",
                        artifact_root="../../outside",
                        artifact_sha256="0" * 64,
                        product={
                            "title": "Escape",
                            "summary": "Points outside the reserved output.",
                            "lane": "moving-machines",
                        },
                    ),
                )

            client = ContributionHookClient(
                inventor,
                "custom-make",
                runner=self.fake_runner(attack),
                isolation=trusted_test_isolation,
            )
            with self.assertRaisesRegex(ContractError, "stay inside"):
                client.make(context)

    def test_manager_rejects_symlink_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor, _, context = self.fixture(temporary)
            outside = context.workspace.parent.parent / "outside.txt"
            outside.write_text("outside bytes\n", encoding="utf-8")

            def attack(request, response_path, cwd, env, command):
                del cwd, env, command
                workspace = Path(request["workspace"])
                workspace.mkdir()
                (workspace / "leak.txt").symlink_to(outside)
                write_response(
                    response_path,
                    response_for(
                        request,
                        status="result",
                        artifact_root=".",
                        artifact_sha256="0" * 64,
                        product={
                            "title": "Symlink",
                            "summary": "Attempts to smuggle another file.",
                            "lane": "moving-machines",
                        },
                    ),
                )

            client = ContributionHookClient(
                inventor,
                "custom-make",
                runner=self.fake_runner(attack),
                isolation=trusted_test_isolation,
            )
            with self.assertRaises(ArtifactError):
                client.make(context)

    def test_manager_rejects_forged_artifact_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor, _, context = self.fixture(temporary)

            def attack(request, response_path, cwd, env, command):
                del cwd, env, command
                workspace = Path(request["workspace"])
                workspace.mkdir()
                (workspace / "toy.txt").write_text("real bytes\n", encoding="utf-8")
                write_response(
                    response_path,
                    response_for(
                        request,
                        status="result",
                        artifact_root=".",
                        artifact_sha256="f" * 64,
                        product={
                            "title": "Forgery",
                            "summary": "Claims a digest for different bytes.",
                            "lane": "moving-machines",
                        },
                    ),
                )

            client = ContributionHookClient(
                inventor,
                "custom-make",
                runner=self.fake_runner(attack),
                isolation=trusted_test_isolation,
            )
            with self.assertRaisesRegex(ContractError, "different artifact bytes"):
                client.make(context)

    def test_manager_rejects_secret_content_and_silently_excluded_files(self):
        cases = (
            ("secret-content", {"design.txt": "sk-proj-" + "A" * 40}),
            ("excluded-file", {"design.txt": "safe\n", ".env": "HIDDEN=value\n"}),
        )
        for label, files in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                inventor, _, context = self.fixture(temporary)

                def attack(request, response_path, cwd, env, command):
                    del cwd, env, command
                    workspace = Path(request["workspace"])
                    workspace.mkdir()
                    for name, content in files.items():
                        (workspace / name).write_text(content, encoding="utf-8")
                    manifest = build_artifact_manifest(
                        workspace, created_at="content-addressed"
                    )
                    write_response(
                        response_path,
                        response_for(
                            request,
                            status="result",
                            artifact_root=".",
                            artifact_sha256=manifest.artifact_sha256,
                            product={
                                "title": "Excluded bytes",
                                "summary": "Contains content the Manager must reject.",
                                "lane": "moving-machines",
                            },
                        ),
                    )

                client = ContributionHookClient(
                    inventor,
                    "custom-make",
                    runner=self.fake_runner(attack),
                    isolation=trusted_test_isolation,
                )
                with self.assertRaises(ArtifactError):
                    client.make(context)

    def test_manager_rejects_response_symlink_and_digest_forgery(self):
        attacks = []

        def response_symlink(request, response_path, cwd, env, command):
            del cwd, env, command
            outside = response_path.parent.parent.parent / "outside-response.json"
            write_response(
                outside,
                response_for(
                    request,
                    status="waiting",
                    needs=[
                        {
                            "job": "make",
                            "capability": "outside",
                            "reason": "This response is outside the control directory.",
                            "instructions": "Reject the symlink.",
                        }
                    ],
                ),
            )
            response_path.symlink_to(outside)

        attacks.append(("regular file", response_symlink))

        def digest_forgery(request, response_path, cwd, env, command):
            del cwd, env, command
            response = response_for(
                request,
                status="waiting",
                needs=[
                    {
                        "job": "make",
                        "capability": "digest",
                        "reason": "The content identity is forged.",
                        "instructions": "Reject the response.",
                    }
                ],
            )
            response["response_sha256"] = "0" * 64
            write_response(response_path, response)

        attacks.append(("content identity changed", digest_forgery))

        for expected, attack in attacks:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temporary:
                inventor, _, context = self.fixture(temporary)
                client = ContributionHookClient(
                    inventor,
                    "custom-make",
                    runner=self.fake_runner(attack),
                    isolation=trusted_test_isolation,
                )
                with self.assertRaisesRegex(ContractError, expected):
                    client.make(context)

    def test_manager_rejects_request_hook_and_attempt_mutation(self):
        def request_mutation(request, response_path, cwd, env, command):
            del cwd, env
            request_path = Path(command[3])
            source = request_path.read_bytes()
            request_path.write_bytes(source.replace(b"tiny", b"evil", 1))
            write_response(
                response_path,
                response_for(
                    request,
                    status="waiting",
                    needs=[
                        {
                            "job": "make",
                            "capability": "mutated-request",
                            "reason": "The hook changed its request.",
                            "instructions": "Reject it.",
                        }
                    ],
                ),
            )

        def hook_mutation(request, response_path, cwd, env, command):
            del cwd, env
            Path(command[1]).write_text("raise SystemExit(0)\n", encoding="utf-8")
            write_response(
                response_path,
                response_for(
                    request,
                    status="waiting",
                    needs=[
                        {
                            "job": "make",
                            "capability": "mutated-hook",
                            "reason": "The hook changed its own bytes.",
                            "instructions": "Reject it.",
                        }
                    ],
                ),
            )

        def attempt_escape(request, response_path, cwd, env, command):
            del env, command
            (cwd / "stolen.txt").write_text("unexpected side output\n", encoding="utf-8")
            write_response(
                response_path,
                response_for(
                    request,
                    status="waiting",
                    needs=[
                        {
                            "job": "make",
                            "capability": "side-output",
                            "reason": "The hook wrote outside its output.",
                            "instructions": "Reject it.",
                        }
                    ],
                ),
            )

        cases = (
            ("mutated its exact request", request_mutation),
            ("changed while executing", hook_mutation),
            ("outside its reserved output", attempt_escape),
        )
        for expected, attack in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temporary:
                inventor, _, context = self.fixture(temporary)
                client = ContributionHookClient(
                    inventor,
                    "custom-make",
                    runner=self.fake_runner(attack),
                    isolation=trusted_test_isolation,
                )
                with self.assertRaisesRegex(ContractError, expected):
                    client.make(context)

    def test_custom_playtest_descriptor_cannot_switch_product_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor, _, make_context = self.fixture(
                temporary, level="custom-playtest"
            )
            product_root = Path(temporary).resolve() / "product"
            product_root.mkdir()
            (product_root / "toy.txt").write_text("product bytes\n", encoding="utf-8")
            made = Made.from_root(
                product_root,
                {
                    "title": "Exact toy",
                    "summary": "The product whose identity cannot be switched.",
                    "lane": "moving-machines",
                },
            )
            attempt = Path(temporary).resolve() / "playtest-attempt"
            attempt.mkdir(mode=0o700)
            os.chmod(attempt, 0o700)
            context = PlaytestContext(
                make_context.wish,
                make_context.taste,
                make_context.blueprint,
                1,
                made,
                attempt / "workspace",
                2,
            )

            def attack(request, response_path, cwd, env, command):
                del cwd, env, command
                write_response(
                    response_path,
                    response_for(
                        request,
                        status="result",
                        artifact_sha256="f" * 64,
                        evidence={
                            "source": "product",
                            "root": None,
                            "artifact_sha256": "f" * 64,
                        },
                        results=[],
                        cad_release=None,
                        feedback=[],
                    ),
                )

            client = ContributionHookClient(
                inventor,
                "custom-playtest",
                runner=self.fake_runner(attack),
                isolation=trusted_test_isolation,
            )
            with self.assertRaisesRegex(ContractError, "another Make"):
                client.playtest(context)

    def test_declared_level_is_exact_and_playtest_requires_custom_make(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor, _, make_context = self.fixture(temporary, level="custom-make")
            with self.assertRaisesRegex(ContractError, "exceeds its manifest"):
                ContributionHookClient(inventor, "custom-playtest")

            product_root = Path(temporary).resolve() / "product"
            product_root.mkdir()
            (product_root / "toy.txt").write_text("product bytes\n", encoding="utf-8")
            made = Made.from_root(
                product_root,
                {
                    "title": "Exact toy",
                    "summary": "A valid product for the declaration check.",
                    "lane": "moving-machines",
                },
            )
            attempt = Path(temporary).resolve() / "playtest-attempt"
            attempt.mkdir(mode=0o700)
            os.chmod(attempt, 0o700)
            playtest_context = PlaytestContext(
                make_context.wish,
                make_context.taste,
                make_context.blueprint,
                1,
                made,
                attempt / "workspace",
                2,
            )
            client = ContributionHookClient(inventor, "custom-make")
            with self.assertRaisesRegex(ContractError, "not declared"):
                client.playtest(playtest_context)


if __name__ == "__main__":
    unittest.main()
