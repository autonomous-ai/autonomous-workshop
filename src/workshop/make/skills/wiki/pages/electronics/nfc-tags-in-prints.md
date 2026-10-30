---
title: NFC tags sealed in a print
tags: [nfc, ntag213, ntag215, rfid, tag, transponder, pause, embed, keychain]
aliases: [nfc sticker, nfc tag, ntag, rfid tag, nfc inlay, tap to unlock, tap to pay, nfc keychain, nfc token, nfc coin]
sources:
  - "https://rfid.it/en/avery-dennison/404-hf-midas-wet-inlay-nxp-ntag213-12x19.html (Midas NTAG213 12 x 19 mm, ref 3002647, 10 x 17 antenna, 157 um)"
  - https://rfid.it/en/avery-dennison/403-nfc-stickers-ntag213-round-o18mm.html (Circus NTAG213 mini: 18 +/-0.2 mm label, 16 mm antenna, 136 um overall excluding the IC, clear PET and aluminium, not for metal surfaces)
  - NXP NTAG213/215/216 product data sheet (one IC family: 144 / 504 / 888 bytes of user memory, the same 7-byte factory UID)
  - https://makerworld.com/models/1058791 (keychain with a print pause built in for an NTAG chip)
  - https://www.digitaltransactions.net/cash-app-tags-debut-starting-with-a-wand/ (a commercial NFC wand, 4.29 x 1.71 in)
  - "experience: a tag on the mid-plane of a 13 mm thick two-half token sat 5.3 mm under one face and 13.7 mm under the other face's ornament; sealed under the tap face it sits 1.75 mm deep"
related: [magnets-and-strap-slots, wall-thickness-and-hollowing, overhangs-and-print-orientation, electrical-component-selection, printed-part-count, key-rings-and-charm-hardware]
updated: 2026-10-10
---

# NFC tags sealed in a print

A passive NFC tag is the cheapest "electronics" a print can carry: no battery,
no wire, no switch. Its failure modes are all placement — too deep, next to
metal, or in a pocket the printer cannot close — and no geometry gate sees any
of them.

## What the tag is

- A passive 13.56 MHz transponder, powered by the reader's field. Nothing in
  the print is powered, so it needs no power manifest.
- NTAG213 (144 bytes), NTAG215 and NTAG216 differ in memory only. An app that
  identifies the object by the tag's factory UID accepts any of them, so the
  form factor is free to follow the object: round stickers are sold at 18, 22,
  23, 25, 27 and 30 mm, PVC coins at 25 and 30 mm.
- A sticker is a PET-and-aluminium inlay about 0.14 mm thick plus the IC bump;
  model it as an envelope 0.35 mm thick at the label's largest diameter
  (nominal plus tolerance). No catalog carries a STEP for one.
- **Metal detunes it.** Keep screws, magnets, inserts and the key ring away
  from the antenna; a steel split ring several centimetres away is fine.
  On-metal tags exist with a ferrite backing and are thicker. Ring hole
  size, ligament and loop orientation: [[key-rings-and-charm-hardware]].

## Read distance decides where it goes

- Range falls with distance and shrinks with antenna size, and the small tags
  that fit a keychain have the least to spare. Keep the tag within about
  2 mm of the face the user taps; a printed key token keeps it near 1 mm.
- **Never centre it in a thick part.** A two-half print invites the tag on the
  split plane, which leaves it half the thickness from both faces, and an
  ornament on one face (a gem, a boss) adds its height to that side.
- Put it under one face and **mark that face** — a logo or glyph directly
  over the antenna — because nobody knows where the antenna is.
- **A thin two-faced token is the exception to "never centre it".** When the
  part is thin enough that the tag in the middle sits within the read distance
  of both faces, centre it: either face taps, so neither needs a mark, and a
  design meant to look the same on both sides also works the same. A 1 mm tag
  under 0.6 mm colour inlays and five black layers each side makes a 4.4 mm
  slab with the tag 1.6 and 1.8 mm from the faces.
- Plastic does not shield it; the distance does. Thick infill over the tag is
  harmless, a thick part is not.
- **A through-opening and the tag compete for the same middle.** A concept
  with an open mouth or door at the centre of a flat charm leaves no disc for
  a round tag plus its wall (an 18 mm sticker in a slip pocket with 1.6 walls
  needs a solid Ø21.8). Check the pocket-plus-wall envelope against every
  opening before accepting the layout. A rectangular 12 × 19 inlay (Avery
  Dennison Midas NTAG213, 10 × 17 antenna, about the area of an 18 mm round
  tag's 16 mm antenna) fits the band above such an opening; otherwise the
  opening becomes a recess.
- **A 20 × 10 tag needs a solid 23.8 × 13.8 rectangle**: the slip pocket
  (20.6 × 10.6) plus 1.6 of wall each side, and about 4 mm from its edge to
  any metal ring hole. A narrower member holds no tag. Where a ring hole and
  an opening crowd the same region, the window left between them can be a few
  tenths over the pocket: size that window first, because it decides whether
  the pocket lies across or along, whether a locating peg can stay on the
  axis, and whether an opening has to move.

## Sealing it: pause and embed

Seal it inside one printed part by pausing the print
([[magnets-and-strap-slots#pause-and-embed]]):

- Cavity diameter `slot_for(label max diameter, "slip")`; height two layers
  (0.4 mm at 0.2 mm layers) for a 0.35 mm sticker envelope.
  A rigid tag (PVC, epoxy, PCB, 1 mm and up) gets a cavity one layer taller
  than its thickness.
- A rectangular tag with square corners in a pocket with rounded corners:
  the corner clears only while the pocket radius is at most
  `c √2 / (√2 − 1) ≈ 3.4 c`, `c` the clearance a side. At the slip fit's
  0.2 that is 0.68; a 1.0 corner radius catches the tag's corners.
- Roof at least 1.0 mm (five layers) over the whole footprint, not just the
  centre. On a domed face, find the lowest point of the face over the tag's
  footprint, subtract the roof, and round **down** to a layer boundary: that
  is the cavity top and the pause height. Assert it from the surface, so a
  thickness change re-derives the pause.
- The tag supports the roof's first layer, so the "bridge" is over the tag,
  not over air. An open pocket in the **bed face** of a part is a bridge over
  air of the tag's full span (18 mm and more); never put the tag there.
- A sealed cavity exports as a second shell: `check_mesh` reports two shells
  and passes, the part's solid has two shells, and a local audit can assert
  exactly that as proof the cavity is closed. `check_motion` can prove the tag
  is captured with blocked sweeps in both Z directions and sideways, its
  retention resting on the part that seals it.
- Any later deboss over the tag (the face mark) must leave the full roof:
  `face height - mark depth - cavity top >= roof`.
- A part printed as two glued halves needs no pause: pocket the tag in the glue
  face, half its depth in each half, and drop it in before gluing. Each half
  prints its pocket open upward, so the floors are solid layers rather than a
  bridge. Keep each floor 1.0 mm all the same: `check_thickness` measures a
  0.8 mm (two-line) floor as 0.73 at its voxel and fails it. A 1 mm tag in a
  1.2 mm pocket with a 1.0 mm floor each side makes the part 3.2 mm at least.

## Failure classes

| Failure | What it looks like | Rule that prevents it |
|---|---|---|
| Buried tag | the phone reads only when pressed hard, or never | within about 2 mm of the tap face |
| Wrong face | users tap the ornament side and nothing happens | tag under one face, that face marked |
| Detuned tag | reads off the part, not in it | no metal over or beside the antenna |
| Sagged roof | a dent or hole over an open bed-face pocket | sealed cavity at a pause, never a bed-face pocket |
| Thin roof | the tag outline shows through or the roof splits | roof checked at the footprint's lowest point |
