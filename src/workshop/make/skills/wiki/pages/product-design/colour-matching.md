---
title: Colour matching and colour systems
tags: [colour, color, ral, pantone, delta-e, white-balance, filament, appearance]
aliases: [colour difference, cielab, ciede2000, grey card, colour checker, filament colour, color matching]
sources:
  - https://en.wikipedia.org/wiki/RAL_colour_standard
  - https://en.wikipedia.org/wiki/Color_difference
  - https://en.wikipedia.org/wiki/Pantone
  - https://en.wikipedia.org/wiki/Color_balance
  - https://www.pixelz.com/blog/need-accurate-color-let-grey-cards-white-balancing-come-rescue/
  - https://fastershape.com/blogs/random/understanding-filament-color-transmission-for-lamp-and-light-design
related: [form-and-finish-heuristics, measuring-reference-photos, organic-likeness, post-processing-and-finishing]
updated: 2026-10-02
---

# Colour matching and colour systems

Colour is part of likeness, and a printed part's colour is the filament's.
This page covers how colours are named, how differences are measured, and
why a colour picked from a photo is only an estimate.

## Naming a colour

- **RAL Classic**: four-digit codes; the first digit is the hue group
  (1 yellow, 2 orange, 3 red, 4 violet, 5 blue, 6 green, 7 grey, 8 brown,
  9 white and black). About 216 colours in the current RAL 840-HR set, used for
  paints, powder coating and plastics. RAL Design System: seven digits
  encoding hue (0–360°), lightness and chroma in CIELAB-based HLC, about 1825
  colours.
- **Pantone Matching System**: a proprietary naming system (2,161 colours as
  of 2019) used across graphic, product and textile design so a colour matches
  whatever equipment produces it. About 30 % of its spot colours cannot be
  printed in CMYK, and many lie outside sRGB, so a Pantone colour on screen is
  already an approximation.
- A named colour (RAL, Pantone, a maker's filament name) is a better colour
  record than an RGB value sampled from a photo, because it names a physical
  sample.

## Measuring a difference

Colour difference is measured in CIELAB, never in RGB (RGB is
device-dependent and not perceptually uniform):

```text
ΔE*ab (CIE76) = sqrt(ΔL*² + Δa*² + Δb*²)
```

- ΔE*ab ≈ 2.3 is about one just-noticeable difference. CIEDE2000 (ΔE00)
  corrects CIE76's non-uniformity (neutrals, lightness, chroma, hue, and the
  blue region) and is the formula to use.
- A ΔE is only meaningful under a stated illuminant (D65 for most colour work,
  D50 in printing).

## A photo is a poor colour reference

- A camera's sensor does not match the eye, so every photo's colours are
  transformed for display, and the camera chooses that correction from the
  scene lighting: manually, by automatic white balance (an estimate), or by a
  custom balance. The same object photographed under two lights records two
  colours.
- A grey card (or any neutral object) placed where the subject is and
  photographed under the same light gives the reference: neutral must come out
  neutral. White-balance on it before sampling.
- Sample a flat, evenly lit area away from highlights and shadows, and
  average a patch rather than one pixel.

Record a photo-sampled colour as `[inferred]` and say whether it was
white-balanced.

## Filament appearance

- Filaments that look identical in reflected light can transmit different
  colours when backlit (one glowing white, another lavender), because
  pigments and additives differ between suppliers. Confirm lamp and
  light-pipe colours with a backlit printed sample.
- Transmitted light depends on how the part is printed: thin vertical walls
  pass more light but show layer lines and uneven diffusion, the bed face
  transmits less because it is denser, and top surfaces vary with the infill
  beneath them.
- A colour chosen on screen is not the printed colour: screens show sRGB, and
  filament colours are physical samples.

## In the model

Choose the colour from stock filaments rather than an arbitrary RGB, name
it, and assign it per region (the repository's `cadfilament` helper exists for
this). Colour regions are a likeness decision; see [[organic-likeness]] for
region splitting on figures.

Software review renderers must keep the colour and coordinate contracts:

- `cadgen.srgb` and `cadfilament.filament` give linear-light channels. Apply
  lighting in linear light, then encode sRGB before writing PNG pixels;
  writing the linear values directly makes ivory brown and darkens colours.
- Traverse coloured leaves inside nested assemblies. A module-level fallback
  colour can otherwise replace black glass and coloured artwork.
- A leaf's tessellation carries its own transform. Apply the accumulated
  ancestor placement too; dropping it can draw a display at the origin while
  the whole-assembly silhouette still passes.

Colour and placement regression fixtures must include a transformed nested
compound, not just coloured top-level primitives.

Splitting a part so each colour can be painted separately:
[[post-processing-and-finishing]].
