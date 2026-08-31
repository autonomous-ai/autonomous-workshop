import tempfile
import unittest
from pathlib import Path

from workshop.errors import StateConflict
from workshop.runtime.concept_effects import ConceptEffectLedger


class ConceptEffectLedgerTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.ledger = ConceptEffectLedger(Path(temporary.name) / "effects.sqlite3")
        self.bindings = {
            "product_id": "moon-lamp",
            "checkpoint_sha256": "1" * 64,
            "subject_sha256": "2" * 64,
            "pre_render_sha256": "3" * 64,
            "source_manifest_sha256": "4" * 64,
        }

    def identity(self, role="front", references=()):
        return {
            **self.bindings,
            "role": role,
            "output_path": "images/%s.png" % role,
            "instruction_sha256": "5" * 64,
            "references": list(references),
            "profile_id": "openrouter-images-v1",
            "profile_sha256": "6" * 64,
            "model": "openai/gpt-image-2",
            "request_schema_version": "openrouter-images-v1",
        }

    def test_role_transitions_are_token_fenced_and_idempotent(self):
        aggregate = self.ledger.prepare_aggregate(
            **self.bindings, required_roles=("front",)
        )
        first = self.ledger.prepare_role(
            aggregate_id=aggregate, identity=self.identity()
        )
        self.assertEqual(
            self.ledger.prepare_role(
                aggregate_id=aggregate, identity=self.identity()
            ).intent_id,
            first.intent_id,
        )
        sending = self.ledger.begin(first.intent_id)
        with self.assertRaises(StateConflict):
            self.ledger.finish(
                first.intent_id,
                "stale",
                state="succeeded",
                response={"image_sha256": "7" * 64},
            )
        succeeded = self.ledger.finish(
            first.intent_id,
            sending.effect_token,
            state="succeeded",
            response={"image_sha256": "7" * 64},
        )
        self.assertEqual(succeeded.state, "succeeded")
        self.assertEqual(
            [item["state"] for item in self.ledger.audit(first.intent_id)],
            ["planned", "sending", "succeeded"],
        )
        self.ledger.mark_aggregate_succeeded(
            aggregate, observed={"front": "7" * 64}
        )

    def test_unknown_cannot_be_reopened_and_partial_aggregate_cannot_pass(self):
        aggregate = self.ledger.prepare_aggregate(
            **self.bindings, required_roles=("front", "top")
        )
        operation = self.ledger.prepare_role(
            aggregate_id=aggregate, identity=self.identity()
        )
        sending = self.ledger.begin(operation.intent_id)
        self.ledger.finish(
            operation.intent_id,
            sending.effect_token,
            state="unknown",
            response={"provider_operation_id": "provider-1"},
            error_code="ambiguous-after-transmission",
        )
        with self.assertRaises(StateConflict):
            self.ledger.begin(operation.intent_id)
        with self.assertRaises(StateConflict):
            self.ledger.mark_aggregate_succeeded(
                aggregate, observed={"front": "7" * 64}
            )
        planned = self.ledger.reconcile_unknown(
            operation.intent_id,
            "provider-1",
            state="planned",
            error_code="authenticated-absence",
        )
        self.assertEqual(planned.state, "planned")
        self.assertEqual(
            [item["state"] for item in self.ledger.audit(operation.intent_id)],
            ["planned", "sending", "unknown", "planned"],
        )

    def test_definitive_rejections_reopen_but_unknown_never_does(self):
        aggregate = self.ledger.prepare_aggregate(
            **self.bindings, required_roles=("front",)
        )
        for error_code in ("pre-transmission", "provider-rejected"):
            with self.subTest(error_code=error_code):
                identity = self.identity(role=error_code)
                operation = self.ledger.prepare_role(
                    aggregate_id=aggregate,
                    identity=identity,
                )
                sending = self.ledger.begin(operation.intent_id)
                self.ledger.finish(
                    operation.intent_id,
                    sending.effect_token,
                    state="rejected",
                    error_code=error_code,
                )
                reopened = self.ledger.retry_rejected(operation.intent_id)
                self.assertEqual(reopened.state, "planned")
                self.assertEqual(
                    [item["state"] for item in self.ledger.audit(operation.intent_id)],
                    ["planned", "sending", "rejected", "planned"],
                )

        unknown = self.ledger.prepare_role(
            aggregate_id=aggregate,
            identity=self.identity(role="unknown"),
        )
        sending = self.ledger.begin(unknown.intent_id)
        self.ledger.finish(
            unknown.intent_id,
            sending.effect_token,
            state="unknown",
            response={"provider_operation_id": None},
            error_code="ambiguous-after-transmission",
        )
        with self.assertRaises(StateConflict):
            self.ledger.retry_rejected(unknown.intent_id)

    def test_sanitized_intent_is_stable_while_private_checkpoint_fence_changes(self):
        first_aggregate = self.ledger.prepare_aggregate(
            **self.bindings, required_roles=("front",)
        )
        first = self.ledger.prepare_role(
            aggregate_id=first_aggregate, identity=self.identity()
        )
        changed = {**self.bindings, "checkpoint_sha256": "9" * 64}
        second_aggregate = self.ledger.prepare_aggregate(
            **changed, required_roles=("front",)
        )
        second_identity = self.identity()
        second_identity["checkpoint_sha256"] = "9" * 64
        second = self.ledger.prepare_role(
            aggregate_id=second_aggregate,
            identity=second_identity,
        )
        self.assertNotEqual(first.intent_id, second.intent_id)
        self.assertEqual(
            first.evidence_intent_sha256,
            second.evidence_intent_sha256,
        )


if __name__ == "__main__":
    unittest.main()
