# Periastra Syzygy

Lift the observatory dome to reveal a complete game of English draughts. The two sides are the Sun and the Moon, the two bodies an observatory is built to watch; the counter's king step is the dome's rotation ring at counter scale.

## Contents and setup

One board-box, one removable domed roof, twelve Sun counters and twelve Moon counters. Place the board between the two players with a recessed square at each near-left corner. Set each side's twelve counters on the recessed squares of its nearest three rows, man face upwards. Randomly assign sides; the Sun side starts. Flip a counter to expose its rebated king face when it becomes a king.

Every counter is a plain 16 mm disc. The Sun counters are terracotta and carry a ball with eight separate rays; the Moon counters are cream and carry one bold crescent. The same mark is sunk into both faces of a counter, so a piece's owner reads whichever way up it lies. Rank is the edge: the man face is flat and plain, and the king face carries a 2 mm wide step round the edge leaving a raised 12 mm plateau.

Lift the roof straight up; the illustration holds it 100 mm above the base. It is loose and must be held by a person, then set aside for play. To store the complete initial position, replace the counters and lower the roof onto the four corner seats. The rim has an intentional ventilation gap. Carry the base and roof separately or support both; there is no latch.

## Printing and files

Print all 26 files in `parts/`, one copy each. Base and roof use their broad flat undersides — the roof prints plate down with the dome apex up. Counters print flat with the plain man face on the bed, so the annular king rebate and its plateau print upwards. The files are already oriented this way. A 220 × 220 mm bed and 0.4 mm nozzle are the verified digital envelope. Choose filament and slicer settings suitable for your printer; digital checks do not establish physical fit or strength. The large solid-modeled roof and base can use slicer infill.

`assembled.step` is the complete stored arrangement. `assembled.step.json` records named placements and colours. The `cad/` directory contains editable parametric sources and verification evidence. Base: 190 × 190 × 24 mm. Board: 176 mm, eight 22 mm cells per side. Counters: 16 mm diameter, 7 mm high. Roof: 182.4 mm square plate, 180 mm drum rising to a dome whose apex is 78 mm above the base floor, with a 30 mm shutter slit and a telescope on a fork. Roof clearance: nominal 0.8 mm per side. Roof underside: 10 mm above the smooth board floor.

No physical print, handling trial or human playtest has occurred. Small loose counters require suitable supervision and should be kept away from children who mouth objects.

## Limitations

- The undisturbed band between the sun's ball and its rays is 1.0 mm, and the raised gaps between adjacent rays are about 0.6 mm. Both are below the 3 mm minimum feature width the rest of this set observes. They are shallow 1.2 mm relief on a solid disc, not standing walls, so they are not a fragility risk; at a 0.4 mm nozzle they will print soft and may lose definition. At 16 mm there is no arrangement that keeps a dominant central ball, gives eight separate rays and holds a wider band.
- The crescent's horns end in flat square tips 2.17 mm across, a little under the 3.0 mm the correction asked for. A 3.0 mm tip cannot coexist with a crescent of this waist: truncating far enough to reach it removes the concave bite and the mark stops reading as a moon. Neither horn is pointed and neither is a sliver.
- Motion is unverified. No motion sweep, animation or independent motion review was run for this revision, so nothing here establishes working motion, assemblability or physical fit. The roof is a loose lid; lifting it is a handling action, not a verified mechanism.
- Playtest was not run.

## Rules and astronomical meaning

Authority: [WCDF 2012 section1](https://wcdf.net/rules/rules_of_checkers_english.pdf). The following is an original compact mechanical specification, not copied rulebook prose. Geometry encodes identical states and legal actions. This revision substitutes miniature 22 mm cells and reversible16×7 counters for tournament-sized cylindrical equipment and stacking to crown. Thus gameplay is unchanged, but this is not WCDF tournament equipment and cannot be described as literal compliance with every equipment clause. No opening ballots or new scoring.

- Two opponents; one8×8 board;32 playable squares;12 independently movable pieces each. Randomly assign sides for the first game; alternate sides on later games. Sun/dark corresponds to Red and starts every game. Public position, ownership and man/king status; no hidden game information. A fair random side assignment can use the traditional closed-hand choice with one counter of each side; no extra randomizer part required.
- Each side fills its nearest three playable rows. Moves alternate. A man steps one vacant forward diagonal cell; kings can step one vacant diagonal in either Y direction. No flying kings.
- A capture jumps one adjacent opponent into the empty square immediately beyond. Men capture forward; kings either way. Available capture is mandatory. When routes differ, choose any route, not necessarily the longest. Continue the same piece's chain until no further legal capture exists; never jump the same victim twice. Remove chain victims at the end of the chain. Arrival on the far row crowns and immediately ends that turn, including during a capture; no continuation as a new king that turn.
- Declare an adjustment before touching either side's pieces to straighten them. Otherwise, touching on your turn binds you to that piece; touching an unplayable piece is an offence. Once any part of a playable piece crosses a corner of its origin square, complete its move in that direction.
- First illegal move: caution and recall; another offence in that game: forfeit. This includes skipped or incomplete capture, wrong-square moves, backward man moves, wrong removal, added own pieces, uncrowned continuation through the far row, wrong turn and touching an unplayable piece. An opponent's subsequent move condones the illegal move. Accidental displacement is restored without penalty. Refusal to follow rules forfeits.
- Win by leaving the opponent with no legal move, through capture or blocking; also by opponent resignation, forfeiture, or failure of a time control when clocks are in use. No clock is required for this unclocked set; no new time control is invented.
- Draw by agreement, or by demonstrating to the referee that the next move would produce the position a third time, or the specified condition that each player's own previous40 moves contain neither advancement of an uncrowned man nor removal of any piece. Do not replace the prospective third-position condition with automatic third repetition, and do not replace40 moves per player with40 plies. No score, points or tie-breaker is added.

The zero-difference claim applies to legal play, state transitions, information and result. Administrative conditions remain as above. Equipment expression substitutions are explicitly disclosed, not hidden as a rules change.

## Necessary astronomical mapping

An observatory tracks two bodies above all others: the Sun and the Moon. A syzygy is the moment they line up. The two low star half-discs lie beyond opposing approach edges, and the two sides approach each other across the board; each side's obligatory forward direction establishes that approach. Crossing the far row is the alignment, and the flipped king face marks it: the rebated step round the counter's edge is the dome's own rotation ring at counter scale, which is what ties the pieces to the lid. Adjacent capture is the game's encounter and occultation metaphor; chained captures are successive encounters, retaining compulsory interaction and choices. Blockade or elimination leaves one body in the sky; a draw leaves neither dominant. The checkerboard's unchanged diagonal topology is a discrete encounter chart, not simulated orbital mechanics. The sun mark and the crescent mark identify the two sides; all four ordinary role/state combinations remain visually distinct, and because the same mark is sunk into both faces, ownership never depends on which way up a piece lies. This spatial metaphor does not assert that the real Sun and Moon move on squares, that they reverse after alignment, or that gravity forces all represented captures.
