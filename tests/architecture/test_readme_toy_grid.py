import re
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
README = REPOSITORY / "README.md"
_IMG = re.compile(
    r'<img\s+[^>]*src="([^"]+)"[^>]*width="(\d+)"',
    re.IGNORECASE,
)
_TR = re.compile(r"<tr\b", re.IGNORECASE)
_TD = re.compile(r"<td\b", re.IGNORECASE)


class ReadmeToyGridTest(unittest.TestCase):
    def test_opener_grid_is_two_by_three_of_small_existing_toys(self):
        text = README.read_text(encoding="utf-8")
        heading = text.find("\n# ")
        self.assertGreater(heading, 0)
        grid = text[:heading]
        self.assertTrue(grid.lstrip().startswith("<table>"))
        self.assertEqual(len(_TR.findall(grid)), 2)
        self.assertEqual(len(_TD.findall(grid)), 6)
        images = _IMG.findall(grid)
        self.assertEqual(len(images), 6)
        gifs = 0
        for relative, width in images:
            self.assertTrue(180 <= int(width) <= 280)
            path = REPOSITORY / relative
            self.assertTrue(path.is_file(), "%s is missing" % relative)
            if path.suffix.lower() == ".gif":
                gifs += 1
        self.assertGreaterEqual(gifs, 2)


if __name__ == "__main__":
    unittest.main()
