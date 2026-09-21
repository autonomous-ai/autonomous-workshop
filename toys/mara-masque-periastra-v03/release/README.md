# Periastra Meridian

English draughts under an observatory dome. The lid of the box is a 150 mm
hemispherical dome on a visible drum, split by one shutter slit with a slender
bored telescope standing centred in it on a two-arm yoke. Lift the dome straight
up and the board is underneath, already set out: twelve terracotta Sun counters
against twelve cream Moon counters on the indigo squares of an 8 x 8 board.

Closed, it is 190 x 190 x 110.7 mm. It comes apart into two pieces, 32 board
inlays and 24 counters, with no hardware, no fasteners, no magnets and no
assembly step beyond dropping the inlays into their pockets once.

## What is in the box

| part | count | colour |
|---|---|---|
| Observatory board base | 1 | pale slate |
| Observatory dome roof | 1 | deep teal |
| Board inlay (`inlay_01`..`inlay_32`) | 32 | night indigo |
| Sun counter (`single_01`..`single_12`) | 12 | terracotta |
| Moon counter (`forked_01`..`forked_12`) | 12 | cream |

58 printed parts in total, from five designs. Every design prints flat on a
220 x 220 mm bed at a 0.4 mm nozzle with no raft-side trickery: the base bottom
down, the roof on its flat backing plate with the dome apex up, the inlays flat,
and the counters on either face.

## The board

The 32 dark squares are separate printed tiles, not a recess. Each one drops into
a blind 22.0 mm pocket 2.0 mm deep in the board floor and finishes flush with it,
with 0.25 mm of clearance per side. Print them in a colour that contrasts with
the base — they are specified in a night indigo against the base's pale slate —
and the chequer reads across the table instead of being a shallow step you have
to hunt for.

They are gravity-seated, with nothing holding them in. Drop them in once and the
board is a board; turn the base over and they fall out.

## How to play

English draughts, exactly as you already know it. Nothing about the rules, the
components' functions, the probabilities, the legal choices, the ending or the
player count is changed by the theme.

- Two players. Twelve counters a side, on the dark squares of the three rows
  nearest each player.
- Men move one square diagonally forward and capture by jumping diagonally
  forward. Capture is compulsory.
- A man that reaches the far row is crowned and its turn ends there.
- A king moves and captures one square diagonally in all four directions.
- You lose when you cannot move, or have no counters left.

**Crowning.** Stack a second counter of your own colour, face to face, on the
promoted piece. The two counters meet on their broad flat rim bands and on their
symbol tops — four surfaces coplanar at full face level — so the crowned pair is
14.0 mm tall and sits square on its square whichever way the two are turned.

Honestly: you crown by stacking one of your own captured counters, which is how
an ordinary draughts set works. A position exists in which a player reaches the
far row before any of their counters has been captured, and in that position the
set supplies nothing to stack. It is uncommon but it is real. This set stays at
twelve a side rather than carrying spares. The rules, powers, probabilities and
legal choices are unaffected; what is affected is the token, and players resolve
it as they would with any twelve-a-side set.

## Reading the pieces

Every counter is a Ø20.0 x 7.0 mm disc with a 1.0 mm chamfer on both edges. Both
faces are identical mirror images, so there is no starting face to specify and no
wrong way up. Each face has a flat 2.0 mm rim band, a field sunk 1.5 mm inside
it, and the mark standing back up out of that field to full face level:

- **Sun** — an unbroken ball with eight detached wedges round it, widening
  outward to blunt tips.
- **Moon** — one slim crescent whose horns curl past the middle towards each
  other, its tips rounded.

The marks are raised, never carved as holes. Colour separates the two sides at a
glance across the board; the marks tell you which is which in the hand and close
to. A counter is 20.0 mm on a 22.0 mm square, so it sits with 1.0 mm of indigo
showing round it.

## Storing it

Leave the counters on their starting squares and lower the roof back onto the
four integral corner ledges. The roof underside clears a counter's top by 3.0 mm.
The base wall is cut down along the four side spans, so the counters stay visible
through the reveal when the box is closed.

**Two things to know before you tip it over.** That reveal is 4.0 mm tall and
open all the way round. A counter is 7.0 mm thick and cannot pass through it, so
the counters stay in. An inlay is 2.0 mm thick and can, so tip the closed box and
you will lose inlays. Both are deliberate and neither is fixed in this revision.

## What has been checked, and what has not

This set has been verified digitally: exact solid geometry, algebraic and boolean
fit measured on the built STEP files, wall thickness at a 0.4 mm nozzle, a closed
manifold board mesh, and independent visual review by a critic who was shown the
renders before being told what the object was.

**It has not been printed.** No physical print, tactile fit, strength, durability
or human playtesting has occurred, and none is claimed. Motion is unverified: no
motion sweep, animation or motion review was run for this revision, so nothing
here claims the roof has been shown to seat or the inlays to drop in.

**It is not called print-ready.** The overhang gate fails both counters on its
span proxy — it measures the sunk field floor as one connected 14.0 mm ring
against a 12 mm allowance, while the real free bridge under that floor is 2.40 mm
on the Sun counter and 9.75 mm on the Moon. The counters are frozen in this
revision and have not been redesigned to make the proxy pass, so the product
carries no print-ready claim. `cad/GEOMETRY-NOTES.md` sets out every measurement,
deviation and limitation in full.

## This revision

Revision C corrects two defects in the previous Periastra Meridian build and
changes nothing else.

1. **The telescope yoke was 4 mm off centre** — both arms, by exactly one arm
   thickness, so one arm stood beside the tube without touching it and the other
   carried the telescope by itself off its centreline. Both arms now straddle the
   tube with 6.0 mm of clear air to each slit wall, and the roof is exactly
   mirror-symmetric about the slit's centre plane, measured on the built STEP.
2. **The board had no contrast** — 32 cells recessed 0.8 mm in one colour. They
   are now 32 separate inlays in a second filament.

The two counters come out of this revision byte for byte identical to the ones
before it, and the build fails if either moves.
