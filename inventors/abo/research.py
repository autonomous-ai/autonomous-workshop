"""ABO's wish research: invent the game, then state its physical facts.

Workshop's Concept derives its brief from a researched breakdown of the Wish —
a closed record of *physical* facts with no field in it for game rules. For an
abstract game that ordering is the wrong way round, because the pieces are the
rules: there is nothing to state the envelope of until the game exists.

So ABO's researcher does both halves in order. It asks its game inventor for a
complete game, refuses it unless the deterministic checks pass, and then reads
the physical facts *off* that game — the bill becomes the components, the board
decides the envelope, the socket decides the fit. Every fact it states carries
either a source the inventor recorded or ABO's own decision with the reason it
was chosen, because a number nobody stands behind must not reach a brief.

The rules themselves do not travel in the breakdown. `WishResearch`'s field
vocabulary is closed to eight physical-fact names, and widening it would make
one lane's concept a shared contract. The rules are sealed into the concept
root instead — see `concept.py` and design decision D1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple

from inventor_workshop.concept import WishResearchRequest
from inventor_workshop.jobs import (
    ConceptComponent,
    Need,
    WaitingFor,
    WishResearch,
    WishResearchFinding,
    WishResearchSource,
)

from game import GameRecord, assert_playable_record, CheckResult


# The board sits inside a box with room for a lid and for the reserve; these
# are ABO's decisions and are recorded as such, never presented as measured.
BOX_MARGIN_MM = 12.0
BOX_LID_MM = 14.0
DEFAULT_WALL_MM = 2.4
SOCKET_CLEARANCE_MM = 0.25


# A Wish whose meaning is a person, a relationship, a place or a memory belongs
# to the inventor whose Taste requires exactly that. ABO refusing it is not
# modesty: answering it with an abstract game would deliver something nobody
# asked for, and the Wish-is-structural rule would then refuse the result
# anyway — later, and less clearly.
PERSONAL_MARKERS = (
    "my husband", "my wife", "my partner", "my son", "my daughter", "my mum",
    "my mother", "my dad", "my father", "my sister", "my brother", "my family",
    "my household", "my friends", "my team", "my class", "my grandmother",
    "my grandfather", "our household", "our family", "our in-jokes",
    "our inside joke", "our wedding", "our holiday", "our anniversary",
    "in-jokes", "inside jokes", "private joke", "shared history",
    "the day we", "the summer we", "the year we", "in memory of",
    "to remember", "remembers the", "based on our", "built around my",
    "built around our", "for my", "for our",
)


class WishRefused(ValueError):
    """This Wish belongs to a different inventor, and ABO says which."""


def assert_wish_is_abstract(wish) -> None:
    """Refuse a Wish whose meaning is a person, a place, or a memory."""

    objective = getattr(wish, "objective", "") or ""
    lowered = objective.casefold()
    found = sorted({marker for marker in PERSONAL_MARKERS if marker in lowered})
    if found:
        raise WishRefused(
            "ABO refuses this Wish: its meaningful content is a person, a "
            "relationship, a place, or a memory (%s). ABO invents abstract "
            "games whose depth is combinatorial, and it would make a worse "
            "version of this than the inventor in the same lane whose Taste "
            "requires a Wish's people and private references to become "
            "mechanism. Route it there." % ", ".join(repr(item) for item in found)
        )


@dataclass(frozen=True)
class InventedGame:
    """What a game inventor returns: one game, and any prior art it read."""

    record: GameRecord
    sources: Sequence[WishResearchSource] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.record, GameRecord):
            raise TypeError("a game inventor must return a GameRecord")
        sources = tuple(self.sources)
        if not all(isinstance(item, WishResearchSource) for item in sources):
            raise TypeError("recorded prior art must use WishResearchSource records")
        object.__setattr__(self, "sources", sources)


# Wish + Taste + blueprint in, one game out.
GameInventor = Callable[[WishResearchRequest], InventedGame]


def _decision(claim: str, field: str, because: str) -> WishResearchFinding:
    return WishResearchFinding(claim=claim, field=field, decided_because=because)


def _sourced(claim: str, field: str, source_ids: Sequence[str]) -> WishResearchFinding:
    return WishResearchFinding(claim=claim, field=field, source_ids=tuple(source_ids))


def concept_components(record: GameRecord) -> Tuple[ConceptComponent, ...]:
    """The bill, as the concept's component breakdown.

    One entry per part *type*, at the granularity Make will build and the box
    will contain. Two families that share a body and differ only in relief stay
    two entries, because a player has to tell them apart by shape and Make has
    to build both. How many of each the game needs lives in the purpose line,
    where a count belongs — `ConceptComponent` has no quantity field, and one
    entry per instance would spend the brief's twelve slots on arithmetic.
    """

    built = []
    for item in record.components:
        quantity = "%d in the box" % item.qty
        if item.per_player is not None:
            quantity += ", %d per player" % item.per_player
        built.append(
            ConceptComponent(
                key=item.concept_key,
                name=item.name.replace("_", " "),
                purpose="%s (%s)" % (item.desc, quantity),
                form=item.form,
                dimensions_mm=item.dimensions_mm,
                placement=item.placement,
                interfaces=item.interfaces,
            )
        )
    return tuple(built)


def _largest(record: GameRecord):
    return max(record.components, key=lambda item: max(item.dimensions_mm))


def research_from_game(
    record: GameRecord, sources: Sequence[WishResearchSource] = ()
) -> WishResearch:
    """Read the design's physical facts off the game that was invented.

    Nothing here is substituted for research that did not happen. Every value
    either comes from the game record — which is itself the research, decided
    for this Wish — or is ABO's own decision, and says why.
    """

    board = _largest(record)
    tallest = max(item.dimensions_mm[2] for item in record.components)
    length, width, _height = board.dimensions_mm
    envelope = (
        round(length + 2 * BOX_MARGIN_MM, 1),
        round(width + 2 * BOX_MARGIN_MM, 1),
        round(tallest + BOX_LID_MM, 1),
    )

    known = {item.id for item in sources}
    findings = [
        _decision(
            "The object is a printed edition of %s, a %d-seat abstract strategy "
            "game invented for this Wish." % (record.title, record.players_max),
            "object",
            "the game did not exist before this Wish, so what the object is was "
            "decided by inventing it rather than found",
        ),
        _decision(
            "It is a printed edition of a new game rather than of a known one.",
            "category",
            "the lane is invented games and the rules are original to this Wish",
        ),
        _decision(
            "The box envelope is %s mm: the %s footprint plus %.0f mm of margin "
            "on each side, and the tallest piece (%.0f mm) plus %.0f mm of lid."
            % (
                " x ".join("%.1f" % value for value in envelope),
                board.name,
                BOX_MARGIN_MM,
                tallest,
                BOX_LID_MM,
            ),
            "envelope_mm",
            "the largest component and the tallest piece set the box, and the "
            "margins are chosen so the board lifts out without tipping the "
            "reserve",
        ),
        _decision(
            "Walls are %.1f mm." % DEFAULT_WALL_MM,
            "wall_mm",
            "it is the thinnest wall that prints reliably at a 0.4 mm nozzle in "
            "three perimeters, and every part here is a hand-handled game piece "
            "rather than a load-bearing one",
        ),
        _decision(
            "The bill is %d part types: %s."
            % (len(record.components), ", ".join(record.bill_names)),
            "components",
            "these are exactly the pieces the rules reach for, proved by the "
            "rules-versus-bill consistency check recorded with this design",
        ),
        _decision(
            "Parts print flat on their largest face with no supports.",
            "print",
            "every part is a prism or a plate whose largest face is flat, so "
            "printing it face-down removes the overhangs entirely rather than "
            "propping them up",
        ),
    ]
    for line in record.art_direction:
        findings.append(
            _decision(
                line,
                "features",
                "the game assigns no colour and no material, so every "
                "distinction a player must make is carried by shape and the "
                "art direction is what decides which shape carries which",
            )
        )
    fits = {
        "target": "%s spigot in a %s socket" % (record.components[-1].name, board.name),
        "ref_mm": list(record.components[-1].dimensions_mm),
        "clearance_mm": SOCKET_CLEARANCE_MM,
    }
    findings.append(
        _decision(
            "Pieces seat into the board with %.2f mm of clearance."
            % SOCKET_CLEARANCE_MM,
            "fits",
            "it is the smallest clearance that still seats by hand after the "
            "elephant-foot of a first layer, and a game piece that has to be "
            "forced is a game piece that gets dropped",
        )
    )
    for source in sources:
        findings.append(
            _sourced(
                "Prior art read before inventing: %s." % source.title,
                "object",
                [source.id],
            )
        )
        known.add(source.id)

    return WishResearch(
        object="%s, a printed %d-seat abstract strategy game"
        % (record.title, record.players_max),
        category="a printed edition of a new game",
        envelope_mm=envelope,
        wall_mm=DEFAULT_WALL_MM,
        features=tuple(record.art_direction),
        print={"orientation": "largest flat face down", "supports": False},
        components=concept_components(record),
        fits=fits,
        findings=tuple(findings),
        sources=tuple(sources),
    )


class AboWishResearcher:
    """ABO's `WishResearcher`: invent the game, then state its facts.

    Holds the game it invented and the check result that let it through, so the
    Concept hook can seal both into the concept root without inventing twice.
    A refining round reuses the standing game rather than proposing a new one —
    `revise` folds this round's feedback into the game that is already there.
    """

    def __init__(self, game_inventor: Optional[GameInventor] = None) -> None:
        self.game_inventor = game_inventor
        self._record: Optional[GameRecord] = None
        self._check: Optional[CheckResult] = None
        self._research: Optional[WishResearch] = None

    # -- what the Concept hook reads back --------------------------------
    #
    # `DefaultConcept` asks for research first and for the brief second, so by
    # the time ABO's brief maker runs, whatever the round settled is standing
    # here. That ordering is the whole reason these are readable properties
    # rather than arguments threaded through the job.

    @property
    def record(self) -> Optional[GameRecord]:
        return self._record

    @property
    def check(self) -> Optional[CheckResult]:
        return self._check

    @property
    def research(self) -> Optional[WishResearch]:
        return self._research

    def adopt(
        self,
        record: GameRecord,
        result: CheckResult,
        research: WishResearch,
    ) -> None:
        """Carry a standing game into a refining round without re-inventing.

        `DefaultConcept` reuses the standing concept's research on a refining
        round and never calls this researcher again, so the round's game and
        its facts are placed here instead of returned.
        """

        self._record, self._check, self._research = record, result, research

    # -- the WishResearcher contract -------------------------------------

    def __call__(self, request: WishResearchRequest) -> WishResearch:
        if not isinstance(request, WishResearchRequest):
            raise TypeError("AboWishResearcher requires a WishResearchRequest")
        if self.game_inventor is None:
            raise WaitingFor(
                Need(
                    "concept",
                    "abstract-game-invention",
                    "ABO invents the whole game at Concept — rules, bill and "
                    "art direction — and no game inventor is configured, so "
                    "there is no game for a brief to be derived from.",
                    "Configure ABO's game inventor (the board-game-ideator "
                    "agent, or a fixture for an offline check); never derive a "
                    "brief from a component breakdown nothing decided.",
                )
            )
        # Refused before anything is invented, so a mis-routed Wish costs one
        # sentence rather than a game nobody asked for.
        assert_wish_is_abstract(request.wish)
        invented = self.game_inventor(request)
        if not isinstance(invented, InventedGame):
            raise TypeError("ABO's game inventor must return an InventedGame")
        # Refuse rather than return. A breakdown that fails the check is not a
        # passing breakdown with a warning attached.
        result = assert_playable_record(invented.record, request.wish.objective)
        self._record, self._check = invented.record, result
        self._research = research_from_game(invented.record, invented.sources)
        return self._research


__all__ = [
    "AboWishResearcher",
    "PERSONAL_MARKERS",
    "WishRefused",
    "assert_wish_is_abstract",
    "BOX_LID_MM",
    "BOX_MARGIN_MM",
    "DEFAULT_WALL_MM",
    "GameInventor",
    "InventedGame",
    "SOCKET_CLEARANCE_MM",
    "concept_components",
    "research_from_game",
]
