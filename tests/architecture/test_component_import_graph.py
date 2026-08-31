"""Static guards for the component-level module-load dependency graph."""

from __future__ import annotations

import ast
import tokenize
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
WORKSHOP = REPOSITORY / "src" / "workshop"
COMPONENTS = {
    "artifacts",
    "concept",
    "contributors",
    "release",
    "integrations",
    "invent",
    "make",
    "match",
    "playtest",
    "product",
    "runtime",
    "wish",
    "workflow",
}


def _tree(path: Path) -> ast.Module:
    with tokenize.open(path) as source:
        return ast.parse(source.read(), filename=str(path))


def _is_type_checking(test: ast.expr) -> bool:
    return (
        isinstance(test, ast.Name)
        and test.id == "TYPE_CHECKING"
        or isinstance(test, ast.Attribute)
        and test.attr == "TYPE_CHECKING"
    )


def _module_load_imports(statements):
    """Yield imports executed while a module loads, excluding definitions."""

    for statement in statements:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                yield alias.name, (), statement.lineno
        elif isinstance(statement, ast.ImportFrom) and statement.module:
            yield (
                statement.module,
                tuple(alias.name for alias in statement.names),
                statement.lineno,
            )
        elif isinstance(statement, ast.If):
            if not _is_type_checking(statement.test):
                yield from _module_load_imports(statement.body)
            yield from _module_load_imports(statement.orelse)
        elif isinstance(statement, (ast.Try, ast.TryStar)):
            yield from _module_load_imports(statement.body)
            for handler in statement.handlers:
                yield from _module_load_imports(handler.body)
            yield from _module_load_imports(statement.orelse)
            yield from _module_load_imports(statement.finalbody)
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            yield from _module_load_imports(statement.body)


def _component(module: str):
    parts = module.split(".")
    if len(parts) >= 2 and parts[0] == "workshop" and parts[1] in COMPONENTS:
        return parts[1]
    return None


def _source_files():
    for owner in sorted(COMPONENTS):
        for path in sorted((WORKSHOP / owner).rglob("*.py")):
            if (WORKSHOP / "make" / "skills") in path.parents:
                continue
            yield owner, path


def _cycle(edges):
    visiting = set()
    visited = set()
    stack = []

    def visit(node):
        if node in visiting:
            start = stack.index(node)
            return stack[start:] + [node]
        if node in visited:
            return None
        visiting.add(node)
        stack.append(node)
        for target in sorted(edges[node]):
            found = visit(target)
            if found:
                return found
        stack.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for node in sorted(edges):
        found = visit(node)
        if found:
            return found
    return None


class ComponentImportGraphTest(unittest.TestCase):
    def test_module_load_component_graph_is_acyclic(self):
        edges = {component: set() for component in COMPONENTS}
        for owner, path in _source_files():
            for module, _names, _line in _module_load_imports(_tree(path).body):
                target = _component(module)
                if target is not None and target != owner:
                    edges[owner].add(target)
        found = _cycle(edges)
        self.assertIsNone(
            found,
            "component module-load cycle: %s"
            % (" -> ".join(found) if found else "unknown"),
        )

    def test_components_never_import_private_sibling_names(self):
        offenders = []
        for owner, path in _source_files():
            for module, names, line in _module_load_imports(_tree(path).body):
                target = _component(module)
                if target is None or target == owner:
                    continue
                for name in names:
                    if name.startswith("_"):
                        offenders.append(
                            "%s:%d imports private %s.%s"
                            % (path.relative_to(REPOSITORY), line, module, name)
                        )
        self.assertEqual(offenders, [])

    def test_domain_components_do_not_import_concrete_integrations(self):
        offenders = []
        for owner, path in _source_files():
            if owner == "integrations":
                continue
            if path == WORKSHOP / "workflow" / "native_run.py":
                # The trusted whole-run host is the sole composition root.
                continue
            for module, _names, line in _module_load_imports(_tree(path).body):
                if _component(module) == "integrations":
                    offenders.append(
                        "%s:%d imports %s"
                        % (path.relative_to(REPOSITORY), line, module)
                    )
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
