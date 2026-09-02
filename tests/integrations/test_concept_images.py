import base64
import json
import os
import tempfile
import unittest

from workshop.errors import ContractError
from workshop.integrations.concept_images import (
    ConceptImageProfile,
    ConceptImageReconciliation,
    ConceptImageReference,
    ConceptImageRejected,
    ConceptImageRequest,
    ConceptImageResponse,
    DEFAULT_IMAGE_TIMEOUT_SECONDS,
    OpenRouterConceptImageClient,
    load_concept_image_credentials,
)


PNG = b"\x89PNG\r\n\x1a\nexact-provider-image"


class ConceptImageIntegrationTest(unittest.TestCase):
    def test_adapter_sends_one_bound_image_request_with_ordered_references(self):
        calls = []

        def transport(url, headers, body, timeout):
            calls.append((url, headers, json.loads(body), timeout))
            return 200, {"x-request-id": "private-operation"}, json.dumps(
                {"data": [{
                    "b64_json": base64.b64encode(PNG).decode("ascii"),
                    "media_type": "image/png",
                }]}
            ).encode()

        profile = ConceptImageProfile(supports_idempotency=True)
        client = OpenRouterConceptImageClient(profile, "secret", transport=transport)
        reference = ConceptImageReference(
            "front",
            __import__("hashlib").sha256(PNG).hexdigest(),
            "image/png",
            PNG,
        )
        response = client.render(
            ConceptImageRequest(
                role="top",
                instruction="Draw the exact top view.",
                output_path="images/top.png",
                idempotency_key="intent-1",
                references=(reference,),
            )
        )
        self.assertEqual(response.content, PNG)
        self.assertEqual(calls[0][0], "https://openrouter.ai/api/v1/images")
        self.assertEqual(calls[0][1]["Idempotency-Key"], "intent-1")
        self.assertEqual(calls[0][2]["n"], 1)
        self.assertEqual(len(calls[0][2]["input_references"]), 1)
        self.assertEqual(
            calls[0][2]["input_references"][0],
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:image/png;base64,%s"
                    % base64.b64encode(PNG).decode("ascii")
                },
            },
        )
        self.assertEqual(calls[0][3], DEFAULT_IMAGE_TIMEOUT_SECONDS)

    def test_adapter_serializes_adaptive_role_context_canonically(self):
        calls = []

        def transport(url, headers, body, timeout):
            calls.append(json.loads(body))
            return 200, {}, json.dumps(
                {"data": [{"b64_json": base64.b64encode(PNG).decode("ascii")}]}
            ).encode()

        request = ConceptImageRequest(
            role="signature-open",
            instruction="Show the held opening action.",
            output_path="images/signature-open.png",
            idempotency_key="intent-adaptive",
            context={
                "role": {"kind": "signature-experience", "id": "signature-open"},
                "normalized_constraints": {"wall": {"value": 1.2}},
            },
        )
        OpenRouterConceptImageClient(
            ConceptImageProfile(), "secret", transport=transport
        ).render(request)
        self.assertEqual(
            calls[0]["prompt"],
            json.dumps(
                {"instruction": request.instruction, "context": request.context},
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ),
        )

    def test_adapter_rejects_declared_media_type_mismatching_exact_bytes(self):
        client = OpenRouterConceptImageClient(
            ConceptImageProfile(),
            "secret",
            transport=lambda *unused: (
                200,
                {},
                json.dumps({"data": [{
                    "b64_json": base64.b64encode(PNG).decode("ascii"),
                    "media_type": "image/jpeg",
                }]}).encode(),
            ),
        )
        with self.assertRaisesRegex(ConceptImageRejected, "media type"):
            client.render(
                ConceptImageRequest(
                    "front", "Draw front.", "images/front.png", "intent"
                )
            )

    def test_adapter_rejects_redirects_multiple_images_and_unrecognized_media(self):
        cases = (
            (302, b"{}"),
            (200, json.dumps({"data": [{"b64_json": base64.b64encode(PNG).decode()}, {"b64_json": base64.b64encode(PNG).decode()}]}).encode()),
            (200, json.dumps({"data": [{"b64_json": base64.b64encode(b"not-image").decode()}]}).encode()),
        )
        for status, body in cases:
            with self.subTest(status=status, size=len(body)):
                client = OpenRouterConceptImageClient(
                    ConceptImageProfile(),
                    "secret",
                    transport=lambda *unused, status=status, body=body: (status, {}, body),
                )
                with self.assertRaises((ConceptImageRejected, ContractError)):
                    client.render(
                        ConceptImageRequest(
                            "front", "Draw front.", "images/front.png", "intent"
                        )
                    )

    def test_profile_request_response_and_transport_are_strictly_bounded(self):
        with self.assertRaises(ContractError):
            ConceptImageProfile(origin="https://user:secret@example.test")
        for output_path in ("../images/front.png", "/images/front.png", "front.png"):
            with self.subTest(output_path=output_path):
                with self.assertRaises(ContractError):
                    ConceptImageRequest(
                        "front", "Draw front.", output_path, "intent"
                    )
        client = OpenRouterConceptImageClient(
            ConceptImageProfile(),
            "secret",
            transport=lambda *unused: (True, {}, b"{}"),
        )
        with self.assertRaisesRegex(ConceptImageRejected, "transport response"):
            client.render(
                ConceptImageRequest(
                    "front", "Draw front.", "images/front.png", "intent"
                )
            )
        with self.assertRaises(ContractError):
            ConceptImageResponse(PNG, "image/png", metadata={"bad": float("nan")})

    def test_private_credentials_loader_requires_exact_profile_and_permissions(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = __import__("pathlib").Path(temporary) / "concept.json"
            profile = ConceptImageProfile()
            path.write_text(json.dumps({
                "schema_version": 1,
                "profile": {
                    "profile_id": profile.profile_id,
                    "origin": profile.origin,
                    "model": profile.model,
                    "request_schema_version": profile.request_schema_version,
                    "supports_idempotency": False,
                    "supports_operation_readback": False,
                    "supports_absence_proof": False,
                },
                "api_key": "private-key",
            }))
            path.chmod(0o600)
            client = load_concept_image_credentials(
                str(path), transport=lambda *unused: (500, {}, b"{}")
            )
            self.assertEqual(client.profile.profile_sha256, profile.profile_sha256)
            path.chmod(0o644)
            with self.assertRaises(ContractError):
                load_concept_image_credentials(str(path))

    def test_reconciliation_uses_only_declared_authenticated_capabilities(self):
        succeeded = ConceptImageReconciliation(
            "succeeded",
            response=ConceptImageResponse(PNG, "image/png", "operation-1"),
        )
        calls = []
        client = OpenRouterConceptImageClient(
            ConceptImageProfile(
                supports_idempotency=True,
                supports_operation_readback=True,
                supports_absence_proof=True,
            ),
            "secret",
            transport=lambda *unused: (500, {}, b"{}"),
            reconciler=lambda operation_id, headers, timeout: (
                calls.append((operation_id, headers, timeout)) or succeeded
            ),
        )
        self.assertEqual(client.reconcile("operation-1"), succeeded)
        self.assertEqual(calls[0][0], "operation-1")
        self.assertIn("Authorization", calls[0][1])
        unsupported = OpenRouterConceptImageClient(
            ConceptImageProfile(), "secret", transport=lambda *unused: (500, {}, b"{}")
        )
        self.assertEqual(unsupported.reconcile("operation-1").status, "unknown")


if __name__ == "__main__":
    unittest.main()
