"""Issue #201 (ADR 0096 pilot B10/B15): the Wish's name line names the toy.

build-a-toy opens the Wish with ``Name this toy exactly: <title> v01.`` (or
``Name this revision exactly: ... vNN.``). The Make finalizer refuses a
product title other than that name, so the version reaches the toy's name;
a Wish without the line, or a run with no materialized WISH.json, names
nothing, and a WISH.json not bound to the assignment still refuses."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

TOOL = (
    Path(__file__).resolve().parents[2]
    / ".agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("stage_proposal_name_line_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TOOLMOD = _load()


def _run_root(tmp: str, objective: str) -> tuple[Path, str]:
    root = Path(tmp)
    content = json.dumps({"objective": objective}).encode("utf-8")
    (root / "WISH.json").write_bytes(content)
    return root, hashlib.sha256(content).hexdigest()


class WishNameTest(unittest.TestCase):
    def test_a_toy_and_a_revision_name_line(self):
        self.assertEqual(
            TOOLMOD.wish_name("Name this toy exactly: Beaver Coaster Keeper v01.\n\n# Beaver"),
            "Beaver Coaster Keeper v01",
        )
        self.assertEqual(TOOLMOD.wish_name("Name this revision exactly: Broken God v09.\nbody"), "Broken God v09")

    def test_no_name_line_names_nothing(self):
        for objective in ("# Beaver\n\nName this toy exactly: X v01.", "", None, 7, "Name this toy exactly: ."):
            self.assertIsNone(TOOLMOD.wish_name(objective), objective)


class NamedTitleTest(unittest.TestCase):
    def test_the_named_title_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, sha = _run_root(tmp, "Name this toy exactly: Beaver Coaster Keeper v01.\n\nbody")
            TOOLMOD._require_named_title(root, sha, "Beaver Coaster Keeper v01")
            TOOLMOD._require_named_title(root, sha, " Beaver Coaster Keeper v01 ")

    def test_a_title_without_the_version_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, sha = _run_root(tmp, "Name this toy exactly: Beaver Coaster Keeper v01.\n\nbody")
            for title in ("Beaver Coaster Keeper", "Beaver Coaster Keeper v02", None):
                with self.assertRaisesRegex(TOOLMOD.ProposalError, "must be exactly 'Beaver Coaster Keeper v01'"):
                    TOOLMOD._require_named_title(root, sha, title)

    def test_a_wish_without_a_name_line_takes_any_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, sha = _run_root(tmp, "A beaver that keeps coasters.")
            TOOLMOD._require_named_title(root, sha, "Anything At All")

    def test_a_run_without_a_materialized_wish_is_not_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            TOOLMOD._require_named_title(Path(tmp), "0" * 64, "Anything")

    def test_an_unbound_wish_still_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = _run_root(tmp, "Name this toy exactly: X v01.")
            with self.assertRaisesRegex(TOOLMOD.ProposalError, "does not match its assignment binding"):
                TOOLMOD._require_named_title(root, "0" * 64, "X v01")

    def test_make_checks_the_title_where_it_reads_it(self):
        source = TOOL.read_text(encoding="utf-8")
        read = source.index('_bounded_text(product.get("title"), "Make product title", 2_000)')
        self.assertIn(
            '_require_named_title(run_root, assignment["wish_sha256"], product["title"])',
            source[read : read + 200],
        )


if __name__ == "__main__":
    unittest.main()
