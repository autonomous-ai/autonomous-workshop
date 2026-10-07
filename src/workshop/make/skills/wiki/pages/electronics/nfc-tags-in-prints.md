---
title: NFC tags sealed in a print
tags: [nfc, ntag213, ntag215, rfid, tag, transponder, pause, embed, keychain]
aliases: [nfc sticker, nfc tag, ntag, rfid tag, nfc inlay, tap to unlock, tap to pay, nfc keychain, nfc token, nfc coin]
sources:
  - https://rfid.it/en/avery-dennison/403-nfc-stickers-ntag213-round-o18mm.html (Circus NTAG213 mini: 18 +/-0.2 mm label, 16 mm antenna, 136 um overall excluding the IC, clear PET and aluminium, not for metal surfaces)
  - https://github.com/autonomous-ai/autonomous-key (an app that pairs by the tag's factory UID accepts any NTAG213/215/216)
  - https://makerworld.com/models/1058791 (keychain with a print pause built in for an NTAG chip)
  - https://www.digitaltransactions.net/cash-app-tags-debut-starting-with-a-wand/ (a commercial NFC wand, 4.29 x 1.71 in)
  - "experience: a tag on the mid-plane of a 13 mm thick two-half token sat 5.3 mm under one face and 13.7 mm under the other face's ornament; sealed under the tap face it sits 1.75 mm deep"
related: [magnets-and-strap-slots, wall-thickness-and-hollowing, overhangs-and-print-orientation, electrical-component-selection, printed-part-count]
updated: 2026-10-05
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
  On-metal tags exist with a ferrite backing and are thicker.

## Read distance decides where it goes

- Range falls with distance and shrinks with antenna size, and the small tags
  that fit a keychain have the least to spare. Keep the tag within about
  2 mm of the face the user taps; a printed key token keeps it near 1 mm.
- **Never centre it in a thick part.** A two-half print invites the tag on the
  split plane, which leaves it half the thickness from both faces, and an
  ornament on one face (a gem, a boss) adds its height to that side.
- Put it under one face and **mark that face** — a logo or glyph directly
  over the antenna — because nobody knows where the antenna is.
- Plastic does not shield it; the distance does. Thick infill over the tag is
  harmless, a thick part is not.

## Sealing it: pause and embed

Seal it inside one printed part by pausing the print
([[magnets-and-strap-slots#pause-and-embed]]):

- Cavity diameter `slot_for(label max diameter, "slip")`; height two layers
  (0.4 mm at 0.2 mm layers) for a 0.35 mm sticker envelope.
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

## Failure classes

| Failure | What it looks like | Rule that prevents it |
|---|---|---|
| Buried tag | the phone reads only when pressed hard, or never | within about 2 mm of the tap face |
| Wrong face | users tap the ornament side and nothing happens | tag under one face, that face marked |
| Detuned tag | reads off the part, not in it | no metal over or beside the antenna |
| Sagged roof | a dent or hole over an open bed-face pocket | sealed cavity at a pause, never a bed-face pocket |
| Thin roof | the tag outline shows through or the roof splits | roof checked at the footprint's lowest point |
