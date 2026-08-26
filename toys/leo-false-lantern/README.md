# False Lantern

A compact two-player firefly signaling duel invented by Leo and completed by
the Codex-orchestrated Workshop flow: Wish → Match → Invent → Make ↔ Playtest →
Release.

[View the verified public product page](https://www.autonomous.ai/factory/product/false-lantern)

## Print it

1. Read [MANUAL.md](MANUAL.md), especially the evidence boundary and safety
   sections.
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
- `MANUAL.md` — complete setup, rules, printing, assembly, care, and safety.
- `PUBLICATION.json` — sanitized Factory verification and content identities.
- `print/*.stl` — the six exact printable game components.
- `calibration/clearance-coupon.stl` — the exact clearance coupon referenced by
  the manual; it is not a seventh game component.
