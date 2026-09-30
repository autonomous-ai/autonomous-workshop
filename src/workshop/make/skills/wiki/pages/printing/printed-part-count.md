---
title: How many printed parts
tags: [split, part-count, decomposition, print-in-place, seam, assembly, purchased-part, detail-level]
aliases: [one part or many, splitting a model, parting line, mould seam, multi-part print, level of detail]
sources:
  - skills/cad/references/project-structure.md
  - skills/image-to-cad/references/decomposition.md
  - skills/cad/scripts/cadfits.py (print_in_place_gap)
  - "experience: image-derived specs that copied a photographed split into parts that never fitted, or fused a moving joint into one body"
related: [feature-build-order, fit-derivation, joints, wall-thickness-and-hollowing, print-in-place-mechanisms]
updated: 2026-09-23
---

# How many printed parts

Decide this before the file layout, because it decides the layout. **Default to
one part.** Most objects are a single sculpted body; a unified body looks
better, prints better, and has nothing to misfit.

The photographed object shows a *manufacturing* decomposition chosen for
injection moulding, assembly lines and material cost. None of those constraints
apply to an FDM print. Copying the photographed split is the most common way a
spec balloons from one clean part into six that never fit together. The
opposite failure is collapsing a genuine moving joint into one solid: a lamp
whose arm cannot move, a box whose lid cannot open.

## The split test

Split into a separate printed part **only** if at least one is true:

1. **It must open or be removed in use** — a lid, a cover, a drawer, a cap.
2. **It moves relative to the rest** — hinge, linkage, bearing, rotating joint —
   and is not print-in-place.
3. **No single orientation can print it** — two functional faces that must both
   be smooth and face opposite ways, or an unsupportable internal overhang or
   void ([[overhangs-and-print-orientation]]).
4. **It exceeds the bed** in every orientation.
5. **It must be a different material or colour**, and the user said so.
6. **It is a purchased component**, not printed at all — bearing, magnet, screw,
   PCB, motor. These are *pockets* in a printed part, sized from the real
   component's STEP rather than from a typed datasheet number
   ([[seating-bought-parts]]).

If none is true: **one part**. When genuinely unsure: **one part**.

A part count is not a file count. "Default to one part" answers *what gets
printed*; it does not answer *how many source files*. A one-piece display model
with 50 named solids is still a multi-file project. Decide the two questions
separately, in that order.

## The cosmetic-seam trap

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

State the call: *"The photo shows a seam at the waist. It is a mould parting
line, not a functional split — modelled as one body with a 0.5 mm decorative
groove at that height."* Naming it proves you saw it and decided.

## Print-in-place before splitting

Before splitting for a moving joint, ask whether it can print as one piece with
a clearance gap: hinges, sliders, drawers, ball joints and captive gears all
can, at the cost of a designed gap. Print-in-place keeps the object one part
*and* moving, which is usually what the image shows.

Take the gap from `cadfits.print_in_place_gap(fit, layer_height=, material=)`,
never a typed number: XY per mating face is 0.20 (`tight`), 0.30 (`sliding`,
the default) or 0.40 (`loose`), plus 0.05 for ooze-prone PETG/ABS/ASA; Z is
XY + layer height, because the top of a gap is a bridge that droops; and the
bottom chamfer is 0.5 mm ([[joints#revolute-joints]]). State the gap once so
both mating faces derive from it, and
record that only a print proves the joint frees.

The rest of the design — gaps near the bed, gap ceilings, pin orientation,
captive joints and the clearance check — is in [[print-in-place-mechanisms]].

## When you do split

For every printed part, state:

- **name** and **purpose** in one line;
- **outer envelope** (L × W × H mm);
- **the joint type** to its neighbour — lid lip, snap fit, dovetail, screw boss,
  magnet, press fit ([[joints]]);
- **the single shared mating dimension** the joint derives from;
- **the clearance per side**.

Both halves of a mate derive from **one** value, with the FDM clearance applied
in exactly **one** place — `lid_id = cavity_id + 2 × 0.2 mm slip` — so the two
halves cannot drift until they jam or fall out ([[fit-derivation]]).

State the **assembly order** too: the ordered steps to put it together and the
clearance each step needs. A part that is a valid solid but cannot be assembled
is a failure.

## How much detail is enough

Stop when every remaining difference between the design and the reference is
either (a) below the FDM minimum feature size, or (b) a texture rather than
geometry.

**Do not** model as geometry: fabric weave, brushed-metal grain, paint texture,
printed graphics, sub-0.3 mm panel gaps. Note them once under the finish.
Modelling them costs render time, blows up the mesh, and does not survive the
nozzle.

**Do** model as geometry: anything that reads at arm's length, anything
load-bearing, anything that interfaces with another object, and anything the
user pointed at.

## Pitfalls

- Copying the photographed split into printed parts.
- Splitting for a seam that is a mould line.
- Collapsing a real moving joint into one solid.
- Specifying a purchased component as a printed part instead of as a pocket.

How to cut and join once you do split: [[fdm-joining-split-prints]].
