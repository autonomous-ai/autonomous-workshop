# scale-anchors

Turning pixel ratios into millimetres.

**Trigger:** The user gave no dimension and the image carries no dimension
lines. Load before writing the Size section.

## What the spec must carry

- **Name the anchor, name its source, and put it first in the Assumptions
  list.** Everything in the Size section hangs off it.
- Take the first anchor that applies, in the order `SKILL.md` Step 3 lists, and
  tag it: user-stated and drawing `[observed]`; known object, standard and
  function `[inferred]` with the object, standard or formula cited; nothing at
  all `[assumed]` with the verbatim line *"Everything scales with this — change
  it and the rest follows."*
- For a named product or component, web-search the manufacturer or standard and
  cite it; search `$step-parts` first for anything purchasable in frame.
- Run every sanity gate before writing the Size section — bed fit, minimum wall,
  minimum feature, overhang, order of magnitude — and state each finding,
  including every wall thickened and every feature dropped.
- When scaling, keep component-driven dimensions (walls, clearances, fasteners,
  seats, minimum feature) fixed and let the body absorb the change.

## The knowledge

- Anchor priority, focal-plane rule, standards and function minimums, the
  one-governing-dimension fallback: `skills/wiki/pages/image-reading/scale-anchors.md`
  (`wiki show scale-anchors`).
- Reference objects and their exact sizes (cards, paper, coins, batteries,
  LEGO, keys, connectors, fasteners): `skills/wiki/pages/image-reading/known-object-sizes.md`
  (`wiki show known-object-sizes`).
- Sanity gates and what does not scale: `skills/wiki/pages/image-reading/scaling-limits.md`
  (`wiki show scaling-limits`).
