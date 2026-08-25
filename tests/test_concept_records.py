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
from inventor_workshop.concept import (
    CONCEPT_RESEARCH_DIRECTORY,
    CONCEPT_RESEARCH_FINDINGS_FILENAME,
    CONCEPT_RESEARCH_SOURCES_DIRECTORY,
)
from inventor_workshop.jobs import (
    CONCEPT_DESCRIPTOR_FILENAME,
    CONCEPT_OVERALL_ROLES,
    ConceptBrief,
    ConceptComponent,
    ConceptContext,
    ConceptImages,
    DerivedWish,
    Feedback,
    MakeContext,
    WishResearch,
    WishResearchFinding,
    WishResearchSource,
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


RESEARCH_EXCERPT = (
    "A tournament king stands 95 mm tall on a 40 mm base, and the board's "
    "squares are 55 mm across."
)


def source(identifier="fide-standards"):
    return WishResearchSource.create(
        identifier,
        "https://example.invalid/standards",
        "Tournament equipment standards",
        RESEARCH_EXCERPT,
        "2026-08-25T00:00:00Z",
    )


def research(components=None, findings=None, sources=None, **overrides):
    """One breakdown that satisfies every attribution rule by default."""

    parts = components if components is not None else (
        component(),
        component(
            "lid",
            name="Lid",
            purpose="Closes the body.",
            form="a shallow dome with a knurled rim",
            dimensions_mm=(38.0, 38.0, 8.0),
            placement="on top of the body",
            interfaces="snaps onto the body rim",
        ),
    )
    fields = {
        "object": "a pocket spinner",
        "category": "a hand-operated mechanism",
        "envelope_mm": (60.0, 60.0, 20.0),
        "wall_mm": 2.4,
        "features": ("one surprising rhythm",),
        "print": {"orientation": "flat on its largest face", "supports": False},
        "components": parts,
        "fits": None,
    }
    fields.update(overrides)
    recorded = source() if sources is None else None
    if findings is None:
        findings = tuple(
            WishResearchFinding(
                "Research decided %s." % name,
                name,
                decided_because="no source stated it",
            )
            for name in (
                "object",
                "category",
                "envelope_mm",
                "wall_mm",
                "features",
                "print",
            )
        ) + (
            WishResearchFinding(
                "The design is made of %d printed parts." % len(parts),
                "components",
                ("fide-standards",),
            ),
        )
        if fields["fits"] is not None:
            findings += (
                WishResearchFinding(
                    "It must hold the stated target.",
                    "fits",
                    decided_because="no source stated it",
                ),
            )
    return WishResearch(
        fields["object"],
        fields["category"],
        fields["envelope_mm"],
        fields["wall_mm"],
        fields["features"],
        fields["print"],
        fields["components"],
        fields["fits"],
        findings,
        (recorded,) if sources is None else tuple(sources),
    )


def derived(wish=None, constraints=None):
    routed = wish if wish is not None else Wish.create(
        "pocket-spinner", "A pocket spinner that reveals a changing beat"
    )
    return DerivedWish.derive(
        routed, constraints if constraints is not None else {"wall_mm": 2.4}
    )


def write_research(root, record):
    """Lay the research out on disk the way DefaultConcept seals it."""

    directory = Path(root) / CONCEPT_RESEARCH_DIRECTORY
    (directory / CONCEPT_RESEARCH_SOURCES_DIRECTORY).mkdir(
        parents=True, exist_ok=True
    )
    filed = []
    for position, item in enumerate(record.sources, start=1):
        relative = "%s/%03d.json" % (CONCEPT_RESEARCH_SOURCES_DIRECTORY, position)
        (directory / relative).write_text(
            json.dumps(item.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        filed.append({"id": item.id, "file": relative})
    (directory / CONCEPT_RESEARCH_FINDINGS_FILENAME).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "workshop-wish-research",
                "research_sha256": record.research_sha256,
                "findings": [item.to_dict() for item in record.findings],
                "sources": filed,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def write_concept(
    root,
    design,
    *,
    overall=None,
    components=None,
    descriptor=None,
    round_number=1,
    record=None,
    derived_wish=None,
):
    """Lay out a concept on disk the way DefaultConcept seals one."""

    root = Path(root)
    (root / "images").mkdir(parents=True, exist_ok=True)
    record = record if record is not None else research(components=design.components)
    derived_wish = derived_wish if derived_wish is not None else derived()
    write_research(root, record)
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
            "research": {
                "research_sha256": record.research_sha256,
                "valid_as_product_proof": False,
            },
            "derived_wish": {
                "wish_sha256": derived_wish.wish_sha256,
                "derived_wish_sha256": derived_wish.derived_wish_sha256,
            },
        }
    if descriptor is not False:
        (root / CONCEPT_DESCRIPTOR_FILENAME).write_text(
            json.dumps(descriptor, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return overall, components, record, derived_wish


def seal(root, design, *, round_number=1, **kwargs):
    overall, components, record, derived_wish = write_concept(
        root, design, round_number=round_number, **kwargs
    )
    return ConceptImages.from_root(
        root, design, overall, components, round_number, record, derived_wish
    )


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
        overall, components, record, derived_wish = write_concept(self.root, self.design)
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
                        self.root,
                        manifest,
                        self.design,
                        unsafe,
                        components,
                        1,
                        record,
                        derived_wish,
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
        overall, components, record, derived_wish = write_concept(self.root, self.design)
        target = self.root / "images" / "front.png"
        link = self.root / "images" / "top.png"
        link.unlink()
        link.symlink_to(target)
        with self.assertRaises(ContractError):
            ConceptImages.from_root(
                self.root, self.design, overall, components, 1, record, derived_wish
            )

    def test_a_descriptor_that_disagrees_with_the_files_is_refused(self):
        overall, components, record, derived_wish = write_concept(self.root, self.design)
        manifest = build_artifact_manifest(self.root, created_at="content-addressed")
        with self.assertRaises(ContractError):
            # A relabelled descriptor: top and bottom swapped.
            swapped = dict(overall)
            swapped["top"], swapped["bottom"] = swapped["bottom"], swapped["top"]
            ConceptImages(
                self.root,
                manifest,
                self.design,
                swapped,
                components,
                1,
                record,
                derived_wish,
            )

        write_concept(self.root, self.design, descriptor={"schema_version": 1})
        with self.assertRaises(ContractError):
            ConceptImages.from_root(
                self.root, self.design, overall, components, 1, record, derived_wish
            )

    def test_a_descriptor_naming_a_missing_file_is_refused(self):
        overall, components, record, derived_wish = write_concept(self.root, self.design)
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
            ConceptImages.from_root(
                self.root, self.design, overall, components, 1, record, derived_wish
            )

    def test_a_concept_must_mark_itself_as_concept_art(self):
        overall, components, record, derived_wish = write_concept(self.root, self.design)
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
            ConceptImages.from_root(
                self.root, self.design, overall, components, 1, record, derived_wish
            )

    def test_a_missing_or_malformed_descriptor_is_refused(self):
        overall, components, record, derived_wish = write_concept(self.root, self.design, descriptor=False)
        with self.assertRaises(ContractError):
            ConceptImages.from_root(
                self.root, self.design, overall, components, 1, record, derived_wish
            )
        (self.root / CONCEPT_DESCRIPTOR_FILENAME).write_text(
            "not json\n", encoding="utf-8"
        )
        with self.assertRaises(ContractError):
            ConceptImages.from_root(
                self.root, self.design, overall, components, 1, record, derived_wish
            )

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


class WishResearchRecordTest(unittest.TestCase):
    """What a breakdown must refuse before any brief is derived from it."""

    def test_a_source_records_the_excerpt_it_contributed(self):
        recorded = source()
        self.assertEqual(recorded.excerpt, RESEARCH_EXCERPT)
        self.assertEqual(
            set(recorded.to_dict()),
            {"id", "origin", "title", "excerpt", "excerpt_sha256", "retrieved_at"},
        )

    def test_a_source_whose_hash_does_not_match_its_excerpt_is_refused(self):
        with self.assertRaisesRegex(ContractError, "does not hash its own excerpt"):
            WishResearchSource(
                "fide-standards",
                "https://example.invalid/standards",
                "Tournament equipment standards",
                RESEARCH_EXCERPT,
                "0" * 64,
                "2026-08-25T00:00:00Z",
            )

    def test_a_source_recorded_without_its_excerpt_is_refused(self):
        with self.assertRaises(ContractError):
            WishResearchSource.create(
                "fide-standards",
                "https://example.invalid/standards",
                "Tournament equipment standards",
                "",
                "2026-08-25T00:00:00Z",
            )

    def test_a_finding_carrying_both_a_source_and_a_decision_is_refused(self):
        with self.assertRaisesRegex(ContractError, "never both and never neither"):
            WishResearchFinding(
                "A king stands 95 mm tall.",
                "envelope_mm",
                ("fide-standards",),
                "no source stated it",
            )

    def test_a_finding_carrying_neither_is_refused(self):
        with self.assertRaisesRegex(ContractError, "never both and never neither"):
            WishResearchFinding("A king stands 95 mm tall.", "envelope_mm")

    def test_a_finding_must_decide_a_field_the_brief_needs(self):
        with self.assertRaises(ContractError):
            WishResearchFinding(
                "Something true.", "colour", decided_because="no source stated it"
            )

    def test_a_breakdown_citing_an_unknown_source_is_refused(self):
        findings = tuple(
            WishResearchFinding(
                "Research decided %s." % name,
                name,
                decided_because="no source stated it",
            )
            for name in (
                "object",
                "category",
                "envelope_mm",
                "wall_mm",
                "features",
                "print",
            )
        ) + (
            WishResearchFinding(
                "The design is made of two printed parts.",
                "components",
                ("never-recorded",),
            ),
        )
        with self.assertRaisesRegex(ContractError, "recorded sources do not contain"):
            research(findings=findings)

    def test_a_breakdown_leaving_a_required_field_unattributed_is_refused(self):
        findings = tuple(
            WishResearchFinding(
                "Research decided %s." % name,
                name,
                decided_because="no source stated it",
            )
            for name in (
                "object",
                "category",
                "envelope_mm",
                "features",
                "print",
                "components",
            )
        )
        with self.assertRaisesRegex(ContractError, "leaves wall_mm unattributed"):
            research(findings=findings, sources=())

    def test_a_stated_fit_target_must_be_attributed_too(self):
        findings = tuple(
            WishResearchFinding(
                "Research decided %s." % name,
                name,
                decided_because="no source stated it",
            )
            for name in (
                "object",
                "category",
                "envelope_mm",
                "wall_mm",
                "features",
                "print",
                "components",
            )
        )
        with self.assertRaisesRegex(ContractError, "leaves fits unattributed"):
            research(
                findings=findings,
                sources=(),
                fits={
                    "target": "four coasters",
                    "ref_mm": [100.0, 100.0, 8.0],
                    "clearance_mm": 0.6,
                },
            )

    def test_a_derived_wish_that_changed_the_words_is_refused(self):
        routed = Wish.create("pocket-spinner", "A pocket spinner")
        altered = DerivedWish(
            DerivedWish.derive(routed, {}).wish_sha256,
            Wish.create("pocket-spinner", "A pocket spinner with a light"),
        )
        with self.assertRaisesRegex(ContractError, "unchanged"):
            altered.assert_derived_from(routed)

    def test_a_derived_wish_names_both_identities(self):
        routed = Wish.create("pocket-spinner", "A pocket spinner")
        record = DerivedWish.derive(routed, {"wall_mm": 2.0})
        record.assert_derived_from(routed)
        self.assertNotEqual(record.wish_sha256, record.derived_wish_sha256)
        self.assertEqual(record.wish.objective, routed.objective)
        self.assertEqual(record.wish.constraints, {"wall_mm": 2.0})
        self.assertEqual(
            DerivedWish.from_dict(record.to_dict()).to_dict(), record.to_dict()
        )


class SealedResearchTest(unittest.TestCase):
    """The research is covered by the concept's hash, exactly as the pixels are."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve() / "concept"
        self.root.mkdir()
        self.design = brief()

    def tearDown(self):
        self.temporary.cleanup()

    def findings_path(self):
        return (
            self.root
            / CONCEPT_RESEARCH_DIRECTORY
            / CONCEPT_RESEARCH_FINDINGS_FILENAME
        )

    def test_the_sealed_root_contains_the_research(self):
        concept = seal(self.root, self.design)
        self.assertTrue(self.findings_path().is_file())
        sources = (
            self.root / CONCEPT_RESEARCH_DIRECTORY / CONCEPT_RESEARCH_SOURCES_DIRECTORY
        )
        self.assertEqual(
            sorted(item.name for item in sources.iterdir()), ["001.json"]
        )
        self.assertEqual(
            concept.research.research_sha256,
            json.loads(self.findings_path().read_text(encoding="utf-8"))[
                "research_sha256"
            ],
        )
        paths = {entry.path for entry in concept.manifest.entries}
        self.assertIn("research/findings.json", paths)
        self.assertIn("research/sources/001.json", paths)

    def test_editing_the_research_after_sealing_invalidates_the_concept(self):
        concept = seal(self.root, self.design)
        concept.assert_current()
        record = json.loads(self.findings_path().read_text(encoding="utf-8"))
        record["findings"][0]["claim"] = "Something else entirely."
        self.findings_path().write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        with self.assertRaises(ArtifactError):
            concept.assert_current()

    def test_two_identical_briefs_with_different_research_seal_differently(self):
        first = seal(self.root, self.design)
        other_root = self.root.parent / "other"
        other_root.mkdir()
        second = seal(
            other_root,
            self.design,
            record=research(
                components=self.design.components,
                sources=(
                    WishResearchSource.create(
                        "other-standards",
                        "https://example.invalid/other",
                        "A different source",
                        "A different excerpt was relied upon here.",
                        "2026-08-25T00:00:00Z",
                    ),
                ),
                findings=tuple(
                    WishResearchFinding(
                        "Research decided %s." % name,
                        name,
                        decided_because="no source stated it",
                    )
                    for name in (
                        "object",
                        "category",
                        "envelope_mm",
                        "wall_mm",
                        "features",
                        "print",
                    )
                )
                + (
                    WishResearchFinding(
                        "The design is made of two printed parts.",
                        "components",
                        ("other-standards",),
                    ),
                ),
            ),
        )
        self.assertEqual(first.brief.to_dict(), second.brief.to_dict())
        self.assertNotEqual(
            first.research.research_sha256, second.research.research_sha256
        )
        self.assertNotEqual(first.concept_sha256, second.concept_sha256)

    def test_the_sealed_research_is_labelled_as_not_product_proof(self):
        seal(self.root, self.design)
        descriptor = json.loads(
            (self.root / CONCEPT_DESCRIPTOR_FILENAME).read_text(encoding="utf-8")
        )
        self.assertIs(descriptor["research"]["valid_as_product_proof"], False)

    def test_a_concept_without_its_research_is_refused(self):
        overall, components, _, derived_wish = write_concept(self.root, self.design)
        with self.assertRaisesRegex(ContractError, "WishResearch"):
            ConceptImages.from_root(
                self.root, self.design, overall, components, 1, None, derived_wish
            )

    def test_a_descriptor_naming_other_research_is_refused(self):
        overall, components, record, derived_wish = write_concept(
            self.root, self.design
        )
        other = research(
            components=self.design.components,
            findings=tuple(
                WishResearchFinding(
                    "Research decided %s, differently." % name,
                    name,
                    decided_because="no source stated it",
                )
                for name in (
                    "object",
                    "category",
                    "envelope_mm",
                    "wall_mm",
                    "features",
                    "print",
                    "components",
                )
            ),
            sources=(),
        )
        with self.assertRaisesRegex(ContractError, "different research"):
            ConceptImages.from_root(
                self.root, self.design, overall, components, 1, other, derived_wish
            )


if __name__ == "__main__":
    unittest.main()
