"""B13 (ADR 0096 pilot): every instance in an assembly STEP has its own label.

Instances of one solid share a definition, and the STEP writer gives a shared
solid one PRODUCT, so the beaver's four coasters were all read back as
``coaster_4_dark_oak``, the last instance's name. cadgen now gives an instance
named differently its own copy of the B-rep, so each PRODUCT keeps its name;
instances named alike still share one definition."""

from __future__ import annotations

import importlib
import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path

from workshop.runtime.package_data import product_run_domain_skill_roots

CADGEN_SRC = product_run_domain_skill_roots()["cad"] / "scripts" / "packages" / "cadgen" / "src"
HAS_CAD = importlib.util.find_spec("build123d") is not None and importlib.util.find_spec("OCP") is not None


def _skill_step_export():
    """The skill tree's own cadgen, not whichever copy is installed."""

    saved = {name: module for name, module in sys.modules.items() if name == "cadgen" or name.startswith("cadgen.")}
    for name in saved:
        del sys.modules[name]
    sys.path.insert(0, str(CADGEN_SRC))
    try:
        module = importlib.import_module("cadgen.step_export")
    finally:
        sys.path.remove(str(CADGEN_SRC))
        for name in [n for n in sys.modules if n == "cadgen" or n.startswith("cadgen.")]:
            del sys.modules[name]
        sys.modules.update(saved)
    return module


def _leaf_labels(node) -> list[str]:
    children = list(getattr(node, "children", ()) or ())
    if not children:
        return [node.label]
    return [label for child in children for label in _leaf_labels(child)]


@unittest.skipUnless(HAS_CAD, "needs build123d and OCP")
class StepInstanceLabelTest(unittest.TestCase):
    def _export(self, labels: list[str]) -> tuple[list[str], str]:
        import build123d as bd

        step_export = _skill_step_export()
        self.assertTrue(Path(step_export.__file__).is_relative_to(CADGEN_SRC), step_export.__file__)
        base = bd.Cylinder(10, 3)
        children = []
        for index, label in enumerate(labels, 1):
            child = base.moved(bd.Location((0, 0, 4 * index)))
            child.label = label
            children.append(child)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stack.step"
            step_export.export_build123d_step_file(bd.Compound(children=children, label="stack"), path)
            text = path.read_text(encoding="utf-8", errors="replace")
            imported = bd.import_step(str(path))
        return _leaf_labels(imported), text

    def test_each_differently_named_instance_keeps_its_own_label(self):
        names = ["coaster_%d_dark_oak" % n for n in range(1, 5)]
        labels, text = self._export(names)
        self.assertEqual(sorted(labels), names)
        products = set(re.findall(r"PRODUCT\('([^']*)'", text))
        self.assertTrue(set(names) <= products, products)

    def test_instances_named_alike_still_share_one_definition(self):
        labels, text = self._export(["eye_black", "eye_black"])
        self.assertEqual(labels, ["eye_black", "eye_black"])
        # One cylinder's three faces: the shared B-rep was not copied.
        self.assertEqual(len(re.findall(r"ADVANCED_FACE\(", text)), 3)


if __name__ == "__main__":
    unittest.main()
