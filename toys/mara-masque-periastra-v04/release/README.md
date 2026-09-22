# Periastra Zenith

English draughts under an observatory dome. The lid of the box is a 150 mm
hemispherical dome on a visible drum, and its shutter is open from the
observatory floor, over the apex, and down the far flank. Standing on that floor,
lying diagonally across the open dome with most of its length visible down the
slit, is a long bored telescope; only its mouth clears the shell. Lift the dome
straight up and the board is underneath, already set out: twelve terracotta Sun
counters against twelve cream Moon counters on the indigo squares of an 8 x 8
board.

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

## The dome and the telescope

The dome is a 150 mm exact hemisphere standing on a visible 11.7 mm drum. The
drum carries the rotation ring a real dome turns on, and that ring runs unbroken
all the way round: nothing is cut through the drum wall at any point, and nothing
on the roof stands outside the drum's own 75 mm radius below the springing line.

The shutter slit is 30 mm wide and cuts the dome only. It runs from 30 mm of arc
past the apex on the far side, over the apex, and down the near flank to the
springing line, where it stops on the drum top. That drum top is the observatory
floor.

The telescope stands on it, and nothing else holds it up. It is an 85 mm tube
15 mm across, inclined 50 degrees, its axis meeting the floor 13 mm from the
dome's centre, and the floor plane cuts it off flat on a level 15.0 x 19.6 mm
elliptical foot fused to the drum. Where it meets the floor it is blended in with
a 6 mm cove all the way round its foot, which spreads the root to 26.4 mm across
the slit and 35.2 mm along it. There is no fork, no yoke, no keel and no bracket:
the instrument stands on its own footing on the floor, the way it does in a real
observatory, and the dome turns around it. Its muzzle is open, bored 13 mm deep
into a 4 mm wall, and stands 3.9 mm proud of the shell — about a quarter of the
tube's own diameter, and 3.3 mm below the top of the dome. Of its 85 mm, 83 mm
are inside the dome, visible down the open slit.

The 16.2 mm plate margin round the dome is bare. No railing, walkway, ladder,
panelling, ribs, rivets, windows or finial.

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

**The telescope is a cantilever, and nothing physical backs it.** 85 mm of tube
stands off a 15.0 x 19.6 mm foot, with its centre of mass 17.6 mm outside that
foot. In an FDM print the layer lines at the root run the weak way across the
bending plane. The 6 mm cove round the foot is there for exactly that reason, and
it is a geometric mitigation only: no print, no drop, no load and no handling test
has been done on it. `cad/GEOMETRY-NOTES.md` section D4 states this in full.

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

Periastra Zenith is a correction of Periastra Meridian. One thing changes — the
telescope and the way the dome carries it — and nothing else in the object moves.

Before, the tube left the dome 55 degrees from the apex, low on the flank, and
stood nearly a whole tube's width of barrel in the open; an independent critic
read it as a teapot spout and, separately, as a cannon. It was carried on a
two-armed yoke whose foot block sat in a 30 mm channel cut clean through the drum
wall, which broke the rotation ring and showed two raw sawn faces.

Now the slit stops at the springing line, so the drum and its ring are whole; the
telescope stands on the slit floor as its own pier; and the fork, the arms, the
keel and the foot block are gone. Measured on the built STEP, the tube leaves the
dome 32.4 degrees from the apex, its muzzle stands 3.9 mm proud instead of
11.9 mm, exactly one piece of material stands in the slit at every height and it
is centred on the slit's mid-plane, and the drum ring has no gap anywhere.

The base, the 32 inlays and both counters come out of this revision byte for byte
identical to the ones before it, and the build fails if any of them moves. The
name changed because a correction cannot be published over a slug that already
holds different bytes; `cad/GEOMETRY-NOTES.md` section D0 has the reason in full.
