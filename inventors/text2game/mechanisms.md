# Mechanism vocabulary and compatibility

The ids below are the ONLY mechanisms MECHANISM LOCK may choose from. They are
the "Moves" section of `taste_boardgame.md` given stable names so a machine can
check the combination. This is deliberately NOT a BoardGameGeek taxonomy:
names like "worker placement" or "area movement" describe a rules abstraction,
and `taste_boardgame.md` bans reaching for those. Every id here is a PHYSICAL
thing a printed part does.

## Vocabulary

| id | what the part physically does |
|---|---|
| `blind_bag_draw` | hand goes into an opaque hopper, feels an engraved face before seeing it |
| `opaque_sleeve` | tile hidden in a sleeve; only its owner slides it out |
| `rotating_drum` | barrel presents exactly one face at a time |
| `gravity_magazine` | dispenses exactly one piece, order unknown |
| `peephole_screen` | screen with a hole only one seat can see through |
| `marble_tower` | gravity sorts pieces into unpredictable outlets |
| `printed_die` | polyhedral or asymmetric die, spinner, or top |
| `pachinko_drop` | piece falls through printed pegs |
| `tipping_platform` | platform tips, the spill pattern IS the roll |
| `snap_off_tab` | tab breaks off, never restorable |
| `bolted_module` | module clipped or dovetailed on and left there |
| `ratchet_dial` | one-way pawl, one click per campaign |
| `sealed_compartment` | opened once, the lid is destroyed opening it |
| `socket_swap` | piece swaps into a socket and changes a rule forever |
| `physical_timer` | sand, wound spring, or slow marble run |
| `shared_push_track` | one player advancing physically pushes another back |
| `modular_tiles` | board tiles clip together (required anyway under 160mm) |
| `bistable_snap` | two stable states, flipping one flips a rule |
| `balance_lever` | platform tilts as resources accumulate |
| `stack_height` | the stack height IS the score and the risk |
| `asymmetric_module` | a player power as a physical module keyed to a personal board |
| `shape_change` | a piece folds, telescopes or nests between plays |
| `box_as_component` | the box or its insert is played with |
| `hand_off` | ONE piece physically moves from player to player; only whoever holds it may take the action it carries |
| `blocking_claim` | a piece occupies a printed slot others need, and denies it while it sits there |
| `physical_bid` | every player commits a choice on a dial or face-down token at once, and all are revealed together |
| `cascade_sort` | at game end the pieces release and fall into sorted stacks — teardown plays itself |
| `print_in_place_flip` | a piece flips state (owner, colour, face) without ever leaving the board |
| `roll_up_board` | the board rolls, folds or snaps around its own pieces and becomes the box |
| `spring_launcher` | a printed spring or banded arm fires a piece into the board state |
| `predictable_teeter` | ridged rocker: the platform wobbles, but along ONE printed axis a player can read |

## Permanent change runs BOTH ways

The permanent-change group is not one thing, and reading it as one is why every
game this pipeline has picked is a story of loss: a submarine welded shut, a
capacity tray fragmenting, a fighter scarred and retired. That tone was never
designed. It fell out of a vocabulary whose destructive ids are the easiest to
describe, and out of nobody ever writing this table down.

| direction | ids | what the campaign feels like |
|---|---|---|
| SUBTRACTION | `snap_off_tab`, `sealed_compartment` | the box gets smaller; you spend what you cannot get back |
| ACCRETION | `bolted_module`, `socket_swap`, `asymmetric_module` | the box gets bigger; what you build stays built |
| RATCHET | `ratchet_dial`, `bistable_snap`, `shape_change` | neither - the state moves one way and the game changes with it |

All three satisfy `mech-no-legacy`. Choose the direction on purpose: a campaign
a table BUILDS across six nights is the same mechanism class as one that eats
itself, and a completely different Friday night. Subtraction is the default
every model reaches for, so it is the one that has to argue for itself.

## REINFORCE - pairs that compound

| a | b | why |
|---|---|---|
| `ratchet_dial` | `physical_timer` | two clocks running at different rates; the pawl makes the pressure irreversible |
| `snap_off_tab` | `stack_height` | the resource you spend permanently is the same one you are scored on |
| `gravity_magazine` | `peephole_screen` | unknown order plus asymmetric sight = a real information market |
| `shared_push_track` | `balance_lever` | one physical state carries both the race and the load |
| `socket_swap` | `asymmetric_module` | the legacy change and the player identity are the same object |
| `modular_tiles` | `shape_change` | the board and the piece reconfigure on the same axis |
| `bistable_snap` | `shared_push_track` | a flip that reverses who is pushing whom |
| `marble_tower` | `stack_height` | the randomiser and the score share one physical column |
| `hand_off` | `physical_timer` | the object you must pass is also the clock: holding it costs everyone |
| `hand_off` | `snap_off_tab` | what one player spends permanently is spent while the whole table waits on them |
| `blocking_claim` | `asymmetric_module` | the slot one player must have is the slot another player's power wants |
| `spring_launcher` | `blocking_claim` | the shot you land occupies the slot the next player needed — aim IS denial |
| `predictable_teeter` | `stack_height` | the tilt telegraphs exactly the risk the height is scoring |
| `roll_up_board` | `modular_tiles` | the board that folds is the board that clips — one storage story, no box needed |
| `cascade_sort` | `gravity_magazine` | the pieces that fall sorted are the pieces the magazine deals next game |

## COLLIDE - pairs that must NOT both be chosen

| a | b | why |
|---|---|---|
| `blind_bag_draw` | `gravity_magazine` | same job twice: unknown draw order. One is redundant. |
| `printed_die` | `pachinko_drop` | two independent randomisers dilute each other; neither reads as the game |
| `marble_tower` | `pachinko_drop` | both are gravity randomisers with the same feel |
| `blind_bag_draw` | `opaque_sleeve` | two hidden-information channels, no reason to hold both |
| `rotating_drum` | `gravity_magazine` | drum already sequences one face at a time |
| `physical_timer` | `marble_tower` | a slow marble run IS a timer; pick which job it does |
| `sealed_compartment` | `bolted_module` | both are one-shot legacy adds; two ceremonies compete |
| `balance_lever` | `tipping_platform` | the same tilt read two ways confuses which one matters |
| `blocking_claim` | `shared_push_track` | two ways to deny a position; the table cannot tell which one is the game |
| `predictable_teeter` | `balance_lever` | the same readable tilt doing two jobs; the table cannot tell which one scores |
| `predictable_teeter` | `tipping_platform` | one tilt is a skill read, the other a randomiser — together neither reads |
| `cascade_sort` | `marble_tower` | two gravity columns with the same feel; one is redundant |
| `print_in_place_flip` | `bistable_snap` | two flip ceremonies — a piece flip and a rule flip — and the table conflates them |

## Rule for MECHANISM LOCK

Choose 2-3 ids. Zero COLLIDE pairs allowed. State in one sentence how the
chosen ids interact; if you cannot, they do not belong in the same box.

ONE group is mandatory for every game, the second only for the legacy lane:

- **interaction** (`hand_off`, `blocking_claim`, `physical_bid`,
  `shared_push_track`, `opaque_sleeve`, `peephole_screen`) - ALWAYS. What makes
  it a game for a TABLE rather than several people doing solitaire beside each
  other.
- **permanent-change** (`snap_off_tab`, `bolted_module`, `ratchet_dial`,
  `sealed_compartment`, `socket_swap`, `bistable_snap`, `shape_change`) - only
  when the game is a LEGACY game. It is what makes a campaign worth printing
  rather than buying, and it was mandatory for every lane until 2026-08-20.
  That is why all three games this pipeline had produced were campaigns: a
  co-op and a family game were each forced to carry a layer that persists
  between sessions, and that layer is the largest single block of rules a
  player has to learn. A non-legacy game spending its second id on another
  interaction or on a tension mechanism is a BETTER two-id lock, not a
  weaker one.

The second group was added 2026-08-19 after a measurement. Of the 23 ids here,
19 carried no player-to-player content at all, so a lock that simply picked the
two strongest ids picked two solo ones: keep-the-light-relay's rebuild chose
`gravity_magazine` + `snap_off_tab`, dropped the lamp relay that was the whole
reason four people sat down, and its design evaluation fell from social 9 to 3.
The relay could not even be named - nothing in this table expressed "one object
passed between players" until `hand_off` was added.

With both groups mandatory, a two-id game is exactly one permanent-change and
one interaction. A third id is for a randomiser or a physical-state mechanism
and must earn its place: three is the ceiling, not the target.

## SYMPTOM - the failure vocabulary

The ids below are the ONLY names the critic, the referee and `harvest.py` may
use for a failure. Until 2026-08-20 this vocabulary existed as seven bullets
hard-coded in `prompts.critic()`, with no ids, no scope and no memory: every
run rediscovered the same failures from scratch and threw them away at the end.
Four designs produced 28 critic findings before anything counted them.

A symptom is what someone would SEE, not a judgement about whether the game is
good. The third column is who can see it, and it decides where the check
belongs: `consistency` symptoms are arithmetic and must move into
`consistency.py` where they stop costing tokens and stop being negotiable;
`referee` symptoms are measurable from the turn logs `referee.md` already
writes; `table` symptoms need four people and are the only ones that have to
wait.

### PLAY - the game fails as a game

| id | what it looks like | seen by |
|---|---|---|
| `alpha_solve` | one confident player solves the co-op out loud for everyone | table |
| `silent_calc` | the numbers make the choice automatic, so every seat computes the same answer and nobody decides anything | table |
| `dominant_action` | one action is never wrong to take | referee |
| `trap_option` | an option no informed player would ever take | referee |
| `runaway_leader` | a lead feeds itself and nothing pushes back | referee |
| `spiral` | one loss makes the next loss likelier, with no floor | referee |
| `decided_early` | the result is fixed before the last round or the last session | referee |
| `idle_player` | a seat has no meaningful move left and is still at the table | referee |
| `seat_advantage` | turn order decides the last scoring moment | referee |
| `count_break` | the design works at one player count and fails at another | referee |
| `legacy_flattens` | the permanent change makes later sessions poorer for everyone | table |
| `legacy_seat_penalty` | the permanent change makes the next play strictly worse for one seat | table |
| `kingmaker` | a player who cannot win chooses who does | table |
| `teach_overrun` | the rules cannot be taught inside the TEACH floor | table |
| `unsatisfying_action` | the signature move lands and the table feels nothing — no cascade, no snap, no reveal | table |
| `fiddly_reset` | packing up or resetting for the next round takes longer than playing one | table |
| `physics_untested` | a balance question the document cannot settle because the OBJECT settles it - mass, spill, wobble - and nobody has thrown it yet | table |
| `handling_wipe` | a required handling motion (sweep, lift, reset) moves or destroys game state mid-game | table |

### DOCUMENT - the rules fail before anyone plays

| id | what it looks like | seen by |
|---|---|---|
| `contradiction` | two rules answer the same situation differently | referee |
| `dead_state` | a legal position from which no legal move exists | referee |
| `unreachable` | a win condition that cannot be reached from setup | referee |
| `illegal_turn` | a turn that cannot be legally ended as written | referee |
| `missing_info` | a rule needs information no listed component can carry | referee |
| `duplicate_state` | two components display the same state | consistency |
| `dead_range` | a track or counter with values no legal play can reach | consistency |
| `decoration` | removing the component costs the game no decision | consistency |
| `homeless_part` | a component with no printed place to live between games | consistency |
| `undocumented_build` | a part needs an external item or assembly step no document specifies | consistency |

`duplicate_state` is not `decoration` and that is why it kept getting through:
the duplicate part IS named in `## Turn structure`, so the `decoration` check
passes it. Two designs shipped one - a fragment ratchet beside the wedges that
already count the damage, a rank track totalling a number the harbour headcount
already shows - and a third shipped a 0-120 track with 54 spaces no legal play
can reach.

## MITIGATE - a fix, and what it costs

REINFORCE and COLLIDE say how mechanisms sit beside each other. Neither says
what happens when you FIX something, and the price of a fix is the part that
lives in a designer's head and never gets written down.

Rule: **a fix with an empty `costs` cell is not accepted.** Write the cost, or
write `untested` and let the next design find out. `duplicate_state` is the
only free fix in this table so far, and free fixes are the exception.

| symptom | the fix | what it costs | evidence |
|---|---|---|---|
| `alpha_solve` | a speech restriction during the turn | `silent_calc`; and it is unenforceable between turns | 2 designs, critic rejected it both times |
| `alpha_solve` | asymmetric sight (`peephole_screen`, `opaque_sleeve`) | MEASURED on the-rounds 2026-08-20: `social` 2->8, and it cost `teach` 8->5 in one round (floor is 7), one extra printed design, and a referee regression from CLEAN to three ILLEGAL TURNs - the private-channel rules could not resolve turn 1 | 1 design, priced |
| `alpha_solve` | simultaneous commit (`physical_bid`) | `silent_calc`, if every seat sees the same board | 1 design - the critic found the cost |
| `silent_calc` | give seats different information or different powers (`asymmetric_module`) | teach time, and a balance tail nobody has measured | untested |
| `dominant_action` | raise the cost of the dominant action | `trap_option` if raised too far - and it was, on the-rounds 2026-08-20: round 2 fixed `silent_calc` and shipped a new `trap_option` high in the same revision | 1 design, confirmed |
| `decided_early` | end the campaign when the win condition is met | the box has fewer nights in it | 3 designs, 5 findings - the most common failure this pipeline makes, all unfixed |
| `spiral` | a recovery floor on the ratchet | drains the permanence stake, which is the thing being sold | 1 design, unfixed |
| `spiral` | ACCRETION or RATCHET instead of SUBTRACTION | the campaign stops being a story of loss - usually the point | the direction table above |
| `runaway_leader` | catch-up pressure | anticlimax; the last round stops mattering | untested |
| `seat_advantage` | rotate or compensate the last activation | one more rule to teach | 2 designs, unfixed |
| `idle_player` | a floor that always leaves one legal move | can make losing painless, which is its own failure | 1 design |
| `legacy_flattens` | make the permanent change additive, not subtractive | none known | untested |
| `duplicate_state` | delete one of the two displays | none - this one is free | 2 designs; a third shipped a `dead_range` track instead |
| `decoration` | delete the component | one fewer part against the PARTS dial | already enforced in `consistency.py` |
| `unsatisfying_action` | give the move a visible physical consequence (`cascade_sort`, a snap, a topple) | a mechanism id and the parts to carry it, against the PARTS budget | untested |
| `fiddly_reset` | make teardown the game's own motion (`cascade_sort`, `roll_up_board`) | constrains piece geometry to what can fall or fold into place | untested |
| `homeless_part` | nest it inside the signature part or the board | the host part grows and may cross the plate budget | untested |
| `dominant_action` (physical game) | let the OBJECT price it - heavier load spills more, taller stack wobbles more - and file `physics_untested` for the table | nothing on paper; a print and a night to find out | dead-stop 2026-08-22: pricing it with rules instead cost 3 subsystems and replayability -2 |
| `physics_untested` | throw it: a print, four people, `table_notes.md` | a print | the only fix that is not a guess |
