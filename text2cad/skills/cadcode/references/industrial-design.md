# Industrial design — the premium-product bar

Vibe parts should look like a high-end consumer product, not a blocky CAD
default. The anchor is Apple / Jony Ive — calm, reductive, cohesive — but the
range is broader: tasteful texture, contrast, and ergonomic sculpting are all
fair game when they serve the object. This doc is the rubric the build's
render-and-self-critique pass and the automatic polish round judge against.

**Function and printability win every conflict.** Aesthetics never override the
engineering rules in `references/hobbyist-defaults.md`,
`references/patterns/wall-thickness-rules.md`,
`references/patterns/fillet-stress-relief.md`, or
`references/patterns/overhang-relief.md`. Never thin a wall below its minimum,
remove material a load path needs, leave a functional/mating edge rounded, or add
a fillet that creates an unprintable overhang or a sub-1 mm³ sliver for looks. If
a beautiful move would hurt the part, pick function and say so in the source.

What separates a premium object from a blocky one is mostly **edges and
proportion**, and both are cheap to get right.

## 1. A unified radius language

The single highest-leverage move. Pick **one** corner radius for the object and
use it everywhere it belongs, instead of a scatter of raw 90° arrises and
ad-hoc fillets.

- Derive the radius from the part, don't guess it: `cadlib.styling.design_radius_for`
  takes the short plan dimension and returns a tasteful value (≈6–12% of the
  dimension, clamped). See `references/patterns/unified-radius.md`.
- **Soften every visible convex outer edge** to that radius with
  `cadlib.styling.soften_edges`. The deterministic check counts un-softened
  convex arrises and reports them as a `sharp_edges` advisory — drive that
  toward zero on visible faces, but only where it doesn't hurt function.
- **Concentric / nested radii.** When one rounded form sits inside another (a
  cavity in a shell), the inner radius should relate to the outer:
  `inner_r = outer_r − wall` keeps the wall a constant thickness around the
  curve. Mismatched radii read cheap.
- **Keep functional arrises sharp on purpose.** Mating faces, sealing lips,
  press-fit lands, and the build-plate edge (which already gets a chamfer) stay
  crisp. A unified radius language is about the parts the eye and hand land on,
  not every edge.

## 2. Proportion and restraint

- **Cohesive proportions.** Avoid arbitrary aspect ratios. A 1:1.3–1:1.6 plan
  rectangle reads more considered than 1:1.05 or 1:2.4. Heights that are a clean
  fraction of the plan (≈⅕–⅓) feel resolved.
- **Generous, uninterrupted primary surfaces.** The face the user sees most
  should be calm — push fasteners, vents, and labels to secondary faces or hide
  them. Negative space is a feature.
- **Align everything to a grid.** Holes, slots, and ribs on a shared pitch and
  shared margins look designed; features at eyeballed offsets look accidental.
- **Reductive part count.** Prefer one monolithic form to three bolted plates
  when the function allows it. Fewer seams, fewer fasteners, fewer radii to
  reconcile. See `references/patterns/surface-continuity.md`.
- **Minimize and conceal fasteners** — recess screw heads, use captive/hidden
  bosses, put the parting line where it's least visible — *only when the part
  still prints cleanly and assembles by hand.*

## 3. Surface continuity

- **Soft transitions, not abrupt steps.** Where a boss meets a wall or a stem
  meets a base, blend it (a root fillet) instead of leaving a hard shoulder. It
  reads better and relieves stress — function and form agree here.
- **Chamfer where a crisp line reads better than a round.** A small chamfer
  catches one clean line of light and, on a top edge, doubles as a support-free
  overhang break. Use `cadlib.styling.break_edges`. A chamfer-then-fillet combo
  on a prominent edge gives a soft transition with a defined highlight.
- **Don't mix raw 90° edges and rounded edges arbitrarily** on the same visible
  surface — commit to one treatment per face so the object reads intentional.

## 4. Ergonomics and texture

- **Sculpt where the hand or eye lands.** A finger scoop on a lid, a thumb
  relief on a grip, a gentle draft on a wall the eye rakes — small moves, big
  feel. Grip diameters ≈30–40 mm sit comfortably in the hand.
- **Texture and contrast are allowed when they serve the product** — a knurled
  grip band, a brushed-direction surface (printed bottom-face-down for the
  smooth glass finish), a recessed accent. Keep it deliberate and sparse;
  texture everywhere is noise.

## 5. Printability is part of the aesthetic

The finish *is* the surface, so orientation is a design decision, not an
afterthought.

- **Put the show face down** on the build plate for the glass-smooth finish; let
  layer lines fall on hidden faces (`references/patterns/print-orientation.md`).
- **Design the radius language to print support-free.** Chamfer top overhangs;
  keep fillets within the angles the printer bridges. A gorgeous render that
  needs a forest of supports loses its finish to scarring.
- A premium part is one that looks resolved **and** lifts off the plate clean.

## The bar, in one line

One radius language, calm primary surfaces, soft transitions, hidden fasteners,
printed show-face-down — every move paying for itself and none of it costing
strength or printability.
