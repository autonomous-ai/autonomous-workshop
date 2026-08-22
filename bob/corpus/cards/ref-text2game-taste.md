# Board game taste

For DISCOVER and BRIEF — the phases that decide WHAT to make. BUILD and REPAIR
run on lessons.md and must never be handed this file.

Market: adults in the USA and Europe (Germany first). Every component is FDM
printed — no cards, no cardboard, no bought dice. No app, no battery, no screen.
Two commodity exceptions, allowed ONLY when load-bearing (decided 2026-08-22
from the market read in `text2game-ops/findings/`: magnets carry most of the
printed games people actually buy — roll-up boards, pieces that hold their
square, sets that snap into their own box): **neodymium disc magnets** and
**standard rubber bands**. Each use must name an exact spec ("6x3mm N35 disc",
"size #32 band") and the printed pocket or channel that holds it; an external
part without a spec fails the build the way an unbound number fails a rule.
Everything else stays banned — no steel balls, no bought springs, no sand.

## Dials

- **NOVELTY** — 1 = a familiar game with new art, 10 = no published game works
  like this.
- **MECHANISM** — 1 = one static rule, 10 = a system of interacting physical
  parts whose relationship IS the game.
- **ORNAMENT** — 1 = pure play, 10 = heavily decorated components. Never buy
  novelty here: a theme wrapped around a thin loop is still a thin loop.
- **PARTS** — DISTINCT printed designs, not total pieces. 30 identical tokens
  is ONE design. Fewer is better: a part is a rule and a rule is teaching time.
- **TEACH** — 1 = needs a glossary before anyone can start, 10 = fully explained
  in under five minutes and the first turn is played right. This is a floor in
  the panel, not a preference: depth is welcome, a private vocabulary is not.

## Slop — the shapes every model defaults to

Instant reject, however good the theme is. These are what the market is already
drowning in, and a model reaches for them because they are easy to describe.

- Roll-and-move around a track.
- Trivia or quiz with a new subject.
- Party game that is "cards that say funny things" — and it needs cards anyway.
- Zombie / pirate / space / cyberpunk / Cthulhu theme laid over a generic loop.
- Co-op that one confident player solves out loud for everyone (alpha player).
- Legacy that is only stickers, or only "write your name on it".
- Memory / matching pairs.
- Jenga-alike stacking tower with a new shape.
- Worker placement with no blocking and therefore no tension.
- Deck-builder — you cannot print a deck; if the loop needs one, it is the
  wrong game for this pipeline.
- A 3D-printed chess/checkers/go variant whose print is decoration — new
  minis, new theme, same play. (A familiar skeleton IS allowed when the
  printing is load-bearing: a physical mechanism no published edition has —
  pieces that flip in place instead of being captured, a board that rolls up
  around its own magnetic pieces, a set that sorts itself away at game end.
  The novelty this pipeline sells lives in the OBJECT; the test is the
  mechanism, never the theme.)
- Tile-laying that is Carcassonne with different edges.
- "Escape room in a box" that needs paper puzzles or a companion app.
- A game whose selling point is that the pieces look nice.
- Dexterity flicking as the whole game.

Read this list knowing what it costs: it bans nearly every SIMPLE shape a game
can take, so whatever survives is complex by construction. It is a ban on the
tired, not a licence for the baroque — if the only way past it is a game with
four subsystems and its own vocabulary, the answer is a familiar shape used a
way nobody has used it, not a bigger machine.
- Anything where the printed parts are a deluxe upgrade to a game that would
  work fine with paper — the printing must be load-bearing.

If the pitch still makes sense after swapping the theme for any other theme, it
is a skin. Reject it.

## Moves — the vocabulary to reach for

Name the mechanism explicitly in the brief so BUILD models the real thing.

**Hidden information without cards**
- Blind draw from a cloth-free printed bag or hopper — engraved faces, felt by
  hand before they are seen.
- A tile in an opaque printed sleeve; only its owner slides it out.
- Rotating drum or barrel that presents one face at a time.
- Gravity magazine that dispenses exactly one piece, order unknown.
- Screen with a peephole only one seat can use.

**Physical randomness**
- Marble/gravity tower that sorts pieces into unpredictable outlets.
- Printed polyhedral or asymmetric die, spinner, or top.
- Pachinko-style drop with printed pegs.
- Tipping platform whose spill pattern is the roll.

**Permanent change (legacy, no stickers)**
- A tab snapped off a component, never restorable.
- A module bolted, clipped or dovetailed on and left there.
- A ratchet dial advanced one click per campaign, one-way pawl.
- A sealed printed compartment opened once — the lid is destroyed opening it.
- A piece that swaps into a socket and changes a rule for every future game.

**Tension and constraint**
- Physical timer: sand, a wound spring, a slow marble run.
- Shared track where one player advancing pushes another back.
- Interlocking modular board tiles that clip together — required anyway,
  since no printed part exceeds 160x160x180mm.
- A component with two stable states (bistable snap) that flips a rule.
- Balance/lever platform that tilts as resources accumulate.
- Stacked pieces where the stack height IS the score and the risk.
- Asymmetric player powers as physical modules keyed into a personal board.
- A piece whose shape changes between plays (folding, telescoping, nesting).
- The box or its insert used as a component.

**Satisfying motion — the hook is a moving picture**
- A cascade: end-of-game teardown that plays itself and sorts the pieces away.
- Print-in-place pieces that flip state without ever leaving the board.
- A board that rolls, folds or snaps around its own pieces to become the box.
- A printed spring or banded launcher whose shot changes the next player's
  problem — never bare target practice.
- A teeter with printed ridges so the wobble runs along ONE readable axis:
  risk you can see, not luck you endure.

**Self-containing — the game puts itself away**
- Every piece has a printed home: nesting, stacking, a lidded signature part.
- The rules ride ON a part — engraved on a lid or base, or a slot that holds
  the one printed rules plate. A box with homeless pieces or homeless rules
  loses at the shelf, which is where a buyer meets it second.

## Elaborate is the target

Aim for a box that reads as a real piece of engineering: many distinct printed
designs, each visibly doing a job. Density of purposeful components is the
point.

This does NOT relax the slop ban, it sharpens it. Every design must earn its
place: if removing a component costs the game no decision, it was decoration.
Elaborate means more things doing work, never more things to look at.

## One object carries the box

Elaborate is how the game PLAYS. It is not how the game is remembered, and the
two get confused. Monopoly's rules were overtaken decades ago and it still
outsells almost everything, on a little metal dog, a stack of coloured money and
GO — a shopper remembers one object, never a well-balanced set of thirteen.

So name it. Every game must have ONE component that is the thing in the photo,
the thing a player reaches for first, the thing someone describes to a friend
when they cannot remember the title. It carries `"signature": true` in
components.json and it must be a part the turn loop actually runs on: a
signature part the rules never touch is a mascot, and this is not a pipeline
with a budget for mascots. If nothing in a design is memorable on its own, that
is a fact about the design and not about the render.

And name the game. A name is the cheapest thing a product owns and the only one
every buyer meets. `switchyard-slit-scan` and `blind-bone-dig` are real output
from this panel; both describe a mechanism and neither is a thing anyone would
say out loud in a shop.

## The fifteen-second test

The market's verdict is unambiguous: every printed game that actually sells is
sold by a MOVING PICTURE — pieces cascading into sorted stacks, a log splitting
into a chess set, a shot arcing into the one gap left. So before anything is
scored: can the signature part do something visibly satisfying in ONE
continuous fifteen-second shot, with no caption? Name the shot. If the honest
answer is a still life — the box open, the parts laid out — the design has a
face for a catalogue and none for a table, and `desire` is scored accordingly.

## The two targets, restated

1. **Not for sale anywhere** — BoardGameGeek, Kickstarter, Gamefound, Amazon,
   Etsy, Printables, MakerWorld, Thingiverse.
2. **The OBJECT never existed** — not a reskin, not "X with Y theme". The
   ruleset may descend from a familiar skeleton when the printed mechanism is
   the thing nobody sells; what must be new is what the buyer HOLDS. The
   exists-gate checks listings for the object, never the genealogy of the
   rules.
