# Which Uranus pole faces the camera

Measured on the exact colour bodies `parts/world.py` builds, sampled
on their own surfaces at 0.12 mm and dotted against each canonical
camera's view axis. Nothing here is read off a render.

Uranus's obliquity is 97.77 degrees, which puts its pole 7.77 degrees
past horizontal. A Sol world leans its north pole toward +X and its
Anti-Sol mirror toward -X, so the two armies show opposite poles.

## The poles themselves

| frame | army | north pole vs view axis | south pole vs view axis |
|---|---|---:|---:|
| hero (-55, 22) | sol | 61.6 deg | 118.4 deg |
| hero (-55, 22) | anti | 125.3 deg | 54.7 deg |
| sheet (-45, 35.264) | sol | 60.4 deg | 119.6 deg |
| sheet (-45, 35.264) | anti | 130.5 deg | 49.5 deg |

Under 90 degrees is on the visible face; over 90 is behind the limb.

## The hoods, as built

| frame | army | body | facing | pole offset | visible span | reads as |
|---|---|---|---:|---:|---|---|
| hero (-55, 22) | sol | `hood_north` | 92% | 0.88 | 0.47 to 1.00 | a broad region over the outer face, from 0.47 of the silhouette radius out to the limb |
| hero (-55, 22) | sol | `hood_south` | 4% | 1.12 | -- | hidden behind the limb |
| hero (-55, 22) | anti | `hood_north` | 0% | 1.18 | -- | hidden behind the limb |
| hero (-55, 22) | anti | `hood_south` | 100% | 0.82 | 0.37 to 1.00 | a broad region over the outer face, from 0.37 of the silhouette radius out to the limb |
| sheet (-45, 35.264) | sol | `hood_north` | 96% | 0.87 | 0.45 to 1.00 | a broad region over the outer face, from 0.45 of the silhouette radius out to the limb |
| sheet (-45, 35.264) | sol | `hood_south` | 2% | 1.13 | -- | hidden behind the limb |
| sheet (-45, 35.264) | anti | `hood_north` | 0% | 1.24 | -- | hidden behind the limb |
| sheet (-45, 35.264) | anti | `hood_south` | 100% | 0.76 | 0.30 to 0.98 | a broad region over the outer face, from 0.30 of the silhouette radius out to the limb |

Facing is the share of that body's own surface samples on the
hemisphere the camera can see. Pole offset is the sine of the angle
between the body's mean direction and the view axis: 0.00 is the dead
centre of the visible disc, 1.00 is the limb, above 1.00 is past it.
Visible span is where the part a reader can actually see lands in
projection, as a fraction of the globe's own radius.

**The hood is a broad region, not a spot, and it is not centred.**
The product's own two cameras are 60 to 62 degrees off this planet's
pole, so the visible hood runs from roughly half a radius out to the
limb: a wide soft brightening across the outer half of the face on the
side the piece leans toward. The centred reading the reference shows
is what the piece's own polar frame sees -- `snap/worlds/
uranus-sol-polar.png` and `uranus-anti-south-polar.png` -- and those
cameras sit 7.77 degrees below the horizon, which is the obliquity
rather than a choice. Both are rendered and both are kept.

## The ring against the hood

| frame | army | ring, visible span | ring outside the globe | visible hood span | hood cells the ring crosses |
|---|---|---|---:|---|---:|
| hero (-55, 22) | sol | 0.44 to 1.15 | 17% | 0.47 to 1.00 | 0% |
| hero (-55, 22) | anti | 0.54 to 1.11 | 16% | 0.37 to 1.00 | 0% |
| sheet (-45, 35.264) | sol | 0.45 to 1.09 | 13% | 0.45 to 1.00 | 0% |
| sheet (-45, 35.264) | anti | 0.61 to 1.17 | 20% | 0.30 to 0.98 | 0% |


A ring lies in the planet's equatorial plane, which is square to the
pole, so in space the hoop is 90 degrees from the hood everywhere and
the two cannot touch. What is left to check is the picture, where a
near limb can still cross in front of something behind it, and that is
the last column: the share of the picture cells the visible hood covers
that the visible ring also covers, at 0.5 mm of picture per cell.

**The hoop crosses none of the visible hood, at either frame, on
either army.** Not a small share -- none. The hoop is a narrow
upright band running over the meridian square to the pole, and the
hood is a wide region filling the outer face on the side the piece
leans toward, so the chord the hoop draws falls clear of it. They
occupy different parts of the piece, **checked rather than
assumed**, which is what the correction asked for.

Between 13 and 20 per cent of the visible hoop stands outside the
globe's own silhouette. That is the part that reads as a ring standing
off the ball rather than as a line drawn on it; the rest is the near
limb of the same hoop seen against the globe behind it. On a hoop this
small -- 1.00 mm of projection on an 11.01 mm radius -- that is what
a ring seen from anywhere but down its own axis looks like, and the
frame that shows the whole circle is the piece's own polar one.

## Verdict

**Every army shows a hood at every photographed frame.** That is
not what a single northern hood would have done, and measuring it
is what put a hood on both poles: with north alone, the Anti-Sol
piece turns its only marking 125.3 degrees from the camera at the
hero frame and 130.5 at the sheet frame -- past the limb at both,
so a whole army would have carried a marking no player ever sees.
Two hoods is also what the planet has. Uranus points a pole at the
Sun for forty years at a time and the bright polar region follows
whichever pole that is, so over one orbit it is both.

## What two hoods cost, said rather than hidden

A hood at each pole makes this world's SURFACE symmetric, so at the
product's own two frames the two armies show the same thing: a pale
region on the same side of the globe and the hoop across the other.
`snap/worlds/uranus-pair-hero.png` shows exactly that. On Saturn the
single northern cap is an ownership cue in its own right --
`measure/saturn-cap-visibility.md` makes that case -- and Uranus gives
that up.

It gives it up for a reason and not for nothing. A northern hood alone
is not a cue on this world, it is a marking one army never shows: the
numbers above put it 125.3 and 130.5 degrees from the camera on every
Anti-Sol piece, past the limb at both frames. A cue that is invisible on
half the pieces is not a cue. What still tells the two apart on this
world is what tells them apart on the six worlds with no cap at all --
the disc, `white` against `black`, and the numeral in the other tone --
plus one thing those six do not have: the hoop leans the other way,
because it stands in the equatorial plane of a globe that leans the
other way. `measure/uranus-mirror.md` measures that as an exact mirror
in X.

The hoods print in `beige`; `measure/uranus-tone-separation.md` is why.
Measured by `measure/uranus_facing.py` on the built solids.
