"""ABO's Concept: invent the game, draw it, and seal both together.

Workshop owns the Concept job's seam and ABO owns this hook, which is what
`docs/ARCHITECTURE.md` permits and what leaves the customization level alone.
The drawing is not reimplemented here: `DefaultConcept` still decides the
order, the anchoring, the exploded-view check and the descriptor, and ABO
supplies it the two things an abstract game changes — the researcher that
invents the game, and the brief derived from that game's own bill.

What this module adds on top is design decision D1. The rules do not fit inside
`WishResearch`, whose field vocabulary is closed to eight physical-fact names,
so they do not travel as a research field. They are written into the concept
root *after* `DefaultConcept` returns, the artifact manifest is rebuilt over the
augmented root, and the returned `ConceptImages` is sealed over all of it. The
concept hash therefore covers the rules, the bill, the check result, the
research and the pixels together — which is what makes `MakeContext`'s seal
re-check able to catch a rules edit made while Make was running.
"""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

from inventor_workshop.concept import (
    DefaultConcept,
    ConceptArtist,
    ExplodeInspector,
    _accumulated_edits,
    _assumption_from,
)
from inventor_workshop.errors import ContractError
from inventor_workshop.jobs import (
    ConceptBrief,
    ConceptContext,
    ConceptImages,
    Feedback,
    MAX_CONCEPT_COMPONENTS,
    WishResearch,
)

from game import (
    CheckResult,
    GameRecord,
    MAX_PIECE_TYPES,
    assert_playable_record,
    write_game_record,
)
from research import AboWishResearcher, GameInventor, InventedGame, concept_components


class AboConcept:
    """`ConceptContext -> ConceptImages` for an inventor that invents the game.

    `game_inventor` is called once per run with the round's Wish, Taste and
    blueprint. On a refining round it is called again with the standing game
    and this round's feedback, and must return a revision of that game — never
    an unrelated one.
    """

    def __init__(
        self,
        concept_artist: Optional[ConceptArtist] = None,
        explode_inspector: Optional[ExplodeInspector] = None,
        game_inventor: Optional[GameInventor] = None,
    ) -> None:
        self.concept_artist = concept_artist
        self.explode_inspector = explode_inspector
        self.game_inventor = game_inventor
        self._record: Optional[GameRecord] = None
        self._check: Optional[CheckResult] = None
        self._research: Optional[WishResearch] = None

    # -- the brief ------------------------------------------------------

    def _make_brief(
        self, context: ConceptContext, researcher: AboWishResearcher
    ) -> ConceptBrief:
        """The bill, as the brief's binding component breakdown.

        `DefaultConcept` calls this after research has run, so the game is
        already standing on the researcher by the time the brief is built.
        Nothing is summarized into prose on the way through: the brief's
        components correspond one-to-one with the bill's, and two families that
        differ only in relief motif stay two components because a player tells
        them apart by shape.
        """

        self._record = researcher.record
        self._check = researcher.check
        self._research = researcher.research
        record, research = self._record, self._research
        if record is None or research is None:
            raise ContractError(
                "ABO's brief is derived from the game it invented, and no game "
                "is standing for this round"
            )
        components = concept_components(record)
        if len(components) > MAX_CONCEPT_COMPONENTS:
            raise ContractError(
                "%s asks for %d distinct part types and a concept may name at "
                "most %d. This is not a cap to argue with: component count is a "
                "learnability cost, and ABO's own ceiling is %d part types. "
                "Subtract a piece family rather than describing the same design "
                "more carefully."
                % (
                    record.title,
                    len(components),
                    MAX_CONCEPT_COMPONENTS,
                    MAX_PIECE_TYPES,
                )
            )

        assumptions = [_assumption_from(item) for item in research.decisions()]
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

    # -- the refining round ---------------------------------------------

    def _revise(self, context: ConceptContext):
        """Fold this round's feedback into the game that is already standing.

        Research runs once per run, so the physical-facts breakdown is the one
        the standing concept carries. The *game* is what this round changes,
        and it changes by revision: the standing record goes in, the same game
        comes back altered, and a returned record that is not a revision of it
        is refused rather than accepted as a fresh idea.
        """

        assert context.previous is not None
        standing = GameRecord.from_root(context.previous.root)
        if self.game_inventor is None:
            raise ContractError(
                "a refining round has to revise the standing game and no game "
                "inventor is configured to revise it"
            )
        revised = self.game_inventor(
            GameRevision(
                standing=standing,
                feedback=tuple(context.feedback),
                wish=context.wish,
                taste=context.taste,
                blueprint=context.blueprint,
                round=context.round,
            )
        )
        if not isinstance(revised, InventedGame):
            raise ContractError("ABO's game inventor must return an InventedGame")
        if revised.record.slug != standing.slug:
            raise ContractError(
                "a refining round returned %r, which is not a revision of the "
                "standing game %r; feedback revises the game it was about"
                % (revised.record.slug, standing.slug)
            )
        return revised.record, assert_playable_record(
            revised.record, context.wish.objective
        )

    # -- the job --------------------------------------------------------

    def __call__(self, context: ConceptContext) -> ConceptImages:
        if not isinstance(context, ConceptContext):
            raise ContractError("ABO's Concept requires a ConceptContext")

        self._record = self._check = self._research = None
        researcher = AboWishResearcher(self.game_inventor)
        if context.previous is not None:
            # `DefaultConcept` reuses the standing concept's research on a
            # refining round and never calls the researcher again, so the
            # standing *game* is revised here and placed on the researcher for
            # the brief maker to read.
            standing_research = context.previous.research
            if not isinstance(standing_research, WishResearch):
                raise ContractError(
                    "the standing concept carries no research to refine from"
                )
            record, check = self._revise(context)
            researcher.adopt(record, check, standing_research)

        job = DefaultConcept(
            self.concept_artist,
            self.explode_inspector,
            lambda inner: self._make_brief(inner, researcher),
            researcher,
        )
        images = job(context)

        if self._record is None or self._check is None:
            raise ContractError("ABO's Concept produced no game to seal")

        # Design decision D1.  The rules are the design for an abstract game,
        # so they belong inside what the concept hash covers, and `WishResearch`
        # has nowhere to put them.  Writing them here and rebuilding the
        # manifest over the augmented root is what puts `game/idea.json` and
        # `game/rules_check.json` under `concept_sha256` alongside the pixels.
        # It reads like tampering with a root a shared job just sealed, which is
        # why it happens in exactly this one place, and why the offline check
        # proves the returned concept's hash covers the game record.
        write_game_record(images.root, self._record, self._check)
        return ConceptImages.from_root(
            images.root,
            images.brief,
            images.overall,
            images.components,
            images.round,
            images.research,
            images.derived_wish,
        )

    # -- what Make reads back -------------------------------------------

    @property
    def record(self) -> Optional[GameRecord]:
        return self._record

    @property
    def check(self) -> Optional[CheckResult]:
        return self._check


class GameRevision:
    """The request a refining round hands the game inventor.

    Deliberately not a `WishResearchRequest`: research does not run again, and
    handing the inventor the same request twice is what invites it to invent
    twice.
    """

    __slots__ = ("standing", "feedback", "wish", "taste", "blueprint", "round")

    def __init__(
        self,
        *,
        standing: GameRecord,
        feedback: Sequence[Feedback],
        wish,
        taste,
        blueprint,
        round: int,
    ) -> None:
        if not isinstance(standing, GameRecord):
            raise ContractError("a game revision requires the standing GameRecord")
        self.standing = standing
        self.feedback: Tuple[Feedback, ...] = tuple(feedback)
        self.wish = wish
        self.taste = taste
        self.blueprint = blueprint
        self.round = round

    @property
    def changes(self) -> Tuple[str, ...]:
        """Every concrete change this round's feedback asked for."""

        return tuple(item.change for item in self.feedback)

    @property
    def design_changes(self) -> Tuple[str, ...]:
        """The changes that invalidate the design rather than only the build.

        A finding that only invalidates the geometry leaves the game standing;
        redesigning the game for it would be exactly the drift the loop exists
        to prevent.
        """

        return tuple(
            item.change for item in self.feedback if "concept" in item.invalidates
        )


__all__ = ["AboConcept", "GameRevision"]
