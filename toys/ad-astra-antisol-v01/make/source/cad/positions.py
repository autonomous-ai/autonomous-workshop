"""Three positions from one game, for the product's state sheet.

A set spends almost none of its life in the perfect symmetric opening, so the
product is shown in three exact states: the opening, a crowded asymmetric
mid-game, and the moment the game ends.  Each is a legal Dou Shou Qi position;
none of them is a rule, and nothing here changes what the plastic can do.

A position names, for each side, where each world stands, and lists the worlds
already taken off the board.  A cell may be land, a belt cell, a corona well or
a den, and the world's height follows from which:

* land or belt   -- the disc sits on the field
* corona well    -- the disc drops 3.00 mm, and its rank counts for nothing
* den            -- the disc steps up onto the star, and the game is over
* taken          -- the disc lies in a socket of its owner's orbit tray
"""

from __future__ import annotations

FILE_INDEX = {name: index for index, name in enumerate("abcdefg")}


def cell(text: str) -> tuple[int, int]:
    """'d1' -> (3, 0)."""
    return FILE_INDEX[text[0]], int(text[1:]) - 1


OPENING = {
    "name": "opening",
    "caption": "The opening position, set up as the source game sets it up.",
    "sol": {"saturn": "a1", "uranus": "g1", "earth": "b2", "mars": "f2",
            "mercury": "a3", "neptune": "c3", "venus": "e3", "jupiter": "g3"},
    "anti": {"saturn": "g9", "uranus": "a9", "earth": "f8", "mars": "b8",
             "mercury": "g7", "neptune": "e7", "venus": "c7", "jupiter": "a7"},
}

MIDGAME = {
    "name": "midgame",
    "caption": ("Mid-game, four worlds already taken. Anti-Sol's Mercury is in "
                "Sol's corona and counts for nothing there; Sol's Mercury is "
                "standing in the asteroid belt, where only it may go."),
    "sol": {"saturn": "a5", "uranus": "g4", "mercury": "c4", "neptune": "d6",
            "venus": "e2", "jupiter": "f7"},
    "anti": {"saturn": "b3", "uranus": "a9", "mercury": "d2", "earth": "d7",
             "neptune": "e8", "jupiter": "a6"},
    "taken_sol": ["earth", "mars"],
    "taken_anti": ["mars", "venus"],
}

ENDGAME = {
    "name": "endgame",
    "caption": ("The game ends. Sol's Neptune is standing on the Anti-Sol star, "
                "one step above the field, and four worlds are already in the "
                "trays."),
    "sol": {"neptune": "d9", "saturn": "g2", "jupiter": "b7", "venus": "d5"},
    "anti": {"saturn": "c3", "mars": "f3"},
    "taken_sol": ["mercury", "mars", "earth", "uranus"],
    "taken_anti": ["uranus", "jupiter", "venus", "neptune", "mercury", "earth"],
}

POSITIONS = {p["name"]: p for p in (OPENING, MIDGAME, ENDGAME)}
