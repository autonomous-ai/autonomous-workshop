"""Mechanical guards for Runtime, Artifact, and Integration ownership."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from workshop.artifacts import load_artifact_payload, validate_artifact_payload
from workshop.deliver import DeliveryDoor, DeliveryPort
from workshop.instructions import LaunchPort
from workshop.integrations import Adapter
from workshop.integrations.doors import (
    CadDoor as LegacyCadDoor,
    DeliveryDoor as LegacyDeliveryDoor,
    SendDoor as LegacySendDoor,
)
from workshop.integrations.ports import (
    CadPort as LegacyCadPort,
    DeliveryPort as LegacyDeliveryPort,
    LaunchPort as LegacyLaunchPort,
)
from workshop.integrations.receipts import Receipt as LegacyReceipt
from workshop.make import CadDoor
from workshop.runtime import Receipt, SendDoor


SOURCE = Path(__file__).resolve().parents[2] / "src" / "workshop"


def _imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            yield node.module or "", tuple(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, ()


class RuntimeIntegrationBoundaryTest(unittest.TestCase):
    def test_runtime_never_imports_an_integration(self):
        violations = []
        for path in sorted((SOURCE / "runtime").glob("*.py")):
            for module, _ in _imports(path):
                if module == "workshop.integrations" or module.startswith(
                    "workshop.integrations."
                ):
                    violations.append("%s -> %s" % (path.name, module))
        self.assertEqual(violations, [])

    def test_integrations_use_only_public_artifact_and_runtime_names(self):
        violations = []
        for path in sorted((SOURCE / "integrations").glob("*.py")):
            for module, names in _imports(path):
                if module.startswith(("workshop.artifacts", "workshop.runtime")):
                    for name in names:
                        if name.startswith("_"):
                            violations.append("%s -> %s.%s" % (path.name, module, name))
        self.assertEqual(violations, [])

    def test_contracts_and_ports_are_owned_upstream(self):
        self.assertIs(LegacyReceipt, Receipt)
        self.assertEqual(Receipt.__module__, "workshop.runtime.contracts")
        self.assertIs(Adapter, __import__("workshop.runtime", fromlist=["Adapter"]).Adapter)
        self.assertIs(LegacySendDoor, SendDoor)
        self.assertIs(LegacyCadDoor, CadDoor)
        self.assertIs(LegacyCadPort, CadDoor)
        self.assertIs(LegacyDeliveryDoor, DeliveryDoor)
        self.assertIs(LegacyDeliveryPort, DeliveryPort)
        self.assertIs(LegacyLaunchPort, LaunchPort)

    def test_artifact_effect_boundary_is_documented_and_public(self):
        self.assertEqual(load_artifact_payload.__name__, "load_artifact_payload")
        self.assertEqual(validate_artifact_payload.__name__, "validate_artifact_payload")

    def test_factory_canonicalization_lives_with_factory_adapter(self):
        store_source = (SOURCE / "runtime" / "store.py").read_text(encoding="utf-8")
        factory_source = (
            SOURCE / "integrations" / "factory_contracts.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("def _validate_factory_assembly", store_source)
        self.assertIn("def validate_factory_assembly_parts", factory_source)
        self.assertIn("def bind_factory_assembly_parts", factory_source)


if __name__ == "__main__":
    unittest.main()
