"""Contract tests for the Concept records.

These cover what a concept must refuse: an under-specified component, a brief
that never decided its numbers, an image set whose roles cannot be told apart
without opening the pixels, and a sealed concept whose bytes moved afterwards.
"""

import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.errors import ArtifactError, ContractError
from inventor_workshop.jobs import (
    CONCEPT_DESCRIPTOR_FILENAME,
    CONCEPT_OVERALL_ROLES,
    ConceptBrief,
    ConceptComponent,
    ConceptContext,
    ConceptImages,
    Feedback,
    MakeContext,
)
from inventor_workshop.make import Wish
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint


def component(key="body", **overrides):
    fields = {
        "key": key,
        "name": "Body",
        "purpose": "Carries the design.",
        "form": "a rounded shell with one flat base",
        "dimensions_mm": (40.0, 40.0, 12.0),
        "placement": "the base of the assembly",
        "interfaces": "receives the lid on its upper rim",
    }
    fields.update(overrides)
    return ConceptComponent(
        fields["key"],
        fields["name"],
        fields["purpose"],
        fields["form"],
        fields["dimensions_mm"],
        fields["placement"],
        fields["interfaces"],
    )


def brief(components=None, **overrides):
    fields = {
        "object": "a pocket spinner",
        "category": "a hand-operated mechanism",
        "envelope_mm": (60.0, 60.0, 20.0),
        "wall_mm": 2.4,
        "features": ("one surprising rhythm",),
        "print": {"orientation": "flat on its largest face", "supports": False},
        "components": components if components is not None else (component(),),
        "fits": None,
        "assumptions": ("The Wish did not state an envelope.",),
    }
    fields.update(overrides)
    return ConceptBrief(
        fields["object"],
        fields["category"],
        fields["envelope_mm"],
        fields["wall_mm"],
        fields["features"],
        fields["print"],
        fields["components"],
        fields["fits"],
        fields["assumptions"],
    )


def write_concept(
    root,
    design,
    *,
    overall=None,
    components=None,
    descriptor=None,
    round_number=1,
):
    """Lay out a concept on disk the way DefaultConcept seals one."""

    root = Path(root)
    (root / "images").mkdir(parents=True, exist_ok=True)
    if overall is None:
        overall = {role: "images/%s.png" % role for role in CONCEPT_OVERALL_ROLES}
    if components is None:
        components = {
            item.key: "images/component-%s.png" % item.key
            for item in design.components
        }
    for label, relative in list(overall.items()) + list(components.items()):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(("fixture %s\n" % label).encode("utf-8"))
    if descriptor is None:
        images = dict(overall)
        images["components"] = dict(components)
        descriptor = {
            "schema_version": 1,
            "round": round_number,
            "concept_art": True,
            "brief": design.to_dict(),
            "images": images,
        }
    if descriptor is not False:
        (root / CONCEPT_DESCRIPTOR_FILENAME).write_text(
            json.dumps(descriptor, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return overall, components


def seal(root, design, *, round_number=1, **kwargs):
    overall, components = write_concept(
        root, design, round_number=round_number, **kwargs
    )
    return ConceptImages.from_root(root, design, overall, components, round_number)


class ConceptComponentTest(unittest.TestCase):
    def test_a_component_states_the_geometry_an_image_cannot_show(self):
        item = component()
        self.assertEqual(item.dimensions_mm, (40.0, 40.0, 12.0))
        self.assertEqual(
            set(item.to_dict()),
            {
                "key",
                "name",
                "purpose",
                "form",
                "dimensions_mm",
                "placement",
                "interfaces",
            },
        )

    def test_a_component_carrying_only_a_name_and_purpose_is_refused(self):
        for field in ("form", "placement", "interfaces"):
            with self.subTest(field=field), self.assertRaises(ContractError):
                component(**{field: "   "})
        with self.assertRaises(ContractError):
            component(dimensions_mm=(40.0, 40.0))
        with self.assertRaises(ContractError):
            component(dimensions_mm=(40.0, 40.0, 0.0))
        with self.assertRaises(ContractError):
            component(dimensions_mm=(40.0, 40.0, -1.0))

    def test_a_component_key_must_survive_being_a_filename(self):
        for key in ("Body", "body/lid", "-body", "bo dy", ""):
            with self.subTest(key=key), self.assertRaises(ContractError):
                component(key=key)

    def test_a_component_may_not_reuse_an_overall_view_name(self):
        for role in CONCEPT_OVERALL_ROLES:
            with self.subTest(role=role), self.assertRaises(ContractError):
                component(key=role)


class ConceptBriefTest(unittest.TestCase):
    def test_the_brief_carries_the_numbers_the_geometry_hangs_on(self):
        design = brief(
            fits={
                "target": "four coasters",
                "ref_mm": (100.0, 100.0, 8.0),
                "clearance_mm": 0.6,
            }
        )
        self.assertEqual(design.envelope_mm, (60.0, 60.0, 20.0))
        self.assertEqual(design.wall_mm, 2.4)
        self.assertEqual(design.fits["ref_mm"], [100.0, 100.0, 8.0])
        self.assertEqual(design.fits["clearance_mm"], 0.6)
        self.assertEqual(design.component_keys, ("body",))
        self.assertEqual(design.to_dict()["schema_version"], 1)

    def test_a_brief_missing_required_facts_is_refused(self):
        with self.assertRaises(ContractError):
            brief(object="  ")
        with self.assertRaises(ContractError):
            brief(envelope_mm=(60.0, 60.0))
        with self.assertRaises(ContractError):
            brief(wall_mm=0)
        with self.assertRaises(ContractError):
            brief(components=())

    def test_the_component_cap_fails_the_brief_rather_than_truncating(self):
        many = tuple(component(key="part-%d" % index) for index in range(13))
        with self.assertRaises(ContractError):
            brief(components=many)
        self.assertEqual(len(brief(components=many[:12]).components), 12)

    def test_component_keys_must_be_unique(self):
        with self.assertRaises(ContractError):
            brief(components=(component(), component()))

    def test_print_and_fits_must_state_exactly_their_facts(self):
        with self.assertRaises(ContractError):
            brief(print={"orientation": "flat"})
        with self.assertRaises(ContractError):
            brief(print={"orientation": "flat", "supports": "no"})
        with self.assertRaises(ContractError):
            brief(fits={"target": "four coasters", "ref_mm": (1.0, 1.0, 1.0)})
        with self.assertRaises(ContractError):
            brief(
                fits={
                    "target": "four coasters",
                    "ref_mm": (1.0, 1.0),
                    "clearance_mm": 0.6,
                }
            )

    def test_hidden_geometry_is_still_stated_in_full(self):
        hidden = component(
            key="spring",
            name="Return spring",
            placement="inside the body, invisible from every external view",
        )
        design = brief(components=(component(), hidden))
        self.assertEqual(design.component("spring").form, hidden.form)
        with self.assertRaises(ContractError):
            design.component("absent")


class ConceptImagesTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve() / "concept"
        self.root.mkdir()
        self.design = brief()

    def tearDown(self):
        self.temporary.cleanup()

    def test_sealing_produces_a_stable_identity_over_brief_and_pixels(self):
        concept = seal(self.root, self.design)
        self.assertEqual(len(concept.concept_sha256), 64)
        self.assertEqual(set(concept.overall), set(CONCEPT_OVERALL_ROLES))
        self.assertEqual(set(concept.components), {"body"})
        self.assertEqual(len(concept.paths()), 5)
        self.assertEqual(len(concept.image_digests()), 5)
        concept.assert_current()

    def test_a_set_missing_an_overall_view_is_refused(self):
        for role in CONCEPT_OVERALL_ROLES:
            with self.subTest(role=role):
                overall = {
                    name: "images/%s.png" % name
                    for name in CONCEPT_OVERALL_ROLES
                    if name != role
                }
                with self.assertRaises(ContractError):
                    seal(self.root, self.design, overall=overall)

    def test_component_images_and_brief_components_must_correspond(self):
        with self.assertRaises(ContractError):
            seal(self.root, self.design, components={"lid": "images/component-lid.png"})
        with self.assertRaises(ContractError):
            seal(self.root, self.design, components={})

    def test_image_paths_must_be_safe_and_distinct(self):
        overall, components = write_concept(self.root, self.design)
        manifest = build_artifact_manifest(self.root, created_at="content-addressed")
        for value in (
            "/etc/passwd.png",
            "../escape.png",
            "images\\front.png",
            "images/front.txt",
            "images/missing.png",
            "",
            None,
        ):
            with self.subTest(value=value):
                unsafe = dict(overall)
                unsafe["front"] = value
                with self.assertRaises(ContractError):
                    ConceptImages(
                        self.root, manifest, self.design, unsafe, components, 1
                    )

    def test_two_roles_may_not_share_one_file(self):
        overall = {role: "images/%s.png" % role for role in CONCEPT_OVERALL_ROLES}
        overall["top"] = "images/front.png"
        with self.assertRaises(ContractError):
            seal(self.root, self.design, overall=overall)

    def test_filenames_must_identify_their_role(self):
        overall = {role: "images/%s.png" % role for role in CONCEPT_OVERALL_ROLES}
        overall["front"] = "images/view-a.png"
        with self.assertRaises(ContractError):
            seal(self.root, self.design, overall=overall)
        with self.assertRaises(ContractError):
            seal(
                self.root,
                self.design,
                components={"body": "images/part-one.png"},
            )

    def test_a_symlinked_image_or_root_is_refused(self):
        overall, components = write_concept(self.root, self.design)
        target = self.root / "images" / "front.png"
        link = self.root / "images" / "top.png"
        link.unlink()
        link.symlink_to(target)
        with self.assertRaises(ContractError):
            ConceptImages.from_root(self.root, self.design, overall, components, 1)

    def test_a_descriptor_that_disagrees_with_the_files_is_refused(self):
        overall, components = write_concept(self.root, self.design)
        manifest = build_artifact_manifest(self.root, created_at="content-addressed")
        with self.assertRaises(ContractError):
            # A relabelled descriptor: top and bottom swapped.
            swapped = dict(overall)
            swapped["top"], swapped["bottom"] = swapped["bottom"], swapped["top"]
            ConceptImages(self.root, manifest, self.design, swapped, components, 1)

        write_concept(self.root, self.design, descriptor={"schema_version": 1})
        with self.assertRaises(ContractError):
            ConceptImages.from_root(self.root, self.design, overall, components, 1)

    def test_a_descriptor_naming_a_missing_file_is_refused(self):
        overall, components = write_concept(self.root, self.design)
        images = dict(overall)
        images["components"] = dict(components)
        images["front"] = "images/absent.png"
        write_concept(
            self.root,
            self.design,
            descriptor={
                "schema_version": 1,
                "round": 1,
                "concept_art": True,
                "brief": self.design.to_dict(),
                "images": images,
            },
        )
        with self.assertRaises(ContractError):
            ConceptImages.from_root(self.root, self.design, overall, components, 1)

    def test_a_concept_must_mark_itself_as_concept_art(self):
        overall, components = write_concept(self.root, self.design)
        images = dict(overall)
        images["components"] = dict(components)
        write_concept(
            self.root,
            self.design,
            descriptor={
                "schema_version": 1,
                "round": 1,
                "concept_art": False,
                "brief": self.design.to_dict(),
                "images": images,
            },
        )
        with self.assertRaises(ContractError):
            ConceptImages.from_root(self.root, self.design, overall, components, 1)

    def test_a_missing_or_malformed_descriptor_is_refused(self):
        overall, components = write_concept(self.root, self.design, descriptor=False)
        with self.assertRaises(ContractError):
            ConceptImages.from_root(self.root, self.design, overall, components, 1)
        (self.root / CONCEPT_DESCRIPTOR_FILENAME).write_text(
            "not json\n", encoding="utf-8"
        )
        with self.assertRaises(ContractError):
            ConceptImages.from_root(self.root, self.design, overall, components, 1)

    def test_relabelling_a_sealed_concept_changes_its_identity(self):
        concept = seal(self.root, self.design)
        descriptor = json.loads(
            (self.root / CONCEPT_DESCRIPTOR_FILENAME).read_text(encoding="utf-8")
        )
        descriptor["images"]["top"], descriptor["images"]["bottom"] = (
            descriptor["images"]["bottom"],
            descriptor["images"]["top"],
        )
        (self.root / CONCEPT_DESCRIPTOR_FILENAME).write_text(
            json.dumps(descriptor, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with self.assertRaises(ArtifactError):
            concept.assert_current()

    def test_tampering_is_caught_at_the_next_boundary(self):
        concept = seal(self.root, self.design)
        (self.root / "images" / "front.png").write_bytes(b"different pixels\n")
        with self.assertRaises(ArtifactError):
            concept.assert_current()

    def test_a_round_must_be_a_positive_integer(self):
        with self.assertRaises(ContractError):
            seal(self.root, self.design, round_number=0)


class ConceptContextTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        inventor = self.root / "inventor"
        inventor.mkdir()
        (inventor / "TASTE.md").write_text(
            "---\n"
            "name: Test Inventor\n"
            "description: Small playthings with one surprising interaction.\n"
            "---\n"
            "# Taste\n\nSmall playthings.\n",
            encoding="utf-8",
        )
        self.taste = load_taste(inventor)
        self.wish = Wish.create("rhythm-top", "A delightful desk spinner")
        self.blueprint = ToyBlueprint.for_lane("moving-machines")
        self.workspace = (self.root / "run" / "concept").absolute()
        self.design = brief()

    def tearDown(self):
        self.temporary.cleanup()

    def context(self, **overrides):
        fields = {
            "round": 1,
            "workspace": self.workspace,
            "feedback": (),
            "playtest_rounds": 2,
            "previous": None,
            "refine_depth": 0,
        }
        fields.update(overrides)
        return ConceptContext(
            self.wish,
            self.taste,
            self.blueprint,
            fields["round"],
            fields["workspace"],
            fields["feedback"],
            fields["playtest_rounds"],
            fields["previous"],
            fields["refine_depth"],
        )

    def test_a_well_formed_context_is_accepted(self):
        context = self.context()
        self.assertEqual(context.round, 1)
        self.assertEqual(context.feedback, ())
        self.assertIsNone(context.previous)

    def test_a_malformed_context_is_refused(self):
        with self.assertRaises(ContractError):
            self.context(workspace=Path("relative/concept"))
        with self.assertRaises(ContractError):
            self.context(round=0)
        with self.assertRaises(ContractError):
            self.context(round=3)
        with self.assertRaises(ContractError):
            self.context(feedback=("not a feedback record",))
        with self.assertRaises(ContractError):
            self.context(refine_depth=-1)
        with self.assertRaises(ContractError):
            self.context(previous="not a concept")

    def test_feedback_may_name_concept_among_the_jobs_it_invalidates(self):
        item = Feedback(
            "silhouette-wrong",
            "form",
            "improve",
            "The silhouette reads as a lamp, not a spinner.",
            "Narrow the waist and raise the shoulder.",
            ("playtest.json",),
            ("concept", "make", "playtest"),
        )
        context = self.context(round=2, feedback=(item,))
        self.assertEqual(context.feedback[0].invalidates[0], "concept")

    def test_a_previous_concept_must_come_from_an_earlier_round(self):
        concept_root = self.root / "concept"
        concept_root.mkdir()
        concept = seal(concept_root, self.design, round_number=2)
        with self.assertRaises(ContractError):
            self.context(round=2, previous=concept)
        self.assertIsNotNone(
            self.context(round=1, playtest_rounds=2, previous=None).round
        )


class MakeContextConceptTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        inventor = self.root / "inventor"
        inventor.mkdir()
        (inventor / "TASTE.md").write_text(
            "---\n"
            "name: Test Inventor\n"
            "description: Small playthings with one surprising interaction.\n"
            "---\n"
            "# Taste\n\nSmall playthings.\n",
            encoding="utf-8",
        )
        self.taste = load_taste(inventor)
        self.wish = Wish.create("rhythm-top", "A delightful desk spinner")
        self.blueprint = ToyBlueprint.for_lane("moving-machines")
        self.workspace = (self.root / "run" / "make").absolute()
        concept_root = self.root / "concept"
        concept_root.mkdir()
        self.concept = seal(concept_root, brief(), round_number=1)

    def tearDown(self):
        self.temporary.cleanup()

    def make_context(self, round_number=1, concept=None):
        return MakeContext(
            self.wish,
            self.taste,
            self.blueprint,
            round_number,
            self.workspace,
            (),
            2,
            concept,
        )

    def test_omitting_the_concept_stays_valid(self):
        context = self.make_context()
        self.assertIsNone(context.concept_images)

    def test_the_rounds_concept_reaches_make(self):
        context = self.make_context(concept=self.concept)
        self.assertEqual(
            context.concept_images.concept_sha256, self.concept.concept_sha256
        )

    def test_a_concept_from_another_round_is_refused(self):
        with self.assertRaises(ContractError):
            self.make_context(round_number=2, concept=self.concept)

    def test_a_stale_concept_is_refused(self):
        (self.concept.root / "images" / "front.png").write_bytes(b"moved\n")
        with self.assertRaises(ArtifactError):
            self.make_context(concept=self.concept)

    def test_a_concept_must_be_a_concept_record(self):
        with self.assertRaises(ContractError):
            self.make_context(concept={"front": "images/front.png"})


if __name__ == "__main__":
    unittest.main()
