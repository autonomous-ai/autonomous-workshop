---
title: GD&T basics for reading drawings
tags: [gdt, geometric-tolerance, datum, feature-control-frame, mmc, position, flatness, runout]
aliases: [geometric dimensioning and tolerancing, ASME Y14.5, ISO 1101, feature control frame, datum reference frame, maximum material condition, true position]
sources:
  - https://en.wikipedia.org/wiki/Geometric_dimensioning_and_tolerancing
  - https://www.rivcut.com/resources/iso-2768-tolerance-chart
related: [reading-technical-drawings, iso-2768-general-tolerances, iso-286-fits, drawing-projection-conventions, tolerance-stack-up, exact-constraint-and-kinematic-mounts]
updated: 2026-09-23
---

# GD&T basics for reading drawings

Geometric dimensioning and tolerancing (ASME Y14.5, ISO 1101) controls
*form, orientation, location and runout*, not just size. An agent modelling
from a drawing needs only to read it: the nominal geometry comes from the
basic dimensions, and the frames say which surfaces are functional datums.

## The characteristics

| group | characteristics | needs a datum |
|---|---|---|
| form | straightness, flatness, circularity, cylindricity | no |
| profile | profile of a line, profile of a surface | optional |
| orientation | perpendicularity, angularity, parallelism | yes |
| location | position, concentricity, symmetry | yes |
| runout | circular run-out, total run-out | yes |

## The feature control frame

A row of boxes, read left to right:

1. the characteristic symbol;
2. the tolerance zone size, with `Ø` in front when the zone is cylindrical
   (typical for hole position);
3. an optional material-condition modifier: Ⓜ maximum material condition,
   Ⓛ least material condition;
4. datum references in order: primary, secondary, tertiary.

## Datums

Datums (letters A, B, C…) are the surfaces the part is measured from, and
usually the ones it is mounted by. The datum reference frame is three
mutually perpendicular planes set up **3-2-1**: the primary datum contacts at
three points (a plane), the secondary at two (a line), the tertiary at one (a
point).

For modelling: **datum A is the mounting face**. Put the part's origin or a
named datum plane there, and position the features from it with the same
basic dimensions the drawing uses ([[parametric-design-intent#reference-stable-things]]).

Datums set where a stack-up loop starts: [[tolerance-stack-up]].

The 3-2-1 location a datum frame describes, and kinematic mounts that realise
it: [[exact-constraint-and-kinematic-mounts]].

## Material condition and bonus tolerance

- **MMC**: a feature of size holds the most material within its limits, i.e.
  the smallest hole or the largest pin. **LMC** is the opposite, used to protect
  a minimum wall.
- **Bonus tolerance**: with Ⓜ, a feature produced away from MMC gains
  positional tolerance equal to its departure from MMC. A hole made larger may
  be further off position and still assemble.
- The practical reading: Ⓜ on a hole's position means *assembly* is the
  function, and the drawing is protecting clearance for a fastener.

## Envelope versus independency

- **ASME Y14.5, Rule #1 (envelope principle)**: a feature of size may not
  exceed its MMC boundary, so size limits also control form.
- **ISO (ISO 8015, independency principle)**: size and form are independent
  unless the envelope Ⓔ is called out.

The same drawing can therefore mean different things under ASME and under
ISO. Check which standard the title block cites before inferring form from a
size tolerance.

## General geometric tolerances

A drawing that cites `ISO 2768-…K` (or H/L) applies default flatness,
straightness and run-out to features without a frame
([[iso-2768-general-tolerances#part-2-straightness-and-flatness-mm]]).
