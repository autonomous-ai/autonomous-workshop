import json
import re
import unittest
from pathlib import Path

from inventor_workshop.cad import (
    CadPart,
    CadProjectManifest,
    WORKSHOP_CHECKS,
    WORKSHOP_CHECK_MEASUREMENTS,
    PhysicalClaim,
    ValidatorRequirement,
    VerificationCheck,
    VerificationReceipt,
)
from inventor_workshop.errors import ContractError
from inventor_workshop.models import require_exact_version, require_safe_evidence_path


CORE = Path(__file__).resolve().parents[1]
ASSETS = CORE / "skills" / "product-to-cad" / "assets"
SCHEMAS = CORE / "schemas"


class ProductToCadAssetTest(unittest.TestCase):
    def test_cad_project_example_matches_workshop_contract(self):
        raw = json.loads((ASSETS / "cad-project.example.json").read_text(encoding="utf-8"))
        raw["parts"] = tuple(CadPart(**item) for item in raw["parts"])
        raw["physical_claims"] = tuple(
            PhysicalClaim(**item) for item in raw["physical_claims"]
        )
        manifest = CadProjectManifest(**raw)
        self.assertEqual(manifest.physical_claims[0].status, "held")

    def test_receipt_example_is_conspicuously_held(self):
        raw = json.loads(
            (ASSETS / "verification-receipt.example.json").read_text(encoding="utf-8")
        )
        raw["checks"] = tuple(VerificationCheck(**item) for item in raw["checks"])
        receipt = VerificationReceipt(**raw)
        self.assertEqual(receipt.status, "held")
        self.assertEqual(receipt.checks[0].check_id, "manifest")
        self.assertIn("TEMPLATE ONLY", receipt.checks[0].limitations[0])

    def test_validator_policy_example_covers_all_workshop_checks(self):
        raw = json.loads(
            (ASSETS / "validator-policy.example.json").read_text(encoding="utf-8")
        )
        requirements = tuple(ValidatorRequirement(**item) for item in raw)
        covered = {
            check
            for requirement in requirements
            for check in requirement.required_checks
        }
        self.assertEqual(covered, set(WORKSHOP_CHECKS))
        self.assertEqual(
            {item.substrate for item in requirements},
            {"deterministic", "independent-review", "physical"},
        )

    def test_receipt_schema_tracks_workshop_measurement_contract(self):
        schema = json.loads(
            (SCHEMAS / "verification-receipt.schema.json").read_text(
                encoding="utf-8"
            )
        )
        branches = schema["$defs"]["check"]["allOf"]
        required_by_check = {}
        for branch in branches:
            properties = branch.get("if", {}).get("properties", {})
            check_id = properties.get("check_id", {}).get("const")
            status = properties.get("status", {}).get("const")
            if check_id is not None and status == "passed":
                required_by_check[check_id] = set(
                    branch["then"]["properties"]["measurements"]["required"]
                )
        self.assertEqual(set(required_by_check), set(WORKSHOP_CHECKS))
        self.assertEqual(
            required_by_check,
            {
                check_id: set(measurements)
                for check_id, measurements in WORKSHOP_CHECK_MEASUREMENTS.items()
            },
        )

    def test_receipt_schema_types_partial_workshop_measurements(self):
        schema = json.loads(
            (SCHEMAS / "verification-receipt.schema.json").read_text(
                encoding="utf-8"
            )
        )
        typed_refs = {}
        for branch in schema["$defs"]["check"]["allOf"]:
            properties = branch.get("if", {}).get("properties", {})
            check_id = properties.get("check_id", {}).get("const")
            status = properties.get("status", {}).get("const")
            measurement = (
                branch.get("then", {})
                .get("properties", {})
                .get("measurements", {})
            )
            if check_id is not None and status is None and "$ref" in measurement:
                typed_refs[check_id] = measurement["$ref"].rsplit("/", 1)[-1]
        self.assertEqual(set(typed_refs), set(WORKSHOP_CHECKS))
        for check_id, runtime_rules in WORKSHOP_CHECK_MEASUREMENTS.items():
            properties = schema["$defs"][typed_refs[check_id]]["properties"]
            self.assertEqual(set(properties), set(runtime_rules))
            for name, runtime_rule in runtime_rules.items():
                field = properties[name]
                self.assertEqual(field["type"], runtime_rule["type"])
                if "minimum" in runtime_rule:
                    self.assertEqual(field["minimum"], runtime_rule["minimum"])
                if "min_length" in runtime_rule:
                    self.assertEqual(field["pattern"], r"\S")

    def test_cad_schemas_bind_physical_claim_evidence_and_reviewer_identity(self):
        project = json.loads(
            (SCHEMAS / "cad-project.schema.json").read_text(encoding="utf-8")
        )
        receipt = json.loads(
            (SCHEMAS / "verification-receipt.schema.json").read_text(
                encoding="utf-8"
            )
        )
        policy = json.loads(
            (SCHEMAS / "validator-policy.schema.json").read_text(encoding="utf-8")
        )
        gate = json.loads(
            (SCHEMAS / "gate-result.schema.json").read_text(encoding="utf-8")
        )
        claim = project["properties"]["physical_claims"]["items"]
        passed = next(
            rule
            for rule in claim["allOf"]
            if rule["if"].get("properties", {}).get("status", {}).get("const")
            == "passed"
        )
        passed_properties = passed["then"]["properties"]
        self.assertEqual(passed_properties["evidence_ref"], {"$ref": "#/$defs/safePath"})
        self.assertEqual(
            passed_properties["evidence_sha256"]["pattern"], "^[0-9a-f]{64}$"
        )
        paired = next(
            rule
            for rule in claim["allOf"]
            if rule["if"].get("properties", {}).get("evidence_ref", {}).get("type")
            == "null"
        )
        self.assertEqual(
            paired["then"]["properties"]["evidence_sha256"], {"type": "null"}
        )

        reviewer_rules = (
            project["properties"]["engine"]["properties"]["name"],
            receipt["properties"]["validator"],
            policy["items"]["properties"]["validator"],
            gate["properties"]["evaluator"],
        )
        for rule in reviewer_rules:
            pattern = rule["not"]["pattern"]
            self.assertRegex("SELF-REPORT", pattern)
            self.assertRegex("Trust-Me", pattern)
            self.assertNotRegex("reviewer-1.2", pattern)

    def test_all_evidence_path_schemas_match_the_runtime_contract(self):
        artifact = json.loads(
            (SCHEMAS / "artifact-manifest.schema.json").read_text(encoding="utf-8")
        )
        project = json.loads(
            (SCHEMAS / "cad-project.schema.json").read_text(encoding="utf-8")
        )
        gate = json.loads(
            (SCHEMAS / "gate-result.schema.json").read_text(encoding="utf-8")
        )
        receipt = json.loads(
            (SCHEMAS / "verification-receipt.schema.json").read_text(
                encoding="utf-8"
            )
        )
        safe_path = artifact["$defs"]["safePath"]
        self.assertEqual(safe_path, project["$defs"]["safePath"])
        self.assertEqual(safe_path, gate["$defs"]["safePath"])
        self.assertEqual(safe_path, receipt["$defs"]["safePath"])
        pattern = safe_path["pattern"]
        accepted = ("evidence/report.json", ".hidden", "a/.hidden", "a..b")
        rejected = (
            ".",
            "..",
            "/absolute",
            "a\\b",
            "a//b",
            "a/./b",
            "a/../b",
            "a/",
            "bad\x00name",
        )
        for value, expected in (
            *((value, True) for value in accepted),
            *((value, False) for value in rejected),
        ):
            schema_accepts = bool(re.fullmatch(pattern, value))
            try:
                require_safe_evidence_path(value)
                runtime_accepts = True
            except ContractError:
                runtime_accepts = False
            with self.subTest(path=value):
                self.assertEqual(schema_accepts, expected)
                self.assertEqual(runtime_accepts, expected)

    def test_validator_policy_schema_is_valid_json_and_matches_example_shape(self):
        schema = json.loads(
            (SCHEMAS / "validator-policy.schema.json").read_text(encoding="utf-8")
        )
        example = json.loads(
            (ASSETS / "validator-policy.example.json").read_text(encoding="utf-8")
        )
        self.assertEqual(schema["type"], "array")
        required = set(schema["items"]["required"])
        self.assertTrue(example)
        self.assertTrue(all(set(item) == required for item in example))

    def test_cad_schemas_share_the_exact_runtime_version_contract(self):
        receipt_schema = json.loads(
            (SCHEMAS / "verification-receipt.schema.json").read_text(
                encoding="utf-8"
            )
        )
        policy_schema = json.loads(
            (SCHEMAS / "validator-policy.schema.json").read_text(encoding="utf-8")
        )
        gate_schema = json.loads(
            (SCHEMAS / "gate-result.schema.json").read_text(encoding="utf-8")
        )
        project_schema = json.loads(
            (SCHEMAS / "cad-project.schema.json").read_text(encoding="utf-8")
        )
        exact = receipt_schema["$defs"]["exactVersion"]
        self.assertEqual(exact, policy_schema["$defs"]["exactVersion"])
        self.assertEqual(exact, gate_schema["$defs"]["exactVersion"])
        self.assertEqual(exact, project_schema["$defs"]["exactVersion"])

        accepted = (
            "1",
            "v1.2.3+build-7",
            "unknown1.2",
            "1x",
            "A" * 127 + "1",
        )
        rejected = (
            "",
            "release",
            "-1",
            "1 beta",
            "v1/2",
            "v1.latest",
            "v1-LATEST",
            "main.1",
            "v1_master",
            "v1+HEAD",
            "v1-dev",
            "v1.development",
            "v1-unknown",
            "v1_snapshot",
            "v1.x",
            "v1-*",
            "A" * 128 + "1",
        )

        def schema_accepts(value):
            return bool(re.fullmatch(exact["pattern"], value)) and not bool(
                re.search(exact["not"]["pattern"], value)
            )

        for value, expected in (
            *((value, True) for value in accepted),
            *((value, False) for value in rejected),
        ):
            try:
                require_exact_version(value, "test version")
                runtime_accepts = True
            except ContractError:
                runtime_accepts = False
            with self.subTest(version=value):
                self.assertEqual(schema_accepts(value), expected)
                self.assertEqual(runtime_accepts, expected)


if __name__ == "__main__":
    unittest.main()
