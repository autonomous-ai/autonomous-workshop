# Moon-Moth Bloom CAD specification

## Intent and datums

This source-first model implements the sealed Invent r0002 correction as exactly
three separately printed rigid parts: one chassis, one left wing/control, and
one right wing.  The chassis assembly datum is the centre of its floor at
Z=0.  The wing local datum is its journal axis in the print bed plane.  +Z is
up; operating rotation is in XY.

The paired journal axes are at X=-9 and +9 mm, Y=-7.5 mm.  Both complete
module-1, 18-tooth gears use a 9 mm pitch radius and rounded 1.9 mm tooth
lobes on the exact angular pitch, avoiding sub-nozzle involute tips.  The
right gear carries the half-pitch phase required for external
mesh; assembly motion is left +q and right -q.  The product has no purchased
hardware and no functional electrical load.

## Sealed repair geometry

| Feature | Value |
| --- | ---: |
| seated moving stack | Z=4.5 to 7.5 mm |
| raised service stack | Z=5.7 to 8.7 mm |
| operating roof underside | Z=8.0 mm |
| service hood underside | Z=9.2 mm |
| paired drop | q=78 degrees, -1.2 mm Z |
| raised stop crossing | q=82 degrees |
| operating roof entry | nominal q=76 degrees, seated |
| journal post / running bore | 5.0 / 5.6 mm |
| mushroom flange / keyhole lobe | 7.4 / 7.8 mm |
| printable neck | 0.9 mm minimum, two 0.4 mm nozzle lines plus margin |

Four smooth low capture buttons descend from each high canopy at q=20, 41,
62, and 68 degrees.  The q=76 inspection pose is therefore seated and fully
past the final solid entry even at either backlash extreme.  At q=78 the
raised neck has cleared every Z=8.0 button; overlap with the high hood is permitted
because its underside is Z=9.2, 0.5 mm above the raised part.  This is the
exact geometric change that prevents the r0001 0.7 mm roof collision.

## Manufacturing plan

All printable entries return one positive-volume solid in support-free bed
pose at Z=0.  The chassis floor, journal shelves, central posts, circular high
canopies, and stout low capture buttons are one fused body.  Each wing is one fused gear/neck/petal body
with through keyhole and star apertures.  No support, glue, fastener, flexure,
or snap is part of the design intent.

## Component search record

The mandatory step.parts search for `module 1 18 tooth spur gear` could not
reach `api.step.parts` from the frozen sandbox (DNS unavailable), and a second
public-index search returned no indexed result.  This is recorded as
inconclusive, not as a catalog miss.  The gears are therefore purpose-built
integral printed geometry, not stand-ins for purchased parts.

## Evidence boundary

CAD checks can establish source identity, solid and mesh validity, nominal
clearances, sampled rigid-body non-intersection, thickness, print pose, and
the stated service Z sequence.  They cannot prove a successful physical print,
fit, friction, force, wear, cycle life, child safety, or human discovery.
