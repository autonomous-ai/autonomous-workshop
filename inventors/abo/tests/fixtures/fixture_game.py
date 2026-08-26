"""One small, complete, consistent game, and the ways a game can be wrong.

`notchline` exists so ABO's declared checks can prove their contracts with no
model, no network, and no printer: the rules-versus-bill check on a good game
and on each way of breaking it, the Wish-is-structural rule, colour freedom,
the brief the bill becomes, and — through `fixture_engine.py` — the simulation
floor, the style-distinctness measurement, and the seat boundary.

It is a fixture, not a proposal. It is small enough to read in one sitting and
deliberately plain, because its job is to make the checks fail for the reason
the test says and for no other.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from game import (  # noqa: E402
    DesignContract,
    GameComponent,
    GameRecord,
    RuleStep,
    WishHook,
)


FIXTURE_OBJECTIVE = (
    "I wish for a two-player abstract strategy game that is quick to teach and "
    "hard to master, where each piece tells you how strong it is just by "
    "looking at it."
)


def fixture_components():
    return (
        GameComponent(
            name="board_frame",
            qty=1,
            desc="The 5x5 socket grid both players build on.",
            form=(
                "Flat square plate, chamfered outer edge, a pierced hole at each "
                "socket floor so a seated pillar stops positively."
            ),
            dimensions_mm=(180.0, 180.0, 8.0),
            placement="Between the two seats, socket grid facing up.",
            interfaces="Each socket accepts one pillar spigot or one lock marker.",
        ),
        GameComponent(
            name="pillar_low",
            qty=12,
            per_player=6,
            desc="The weaker pillar. One notch, so its rank is read at a glance.",
            form=(
                "Square shaft on the shared footprint, one notch cut around the "
                "shaft below the cap."
            ),
            dimensions_mm=(14.0, 14.0, 18.0),
            placement="Standing in a board socket.",
            interfaces="Spigot seats into a socket; cap is flat so pillars stack flush.",
        ),
        GameComponent(
            name="pillar_high",
            qty=12,
            per_player=6,
            desc="The stronger pillar. Three notches, and taller.",
            form=(
                "Same square footprint as the low pillar, roughly twice the "
                "height, three notches cut around the shaft."
            ),
            dimensions_mm=(14.0, 14.0, 34.0),
            placement="Standing in a board socket.",
            interfaces="Spigot seats into a socket; cap is flat.",
        ),
        GameComponent(
            name="marker_lock",
            qty=4,
            per_player=2,
            desc="Seals one socket a player already holds so it can never empty.",
            form=(
                "Pierced disc with a knurled relief rim, sitting flush in the "
                "socket mouth."
            ),
            dimensions_mm=(12.0, 12.0, 4.0),
            placement="Flush in an occupied socket.",
            interfaces="Drops into the socket mouth around a seated pillar spigot.",
        ),
    )


def fixture_record(**overrides) -> GameRecord:
    """The good game. Keyword arguments replace one field for a failure test."""

    values = dict(
        slug="notchline",
        title="Notchline",
        central_idea=(
            "Two players fill a shared grid with pillars of two heights and win "
            "by owning the run of sockets carrying the most notches without ever "
            "stepping down, so every placement both builds your own run and "
            "spoils the run your opponent was building through the same square."
        ),
        players_min=2,
        players_max=2,
        playtime_min=20,
        setup=(
            RuleStep(
                "Place the board frame between the players with the socket grid "
                "facing up. Every socket starts empty.",
                ["board_frame"],
            ),
            RuleStep(
                "Each player takes six low pillars and six high pillars as a "
                "reserve, kept where both players can count them.",
                ["pillar_low", "pillar_high"],
            ),
            RuleStep(
                "Each player takes two lock markers and keeps them beside their "
                "reserve.",
                ["marker_lock"],
            ),
        ),
        turn=(
            RuleStep(
                "On your turn, seat one pillar from your reserve into any empty "
                "socket on the board frame.",
                ["pillar_low", "pillar_high", "board_frame"],
            ),
            RuleStep(
                "Instead of seating a pillar, you may spend one lock marker into "
                "a socket you already occupy. A locked socket can never be "
                "emptied for the rest of the game.",
                ["marker_lock", "board_frame"],
            ),
        ),
        end=(
            RuleStep(
                "The game ends at the end of the turn on which no socket of the "
                "board frame is empty, or on which the player to move holds "
                "neither a pillar nor a lock marker.",
                ["board_frame", "pillar_low", "pillar_high", "marker_lock"],
            ),
        ),
        win=RuleStep(
            "You win if you hold the straight run of adjacent sockets with the "
            "greatest total notch count, counting only runs in which no socket "
            "is lower than the socket before it. A tie in total is broken by "
            "the run holding more lock markers, and a tie in both is a draw.",
            ["board_frame", "pillar_low", "pillar_high", "marker_lock"],
        ),
        components=fixture_components(),
        art_direction=(
            "Every pillar shares one square footprint, so rank is never a matter "
            "of size at the base: it is read from the notch count cut around the "
            "shaft, one notch against three.",
            "The board frame is a flat plate with a chamfered outer edge and a "
            "pierced hole at each socket floor, so a seated pillar reaches a "
            "positive stop rather than a friction fit.",
            "Lock markers are pierced discs with a knurled relief rim, sitting "
            "flush in the socket mouth so a locked square reads by silhouette "
            "from the far side of the table.",
        ),
        action_types=("seat_pillar", "spend_lock"),
        design_contract=DesignContract(
            core_experience=(
                "Every placement is two decisions at once, because the run you "
                "extend is the run your opponent wanted."
            ),
            core_mechanism=(
                "A never-descending run of notch counts along a straight line "
                "of sockets, on a grid both players share."
            ),
            must_preserve=(
                "Two pillar ranks and no third.",
                "One shared grid rather than a board per player.",
                "Rank readable from the piece itself, without a reference card.",
            ),
            anti_goals=(
                "A third action type.",
                "Hidden reserves.",
                "Any distinction that needs colour to be made.",
            ),
            kill_criteria=(
                "A first-seat win rate whose interval floor sits above 55%.",
                "A dominant opening that lookahead cannot beat.",
                "More than a quarter of turns offering no real choice.",
            ),
            max_rule_words=260,
            max_action_types=3,
        ),
        wish_hooks=(
            WishHook(
                "each piece tells you how strong it is just by looking at it",
                "component",
                "pillar_high",
            ),
            WishHook(
                "each piece tells you how strong it is just by looking at it",
                "rule",
                "win[1]",
            ),
            WishHook("quick to teach", "rule", "turn[1]"),
            WishHook("hard to master", "rule", "win[1]"),
        ),
    )
    values.update(overrides)
    return GameRecord(**values)


# -- the ways a game can be wrong -------------------------------------------


def record_reaching_for_absent_component() -> GameRecord:
    """A rule step uses a piece the bill does not contain."""

    record = fixture_record()
    return fixture_record(
        turn=(
            RuleStep(record.turn[0].text, ["pillar_low", "pillar_high", "board_frame"]),
            RuleStep(record.turn[1].text, ["marker_lock", "board_frame", "score_track"]),
        )
    )


def record_with_unused_component() -> GameRecord:
    """The box contains a piece no rule ever reaches for."""

    return fixture_record(
        components=fixture_components()
        + (
            GameComponent(
                name="spare_riser",
                qty=2,
                desc="A part nothing in the rules ever asks for.",
                form="Square riser on the shared footprint, no notch.",
                dimensions_mm=(14.0, 14.0, 9.0),
                placement="In the box.",
                interfaces="Spigot seats into a socket.",
            ),
        )
    )


def record_over_its_own_ceiling() -> GameRecord:
    """The design goes through the complexity budget it declared itself."""

    contract = fixture_record().design_contract
    return fixture_record(
        design_contract=DesignContract(
            core_experience=contract.core_experience,
            core_mechanism=contract.core_mechanism,
            must_preserve=contract.must_preserve,
            anti_goals=contract.anti_goals,
            kill_criteria=contract.kill_criteria,
            max_rule_words=40,
            max_action_types=3,
        )
    )


def record_with_decorative_wish() -> GameRecord:
    """The Wish reaches the title and nothing that decides the game."""

    return fixture_record(
        wish_hooks=(
            WishHook("hard to master", "title", "Notchline"),
        )
    )


def record_without_wish_hooks() -> GameRecord:
    return fixture_record(wish_hooks=())


def record_distinguishing_by_colour() -> GameRecord:
    """A rule asks a player to tell two pieces apart by colour."""

    record = fixture_record()
    return fixture_record(
        turn=(
            RuleStep(
                "On your turn, seat one white or black pillar from your reserve "
                "into any empty socket on the board frame.",
                ["pillar_low", "pillar_high", "board_frame"],
            ),
            record.turn[1],
        )
    )


def record_with_empty_art_direction() -> GameRecord:
    """Art direction that says nothing in form language."""

    return fixture_record(
        art_direction=("Make it look handsome and grown-up on the table.",)
    )


__all__ = [
    "FIXTURE_OBJECTIVE",
    "fixture_components",
    "fixture_record",
    "record_distinguishing_by_colour",
    "record_over_its_own_ceiling",
    "record_reaching_for_absent_component",
    "record_with_decorative_wish",
    "record_with_empty_art_direction",
    "record_with_unused_component",
    "record_without_wish_hooks",
]
