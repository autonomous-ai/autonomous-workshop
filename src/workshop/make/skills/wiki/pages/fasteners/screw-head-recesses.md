---
title: Screw head recesses — counterbores and countersinks
tags: [counterbore, countersink, socket-head, button-head, flat-head, iso-4762, iso-7380, iso-10642]
aliases: [cap screw pocket, head recess, spotface, csk, DIN 912, DIN 7991, SHCS, BHCS, FHCS]
sources:
  - ISO 4762:2004 Table 1 (preview, https://cdn.standards.iteh.ai/samples/34460/06335046afaf46fb8e84d91a3eda001d/ISO-4762-2004.pdf)
  - https://engineersbible.com/counterbore-socket-iso/ (counterbore Ø and depth for ISO 4762)
  - https://www.aspenfasteners.com/content/pdf/Metric_ISO_7380_spec.pdf (ISO 7380-1 and -2 head sizes)
  - https://www.westfieldfasteners.co.uk/Standards/ScrewBolt-SHCsk-M.pdf (ISO 10642 Table 1)
  - https://meshra.ai/blog/bolt-and-screw-holes-3d-printing (printed counterbore and countersink practice)
  - https://hackaday.com/2017/10/17/sacrificial-bridge-avoids-3d-printed-supports/ (sacrificial bridge)
related: [metric-screw-clearance-holes, overhangs-and-print-orientation, heat-set-inserts, wall-mounting-and-hanging]
updated: 2026-10-02
---

# Screw head recesses — counterbores and countersinks

A head recess is sized from the head the standard allows at its largest, plus
clearance. The screw itself comes from `stdpart`; these tables check the
recess.

## Socket head cap screws, ISO 4762

| thread | head Ø dk max | head height k max | hex key s | counterbore Ø | counterbore depth |
|---|---|---|---|---|---|
| M2 | 3.80 | 2.00 | 1.5 | 4.4 | 2.2 |
| M2.5 | 4.50 | 2.50 | 2 | 5.5 | 3.0 |
| M3 | 5.50 | 3.00 | 2.5 | 6.5 | 3.5 |
| M4 | 7.00 | 4.00 | 3 | 8.0 | 4.8 |
| M5 | 8.50 | 5.00 | 4 | 10.0 | 5.8 |
| M6 | 10.00 | 6.00 | 5 | 11.0 | 6.8 |
| M8 | 13.00 | 8.00 | 6 | 15.0 | 8.8 |

Head height equals the thread diameter. Knurled heads may be larger (M3 up to
5.68, M8 up to 13.27), so a tight recess measures the actual screw. Printed
practice: make the bore about 1 mm over the head, and the depth the head height
for flush (M3 6.5 × 3.0, M4 8.0 × 4.0, M5 9.5 × 5.0). Add depth for a washer or
to sink the head below the surface.

## Recess datums on curved skins

An enclosure's global rear coordinate is not the local exterior at every
opening. Intersect the actual B-rep with the proposed screw or opening axis
at its station, then derive the recess from that skin point. For a screw,
subtract the standard object's head height and the desired depression to
find its under-head datum; derive both the shaft and head clearances from
that same object.

The same rule applies to cable and strap recesses: a cutter starting beyond
the local skin can silently cut nothing while the smaller through-hole and
global silhouette still pass. Give the larger recess its own measured
end-wall or boundary landmark, independently of the through-opening.

## Button heads, ISO 7380

| thread | 7380-1 head Ø | 7380-2 (collar) head Ø | head height | hex key |
|---|---|---|---|---|
| M3 | 5.7 | 6.9 | 1.65 | 2 |
| M4 | 7.6 | 9.4 | 2.2 | 2.5 |
| M5 | 9.5 | 11.8 | 2.75 | 3 |
| M6 | 10.5 | 13.6 | 3.3 | 4 |
| M8 | 14 | 17.8 | 4.4 | 5 |

Button heads take a smaller hex key than a cap screw of the same thread. The
collared -2 form has a larger bearing face, which spreads the clamp load on
plastic.

A slot a screw head passes through and then slides under:
[[wall-mounting-and-hanging]].

## Countersunk heads, ISO 10642

90° head angle. Countersink to the theoretical maximum head diameter.

| thread | dk theoretical max | dk actual min | k max | hex key |
|---|---|---|---|---|
| M2 | 4.70 | 3.70 | 1.35 | 1.3 |
| M2.5 | 5.88 | 4.80 | 1.69 | 1.5 |
| M3 | 6.72 | 5.54 | 1.86 | 2 |
| M4 | 8.96 | 7.53 | 2.48 | 2.5 |
| M5 | 11.20 | 9.43 | 3.1 | 3 |
| M6 | 13.44 | 11.34 | 3.72 | 4 |
| M8 | 17.92 | 15.24 | 4.96 | 5 |

Socket countersunk screws are considered to have reduced loadability compared
with other head types (ISO 898 / ISO 3506, as the Westfield specification
notes). A printed countersink at 45° per side needs no support when the head
faces up.

## Printing a counterbore on its ceiling

A counterbore that opens downward (head on the bed side) leaves the smaller
through-hole starting in mid-air over the larger bore, and a printer cannot
draw a circle in mid-air. The support-free fix is a **sacrificial bridge**:
close the hole with a thin solid layer at the counterbore ceiling so the
printer first lays a flat bridge, print the round hole on top, then drill or
poke through the skin after printing. The bridge itself follows
[[overhangs-and-print-orientation#bridge-ledge-overhang]].

## Checks

```python
assert cbore_d >= CBORE_D[size], "counterbore below the table value (about head + 1 mm)"
assert cbore_depth >= K_MAX[size], "head stands proud of the surface"
```
