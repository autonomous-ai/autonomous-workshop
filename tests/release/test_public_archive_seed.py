"""ADR 0096: a seeded toy's archive carries its Approved Proof.

Contract: `_copy_seed` writes a seeded run's sealed `seed/` tree (the
approval and exactly its manifest's files) under `wish/seed/`, checking each
file against the hashes the Wish recorded; an unseeded Wish writes nothing.
It refuses an approval or manifest that is not the Wish's, a changed, missing
or symlinked file and an unsafe manifest path. A correction accepts an
archive that carries the seed, and a schema 11 correction still needs
`--seed-source` (tests/cli/test_seed_source.py)."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from workshop.errors import StateConflict
from workshop.release.public_archive import PUBLIC_SEED_DIRECTORY, _copy_seed, build_public_archive_manifest
from workshop.workflow.revision import prepare_revision

FILES = {"params.py": b"WIDTH = 40\n", "part_body.step.py": b"# body\n",
         "approved/part_body.step": b"ISO-10303-21;\n", "CRITIC.json": b'{"verdict":"agree"}',
         "CONCEPT-CHECKLIST.md": b"- T1 required\n"}


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class CopySeedTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run = Path(temporary.name)
        seed = self.run / "seed"
        for name, content in FILES.items():
            (seed / name).parent.mkdir(parents=True, exist_ok=True)
            (seed / name).write_bytes(content)
        self.manifest = {name: _sha(content) for name, content in FILES.items()}
        self.write_approval()
        self.written = {}

    def write_approval(self, **changes):
        approval = {"schema_version": 1, "manifest": self.manifest,
                    "manifest_sha256": _sha(json.dumps(self.manifest, sort_keys=True).encode())}
        approval.update(changes)
        content = json.dumps(approval, sort_keys=True).encode()
        (self.run / "seed/APPROVAL.json").write_bytes(content)
        self.context = {"seed": {"approval_sha256": _sha(content),
                                 "manifest_sha256": approval["manifest_sha256"]}}

    def copy(self, context=None):
        _copy_seed(lambda relative, content: self.written.__setitem__(relative, content), self.run,
                   self.context if context is None else context)

    def test_the_seed_tree_is_written_under_wish_seed(self):
        self.copy()
        expected = {"%s/%s" % (PUBLIC_SEED_DIRECTORY, name): content for name, content in FILES.items()}
        expected["wish/seed/APPROVAL.json"] = (self.run / "seed/APPROVAL.json").read_bytes()
        self.assertEqual(self.written, expected)

    def test_an_unseeded_wish_writes_nothing(self):
        self.copy({"inventor_id": "x"})
        self.copy({})
        self.assertEqual(self.written, {})

    def test_refusals(self):
        def changed():
            (self.run / "seed/params.py").write_bytes(b"WIDTH = 41\n")

        def missing():
            (self.run / "seed/CRITIC.json").unlink()

        def linked():
            (self.run / "seed/params.py").unlink()
            (self.run / "seed/params.py").symlink_to(self.run / "seed/part_body.step.py")

        def other_approval():
            self.context["seed"]["approval_sha256"] = "0" * 64

        def other_manifest():
            self.context["seed"]["manifest_sha256"] = "0" * 64

        def unsafe():
            self.manifest = {"../escape.py": _sha(b"x")}
            self.write_approval()

        cases = {"differs from its approval: params.py": changed, "CRITIC.json is unavailable": missing,
                 "not a bounded regular file": linked, "approval differs from the Wish": other_approval,
                 "manifest differs from the Wish": other_manifest, "unsafe path": unsafe}
        for fragment, change in cases.items():
            with self.subTest(fragment):
                self.setUp()
                change()
                with self.assertRaisesRegex(StateConflict, fragment):
                    self.copy()


class SeedCarryingArchiveTest(unittest.TestCase):
    def test_a_correction_accepts_an_archive_with_its_seed(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary).resolve() / "published"
            files = {"make/source/toy.step.py": b"# CAD\n", "wish/wish.json": b'{"objective":"x"}',
                     **{"wish/seed/%s" % name: content for name, content in FILES.items()},
                     "wish/seed/APPROVAL.json": b"{}",
                     "publication/PUBLICATION.json": json.dumps({
                         "kind": "autonomous-workshop.public-toy-snapshot", "schema_version": 2,
                         "title": "Beaver", "inventor": {"id": "mara-masque"},
                         "publication": {"status": "public", "page_url": "https://example.com/b"}}).encode()}
            for name, content in files.items():
                (source / name).parent.mkdir(parents=True, exist_ok=True)
                (source / name).write_bytes(content)
            manifest = build_public_archive_manifest(source)
            (source / "MANIFEST.json").write_text(json.dumps({
                "schema_version": 4, "kind": "autonomous-workshop.public-toy-archive",
                "artifact_manifest": manifest.to_dict()}))
            wish, _ = prepare_revision(source, "Correct the beaver.\n")
            self.assertEqual(wish.context["inventor_id"], "mara-masque")


if __name__ == "__main__":
    unittest.main()
