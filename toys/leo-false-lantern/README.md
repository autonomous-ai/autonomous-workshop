# False Lantern

A compact two-player firefly signaling duel invented by Leo and completed by
the Codex-orchestrated Workshop flow: Wish → Match → Invent → Make ↔ Playtest →
Release.

[View the verified public product page](https://www.autonomous.ai/factory/product/false-lantern)

## Play it

`MANUAL.pdf` is the complete, self-contained in-box field guide. It teaches the
game through a scripted first exchange, then leaves the back cover usable as a
table-side quick reference. It requires no website, video, QR code, or phone.

For the physical box, print it at 100% on A6 pages in reading order. A print
shop can impose the 12 pages as a saddle-stitched booklet; office printers can
use their booklet setting on larger paper. Do not scale the pages to fill.

## Print it

1. Read [MANUAL.md](MANUAL.md), the full production and rules reference,
   especially its evidence boundary and safety sections.
2. Print `calibration/clearance-coupon.stl` first with the intended Bambu Lab
   printer, filament, nozzle, and layer profile. Measure the coupon before
   relying on any nominal clearance.
3. Slice the six files in `print/` separately in their exported orientation.
   The game uses one of each file. Supports were disabled in the generic Orca
   validation, but this snapshot deliberately contains no machine-specific
   G-code; generate fresh Bambu-specific jobs locally.
4. Inspect every part and confirm lid fit, screen stability, readable marks,
   smooth motion, and the absence of loose or sharp fragments before play.

Digital validation covered all six exact STLs, rules replay, mechanical
envelopes, and generic-profile OrcaSlicer jobs. It did not prove a physical
print, Bambu-specific settings, calibrated fit, durability, or human response.

## Snapshot contents

- `product.json` — the exact public Release page contract.
- `MANUAL.pdf` — the finished printable customer guide that goes in the box.
- `MANUAL.md` — complete rules and production reference in accessible text.
- `PUBLICATION.json` — sanitized Factory verification and content identities.
- `print/*.stl` — the six exact printable game components.
- `calibration/clearance-coupon.stl` — the exact clearance coupon referenced by
  the manual; it is not a seventh game component.
