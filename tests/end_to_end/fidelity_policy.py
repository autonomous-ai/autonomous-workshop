"""Static policy guard for the deterministic production-boundary E2E suite."""

from __future__ import annotations

import ast
from pathlib import Path


DETERMINISTIC_E2E_FILES = (
    "deterministic_codex.py",
    "deterministic_fidelity.py",
    "fidelity_policy.py",
    "test_deterministic_native_fidelity.py",
)
APPROVED_PATCH_TARGETS = frozenset(
    {
        "workshop.workflow.native_run._FACTORY_TRANSPORT",
        "workshop.workflow.native_run._FACTORY_PROJECT_FILE_TRANSPORT",
    }
)
FORBIDDEN_INTERNAL_TERMS = frozenset(
    {
        "launcher",
        "stage_evaluator",
        "finalizer_override",
        "contract_reader",
        "checkpoint_store",
        "verify_native_made_cad",
        "native_cad_gate",
        "release_writer",
        "factory_session",
        "public_transition",
        "apply_outcome",
        "gate_receipt",
        "stage_result",
    }
)
FORBIDDEN_TRANSPORT_FILE_MUTATORS = frozenset(
    {
        "chmod",
        "mkdir",
        "open",
        "rename",
        "replace",
        "rmdir",
        "unlink",
        "write_bytes",
        "write_text",
    }
)


def _literal_text(node: ast.AST) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def fidelity_policy_violations(source: str, *, filename: str) -> tuple[str, ...]:
    tree = ast.parse(source, filename=filename)
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name.endswith("Transport"):
            for child in ast.walk(node):
                if (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Attribute)
                    and child.func.attr in FORBIDDEN_TRANSPORT_FILE_MUTATORS
                ):
                    violations.append(
                        "%s:%d transport mutates files with %s"
                        % (filename, child.lineno, child.func.attr)
                    )
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
            for argument in arguments:
                if argument.arg == "monkeypatch" or argument.arg in FORBIDDEN_INTERNAL_TERMS:
                    violations.append("%s:%d injects internal %s" % (filename, node.lineno, argument.arg))
        if isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute) else ""
            )
            if name in {"setattr", "fixture", "fixture_factory"}:
                violations.append("%s:%d calls %s" % (filename, node.lineno, name))
            if name == "patch":
                target = _literal_text(node.args[0]) if node.args else None
                if target not in APPROVED_PATCH_TARGETS:
                    violations.append("%s:%d patches internal %s" % (filename, node.lineno, target))
            for keyword in node.keywords:
                if keyword.arg in FORBIDDEN_INTERNAL_TERMS:
                    violations.append(
                        "%s:%d injects internal %s" % (filename, node.lineno, keyword.arg)
                    )
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("tests.") and any(
                term in node.module for term in ("fixture", "fake_stage", "mock_session")
            ):
                violations.append("%s:%d imports phase fixture %s" % (filename, node.lineno, node.module))
    return tuple(sorted(set(violations)))


def deterministic_e2e_paths() -> tuple[Path, ...]:
    root = Path(__file__).resolve().parent
    return tuple(root / name for name in DETERMINISTIC_E2E_FILES)


__all__ = [
    "APPROVED_PATCH_TARGETS",
    "DETERMINISTIC_E2E_FILES",
    "deterministic_e2e_paths",
    "fidelity_policy_violations",
]
