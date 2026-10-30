---
title: Screw head recesses — counterbores and countersinks
tags: [counterbore, countersink, socket-head, button-head, flat-head, iso-4762, iso-7380, iso-10642]
aliases: [cap screw pocket, head recess, spotface, csk, DIN 912, DIN 7991, SHCS, BHCS, FHCS]
sources:
  - ISO 4762:2004 Table 1 (preview, https://cdn.standards.iteh.ai/samples/34460/06335046afaf46fb8e84d91a3eda001d/ISO-4762-2004.pdf)
  - skills/cad/scripts/stdpart (bd_warehouse screw_data and counterbore width)
  - https://www.aspenfasteners.com/content/pdf/Metric_ISO_7380_spec.pdf (ISO 7380-1 and -2 heads, hex key)
  - https://www.westfieldfasteners.co.uk/Standards/ScrewBolt-SHCsk-M.pdf (ISO 10642 Table 1)
  - https://meshra.ai/blog/bolt-and-screw-holes-3d-printing (printed counterbore and countersink practice)
  - https://hackaday.com/2017/10/17/sacrificial-bridge-avoids-3d-printed-supports/ (sacrificial bridge)
related: [metric-screw-clearance-holes, overhangs-and-print-orientation, heat-set-inserts, wall-mounting-and-hanging]
updated: 2026-10-10
---

# Screw head recesses — counterbores and countersinks

A head recess is sized from the head the standard allows at its largest, plus
clearance. The screw comes from `stdpart`, and its `bd_warehouse` object
carries the head: `screw.head_diameter`, `screw.head_height` and
`screw.screw_data` (`dk`, `k`, socket `s`; `dc` for a collar). Cap and button
heads are read from it, not copied here.

## Counterbores for socket head cap screws

ISO 4762 head height equals the thread diameter. The library's `dk` is the
knurled-head maximum (M3 5.68, M8 13.27), above the smooth head's 5.50 and
13.00, so a recess derived from it takes either head. Its own counterbore
(`ClearanceHole(..., counter_sunk=True)`) is `dk + (clearance − d)` wide —
only 0.6 mm over the head for M3 at `Loose` — which is a machined fit, not a
printed one. Printed practice: make the bore about 1 mm over the smooth head,
which is about 0.8 mm over the library's knurled `dk`, and the depth the head
height for flush (M3 6.5 × 3.0, M4 8.0 × 4.0, M5 9.5 × 5.0). Add depth for a
washer or to sink the head below the surface.

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

Button heads (`ButtonHeadScrew`) take a smaller hex key than a cap screw of
the same thread. The collared ISO 7380-2 form (`ButtonHeadWithCollarScrew`,
collar `dc`) has a larger bearing face, which spreads the clamp load on
plastic.

A slot a screw head passes through and then slides under:
[[wall-mounting-and-hanging]].

## Countersunk heads, ISO 10642

90° head angle. Countersink to the theoretical maximum head diameter. This
table stays because the library does not carry it: `CounterSunkScrew(...,
fastener_type="iso10642")` starts at M3 and holds a nominal `dk` and `k`
(M3 6.0 and 1.7), and its countersink profile is cut to those, below the
theoretical maximum a head may reach.

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
screw = SocketHeadCapScrew(size, length, simple=True)       # bd_warehouse, via stdpart
assert cbore_d >= screw.head_diameter + 0.75, "printed counterbore under knurled head + 0.75 mm"
assert cbore_depth >= screw.head_height + sink, "head stands proud of the surface"
assert csk_d >= DK_THEORETICAL_MAX[size], "countersink below ISO 10642 theoretical max (table above)"
```
