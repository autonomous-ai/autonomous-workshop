import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tests.end_to_end.test_native_full_run import (
    _OneSessionProductAgent,
    _sha256,
)
from tests.integrations.test_factory import FactoryTransport
from workshop.integrations.factory import (
    FactoryAgentCredentials,
    FactoryAgentSession,
)
from workshop.make.native_gate import (
    NATIVE_CAD_FULL_TIER,
    NATIVE_CAD_VERIFIER_MODE,
)
from workshop.runtime import EffectLedger, Receipt
from workshop.wish import Wish
from workshop.workflow.native_run import (
    native_run_paths,
    native_run_status,
    resume_native_run,
    start_native_run,
)


class _UnknownPublishTransport(FactoryTransport):
    def __init__(self, product_id):
        super().__init__(product_id=product_id, include_thumbnails=False)
        self.publish_attempts = 0

    def __call__(self, method, url, headers, body, timeout):
        if method == "POST" and url.endswith("/publish"):
            self.calls.append((method, url, dict(headers), body, timeout))
            self.publish_attempts += 1
            raise RuntimeError("connection lost after publication send")
        return super().__call__(method, url, headers, body, timeout)


class NativePublicationReconciliationTest(unittest.TestCase):
    def test_unknown_publish_overrides_local_draft_and_retry_does_not_resend(self):
        launcher = _OneSessionProductAgent()
        product_id = "orbit-dog-unknown-publication"
        transport = _UnknownPublishTransport(product_id)
        credentials = FactoryAgentCredentials("alice", "fixture-secret")

        def verify_cad(made, **arguments):
            return SimpleNamespace(
                passed=True,
                receipt_sha256=_sha256(made.made_sha256.encode("ascii")),
                verifier_sha256=arguments["expected_verifier_sha256"],
                verifier_mode=NATIVE_CAD_VERIFIER_MODE,
                verification_tier=NATIVE_CAD_FULL_TIER,
                thickness_gate_required=True,
                print_ready_eligible=True,
            )

        def writer(unused_ledger, inventor_id, observed_credentials):
            self.assertEqual(inventor_id, "alice")
            self.assertIs(observed_credentials, credentials)

            def write(context, unused_root, manifest):
                transport.manual_bytes = (unused_root / "MANUAL.pdf").read_bytes()
                entries = {entry.path: entry for entry in manifest.entries}
                return Receipt(
                    payload_sha256=_sha256(b"exact-factory-handoff"),
                    artifact_sha256=context.made.artifact_sha256,
                    adapter="factory",
                    status="draft",
                    observed_at="2026-08-27T00:00:00+00:00",
                    reference="design-1",
                    details={
                        "product_id": product_id,
                        "release_sha256": manifest.artifact_sha256,
                        "playtest_evidence_sha256": (
                            context.playtested.evidence.evidence_artifact_sha256
                        ),
                        "handoff_artifact_sha256": _sha256(
                            b"exact-factory-handoff"
                        ),
                        "product_page_sha256": entries["product.json"].sha256,
                        "manual_path": "MANUAL.pdf",
                        "manual_sha256": entries["MANUAL.pdf"].sha256,
                        "manual_url": (
                            "https://cdn.autonomous.ai/projects/history-1/"
                            "MANUAL.pdf"
                        ),
                        "manual_readback_sha256": entries["MANUAL.pdf"].sha256,
                        "page_url": (
                            "https://www.autonomous.ai/factory/product/"
                            + product_id
                        ),
                    },
                    design_id="design-1",
                    slug=product_id,
                    owner_id="owner-alice",
                    root_id="design-1",
                    current_history_id="history-1",
                    published_history_id=None,
                    project_url="https://cdn.autonomous.ai/projects/history-1/",
                )

            return write

        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            wish = Wish.create(
                product_id,
                "Build a pocket draughts set inspired by my orbit-loving dog.",
                constraints={
                    "audience": "14+",
                    "manufacture": "not-authorized",
                },
                context={"source": "unknown-publication-test"},
            )
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "workshop.workflow.native_run.verify_native_made_cad",
                side_effect=verify_cad,
            ), mock.patch(
                "workshop.workflow.native_run._factory_credentials",
                return_value=credentials,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryReleaseWriter",
                side_effect=writer,
            ), mock.patch(
                "workshop.workflow.native_run.FactoryAgentSession",
                side_effect=lambda value: FactoryAgentSession(
                    value, transport=transport
                ),
            ):
                started = start_native_run(wish)
                inspected = native_run_status(product_id)
                retried = resume_native_run(product_id)
                paths = native_run_paths(product_id)
                effect = Receipt.from_dict(
                    json.loads(
                        (paths.host_state / "release-effect.json").read_text(
                            encoding="utf-8"
                        )
                    )["receipt"]
                )
                intent = EffectLedger.inspect_latest(
                    paths.host_state / "factory-effects.sqlite3",
                    product_id,
                    "factory-publish",
                )

        self.assertTrue(effect.is_verified_draft)
        self.assertIsNotNone(intent)
        self.assertEqual(intent.state, "unknown")
        self.assertEqual(transport.publish_attempts, 1)
        for receipt in (started, inspected, retried):
            self.assertEqual(receipt["publication"]["status"], "unknown")
            self.assertFalse(receipt["publication"]["verified"])
            self.assertIn("reconciliation", receipt["publication"]["reason"])
            self.assertNotIn("fixture-secret", repr(receipt))
        self.assertEqual(retried["action"], "publication-unverified")
        self.assertEqual(started["native_turns"], retried["native_turns"])


if __name__ == "__main__":
    unittest.main()
