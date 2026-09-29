# decomposition

Splitting the object — into printed parts, then into features.

**Trigger:** Any object with visible seams, moving parts, or more than ~6
features. Load before writing Step 5.

## Why this exists

A photo shows a manufacturing decomposition chosen for moulding and assembly
lines, not for an FDM print. Copying it balloons one clean part into six that
never fit; the opposite failure fuses a moving joint into one body. Get this
level right and the rest of the spec is bookkeeping.

The design knowledge — the split test, the cosmetic-seam table, print-in-place
gaps, what a split owes, how much detail to model, and the feature-tree tiers
and ordering rules — lives in the wiki:

- `skills/wiki/pages/printing/printed-part-count.md` (`wiki show printed-part-count`)
- `skills/wiki/pages/printing/feature-build-order.md` (`wiki show feature-build-order`)

This page holds only what the spec must record.

## Level 1 — printed parts: default to ONE

Apply the split test (`wiki show printed-part-count#the-split-test`); it is the
same rule as the `cad` skill's. What the spec records:

- **Every seam you decided not to split on**, as a stated call: *"The photo
  shows a seam at the waist `[observed]`. It is a mould parting line, not a
  functional split — modelled as one body with a 0.5 mm decorative groove at
  that height."* Naming it proves you saw it and decided, rather than missed it.
- **A purchased component** (bearing, magnet, screw, PCB, motor) as a pocket,
  not a printed part. Search `$step-parts` for it first, download its STEP into
  `<project-dir>/ref/`, and let `cadmount` derive the cavity and the screw
  pattern from that file — never a number typed from a datasheet. Log the hit or
  the miss in spec section 6c, and give every seated component a row in 6e so
  `check_mount` can measure the seat the generator actually cut.
- **A print-in-place joint** as a construction decision with its gap value,
  stated once so both mating faces derive from it.
- **For every printed part you do split**: name and purpose, outer envelope,
  joint type to its neighbour, the single shared mating dimension, and the
  clearance per side — written as a derivation (`lid_id = cavity_id + 2 × 0.2 mm
  slip`) so the implementation cannot size the halves independently — plus the
  **assembly order** and the clearance each step needs
  (`wiki show printed-part-count#when-you-do-split`).

## Level 2 — the feature tree

Inside each printed part, find the base solid and order the features by the
tiers and rules in `wiki show feature-build-order`. What the spec records:

- the feature tree as **numbered rows** — `cad` executes them in that order
  inside `gen_step()`, so the order *is* the implementation;
- a repeated feature as **one row** with a count and a placement rule
  (`GridLocations`, `PolarLocations`, or `Locations` with a named point list),
  never N rows.

## How much detail is enough

Stop at the FDM minimum feature size and at texture
(`wiki show printed-part-count#how-much-detail-is-enough`). Note textures (fabric
weave, brushed grain, printed graphics, sub-0.3 mm panel gaps) once under the
object's finish, and move on.

## Pitfalls

The recurring ones are in `wiki show printed-part-count#pitfalls` and
`wiki show feature-build-order#pitfalls`.
