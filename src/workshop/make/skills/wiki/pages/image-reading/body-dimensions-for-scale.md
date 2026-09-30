---
title: Human body dimensions for scaling photos
tags: [anthropometry, scale, hand, finger, stature, reference-object, percentile]
aliases: [hand size, finger width, hand length, hand breadth, adult height, interpupillary distance, ipd, ansur]
sources:
  - https://hf.tc.faa.gov/hfds/download-hfds/hfds_pdfs/App_B_Tech_Ops_Anthropometrics.pdf
  - https://en.wikipedia.org/wiki/Pupillary_distance
  - https://www.roymech.co.uk/Useful_Tables/Ergonomics/Human_sizes.html
related: [known-object-sizes, scale-anchors, handheld-ergonomics, single-view-metrology]
updated: 2026-09-23
---

# Human body dimensions for scaling photos

A hand holding the object is the most common scale reference in a product
photo, and the least precise. These are published anthropometric values, so
the scale you take from a hand has a known spread. The coarse palm and finger
rows in [[known-object-sizes]] agree with them.

## Hands and fingers (adults)

FAA Technical Operations anthropometric survey (US adults), in mm:

| dimension | how measured | men 5th / 50th / 95th | women 5th / 50th / 95th |
|---|---|---|---|
| hand length | wrist crease (stylion) to middle fingertip | 180 / 196 / 212 | 163 / 178 / 193 |
| hand breadth | across the knuckles (metacarpal-phalangeal joints) | 80 / 88 / 96 | 71 / 77 / 84 |
| index finger length | tip to the crease at its base | 67 / 74 / 82 | 62 / 69 / 76 |
| index finger breadth | at the middle joint (PIP) | 19 / 21 / 23 | 16 / 18 / 21 |

British adults (Pheasant and Haslegrave, *Bodyspace*, via RoyMech) give hand
length 170 / 190 / 210 mm (men) and 160 / 175 / 190 mm (women), and hand
breadth 80 / 90 / 100 and 70 / 80 / 90 mm, the same within ~5 %.

## Whole body and face

| dimension | men 5th / 50th / 95th | women 5th / 50th / 95th | source |
|---|---|---|---|
| stature | 1647 / 1767 / 1876 mm | 1516 / 1626 / 1731 mm | FAA survey |
| interpupillary distance | mean 64.0 mm, range 53–77 (SD 3.4) | mean 61.7 mm, range 51–74.5 (SD 3.6) | 2012 US Army survey (ANSUR II) |

## How much to trust a body reference

- The 5th–95th spread of hand length is about ±8 % around the median.
  Without knowing whose hand it is, a hand-scaled dimension is `[inferred]`
  with at least ±10 % uncertainty; state it that way ([[scale-anchors]]).
- Measure the body part at the object's depth. A hand in front of the object
  is drawn larger than the object's plane
  ([[camera-model-and-focal-length#size-is-inversely-proportional-to-distance]]).
- Measure between landmarks that match the definition: hand length runs from
  the wrist crease, not the wrist edge; finger breadth is at the middle joint,
  not the tip.
- A child's hand, a gloved hand or a model's hand (often small) breaks the
  table; say so when you suspect it.
- Stature needs a full standing figure and is best used with single-view
  metrology on the ground plane ([[single-view-metrology]]).

The same tables size things the object must fit — grips, buttons, finger
openings — in [[handheld-ergonomics]].
