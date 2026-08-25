import ast
import unittest
from pathlib import Path

import workshop.make as make
import workshop.playtest as playtest


ROOT = Path(__file__).resolve().parents[2]
MAKE = ROOT / "src" / "workshop" / "make"
PLAYTEST = ROOT / "src" / "workshop" / "playtest"


def imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            yield node.module, tuple(alias.name for alias in node.names), node.lineno
        elif isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, (), node.lineno


def module_load_imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            yield node.module, node.lineno
        elif isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, node.lineno


class MakePlaytestBoundaryTest(unittest.TestCase):
    def test_playtest_never_reaches_into_make_agent_implementation(self):
        offenders = []
        for path in PLAYTEST.rglob("*.py"):
            for module, names, line in imports(path):
                if module == "workshop.make.agent":
                    offenders.append(
                        "%s:%d imports %s"
                        % (path.relative_to(ROOT), line, ", ".join(names) or module)
                    )
        self.assertEqual(offenders, [])

    def test_playtest_uses_make_component_boundary_not_submodules(self):
        offenders = []
        for path in PLAYTEST.rglob("*.py"):
            for module, _names, line in imports(path):
                if module.startswith("workshop.make."):
                    offenders.append(
                        "%s:%d imports %s"
                        % (path.relative_to(ROOT), line, module)
                    )
        self.assertEqual(offenders, [])

    def test_make_has_no_playtest_module_load_dependency(self):
        offenders = []
        for path in MAKE.rglob("*.py"):
            if (MAKE / "skills") in path.parents:
                continue
            for module, line in module_load_imports(path):
                if module == "workshop.playtest" or module.startswith(
                    "workshop.playtest."
                ):
                    offenders.append(
                        "%s:%d imports %s"
                        % (path.relative_to(ROOT), line, module)
                    )
        self.assertEqual(offenders, [])

    def test_component_packages_publish_the_shared_contracts(self):
        for name in (
            "Feedback",
            "Made",
            "MakeContext",
            "CadProjectVerifier",
            "CadDoor",
            "CadInspectionDoor",
            "InspectionDoor",
            "ModelDoor",
            "MOVING_MACHINE_BINDING_KIND",
            "MOVING_MACHINE_BINDING_VERSION",
            "canonical_cad_project_sources",
            "locked_cad_project_verifier",
            "moving_machine_parts",
            "validate_cad_design_action",
            "validate_moving_machine_binding",
            "validate_moving_machine_lane_contract",
        ):
            self.assertIn(name, make.__all__)
            self.assertTrue(hasattr(make, name))
        for name in (
            "Playtest",
            "Playtested",
            "PlaytestContext",
            "PlaytestResult",
            "WorkshopMovingMachineVerifier",
        ):
            self.assertIn(name, playtest.__all__)
            self.assertTrue(hasattr(playtest, name))

    def test_moving_machine_verifier_is_owned_by_playtest(self):
        from workshop.make.moving_machine import (
            WorkshopMovingMachineVerifier as compatibility_verifier,
        )
        from workshop.playtest.moving_machine import WorkshopMovingMachineVerifier

        self.assertIs(compatibility_verifier, WorkshopMovingMachineVerifier)
        self.assertEqual(
            WorkshopMovingMachineVerifier.__module__,
            "workshop.playtest.moving_machine",
        )

    def test_game_simulator_template_is_owned_by_playtest(self):
        make_source = (MAKE / "agent.py").read_text(encoding="utf-8")
        self.assertNotIn("_FINITE_GAME_SIMULATOR =", make_source)
        self.assertTrue(
            playtest.FINITE_GAME_SIMULATOR_SOURCE.startswith(
                "#!/usr/bin/env python3"
            )
        )


if __name__ == "__main__":
    unittest.main()
