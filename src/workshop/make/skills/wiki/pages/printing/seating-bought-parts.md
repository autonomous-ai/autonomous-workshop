---
title: Seating a purchased part
tags: [purchased-part, seat, pocket, servo, motor, bearing, offset, bore, step-import, mount]
aliases: [bought part, off-the-shelf component, component pocket, cavity, motor mount, servo bracket, cots]
sources:
  - skills/cad/scripts/cadmount.py (seat_for, envelope_for, bolt_holes, bolt_pattern)
  - skills/cad/references/bought-parts.md
  - "toolchain: OCC offset(+0.3) on the step.parts sg90_micro_servo STEP drops the hub and spline and returns a solid 2.9 mm shorter (reproducible)"
  - "experience: a seat whose mouth was cut on the floor side, leaving a skin over the well"
related: [printed-part-count, fit-derivation, joints]
updated: 2026-10-07
---

# Seating a purchased part

A servo, gearmotor, bearing or board is the one dimension a project cannot own.
It lives in a datasheet, a product page or a photograph, and once it is typed
into a generator nothing downstream can check it: every soundness, clash, fit,
motion and mesh check passes a bracket whose pocket is 2 mm too shallow for the
motor it was drawn for. Do not type it — derive the cavity from the component's
own STEP (procedure: `skills/cad/references/bought-parts.md`).

## Never offset the imported solid

`offset(component, +clearance)` is the obvious way to grow a part into its
clearance envelope, and on a real catalog STEP it is a trap. Measured on the
step.parts `sg90_micro_servo` file:

| | bbox Z |
|---|---|
| the servo as imported | 0.00 .. **29.90** |
| `offset(servo, +0.3)` | -0.30 .. **27.00** |

OCC grew it in X and Y, dropped the output hub and all 24 spline teeth, and
returned a solid 2.9 mm *shorter* than its input with no error. A pocket cut
from that envelope is a pocket the servo's spline crashes into — and it
validates, because the bracket is a perfectly sound solid.

The reliable route: section the raw solid along the insertion axis, union the
sections, apply clearance as a **2D** offset of that outline (where OCC is
reliable), extrude, then verify the seat contains the component and refine
until it does.

## A seat is a prism along the insertion direction

The seat should be the component's silhouette along its insertion direction,
swept straight through. An exact offset would hug the part more closely and
could not be assembled at all: any component wider somewhere than it is at its
mouth has an undercut, and rigid parts do not bend into one.

- Extend the cavity back past the component (a *mouth*) to break through the
  bracket's surface. A blind pocket is correct geometry and frequently leaves a
  skin the slicer prints and the component cannot pass. The mouth goes on the
  side the part comes in from; a mouth on the floor side leaves the skin, as
  thin as the clearance, and only an insertion sweep sees it.
- Use a running fit (`slip`, 0.20 per side) by default; never an interference
  class — a bought part does not compress.
- A bounding-box envelope is looser and cannot miss a feature: the answer when a
  silhouette seat will not converge, or when a rectangular pocket is what the
  bracket wanted anyway.
- A seat with ~3 mm of gap all round does not locate the component. That is
  right for a foam cradle and a defect everywhere else.

## Reading holes off an imported STEP

A component's STEP has every bore, including ones that are not for mounting
(a servo's horn screw is a bore like any other). Group bores by diameter; the
largest group of one diameter is the flange pattern on every servo and
gearmotor in the catalog (SG90: holes 1.7, 2.0, 2.0 → two Ø2.000 holes
27.20 mm apart, matching the datasheet's 27.2).

Two things about imported bores that a naive reader gets wrong:

- **A bore is often not a full cylindrical face.** Some files store flange holes
  as single faces sweeping ~77.5 % of a turn; other importers split a bore at its
  seam into halves. Group faces by axis line and radius and sum their sweeps;
  requiring ~60 % of a turn keeps a trimmed bore and rejects a slot end, which is
  exactly half.
- **The centroid of a trimmed cylindrical face is not on its axis** — about
  1 mm off on those flange holes. Reading a hole position from `face.center()`
  drills the screw hole a millimetre from where the screw is. Derive every
  position from the cylinder axis.

Size screw clearance holes through the same fit table as every other mate, and
a screw only needs one open side along its axis — a bracket with a back wall is
fine if the other side is clear.

## A multi-solid STEP is a pose, not a part

A catalog STEP that imports as several solids usually includes the parts that
move: a servo's horn, a motor's output shaft. A seat derived from all of them at
once is a seat for where they happen to sit, and fits nothing after the first
revolution. Choose which solid is the part: the largest (the others move), a
specific index read from the file in the same session (import order is not a
contract across vendors or revisions), or all of them only when nothing in the
component moves.

## What a derived seat still cannot tell you

- **That the component can reach its seat** through the rest of the model — a
  prismatic pocket is insertable in isolation. That is a motion check: `clear`
  along the insertion, `blocked` in the direction it must not back out.
- **That the wall around the seat prints.** A seat close to an outer surface
  leaves a thin wall ([[wall-thickness-and-hollowing]]); keep that wall a named
  parameter.
- **That the catalog model matches the part in your hand.** Hobby servos vary
  between vendors under one name. The STEP is a claim with a checksum, not a
  measurement.

Inserts, nut traps and printed threads: [[printed-threads-and-bosses]].

## A pocket square to a leaning face dives

A socket cut square to a face that leans `θ` from vertical (a drafted or
tapered side) runs downhill: over a depth `d` its floor drops `d sin θ`. A
7.4 mm connector opening cut square to a 9° side face dropped 1.2 mm and left
a 0.4 mm floor over a tie whose nominal wall was 1.5 mm; the thickness gate
found it, nothing else did ([[wall-thickness-and-hollowing]]). Cut a socket along the axis its part is inserted
(usually level), and check the wall at the far end of the cut, not at the
mouth.
