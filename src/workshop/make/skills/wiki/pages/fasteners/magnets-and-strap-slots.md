---
title: Magnets and strap slots as fasteners
tags: [magnet, neodymium, magnet-pocket, zip-tie, cable-tie, strap, slot]
aliases: [magnet press fit, embedded magnet, N52, N35, 6x3 magnet, cable tie slot, tie wrap, velcro strap]
sources:
  - https://meshra.ai/blog/magnet-pockets-3d-printing (press-fit and glue-in pocket sizes, walls, pause-and-embed, polarity, 80 °C rating)
  - https://kingroon.com/blogs/3d-printing-guides/how-to-embed-magnets-into-3d-prints (0.2–0.3 mm oversize press fit; via search excerpt)
  - https://wellwhisk.com/best-magnets-for-3d-printing/ (N52 vs N35; via search excerpt)
  - https://www.nylon-cabletie.com/news/what-are-the-specifications-and-dimensions-of-standard-cable-ties-teach-you-how-to-easily-choose-the-right-tie (standard tie widths; via search excerpt)
  - https://ziptie.com/blogs/blog/what-size-do-zip-ties-come-in (miniature 2.5 mm, intermediate 3.6 mm; via search excerpt)
related: [dowel-pins-and-press-fits, nut-traps-and-captive-nuts, heat-resistance-of-printed-parts, latches-detents-and-ratchets, exact-constraint-and-kinematic-mounts, straps-buckles-and-textile-attachment]
updated: 2026-09-23
---

# Magnets and strap slots as fasteners

Magnets make a removable lid or panel with no wear part; straps and cable ties
hold wires and bought parts without a designed seat.

## Magnet pockets

The 6 × 3 mm neodymium disc is the common size for printed parts: strong
enough for lids, panels and tool holders, thin enough to hide in a normal wall.
N52 is the strongest consumer grade, with roughly 50 % more pull than N35 in
the same size.

| fit | pocket diameter (6 mm magnet) | pocket depth (3 mm magnet) |
|---|---|---|
| press fit, no glue | 6.0–6.1 mm (a hole modelled at 6.0 prints about 5.8–5.9) | 3.0 mm, exactly the magnet |
| glue-in | 6.2–6.4 mm | 3.1 mm |

Sources disagree on the press fit: Meshra models nominal to +0.1 mm and relies
on the printed hole shrinking; Kingroon models +0.2–0.3 mm for a finger-press
fit. The difference is each printer's hole compensation. Print a coupon
([[dowel-pins-and-press-fits#prove-it-on-a-coupon]]).

- **Walls:** at least 1.5–2 mm (three or four perimeters) around and behind
  the pocket, so the magnet cannot blow out the side or show a bump through a
  thin skin.
- **Temperature:** N-grade discs are rated to roughly 80 °C. A printed part
  may soften first; check [[heat-resistance-of-printed-parts]].

Magnetic catches among the other latch types:
[[latches-detents-and-ratchets]].

A magnet as the preload of a kinematic mount:
[[exact-constraint-and-kinematic-mounts]].

## Polarity

Mark the face that must point out on every pocket, and check each magnet
against a reference before fitting it. A polarity mistake is cheap to fix in a
press fit and permanent in an embedded magnet.

## Pause and embed

Seal the magnet (or a nut) inside the print: stop at the layer where the
pocket closes, insert, and resume.

- End the pocket depth on a layer boundary so the pause lands exactly at the
  pocket's top.
- Cap it with two or three solid layers; 0.15–0.2 mm layers give a clean
  landing and cap.
- A buried magnet is a retained part with no removal path: record it as
  permanent.

## Cable ties and straps

Standard cable tie widths are 2.5 mm (miniature), 3.6 mm (intermediate),
4.8 mm, 7.2 mm, 9 mm and 12 mm. The label gives width × length, e.g.
4.8 × 200. Strength grows with width. One vendor rates an 8" nylon 6/6 tie at
18 lb for 2.5 mm width and 75 lb for 4.5 mm. Size a printed tie slot from the
tie actually specified, and model the slot as a clearance feature
([[fit-derivation]]). No vendor tolerance for slot size was found, so prove the
first slot on a print.

Webbing slots, buckles, adjusters and sewing flanges:
[[straps-buckles-and-textile-attachment]].
