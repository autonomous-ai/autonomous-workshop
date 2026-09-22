# Periastra

Lift the telescope roof to reveal a complete game of English draughts. Two comet streams approach opposite stars; a crowned comet earns its return journey.

## Contents and setup

One board-box, one removable roof, twelve single-tail counters and twelve forked-tail counters. Place the board between the two players with a recessed square at each near-left corner. Set each side's twelve counters on the recessed squares of its nearest three rows, plain face upwards. Randomly assign sides; single-tail starts. Flip a counter to expose its orbit-crown when it becomes a king.

Lift the roof straight up; the illustration holds it 100 mm above the base. It is loose and must be held by a person, then set aside for play. To store the complete initial position, replace the counters and lower the roof onto the four corner seats. The rim has an intentional ventilation gap. Carry the base and roof separately or support both; there is no latch.

## Printing and files

Print all 26 files in `parts/`, one copy each. Base and roof use their broad flat undersides; counters print plain face down, recessed crown up. The files are already oriented this way. A 220 × 220 mm bed and 0.4 mm nozzle are the verified digital envelope. Choose filament and slicer settings suitable for your printer; digital checks do not establish physical fit or strength. The large solid-modeled roof and base can use slicer infill.

`assembled.step` is the complete stored arrangement. `assembled.step.json` records named placements and colours. The `cad/` directory contains editable parametric sources and verification evidence. Base: 190 × 190 × 24 mm. Board: 176 mm, eight 22 mm cells per side. Counters: 16 mm maximum planar extent, 7 mm high. Roof clearance: nominal 0.8 mm per side. Roof underside: 10 mm above the smooth board floor.

No physical print, handling trial or human playtest has occurred. Small loose counters require suitable supervision and should be kept away from children who mouth objects.

## Rules and astronomical meaning


Authority: [WCDF 2012 section1](https://wcdf.net/rules/rules_of_checkers_english.pdf). The following is an original compact mechanical specification, not copied rulebook prose. Geometry encodes identical states and legal actions. The Wish explicitly substitutes miniature 22 mm cells and reversible16×7 counters for tournament-sized cylindrical equipment and stacking to crown. Thus gameplay is unchanged, but this is not WCDF tournament equipment and cannot be described as literal compliance with every equipment clause. No opening ballots or new scoring.

- Two opponents; one8×8 board;32 playable squares;12 independently movable pieces each. Randomly assign sides for the first game; alternate sides on later games. Single-tail/dark corresponds to Red and starts every game. Public position, ownership and man/king status; no hidden game information. A fair random side assignment can use the traditional closed-hand choice with one counter of each side; no extra randomizer part required.
- Each side fills its nearest three playable rows. Moves alternate. A man steps one vacant forward diagonal cell; kings can step one vacant diagonal in either Y direction. No flying kings.
- A capture jumps one adjacent opponent into the empty square immediately beyond. Men capture forward; kings either way. Available capture is mandatory. When routes differ, choose any route, not necessarily the longest. Continue the same piece's chain until no further legal capture exists; never jump the same victim twice. Remove chain victims at the end of the chain. Arrival on the far row crowns and immediately ends that turn, including during a capture; no continuation as a new king that turn.
- Declare an adjustment before touching either side's pieces to straighten them. Otherwise, touching on your turn binds you to that piece; touching an unplayable piece is an offence. Once any part of a playable piece crosses a corner of its origin square, complete its move in that direction.
- First illegal move: caution and recall; another offence in that game: forfeit. This includes skipped or incomplete capture, wrong-square moves, backward man moves, wrong removal, added own pieces, uncrowned continuation through the far row, wrong turn and touching an unplayable piece. An opponent's subsequent move condones the illegal move. Accidental displacement is restored without penalty. Refusal to follow rules forfeits.
- Win by leaving the opponent with no legal move, through capture or blocking; also by opponent resignation, forfeiture, or failure of a time control when clocks are in use. No clock is required for this unclocked set; no new time control is invented.
- Draw by agreement, or by demonstrating to the referee that the next move would produce the position a third time, or the specified condition that each player's own previous40 moves contain neither advancement of an uncrowned man nor removal of any piece. Do not replace the prospective third-position condition with automatic third repetition, and do not replace40 moves per player with40 plies. No score, points or tie-breaker is added.

The zero-difference claim applies to legal play, state transitions, information and result. Administrative conditions remain as above. Equipment expression substitutions are explicitly disclosed, not hidden as a rules change.

## Necessary astronomical mapping

The two low star half-discs lie beyond opposing approach edges. Uncrowned pieces represent inbound comet streams approaching the other star; their obligatory forward direction establishes approach. Crossing the far row is closest passage and the flipped orbit-crown marks return travel, explaining newly bidirectional kings. Adjacent capture is the game's encounter/ejection metaphor; chained captures are successive encounters, retaining compulsory interaction and choices. Blockade or elimination leaves one stream dominant; a draw leaves neither dominant. The checkerboard's unchanged diagonal topology is a discrete encounter chart, not simulated orbital mechanics. Single and bifurcated tails identify streams; all four ordinary role/state combinations remain visually distinct. This spatial metaphor does not assert that real comets follow squares, reverse freely after periastron, or that gravity forces all represented captures.

