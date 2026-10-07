---
title: Volvelle two-state display (one disc, a cover hides the other half)
tags: [volvelle, rotating-disc, two-state, day-night, sun-moon, detent, toy, display, cover]
aliases: [day night disc, sun and moon toy, turning disc behind a cover, planisphere disc, moon phase disc, two state turning toy, flip state by turning, rotating indicator disc]
sources:
  - https://en.wikipedia.org/wiki/Planisphere (two discs on a common pivot; the overlay shows only part of the turning disc)
  - https://swisswatches-magazine.com/midnight-jour-nuit-phase-de-lune/ (a sun gives way to a moon on rotating discs under a dial that hides the one not shown)
  - "experience: a crescent-moon / rayed-sun toy built as one disc turning half a turn behind a cloud-shaped cover"
  - "experience: identical crescent blades fanned about one pivot read as a pinwheel, not a sun, at three proportions"
  - "experience: a floor finger, spherical dimples and a bed-face logo each failed the print gates until tied, flat-roofed and moved to the top"
related: [latches-detents-and-ratchets, flexure-materials-and-snap-strain, swivels-and-turntables, push-to-turn-indexer, product-aesthetics]
updated: 2026-10-05
---

# Volvelle two-state display

A toy or indicator that shows one of two things — a sun or a moon, open or
closed — by turning one flat disc half a turn behind a cover. The cover hides
whichever body is down; the body that is up stands out past the cover's edge,
so the two states have different silhouettes, not just different faces.

## Why one disc and a cover

Morphing one silhouette into another by rotating rigid plates about a single
pivot runs into area: every plate's outline is part of the union's outline,
and the plates stacked in the smaller state must each fit inside it. A crescent
cannot become a rayed sun with two plates, and with four identical crescents
fanned round one pivot the result reads as a pinwheel at every proportion
tried. A disc that carries both bodies, half a turn apart, behind a cover that
hides the lower half, needs one moving part and gives each state its own
silhouette. A flip coin in a ring is simpler still, but its outline is the
same circle in both states.

## Geometry rules

- **Each body lives in its own half-plane.** With the up direction `u`, cut
  the up body to `u . p >= 0` and the down body to `u . p <= 0` (in the disc's
  frame, before turning it). Turned half a turn, each lands exactly where the
  other was, so the cover only has to hide one half-disc of the sweep radius.
- **The cover must contain the whole down half in both states**, and the hub
  round the bore too: a hub radius larger than the cover reaches past the
  axle shows as a lump beside the up body. Size the hub from the cover's reach
  round the axle, not from the bore alone.
- **Crown the cover's edge past the dividing line** (2–5 mm) so the bodies' cut
  edges never show; puffs or bumps stepping up the line do it and read as the
  cover's own shape.
- **Offset the up body outward** along `u` so more than half of it shows; the
  sweep radius (body centre offset plus its reach) sets the cover's size.
- Check both states numerically: (disc turned) ∩ (hidden half) − cover must
  be empty, and so must the same for the other state.

## Holding the states

- Sandwich the disc between floor and cover on one axle: one radial locator,
  the plates take the tilt ([[swivels-and-turntables#which-swivel]]).
- A **flexing finger cut from the floor** with a bump under the disc and two
  holes in the disc's back half a turn apart gives the click. Undercut the
  finger from the back face by more than its travel, or the finger bottoms on
  the table when the toy lies on its back.
- **That undercut's roof is the finger's underside, held only at its root** — a
  cantilevered first layer over air when the floor prints face down. Tie the
  finger's tip across its slot with one small square (two lines a side) so the
  roof prints as a bridge from root to tie, keep that span under the printer's
  bridge limit (about 12 mm: shorten the finger and widen it to keep the force),
  and cut the tie before assembly.
- **Holes, not dimples, on a bed face.** A spherical dimple's roof is an
  overhang; a flat-roofed hole is a short bridge, and the bump sits on its rim
  the same way (seat depth `r - sqrt(r^2 - (d/2)^2)` for bump radius `r`, hole
  diameter `d`). Make the hole deeper than the seat so the rim, not the roof,
  carries the bump, and leave a roof of two minimum walls over it.
- **Marks go on top faces.** A logo debossed into the bed-face side leaves its
  skin as the thin wall; deboss it into the cover's top over the spot instead
  and say which face to tap.
- **The bump must exceed the axial play.** Travel off the dimple is
  `bump height − (pocket height − disc thickness)`; with a bump equal to the
  play the disc just lifts and nothing clicks. Make the dimple shallower than
  `bump − play` and the seated bump still lifts the disc a little, so it does
  not rattle in either state.
- Put the bump where the disc has material in **both** states: at `B` and at
  `−B` in the disc's frame. Search that radius numerically; the largest one
  gives the most holding torque.
- Holding force and strain follow [[latches-detents-and-ratchets#detent-holding-force]]
  and [[flexure-materials-and-snap-strain]]; keep PLA under about 0.5 % strain.
- A rigid sweep reads the bump as a collision: declare the bump's overlap
  volume as the rotation check's allowance and run a second rotation check
  against the cover alone at zero allowance.
