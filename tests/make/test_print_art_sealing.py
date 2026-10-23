"""ADR 0091: print art seals beside the references and guides, and nothing
that compares references with the model takes it for one."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
MAKE_ROUND = ROOT / "src/workshop/make/skills/make-round/scripts/make_round"
STAGE_PROPOSAL = ROOT / ".agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py"
IMAGES = {
    "ref-01-whole.png": b"whole",
    "guide-01-steps.png": b"steps",
    "print-01-sky.png": b"sky",
    "print-02-cover.png": b"cover",
}
CONTRACT = {
    "schema_version": 6,
    "title": "Nook",
    "references": [{"file": "ref-01-whole.png", "shows": "assembly", "camera": [-90, 15]}],
    "guides": [{"file": "guide-01-steps.png", "shows": "How the shelves stack."}],
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PrintArtSealingTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name).resolve()
        (self.run_root / "wish-references").mkdir()
        for name, content in IMAGES.items():
            (self.run_root / "wish-references" / name).write_bytes(content)
        self.project = self.run_root / "artifacts/make/r0001/product/cad"
        self.project.mkdir(parents=True)

    def write_wish(self, names):
        wish = {"references": [{"name": n, "sha256": sha(IMAGES[n])} for n in names],
                "context": {"design_contract": CONTRACT}}
        content = json.dumps(wish).encode()
        (self.run_root / "WISH.json").write_bytes(content)
        return sha(content)

    def test_make_round_compares_only_the_references(self):
        self.write_wish(IMAGES)
        make_round = runpy.run_path(str(MAKE_ROUND))
        sealed, error = make_round["sealed_references"](self.project)
        self.assertIsNone(error)
        self.assertEqual([item["label"] for item in sealed], ["assembly"])
        guides, error = make_round["sealed_guides"](self.project)
        self.assertIsNone(error)
        self.assertEqual([item["file"] for item in guides], ["guide-01-steps.png"])

    def test_the_finalizer_counts_no_print_art_as_a_sealed_reference(self):
        spec = importlib.util.spec_from_file_location("stage_proposal_print_art", STAGE_PROPOSAL)
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        digest = self.write_wish(["guide-01-steps.png", "print-01-sky.png"])
        self.assertFalse(tool._wish_has_sealed_references(self.run_root, digest))
        digest = self.write_wish(IMAGES)
        self.assertTrue(tool._wish_has_sealed_references(self.run_root, digest))


if __name__ == "__main__":
    unittest.main()
