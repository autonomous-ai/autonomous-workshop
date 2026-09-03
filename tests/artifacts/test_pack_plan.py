import tempfile
import unittest
from pathlib import Path

from workshop.artifacts.core import assert_packable_content
from workshop.artifacts.core import MAX_PACK_BYTES
from workshop.errors import ArtifactError
from workshop.artifacts.pack import (
    Artifact,
    ArtifactPlan,
    bundle_artifact,
    inspect_artifact,
    plan_artifact,
)


class PackPlanTest(unittest.TestCase):
    def test_artifact_contract_round_trips_exact_serialized_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.artifact(temporary)
            destination = Path(temporary) / "product.zip"
            artifact = bundle_artifact(root, destination)
            self.assertIsInstance(artifact, Artifact)
            self.assertEqual(inspect_artifact(destination), artifact)
            reconstructed = Artifact(
                artifact.path,
                artifact.bytes,
                artifact.entries,
                pack_sha256=artifact.pack_sha256,
                artifact_sha256=artifact.artifact_sha256,
            )
            self.assertEqual(reconstructed, artifact)

    def artifact(self, temporary: str) -> Path:
        root = Path(temporary) / "artifact"
        root.mkdir()
        (root / "product.txt").write_text("one product\n", encoding="utf-8")
        return root

    def test_secret_shaped_filename_is_rejected_before_path_bearing_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.artifact(temporary)
            secret_name = "ghp_" + ("A" * 24) + ".bin"
            (root / secret_name).write_bytes(b"large enough for the tiny limit")
            destination = Path(temporary) / "product.pack.zip"

            for operation in (
                lambda: plan_artifact(root, maximum_bytes=1),
                lambda: bundle_artifact(root, destination, maximum_bytes=1),
            ):
                with self.subTest(operation=operation):
                    with self.assertRaises(ArtifactError) as raised:
                        operation()
                    message = str(raised.exception)
                    self.assertIn("filename matches secret rule github-token", message)
                    self.assertNotIn(secret_name, message)
            self.assertFalse(destination.exists())

    def test_pack_plan_contract_cannot_emit_a_secret_shaped_path(self):
        secret_name = "ghp_" + ("A" * 24) + ".bin"

        with self.assertRaises(ArtifactError) as raised:
            ArtifactPlan(
                artifact_sha256="a" * 64,
                product_bytes=1,
                pack_bytes=256,
                entries=2,
                limit_bytes=MAX_PACK_BYTES,
                largest_files=((secret_name, 1),),
            )

        self.assertNotIn(secret_name, str(raised.exception))

    def test_limit_above_canonical_ceiling_is_rejected_before_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.artifact(temporary)
            destination = Path(temporary) / "product.pack.zip"

            for operation in (
                lambda: plan_artifact(root, maximum_bytes=MAX_PACK_BYTES + 1),
                lambda: bundle_artifact(
                    root,
                    destination,
                    maximum_bytes=MAX_PACK_BYTES + 1,
                ),
            ):
                with self.subTest(operation=operation):
                    with self.assertRaisesRegex(
                        ArtifactError,
                        "cannot exceed the canonical 50 MB limit",
                    ):
                        operation()
            self.assertFalse(destination.exists())

    def test_oversize_preflight_does_not_create_the_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.artifact(temporary)
            (root / "oversize.bin").write_bytes(b"x" * 1024)
            destination = Path(temporary) / "product.pack.zip"

            plan = plan_artifact(root, maximum_bytes=512)
            self.assertFalse(plan.fits)
            with self.assertRaisesRegex(ArtifactError, "Pack would be"):
                bundle_artifact(root, destination, maximum_bytes=512)
            self.assertFalse(destination.exists())

    def test_unicode_member_names_have_an_exact_planned_size(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.artifact(temporary)
            pieces = root / "pieces"
            pieces.mkdir()
            (pieces / "棋子-雪.txt").write_text("雪のコマ\n", encoding="utf-8")
            destination = Path(temporary) / "product.pack.zip"

            plan = plan_artifact(root)
            packed = bundle_artifact(root, destination)

            self.assertTrue(plan.fits)
            self.assertEqual(plan.pack_bytes, destination.stat().st_size)
            self.assertEqual(plan.pack_bytes, packed.bytes)
            self.assertEqual(plan.artifact_sha256, packed.artifact_sha256)


class PackableContentSecretBoundaryTest(unittest.TestCase):
    def test_key_prefixes_need_a_left_boundary(self):
        prose = (
            b"- sources: https://example.test/ask-the-league-of-game-makers-about-catch-up/\n"
            b"  https://example.test/desk-anthology-of-mechanisms-and-their-failures/\n"
        )
        assert_packable_content("vault/anti-patterns/decided-early.md", prose)
        for name, blob in (
            ("openai-key", b"token=sk-" + b"a" * 40 + b"\n"),
            ("anthropic-key", b"token=sk-ant-" + b"b" * 30 + b"\n"),
        ):
            with self.subTest(rule=name):
                with self.assertRaisesRegex(ArtifactError, "matches secret rule " + name):
                    assert_packable_content("notes.md", blob)


if __name__ == "__main__":
    unittest.main()
