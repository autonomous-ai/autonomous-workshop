# form-from-reference

Pick the construction operation from the image, not from habit.

**Trigger:** A reference image defines the requested exterior, silhouette, or
stance, especially when the form tapers, rolls, floats, or curves in two axes.

## Why this exists

When a reference image is attached, the single most consequential decision of
the whole build happens **before any code**: which construction operation family
can express the form the image shows. Every later edit inherits that choice. A
form authored as the wrong family cannot be rescued by parameter edits — only by
re-authoring — so a mistake here costs the user the entire follow-up
conversation.

**The failure this doc exists to prevent:** extruding one 2D side profile at
constant depth and presenting it as a match for a reference whose width visibly
changes along its length. The silhouette matches from exactly one viewpoint; from
every other angle the object reads as a slab with soft corners. If the reference
shows a tapering, rolling, or double-curved body, a constant-depth extrusion is
**wrong by construction** — do not start there and plan to "fix it later".

## Triage: three questions about the reference

Answer these by looking at the image before editing geometry:

1. **Does the cross-section change along the object's length?** (width taper in
   plan, height taper in elevation, or a rolling section shape)
2. **Are there double-curved surfaces?** (surfaces curving in two directions at
   once — a fuselage belly, a blended nose, an organic shell)
3. **Is the object's identity carried by its silhouette from more than one
   view?** (product hero shots almost always say yes)

"No" to all three → prismatic; extrude and move on. **Any "yes" → the form needs
a section-driven operation (loft/sweep/revolve), not an extrusion.**

## Form class → operation family

| The reference shows… | Author it as | CadQuery idiom |
|---|---|---|
| Prismatic body, constant section (box, tray, bracket, plate) | Extrude | `Workplane.rect/polyline ….extrude()` |
| Rotationally symmetric body (vase, knob, bottle, dome) | Revolve | `Workplane.polyline/spline ….revolve()` |
| Tapering / rolling body — fuselage, ribbon, swoosh, hull, handle | **Loft over ≥3 cross-sections** placed along a spine | one wire per station via a `section_at(t)` helper → `Workplane.loft(ruled=False)` |
| Constant-ish section flowing along a curved path (tube, rail, strap) | Sweep along a spine wire | `Workplane.sweep(path, multisection=…)` |
| Blended freeform mass (organic shell, sculpted grip) | Loft stack + generous blends; interpolated plate for a local freeform patch | `loft` + `fillet`; `Solid.interpPlate` for a bounded patch |

Mixed objects decompose: a lofted outer skin + extruded/booleaned functional
interior (bays, channels, bosses) is the normal premium pattern. The skin
carries the image; the interior carries the engineering contract.

## Loft mechanics that keep the part buildable and remixable

- **One `section_at(...)` helper, parameter-driven.** Generate every station
  wire from the same function of the `Params` dataclass so the sections stay
  remixable and structurally consistent. Never hand-place N unrelated wires.
- **Same segment structure per section.** Each station wire should be built
  from the same number and order of segments/control points; OCCT lofts between
  corresponding vertices, and mismatched wires produce twisted or failed lofts.
- **Place stations at curvature events**, not on an even grid: nose, widest
  point, waist, tail — wherever the reference's outline changes character. Three
  to six stations express most product forms.
- **`ruled=False`** for the smooth premium read; `ruled=True` only when the
  reference genuinely shows flat panels between stations.
- **Boolean the functional interior afterwards.** Cut bays/channels from the
  lofted solid; root added bosses inside the skin so `fast_union` fuses
  watertight (see `references/patterns/anchor-to-body.md`).

## Prove the match with numbers, not adjectives

Extract a small **proportion ledger** from the reference image in working notes,
and assert it in `validation.py` like any other literal contract:

- overall aspect ratios (length : height : depth) read from the image, ±10%;
- ground-contact length as a fraction of body length (a "floating" stance is a
  *measurable* short contact patch, not a vibe);
- the height of any hover/undercut as a fraction of body height;
- where along the length the widest/tallest point sits (front third? middle?).

A build that fails its own ledger does not go to render review as a "match". The
ledger is also what makes the next edit turn cheap: the numbers name exactly
which aspect of the form moved away from the reference.

## When the image and the function disagree

Function and printability still win every conflict
(`references/industrial-design.md`). Keep the engineering contract — envelopes,
interfaces, load paths — and sculpt the *skin* to the reference around it. Say
explicitly in the final summary which visible aspect of the reference was traded
away and why, so the user hears the trade instead of discovering it in the render.

## Pitfalls

- Matching one side silhouette with a constant-depth extrusion.
- Adding fillets or notches while retaining the rejected construction family.
- Using unrelated station wires whose vertex order twists the loft.
- Treating prose such as "premium" or "iconic" as a substitute for measured
  proportions and multi-view render comparison.
