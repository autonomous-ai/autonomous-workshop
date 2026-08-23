from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from alice.adapters import AdapterError, adapter_input_sha256
from alice.cli import _adapters
from alice.config import load_config
from alice.store import DurableStore, IdempotencyConflictError
from alice.vibe_pipeline import (
    ALICE_REVISION_BOUND_RELEASE_CAPABILITIES,
    LISTING_BOUND_PUBLISH_CAPABILITY,
    PUBLICATION_TARGET,
    RICH_PAGE_BOUND_PUBLISH_CAPABILITY,
    REVISION_BOUND_PUBLISH_CAPABILITY,
    AmbiguousVibeEffect,
    ExistingVibeDesignRequest,
    VibeHttpClient,
    VibePageIncomplete,
    VibePipeline,
    VibePipelineError,
    VibePipelineRequest,
    VibePublishingAdapter,
)


def complete_design(*, price_cents: int = 9_999) -> dict[str, object]:
    return {
        "id": "design-1",
        "slug": "arrows-across-the-river",
        "title": "Arrows Across the River",
        "description": "A complete strategy game.\n\nBy Alice.",
        "status": "public",
        "rich_page_complete": True,
        "current_history_id": "history-1",
        "published_history_id": "history-1",
        "category": {"slug": "games", "name": "Games"},
        "project_url": "https://cdn.example/project/",
        "project_sha256": "d" * 64,
        "primary_thumbnail_url": "https://cdn.example/hero.png",
        "thumbnail_urls": ["https://cdn.example/hero.png"],
        "listing": {
            "sku": "VB-1",
            "price_cents": price_cents,
            "currency": "USD",
            "active": True,
            "ships_within_days": 14,
        },
        "use_case": {
            "label": "At the table",
            "body": "A concrete player experience.",
            "image": "https://cdn.example/use.png",
        },
        "story_blocks": [
            {"lead": "One", "body": "Body", "hero_image": "https://cdn.example/1.png"},
            {"lead": "Two", "body": "Body", "hero_image": "https://cdn.example/2.png"},
            {"lead": "Three", "body": "Body", "hero_image": "https://cdn.example/3.png"},
        ],
        "print_specs": {
            "dimensions_mm": {"x": 200, "y": 200, "z": 60},
            "weight_g": 400,
            "print_time_minutes": 900,
            "part_count": 24,
            "materials": ["PETG"],
        },
        "assembly_parts": [{"part": "board.stl", "color": "#ffffff"}],
    }


class FakeTransport:
    def __init__(self, store: DurableStore) -> None:
        self.store = store
        self.create_calls: list[tuple[dict[str, object], str]] = []
        self.job_calls = 0
        self.message_calls: list[tuple[str, dict[str, object], str]] = []
        self.publish_calls: list[tuple[str, dict[str, object], str]] = []
        self.public_calls: list[str] = []
        self.capability_calls = 0
        self.design_calls: list[str] = []
        self.capability_values = frozenset(
            {
                REVISION_BOUND_PUBLISH_CAPABILITY,
                LISTING_BOUND_PUBLISH_CAPABILITY,
                RICH_PAGE_BOUND_PUBLISH_CAPABILITY,
            }
        )
        self.authenticated_design = {
            "id": "design-1",
            "slug": "arrows-across-the-river",
            "description": "A complete strategy game.\n\nBy Alice.",
            "status": "draft",
            "current_history_id": "history-1",
            "project_url": "https://cdn.example/project/",
            "project_sha256": "d" * 64,
        }
        self.echo_publish_binding = True
        self.echo_rich_page_binding = True
        self.publish_listing_override: dict[str, object] = {}
        self.jobs: list[dict[str, object]] = [
            {
                "id": "job-1",
                "status": "done",
                "result": {
                    "history_id": "history-1",
                    "project_url": "https://cdn.example/project/",
                },
            }
        ]
        self.public_designs: list[dict[str, object]] = [complete_design()]
        self.create_error: BaseException | None = None
        self.publish_error: BaseException | None = None

    def capabilities(self):
        self.capability_calls += 1
        return self.capability_values

    def get_design(self, slug_or_id):
        self.design_calls.append(slug_or_id)
        return dict(self.authenticated_design)

    def create_design(self, payload, *, operation_key):
        intent = self.store.get_publication_intent(PUBLICATION_TARGET, operation_key)
        assert intent is not None
        assert intent.state == "in_flight"
        assert intent.response["stage"] == "create_sending"
        self.create_calls.append((dict(payload), operation_key))
        if self.create_error is not None:
            raise self.create_error
        return {
            "job_id": "job-1",
            "design_id": "design-1",
            "slug": "arrows-across-the-river",
        }

    def get_job(self, job_id):
        self.job_calls += 1
        if len(self.jobs) > 1:
            return self.jobs.pop(0)
        return self.jobs[0]

    def send_job_message(self, job_id, payload, *, operation_key):
        self.message_calls.append((job_id, dict(payload), operation_key))
        return {"id": job_id, "status": "queued"}

    def publish_design(self, slug_or_id, payload, *, operation_key):
        root_key = operation_key.removesuffix(":publish")
        intent = self.store.get_publication_intent(PUBLICATION_TARGET, root_key)
        assert intent is not None
        assert intent.response["stage"] == "publish_sending"
        self.publish_calls.append((slug_or_id, dict(payload), operation_key))
        if self.publish_error is not None:
            raise self.publish_error
        response = complete_design(price_cents=payload["listing"]["price_cents"])
        response["listing"] = {
            **response["listing"],
            "sku": payload["listing"]["sku"],
            "currency": payload["listing"]["currency"],
            **self.publish_listing_override,
        }
        response["published_history_id"] = payload["expected_history_id"]
        response["current_history_id"] = payload["expected_history_id"]
        response["project_url"] = intent.response["project_url"]
        if self.echo_publish_binding:
            response["packet_hash"] = payload["packet_hash"]
            response["policy_hash"] = payload["policy_hash"]
        if not self.echo_rich_page_binding:
            response.pop("rich_page_complete", None)
        return response

    def get_public_design(self, slug_or_id):
        self.public_calls.append(slug_or_id)
        if len(self.public_designs) > 1:
            return self.public_designs.pop(0)
        return self.public_designs[0]


class _Response:
    def __init__(self, payload) -> None:
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class VibePipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.store = DurableStore(Path(self.temporary.name) / "alice.sqlite3")
        self.candidate_content = {"brief": "river game — Cà phê"}
        self.candidate_content_sha256 = self.store.sha256_json(
            self.candidate_content
        )
        self.policy_hash = "b" * 64
        self.artifact_manifest_sha256 = "a" * 64
        self.vibe_design = {
            "design_id": "design-1",
            "slug": "arrows-across-the-river",
            "history_id": "history-1",
            "project_url": "https://cdn.example/project/",
            "project_sha256": "d" * 64,
            "artifact_hashes": {"artifact_hash": "e" * 64},
        }
        self.production_manifest = {
            "candidate_id": "candidate-1",
            "candidate_version": 1,
            "candidate_content_sha256": self.candidate_content_sha256,
            "manufacturing": {"vibe_design": self.vibe_design},
            "price": {"price_cents": 9_999, "currency": "USD"},
            "listing": {"sku": "VB-1"},
        }
        self.packet_hash = self.store.sha256_json(self.production_manifest)
        self.metadata_release_decision = {
            "allowed": True,
            "effect_mode": "live",
            "candidate_id": "candidate-1",
            "candidate_version": 1,
            "release_candidate_version": 1,
            "production_candidate_version": 1,
            "production_packet_hash": self.packet_hash,
            "reviewed_packet_hash": self.packet_hash,
            "policy_hash": self.policy_hash,
            "artifact_manifest_sha256": self.artifact_manifest_sha256,
            "production_manifest": self.production_manifest,
        }
        candidate = self.store.create_candidate(
            self.candidate_content,
            candidate_id="candidate-1",
            state="production_validated",
        )
        self.candidate = self.store.transition_candidate(
            candidate.id,
            "publish_ready",
            expected_state="production_validated",
            expected_version=candidate.version,
            metadata_patch={"release_decision": self.metadata_release_decision},
        )
        self.release_decision = {
            "allowed": True,
            "effect_mode": "live",
            "candidate_id": self.candidate.id,
            "release_candidate_version": self.candidate.version - 1,
            "publish_candidate_version": self.candidate.version,
            "production_candidate_version": 1,
            "production_packet_hash": self.packet_hash,
            "reviewed_packet_hash": self.packet_hash,
            "policy_hash": self.policy_hash,
            "artifact_manifest_sha256": self.artifact_manifest_sha256,
        }
        self.transport = FakeTransport(self.store)
        self.transport.public_designs[0]["packet_hash"] = self.packet_hash
        self.transport.public_designs[0]["policy_hash"] = self.policy_hash

    def tearDown(self) -> None:
        self.store.close()
        self.temporary.cleanup()

    def request(self, **changes: object) -> VibePipelineRequest:
        values: dict[str, object] = {
            "operation_key": "alice:vibe:1",
            "candidate_id": self.candidate.id,
            "packet_hash": "a" * 64,
            "prompt": "Build the approved river-crossing board game.",
            "category": "games",
            "price_cents": 9_999,
            "tags": ("board-game", "strategy"),
        }
        values.update(changes)
        return VibePipelineRequest(**values)  # type: ignore[arg-type]

    def pipeline(self, **changes: object) -> VibePipeline:
        values: dict[str, object] = {
            "poll_interval_seconds": 0,
            "max_job_polls": 5,
            "max_page_polls": 5,
            "sleep": lambda _: None,
        }
        values.update(changes)
        return VibePipeline(self.store, self.transport, **values)  # type: ignore[arg-type]

    def existing_request(self, **changes: object) -> ExistingVibeDesignRequest:
        values: dict[str, object] = {
            "operation_key": "alice:vibe:existing:1",
            "candidate_id": self.candidate.id,
            "candidate_version": self.candidate.version,
            "candidate_content_sha256": self.candidate_content_sha256,
            "packet_hash": self.packet_hash,
            "production_packet_hash": self.packet_hash,
            "reviewed_packet_hash": self.packet_hash,
            "policy_hash": self.policy_hash,
            "production_candidate_version": 1,
            "production_manifest": self.production_manifest,
            "design_id": "design-1",
            "slug": "arrows-across-the-river",
            "history_id": "history-1",
            "project_url": "https://cdn.example/project/",
            "project_sha256": "d" * 64,
            "price_cents": 9_999,
            "release_decision": self.release_decision,
            "artifact_hashes": {"artifact_hash": "e" * 64},
        }
        values.update(changes)
        return ExistingVibeDesignRequest(**values)  # type: ignore[arg-type]

    def adapter_payload(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate.id,
            "candidate_version": self.candidate.version,
            "candidate": self.candidate.content,
            "candidate_content_sha256": self.candidate_content_sha256,
            "candidate_metadata": dict(self.candidate.metadata),
            "dependencies": {
                "publish.packet": {
                    "result": {
                        "executor": "release_policy",
                        "content": {
                            "publication_packet": self.production_manifest,
                            "packet_hash": self.packet_hash,
                            "policy_hash": self.policy_hash,
                            "release_decision": self.release_decision,
                        },
                    }
                }
            },
        }

    def test_create_flow_builds_but_cannot_cross_the_release_boundary(self) -> None:
        with self.assertRaisesRegex(VibePipelineError, "not production-bound"):
            self.pipeline().run(self.request())
        self.assertEqual(
            self.transport.create_calls[0][0],
            {
                "prompt": "Build the approved river-crossing board game.",
                "category": "games",
                "tags": ["board-game", "strategy"],
                "auto_build": True,
                "concept_phase": True,
            },
        )
        self.assertEqual(self.transport.publish_calls, [])
        stored = self.store.get_publication_intent(PUBLICATION_TARGET, "alice:vibe:1")
        assert stored is not None
        self.assertEqual(stored.state, "failed")
        self.assertEqual(stored.request["operation_key"], "alice:vibe:1")
        self.assertEqual(stored.response["operation_key"], "alice:vibe:1")

    def test_existing_verified_design_publishes_without_regeneration(self) -> None:
        request = self.existing_request()

        receipt = self.pipeline().publish_existing(request)

        self.assertEqual(receipt.status, "complete")
        self.assertEqual(receipt.packet_hash, self.packet_hash)
        self.assertEqual(receipt.pipeline_run_id, "history-1")
        self.assertEqual(self.transport.create_calls, [])
        self.assertEqual(self.transport.job_calls, 0)
        self.assertEqual(
            self.transport.publish_calls,
            [
                (
                    "arrows-across-the-river",
                    {
                        "listing": {
                            "price_cents": 9_999,
                            "sku": "VB-1",
                            "currency": "USD",
                        },
                        "expected_history_id": "history-1",
                        "packet_hash": self.packet_hash,
                        "policy_hash": self.policy_hash,
                        "project_sha256": "d" * 64,
                        "preconditions": {
                            "rich_page_complete": True,
                            "history_id": "history-1",
                            "project_sha256": "d" * 64,
                        },
                    },
                    "alice:vibe:existing:1:publish",
                )
            ],
        )
        stored = self.store.get_publication_intent(
            PUBLICATION_TARGET, "alice:vibe:existing:1"
        )
        assert stored is not None
        self.assertEqual(stored.history_id, "history-1")
        self.assertEqual(stored.project_url, "https://cdn.example/project/")

    def test_missing_revision_capability_fails_before_publish(self) -> None:
        self.transport.capability_values = frozenset()

        with self.assertRaisesRegex(VibePipelineError, "revision/listing"):
            self.pipeline().publish_existing(self.existing_request())

        self.assertEqual(self.transport.publish_calls, [])
        self.assertEqual(self.transport.design_calls, [])

    def test_each_atomic_public_boundary_capability_is_required(self) -> None:
        all_capabilities = {
            REVISION_BOUND_PUBLISH_CAPABILITY,
            LISTING_BOUND_PUBLISH_CAPABILITY,
            RICH_PAGE_BOUND_PUBLISH_CAPABILITY,
        }
        for missing in sorted(all_capabilities):
            with self.subTest(missing=missing):
                self.transport.capability_values = frozenset(
                    all_capabilities - {missing}
                )
                request = self.existing_request(
                    operation_key=f"alice:vibe:missing:{missing}"
                )
                with self.assertRaisesRegex(VibePipelineError, "missing"):
                    self.pipeline().publish_existing(request)
                self.assertEqual(self.transport.publish_calls, [])

    def test_release_capabilities_are_exposed_only_for_bound_backend(self) -> None:
        adapter = VibePublishingAdapter(self.pipeline())

        self.assertEqual(
            adapter.release_capabilities(),
            ALICE_REVISION_BOUND_RELEASE_CAPABILITIES,
        )
        self.transport.capability_values = frozenset()
        self.assertEqual(adapter.release_capabilities(), ())
        with patch.object(
            self.transport, "capabilities", side_effect=RuntimeError("offline")
        ):
            self.assertEqual(adapter.release_capabilities(), ())

    def test_release_capabilities_fail_closed_on_malformed_read(self) -> None:
        adapter = VibePublishingAdapter(self.pipeline())
        with patch.object(self.transport, "capabilities", return_value=None):
            self.assertEqual(adapter.release_capabilities(), ())

    def test_stale_candidate_version_fails_before_remote_preflight(self) -> None:
        stale_decision = dict(self.release_decision)
        stale_decision["release_candidate_version"] = self.candidate.version
        stale_decision["publish_candidate_version"] = self.candidate.version + 1
        with self.assertRaisesRegex(VibePipelineError, "stale"):
            self.pipeline().publish_existing(
                self.existing_request(
                    candidate_version=self.candidate.version + 1,
                    release_decision=stale_decision,
                )
            )

        self.assertEqual(self.transport.capability_calls, 0)
        self.assertEqual(self.transport.publish_calls, [])

    def test_authenticated_history_mismatch_fails_before_publish(self) -> None:
        self.transport.authenticated_design["current_history_id"] = "newer-history"

        with self.assertRaisesRegex(VibePipelineError, "current_history_id mismatch"):
            self.pipeline().publish_existing(self.existing_request())

        self.assertEqual(self.transport.publish_calls, [])

    def test_project_hash_mismatch_fails_before_publish(self) -> None:
        self.transport.authenticated_design["project_sha256"] = "f" * 64

        with self.assertRaisesRegex(VibePipelineError, "project_sha256 mismatch"):
            self.pipeline().publish_existing(self.existing_request())

        self.assertEqual(self.transport.publish_calls, [])

    def test_authenticated_description_attribution_fails_before_publish(self) -> None:
        self.transport.authenticated_design["description"] = (
            "A complete strategy game.\n\nBy Alice. "
        )

        with self.assertRaisesRegex(VibePipelineError, "exact attribution"):
            self.pipeline().publish_existing(self.existing_request())

        self.assertEqual(self.transport.publish_calls, [])

    def test_missing_revision_echo_is_ambiguous_and_not_retried(self) -> None:
        self.transport.echo_publish_binding = False

        with self.assertRaisesRegex(AmbiguousVibeEffect, "packet hash"):
            self.pipeline().publish_existing(self.existing_request())
        with self.assertRaises(AmbiguousVibeEffect):
            self.pipeline().publish_existing(self.existing_request())

        self.assertEqual(len(self.transport.publish_calls), 1)

    def test_missing_atomic_rich_page_echo_is_ambiguous_and_not_retried(self) -> None:
        self.transport.echo_rich_page_binding = False

        with self.assertRaisesRegex(AmbiguousVibeEffect, "rich-page precondition"):
            self.pipeline().publish_existing(self.existing_request())
        with self.assertRaises(AmbiguousVibeEffect):
            self.pipeline().publish_existing(self.existing_request())

        self.assertEqual(len(self.transport.publish_calls), 1)

    def test_publish_receipt_must_echo_exact_sku_and_usd_currency(self) -> None:
        self.transport.publish_listing_override = {
            "sku": "OTHER-SKU",
            "currency": "EUR",
        }
        with self.assertRaisesRegex(AmbiguousVibeEffect, "exact revision"):
            self.pipeline().publish_existing(self.existing_request())

    def test_public_postflight_requires_the_bound_published_history(self) -> None:
        wrong = complete_design()
        wrong["published_history_id"] = "other-history"
        self.transport.public_designs = [wrong]

        with self.assertRaises(VibePageIncomplete):
            self.pipeline(max_page_polls=1).publish_existing(
                self.existing_request()
            )

        self.assertEqual(len(self.transport.publish_calls), 1)
        stored = self.store.get_publication_intent(
            PUBLICATION_TARGET, "alice:vibe:existing:1"
        )
        assert stored is not None
        self.assertEqual(stored.state, "in_flight")
        self.assertEqual(stored.response["stage"], "public_waiting")

    def test_worker_adapter_publishes_packet_bound_existing_design(self) -> None:
        adapter = VibePublishingAdapter(self.pipeline())
        payload = self.adapter_payload()

        invoked = adapter.invoke("publish.invoke_pipeline", payload)
        page_ready = self.store.transition_candidate(
            self.candidate.id,
            "page_ready",
            expected_state="publish_ready",
            expected_version=self.candidate.version,
        )
        verified = adapter.invoke(
            "publish.verify_page",
            {
                "candidate_id": page_ready.id,
                "candidate_version": page_ready.version,
                "candidate": page_ready.content,
                "candidate_content_sha256": self.store.sha256_json(
                    page_ready.content
                ),
                "candidate_metadata": dict(page_ready.metadata),
                "dependencies": {},
            },
        )

        expected_hash = payload["dependencies"]["publish.packet"]["result"]["content"]["packet_hash"]  # type: ignore[index]
        self.assertEqual(invoked.status, "passed")
        self.assertEqual(
            invoked.input_sha256,
            adapter_input_sha256("publish.invoke_pipeline", payload),
        )
        self.assertEqual(invoked.payload["packet_hash"], expected_hash)
        self.assertEqual(verified.status, "passed")
        self.assertEqual(verified.payload["packet_hash"], expected_hash)
        self.assertEqual(self.transport.create_calls, [])
        self.assertEqual(self.transport.job_calls, 0)

    def test_worker_adapter_rejects_a_forged_packet_hash_before_publish(self) -> None:
        adapter = VibePublishingAdapter(self.pipeline())
        payload = self.adapter_payload()
        content = payload["dependencies"]["publish.packet"]["result"]["content"]  # type: ignore[index]
        content["packet_hash"] = "f" * 64  # type: ignore[index]

        with self.assertRaisesRegex(AdapterError, "hash does not match"):
            adapter.invoke("publish.invoke_pipeline", payload)

        self.assertEqual(self.transport.publish_calls, [])

    def test_worker_adapter_rejects_agent_packet_envelope_before_publish(self) -> None:
        adapter = VibePublishingAdapter(self.pipeline())
        payload = self.adapter_payload()
        dependency = payload["dependencies"]["publish.packet"]  # type: ignore[index]
        canonical_content = dependency["result"]["content"]  # type: ignore[index]
        dependency["result"] = {  # type: ignore[index]
            "executor": "agent",
            "response": {"content": canonical_content},
        }

        with self.assertRaisesRegex(AdapterError, "release_policy"):
            adapter.invoke("publish.invoke_pipeline", payload)

        self.assertEqual(self.transport.capability_calls, 0)
        self.assertEqual(self.transport.publish_calls, [])

    def test_worker_adapter_rejects_packet_for_another_candidate_version(self) -> None:
        adapter = VibePublishingAdapter(self.pipeline())
        payload = self.adapter_payload()
        content = payload["dependencies"]["publish.packet"]["result"]["content"]  # type: ignore[index]
        packet = content["publication_packet"]  # type: ignore[index]
        packet["candidate_version"] = self.candidate.version + 1  # type: ignore[index]
        content["packet_hash"] = self.store.sha256_json(packet)  # type: ignore[index]

        with self.assertRaisesRegex(AdapterError, "hashes do not match|candidate_version"):
            adapter.invoke("publish.invoke_pipeline", payload)

        self.assertEqual(self.transport.publish_calls, [])

    def test_worker_adapter_rejects_disallowed_release_decision(self) -> None:
        adapter = VibePublishingAdapter(self.pipeline())
        payload = self.adapter_payload()
        content = payload["dependencies"]["publish.packet"]["result"]["content"]  # type: ignore[index]
        decision = dict(content["release_decision"])  # type: ignore[index]
        decision["allowed"] = False
        content["release_decision"] = decision  # type: ignore[index]

        with self.assertRaisesRegex(AdapterError, "not allowed"):
            adapter.invoke("publish.invoke_pipeline", payload)

        self.assertEqual(self.transport.publish_calls, [])

    def test_worker_adapter_rejects_non_live_release_before_publish(self) -> None:
        adapter = VibePublishingAdapter(self.pipeline())
        payload = self.adapter_payload()
        content = payload["dependencies"]["publish.packet"]["result"]["content"]  # type: ignore[index]
        decision = dict(content["release_decision"])  # type: ignore[index]
        decision["effect_mode"] = "draft"
        content["release_decision"] = decision  # type: ignore[index]

        with self.assertRaisesRegex(AdapterError, "effect_mode mismatch"):
            adapter.invoke("publish.invoke_pipeline", payload)

        self.assertEqual(self.transport.capability_calls, 0)
        self.assertEqual(self.transport.publish_calls, [])

    def test_worker_adapter_rejects_stale_release_version_before_publish(self) -> None:
        adapter = VibePublishingAdapter(self.pipeline())
        payload = self.adapter_payload()
        content = payload["dependencies"]["publish.packet"]["result"]["content"]  # type: ignore[index]
        decision = dict(content["release_decision"])  # type: ignore[index]
        decision["release_candidate_version"] = 0
        content["release_decision"] = decision  # type: ignore[index]

        with self.assertRaisesRegex(AdapterError, "release_candidate_version mismatch"):
            adapter.invoke("publish.invoke_pipeline", payload)

        self.assertEqual(self.transport.capability_calls, 0)
        self.assertEqual(self.transport.publish_calls, [])

    def test_worker_adapter_rejects_release_for_another_candidate(self) -> None:
        adapter = VibePublishingAdapter(self.pipeline())
        payload = self.adapter_payload()
        content = payload["dependencies"]["publish.packet"]["result"]["content"]  # type: ignore[index]
        decision = dict(content["release_decision"])  # type: ignore[index]
        decision["candidate_id"] = "candidate-elsewhere"
        content["release_decision"] = decision  # type: ignore[index]

        with self.assertRaisesRegex(AdapterError, "release decision candidate_id mismatch"):
            adapter.invoke("publish.invoke_pipeline", payload)

        self.assertEqual(self.transport.capability_calls, 0)
        self.assertEqual(self.transport.publish_calls, [])

    def test_verify_rejects_a_newer_public_history_without_republishing(self) -> None:
        adapter = VibePublishingAdapter(self.pipeline())
        adapter.invoke("publish.invoke_pipeline", self.adapter_payload())
        page_ready = self.store.transition_candidate(
            self.candidate.id,
            "page_ready",
            expected_state="publish_ready",
            expected_version=self.candidate.version,
        )
        newer = complete_design()
        newer["published_history_id"] = "history-newer"
        self.transport.public_designs = [newer]

        with self.assertRaisesRegex(AdapterError, "not the revision bound"):
            adapter.invoke(
                "publish.verify_page",
                {
                    "candidate_id": page_ready.id,
                    "candidate_version": page_ready.version,
                    "candidate": page_ready.content,
                    "candidate_content_sha256": self.store.sha256_json(
                        page_ready.content
                    ),
                    "candidate_metadata": dict(page_ready.metadata),
                    "dependencies": {},
                },
            )

        self.assertEqual(len(self.transport.publish_calls), 1)

    def test_same_operation_key_with_changed_price_is_a_conflict(self) -> None:
        with self.assertRaises(VibePipelineError):
            self.pipeline().run(self.request())
        with self.assertRaises(IdempotencyConflictError):
            self.pipeline().run(self.request(price_cents=10_999))
        self.assertEqual(len(self.transport.publish_calls), 0)

    def test_same_operation_key_cannot_be_rebound_to_another_packet(self) -> None:
        with self.assertRaises(VibePipelineError):
            self.pipeline().run(self.request())
        with self.assertRaises(IdempotencyConflictError):
            self.pipeline().run(self.request(packet_hash="b" * 64))
        self.assertEqual(len(self.transport.publish_calls), 0)

    def test_packet_hash_is_validated_before_any_intent_or_effect(self) -> None:
        with self.assertRaises(ValueError):
            self.request(packet_hash="not-a-sha256")
        self.assertIsNone(
            self.store.get_publication_intent(PUBLICATION_TARGET, "alice:vibe:1")
        )
        self.assertEqual(self.transport.create_calls, [])

    def test_ambiguous_create_is_durable_and_never_retried(self) -> None:
        self.transport.create_error = TimeoutError("lost response")
        with self.assertRaises(AmbiguousVibeEffect):
            self.pipeline().run(self.request())
        stored = self.store.get_publication_intent(PUBLICATION_TARGET, "alice:vibe:1")
        assert stored is not None
        self.assertEqual(stored.state, "ambiguous")
        self.assertEqual(stored.response["ambiguous_stage"], "create_sending")

        with self.assertRaises(AmbiguousVibeEffect):
            self.pipeline().run(self.request())
        self.assertEqual(len(self.transport.create_calls), 1)

    def test_ambiguous_publish_is_durable_and_never_retried(self) -> None:
        self.transport.publish_error = TimeoutError("lost response")
        with self.assertRaises(AmbiguousVibeEffect):
            self.pipeline().publish_existing(self.existing_request())
        stored = self.store.get_publication_intent(
            PUBLICATION_TARGET, "alice:vibe:existing:1"
        )
        assert stored is not None
        self.assertEqual(stored.state, "ambiguous")
        self.assertEqual(stored.response["ambiguous_stage"], "publish_sending")
        with self.assertRaises(AmbiguousVibeEffect):
            self.pipeline().publish_existing(self.existing_request())
        self.assertEqual(len(self.transport.publish_calls), 1)

    def test_existing_publish_has_one_durable_sender(self) -> None:
        request = self.existing_request()
        intent = request.durable_request()
        record = self.store.prepare_publication(
            PUBLICATION_TARGET,
            request.operation_key,
            self.store.sha256_json(intent),
            intent,
            candidate_id=request.candidate_id,
            slug=request.slug,
        )
        self.store.put_state(
            (
                f"alice.effect:candidate:{request.candidate_id}:"
                f"v{request.candidate_version}:publish"
            ),
            {
                "publication_id": record.id,
                "payload_sha256": "f" * 64,
                "status": "sending",
            },
            None,
        )

        with self.assertRaisesRegex(AmbiguousVibeEffect, "sender claim"):
            self.pipeline().publish_existing(request)

        self.assertEqual(self.transport.publish_calls, [])

    def test_candidate_retraction_during_preflight_stops_public_write(self) -> None:
        original_get_design = self.transport.get_design

        def get_design_and_retract(slug_or_id):
            result = original_get_design(slug_or_id)
            current = self.store.get_candidate(self.candidate.id)
            self.store.transition_candidate(
                current.id,
                "rework",
                expected_state="publish_ready",
                expected_version=current.version,
            )
            return result

        self.transport.get_design = get_design_and_retract

        with self.assertRaisesRegex(
            VibePipelineError, "retracted or revised before the public write"
        ):
            self.pipeline().publish_existing(self.existing_request())

        self.assertEqual(self.transport.publish_calls, [])

    def test_concept_pause_uses_the_supported_message_endpoint(self) -> None:
        self.transport.jobs = [
            {"id": "job-1", "status": "awaiting_concept_selection"},
            {
                "id": "job-1",
                "status": "done",
                "result": {
                    "history_id": "history-1",
                    "project_url": "https://cdn.example/project/",
                },
            },
        ]
        with self.assertRaisesRegex(VibePipelineError, "not production-bound"):
            self.pipeline().run(
                self.request(), pause_handler=lambda _: {"set_id": "a"}
            )
        self.assertEqual(
            self.transport.message_calls,
            [("job-1", {"set_id": "a"}, "alice:vibe:1:pause:1")],
        )

    def test_incomplete_public_page_resumes_only_anonymous_observation(self) -> None:
        incomplete = complete_design()
        incomplete["story_blocks"] = []
        incomplete["packet_hash"] = self.packet_hash
        incomplete["policy_hash"] = self.policy_hash
        self.transport.public_designs = [incomplete]
        pipeline = self.pipeline(max_page_polls=1)
        with self.assertRaises(VibePageIncomplete) as raised:
            pipeline.publish_existing(self.existing_request())
        self.assertIn("story_blocks_below_three", raised.exception.verification.failures)
        stored = self.store.get_publication_intent(
            PUBLICATION_TARGET, "alice:vibe:existing:1"
        )
        assert stored is not None
        self.assertEqual(stored.state, "in_flight")
        self.assertEqual(stored.response["stage"], "public_waiting")

        complete = complete_design()
        complete["packet_hash"] = self.packet_hash
        complete["policy_hash"] = self.policy_hash
        self.transport.public_designs = [complete]
        receipt = pipeline.publish_existing(self.existing_request())
        self.assertEqual(receipt.status, "complete")
        self.assertEqual(len(self.transport.create_calls), 0)
        self.assertEqual(len(self.transport.publish_calls), 1)

    def test_http_public_observer_is_anonymous_and_writes_carry_key(self) -> None:
        client = VibeHttpClient("https://vibe.example", "top-secret")
        with patch.object(
            client._opener,
            "open",
            side_effect=[_Response({"id": "design-1"}), _Response({"job_id": "job-1"})],
        ) as opened:
            client.get_public_design("design-1")
            client.create_design({"prompt": "build"}, operation_key="caller-key-1")

        public_request = opened.call_args_list[0].args[0]
        write_request = opened.call_args_list[1].args[0]
        self.assertFalse(public_request.has_header("Authorization"))
        self.assertEqual(
            public_request.full_url,
            "https://vibe.example/api/v1/designs/design-1",
        )
        self.assertEqual(write_request.get_header("Authorization"), "Bearer top-secret")
        self.assertEqual(write_request.get_header("Idempotency-key"), "caller-key-1")
        self.assertEqual(write_request.get_header("X-alice-operation-key"), "caller-key-1")
        self.assertEqual(json.loads(write_request.data), {"prompt": "build"})
        self.assertNotIn("top-secret", repr(client))

    def test_authenticated_http_client_requires_clean_https_origin(self) -> None:
        for value in (
            "http://vibe.example",
            "https://user:secret@vibe.example",
            "https://vibe.example?redirect=elsewhere",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    VibeHttpClient(value, "top-secret")

    def test_cli_can_select_the_builtin_vibe_adapter(self) -> None:
        config = load_config()
        config["adapters"]["vibe"]["enabled"] = True
        config["runtime"]["effect_mode"] = "live"
        with patch.dict("os.environ", {"ALICE_FACTORY_TOKEN": "dedicated-token"}):
            adapters = _adapters(config, self.store)
        self.assertIsInstance(adapters["publishing_pipeline"], VibePublishingAdapter)


if __name__ == "__main__":
    unittest.main()
