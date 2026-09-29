---
title: ISO 2768 general tolerances
tags: [iso-2768, tolerance, general-tolerance, drawing, linear, angular, flatness]
aliases: [ISO 2768-mK, general tolerance, title block tolerance, default tolerance, untoleranced dimension]
sources:
  - https://www.rivcut.com/resources/iso-2768-tolerance-chart
  - https://qualityforum.zeiss.com/migration/images/137_8bb2b6eeb6a9e6554d254c216a890c89.pdf
  - https://www.3erp.com/blog/iso-2768-standard/
related: [iso-286-fits, gdt-basics, reading-technical-drawings, drawing-projection-conventions, tolerance-stack-up]
updated: 2026-09-23
---

# ISO 2768 general tolerances

A drawing that says `ISO 2768-mK` in or near its title block gives every
dimension without its own tolerance a default one. Part 1 (letters f, m, c, v)
covers linear and angular sizes. Part 2 (letters H, K, L) covers geometry
such as flatness. Use these tables to know how exact an untoleranced number
on a drawing really is.

## Part 1: linear dimensions, ± mm

| nominal (mm) | f fine | m medium | c coarse | v very coarse |
|---|---|---|---|---|
| 0.5 up to 3 | 0.05 | 0.1 | 0.2 | — |
| over 3 up to 6 | 0.05 | 0.1 | 0.3 | 0.5 |
| over 6 up to 30 | 0.1 | 0.2 | 0.5 | 1.0 |
| over 30 up to 120 | 0.15 | 0.3 | 0.8 | 1.5 |
| over 120 up to 400 | 0.2 | 0.5 | 1.2 | 2.5 |
| over 400 up to 1000 | 0.3 | 0.8 | 2.0 | 4.0 |
| over 1000 up to 2000 | 0.5 | 1.2 | 3.0 | 6.0 |
| over 2000 up to 4000 | — | 2.0 | 4.0 | 8.0 |

Below 0.5 mm, the deviation must be written next to the dimension.

## Part 1: external radii and chamfer heights, ± mm

| nominal (mm) | f, m | c, v |
|---|---|---|
| 0.5 up to 3 | 0.2 | 0.4 |
| over 3 up to 6 | 0.5 | 1.0 |
| over 6 | 1.0 | 2.0 |

## Part 1: angles, by the length of the shorter leg

| shorter leg (mm) | f, m | c | v |
|---|---|---|---|
| up to 10 | ±1° | ±1°30′ | ±3° |
| over 10 up to 50 | ±0°30′ | ±1° | ±2° |
| over 50 up to 120 | ±0°20′ | ±0°30′ | ±1° |
| over 120 up to 400 | ±0°10′ | ±0°15′ or ±0°20′ (sources differ) | ±0°30′ |
| over 400 | ±0°5′ | ±0°10′ | ±0°20′ |

## Part 2: straightness and flatness, mm

| nominal length (mm) | H | K | L |
|---|---|---|---|
| up to 10 | 0.02 | 0.05 | 0.1 |
| over 10 up to 30 | 0.05 | 0.1 | 0.2 |
| over 30 up to 100 | 0.1 | 0.2 | 0.4 |
| over 100 up to 300 | 0.2 | 0.4 | 0.8 |
| over 300 up to 1000 | 0.3 | 0.6 | 1.2 |

General circular run-out: H 0.1, K 0.2, L 0.5 mm. The Part 2 tables for
perpendicularity and symmetry disagree between the published summaries
consulted, so take them from the standard itself when they matter.

## Using it

- **`ISO 2768-mK` is the common machining default**: medium linear, K
  geometric. A 50 mm untoleranced length on such a drawing means 50 ± 0.3.
- **Everything critical carries its own tolerance** (an ISO 286 fit or an
  explicit ±). General tolerances are for the non-functional dimensions.
- **For a printed part**, compare the class with the FDM clearances in
  [[fit-derivation]]: below 6 mm, `m` (±0.1) is finer than a 0.2 mm-per-side
  running clearance. Treat a small feature's drawing value as a target, and
  derive the fit instead of copying it.
- **Reading a drawing to model it**: take the nominal. The general tolerance
  tells you how much a measured photo discrepancy can be forgiven
  ([[reading-technical-drawings]]).

Adding these tolerances along a chain: [[tolerance-stack-up]].
