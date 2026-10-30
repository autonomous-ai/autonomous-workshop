---
title: Printed mechanical puzzles
tags: [puzzle, puzzle-box, maze, sliding-puzzle, twisty-puzzle, clearance, sequence, state-graph]
aliases: [puzzle box, secret box, trick box, himitsu bako, secret opening box, sequential discovery puzzle, hidden latch, gravity pin, spin lock, magnet lock, maze puzzle, cylinder maze, maze gift box, ball maze, pin in a track, nub, sliding puzzle, 15 puzzle, fifteen puzzle, sliding tile, captive tiles, twisty puzzle, rubiks cube, 3x3 cube, speedcube, cube core, corner cutting, cube tension, disentanglement puzzle, wire puzzle, packing puzzle, gear puzzle, gear cube]
sources:
  - https://www.printables.com/model/100801-the-heist-puzzle-box (0.1 mm non-sliding, 0.2 mm sliding, verified at 100 % and 150 %, 0.4 nozzle, 0.2 layer)
  - https://printables.com/model/782997-sliding-puzzle-4x4-print-in-place (print-in-place tiles offered at 0.15, 0.2, 0.3 mm gap; one drop of silicone grease)
  - "https://forum.creality.com/t/tuning-in-tollerances/13111 (that puzzle: 0.15 and 0.2 locked solid, 0.3 mostly freed)"
  - https://www.printables.com/model/71486-new-captive-sliding-tile-puzzle-100-print-in-place (captive tiles; scale up 10-20 % when they fuse)
  - "https://web.archive.org/web/2020/https://www.sculpteo.com/blog/2016/04/06/3d-printing-and-twisty-puzzles/ (0.2 mm sliding, 0.5 mm hovering, wear version 0/0.4; no internal angle under 90°; 2-3 mm internal fillets; centres on core, edges between two centres, corners between three edges)"
  - "https://codeberg.org/RevK/PuzzleBox (puzzlebox.c defaults: 3 mm maze step, 2 mm depth, 0.4 mm X/Y clearance, nub +0.1 radial +0.2 height, 0.7 mm park ridge, 1.2 mm wall, two nubs; resin halves clearances)"
  - http://www.revk.uk/2017/06/amazing.html (long dead ends, staging ring with one correct exit, maze repeated per nub)
  - https://en.wikipedia.org/wiki/15_puzzle (half of arrangements unsolvable; permutation plus blank taxicab parity; 80 single-tile, 43 multi-tile moves)
  - https://www.jaapsch.net/puzzles/fifteen.htm (groove arrangement since Kinsey 1878; 14-15 swap impossible; identical tiles change the check)
  - https://en.wikipedia.org/wiki/Sliding_puzzle (mortise-and-tenon key channels along tile edges)
  - https://en.wikipedia.org/wiki/Rubik%27s_Cube (core cross, spring per centre, screw or rivet, clones use a clip; 5.6 cm; 1/12 of reassemblies solvable; 20 moves)
  - https://www.speedcube.us/blogs/speedcubing_news_and_advice/64469763-september-2015-speedcube-characteristics (57 mm typical; corner cutting, popping, lockups)
  - https://www.printables.com/model/1569688 (M3 x 15-20 mm screws, about 5 mm springs; sand every piece, grease; 0.14-0.16 mm layers)
  - https://fab.cba.mit.edu/classes/863.22/Harvard/people/Cedric-Pascal/projects/week_4_rubiks_cube.html (most stable with every piece pressed onto the centre sphere)
  - https://www.jaapsch.net/puzzles/cube3.htm (silicone spray and oil; no WD-40 or petroleum jelly)
  - https://www.jaapsch.net/puzzles/gearcube.htm (a half face turn drives the middle slice a quarter turn; anti-slice moves only)
  - https://patents.google.com/patent/US5411261 (gravity pin transfers only with grooves aligned and box inverted; fortuitous orientation does not open it)
  - https://patents.google.com/patent/US5944311 (offset-mass pendulums gate rods in a fixed orientation sequence; no jarring or force needed)
  - "https://www.ericweinhoffer.com/work/spinlock-puck/ (five pin sets: gravity locks it in every orientation, shaking only rattles, spinning flings the pins out)"
  - https://www.kjmagnetics.com/proddetail.asp?prod=D42-N52 (6.35 x 3.17 mm N52 disc, 1.29 kg on thick steel at contact)
  - https://www.vanishingincmagic.co.uk/puzzles-and-brainteasers/articles/what-is-a-japanese-puzzle-box/ (4-66 steps typical, record 1536; steps do not measure difficulty)
  - "https://puzzleworld.org/PuzzlingWorld/introduction.htm (Coffin - the idea, not fiendish difficulty; close tolerances)"
  - https://en.wikipedia.org/wiki/Disentanglement_puzzle (wire-and-string, wire, plate-and-ring families)
  - skills/cad/scripts/cadfits.py (snug 0.10, slip 0.20, free 0.40 per side; print_in_place_gap sliding 0.30 XY, Z = XY + layer)
related: [interlocking-joinery-for-prints, fit-derivation, fdm-hole-accuracy, print-in-place-mechanisms, tolerance-stack-up, mechanism-verification, latches-detents-and-ratchets, magnets-and-strap-slots, friction-wear-and-lubricants, linear-guides-and-slides, gears, springs, toy-safety-constraints, noise-and-vibration]
updated: 2026-10-10
---

# Printed mechanical puzzles

A puzzle is a mechanism whose free and blocked moves *are* the product: the
solve path runs at every state, every other move is blocked, and neither is
readable from outside. Clearances and invariants for boxes, mazes, sliding
tiles, twisty cubes and smaller families; burrs and interlocking nodes are on
[[interlocking-joinery-for-prints#locking-nodes-three-way-corners-burrs-and-twist-locks]].

## Clearance between puzzle pieces

Per side, derived through `cadfits` ([[fit-derivation]]), never typed twice:

| contact | per side | evidence |
|---|---|---|
| assembled, not meant to move | 0.10 (`snug`) | 0.1 mm in a published printed box |
| separate pieces that slide or turn | 0.20 (`slip`) | 0.2 mm in the same box and in a print bureau's twisty-puzzle guide |
| pieces that must never touch (hover) | 0.4-0.5 (`free`) | 0.5 mm twisty, 0.4 mm X/Y in a maze generator |
| sliding pieces printed in place | ≥ 0.30 (`print_in_place_gap("sliding")`, Z gap one layer more) | 0.15 and 0.2 locked solid, 0.3 mostly freed |

- **Clearance is absolute, not proportional.** Scaling a model in the slicer
  scales its gaps: published advice to scale a fused captive puzzle up
  10-20 % is a gap increase in disguise. Rebuild from the parameter block.
- **Shrink the piece, not the cell.** Many identical pieces share one offset
  part; sloped flanks (dovetails, maze grooves) take it normal to the flank.
- **Slack adds across a row.** `n` pieces in a line leave `2 c n` of play
  ([[tolerance-stack-up]]): a 4-tile row at 0.2 mm has 1.6 mm, enough to cock
  a tile or pull a tongue out of its groove.
- Compensate hole shrink separately ([[fdm-hole-accuracy]]); chamfer the bed
  edge of in-place gaps ([[print-in-place-mechanisms#the-gap-is-per-face-and-per-direction]]).
  0.14-0.16 mm layers slide smoother than 0.2; silicone grease frees the rest.

## Puzzle boxes: each move unblocks the next

A sequential box is a chain of blocks: move *k* is stopped by a feature that
move *k-1* takes away, so the order is enforced by geometry, not by
instruction. Japanese boxes run 4-66 steps (record 1536); step count does not
measure difficulty. A panel slides because its neighbour's tongue has left
its groove; draw the chain as a list before drawing panels.

Hidden locks, and what each needs:

- **Gravity pin.** A pin in a bore crosses the sliding joint; inverted, it
  drops clear. Alone it opens to any tumble. Pair it with a second
  manipulation done *in that orientation* (rotate a plate until two grooves
  align, then invert): the published form states that a fortuitous
  orientation does not open it.
- **Pendulum.** An offset mass hangs to one angle; its slot passes a rod only
  while the box is held there, and each pendulum frees the next rod.
- **Spin lock.** Pins in several directions, so gravity drops one into its
  pocket in *every* orientation: shaking rattles, only spinning frees all.
- **Magnet through a wall.** An external magnet drags a steel latch inside.
  Pull falls steeply with gap (a 6.35 × 3.2 mm N52 disc holds 1.29 kg at
  contact on thick steel), so keep the skin to the thinnest wall the print
  allows, guide the latch, and return it by gravity or a spring
  ([[latches-detents-and-ratchets#magnetic-catches]], [[magnets-and-strap-slots]]).
- **Dial or disc.** A notched disc passes a pin at one angle. Give every
  position an identical detent, or the right one is felt.

## Not readable, not shakeable, not forceable

- **Seams read.** Every moving joint shows a `2c` gap and a shadow line. Cut
  matching decoy seams on fixed panels so the moving ones do not stand out.
- **Sound reads.** A loose pin or ball rattles and announces a gravity step
  ([[noise-and-vibration#rattles-and-panel-buzz]]). Either accept it as the
  clue or shorten its travel.
- **Friction defeats force.** A pin loaded sideways by the panel it blocks
  cannot fall: friction `μF` beats its weight `m g` once `F > m g / μ`
  (a 3 × 10 mm steel pin weighs 0.55 g, so about 18 mN at μ = 0.3). Pushing
  the panel keeps the box locked; the solver must let go first. Use it.
- **Forcing breaks stops.** Put every stop face in the layer plane and size it
  for a hand pull; the 67 N toy tension test is the floor
  ([[toy-safety-constraints#use-and-abuse-tests-what-breaks-off-means]]). The
  intended solution never needs force: a step that does teaches the solver to
  force every other step.
- **Magnets read too.** Any strong magnet finds a steel latch from outside and
  can drive it; hide the latch path or make the magnet the provided tool.

## Verify a sequence as a state graph

List states (each a pose of every mobile piece) and, per state, every move of
every piece. The solve path's moves are `clear`; every other move is
`blocked`. That is one motion condition per (state, move): an
`assembly_sequence` for the path, and blocked linear or rotary sweeps from
each state for the rest ([[mechanism-verification#4-what-the-manifest-must-contain]]).

- Pose pieces by parameter so each state is a real assembly `interfere` clears.
- Gravity, friction and magnets are not rigid-body motion: model a gravity
  pin's two rest poses as two states and record each force-driven step as a
  physical limitation, not a fixed part.
- Check the reverse path: a box that cannot re-lock cannot be gifted twice.
- Keep the graph small (3-8 states): sweep cost grows with movers × obstacles.

## Maze puzzles: pin, track and detent

A cylinder maze is a nub on one tube riding a groove on the other. A
published generator's defaults, all independent parameters:

- maze pitch (track + wall) 3 mm, groove depth 2 mm, wall behind the groove
  1.2 mm, base 1.6 mm;
- groove flanks sloped: 3/4 of the pitch wide at the surface, 1/4 at the
  floor; the nub is the same trapezoid, so it self-centres;
- 0.4 mm X/Y clearance, plus 0.1 mm radial and 0.2 mm height on the nub;
  halved for resin;
- a 0.7 mm park ridge across the track at the closed position, which the nub
  clicks over: the detent that keeps the box shut;
- two nubs 180° apart with the maze repeated for each, so the lid cannot cock.

Rules:

- **Hide the maze**: groove inside the outer sleeve, nub on the inner part.
  An outside maze is a printed solution.
- **Nub engagement > radial play.** Radial engagement minus clearance must
  exceed what the sleeve can flex outward under a pull, or the nub jumps a
  wall. Thin sleeves fail first; keep the wall behind the groove ≥ 3 lines.
- **False paths**: long dead ends beat one-cell stubs; a staging ring with
  many exits and one correct one multiplies the search.
- **Ball mazes**: track = ball + `2·free`; walls at least the ball radius
  tall, or the ball climbs out at a tilt; or close it under a clear lid.

## Sliding-block puzzles: captive tiles and solvable starts

- **Capture every tile at every cell.** Grooves have kept tiles from lifting
  since 1878; commercial sets run key channels along the tile edges, with a
  frame lip over the outer row. A tile beside the gap must stay captured by
  its other three sides, and the tongue must out-reach the row's whole slack
  `2 c n`, because neighbours drift apart by that much.
- **Print the undercut as a 45° V-tongue** on the tile edge and a V-groove in
  its neighbour: both flanks self-support with tiles flat on the bed. Round
  tile corners so a tile enters a slightly misaligned row.
- **Gaps**: separately printed tiles `slip`; printed in place `print_in_place_gap("sliding")`
  (0.30 mm XY) with the bed edge chamfered. Offer the gap as a parameter: printers differ.
- **Solvability.** Half of all arrangements of the 15 puzzle are unsolvable.
  The invariant is the permutation parity of all 16 cells plus the taxicab
  parity of the blank. Ship it solved, or scramble with legal moves only.
  Identical tiles change the check. Longest optimal solution: 80 single-tile
  moves, 43 if a row of tiles moves as one.

## Twisty puzzles: core, shells and tension

- **Anatomy (3×3).** A core of six axles; each centre is screwed or riveted
  to its axle over a spring (clones use a plastic clip). Edges are held under
  two centres, corners under three edges: only the centres touch the core.
- **Surfaces of revolution only.** A face between two pieces that move
  relative to each other during a turn must be a surface of revolution about
  that turn's axis. Edges and corners turn about three axes, so their
  interfaces are the cut planes and spheres centred on the core: that is the
  "sphere shell" every cube shares.
- **Preload holds the shell.** The spring presses each centre toward the core
  and every foot onto its sphere; a cube is most stable with all pieces
  pressed onto the centre sphere. A piece pops when the spring lets a centre
  lift farther than the foot's radial overlap: assert overlap > spring travel
  to solid + clearances.
- **Corner cutting.** No internal angle under 90°, and 2-3 mm fillets on
  internal edges, let a piece ride into a misaligned layer instead of
  locking up.
- **Clearances**: 0.2 mm sliding, 0.5 mm hovering; for heavy use print
  0 / 0.4 and let wear open it.
- **Hardware and finish.** M3 × 15-20 mm screws with about 5 mm springs.
  Sand every piece; lube with silicone, never petroleum jelly (ester oils
  stress-crack PETG: [[friction-wear-and-lubricants]]).
- **Size and solvability.** Hand size is 56-57 mm; print larger when you can,
  because clearances do not scale. Only 1 in 12 random reassemblies is
  solvable: assemble it solved.

## Gear, packing and disentanglement puzzles

- **Gear puzzles.** Geared layers couple turns: in the gear cube a half face
  turn drives the middle slice a quarter turn, so only anti-slice moves exist.
  Every stop must land with the teeth in phase ([[gears#mesh-phasing]]);
  author gears with `stdpart`, never by hand.
- **Packing puzzles.** Piece volume nearly equals the box. Total slack across
  the box, `2 c n`, must stay below the smallest step or notch, or a wrong
  packing closes too.
- **Disentanglement.** Wire-and-string, rigid wire, plate-and-ring. The
  intended passage clears by `free`; every other passage is blocked by more
  than print error plus the ring's flex. A thin printed ring springs over a
  blocker, so check its stiffness ([[springs]]). Size cord holes from the
  cord.

## Difficulty: moves, false leads, the aha

- One idea per puzzle (Coffin): a fiendishly long solve is not a better
  puzzle, and step count is not difficulty. Depths for scale: 15 puzzle ≤ 80
  moves, 3×3 cube ≤ 20; a burr's level counts moves to free the first piece.
- False leads must be plausible and reversible: a dead end that cannot be
  backed out of ends the puzzle.
- End each stage in a discovery (a freed tool, a new seam): a next question.

## Checks

```python
import cadfits
SLIDE = cadfits.slot_for(TILE_W, "slip") - TILE_W          # one source for 2c
assert TILE_PITCH == TILE_W + SLIDE
assert ROW_N * SLIDE <= ROW_SLACK_MAX, "row slack cocks a tile"     # design choice
assert TONGUE_DEPTH - ROW_N * SLIDE >= 2 * LINE_W, "tile leaves its key channel"
assert MAZE_DEPTH - NUB_R_CLEAR > SLEEVE_FLEX_AT_PULL, "nub jumps the wall"
assert BALL_WALL_H >= BALL_D / 2
assert FOOT_OVERLAP > SPRING_TRAVEL_TO_SOLID + 2 * SLIDE, "cube pops"
assert puzzle15_solvable(START), "start position is in the wrong parity"
for state in STATES:                                       # the state graph
    for move in moves_of(state):
        expect = "clear" if move in SOLVE_GRAPH[state] else "blocked"
        conditions.append(sweep(state, move, expect))     # check_motion
```

Sweep each piece of the solved state in all 26 directions: free only along
its first move.
