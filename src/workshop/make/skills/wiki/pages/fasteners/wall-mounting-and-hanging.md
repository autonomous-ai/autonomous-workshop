---
title: Wall mounting and hanging
tags: [wall-mount, keyhole, french-cleat, anchor, drywall, bracket, adhesive-strip, prying]
aliases: [keyhole slot, keyhole hanger, french cleat, z clip, wall anchor, drywall anchor, plasterboard plug, toggle bolt, molly bolt, snaptoggle, picture hook, sawtooth hanger, command strip, adhesive hook, wall bracket, shelf bracket, pull-out, hanging a frame]
sources:
  - https://en.wikipedia.org/wiki/French_cleat (45° mating bevels, cleat spans studs, secure the bottom)
  - https://anchors.aerosmithfastening.com/wp-content/uploads/2020/03/aerosmith-toggle-bolt-performance-data.pdf (wing toggle ultimate and allowable loads in 3/8–3/4 in drywall, safety factor 4)
  - https://toggler.co.uk/wp-content/uploads/2021/09/Metric-Technical_SNAPTOGGLE.pdf (SNAPTOGGLE metric tension/shear in 12.5 and 15 mm drywall, 1/4 of ultimate)
  - https://www.toolboxsupply.com/products/e-z-ancor-25310-twist-n-lock-self-drilling-drywall-anchor-75-lb-50-pack (package "hangs up to 75 lb", rating basis not stated)
  - https://www.rockler.com/hanging-slot-router-bits-router-bits (keyhole bits 3/8 in and 1/2 in, wide end admits the head, narrow slot captures it)
  - https://www.command.com/3M/en_US/command/how-to-use/product-weight-limits/ (strip ratings by size, indoor 50–105 °F; via search excerpt)
  - Meriam & Kraige, Engineering Mechanics: Statics, ch. 3 (equilibrium of a rigid body; the prying moment)
related: [screws-into-plastic, screw-head-recesses, metric-screw-clearance-holes, layer-anisotropy, creep-and-stress-relaxation, fdm-print-orientation-for-strength, overhangs-and-print-orientation, adhesives-and-solvent-welding, magnets-and-strap-slots]
updated: 2026-09-23
---

# Wall mounting and hanging

Hanging something on a wall is three designs in series: the **interface** on
the object (keyhole, cleat, hook), the **fastener in the wall** (screw into a
stud, anchor in drywall, adhesive strip), and the **printed part** between
them. The weakest link is usually the wall anchor loaded in pull-out by a
prying moment nobody computed, or a printed hook creeping open. Read this for
any wall-hung frame, shelf, holder, bracket or display.

## Load the fastener actually sees: prying

An object whose centre of mass sits a distance `e` out from the wall pries the
top fasteners out of the wall. With the top fastener(s) a height `h` above the
bottom edge the object bears on:

```text
V = W                    shear at the fasteners (straight down the wall)
T = W * e / h            tension (pull-out) at the top fasteners, total
C = W * e / h            compression at the bottom bearing edge
```

Worked: a 2 kg shelf load (19.6 N) whose CoM is 100 mm out, fasteners 60 mm
above the bottom bearing edge → T = 19.6 · 100 / 60 = 33 N of pull-out,
nearly twice the weight. Tall back plates (large h) and shallow objects
(small e) keep T down. A frame hanging flat on a wire has e ≈ 0, so its
fastener sees almost pure shear.

## Wall anchors: pull-out versus shear

Vendor tables for toggles give tension and shear of the same order, and the
published figures are **ultimate** loads. Divide by 4 (the industry safety
factor the vendors state) for a working load.

Wing toggle bolts (one vendor's table, ultimate, lb):

| toggle | 3/8 in board T / V | 1/2 in board T / V | 5/8 in board T / V |
|---|---|---|---|
| 1/8 in | 105 / 120 | 140 / 135 | 180 / 180 |
| 3/16 in | 125 / 140 | 175 / 190 | 230 / 235 |
| 1/2 in | 245 / 275 | 315 / 315 | 385 / 375 |

Allowable (÷ 4) in 1/2 in board is therefore roughly 35–80 lb (16–36 kg).
A channel toggle (SNAPTOGGLE, metric) in 12.5 mm drywall: ultimate 108–124 kg
tension and 109–132 kg shear across M5–M10; the vendor recommends 1/4 of
that. The drywall gouges or breaks first: the board, not the steel, is the
limit.

Plastic expansion plugs and self-drilling screw-in anchors are sold with a
single "hangs up to N lb" on the package, and the basis (ultimate or
working, shear or tension) is often not stated. Treat such a number as a
**shear** rating for a flat-hung item, never as pull-out capacity, and design
a pried bracket for toggles or a stud.

Rules:

- Into a stud or solid wall, the screw's own pull-out governs; into drywall
  alone, the anchor's. Record which the design assumes.
- With both loads present, keep `T/T_allow + V/V_allow <= 1` (a conservative
  linear interaction).
- Two fasteners do not share load evenly unless the mount is stiff and the
  holes are well placed; size each for the full T when in doubt.

## Keyhole slots

A keyhole lets a screw left proud of the wall pass its head through a round
entry hole, then slide into a narrow slot that captures the head. Derive every
dimension from the screw head (`stdpart` gives dk, k and d for ISO screws;
[[screw-head-recesses]], [[metric-screw-clearance-holes]]):

```text
entry hole        D_entry = dk + 2c
slot width        S = d + 2c,               with S < dk - 2*overlap
undercut channel  W_ch = dk + 2c wide, depth >= k + c (+ the gap left under the head)
slot length       L >= dk/2 + travel        so the head is fully under the lip
lip thickness     t_lip carries T (above) in bending across S
```

`c` is the printed clearance for the nozzle ([[fdm-hole-accuracy]]), and
`overlap` is how much lip each side of the slot keeps over the head (a
millimetre or more on each side for a pan head).

- The slot runs **up** from the entry hole: the object is placed over the
  heads and pushed down, so the screws end at the top of the slot and gravity
  keeps them there.
- Screws cannot be set on exact centres in a wall. With two keyholes, make the
  slots long enough to absorb the vertical error, and either widen one entry
  and channel horizontally or use one keyhole plus a bottom bearing point.
- Use a pan, button or washer head. A countersunk wood screw's cone wedges the
  lip apart.
- **Print with the back face on the bed.** The channel is then an open slot
  from the bed, and the lip is a short bridge of width `W_ch`
  ([[fdm-bridging-and-sacrificial-layers]]). The lip is a plate in the X-Y plane, so its bending stress
  runs along the layers.

Woodworking keyhole bits are sold in 3/8 in and 1/2 in head sizes; a printed
keyhole sized from the actual screw is better than one copied from a bit.

## French cleats

Two strips with mating **45°** bevels: one screwed to the wall, bevel up and
facing the wall; one on the object, bevel down. Weight pulls the object's cleat
down and in, toward the wall, so the joint self-locks and self-levels. The wall
cleat can run full width and catch every stud it crosses.

- Put a spacer of the cleat's thickness at the object's bottom edge so it
  hangs vertical and the bottom bears on the wall (that edge is the `C` above).
  Screw the bottom edge to the wall if it could be bumped up off the cleat.
- The prying force on the wall cleat is set by e and by the cleat-to-spacer
  height h, exactly as above.
- **Printed cleats**: print the profile on the bed (the cleat's length along
  Z), or lying on its back with the bevel as an up-facing slope. A down-facing
  printed bevel at exactly 45° is at the overhang limit
  ([[overhangs-and-print-orientation]]); a cleat printed lying on its bevel
  puts its hook lip in bending across the layers.

## Hooks, sawtooth hangers and adhesive strips

- **Picture hooks with an angled nail** and **sawtooth hangers** are sold
  with a package rating for a flat frame in shear. They are the right choice
  only when e ≈ 0.
- **Adhesive strips** (Command type) are rated per strip size, for shear on
  smooth painted or finished surfaces, indoors (the maker gives about 10–40 °C,
  50–105 °F), and fail on textured, fresh or wallpapered surfaces. Their
  pull-out resistance is small: keep e near zero and the CoM low on the
  bonded area. The rating is per set on the package; never extrapolate.
- A printed hook under a permanent load **creeps** open, faster when warm
  ([[creep-and-stress-relaxation]]): pick PETG, ASA or PC over PLA, and design
  the hook with a large safety factor on sustained stress.

## Orienting a printed wall bracket

A bracket is a cantilever: the layer weld must not carry its bending tension
([[layer-anisotropy#orient-so-layers-do-not-carry-the-tension]],
[[fdm-print-orientation-for-strength#orient-by-load]]).

- An L-bracket prints **on its side**, so both legs and the inside corner lie
  in the X-Y plane. Printed standing on its wall leg, the corner fails at a
  layer line under the first real load.
- Fillet the inside corner generously; that is where T and the bending peak.
- Screw holes through the wall plate: counterbore for a pan or washer head,
  add perimeters around them ([[screws-into-plastic]]), and give the plate
  enough thickness under the head that screw preload does not crush it.

## Checks

```python
T = W * e / h                              # N, total pull-out at the top fasteners
V = W
assert T / n_top <= T_ult_anchor / 4, "anchor pull-out over 1/4 of ultimate"
assert T / T_allow + V / V_allow <= 1.0, "combined anchor load over allowable"
assert SLOT_W < HEAD_D - 2 * LIP_OVERLAP, "keyhole slot lets the head through"
assert ENTRY_D >= HEAD_D + 2 * CLEAR, "keyhole entry will not pass the head"
assert CHANNEL_DEPTH >= HEAD_K + CLEAR, "head will not fit under the lip"
```
