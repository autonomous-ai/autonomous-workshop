---
title: Print-in-place swivel rings
tags: [ball, socket, spherical, swivel, ring, print-in-place, retention, thumb]
aliases: [swivel ring, sphere band, spherical band, spherical socket ring, thumb ring swivel, rotating thumb ring, rotating ring, spinning ring, print-in-place ring, captive ring, page holder ring, finger loop swivel]
sources:
  - skills/cad/scripts/cadfits.py (print_in_place_gap: sliding xy 0.30, bottom_chamfer 0.5)
  - "experience: a thumb-ring page holder's swivel ring sized from these rules; check_motion spun it 360°, tilted it ±60° clear and blocked it along ±Z and sideways"
related: [ball-and-socket-joints, print-in-place-mechanisms, swivels-and-turntables, rounded-bodies-on-the-print-bed, creep-and-stress-relaxation]
updated: 2026-10-28
---

# Print-in-place swivel rings

A ring that must spin and tilt in a flat plate (a thumb-ring page holder, a
rotating finger loop) is a ball cut by the plate's two faces: a sphere band of
radius `R` between `z = ±h`, printed inside a concentric spherical socket of
radius `R + g`. Concentric spheres keep the gap `g` at every orientation, so
spin and tilt are unlimited; only the hand limits the tilt. Both mouths close
on the band, and the size of the plate sets how much:

```text
mouth radius at a face   r_f = sqrt((R + g)² − h²)
retention per side       y  ≈ R − sqrt((R + g)² − (h − b)²)      b = the edge break at that mouth
escape hoop strain       ε  ≈ y / R                              ring shrinks or plate stretches by this
sphere slope at a face   α  = asin(h / R)                        off vertical: the overhang of ball and lip
```

- **The plate's height buys the retention.** `y` grows as `(h − b)² / 2R`, so
  a thin plate barely holds its ring. A Ø22 bore with a 3.6 mm wall (`R`
  14.6) gives `y` 0.30 mm at 10 mm thick and 0.47 mm at 11 mm. Keep `ε`
  above printed PLA's elastic strain (about 1.5–2 %): at 2.1 % a ring can
  squeeze out. `ε` is an even-shrink estimate; ring and plate can also
  ovalise and bend at lower strain, so the pull-out force needs a pulled print. A larger bore
  with the same wall needs a thicker plate for the same `y`.
- **The gap is cadfits' sliding clearance plus the layer steps.** Each layer
  of a sloped sphere stands proud of the true surface by up to
  `(layer / 2) · tan α`, on the band and on the socket. A tilted band brings a
  ledge of one to a ledge of the other, so add both:
  `g = print_in_place_gap("sliding")["xy"] + 2 · (layer / 2) · tan α`
  (0.30 + 0.08 = 0.38 mm at 0.2 mm layers and α 22°).
- **Self-supporting by construction while α ≤ 30°.** The band's lower half and
  the socket lip above the equator both lean at most `α`. Open the socket
  mouth on the bed with a 30° cone (cadfits' `bottom_chamfer`) so the first
  layer's gap is about twice `g`. Leave the band's own bed edge sharp: it
  already leans outward, and a break there hangs flatter.
- **Grip ribs in the bore**: half-round ribs whose bed ends continue the
  bore's 30° bed flare, stopped short of the top bore round, so nothing
  overhangs and nothing pokes through the round.
- **Prove it both ways, in every direction.** `check_motion` spins the band
  360°, turns it ±90° about X, Y and the diagonal (`clear`), and with the band
  held tilted (a `coupled_motion_collision` whose rotation table stays at the
  tilt while its translation ramps) pushes it out along ±Z and sideways
  (`blocked`). On the built solids, the band's farthest point from the centre
  ≤ `R` and the plate's nearest ≥ `R + g` prove the gap at *any* rotation,
  which sampled axes cannot. None of this says how hard the band pulls out or
  how freely it breaks loose: only a print does.
- **Show it, or it reads as an axle.** A band in the plate's colour, with only
  a thin top cap in an accent, looks like a spinning bushing in a flat render;
  one owner judged it "a plain axial swivel" while it tilted freely to 90°.
  Render the band tilted 20° and 40° about two axes beside the part, and offer
  a contrasting band colour, which costs a filament swap on every layer.
