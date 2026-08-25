"""One concrete visualized design, decided between Wish and Make.

Concept turns the abstract Wish into a locked brief of physical facts plus a set
of images that all depict the same object. Make then builds to a decided design
instead of reinterpreting prose, and a rejected round can be answered in the
design rather than only in the geometry.

Two things carry consistency, and they fail differently, so they are kept apart:

* **Geometry comes from the brief.** Text does not occlude. A component hidden
  behind another part in every external view is still fully stated by its own
  ``form``, ``dimensions_mm``, ``placement``, and ``interfaces``.
* **Appearance comes from the images.** Material, finish, palette, and form
  language are global to the object, so they are legible in any view. Each image
  after the first is produced with the earlier ones attached as references and
  asked to preserve them.

Within a round the work happens in one order: research the Wish, lock the brief
from what research returned, then draw. No physical fact is settled ahead of the
research that decides it, and no image is asked for before the brief is locked.

No image provider and no researcher ship with this repo. ``DefaultConcept`` owns
the prompts, the generation order, and the sealing; the pixels come from an
injected ``concept_artist`` and the facts from an injected ``wish_researcher``.
Without either the job waits truthfully rather than describing a design it
cannot actually draw or inventing numbers nobody researched.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

from .errors import ContractError
from .jobs import (
    CONCEPT_DESCRIPTOR_FILENAME,
    CONCEPT_OVERALL_ROLES,
    ConceptBrief,
    ConceptComponent,
    ConceptContext,
    ConceptImages,
    DerivedWish,
    Need,
    WaitingFor,
    WishResearch,
    WishResearchFinding,
    WishResearchSource,
    _safe_concept_image,
)
from .make import Wish
from .taste import Taste
from .toys import ToyBlueprint


CONCEPT_IMAGE_DIRECTORY = "images"
MAX_CONCEPT_REFINE_DEPTH = 4
DESIGN_FACTS_HEADING = (
    "DESIGN FACTS (these are physical constraints — respect them exactly)"
)
NEUTRAL_PRESENTATION = (
    "PRESENTATION: a neutral flat design study on a plain even background. "
    "No dramatic lighting, no studio scene, no reflections, and no background "
    "props. No text, no dimensions, no logos, no watermarks, no people, and no "
    "hands. Show only the printable design itself: never depict anything it "
    "holds, mounts to, or rests on."
)
_REVISION_PREFIX = "Revision: "
# Panda's descriptor rule, kept because numbers belong in the design-facts block
# where they are constraints rather than adjectives.
_CAD_VERBS = frozenset(
    (
        "fillet",
        "fillets",
        "filleted",
        "chamfer",
        "chamfers",
        "chamfered",
        "bevel",
        "bevels",
        "bevelled",
        "beveled",
        "radius",
        "radii",
        "draft",
        "extrude",
        "extruded",
        "loft",
        "lofted",
        "revolve",
        "revolved",
        "boolean",
        "mm",
        "cm",
        "inch",
        "inches",
    )
)
_LANE_CATEGORIES = {
    "classics-made-yours": "a printed edition of a known game",
    "invented-games": "a printed edition of a new game",
    "moving-machines": "a hand-operated mechanism",
    "holdable-science": "a hands-on demonstration object",
    "little-worlds": "a small scene object",
}


ConceptArtist = Callable[["ConceptImageRequest"], str]
ExplodeInspector = Callable[[Path, ConceptBrief], Sequence[str]]
WishResearcher = Callable[["WishResearchRequest"], WishResearch]

CONCEPT_RESEARCH_DIRECTORY = "research"
CONCEPT_RESEARCH_FINDINGS_FILENAME = "findings.json"
CONCEPT_RESEARCH_SOURCES_DIRECTORY = "sources"


@dataclass(frozen=True)
class WishResearchRequest:
    """Everything one breakdown of a Wish may be decided from.

    Mirrors :class:`ConceptImageRequest`: the researcher is handed the round's
    exact bindings and returns one record. It writes nothing and decides
    nothing about the brief; the Workshop applies the attribution rules in one
    place rather than trusting each provider to have applied them.
    """

    wish: Wish
    taste: Taste
    blueprint: ToyBlueprint
    round: int

    def __post_init__(self) -> None:
        if not isinstance(self.wish, Wish) or not isinstance(self.taste, Taste):
            raise ContractError("WishResearchRequest requires a Wish and Taste")
        if not isinstance(self.blueprint, ToyBlueprint):
            raise ContractError("WishResearchRequest requires a ToyBlueprint")
        if type(self.round) is not int or self.round < 1:
            raise ContractError(
                "WishResearchRequest round must be a positive integer"
            )


@dataclass(frozen=True)
class ConceptImageRequest:
    """One image asked for by name, with everything it may be drawn from.

    ``references`` are absolute paths to images already produced for this
    concept. They supply appearance only; the shape a component must have is
    stated in ``prompt`` from the brief, because a reference can hide a part but
    text cannot.
    """

    role: str
    kind: str
    prompt: str
    references: Sequence[Path]
    workspace: Path
    filename: str
    brief: ConceptBrief
    round: int

    def __post_init__(self) -> None:
        if self.kind not in ("overall", "component"):
            raise ContractError("concept image kind must be overall or component")
        if self.kind == "overall":
            if self.role not in CONCEPT_OVERALL_ROLES:
                raise ContractError("unknown overall concept view %r" % self.role)
        elif self.role not in self.brief.component_keys:
            raise ContractError("unknown concept component %r" % self.role)
        object.__setattr__(self, "references", tuple(self.references))


def _mm(value: float) -> str:
    text = ("%.2f" % float(value)).rstrip("0").rstrip(".")
    return text or "0"


def _extent(dimensions: Sequence[float]) -> str:
    return " x ".join(_mm(value) for value in dimensions) + " mm"


def design_facts_block(brief: Optional[ConceptBrief]) -> str:
    """Render the locked numbers every image request must carry.

    Returns ``""`` for an absent brief so callers can concatenate it without a
    branch. Dropping the fit target's own size was the defect panda's v3 fixed:
    the model was told the name of the thing it had to hold and never its size.
    """

    if brief is None:
        return ""
    lines = [DESIGN_FACTS_HEADING]
    if brief.fits is not None:
        lines.append(
            "Holds: %s, each %s"
            % (brief.fits["target"], _extent(brief.fits["ref_mm"]))
        )
        lines.append(
            "Clearance around each held item: %s mm"
            % _mm(brief.fits["clearance_mm"])
        )
    lines.append("Approximate envelope: %s" % _extent(brief.envelope_mm))
    lines.append("Wall thickness: %s mm" % _mm(brief.wall_mm))
    if brief.features:
        lines.append("Distinctive features: %s" % "; ".join(brief.features))
    return "\n".join(lines)


def style_descriptor(taste: Taste) -> str:
    """Turn the inventor's Taste into style words, with no CAD verbs or numbers."""

    if not isinstance(taste, Taste):
        raise ContractError("concept style requires a Taste")
    words = []
    for word in taste.description.split():
        stripped = word.strip(".,;:!?()[]\"'")
        if not stripped:
            continue
        if any(character.isdigit() for character in stripped):
            continue
        if stripped.casefold() in _CAD_VERBS:
            continue
        words.append(word)
    described = " ".join(words).strip(" ,;:-")
    if not described:
        described = "the inventor's stated aesthetic"
    return "%s's taste — %s" % (taste.name, described)


def _shared_blocks(brief: ConceptBrief) -> str:
    return "\n\n".join((design_facts_block(brief), NEUTRAL_PRESENTATION))


def _edit_block(edits: Sequence[str]) -> str:
    if not edits:
        return ""
    lines = ["REQUESTED CHANGES (apply every one, and change nothing else):"]
    lines.extend("- %s" % item for item in edits)
    return "\n".join(lines) + "\n\n"


def anchor_prompt(
    brief: ConceptBrief,
    style: str,
    *,
    edits: Sequence[str] = (),
    from_previous: bool = False,
) -> str:
    """The `front` view: the one image drawn without an image anchor."""

    if from_previous:
        opening = (
            "Reference image 1 is the previous front view of %s. Depict the SAME "
            "object with the requested changes applied and nothing else changed. "
            "Preserve every shape, proportion, feature, material, and finish the "
            "changes do not touch." % brief.object
        )
    else:
        opening = (
            "A clear front view of %s, in %s. Draw exactly one complete object."
            % (brief.object, style)
        )
    body = "\n\n".join(
        (
            opening,
            _edit_block(edits)
            + "Its silhouette, proportions, and construction must be legible "
            "enough for a later CAD build to follow: show how the parts meet, "
            "where surfaces break, and which faces are flat.",
            _shared_blocks(brief),
        )
    )
    return body


def angle_prompt(brief: ConceptBrief, angle: str, *, edits: Sequence[str] = ()) -> str:
    """`top` and `bottom`, phrased as edits of the anchor rather than fresh views."""

    if angle not in ("top", "bottom"):
        raise ContractError("concept angle must be top or bottom")
    opening = (
        "Reference image 1 is the FRONT VIEW of %s, already in the intended "
        "style. Depict the SAME object, unchanged, from a clear %s view. "
        "Preserve every shape, proportion, feature, material, and finish choice "
        "from the reference — only the camera angle changes."
        % (brief.object, angle)
    )
    return "\n\n".join((opening, _edit_block(edits) + _shared_blocks(brief)))


def exploded_prompt(
    brief: ConceptBrief, *, missing: Sequence[str] = ()
) -> str:
    """The one image where every component is visible by construction."""

    named = "; ".join(
        "%s (%s)" % (item.key, item.name) for item in brief.components
    )
    opening = (
        "Reference images 1, 2, and 3 are the front, top, and bottom views of "
        "%s. Depict the SAME object as an exploded view: every component "
        "separated along its assembly axes, each one wholly visible, and none "
        "hidden behind, inside, or overlapping another. Preserve the material, "
        "finish, palette, and form language of the references."
        % brief.object
    )
    parts = (
        "Show exactly these %d components, all of them, each as its own "
        "separated part: %s." % (len(brief.components), named)
    )
    if missing:
        parts += (
            " The previous attempt did not show these components as separated "
            "parts; they must each be visible this time: %s."
            % ", ".join(missing)
        )
    return "\n\n".join((opening, parts, _shared_blocks(brief)))


def component_prompt(brief: ConceptBrief, component: ConceptComponent) -> str:
    """One component alone, specified in text and matched in appearance only.

    The shape is never asked for "as it appears in" a view that may hide the
    part. The exploded view is the single reference that shows it whole, and the
    written specification governs its form.
    """

    if not isinstance(component, ConceptComponent):
        raise ContractError("concept component prompt requires a ConceptComponent")
    opening = (
        "Reference image 1 is the exploded view of %s and reference image 2 is "
        "its front view. Show only the %s (%s), alone, as it appears in the "
        "exploded view."
        % (brief.object, component.key, component.name)
    )
    specification = "\n".join(
        (
            "Its shape is given here, not read off any view that hides it:",
            "- Form: %s" % component.form,
            "- Bounding dimensions: %s" % _extent(component.dimensions_mm),
            "- Placement in the assembly: %s" % component.placement,
            "- Interfaces: %s" % component.interfaces,
            "- Purpose: %s" % component.purpose,
        )
    )
    inheritance = (
        "Take material, finish, palette, surface treatment, and form language "
        "from the references; take the shape from the specification above. Draw "
        "this component alone, with no other component beside it."
    )
    return "\n\n".join((opening, specification, inheritance, _shared_blocks(brief)))


def concept_handoff_text(concept: ConceptImages) -> str:
    """Name every attached image by position and role, and say what it settles.

    Roles never travel as captions: concept images are handed back to an image
    model as references, so text inside a reference is text the next image can
    inherit.
    """

    if not isinstance(concept, ConceptImages):
        raise ContractError("concept handoff requires a ConceptImages record")
    lines = [
        "The attached images are the approved concept for this round. They say "
        "what to build; they are not a picture of anything that has been built.",
        "",
    ]
    position = 0
    for role in CONCEPT_OVERALL_ROLES:
        position += 1
        lines.append(
            "Image %d is the %s view (%s)."
            % (position, role, concept.overall[role])
        )
    for key in sorted(concept.components):
        component = concept.brief.component(key)
        position += 1
        lines.append(
            "Image %d shows the component %s — %s (%s)."
            % (position, key, component.name, concept.components[key])
        )
    lines.extend(
        (
            "",
            "The front, top, and bottom views establish form and proportion. "
            "The exploded view establishes the part breakdown. Each component "
            "image establishes one part. Where an image and the brief's "
            "millimetres disagree, the numbers below govern.",
            "",
            "Design brief (JSON):",
            json.dumps(
                concept.brief.to_dict(),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            ),
        )
    )
    return "\n".join(lines)


def _sequence(value: Any) -> Tuple[Any, ...]:
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Sequence):
        return ()
    return tuple(value)


def _constraint_dimensions(value: Any) -> Optional[Tuple[float, float, float]]:
    numbers = _sequence(value)
    if len(numbers) != 3:
        return None
    try:
        return tuple(float(item) for item in numbers)  # type: ignore[return-value]
    except (TypeError, ValueError):
        return None


def _components_from_constraints(value: Any) -> Tuple[ConceptComponent, ...]:
    declared = _sequence(value)
    components = []
    for index, item in enumerate(declared):
        if not isinstance(item, Mapping):
            raise ContractError("Wish component %d must be an object" % (index + 1))
        missing = {
            "key",
            "name",
            "purpose",
            "form",
            "dimensions_mm",
            "placement",
            "interfaces",
        } - set(item)
        if missing:
            raise ContractError(
                "Wish component %s is missing %s"
                % (item.get("key", index + 1), ", ".join(sorted(missing)))
            )
        components.append(
            ConceptComponent(
                item["key"],
                item["name"],
                item["purpose"],
                item["form"],
                item["dimensions_mm"],
                item["placement"],
                item["interfaces"],
            )
        )
    return tuple(components)


# The rules a returned breakdown is refused by, named so a refusal says which
# one refused it. A missing capability is a Need; a capability that ran and
# produced something unusable is a refusal, because retrying it blindly is
# exactly what this Workshop does not do.
RESEARCH_RULE_FEATURES_RESTATE_OBJECTIVE = "features-restate-the-objective"
RESEARCH_RULE_LONE_COMPONENT_RESTATES_ENVELOPE = (
    "lone-component-restates-the-envelope"
)
RESEARCH_RULE_SINGLE_COMPONENT_UNDECLARED = (
    "single-component-without-a-one-part-finding"
)

# Words that say nothing a decided envelope does not already say. A lone
# component whose form, placement, and interfaces are drawn entirely from this
# vocabulary has restated the bounding box and called it a part breakdown.
_ENVELOPE_RESTATEMENT_WORDS = frozenset(
    """
    a an and are as at be beside body bodies by closed design designs else
    envelope face faces flat following for in is it its meet meets none
    nothing of on one part parts piece pieces print printed prints shell
    single sit sits surface surfaces that the there this to whole with where
    carries carrying holds holding assembly assemblies
    """.split()
)

_ONE_PART_PHRASES = ("one part", "single part", "one printed part", "one piece")


def _refuse(rule: str, message: str) -> "ContractError":
    return ContractError("wish research refused by rule %s: %s" % (rule, message))


def _normalized_words(text: str) -> Tuple[str, ...]:
    cleaned = "".join(
        character.casefold() if character.isalnum() else " " for character in text
    )
    return tuple(word for word in cleaned.split() if word)


def _restates_objective(feature: str, objective: str) -> bool:
    stated = " ".join(_normalized_words(objective))
    if not stated:
        return False
    return stated in " ".join(_normalized_words(feature))


def assert_researched_breakdown(wish: Wish, research: WishResearch) -> None:
    """Refuse a breakdown that decided nothing, naming the rule that refused it.

    The record itself already refuses an unattributed fact, a cited source it
    does not carry, and an excerpt whose hash does not match. These are the
    rules that need the Wish to judge: whether the breakdown actually said
    something this Wish did not already say.
    """

    if not isinstance(wish, Wish):
        raise ContractError("wish research must be checked against its Wish")
    if not isinstance(research, WishResearch):
        raise ContractError("wish research must be a WishResearch record")
    if len(research.features) == 1 and _restates_objective(
        research.features[0], wish.objective
    ):
        raise _refuse(
            RESEARCH_RULE_FEATURES_RESTATE_OBJECTIVE,
            "its only distinctive feature repeats the Wish's own objective, so "
            "it decides nothing this Wish did not already say",
        )
    if len(research.components) != 1:
        return
    lone = research.components[0]
    spoken = _normalized_words(
        " ".join((lone.form, lone.placement, lone.interfaces))
    )
    if spoken and set(spoken) <= _ENVELOPE_RESTATEMENT_WORDS:
        raise _refuse(
            RESEARCH_RULE_LONE_COMPONENT_RESTATES_ENVELOPE,
            "its single component %r states nothing about the design that the "
            "envelope does not already state" % lone.key,
        )
    declared = any(
        phrase in " ".join(_normalized_words(item.claim))
        for item in research.findings_for("components")
        for phrase in _ONE_PART_PHRASES
    )
    if not declared:
        raise _refuse(
            RESEARCH_RULE_SINGLE_COMPONENT_UNDECLARED,
            "it names one component without recording the finding that this "
            "design is genuinely one printed part",
        )


def _assumption_from(finding: WishResearchFinding) -> str:
    return "%s Decided because %s" % (
        finding.claim.rstrip() if finding.claim.rstrip().endswith((".", "!", "?"))
        else finding.claim.rstrip() + ".",
        finding.decided_because,
    )


def derive_brief(context: ConceptContext, research: WishResearch) -> ConceptBrief:
    """Lock the design's facts from the research done for this Wish.

    Nothing is substituted here. Every number comes from the breakdown research
    returned, and the facts that breakdown decided rather than sourced become
    the brief's ``assumptions``, each carrying the reason it was decided that
    way. A refining round starts from the standing brief so its numbers do not
    drift under feedback that never named a physical fact.
    """

    if not isinstance(context, ConceptContext):
        raise ContractError("concept brief derivation requires a ConceptContext")
    if context.previous is not None:
        standing = context.previous.brief
        assumptions = [
            item
            for item in standing.assumptions
            if not item.startswith(_REVISION_PREFIX)
        ]
        assumptions.extend(_accumulated_edits(context))
        return ConceptBrief(
            standing.object,
            standing.category,
            standing.envelope_mm,
            standing.wall_mm,
            standing.features,
            standing.print,
            standing.components,
            standing.fits,
            tuple(assumptions),
        )
    assert_researched_breakdown(context.wish, research)
    assumptions = [_assumption_from(item) for item in research.decisions()]

    # A Wish that already states its own parts is honoured: those components
    # were decided by the person who wished, not by research, and the brief
    # says which of the two decided them.
    components = _components_from_constraints(
        dict(context.wish.constraints).get("components")
    )
    if components:
        assumptions.append(
            "The Wish stated its own part breakdown; those components are "
            "decided by the Wish rather than by research."
        )
    else:
        components = tuple(research.components)

    assumptions.extend(_accumulated_edits(context))
    return ConceptBrief(
        research.object,
        research.category,
        research.envelope_mm,
        research.wall_mm,
        research.features,
        research.print,
        components,
        research.fits,
        tuple(assumptions),
    )


def derived_wish_from(wish: Wish, brief: ConceptBrief) -> DerivedWish:
    """Write the brief's researched facts back as a second Wish record.

    The routed Wish keeps its bytes — routing was decided from them — so this
    is a new record carrying the same words and the constraints research added
    to them, naming both identities so the two cannot be confused.
    """

    if not isinstance(brief, ConceptBrief):
        raise ContractError("a derived Wish requires a locked ConceptBrief")
    constraints = dict(wish.constraints)
    constraints.update(
        {
            "object": brief.object,
            "category": brief.category,
            "envelope_mm": list(brief.envelope_mm),
            "wall_mm": brief.wall_mm,
            "features": list(brief.features),
            "print_orientation": brief.print["orientation"],
            "print_supports": brief.print["supports"],
            "components": [item.to_dict() for item in brief.components],
        }
    )
    if brief.fits is None:
        constraints.pop("fits", None)
    else:
        constraints["fits"] = dict(brief.fits)
    derived = DerivedWish.derive(wish, constraints)
    derived.assert_derived_from(wish)
    return derived


def _design_edits(context: ConceptContext) -> Tuple[str, ...]:
    """The feedback this round asks the *design* to answer.

    Feedback that invalidates only the build leaves the design standing: it is
    Make's problem, and re-drawing the concept for it would be the very drift
    this loop exists to avoid.
    """

    return tuple(
        item.change
        for item in context.feedback
        if "concept" in item.invalidates
    )


def _accumulated_edits(context: ConceptContext) -> Tuple[str, ...]:
    """Every correction so far, not only this round's.

    Panda's refine risk is that each round re-renders from the last image and
    small reinterpretations compound. Carrying the whole edit list means an
    earlier correction does not have to survive in pixels alone.
    """

    earlier: Tuple[str, ...] = ()
    if context.previous is not None:
        earlier = tuple(
            item
            for item in context.previous.brief.assumptions
            if item.startswith(_REVISION_PREFIX)
        )
    return earlier + tuple(
        _REVISION_PREFIX + item for item in _design_edits(context)
    )


def _edits_for_prompt(brief: ConceptBrief) -> Tuple[str, ...]:
    return tuple(
        item[len(_REVISION_PREFIX) :]
        for item in brief.assumptions
        if item.startswith(_REVISION_PREFIX)
    )


def _research_provenance() -> Dict[str, Any]:
    """The same honest-labelling block the concept art carries.

    Research says what should be built and what that decision rested on. It is
    an instruction, exactly as the pixels are, and it can never stand in as a
    picture of what was made.
    """

    return {
        "kind": "wish research",
        "research": True,
        "describes": "an intended design, not a manufactured artifact",
        "valid_as_product_proof": False,
    }


def _write_research(root: Path, research: WishResearch) -> None:
    """Seal the findings and their sources inside the concept root.

    ``build_artifact_manifest`` walks the whole root, so anything written here
    is covered by ``concept_sha256`` and re-checked by ``assert_current()``
    without any new sealing machinery.
    """

    if not isinstance(research, WishResearch):
        raise ContractError("a concept can only seal a WishResearch record")
    directory = root / CONCEPT_RESEARCH_DIRECTORY
    directory.mkdir(mode=0o700)
    sources = directory / CONCEPT_RESEARCH_SOURCES_DIRECTORY
    sources.mkdir(mode=0o700)
    record = research.to_dict()
    filed = []
    for position, source in enumerate(research.sources, start=1):
        relative = "%s/%03d.json" % (CONCEPT_RESEARCH_SOURCES_DIRECTORY, position)
        _write_json(directory / relative, source.to_dict())
        filed.append({"id": source.id, "file": relative})
    findings = {
        "schema_version": 1,
        "kind": "workshop-wish-research",
        "provenance": _research_provenance(),
        "research_sha256": research.research_sha256,
        "decided": {
            key: record[key]
            for key in (
                "object",
                "category",
                "envelope_mm",
                "wall_mm",
                "features",
                "print",
                "components",
                "fits",
            )
        },
        "findings": record["findings"],
        "sources": filed,
    }
    _write_json(directory / CONCEPT_RESEARCH_FINDINGS_FILENAME, findings)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


class DefaultConcept:
    """Draw one consistent concept, or wait truthfully for the capability.

    ``concept_artist`` receives one :class:`ConceptImageRequest` at a time,
    writes the image into the request's workspace, and returns its path relative
    to the concept root. Requests arrive in dependency order — ``front``, then
    ``top`` and ``bottom``, then ``exploded``, then one per component — so a
    provider never has to know the anchoring rules to satisfy them.

    ``explode_inspector`` receives the finished exploded image and the brief and
    returns the component keys it can see as separated parts. Every component
    image is derived from that one image, so it is checked before any of them is
    drawn. Without an inspector the completeness guarantee cannot be made, and
    Concept says so rather than proceeding as if it had been checked.

    ``brief_maker`` replaces :func:`derive_brief` for an inventor that already
    knows its own physical facts. Everything downstream — the prompts, the
    order, the checks, the seal — is unchanged, because the brief is the only
    thing it decides.

    ``wish_researcher`` receives one :class:`WishResearchRequest` and returns
    the breakdown the brief is derived from. It runs once per run, at the top
    of the first round; a refining round reuses the standing concept's
    research. Without one the job waits rather than substituting a fixed
    envelope, wall, feature, print stance, or part breakdown for research that
    never happened.
    """

    def __init__(
        self,
        concept_artist: Optional[ConceptArtist] = None,
        explode_inspector: Optional[ExplodeInspector] = None,
        brief_maker: Optional[Callable[[ConceptContext], ConceptBrief]] = None,
        wish_researcher: Optional[WishResearcher] = None,
    ) -> None:
        self.concept_artist = concept_artist
        self.explode_inspector = explode_inspector
        self.brief_maker = brief_maker
        self.wish_researcher = wish_researcher

    def with_wish_researcher(
        self, wish_researcher: WishResearcher
    ) -> "DefaultConcept":
        """A copy of this job with the Workshop's shared researcher installed."""

        return DefaultConcept(
            self.concept_artist,
            self.explode_inspector,
            self.brief_maker,
            wish_researcher,
        )

    def __call__(self, context: ConceptContext) -> ConceptImages:
        if not isinstance(context, ConceptContext):
            raise ContractError("DefaultConcept requires a ConceptContext")
        needs = []
        if self.wish_researcher is None:
            needs.append(
                Need(
                    "concept",
                    "wish-research",
                    "The brief's physical facts are derived from research into "
                    "what the wished-for object actually is, and no wish-research "
                    "capability is configured.",
                    "Configure the shared wish-research capability; do not "
                    "substitute default physical facts for research that did "
                    "not happen.",
                )
            )
        if self.concept_artist is None:
            needs.append(
                Need(
                    "concept",
                    "concept-images",
                    "This Wish needs one concrete visualized design before Make "
                    "can build to it, and no concept image provider is configured.",
                    "Configure the shared concept image provider; do not describe "
                    "or placeholder a design that was never drawn.",
                )
            )
        if self.explode_inspector is None:
            needs.append(
                Need(
                    "concept",
                    "exploded-view-check",
                    "Every component image is derived from the exploded view, so "
                    "that view must be checked for completeness before they are "
                    "drawn, and no checker is configured.",
                    "Configure the shared exploded-view component check; do not "
                    "draw component views from an unverified explode.",
                )
            )
        if needs:
            raise WaitingFor(*needs)
        assert self.concept_artist is not None
        assert self.explode_inspector is not None
        assert self.wish_researcher is not None

        # Research first, before a workspace exists to write a brief into: no
        # physical fact may be settled ahead of the research that decides it.
        research = self._research(context)

        root = context.workspace
        if root.exists():
            if root.is_symlink() or not root.is_dir() or any(root.iterdir()):
                raise ContractError("Concept workspace must be fresh and empty")
        else:
            root.mkdir(parents=True, mode=0o700)
        root = root.resolve(strict=True)
        (root / CONCEPT_IMAGE_DIRECTORY).mkdir(mode=0o700)

        if self.brief_maker is None:
            brief = derive_brief(context, research)
        else:
            brief = self.brief_maker(context)
            if not isinstance(brief, ConceptBrief):
                raise ContractError("concept brief maker must return a ConceptBrief")
        if context.previous is None:
            derived_wish = derived_wish_from(context.wish, brief)
        else:
            derived_wish = context.previous.derived_wish
            assert isinstance(derived_wish, DerivedWish)
            derived_wish.assert_derived_from(context.wish)
        _write_research(root, research)
        style = style_descriptor(context.taste)
        edits = _edits_for_prompt(brief)
        overall: Dict[str, str] = {}

        re_anchor = context.refine_depth >= MAX_CONCEPT_REFINE_DEPTH
        previous_front: Tuple[Path, ...] = ()
        if context.previous is not None and not re_anchor:
            previous_front = (
                context.previous.root / context.previous.overall["front"],
            )
        overall["front"] = self._draw(
            context,
            brief,
            root,
            role="front",
            kind="overall",
            prompt=anchor_prompt(
                brief,
                style,
                edits=edits,
                from_previous=bool(previous_front),
            ),
            references=previous_front,
        )
        front_path = root / overall["front"]
        for angle in ("top", "bottom"):
            overall[angle] = self._draw(
                context,
                brief,
                root,
                role=angle,
                kind="overall",
                prompt=angle_prompt(brief, angle, edits=edits),
                references=(front_path,),
            )
        exploded_references = (
            front_path,
            root / overall["top"],
            root / overall["bottom"],
        )
        overall["exploded"] = self._draw(
            context,
            brief,
            root,
            role="exploded",
            kind="overall",
            prompt=exploded_prompt(brief),
            references=exploded_references,
        )
        overall["exploded"] = self._complete_explode(
            context, brief, root, overall["exploded"], exploded_references
        )

        component_references = (root / overall["exploded"], front_path)
        components: Dict[str, str] = {}
        for component in brief.components:
            components[component.key] = self._draw(
                context,
                brief,
                root,
                role=component.key,
                kind="component",
                prompt=component_prompt(brief, component),
                references=component_references,
            )

        self._write_descriptor(
            root, brief, overall, components, context.round, research, derived_wish
        )
        # Drawing may be remote and slow. Refuse the result if the standing
        # design or the Taste it was drawn for changed while it ran.
        context.taste.assert_current()
        if context.previous is not None:
            context.previous.assert_current()
        return ConceptImages.from_root(
            root, brief, overall, components, context.round, research, derived_wish
        )

    def _research(self, context: ConceptContext) -> WishResearch:
        """Break the Wish down once per run; a refining round reuses it.

        Re-researching under feedback would let the design's numbers drift for
        a reason that never named a physical fact, which is the same drift the
        standing brief exists to prevent.
        """

        if context.previous is not None:
            standing = context.previous.research
            if not isinstance(standing, WishResearch):
                raise ContractError(
                    "the standing concept carries no research to refine from"
                )
            return standing
        assert self.wish_researcher is not None
        research = self.wish_researcher(
            WishResearchRequest(
                context.wish, context.taste, context.blueprint, context.round
            )
        )
        if not isinstance(research, WishResearch):
            raise ContractError(
                "wish research capability must return a WishResearch breakdown"
            )
        assert_researched_breakdown(context.wish, research)
        return research

    def _draw(
        self,
        context: ConceptContext,
        brief: ConceptBrief,
        root: Path,
        *,
        role: str,
        kind: str,
        prompt: str,
        references: Sequence[Path],
    ) -> str:
        assert self.concept_artist is not None
        name = role if kind == "overall" else "component-%s" % role
        request = ConceptImageRequest(
            role,
            kind,
            prompt,
            tuple(Path(item).resolve(strict=True) for item in references),
            root,
            "%s/%s.png" % (CONCEPT_IMAGE_DIRECTORY, name),
            brief,
            context.round,
        )
        produced = self.concept_artist(request)
        if not isinstance(produced, str):
            raise ContractError(
                "concept artist must return the relative path of the %s image"
                % role
            )
        return _safe_concept_image(root, produced, role)

    def _complete_explode(
        self,
        context: ConceptContext,
        brief: ConceptBrief,
        root: Path,
        relative: str,
        references: Sequence[Path],
    ) -> str:
        """Count the explode's parts before anything is derived from it."""

        missing = self._missing_components(brief, root / relative)
        if not missing:
            return relative
        retry = self._draw(
            context,
            brief,
            root,
            role="exploded",
            kind="overall",
            prompt=exploded_prompt(brief, missing=missing),
            references=references,
        )
        if retry != relative:
            stale = root / relative
            if stale.is_file():
                stale.unlink()
        still_missing = self._missing_components(brief, root / retry)
        if still_missing:
            raise ContractError(
                "concept exploded view does not separate %s; component views "
                "cannot be drawn from it" % ", ".join(still_missing)
            )
        return retry

    def _missing_components(
        self, brief: ConceptBrief, image: Path
    ) -> Tuple[str, ...]:
        assert self.explode_inspector is not None
        observed = self.explode_inspector(image, brief)
        if isinstance(observed, (str, bytes, Mapping)) or not isinstance(
            observed, Sequence
        ):
            raise ContractError(
                "exploded-view check must return the component keys it can see"
            )
        seen = set()
        for item in observed:
            if item not in brief.component_keys:
                raise ContractError(
                    "exploded-view check named %r, which the brief does not" % item
                )
            seen.add(item)
        return tuple(key for key in brief.component_keys if key not in seen)

    @staticmethod
    def _write_descriptor(
        root: Path,
        brief: ConceptBrief,
        overall: Mapping[str, str],
        components: Mapping[str, str],
        round_number: int,
        research: WishResearch,
        derived_wish: DerivedWish,
    ) -> None:
        """Seal the roles beside the pixels, so relabelling changes the hash."""

        images: Dict[str, Any] = dict(overall)
        images["components"] = dict(components)
        research_binding = _research_provenance()
        research_binding.update(
            {
                "research_sha256": research.research_sha256,
                "findings": "%s/%s"
                % (CONCEPT_RESEARCH_DIRECTORY, CONCEPT_RESEARCH_FINDINGS_FILENAME),
            }
        )
        descriptor = {
            "schema_version": 1,
            "kind": "workshop-concept",
            "round": round_number,
            "concept_art": True,
            "provenance": {
                "kind": "concept art",
                "concept_art": True,
                "depicts": "an intended design, not a manufactured artifact",
                "valid_as_product_proof": False,
            },
            "brief": brief.to_dict(),
            "images": images,
            "research": research_binding,
            # Both identities, side by side: the words routing was decided from
            # and the record the researched constraints were written back to.
            "derived_wish": {
                "wish_sha256": derived_wish.wish_sha256,
                "derived_wish_sha256": derived_wish.derived_wish_sha256,
            },
        }
        _write_json(root / CONCEPT_DESCRIPTOR_FILENAME, descriptor)


__all__ = [
    "CONCEPT_IMAGE_DIRECTORY",
    "CONCEPT_RESEARCH_DIRECTORY",
    "CONCEPT_RESEARCH_FINDINGS_FILENAME",
    "CONCEPT_RESEARCH_SOURCES_DIRECTORY",
    "ConceptArtist",
    "ConceptImageRequest",
    "DESIGN_FACTS_HEADING",
    "DefaultConcept",
    "ExplodeInspector",
    "MAX_CONCEPT_REFINE_DEPTH",
    "NEUTRAL_PRESENTATION",
    "RESEARCH_RULE_FEATURES_RESTATE_OBJECTIVE",
    "RESEARCH_RULE_LONE_COMPONENT_RESTATES_ENVELOPE",
    "RESEARCH_RULE_SINGLE_COMPONENT_UNDECLARED",
    "WishResearchRequest",
    "WishResearcher",
    "anchor_prompt",
    "angle_prompt",
    "assert_researched_breakdown",
    "component_prompt",
    "concept_handoff_text",
    "derive_brief",
    "derived_wish_from",
    "design_facts_block",
    "exploded_prompt",
    "style_descriptor",
]
