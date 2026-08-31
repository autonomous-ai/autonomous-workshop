import ast
import tokenize
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
SOURCE = REPOSITORY / "src"
WORKSHOP = SOURCE / "workshop"
EXPECTED_COMPONENTS = {
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
FORBIDDEN_NAMESPACES = {
    "autonomous_workshop",
    "inventor_core",
    "inventor_foundation",
    "inventor_workshop",
    "workshop_cli",
}
SCHEMA_OWNERS = {
    "artifact-manifest.schema.json": "artifacts",
    "inventor.schema.json": "contributors",
    "cad-project.schema.json": "make",
    "validator-policy.schema.json": "make",
    "verification-receipt.schema.json": "make",
    "receipt.schema.json": "runtime",
    "concept-v1.schema.json": "concept",
    "concept-v2.schema.json": "concept",
}


def _python_imports(path: Path):
    with tokenize.open(path) as source:
        tree = ast.parse(source.read(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


class ComponentLayoutTest(unittest.TestCase):
    def test_only_final_source_namespaces_exist(self):
        for namespace in FORBIDDEN_NAMESPACES:
            self.assertFalse(
                (SOURCE / namespace).exists(),
                "%s must be removed after the namespace migration" % namespace,
            )
        self.assertTrue((SOURCE / "cli" / "main.py").is_file())
        self.assertFalse(
            (SOURCE / "cli" / "native_run.py").exists(),
            "the trusted native host belongs to Workflow, not the CLI",
        )
        self.assertTrue((WORKSHOP / "workflow" / "native_run.py").is_file())
        self.assertTrue((WORKSHOP / "__init__.py").is_file())

    def test_workshop_has_the_architecture_component_packages(self):
        actual = {
            path.name
            for path in WORKSHOP.iterdir()
            if path.is_dir() and (path / "__init__.py").is_file()
        }
        self.assertEqual(actual, EXPECTED_COMPONENTS)

    def test_removed_flat_hubs_cannot_return(self):
        for name in ("__main__.py", "cli.py", "jobs.py", "models.py"):
            self.assertFalse(
                (WORKSHOP / name).exists(),
                "%s must stay in its owning package(s)" % name,
            )
        self.assertFalse(
            (WORKSHOP / "workflow" / "creation.py").exists(),
            "the removed workflow creation compatibility shim must stay absent",
        )

    def test_cli_tests_stay_in_the_top_level_test_suite(self):
        self.assertFalse(
            (SOURCE / "cli" / "tests").exists(),
            "CLI tests belong under tests/cli, outside the installed package",
        )
        misplaced = sorted(
            path.relative_to(SOURCE)
            for path in (SOURCE / "cli").rglob("*.py")
            if path.name.startswith("test_") or path.name.endswith("_test.py")
        )
        self.assertEqual(misplaced, [])
        self.assertTrue((REPOSITORY / "tests" / "cli").is_dir())
        self.assertFalse(
            (REPOSITORY / "tests" / "cli" / "test_native_run.py").exists()
        )
        self.assertFalse(
            (REPOSITORY / "tests" / "cli" / "test_native_full_run.py").exists()
        )
        self.assertTrue(
            (REPOSITORY / "tests" / "workflow" / "test_native_host.py").is_file()
        )
        self.assertTrue(
            (
                REPOSITORY
                / "tests"
                / "end_to_end"
                / "test_native_full_run.py"
            ).is_file()
        )

    def test_resources_live_with_their_owning_components(self):
        self.assertFalse((REPOSITORY / "skills").exists())
        self.assertFalse((REPOSITORY / "schemas").exists())
        self.assertTrue((WORKSHOP / "make" / "skill_registry.py").is_file())
        self.assertTrue((WORKSHOP / "make" / "skills" / "LOCK.json").is_file())
        self.assertFalse((WORKSHOP / "make" / "skills.py").exists())
        self.assertTrue((WORKSHOP / "artifacts" / "schema_registry.py").is_file())
        self.assertFalse((WORKSHOP / "artifacts" / "schemas.py").exists())
        for name, owner in SCHEMA_OWNERS.items():
            self.assertTrue(
                (WORKSHOP / owner / "schemas" / name).is_file(),
                "%s must be owned by workshop.%s" % (name, owner),
            )

    def test_python_never_imports_a_removed_namespace(self):
        offenders = []
        for path in REPOSITORY.rglob("*.py"):
            if not path.is_file():
                continue
            if any(
                part in {".git", ".runtime", "build", "dist", "toys"}
                or part.startswith(".venv")
                for part in path.parts
            ):
                continue
            for imported in _python_imports(path):
                if imported.split(".", 1)[0] in FORBIDDEN_NAMESPACES:
                    offenders.append("%s imports %s" % (path.relative_to(REPOSITORY), imported))
        self.assertEqual(offenders, [])

    def test_library_never_depends_on_the_cli_package(self):
        offenders = []
        for path in WORKSHOP.rglob("*.py"):
            if (WORKSHOP / "make" / "skills") in path.parents:
                continue
            for imported in _python_imports(path):
                if imported == "cli" or imported.startswith("cli."):
                    offenders.append("%s imports %s" % (path.relative_to(REPOSITORY), imported))
        self.assertEqual(offenders, [])

    def test_foundational_component_boundaries_are_one_way(self):
        forbidden = {
            "product": {"workshop.contributors"},
            "contributors": {"workshop.match", "workshop.workflow"},
            "workflow": {"workshop.bootstrap"},
        }
        offenders = []
        for component, prefixes in forbidden.items():
            for path in (WORKSHOP / component).rglob("*.py"):
                for imported in _python_imports(path):
                    if any(
                        imported == prefix or imported.startswith(prefix + ".")
                        for prefix in prefixes
                    ):
                        offenders.append(
                            "%s imports %s"
                            % (path.relative_to(REPOSITORY), imported)
                        )
        self.assertEqual(offenders, [])

    def test_component_packages_expose_stable_public_contracts(self):
        from workshop import contributors, invent, make, match, playtest, product, workflow

        expected = {
            contributors: {
                "InventorManifest",
                "Taste",
                "create_inventor",
                "validate_inventor_collection",
            },
            product: {
                "BASELINE_PLAYTEST_CHECKS",
                "ToyBlueprint",
            },
            match: {
                "MatchRankingEntry",
                "NativeMatchAssignment",
                "InventorRoster",
                "InventorRosterEntry",
            },
            invent: {
                "NativeInvented",
            },
            make: {
                "Made",
                "NativeMade",
            },
            playtest: {
                "Feedback",
                "NativePlaytestCheck",
                "NativePlaytested",
                "Playtest",
                "PlaytestResult",
                "Playtested",
            },
            workflow: {
                "AgentArtifact",
                "AgentOutcome",
                "AgentRun",
                "AgentRunCheckpoint",
                "DeterministicGateReceipt",
            },
        }
        for package, names in expected.items():
            with self.subTest(package=package.__name__):
                self.assertTrue(names <= set(package.__all__))
                self.assertTrue(all(hasattr(package, name) for name in names))
        self.assertEqual(
            set(product.__all__),
            {
                "BASELINE_PLAYTEST_CHECKS",
                "ToyBlueprint",
                "attribute_product_description",
            },
        )
        self.assertEqual(set(invent.__all__), {"NativeInvented"})
        self.assertEqual(
            set(make.__all__),
            {
                "Made",
                "MakeInventRevisionFeedback",
                "NativeMade",
                "NativeMakeInventRevision",
            },
        )
        self.assertNotIn("Feedback", make.__all__)
        self.assertIn("Feedback", playtest.__all__)


if __name__ == "__main__":
    unittest.main()
