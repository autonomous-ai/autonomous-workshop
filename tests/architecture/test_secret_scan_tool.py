import importlib.util
import tempfile
import unittest
from pathlib import Path


TOOL_PATH = Path(__file__).resolve().parents[2] / "tools" / "scan_secrets.py"
SPEC = importlib.util.spec_from_file_location("workshop_scan_secrets", TOOL_PATH)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import machinery guard
    raise RuntimeError("cannot load Workshop secret scanner")
SCAN_SECRETS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCAN_SECRETS)


class SecretScanToolTest(unittest.TestCase):
    def test_canonical_and_legacy_portal_credentials_are_rejected_by_path(self):
        for filename in ("portal-auth.json", "panda-auth.json"):
            with self.subTest(filename=filename):
                self.assertEqual(
                    SCAN_SECRETS.path_problem(Path("state") / filename),
                    "tracked-credential-file",
                )

    def test_noncredential_portal_metadata_is_allowed(self):
        self.assertIsNone(
            SCAN_SECRETS.path_problem(Path("evidence") / "portal-receipt.json")
        )

    def test_large_binary_file_is_stream_scanned_across_chunk_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            artifact = Path(temporary) / "large.step"
            token = b"ghp_" + b"a" * 36
            with artifact.open("wb") as handle:
                handle.seek(SCAN_SECRETS.SCAN_CHUNK_BYTES * 6 - 10)
                handle.write(token)

            self.assertGreater(artifact.stat().st_size, 5 * 1024 * 1024)
            self.assertIn("github-token", SCAN_SECRETS.content_problems(artifact))

    def test_key_prefixes_need_a_left_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            prose = Path(temporary) / "node.md"
            prose.write_text(
                "- sources: https://example.test/ask-the-league-of-game-makers-about-catch-up-rules/\n"
                "  and https://example.test/desk-anthology-of-mechanisms-and-their-failures/\n",
                encoding="utf-8",
            )
            self.assertEqual(SCAN_SECRETS.content_problems(prose), [])
            keyed = Path(temporary) / "keyed.md"
            keyed.write_text(
                "token=sk-%s\nother=sk-ant-%s\n" % ("a" * 40, "b" * 30), encoding="utf-8"
            )
            problems = SCAN_SECRETS.content_problems(keyed)
            self.assertIn("openai-key", problems)
            self.assertIn("anthropic-key", problems)


if __name__ == "__main__":
    unittest.main()
