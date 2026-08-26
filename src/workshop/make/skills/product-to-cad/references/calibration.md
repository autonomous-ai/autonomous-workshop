# Printer and material calibration

There is no universal printable clearance, wall, bridge, thread, snap, or
detent value. Treat nominal numbers as a coupon search space until evidence is
bound to the exact printer, nozzle, layer height, extrusion width, material,
slicer, orientation, and ambient/process settings.

## Minimum calibration record

Record printer and firmware identity, nozzle, measured extrusion width, layer
height, material brand/batch/conditioning, slicer and complete profile hash,
coupon source/artifact hashes, orientation, measurement tool, measurements,
operator, timestamp, photos, failures, and the accepted interval. A change to
any controlled input invalidates the calibration for release.

## Starting exploration bands for 0.4 mm FDM

These are coupon ranges, not accepted defaults:

- radial or planar running clearance: 0.15–0.35 mm per side;
- sliding/key clearance: 0.10–0.30 mm per side;
- printed thread flank clearance: 0.15–0.35 mm per side;
- structural walls: explore at least 3–4 actual extrusion widths;
- embossed/debossed strokes: explore from 2 extrusion widths;
- bridges, overhangs, snap deflection, detents, hinges, and press fits: build a
  geometry- and orientation-specific matrix rather than transferring a value.

Include both sides of each mate on the same coupon. Select the widest interval
that meets the product requirement, not the single specimen that happened to
work. Never use sanding, drilling, heat, or force to turn a failed coupon into a
pass unless that post-process is explicitly part of the manufacturing contract.

## Bounded loop

Declare coupon rounds, material, machine time, money, and full-assembly revision
limits before printing. Preserve every failed receipt. When the bound is spent,
return `no viable artifact` or change the manufacturing contract explicitly;
do not silently relax the acceptance criteria.
