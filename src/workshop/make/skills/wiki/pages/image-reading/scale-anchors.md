---
title: Scale anchors
tags: [scale, anchor, dimension, size, photo, reference-image, confidence]
aliases: [scale reference, reference dimension, mm per pixel, absolute scale, sizing from a photo]
sources:
  - skills/image-to-cad/SKILL.md (confidence tags and the anchor order)
  - "experience: specs whose every dimension hung off an unstated anchor and came out uniformly wrong"
related: [known-object-sizes, scaling-limits, image-types-and-views, perspective-and-hidden-views]
updated: 2026-09-23
---

# Scale anchors

Pixels give ratios. Ratios give a *shape*. Only one real dimension gives a
*part*. Everything in a spec's size table hangs off a single anchor, so the
anchor is the most consequential number written — and the one most likely to
be silently wrong. No number of views supplies it: six views of an unlabelled
object still leave every dimension a ratio.

## Name the anchor first

Name the anchor, name its source, and put it first in the Assumptions list. A
user who can see "I assumed the mug is 95 mm tall" fixes a wrong model in one
message. A user handed a table of dimensions with no stated origin cannot tell
which number to challenge.

## Anchor priority

Work down this list and stop at the first one that applies.

1. **The user stated it — `[observed]`.** Use it exactly. Do not round it to
   something "nicer".
2. **A dimensioned drawing — `[observed]`.** Read the dimension lines. Check
   the title block for units and drawing scale before believing anything: a
   1:2 drawing's numbers are real-world, but a scale bar is not. If the drawing
   is in inches, convert once, state the conversion, and work in mm from there
   ([[reading-technical-drawings]]).
3. **A known object in frame — `[inferred]`.** Measure the reference object's
   pixels, divide by its real size, apply the resulting mm-per-pixel to the
   target. State the reference object and the size used for it
   ([[known-object-sizes]]).
4. **A standard the object must meet — `[inferred]`.** The object's own
   interface fixes its scale (below).
5. **Function forces it — `[inferred]`.** Derive the minimum and show the
   reasoning as a formula (below).
6. **Nothing at all — `[assumed]`.** Pick one governing dimension and derive
   every other as a ratio (below).

## A known object must share the focal plane

The reference object must be in roughly the same focal plane as the target. A
coin held toward the camera is larger in pixels than one lying beside the
object, and will scale the model down by 20–40 %.

## A standard the object must meet

- a Gridfinity bin ⇒ 42 mm grid pitch;
- a GoPro-compatible mount ⇒ the GoPro finger stack (web-search the exact
  finger thickness and gap; do not recall it);
- a bin that must hold a 608 bearing ⇒ Ø22 mm seat;
- a phone cradle ⇒ that phone's body width and thickness (web-search the
  model);
- a VESA plate ⇒ 75 or 100 mm bolt pitch;
- a DIN rail clip ⇒ 35 mm rail.

Measure the standard feature's pixels, set the scale from its known real size,
and derive the rest.

## Function forces a minimum

- a handle that must pass four fingers ⇒ clear opening ≥ 75 mm × 25 mm;
- a wall hook for a coat ⇒ hook depth ≥ 25 mm, upsweep ≥ 15 mm;
- a pen cup ⇒ interior Ø ≥ 60 mm for a useful capacity, depth ≥ 90 mm so pens
  do not tip out;
- a phone stand's lip ⇒ ≥ 8 mm to retain the phone;
- a cable channel ⇒ cable Ø + 2 to 4 mm.

## When nothing anchors the image

Pick **one** governing dimension — usually the overall height, because height
is the axis a photograph measures most honestly (it is unaffected by rotation
about the vertical axis). Derive every other dimension from it as a ratio, and
write, verbatim, in the Assumptions list:

> Overall height `[assumed]` 140 mm. **Everything scales with this — change it
> and the rest follows.**

If one question is allowed, this is where it goes: *"How tall should it be?"*
is almost always the highest-leverage thing to ask about an un-anchored image.

## Check the anchor against the object's class

State the object's real-world class in one clause and check the number
against it — a desk object is 50–300 mm, a handheld tool is 100–250 mm, a wall
bracket is 40–150 mm. A phone stand that came out 40 mm tall means the anchor
is wrong, not that the phone stand is small. The other sanity gates are in
[[scaling-limits]].

With parallel edges and one known length in the scene, single-view metrology
turns an [inferred] anchor into measured ratios: [[single-view-metrology]].
