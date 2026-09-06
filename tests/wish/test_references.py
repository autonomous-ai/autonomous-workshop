import hashlib
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from workshop.errors import ContractError
from workshop.wish import load_wish_references, wish_reference_files
from workshop.wish.contracts import MAX_WISH_REFERENCES


class LoadWishReferencesTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def _image(self, name, size=(64, 48), image_format=None, mode="RGB", **save):
        path = self.root / name
        Image.new(mode, size, "red").save(path, image_format, **save)
        return path

    def test_images_load_in_order_with_slug_names_and_exact_bytes(self):
        side = self._image("HAER Side Élévation (sheet 3).jpg")
        front = self._image("front.png", size=(32, 32), mode="RGBA")
        cab = self._image("cab-rear.webp", size=(20, 30))

        loaded = load_wish_references([side, front, cab])

        self.assertEqual(
            [item.reference.name for item in loaded],
            ["ref-01-haer-side-elevation-sheet-3.jpg", "ref-02-front.png", "ref-03-cab-rear.webp"],
        )
        self.assertEqual(
            [item.reference.media_type for item in loaded],
            ["image/jpeg", "image/png", "image/webp"],
        )
        self.assertEqual(
            [(item.reference.width, item.reference.height) for item in loaded],
            [(64, 48), (32, 32), (20, 30)],
        )
        for item, path in zip(loaded, (side, front, cab)):
            self.assertEqual(item.content, path.read_bytes())
            self.assertEqual(item.reference.size, len(item.content))
            self.assertEqual(
                item.reference.sha256, hashlib.sha256(item.content).hexdigest()
            )
        files = wish_reference_files(loaded)
        self.assertEqual(list(files), [item.reference.name for item in loaded])
        self.assertEqual(files["ref-02-front.png"], front.read_bytes())
        self.assertEqual(load_wish_references([]), ())

    def test_unsupported_or_unreadable_files_are_rejected_by_name(self):
        gif = self._image("spinner.gif")
        text = self.root / "notes.txt"
        text.write_text("not an image\n", encoding="utf-8")
        empty = self.root / "empty.png"
        empty.write_bytes(b"")
        tiny = self._image("tiny.png", size=(8, 8))
        frames = [Image.new("RGB", (16, 16), colour) for colour in ("red", "blue")]
        animated = self.root / "blink.png"
        frames[0].save(animated, save_all=True, append_images=frames[1:])

        cases = (
            (gif, "must be PNG, JPEG, or WebP"),
            (text, "not a readable PNG, JPEG, or WebP"),
            (empty, "is empty"),
            (tiny, "px per side"),
            (animated, "must not be animated"),
            (self.root / "missing.png", "not a readable file"),
            (self.root, "not a readable file"),
        )
        for path, message in cases:
            with self.subTest(path=path.name), self.assertRaisesRegex(
                ContractError, message
            ):
                load_wish_references([path])

    def test_duplicates_and_too_many_files_are_rejected(self):
        first = self._image("front.png")
        copy = self.root / "front-copy.png"
        copy.write_bytes(first.read_bytes())
        with self.assertRaisesRegex(ContractError, "repeats the bytes of front.png"):
            load_wish_references([first, copy])
        with self.assertRaisesRegex(ContractError, "at most %d" % MAX_WISH_REFERENCES):
            load_wish_references([first] * (MAX_WISH_REFERENCES + 1))
        with self.assertRaisesRegex(ContractError, "must be a list"):
            load_wish_references(str(first))


if __name__ == "__main__":
    unittest.main()
