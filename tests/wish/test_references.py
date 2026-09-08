import hashlib
import http.server
import socket
import tempfile
import threading
import unittest
import urllib.parse
from pathlib import Path

from PIL import Image

from workshop.errors import ContractError
from workshop.wish import (
    is_reference_url,
    load_wish_references,
    wish_reference_files,
    wish_reference_sources,
)
from workshop.wish.contracts import MAX_WISH_REFERENCE_BYTES, MAX_WISH_REFERENCES


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
        self.assertEqual(wish_reference_sources(load_wish_references([first])), {})


class _ReferenceServer(http.server.ThreadingHTTPServer):
    """A loopback origin: files from a directory plus a few scripted routes."""

    daemon_threads = True

    def __init__(self, root: Path):
        self.root = root
        super().__init__(("127.0.0.1", 0), _ReferenceHandler)

    @property
    def url(self) -> str:
        return "http://127.0.0.1:%d" % self.server_address[1]


class _ReferenceHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_args):  # quiet
        return

    def do_GET(self):
        path = urllib.parse.unquote(self.path.split("?", 1)[0])
        if path == "/":
            path = "/front.png"
        if path == "/moved":
            self.send_response(302)
            self.send_header("Location", "/front.png")
            self.end_headers()
            return
        if path == "/escape":
            self.send_response(302)
            self.send_header("Location", "file:///etc/hostname")
            self.end_headers()
            return
        if path == "/ftp":
            self.send_response(302)
            self.send_header("Location", "ftp://127.0.0.1/front.png")
            self.end_headers()
            return
        if path == "/huge.png":
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(MAX_WISH_REFERENCE_BYTES + 1))
            self.end_headers()
            return
        if path == "/endless.png":
            # No Content-Length: only the streamed byte cap can stop this one.
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.end_headers()
            chunk = b"\0" * 65536
            try:
                for _ in range(MAX_WISH_REFERENCE_BYTES // len(chunk) + 2):
                    self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        target = self.server.root / path.lstrip("/")
        if not target.is_file():
            self.send_response(404)
            self.end_headers()
            return
        content = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


class LoadWishReferenceLinksTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.server = _ReferenceServer(self.root)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = self.server.url

    def _image(self, name, size=(64, 48), mode="RGB", colour="red"):
        path = self.root / name
        Image.new(mode, size, colour).save(path)
        return path

    def test_links_are_downloaded_once_named_by_their_path_and_bound_by_bytes(self):
        front = self._image("front.png")
        duck = self._image("Wind-Up Duck (grey).webp", size=(20, 30), colour="blue")
        side = self._image("side.jpg", colour="green")

        loaded = load_wish_references(
            [
                self.url + "/front.png?download=1",
                self.url + "/Wind-Up%20Duck%20(grey).webp",
                side,
            ]
        )

        self.assertEqual(
            [item.reference.name for item in loaded],
            ["ref-01-front.png", "ref-02-wind-up-duck-grey.webp", "ref-03-side.jpg"],
        )
        self.assertEqual(loaded[0].content, front.read_bytes())
        self.assertEqual(loaded[1].content, duck.read_bytes())
        self.assertEqual(loaded[0].reference.sha256, hashlib.sha256(front.read_bytes()).hexdigest())
        self.assertEqual((loaded[1].reference.width, loaded[1].reference.height), (20, 30))
        self.assertEqual([item.downloaded for item in loaded], [True, True, False])
        self.assertEqual(loaded[2].source, str(side))
        self.assertEqual(
            wish_reference_sources(loaded),
            {
                "ref-01-front.png": self.url + "/front.png?download=1",
                "ref-02-wind-up-duck-grey.webp": self.url + "/Wind-Up%20Duck%20(grey).webp",
            },
        )
        self.assertEqual(
            wish_reference_files(loaded)["ref-02-wind-up-duck-grey.webp"], duck.read_bytes()
        )

    def test_a_redirect_within_http_is_followed_and_a_bare_origin_is_still_named(self):
        front = self._image("front.png")
        loaded = load_wish_references([self.url + "/moved"])
        self.assertEqual(loaded[0].content, front.read_bytes())
        self.assertEqual(loaded[0].reference.name, "ref-01-moved.png")
        self.assertEqual(
            load_wish_references([self.url + "/"])[0].reference.name, "ref-01-image.png"
        )

    def test_bad_links_are_rejected_with_the_link_named(self):
        self._image("front.png")
        (self.root / "notes.txt").write_text("not an image\n", encoding="utf-8")
        closed = socket.socket()
        closed.bind(("127.0.0.1", 0))
        refused = "http://127.0.0.1:%d/front.png" % closed.getsockname()[1]
        closed.close()

        cases = (
            (self.url + "/missing.png", "returned HTTP 404"),
            (self.url + "/notes.txt", "not a readable PNG, JPEG, or WebP"),
            (self.url + "/huge.png", "exceeds %d bytes" % MAX_WISH_REFERENCE_BYTES),
            (self.url + "/endless.png", "exceeds %d bytes" % MAX_WISH_REFERENCE_BYTES),
            (self.url + "/escape", "redirected to a location the Workshop will not follow"),
            (self.url + "/ftp", "could not be downloaded.*non-http"),
            (refused, "could not be downloaded"),
        )
        for link, message in cases:
            with self.subTest(link=link), self.assertRaisesRegex(ContractError, message) as caught:
                load_wish_references([link])
            self.assertIn(link, str(caught.exception))

    def test_a_link_and_a_file_with_the_same_bytes_are_one_duplicate(self):
        front = self._image("front.png")
        with self.assertRaisesRegex(ContractError, "repeats the bytes of front.png"):
            load_wish_references([front, self.url + "/front.png"])

    def test_only_http_strings_are_links(self):
        self.assertTrue(is_reference_url("https://example.test/a.png"))
        self.assertTrue(is_reference_url("HTTP://example.test/a.png"))
        self.assertFalse(is_reference_url("ftp://example.test/a.png"))
        self.assertFalse(is_reference_url("file:///etc/hostname"))
        self.assertFalse(is_reference_url("front.png"))
        self.assertFalse(is_reference_url(Path("https://example.test/a.png")))
        with self.assertRaisesRegex(ContractError, "not a readable file"):
            load_wish_references([Path(self.url + "/front.png")])


if __name__ == "__main__":
    unittest.main()
