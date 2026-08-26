# scale-anchors

Turning pixel ratios into millimetres.

**Trigger:** The user gave no dimension and the image carries no dimension
lines. Load before writing the Size section.

## Why this exists

Pixels give ratios. Ratios give a *shape*. Only one real dimension gives a
*part*. Everything in the spec's Size section hangs off a single anchor, so the
anchor is the most consequential number you will write — and the one most likely
to be silently wrong.

The rule: **name the anchor, name its source, and put it first in the
Assumptions list.** A user who can see "I assumed the mug is 95 mm tall" fixes a
wrong model in one message. A user handed a table of dimensions with no stated
origin cannot tell which number to challenge.

## Anchor priority

Work down this list and stop at the first one that applies.

### 1. The user stated it — `[observed]`
Use it exactly. Do not round it to something "nicer".

### 2. A dimensioned drawing — `[observed]`
Read the dimension lines. Check the title block for units and drawing scale
before believing anything: a 1:2 drawing's numbers are real-world, but a
scale bar is not. If the drawing is in inches, convert once, state the
conversion, and work in mm from there.

### 3. A known object in frame — `[inferred]`
Measure the reference object's pixels, divide by its real size, apply the
resulting mm-per-pixel to the target. **State the reference object and the size
you used for it.**

The reference object must be in roughly the same focal plane as the target. A
coin held toward the camera is larger in pixels than one lying beside the
object, and will scale your model down by 20–40%.

| Reference object | Real dimension | Confidence |
|---|---|---|
| ISO/IEC 7810 ID-1 card (credit/bank/ID) | 85.60 × 53.98 mm | Exact — a global standard |
| A4 sheet | 297 × 210 mm | Exact |
| US Letter sheet | 279.4 × 215.9 mm | Exact |
| LEGO stud pitch | 8.0 mm | Exact |
| LEGO 2×4 brick | 31.8 × 15.8 × 9.6 mm | Exact |
| Cherry-MX keyboard key pitch (1u) | 19.05 mm | Exact |
| AA battery | 50.5 × Ø14.5 mm | Exact |
| AAA battery | 44.5 × Ø10.5 mm | Exact |
| USB-A plug shell | 12.0 × 4.5 mm | Exact |
| USB-C receptacle opening | 8.34 × 2.56 mm | Exact |
| 608 skate bearing | Ø22 OD × Ø8 ID × 7 W mm | Exact |
| M3 socket-head cap screw head | Ø5.5 mm, 2.5 mm hex | Exact (ISO 4762) |
| M3 nut across flats | 5.5 mm | Exact (ISO 4032) |
| Gridfinity grid pitch | 42.0 mm | Exact |
| US quarter | Ø24.26 mm | Exact |
| US penny | Ø19.05 mm | Exact |
| 1 euro coin | Ø23.25 mm | Exact |
| 2 euro coin | Ø25.75 mm | Exact |
| Adult palm width (4 fingers) | ~80–90 mm | Coarse — ±10%, state as a range |
| Adult index finger width | ~18–20 mm | Coarse |
| Standard coffee mug | ~Ø80 × 95 mm | Coarse — varies enormously |
| Interior door height | ~2000–2100 mm | Coarse, region-dependent |

For anything not on this list — a named phone, a specific motor, a wall plate, a
connector, a vehicle part — **web-search the manufacturer or standards spec**.
Do not carry these from memory: they drift by model and region, and a confident
recalled number is the classic failure. Cite the source in the spec.

If a `step-parts` skill is installed, search its catalog first for any
purchasable component visible in the image — an exact catalog record beats both
a table lookup and a search.

### 4. A standard the object must meet — `[inferred]`
The object's own interface fixes its scale:

- a Gridfinity bin ⇒ 42 mm grid pitch;
- a GoPro-compatible mount ⇒ the GoPro finger stack (web-search the exact
  finger thickness and gap; do not recall it);
- a bin that must hold a 608 bearing ⇒ Ø22 mm seat;
- a phone cradle ⇒ that phone's body width and thickness (web-search the model);
- a VESA plate ⇒ 75 or 100 mm bolt pitch;
- a DIN rail clip ⇒ 35 mm rail.

Measure the standard feature's pixels, set the scale from its known real size,
and derive the rest.

### 5. Function forces it — `[inferred]`
Show the reasoning as a formula:

- a handle that must pass four fingers ⇒ clear opening ≥ 75 mm × 25 mm;
- a wall hook for a coat ⇒ hook depth ≥ 25 mm, upsweep ≥ 15 mm;
- a pen cup ⇒ interior Ø ≥ 60 mm for a useful capacity, depth ≥ 90 mm so pens
  do not tip out;
- a phone stand's lip ⇒ ≥ 8 mm to retain the phone;
- a cable channel ⇒ cable Ø + 2 to 4 mm.

### 6. Nothing at all — `[assumed]`
Pick **one** governing dimension — usually the overall height, because height is
the axis a photograph measures most honestly. Derive every other dimension from
it as a ratio. Then write, verbatim, in the Assumptions list:

> Overall height `[assumed]` 140 mm. **Everything scales with this — change it
> and the rest follows.**

This is also the moment to ask your one question, if you get one: *"How tall
should it be?"* is almost always the highest-leverage thing you can ask about an
un-anchored image.

## Sanity gates — run every one before writing the Size section

**Bed fit.** Does the largest dimension exceed the print bed? Default assumption
is 200 × 200 × 200 mm (the sanity bound to design to); common real beds are 220 mm
(Ender 3 class) and 256 mm (Bambu X1/P1 class). If it does not fit, say so and
name the remedy: scale down, split into parts with a stated joint, or print
diagonally.

**Minimum wall.** At your chosen scale, is any wall thinner than 0.8 mm (2 ×
0.4 mm nozzle)? Walls **do not scale**. A model scaled to half size needs its
walls re-thickened to the same absolute minimum, which changes the proportion the
image showed. Say which walls you thickened and by how much — this is a visible
trade, not a silent fix.

**Minimum feature.** Anything below ~1.5 mm will not survive FDM: thin ribs, fine
engraving, sharp text, small pins. In the image these are often the details that
carry the object's character. Name each one and either deepen/thicken it, or
state that it is dropped.

**Overhang.** From the side view, is any surface more than 45° from vertical? At
your scale, does it bridge more than ~10 mm unsupported? Name the print
orientation that avoids the worst of it.

**Order-of-magnitude.** State the object's real-world class in one clause and
check your number against it — a desk object is 50–300 mm, a handheld tool is
100–250 mm, a wall bracket is 40–150 mm. A phone stand that came out 40 mm tall
means the anchor is wrong, not that the phone stand is small.

## What breaks when you scale

Scaling a spec is not multiplying every number. State these explicitly whenever
you scale:

| Scales with the model | Does **not** scale |
|---|---|
| Overall envelope, feature positions, cosmetic radii | Wall thickness (nozzle-bound) |
| Cavity sizes for scaled contents | Clearances and tolerances (printer-bound, ±0.2/0.4 mm) |
| Aesthetic proportions | Fastener sizes (M3 stays M3) |
| | Bearing/magnet/insert seats (the component is a fixed size) |
| | Minimum printable feature (~1.5 mm) |

A model scaled down 50% with its screw bosses scaled too now has M1.5 bosses
holding M3 screws. Keep component-driven dimensions fixed and let the body
absorb the change.
