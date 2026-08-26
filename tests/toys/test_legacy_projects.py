import importlib.util
import json
import sys
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
VERIFIER = REPOSITORY / "tools" / "verify_toy_projects.py"
EXPECTED_INVENTORY_SHA256 = {
    "alice-blindcap-duel": "e7f30085cfadf7523c38ddf0b171579d916f4f00b009e31b83a65e794d257fc9",
    "alice-cone-nine": "74023f978e85b8642d36d7d8fbb9f828d6a9744df12b45fb7b4171468ac6bdaa",
    "alice-five-job-checkers": "aee38a5dc205e1e3fe14e7a387c31205dbf5e50f476b9baef57467c7b1d9117e",
    "alice-manhattan-nocturne": "1cc22468c46d8d3adae19614f61b606c704514af7821d6946829d628399fcdf1",
    "bob-comet-geneva": "7fa082d1da81c668ea7ea02a9a84bd92479e3a7a237667dddbda144c9704b9c9",
    "eve-rackhaven-night-shift": "9b2ff16c5c454bfa298c90ccb1329ec42a3f1b9d4f2fdbdb44d44272f279d9f5",
    "ivy-montauk-tide-orrery": "15c7b340d5b158ddfc2179ba644a9a97d21d7357d65cd3c75978a842f3c6c4ba",
    "leo-counterorbit": "5396202038e628a50fec4efdc8c5dc3e55dbc96fe406ce0006029fc7e182e5c3",
}
EXPECTED_EXCLUSION_SHA256 = {}


def _load_verifier():
    spec = importlib.util.spec_from_file_location("verify_toy_projects", VERIFIER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load toy project verifier")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class LegacyToyProjectTest(unittest.TestCase):
    def test_every_migrated_toy_is_an_exact_persistent_codex_project(self):
        verifier = _load_verifier()

        self.assertEqual(verifier.verify(), [])

    def test_manifest_accounts_for_the_complete_audited_source_tree(self):
        document = json.loads(
            (REPOSITORY / "toys" / "legacy-migration.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(len(document["projects"]), 8)
        self.assertEqual(
            sum(item["migrated_product"]["file_count"] for item in document["projects"]),
            544,
        )
        self.assertEqual(
            sum(len(item["exclusions"]) for item in document["projects"]),
            0,
        )
        self.assertEqual(
            sum(item["migrated_product"]["file_count"] for item in document["projects"])
            + sum(len(item["exclusions"]) for item in document["projects"]),
            544,
        )
        self.assertEqual(
            sum(item["migrated_product"]["bytes"] for item in document["projects"]),
            55838488,
        )

    def test_source_derived_product_and_exclusion_hashes_are_independently_pinned(self):
        import hashlib

        verifier = _load_verifier()
        document = json.loads(
            (REPOSITORY / "toys" / "legacy-migration.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(document["source_commit"], verifier.SOURCE_COMMIT)
        by_id = {item["toy_id"]: item for item in document["projects"]}
        self.assertEqual(set(by_id), set(EXPECTED_INVENTORY_SHA256))
        for toy_id, expected in EXPECTED_INVENTORY_SHA256.items():
            problems = []
            records = verifier._product_records(
                REPOSITORY / "toys" / toy_id, problems
            )
            self.assertEqual(problems, [])
            self.assertEqual(verifier._inventory(records)[2], expected)
            self.assertEqual(
                by_id[toy_id]["migrated_product"]["inventory_sha256"], expected
            )
            exclusions = by_id[toy_id]["exclusions"]
            exclusion_sha256 = hashlib.sha256(
                json.dumps(
                    exclusions, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")
            ).hexdigest()
            self.assertEqual(
                exclusion_sha256,
                EXPECTED_EXCLUSION_SHA256.get(
                    toy_id,
                    "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
                ),
            )

    def test_runtime_wish_projects_can_coexist_with_fixed_migrations(self):
        verifier = _load_verifier()
        expected = {"%s-%s" % item for item in verifier.PROJECTS}
        observed = set(expected)
        observed.add("wish-20260826-123456-deadbeef")

        self.assertEqual(
            verifier._project_set_difference(observed, expected), ([], [])
        )
        observed.add("unreviewed-showcase")
        self.assertEqual(
            verifier._project_set_difference(observed, expected),
            ([], ["unreviewed-showcase"]),
        )


if __name__ == "__main__":
    unittest.main()
