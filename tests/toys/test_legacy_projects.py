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
    "bob-g0001": "8b03a9ec3cff7b5998f29d0c9e1c2f8967ec7058717c1550fcc9e87e9de79db7",
    "bob-g0002": "57593109577ab369f1c009028d05f72ec16cfe9012b9a490a85dccdcd0d0361e",
    "bob-g0003": "29a3e6b0c50da224446846323acfec8f1459ef443700abd0d343f4d0c12a5650",
    "bob-g0004": "83aa0b78964f66f016a92b79e9ed8f6ea93bcd7c9fe8ed40cd643c5bf9ac6c6b",
    "bob-g0005": "3ac1673c4373e8171f085e3c78bf294883a97d66bcc259c319a8499910a860f0",
    "bob-g0006": "d9caf6166567aa3df300667e8af342fae3262ee3d50d18f9c328b16e454d7c4a",
    "eve-rackhaven-night-shift": "9b2ff16c5c454bfa298c90ccb1329ec42a3f1b9d4f2fdbdb44d44272f279d9f5",
    "ivy-montauk-tide-orrery": "15c7b340d5b158ddfc2179ba644a9a97d21d7357d65cd3c75978a842f3c6c4ba",
    "leo-counterorbit": "5396202038e628a50fec4efdc8c5dc3e55dbc96fe406ce0006029fc7e182e5c3",
}
EXPECTED_EXCLUSION_SHA256 = {
    "bob-g0002": "d18ce659f0842041216428ce9e9813ea06931237c7b1f1bbf8b1f6141cd4a636",
    "bob-g0003": "119200b1ed964f973eff3d9a55f6d50f5e4d7432787bf8fb874afce1dd39d96b",
}


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

        self.assertEqual(len(document["projects"]), 14)
        self.assertEqual(
            sum(item["migrated_product"]["file_count"] for item in document["projects"]),
            1093,
        )
        self.assertEqual(
            sum(len(item["exclusions"]) for item in document["projects"]),
            270,
        )
        self.assertEqual(1093 + 270, 1363)
        self.assertEqual(
            sum(item["migrated_product"]["bytes"] for item in document["projects"]),
            234402484,
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
