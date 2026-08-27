# decomposition

Splitting the object — into printed parts, then into features.

**Trigger:** Any object with visible seams, moving parts, or more than ~6
features. Load before writing Step 5.

## Why this exists

An image of a manufactured object shows you a **manufacturing decomposition**
that was chosen for injection moulding, assembly lines, and material cost. None
of those constraints apply to an FDM print. Copying the photographed split is
the single most common way an image-derived spec balloons from one clean part
into six that never fit together.

The other half of the failure is the opposite: collapsing a genuine moving joint
into one solid body, producing a lamp whose arm cannot move or a box whose lid
cannot open.

Get this level right and the rest of the spec is bookkeeping.

## Level 1 — printed parts: default to ONE

Follow the `cad` skill's rule. Most consumer objects are **one sculpted body**. Split
only when the object physically must come apart.

### The split test

Split into a separate printed part **only** if at least one is true:

1. **It must open or be removed in use** — a lid, a cover, a drawer, a cap.
2. **It moves relative to the rest** — hinge, linkage, bearing, rotating joint.
   (Unless it is print-in-place; see below.)
3. **No single orientation can print it** — two functional faces that must both
   be smooth and face opposite ways, or an unsupportable internal overhang.
4. **It exceeds the bed** in every orientation.
5. **It must be a different material or colour**, and the user said so.
6. **It is a purchased component**, not printed at all — bearing, magnet, screw,
   PCB, motor. These are *not* printed parts; they are pockets in a printed part.
   Spec the pocket, not the component — and search `$step-parts` for it first.
   Then **do not spec the pocket as a number either**: download the component's
   STEP into `<project-dir>/ref/` and let `cadmount` derive the cavity and the
   screw pattern from that file, because a dimension typed from a datasheet is
   one nothing downstream can check. Log the hit or the miss in spec section
   6c, and give every seated component a row in 6e so `check_mount` can measure
   the seat the generator actually cut.

If none is true: **one part**. When genuinely unsure: **one part**. A unified
body looks better, prints better, and has nothing to misfit.

### The cosmetic-seam trap

A visible parting line in a photo is **not** a reason to split. Mass-produced
objects show seams from mould tooling, from an assembly the factory needed, and
from parts sourced separately. On a printed version these become:

| In the photo | On the printed part |
|---|---|
| Mould parting line around the body | Nothing — delete it, or keep as a 0.5 mm cosmetic groove |
| Two-tone colour break | One body; a groove at the boundary if the user wants to paint it |
| Screwed-on faceplate | One body, with the screw heads modelled as cosmetic dimples or omitted |
| Rubber foot pads | Recesses in the base for stick-on pads, or a chamfered foot |
| Sticker / label panel | A shallow recessed panel, 0.4 mm deep |

State the call in the spec: *"The photo shows a seam at the waist `[observed]`.
It is a mould parting line, not a functional split — modelled as one body with a
0.5 mm decorative groove at that height."* Naming it proves you saw it and
decided, rather than missed it.

### Print-in-place before splitting

Before you split for a moving joint, ask whether it can print as one piece with
a clearance gap: hinges, sliders, drawers, ball joints, and captive gears all
can, at the cost of a designed gap. Use 0.35 mm per side for PLA and 0.45 mm
for PETG unless the user says otherwise. Print-in-place
keeps the object one part *and* moving, which is usually what the image shows.

Note it in the spec as a construction decision with its gap value, and state
the gap once so both mating faces derive from it.

### When you do split

For every printed part, the spec must state:

- **name** and **purpose** in one line;
- **outer envelope** (L × W × H mm);
- **the joint type** to its neighbour — lid lip, snap fit, dovetail, screw boss,
  magnet, press fit;
- **the single shared mating dimension** the joint derives from;
- **the clearance per side**.

The shared-dimension rule is non-negotiable and comes straight from `cad`:
both halves of a mate derive from **one** value, with the FDM clearance applied
in exactly **one** place. Write it that way in the spec — `lid_id = cavity_id +
2 × 0.2 mm slip` — so the implementation cannot size the two halves
independently and let them drift until they jam or fall out.

Also state the **assembly order**: the ordered steps to put it together, and the
clearance each step needs. A part that is a valid solid but cannot be assembled
is a failure.

## Level 2 — the feature tree

Inside each printed part, decompose into an ordered list. This is what "split it
into parts" usually means in practice.

### Find the base solid first

The base solid is the one primitive or profile that carries the object's mass
and identity. Everything else is added to it or cut from it. In a photo, it is:

- the largest continuous volume;
- the thing that would remain recognisable if every detail were removed;
- usually the thing the silhouette in `measure_image.py` is measuring.

Pick it wrong and every subsequent feature fights the geometry. Two tests:

- **The squint test.** Blur the object mentally until details vanish. What shape
  is left? That is the base solid.
- **The removal test.** If you deleted this feature, would the object still be
  the same object? If yes, it is a feature. If no, it is the base solid.

For a lofted or revolved body, the base solid is the **outer skin**, and the
functional interior is cut from it afterwards. That split — skin carries the
image, interior carries the engineering — is the normal premium pattern.

### The four tiers, in build order

1. **Base solid** — one operation. Extrude, revolve, loft, or sweep.
2. **Additive** — bosses, ribs, lugs, flanges, handles, fenders, standoffs.
   Each must be **rooted in the base solid**, overlapping it by real material,
   never merely touching. A feature that touches at a tangent produces
   `disconnected_bodies` and a floating part.
3. **Subtractive** — cavities, holes, slots, channels, ports, reliefs, shells.
4. **Finishing** — fillets, chamfers, edge breaks, engraving, texture.

### Ordering rules that prevent build failures

- **Most stable anchor first.** Build the feature that everything else is
  positioned from before the features that reference it.
- **Union before cut**, unless the cut is what makes the shape possible. A hole
  cut before a union can be refilled by the union — silently, with no error.
- **Shell before adding interior features**, so the shell does not hollow out
  the bosses you just added.
- **Fillets last.** A fillet applied before a boolean either gets consumed or
  makes the boolean fail. The exception is a 2D fillet on a sketch profile,
  which is part of the profile, not a finishing operation.
- **Tag frames you will need again.** If a feature's position is defined
  relative to a face that a later boolean will destroy, `tag()` the workplane
  before the destroying operation.

Write the order into the spec as numbered rows. `cad` executes them in that
order inside `gen_step()`, so the order *is* the implementation.

### Group repeated features

Four identical corner bosses are **one** row in the feature table with a count
and a placement rule — not four rows. Say the layout: `GridLocations`,
`PolarLocations`, or `Locations` with a named point list. A
repeated feature spelled out N times is a spec that will be implemented as N
hand-placed copies, and the next edit turn has to touch all of them.

## How much detail is enough

Stop when every remaining difference between your spec and the photo is either
(a) below the FDM minimum feature size, or (b) a texture rather than geometry.

Specifically, **do not** spec as geometry: fabric weave, brushed-metal grain,
paint texture, printed graphics, sub-0.3 mm panel gaps. Note them once under the
object's finish, and move on. Modelling them costs render time, blows up the
mesh, and does not survive the nozzle.

**Do** spec as geometry: anything that reads at arm's length, anything
load-bearing, anything that interfaces with another object, and anything the
user pointed at.

## Pitfalls

- Copying the photographed split into printed parts.
- Splitting for a seam that is a mould line.
- Collapsing a real moving joint into one solid.
- Choosing a detail as the base solid because it is visually prominent.
- Listing repeated features individually instead of as an array.
- Specifying fillets before the booleans they must survive.
- Specifying a purchased component as a printed part instead of as a pocket.
