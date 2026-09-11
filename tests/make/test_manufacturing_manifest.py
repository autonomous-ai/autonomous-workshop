"""Contract tests; all CAD/media fixtures are synthetic, never manufacture evidence."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/mixed-materials/scripts/manufacturing_manifest.py"
API = runpy.run_path(str(SCRIPT))
ManufacturingManifestError = API["ManufacturingManifestError"]
read_manifest = API["read_manifest"]
validate_manifest = API["validate_manifest"]
public_asset_paths = API["public_asset_paths"]


def encoded(value):
    return (json.dumps(value, sort_keys=True) + "\n").encode()


def bind_file(root: Path, path: str, content: bytes | None = None) -> dict:
    target = root / path
    if content is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return {"path": path, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}


def seal_manifest(root: Path, document: dict) -> dict:
    binding = bind_file(root, "internal/manufacturing.json", encoded(document))
    product = {
        "title": "Synthetic mixed-material product",
        "summary": "An assembled toy; fixture only, not a validated product.",
        "manufacturing": {"schema_version": 1, "manifest_path": binding["path"], "manifest_sha256": binding["sha256"]},
    }
    (root / "product.json").write_bytes(encoded(product))
    return product


def make_mixed_product(root: Path) -> tuple[dict, dict]:
    """Reusable synthetic fixture: return (product facts, internal manifest).

    It includes one printed body, two sheet sides, two cut cord pieces, a
    purchased motor and marble. Call seal_manifest after changing its manifest.
    """
    root.mkdir(parents=True, exist_ok=True)
    display = bind_file(root, "assembled.step", b"ISO-10303-21;\n/* SYNTHETIC FIXTURE */\nEND-ISO-10303-21;\n")
    public_display = bind_file(root, "public/assembled.step", (root / display["path"]).read_bytes())
    # A real tiny PNG, but no claim that it depicts a physical or CAD product.
    png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=")
    hero = bind_file(root, "public/hero.png", png)
    bind_file(root, "cad/assembled.step.py", b"PRINTABLE = False\nraise RuntimeError('CAD MUST NOT EXECUTE')\n")
    body = bind_file(root, "cad/part_body.step.py", b"PRINTABLE = True\nraise RuntimeError('CAD MUST NOT EXECUTE')\n")
    side = bind_file(root, "cad/part_side.step.py", b"PRINTABLE = False\nraise RuntimeError('CAD MUST NOT EXECUTE')\n")
    cut = bind_file(root, "internal/cut-and-fold.md", b"Cut two 120 x 80 mm sides from one sheet. Fold marked 10 mm flanges.\n")
    cord = bind_file(root, "internal/cord.md", b"Cut two 150 mm lengths of 2 mm cord; knot around the marked hooks.\n")
    motor = bind_file(root, "cad/ref/motor.step", b"ISO-10303-21;\n/* SUPPLIER ENVELOPE FIXTURE */\nEND-ISO-10303-21;\n")
    names = ["body", "left_side", "right_side", "left_cord", "right_cord", "drive_motor", "marble"]
    descriptor = bind_file(root, "internal/assembled.step.json", encoded({
        "schemaVersion": 2, "kind": "assembly-package", "entryKind": "assembly", "packageSchemaVersion": 3,
        "rootName": "fixture", "units": "mm", "occurrences": [{"name": name} for name in names], "stats": {"occurrenceCount": len(names)},
    }))
    bind_file(root, "assembled.step.json", (root / descriptor["path"]).read_bytes())
    def component(item_id, family, process, occurrences, files, stock_ids, specification):
        return {"id": item_id, "name": item_id.replace("_", " "), "material": {"family": family, "specification": specification}, "process": process, "quantity": len(occurrences), "occurrences": occurrences, "specification": specification, "files": files, "stock_ids": stock_ids}
    components = [
        component("printed_body", "polymer", "3d-print", ["body"], [body], ["pla_stock"], "PLA, nozzle 0.4 mm, source orientation; nozzle gates are separate evidence."),
        component("card_sides", "paperboard", "cut-fold", ["left_side", "right_side"], [side, cut], ["board_stock"], "1.5 mm E-flute board, 120 x 80 mm blank; cut two per sheet."),
        component("cords", "textile", "cut-to-length", ["left_cord", "right_cord"], [cord], ["cord_stock"], "Two 150 mm cuts of 2 mm cotton cord; final tension requires physical testing."),
        component("motor", "mixed", "purchased", ["drive_motor"], [motor], [], "Prewired 3 V DC gearmotor, 30 rpm; exact ratings are synthetic fixture data."),
        component("play_marble", "glass", "purchased", ["marble"], [], [], "One 16 mm glass marble."),
    ]
    for item in components[-2:]:
        item["sourcing"] = {"url": "https://supplier.example/" + item["id"], "specification": item["specification"]}
        item["dimensions_mm"] = {"diameter": 16} if item["id"] == "play_marble" else {"body_length": 25, "body_width": 20, "shaft_diameter": 2}
    inventory = lambda item_id, quantity, unit, specification: {"id": item_id, "name": item_id, "quantity": quantity, "unit": unit, "specification": specification}
    document = {
        "schema_version": 1, "kind": "workshop.manufacturing", "delivery": "assembled-product",
        "assembly": {"step": display, "occurrences": descriptor}, "components": components,
        "stock": [inventory("pla_stock", 50, "g", "PLA spool; total includes trim allowance"), inventory("board_stock", 1, "sheet", "A4 E-flute 1.5 mm board, two side blanks per sheet"), inventory("cord_stock", 330, "mm", "2 mm cotton; two 150 mm cuts plus 30 mm waste")],
        "consumables": [inventory("glue", 3, "mL", "Paper-to-PLA compatible adhesive; follow supplier cure time")],
        "tools": [{"id": "scissors", "name": "Scissors", "specification": "Production cutting tool for card and cord"}],
        "assembly_steps": [{"id": "assemble", "title": "Assemble the toy", "instructions": "Cut the sides and cords, fit the motor and sides to the body, attach cords, then place the marble. Inspect before physical testing.", "components": [item["id"] for item in components], "consumables": ["glue"], "tools": ["scissors"], "files": [cut, cord]}],
        "public_assets": [public_display, hero],
    }
    return seal_manifest(root, document), document


def make_purchased_subassembly(root: Path) -> tuple[dict, dict]:
    """One procurement unit with two colored leaves from a real gen descriptor.

    The committed descriptor was captured from scripts/gen on two synthetic,
    differently colored solids grouped as one purchased unit. Provenance paths
    were omitted; occurrence, component and hierarchy records are unchanged.
    """
    _, document = make_mixed_product(root)
    bind_file(root, "cad/part_body.step.py", b"PRINTABLE = False\n")
    fixture = Path(__file__).with_name("fixtures") / "purchased_unit_assembly.json"
    content = fixture.read_bytes()
    document["assembly"]["occurrences"] = bind_file(root, "internal/assembled.step.json", content)
    bind_file(root, "assembled.step.json", content)
    motor = document["components"][3]
    motor.update(quantity=1, occurrences=["body", "terminal"], assembly_unit_ids=["o1.1"])
    document["components"] = [motor]
    document["assembly_steps"][0]["components"] = ["motor"]
    return seal_manifest(root, document), document


class PurchasedAssemblyUnitTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.product, self.document = make_purchased_subassembly(self.root)
        self.motor = self.document["components"][0]
        self.descriptor = json.loads((self.root / "assembled.step.json").read_bytes())

    def validate(self):
        content = encoded(self.descriptor)
        bind_file(self.root, "assembled.step.json", content)
        self.document["assembly"]["occurrences"] = bind_file(self.root, "internal/assembled.step.json", content)
        self.product = seal_manifest(self.root, self.document)
        return validate_manifest(self.root, self.product, cad_project_path="cad")

    def test_one_purchased_unit_preserves_two_colored_leaves_and_exact_hierarchy(self):
        before = (self.root / "assembled.step.json").read_bytes()
        self.assertEqual(validate_manifest(self.root, self.product, cad_project_path="cad"), self.document)
        self.assertEqual(self.motor["quantity"], 1)
        self.assertEqual(len(self.descriptor["occurrences"]), 2)
        colors = [row["color"] for row in self.descriptor["occurrences"]]
        self.assertNotEqual(colors[0], colors[1])
        self.assertEqual((self.root / "assembled.step.json").read_bytes(), before)
        self.assertEqual((self.root / "internal/assembled.step.json").read_bytes(), before)
        self.assertEqual(public_asset_paths(self.root, self.product), ("public/assembled.step", "public/hero.png"))

    def test_two_purchased_units_use_exact_ids_even_when_parent_names_repeat(self):
        first = self.descriptor["assembly"]["root"]["children"][0]
        second = copy.deepcopy(first)
        def relocate(node):
            node["id"] = node["id"].replace("o1.1", "o1.2", 1)
            node["leafPartIds"] = [value.replace("o1.1", "o1.2", 1) for value in node["leafPartIds"]]
            if node["nodeType"] == "part":
                node["name"] += "_second"
            for child in node["children"]:
                relocate(child)
        relocate(second)
        root = self.descriptor["assembly"]["root"]
        root["children"].append(second)
        root["leafPartIds"].extend(second["leafPartIds"])
        for row in list(self.descriptor["occurrences"]):
            repeated = copy.deepcopy(row)
            repeated["id"] = repeated["id"].replace("o1.1", "o1.2", 1)
            repeated["name"] += "_second"
            repeated["transform"][3] += 30
            self.descriptor["occurrences"].append(repeated)
        self.descriptor["stats"]["occurrenceCount"] = 4
        self.motor.update(quantity=2, occurrences=[row["name"] for row in self.descriptor["occurrences"]], assembly_unit_ids=["o1.1", "o1.2"])
        self.assertEqual(first["name"], second["name"])
        self.assertEqual(self.validate(), self.document)

    def test_without_grouping_the_previous_leaf_quantity_rule_is_unchanged(self):
        del self.motor["assembly_unit_ids"]
        with self.assertRaisesRegex(ManufacturingManifestError, "assembly occurrence count"):
            self.validate()
        self.motor["quantity"] = 2
        self.assertEqual(self.validate(), self.document)

    def test_quantity_cannot_count_leaves_instead_of_declared_physical_units(self):
        self.motor["quantity"] = 2
        with self.assertRaisesRegex(ManufacturingManifestError, "assembly unit count"):
            self.validate()

    def test_duplicated_unknown_root_leaf_and_name_unit_references_fail(self):
        for ids in (["o1.1", "o1.1"], ["o1.9"], ["o1"], ["o1.1.1", "o1.1.2"], ["purchased_unit"]):
            self.motor.update(assembly_unit_ids=ids, quantity=len(ids))
            with self.subTest(ids=ids), self.assertRaises(ManufacturingManifestError):
                self.validate()

    def test_ancestor_and_descendant_units_cannot_count_the_same_leaves_twice(self):
        outer = self.descriptor["assembly"]["root"]["children"][0]
        inner = copy.deepcopy(outer)
        inner["id"] = "o1.1.1"
        inner["leafPartIds"] = [value.replace("o1.1.", "o1.1.1.", 1) for value in inner["leafPartIds"]]
        for leaf in inner["children"]:
            leaf["id"] = leaf["id"].replace("o1.1.", "o1.1.1.", 1)
            leaf["leafPartIds"] = [leaf["id"]]
        outer["children"] = [inner]
        outer["leafPartIds"] = inner["leafPartIds"][:]
        self.descriptor["assembly"]["root"]["leafPartIds"] = inner["leafPartIds"][:]
        for row in self.descriptor["occurrences"]:
            row["id"] = row["id"].replace("o1.1.", "o1.1.1.", 1)
        self.motor.update(quantity=2, assembly_unit_ids=["o1.1", "o1.1.1"])
        with self.assertRaisesRegex(ManufacturingManifestError, "overlap"):
            self.validate()

    def test_grouped_component_must_claim_every_leaf_of_its_unit(self):
        self.motor["occurrences"] = ["body"]
        with self.assertRaisesRegex(ManufacturingManifestError, "exactly cover"):
            self.validate()

    def test_two_components_cannot_claim_the_same_physical_unit(self):
        other = copy.deepcopy(self.motor)
        other["id"] = "other_motor"
        self.document["components"].append(other)
        with self.assertRaisesRegex(ManufacturingManifestError, "two components"):
            self.validate()

    def test_grouped_units_require_purchased_process_and_nonempty_id_list(self):
        for value in ([], None, "o1.1", [True]):
            self.motor["assembly_unit_ids"] = value
            with self.subTest(value=value), self.assertRaises(ManufacturingManifestError):
                self.validate()
        self.motor.update(assembly_unit_ids=["o1.1"], process="handcraft")
        with self.assertRaisesRegex(ManufacturingManifestError, "only for purchased"):
            self.validate()

    def test_grouping_requires_complete_unambiguous_cad_hierarchy(self):
        original = copy.deepcopy(self.descriptor)
        cases = ("missing_tree", "duplicate_leaf_id", "duplicate_tree_id", "leaf_name", "parent_path", "missing_leaf", "extra_declared_leaf", "duplicate_declared_leaf", "unlisted_occurrence")
        for case in cases:
            self.descriptor = copy.deepcopy(original)
            root = self.descriptor["assembly"]["root"]
            unit = root["children"][0]
            if case == "missing_tree":
                del self.descriptor["assembly"]
            elif case == "duplicate_leaf_id":
                self.descriptor["occurrences"][1]["id"] = self.descriptor["occurrences"][0]["id"]
            elif case == "duplicate_tree_id":
                unit["children"][1]["id"] = unit["children"][0]["id"]
            elif case == "leaf_name":
                unit["children"][0]["name"] = "unrelated"
            elif case == "parent_path":
                unit["children"][0]["id"] = "o9.1"
            elif case == "missing_leaf":
                unit["children"].pop()
            elif case == "extra_declared_leaf":
                unit["leafPartIds"].append("o1.99")
            elif case == "duplicate_declared_leaf":
                unit["leafPartIds"].append(unit["leafPartIds"][0])
            elif case == "unlisted_occurrence":
                self.descriptor["occurrences"].append({"id": "o1.9", "name": "orphan"})
                self.descriptor["stats"]["occurrenceCount"] += 1
            with self.subTest(case=case), self.assertRaises(ManufacturingManifestError):
                self.validate()


class PrintedAssemblyUnitTests(unittest.TestCase):
    """Structural unit/source identity only; the source deliberately cannot run."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        _, self.document = make_purchased_subassembly(self.root)
        self.printed = self.document["components"][0]
        self.source = "cad/part_body.step.py"
        self.step = "cad/part_body.step"
        self.printed.update(
            id="printed_body", name="Painted body", process="3d-print",
            material={"family": "polymer", "specification": "PLA body; paint is a finishing consumable"},
            specification="One fused production part per unit; two display regions. Synthetic contract fixture only.",
            files=[
                bind_file(self.root, self.source, b"PRINTABLE = True\nraise RuntimeError('CAD MUST NOT EXECUTE')\n"),
                bind_file(self.root, self.step, b"ISO-10303-21;\n/* SYNTHETIC PRODUCTION FIXTURE */\nEND-ISO-10303-21;\n"),
            ],
            stock_ids=["pla_stock"],
            production_part={"source_path": self.source, "step_path": self.step},
        )
        self.printed.pop("sourcing")
        self.printed.pop("dimensions_mm")
        self.document["assembly_steps"][0]["components"] = ["printed_body"]
        self.descriptor = json.loads((self.root / "assembled.step.json").read_bytes())

    def validate(self):
        content = encoded(self.descriptor)
        bind_file(self.root, "assembled.step.json", content)
        self.document["assembly"]["occurrences"] = bind_file(self.root, "internal/assembled.step.json", content)
        self.product = seal_manifest(self.root, self.document)
        return validate_manifest(self.root, self.product, cad_project_path="cad")

    def repeat_unit(self):
        second = copy.deepcopy(self.descriptor["assembly"]["root"]["children"][0])
        def relocate(node):
            node["id"] = node["id"].replace("o1.1", "o1.2", 1)
            node["leafPartIds"] = [value.replace("o1.1", "o1.2", 1) for value in node["leafPartIds"]]
            if node["nodeType"] == "part":
                node["name"] += "_second"
            for child in node["children"]:
                relocate(child)
        relocate(second)
        root = self.descriptor["assembly"]["root"]
        root["children"].append(second)
        root["leafPartIds"].extend(second["leafPartIds"])
        for row in list(self.descriptor["occurrences"]):
            repeated = copy.deepcopy(row)
            repeated["id"] = repeated["id"].replace("o1.1", "o1.2", 1)
            repeated["name"] += "_second"
            repeated["transform"][3] += 30
            self.descriptor["occurrences"].append(repeated)
        self.descriptor["stats"]["occurrenceCount"] = 4

    def test_one_printed_unit_binds_one_source_and_step_without_executing_cad(self):
        before = {row["path"]: (self.root / row["path"]).read_bytes() for row in self.printed["files"]}
        self.assertEqual(self.validate(), self.document)
        self.assertEqual(self.printed["quantity"], 1)
        self.assertEqual(len(self.printed["occurrences"]), 2)
        self.assertEqual(public_asset_paths(self.root, self.product), ("public/assembled.step", "public/hero.png"))
        self.assertEqual({path: (self.root / path).read_bytes() for path in before}, before)

    def test_repeated_physical_units_share_one_production_definition(self):
        self.repeat_unit()
        self.printed.update(quantity=2, assembly_unit_ids=["o1.1", "o1.2"],
                            occurrences=[row["name"] for row in self.descriptor["occurrences"]])
        self.assertEqual(self.validate(), self.document)
        self.printed["quantity"] = 4
        with self.assertRaisesRegex(ManufacturingManifestError, "assembly unit count"):
            self.validate()

    def test_instruction_and_helper_files_do_not_become_extra_print_sources(self):
        self.printed["files"].reverse()
        self.printed["files"].extend([
            bind_file(self.root, "cad/finish.py", b"raise RuntimeError('HELPERS MUST NOT EXECUTE')\n"),
            bind_file(self.root, "internal/finish.md", b"Apply the specified paint; preserve the fused production shape.\n"),
        ])
        self.assertEqual(self.validate(), self.document)

    def test_grouped_print_requires_explicit_production_part(self):
        del self.printed["production_part"]
        with self.assertRaisesRegex(ManufacturingManifestError, "require production_part"):
            self.validate()

    def test_production_part_has_strict_fields_and_paths(self):
        original = copy.deepcopy(self.printed["production_part"])
        cases = [None, [], {}, {"source_path": self.source},
                 dict(original, sha256="0" * 64), dict(original, source_path=True),
                 dict(original, source_path="../cad/part_body.step.py"),
                 dict(original, step_path="/tmp/part_body.step")]
        for value in cases:
            self.printed["production_part"] = value
            with self.subTest(value=value), self.assertRaises(ManufacturingManifestError):
                self.validate()

    def test_production_part_is_forbidden_on_purchased_ungrouped_and_other_processes(self):
        original = copy.deepcopy(self.printed)
        for process, grouped in (("purchased", True), ("3d-print", False), ("handcraft", False), ("laser-cut", False)):
            self.printed.clear()
            self.printed.update(copy.deepcopy(original))
            self.printed["process"] = process
            if not grouped:
                del self.printed["assembly_unit_ids"]
                self.printed["quantity"] = len(self.printed["occurrences"])
            with self.subTest(process=process, grouped=grouped), self.assertRaisesRegex(ManufacturingManifestError, "only for grouped 3d-print"):
                self.validate()

    def test_only_a_part_source_and_its_exact_generated_sibling_are_supported(self):
        original = copy.deepcopy(self.printed["production_part"])
        for source in ("cad/assembled.step.py", "cad/part_.step.py", "cad/body.step.py", "cad/part_body.py"):
            self.printed["production_part"] = {"source_path": source, "step_path": source.removesuffix(".py")}
            with self.subTest(source=source), self.assertRaisesRegex(ManufacturingManifestError, "part_<role>"):
                self.validate()
        for step in ("cad/part_other.step", "internal/part_body.step", "cad/part_body.stp"):
            self.printed["production_part"] = dict(original, step_path=step)
            with self.subTest(step=step), self.assertRaisesRegex(ManufacturingManifestError, "generated sibling"):
                self.validate()

    def test_both_production_files_must_be_hash_bound_in_this_component(self):
        original = copy.deepcopy(self.printed["files"])
        for omitted in (self.source, self.step):
            self.printed["files"] = [row for row in original if row["path"] != omitted]
            with self.subTest(omitted=omitted), self.assertRaisesRegex(ManufacturingManifestError, "bound"):
                self.validate()
        self.printed["files"] = copy.deepcopy(original)
        del self.printed["files"][1]["sha256"]
        with self.assertRaisesRegex(ManufacturingManifestError, "invalid fields"):
            self.validate()

    def test_changed_missing_and_symlinked_production_bytes_are_refused(self):
        for relative in (self.source, self.step):
            path = self.root / relative
            content = path.read_bytes()
            for change in ("changed", "missing", "symlink"):
                if change == "changed":
                    path.write_bytes(content + b"\nchanged\n")
                else:
                    path.unlink()
                    if change == "symlink":
                        target = self.root / "internal/aliased-production"
                        target.write_bytes(content)
                        path.symlink_to(target)
                with self.subTest(relative=relative, change=change), self.assertRaises(ManufacturingManifestError):
                    self.validate()
                if path.is_symlink():
                    path.unlink()
                path.write_bytes(content)

    def test_grouped_print_requires_exactly_one_source(self):
        self.printed["files"].append(bind_file(self.root, "cad/part_other.step.py", b"PRINTABLE = True\n"))
        with self.assertRaisesRegex(ManufacturingManifestError, "exactly one bound production source"):
            self.validate()

    def test_grouping_does_not_bypass_literal_print_selection(self):
        for declaration in ("False", "bool(1)", "1"):
            self.printed["files"][0] = bind_file(self.root, self.source, f"PRINTABLE = {declaration}\n".encode())
            with self.subTest(declaration=declaration), self.assertRaisesRegex(ManufacturingManifestError, "PRINTABLE"):
                self.validate()

    def test_unclaimed_print_sources_are_still_refused(self):
        bind_file(self.root, "cad/part_extra.step.py", b"PRINTABLE = True\n")
        with self.assertRaisesRegex(ManufacturingManifestError, "absent from the manufacturing print subset"):
            self.validate()

    def test_grouping_cannot_reuse_another_components_print_source(self):
        self.repeat_unit()
        other = copy.deepcopy(self.printed)
        other.update(id="second_body", assembly_unit_ids=["o1.2"], occurrences=["body_second", "terminal_second"])
        self.document["components"].append(other)
        self.document["assembly_steps"][0]["components"].append("second_body")
        with self.assertRaisesRegex(ManufacturingManifestError, "one component definition"):
            self.validate()

    def test_production_files_remain_private_and_inside_the_declared_cad_scope(self):
        original_files = copy.deepcopy(self.printed["files"])
        for directory, expected in (("public", "internal production"), ("other-cad", "outside the declared CAD project")):
            source, step = f"{directory}/part_body.step.py", f"{directory}/part_body.step"
            self.printed["production_part"] = {"source_path": source, "step_path": step}
            self.printed["files"] = [bind_file(self.root, target, (self.root / old["path"]).read_bytes())
                                     for target, old in zip((source, step), original_files)]
            with self.subTest(directory=directory), self.assertRaisesRegex(ManufacturingManifestError, expected):
                self.validate()

    def test_grouped_print_preserves_exact_hierarchy_and_leaf_coverage(self):
        original = copy.deepcopy(self.printed)
        for ids, occurrences in ((["o1"], ["body", "terminal"]), (["o1.1.1"], ["body", "terminal"]),
                                 (["o1.1", "o1.1"], ["body", "terminal"]), (["o1.1"], ["body"])):
            self.printed.update(assembly_unit_ids=ids, quantity=len(ids), occurrences=occurrences)
            with self.subTest(ids=ids, occurrences=occurrences), self.assertRaises(ManufacturingManifestError):
                self.validate()
        self.printed.clear()
        self.printed.update(original)
        del self.descriptor["assembly"]
        with self.assertRaisesRegex(ManufacturingManifestError, "exact CAD assembly hierarchy"):
            self.validate()


class ManufacturingManifestTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.product, self.document = make_mixed_product(self.root)

    def seal(self):
        self.product = seal_manifest(self.root, self.document)

    def assert_invalid(self, pattern=None):
        self.seal()
        with self.assertRaisesRegex(ManufacturingManifestError, pattern or ".+"):
            validate_manifest(self.root, self.product, cad_project_path="cad")

    def test_synthetic_complete_product_validates_without_running_sources(self):
        self.assertEqual(validate_manifest(self.root, self.product, cad_project_path="cad"), self.document)
        self.assertEqual(read_manifest(self.root, self.product), self.document)
        self.assertEqual(public_asset_paths(self.root, self.product), ("public/assembled.step", "public/hero.png"))

    def test_absent_marker_preserves_legacy_without_touching_files(self):
        missing = self.root / "does-not-exist"
        for api in (read_manifest, validate_manifest, public_asset_paths):
            self.assertIsNone(api(missing, {"title": "legacy"}))

    def test_partial_unknown_and_null_marker_never_downgrade_to_legacy(self):
        for value in (None, {}, [], {"schema_version": 2, "manifest_path": "internal/manufacturing.json", "manifest_sha256": "a" * 64}):
            with self.subTest(value=value), self.assertRaises(ManufacturingManifestError):
                read_manifest(self.root, {"manufacturing": value})

    def test_identity_and_top_level_fields_are_strict(self):
        cases = [("schema_version", True), ("schema_version", 2), ("kind", "kit"), ("delivery", "customer-assembled"), ("extra", "value")]
        for key, value in cases:
            document = copy.deepcopy(self.document)
            document[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ManufacturingManifestError):
                read_manifest(self.root, seal_manifest(self.root, document))

    def test_changed_manifest_and_changed_public_assets_fail(self):
        with (self.root / "internal/manufacturing.json").open("ab") as stream:
            stream.write(b" ")
        with self.assertRaisesRegex(ManufacturingManifestError, "sha256"):
            read_manifest(self.root, self.product)
        self.seal()
        (self.root / "public/hero.png").write_bytes(b"changed")
        with self.assertRaisesRegex(ManufacturingManifestError, "sha256"):
            public_asset_paths(self.root, self.product)

    def test_public_projection_does_not_repeat_make_production_validation(self):
        self.document["components"] = "intentionally invalid production specification"
        self.seal()
        (self.root / "cad/part_body.step.py").unlink()
        (self.root / "internal/assembled.step.json").unlink()
        self.assertEqual(public_asset_paths(self.root, self.product), ("public/assembled.step", "public/hero.png"))
        with self.assertRaises(ManufacturingManifestError):
            validate_manifest(self.root, self.product)

    def test_component_collection_types_and_numeric_types_are_bounded(self):
        for key, value in (("quantity", True), ("quantity", 1.0), ("quantity", -1), ("quantity", 10 ** 400), ("occurrences", "body"), ("material", []), ("files", {}), ("process", []), ("specification", "")):
            original = copy.deepcopy(self.document)
            self.document["components"][0][key] = value
            with self.subTest(key=key, value=str(value)[:30]):
                self.assert_invalid()
            self.document = original

    def test_duplicate_and_cross_referenced_component_ids_fail(self):
        self.document["components"][1]["id"] = "printed_body"
        self.assert_invalid("globally unique")
        self.document["components"][1]["id"] = "pla_stock"
        self.assert_invalid("globally unique")

    def test_occurrence_coverage_quantities_and_unknown_names_fail(self):
        cases = [(["left_side"], 1, "complete assembly"), (["left_side", "right_side"], 3, "quantity"), (["left_side", "left_side"], 2, "duplicate"), (["left_side", "absent"], 2, "unknown")]
        for occurrences, quantity, expected in cases:
            self.document["components"][1]["occurrences"] = occurrences
            self.document["components"][1]["quantity"] = quantity
            with self.subTest(occurrences=occurrences, quantity=quantity):
                self.assert_invalid(expected)

    def test_two_components_cannot_claim_one_occurrence(self):
        self.document["components"][1]["occurrences"] = ["body"]
        self.document["components"][1]["quantity"] = 1
        self.assert_invalid("two components")

    def test_unknown_process_and_material_fail(self):
        self.document["components"][0]["process"] = "teleport"
        self.assert_invalid("process")
        self.document["components"][0]["process"] = "3d-print"
        self.document["components"][0]["material"]["family"] = "magic"
        self.assert_invalid("material family")

    def test_printed_source_requires_explicit_true_and_unclaimed_prints_fail(self):
        for content in (b"PRINTABLE = False\n", b"# legacy implicit printable\n", b"PRINTABLE = bool(1)\n", b"PRINTABLE = True\nPRINTABLE = False\n"):
            self.document["components"][0]["files"][0] = bind_file(self.root, "cad/part_body.step.py", content)
            with self.subTest(content=content):
                self.assert_invalid("PRINTABLE")
        self.product, self.document = make_mixed_product(self.root)
        bind_file(self.root, "cad/part_surprise.step.py", b"PRINTABLE = True\n")
        self.assert_invalid("absent from the manufacturing print subset")

    def test_nonprinted_entry_cannot_enter_default_print_sweep(self):
        self.document["components"][1]["files"][0] = bind_file(self.root, "cad/part_side.step.py", b"# PRINTABLE not explicitly false\n")
        self.assert_invalid("nonprinted component")

    def test_printed_component_requires_source_and_craft_requires_files_stock(self):
        self.document["components"][0]["files"] = [self.document["components"][1]["files"][1]]
        self.assert_invalid("printable .step.py")
        self.product, self.document = make_mixed_product(self.root)
        self.document["components"][1]["files"] = []
        self.assert_invalid("component files")
        self.product, self.document = make_mixed_product(self.root)
        self.document["components"][1]["stock_ids"] = []
        self.assert_invalid("stock_ids")

    def test_cad_project_bounds_entries_and_must_be_real_directory(self):
        with self.assertRaisesRegex(ManufacturingManifestError, "outside"):
            validate_manifest(self.root, self.product, cad_project_path="internal")
        with self.assertRaisesRegex(ManufacturingManifestError, "safe relative"):
            validate_manifest(self.root, self.product, cad_project_path="../outside")

    def test_purchased_requires_source_and_dimensions_but_not_mpn(self):
        self.assertNotIn("part_number", self.document["components"][-1]["sourcing"])
        self.assertIsNotNone(validate_manifest(self.root, self.product))
        del self.document["components"][-1]["dimensions_mm"]
        self.assert_invalid("sourcing specifications and dimensions")
        self.document["components"][-1]["dimensions_mm"] = {"diameter": 0}
        self.assert_invalid("dimension")
        self.document["components"][-1]["dimensions_mm"] = {"diameter": 16}
        self.document["components"][-1]["sourcing"]["specification"] = ""
        self.assert_invalid("sourcing specification")

    def test_source_urls_do_not_carry_credentials(self):
        for url in ("http://supplier.example/motor", "https://user:secret@supplier.example/motor", "https://@supplier.example/motor", "file:///tmp/motor", "https://[invalid"):
            self.document["components"][-1]["sourcing"]["url"] = url
            with self.subTest(url=url):
                self.assert_invalid("public HTTPS")

    def test_stock_and_step_references_are_checked(self):
        for field, value in (("stock_ids", ["missing"]),):
            self.document["components"][0][field] = value
            self.assert_invalid("unknown")
        self.product, self.document = make_mixed_product(self.root)
        for key in ("components", "consumables", "tools"):
            original = self.document["assembly_steps"][0][key]
            self.document["assembly_steps"][0][key] = ["missing"]
            with self.subTest(key=key):
                self.assert_invalid("unknown")
            self.document["assembly_steps"][0][key] = original
        self.document["assembly_steps"][0]["components"].pop()
        self.assert_invalid("every component")

    def test_duplicate_steps_and_inventory_ids_fail(self):
        self.document["assembly_steps"].append(copy.deepcopy(self.document["assembly_steps"][0]))
        self.assert_invalid("step IDs")
        self.document["assembly_steps"].pop()
        self.document["stock"].append(copy.deepcopy(self.document["stock"][0]))
        self.assert_invalid("duplicate IDs")

    def test_changed_internal_references_fail_make_only(self):
        (self.root / "internal/cord.md").write_text("different cut length")
        with self.assertRaisesRegex(ManufacturingManifestError, "sha256"):
            validate_manifest(self.root, self.product)
        self.assertIsNotNone(public_asset_paths(self.root, self.product))

    def test_descriptor_is_hash_bound_and_occurrences_unique(self):
        path = self.document["assembly"]["occurrences"]["path"]
        descriptor = json.loads((self.root / path).read_text())
        descriptor["occurrences"].append({"name": "body"})
        self.document["assembly"]["occurrences"] = bind_file(self.root, path, encoded(descriptor))
        bind_file(self.root, "assembled.step.json", encoded(descriptor))
        self.assert_invalid("occurrence names must be unique")

    def test_independent_occurrence_list_cannot_replace_the_canonical_assembly(self):
        path = self.document["assembly"]["occurrences"]["path"]
        descriptor = json.loads((self.root / path).read_text())
        descriptor["occurrences"] = [{"name": "unrelated"}]
        self.document["assembly"]["occurrences"] = bind_file(self.root, path, encoded(descriptor))
        self.assert_invalid("canonical assembled.step.json")

    def test_independent_assembly_cannot_replace_the_canonical_step(self):
        replacement = b"ISO-10303-21;\n/* unrelated model */\n"
        self.document["assembly"]["step"] = bind_file(self.root, "internal/unrelated.step", replacement)
        self.document["public_assets"][0] = bind_file(self.root, "public/assembled.step", replacement)
        self.assert_invalid("canonical assembled.step")

    def test_public_assets_cannot_name_internal_sources_json_or_mesh(self):
        for path in ("internal/cord.md", "public/../internal/cord.md", "public/source.py", "public/bom.json", "public/model.glb", "public/template.dxf", "public/.hidden/hero.png"):
            self.document["public_assets"][1] = {"path": path, "sha256": "a" * 64}
            self.seal()
            with self.subTest(path=path), self.assertRaises(ManufacturingManifestError):
                public_asset_paths(self.root, self.product)

    def test_public_asset_types_and_complete_assembly_required(self):
        self.document["public_assets"][1] = bind_file(self.root, "public/hero.png", b'{"private_supplier_cost":500}')
        self.assert_invalid("file format")
        self.product, self.document = make_mixed_product(self.root)
        self.document["public_assets"] = self.document["public_assets"][:1]
        self.assert_invalid("finished-product image")
        self.product, self.document = make_mixed_product(self.root)
        self.document["public_assets"][0] = bind_file(self.root, "public/part.step", b"ISO-10303-21;\n/* only a part */\n")
        self.assert_invalid("complete assembly")

    def test_duplicate_public_paths_rejected(self):
        self.document["public_assets"].append(self.document["public_assets"][1])
        self.assert_invalid("duplicate public")

    def test_public_document_cannot_link_private_paths(self):
        self.document["public_assets"].append(bind_file(self.root, "public/guide.md", b"[Bill of materials](../internal/manufacturing.json)"))
        self.assert_invalid("private or parent-relative")

    def test_public_document_links_resolve_only_to_allowlisted_public_assets(self):
        self.document["public_assets"].append(bind_file(self.root, "public/guide.md", b"![Finished product](hero.png)\n[View solid](assembled.step)"))
        self.seal()
        self.assertIn("public/guide.md", public_asset_paths(self.root, self.product))
        for content in (b"![Hidden](cad/source.png)", b'<img src="%2e%2e/internal/bom.png">', b'<script src="https://example.com/app.js"></script>', b"[Bad](javascript:alert)"):
            self.document["public_assets"][-1] = bind_file(self.root, "public/guide.md", content)
            with self.subTest(content=content):
                self.assert_invalid()

    def test_symlink_file_and_symlink_parent_cannot_escape(self):
        external = self.root / "external.png"
        external.write_bytes((self.root / "public/hero.png").read_bytes())
        (self.root / "public/hero.png").unlink()
        (self.root / "public/hero.png").symlink_to(external)
        with self.assertRaisesRegex(ManufacturingManifestError, "symlink"):
            public_asset_paths(self.root, self.product)
        (self.root / "public/hero.png").unlink()
        (self.root / "public/hero.png").write_bytes(external.read_bytes())
        (self.root / "public/alias").symlink_to(self.root / "internal", target_is_directory=True)
        self.document["public_assets"].append({"path": "public/alias/cord.md", "sha256": hashlib.sha256((self.root / "internal/cord.md").read_bytes()).hexdigest()})
        self.assert_invalid("symlink")

    def test_internal_reference_and_marker_traversal_fail(self):
        self.document["components"][1]["files"][0]["path"] = "../outside.step.py"
        self.assert_invalid("safe relative")
        self.product["manufacturing"]["manifest_path"] = "internal/../manufacturing.json"
        with self.assertRaises(ManufacturingManifestError):
            read_manifest(self.root, self.product)

    def test_duplicate_json_keys_and_nonfinite_json_rejected(self):
        for content in (b'{"schema_version":1,"schema_version":1}', b'{"schema_version":NaN}', b'[]', b'\xff'):
            binding = bind_file(self.root, "internal/manufacturing.json", content)
            self.product["manufacturing"]["manifest_sha256"] = binding["sha256"]
            with self.subTest(content=content), self.assertRaises(ManufacturingManifestError):
                read_manifest(self.root, self.product)


if __name__ == "__main__":
    unittest.main()
