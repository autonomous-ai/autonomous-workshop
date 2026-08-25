import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workshop.errors import ManifestError
import workshop.contributors.taste as taste_module
from workshop.contributors.taste import (
    MAX_TASTE_DESCRIPTION_CHARS,
    load_taste,
    load_taste_header,
    load_taste_profile,
)


class TasteTest(unittest.TestCase):
    def test_loader_binds_exact_root_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "ada"
            root.mkdir()
            source = (
                b"---\r\n"
                b"name: Ada\r\n"
                b"description: Makes tactile mechanisms with legible physical cause and effect.\r\n"
                b"---\r\n\r\n"
                b"# Ada's taste\r\n\r\nBright, tactile mechanisms.\r\n"
            )
            (root / "TASTE.md").write_bytes(source)

            taste = load_taste(root)

            self.assertEqual(taste.path, (root / "TASTE.md").resolve())
            self.assertEqual(taste.content.encode("utf-8"), source)
            self.assertEqual(taste.sha256, hashlib.sha256(source).hexdigest())
            self.assertEqual(taste.to_binding()["bytes"], len(source))
            self.assertEqual(taste.to_binding()["path"], "TASTE.md")
            self.assertEqual(taste.name, "Ada")
            self.assertEqual(taste.header, load_taste_header(root))

    def test_header_loader_discloses_only_frontmatter_and_body_changes_independently(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "ada"
            root.mkdir()
            path = root / "TASTE.md"
            path.write_text(
                "---\n"
                "name: Ada\n"
                "description: Makes kinetic mathematical instruments.\n"
                "---\n\n"
                "# Secret constitution\n\nBODY-SENTINEL\n",
                encoding="utf-8",
            )
            with mock.patch.object(
                taste_module, "_read_taste_bytes"
            ) as full_reader:
                header = load_taste_header(root)
            full_reader.assert_not_called()
            self.assertEqual(header.name, "Ada")
            self.assertNotIn("BODY-SENTINEL", json.dumps(header.to_binding()))
            first_sha = header.sha256
            path.write_text(
                path.read_text(encoding="utf-8") + "Changed body only.\n",
                encoding="utf-8",
            )
            self.assertEqual(load_taste_header(root).sha256, first_sha)

    def test_frontmatter_is_strict_and_description_is_bounded(self):
        invalid = (
            "# no frontmatter\nBody\n",
            "---\ndescription: Missing name\nname: Wrong order\n---\nBody\n",
            "---\nname: Ada\nsummary: Wrong field\n---\nBody\n",
            "---\nname: Ada\ndescription: Fine\nextra: no\n---\nBody\n",
            "---\nname: Ada\ndescription: %s\n---\nBody\n"
            % ("x" * (MAX_TASTE_DESCRIPTION_CHARS + 1)),
            "---\nname: Ada\ndescription: Fine\n---\n",
        )
        for index, source in enumerate(invalid):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "ada"
                root.mkdir()
                (root / "TASTE.md").write_text(source, encoding="utf-8")
                with self.assertRaises(ManifestError):
                    load_taste(root)

    def test_loader_requires_immediate_regular_taste_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "ada"
            root.mkdir()
            with self.assertRaises(ManifestError):
                load_taste(root)
            (root / "TASTE.md").write_text(" \n", encoding="utf-8")
            with self.assertRaises(ManifestError):
                load_taste(root)

    def test_former_loader_is_the_same_compatibility_function(self):
        self.assertIs(load_taste_profile, load_taste)

if __name__ == "__main__":
    unittest.main()
