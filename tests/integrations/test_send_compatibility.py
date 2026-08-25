import tempfile
import unittest
from pathlib import Path

from workshop.artifacts import bundle_artifact
from workshop.integrations.send import inspect_legacy_packet


class SendCompatibilityTest(unittest.TestCase):
    def test_legacy_packet_inspection_projects_the_canonical_pack_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "artifact"
            root.mkdir()
            (root / "toy.txt").write_text("sealed toy\n", encoding="utf-8")
            packed = bundle_artifact(root, Path(temporary) / "toy.pack.zip")

            self.assertEqual(
                inspect_legacy_packet(packed.path),
                {
                    "bytes": packed.bytes,
                    "entries": packed.entries,
                    "packet_sha256": packed.pack_sha256,
                    "artifact_sha256": packed.artifact_sha256,
                },
            )


if __name__ == "__main__":
    unittest.main()
