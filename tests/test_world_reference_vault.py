import hashlib
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from inventor_workshop import world_reference_vault as vault_module
from inventor_workshop.errors import ContractError, StateConflict
from inventor_workshop.make import Wish
from inventor_workshop.store import InventorStore
from inventor_workshop.world_reference_vault import (
    MAX_WORLD_CONSENT_BYTES,
    MAX_WORLD_REFERENCE_BYTES,
    WorldReferenceScope,
    WorldReferenceVault,
)


class WorldReferenceVaultTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "eve"
        self.root.mkdir()
        self.wish = Wish.create(
            "wish-20260826-000000-ab12cd34",
            "A tiny portrait of my dog guarding our imaginary moon garden",
            context={"source": "workshop-cli"},
        )
        self.store = InventorStore(
            self.root / ".workshop" / "workshop.sqlite3"
        )
        self.store.register_product(
            self.wish.product_id,
            "playtest",
            {
                "wish": self.wish.to_dict(),
                "lane": "little-worlds",
                "inventor_id": "eve",
            },
        )
        self.reference = Path(self.temp.name) / "private-reference.jpg"
        self.consent = Path(self.temp.name) / "private-consent.txt"
        self.reference_bytes = (
            b"\xff\xd8\xffprivate-image-material-for-a-customer-owned-dog\xff\xd9"
        )
        self.consent_bytes = b"customer attests ownership and this bounded use"
        self.reference.write_bytes(self.reference_bytes)
        self.consent.write_bytes(self.consent_bytes)
        self.scope = WorldReferenceScope(
            reference_id="customer-dog",
            subject_kind="customer-owned-subject",
            subject="the customer's dog",
            rights_basis="customer owns the reference and authorizes this toy",
            allowed_features=("proud neck posture", "round ears"),
            excluded_features=("home address",),
            reviewer_id="customer-order-42",
            verification_method="customer-supplied-attestation-record",
        )
        self.personalization = {
            "consented_references": [
                {
                    "reference_id": "customer-dog",
                    "subject": "the customer's dog",
                    "consent_or_rights_basis": (
                        "customer owns the reference and authorizes this toy"
                    ),
                    "allowed_features": ["proud neck posture", "round ears"],
                    "excluded_features": ["home address"],
                }
            ],
            "feature_to_form_map": [
                {
                    "reference_id": "customer-dog",
                    "reference_feature": "proud neck posture",
                    "physical_form": "a raised silhouette",
                    "recognition_test": "the posture remains distinct in profile",
                },
                {
                    "reference_id": "customer-dog",
                    "reference_feature": "round ears",
                    "physical_form": "two rounded ear forms",
                    "recognition_test": "both ears remain visible from the front",
                },
            ],
        }

    def vault(self):
        return WorldReferenceVault(
            self.root,
            create=True,
            trust_same_user_processes=True,
        )

    def test_local_backend_fails_closed_without_same_user_trust_opt_in(self):
        with self.assertRaisesRegex(ContractError, "cannot isolate"):
            WorldReferenceVault(self.root, create=True)

    def add(self, vault=None, scope=None):
        selected = vault or self.vault()
        return selected.add(
            self.wish,
            scope=scope or self.scope,
            reference_path=self.reference,
            consent_path=self.consent,
            media_type="image/jpeg",
        )

    def test_seals_private_bytes_and_returns_only_raw_free_receipts(self):
        vault = self.vault()
        receipt = self.add(vault)
        self.assertEqual(receipt.reference_id, "customer-dog")
        self.assertEqual(
            receipt.content_sha256,
            hashlib.sha256(self.reference_bytes).hexdigest(),
        )
        self.assertEqual(
            receipt.consent_sha256,
            hashlib.sha256(self.consent_bytes).hexdigest(),
        )
        public = json.dumps(receipt.to_dict(), sort_keys=True).encode("utf-8")
        self.assertNotIn(self.reference_bytes, public)
        self.assertNotIn(self.consent_bytes, public)
        self.assertEqual(receipt.to_dict()["schema_version"], 2)
        self.assertFalse(receipt.to_dict()["raw_private_bytes_included"])
        self.assertEqual(
            receipt.to_dict()["storage_security_boundary"],
            "same-user-local-development",
        )
        self.assertEqual(
            receipt.to_dict()["consent_claim_boundary"],
            "customer-supplied-not-independently-authenticated",
        )

        record_path = (
            vault.records_root / receipt.wish_sha256 / "customer-dog.json"
        )
        record = record_path.read_bytes()
        self.assertNotIn(self.reference_bytes, record)
        self.assertNotIn(self.consent_bytes, record)
        self.assertEqual(
            (vault.blobs_root / receipt.content_sha256).read_bytes(),
            self.reference_bytes,
        )
        self.assertEqual(
            (vault.blobs_root / receipt.consent_sha256).read_bytes(),
            self.consent_bytes,
        )
        self.assertEqual(vault.list(self.wish), (receipt,))

        descriptor = vault.descriptors(self.wish)[0]
        self.assertEqual(
            descriptor.invent_contract(),
            self.personalization["consented_references"][0],
        )
        serialized_descriptor = json.dumps(
            descriptor.to_dict(), sort_keys=True
        ).encode("utf-8")
        self.assertNotIn(self.reference_bytes, serialized_descriptor)
        self.assertNotIn(self.consent_bytes, serialized_descriptor)
        vault.verify_admission(
            descriptor.admission,
            self.wish,
            expected_reference_id="customer-dog",
        )

    @unittest.skipIf(os.name == "nt", "POSIX permissions")
    def test_every_private_directory_and_file_has_private_permissions(self):
        vault = self.vault()
        self.add(vault)
        for path in (
            vault.runtime_root,
            vault.private_root,
            vault.root,
            vault.blobs_root,
            vault.records_root,
            next(vault.records_root.iterdir()),
        ):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700)
        for path in vault.root.rglob("*"):
            if path.is_file():
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_provider_access_is_exact_and_authorization_is_replayable(self):
        vault = self.vault()
        self.add(vault)
        authorized = vault.authorized_provider_inputs(
            self.wish,
            self.personalization,
            expected_reviewer_id="customer-order-42",
            provider_id="workshop-local-vision-v1",
        )
        self.assertEqual(len(authorized), 1)
        selected = authorized[0]
        self.assertEqual(selected.reference_bytes, self.reference_bytes)
        self.assertEqual(selected.consent_bytes, self.consent_bytes)
        representation = repr(selected).encode("utf-8")
        self.assertNotIn(self.reference_bytes, representation)
        self.assertNotIn(self.consent_bytes, representation)
        public = json.dumps(selected.public_attestation(), sort_keys=True).encode(
            "utf-8"
        )
        self.assertNotIn(self.reference_bytes, public)
        self.assertNotIn(self.consent_bytes, public)
        vault.verify_authorization(
            selected.public_attestation(),
            self.wish,
            self.personalization,
            expected_reviewer_id="customer-order-42",
            provider_id="workshop-local-vision-v1",
        )

    def test_authorization_rejects_wish_reviewer_provider_and_contract_swaps(self):
        vault = self.vault()
        self.add(vault)
        authorization = vault.authorized_provider_inputs(
            self.wish,
            self.personalization,
            expected_reviewer_id="customer-order-42",
            provider_id="workshop-local-vision-v1",
        )[0].public_attestation()
        with self.assertRaisesRegex(ContractError, "registered little-worlds Wish"):
            vault.authorized_provider_inputs(
                Wish.create(
                    self.wish.product_id,
                    "Different objective with the same unsafe lookup id",
                    context={"source": "workshop-cli"},
                ),
                self.personalization,
                expected_reviewer_id="customer-order-42",
                provider_id="workshop-local-vision-v1",
            )
        with self.assertRaisesRegex(ContractError, "reviewed consent scope"):
            vault.authorized_provider_inputs(
                self.wish,
                self.personalization,
                expected_reviewer_id="another-reviewer",
                provider_id="workshop-local-vision-v1",
            )
        with self.assertRaisesRegex(ContractError, "another context"):
            vault.verify_authorization(
                authorization,
                self.wish,
                self.personalization,
                expected_reviewer_id="customer-order-42",
                provider_id="swapped-provider",
            )
        changed = json.loads(json.dumps(self.personalization))
        changed["feature_to_form_map"][0]["recognition_test"] = "a different test"
        with self.assertRaisesRegex(ContractError, "another context"):
            vault.verify_authorization(
                authorization,
                self.wish,
                changed,
                expected_reviewer_id="customer-order-42",
                provider_id="workshop-local-vision-v1",
            )

    def test_tampered_blob_record_key_and_symlink_fail_closed(self):
        vault = self.vault()
        receipt = self.add(vault)
        blob = vault.blobs_root / receipt.content_sha256
        blob.write_bytes(b"x" * receipt.content_bytes)
        with self.assertRaisesRegex(ContractError, "content hash changed"):
            vault.authorized_provider_inputs(
                self.wish,
                self.personalization,
                expected_reviewer_id="customer-order-42",
                provider_id="workshop-local-vision-v1",
            )

        blob.write_bytes(self.reference_bytes)
        record = vault.records_root / receipt.wish_sha256 / "customer-dog.json"
        document = json.loads(record.read_text(encoding="utf-8"))
        document["payload"]["scope"]["subject"] = "a swapped subject"
        record.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(ContractError, "authentication did not verify"):
            vault.list(self.wish)

        # Restore the authenticated record, then replace its content blob with a link.
        record.unlink()
        self.add(vault)
        blob.unlink()
        blob.symlink_to(self.reference)
        with self.assertRaisesRegex(ContractError, "non-symlink"):
            vault.authorized_provider_inputs(
                self.wish,
                self.personalization,
                expected_reviewer_id="customer-order-42",
                provider_id="workshop-local-vision-v1",
            )

        blob.unlink()
        blob.write_bytes(self.reference_bytes)
        vault.key_path.write_bytes(b"z" * 32)
        with self.assertRaisesRegex(ContractError, "authentication did not verify"):
            vault.list(self.wish)

    def test_source_symlinks_empty_consent_and_oversized_inputs_are_rejected(self):
        vault = self.vault()
        linked = Path(self.temp.name) / "linked.jpg"
        linked.symlink_to(self.reference)
        with self.assertRaisesRegex(ContractError, "non-symlink"):
            vault.add(
                self.wish,
                scope=self.scope,
                reference_path=linked,
                consent_path=self.consent,
                media_type="image/jpeg",
            )
        self.consent.write_bytes(b"")
        with self.assertRaisesRegex(ContractError, "1.."):
            self.add(vault)
        self.consent.write_bytes(self.consent_bytes)
        with self.reference.open("wb") as stream:
            stream.truncate(MAX_WORLD_REFERENCE_BYTES + 1)
        with self.assertRaisesRegex(ContractError, "1.."):
            self.add(vault)
        self.reference.write_bytes(self.reference_bytes)
        with self.consent.open("wb") as stream:
            stream.truncate(MAX_WORLD_CONSENT_BYTES + 1)
        with self.assertRaisesRegex(ContractError, "1.."):
            self.add(vault)

    def test_declared_media_type_must_match_the_reference_bytes(self):
        vault = self.vault()
        self.reference.write_bytes(b"not-an-image")
        with self.assertRaisesRegex(ContractError, "declared supported media type"):
            self.add(vault)

    def test_source_mutation_during_read_is_rejected(self):
        observed = self.reference.stat()
        changed = SimpleNamespace(
            st_dev=observed.st_dev,
            st_ino=observed.st_ino,
            st_mode=observed.st_mode,
            st_size=observed.st_size,
            st_mtime_ns=observed.st_mtime_ns + 1,
            st_ctime_ns=observed.st_ctime_ns,
        )
        with mock.patch.object(
            vault_module.os,
            "fstat",
            side_effect=(observed, changed),
        ), self.assertRaisesRegex(ContractError, "changed while reading"):
            vault_module._read_bounded_regular(
                self.reference,
                MAX_WORLD_REFERENCE_BYTES,
                "private world reference",
            )

    @unittest.skipIf(os.name == "nt", "POSIX permissions")
    def test_permission_mutation_fails_closed(self):
        vault = self.vault()
        receipt = self.add(vault)
        blob = vault.blobs_root / receipt.content_sha256
        blob.chmod(0o644)
        with self.assertRaisesRegex(ContractError, "private 0600"):
            vault.list(self.wish)
        blob.chmod(0o600)
        vault.records_root.chmod(0o755)
        with self.assertRaisesRegex(ContractError, "private 0700"):
            vault.list(self.wish)

    def test_missing_consent_and_unsupported_likeness_classes_are_rejected(self):
        for kind in (
            "celebrity",
            "franchise",
            "public-figure",
            "third-party-likeness",
        ):
            with self.subTest(kind=kind), self.assertRaisesRegex(
                ContractError, "unsupported"
            ):
                WorldReferenceScope(
                    reference_id="unsafe-ref",
                    subject_kind=kind,
                    subject="an unsupported subject",
                    rights_basis="customer asks for it",
                    allowed_features=("face",),
                    excluded_features=(),
                    reviewer_id="customer-order-42",
                    verification_method="customer-supplied-attestation-record",
                )
        with self.assertRaisesRegex(ContractError, "explicit"):
            WorldReferenceScope(
                reference_id="pending-ref",
                subject_kind="customer-self",
                subject="the customer",
                rights_basis="pending",
                allowed_features=("smile",),
                excluded_features=(),
                reviewer_id="customer-order-42",
                verification_method="customer-supplied-attestation-record",
            )
        secret = "sk-proj-" + ("A" * 40)
        with self.assertRaises(ContractError) as caught:
            WorldReferenceScope(
                reference_id="private-scope",
                subject_kind="customer-owned-subject",
                subject="a customer-owned keepsake",
                rights_basis="customer pasted this token by mistake: " + secret,
                allowed_features=("round ears",),
                excluded_features=(),
                reviewer_id="customer-order-42",
                verification_method="customer-supplied-attestation-record",
            )
        self.assertNotIn(secret, str(caught.exception))
        missing = Path(self.temp.name) / "missing-consent.txt"
        with self.assertRaisesRegex(ContractError, "missing or unreadable"):
            self.vault().add(
                self.wish,
                scope=self.scope,
                reference_path=self.reference,
                consent_path=missing,
                media_type="image/jpeg",
            )

    def test_reference_ids_are_immutable_but_exact_retries_are_idempotent(self):
        vault = self.vault()
        first = self.add(vault)
        second = self.add(vault)
        self.assertEqual(first, second)
        self.reference.write_bytes(b"\xff\xd8\xffdifferent-private-reference\xff\xd9")
        with self.assertRaisesRegex(StateConflict, "already sealed"):
            self.add(vault)

    def test_non_world_or_unregistered_wishes_cannot_open_the_vault(self):
        other = Wish.create("wish-20260826-000001-ab12cd35", "A simple checkers set")
        self.store.register_product(
            other.product_id,
            "playtest",
            {"wish": other.to_dict(), "lane": "classics", "inventor_id": "alice"},
        )
        with self.assertRaisesRegex(ContractError, "little-worlds"):
            self.vault().add(
                other,
                scope=self.scope,
                reference_path=self.reference,
                consent_path=self.consent,
                media_type="image/jpeg",
            )
        unknown = Wish.create("wish-20260826-000002-ab12cd36", "Unknown")
        with self.assertRaisesRegex(ContractError, "registered Workshop Wish"):
            self.vault().add(
                unknown,
                scope=self.scope,
                reference_path=self.reference,
                consent_path=self.consent,
                media_type="image/jpeg",
            )


if __name__ == "__main__":
    unittest.main()
