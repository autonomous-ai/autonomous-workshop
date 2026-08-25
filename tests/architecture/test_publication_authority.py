import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_ROOTS = (ROOT / "src" / "workshop", ROOT / "tools")


def production_python():
    for root in PRODUCTION_ROOTS:
        yield from sorted(root.rglob("*.py"))


class PublicationAuthorityTest(unittest.TestCase):
    """Keep Factory's copy/media ownership from regressing silently."""

    def test_no_production_code_contains_remote_page_mutation_endpoints(self):
        forbidden = ("/uploads", "/use-case", "/story-blocks", 'name="thumbnails"')
        for path in production_python():
            source = path.read_text(encoding="utf-8")
            for marker in forbidden:
                with self.subTest(path=path.relative_to(ROOT), marker=marker):
                    self.assertNotIn(marker, source)

    def test_no_production_code_calls_retired_page_mutators(self):
        forbidden_calls = {
            "upload_file_bytes",
            "patch_use_case",
            "put_story_blocks",
            "prepare_shop_effect",
            "begin_shop_effect",
            "mark_shop_effect_succeeded",
        }
        for path in production_python():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = (
                    node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else node.func.id
                    if isinstance(node.func, ast.Name)
                    else None
                )
                with self.subTest(path=path.relative_to(ROOT), line=node.lineno):
                    self.assertNotIn(name, forbidden_calls)
                for keyword in node.keywords:
                    if keyword.arg not in ("thumbnail", "attachments"):
                        continue
                    safe_none = isinstance(keyword.value, ast.Constant) and keyword.value.value is None
                    safe_empty = isinstance(keyword.value, (ast.Tuple, ast.List)) and not keyword.value.elts
                    self.assertTrue(
                        safe_none or safe_empty,
                        "%s:%d supplies creator media through %s"
                        % (path.relative_to(ROOT), node.lineno, keyword.arg),
                    )
                if name in ("publish", "publish_live"):
                    self.assertFalse(
                        any(keyword.arg == "title" for keyword in node.keywords),
                        "%s:%d supplies creator page title copy"
                        % (path.relative_to(ROOT), node.lineno),
                    )

    def test_default_instructions_has_no_production_media_provider(self):
        for path in production_python():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "DefaultInstructions"
                ):
                    continue
                self.assertLessEqual(
                    len(node.args),
                    1,
                    "%s:%d uses the retired two-provider Instructions API"
                    % (path.relative_to(ROOT), node.lineno),
                )
                self.assertFalse(
                    any(keyword.arg == "media_maker" for keyword in node.keywords),
                    "%s:%d configures creator page media"
                    % (path.relative_to(ROOT), node.lineno),
                )

    def test_store_schema_cannot_persist_new_page_mutations(self):
        source = (ROOT / "src" / "workshop" / "runtime" / "store.py").read_text(
            encoding="utf-8"
        ).casefold()
        for statement in (
            "create table if not exists shop_effects",
            "insert into shop_effects",
            "update shop_effects",
            "delete from shop_effects",
        ):
            self.assertNotIn(statement, source)


if __name__ == "__main__":
    unittest.main()
