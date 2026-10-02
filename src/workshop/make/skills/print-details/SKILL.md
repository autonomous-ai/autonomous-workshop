---
name: print-details
description: Add printable decorative detail to a Component - rivets, round bosses, low domes, raised bands and rims, half-round pipe ribs, inset panels, lancet windows, grille slits and teardrop bores - and blunt its points, chisels, keels and rib ends to a land one print minimum across, from a library whose every feature refuses a size below the wiki's print limits for the run's nozzle and prints without support in its declared print direction. Use it instead of modelling surface detail or a sharp edge by hand.
---

# Printable detail

Hand-modelled detail was the main source of print-gate failures in Spark
Make: in one run 64 of 111 component rounds failed `check_thickness` or
`check_overhang`, on thin tapers at the edges of decorative cones and bands,
overhangs under discs and rims, and broken solids from overlapping trims.
Each feature here is built so it cannot make those: it refuses a size below
the wiki's limits, grows a root into the host, gives every face that would
look down a 52 deg slope, ends in a step or a chamfer, and returns one valid
solid or raises `PrintLimitError` naming the limit and its wiki page.

## Install (Workshop Manager)

The library must live inside the CAD project, so the sealed project still
builds when the host copies it elsewhere. Copy it once, with the shared
files, before spawning any Component Worker:

```sh
"$WORKSHOP_PYTHON" .agents/skills/print-details/scripts/print_details.py --install <cad-project>
```

It writes `<cad-project>/features/print_details.py`, byte for byte, and
refuses to overwrite a copy with other bytes. It is a standard element, like
a `stdpart` gear: never edit the copy. Tell each worker it is there.

## Use (Component Worker)

```python
from build123d import Box, Pos
from features import print_details

pd = print_details.Details(nozzle=0.4)      # the run's nozzle; up=(0, 0, 1)

def gen_step():
    body = Pos(0, 0, 10) * Box(30, 30, 20)
    body = pd.rivets(body, pd.along((-10, -15, 18), (10, -15, 18), 6), d=2.4, h=0.8)
    body = pd.panel(body, (0, -15, 10), width=8, height=8, depth=0.8, arch="lancet")
    body = pd.band(body, pd.segment((-14, -15, 3), (14, -15, 3)), width=2.0, height=1.0)
    return body
```

Each call takes the host solid and returns the new one. A point is on the
host's surface; the feature stands on the nearest face along its outward
normal. `up` is the print direction in your generator's coordinates: +Z when
`gen_step()` returns the part in its print stance, as it should.

| Call | Makes | Defaults (mm) |
|---|---|---|
| `boss(host, at, d, h)` | a round boss with a flat top | 4, 1.5 |
| `rivet(host, at, d, h)` / `rivets(...)` | a boss with a chamfered top; `at` may be a list | 3, 1 |
| `dome(host, at, d, h)` | a low spherical cap | 8, 1.2 |
| `band(host, path, width, height)` | a raised band, chamfered on top | 2, 1 |
| `rim(host, axis, radius, width, height)` | a band standing on the face across `axis` | 2, 1 |
| `pipe(host, path, d)` | a half-round pipe rib | 1.5 |
| `panel(host, at, width, height, depth, arch)` | an inset panel, `flat` or `lancet` topped | 8, 12, 0.8 |
| `window(host, at, width, height, depth, arch)` | a window through a wall `depth` thick, `lancet`, `gable` or `flat` | 4, 10, 2 |
| `slit(host, at, width, length, depth, through)` / `slits(...)` | a grille slit running uphill; `at` may be a list | 1.2, 8, 1 |
| `bore(host, at, d, depth, through)` | a round bore with a pointed (teardrop) roof, through a wall, a vault or a pointed roof | 3, 2 |
| `blunt_tip(host, tip, toward, reach, back)` | a point, chisel, keel or ridge cut back to a flat land one print minimum across | 6, 12 |
| `rib_end(rib, end, toward, reach)` | a rib you built cut square at `end` (ramped if it would look down), before you fuse it | whole rib |

Paths and patterns: `pd.segment(start, end)` (a straight run on one face),
`pd.ring(axis, radius, normal="radial"|"axial")` (round a wall, or on a face
across the axis), `pd.around(axis, radius, count, z=...)` and
`pd.along(start, end, count)` (points for `rivets` and `slits`). `angle`
turns a cut about the normal; on a wall a blind cut turns only in quarter
turns of a flat outline, and an arch always points up.

What each feature does where the print would hang:

- a boss or rivet on a wall gets its shoulder disc swept down into the host
  at 52 deg underneath it, a small drip below it;
- a band or pipe drafts only the flank that faces down, so it is wider at the
  foot on that side; a straight band's downhill end is ramped;
- an inset panel or blind slit on a wall has its upper wall sloped outward at
  52 deg, so its mouth is taller than its floor;
- a window or through slit needs a pointed top; a lancet's arcs give way to
  straight 52 deg flanks before its apex;
- a low dome on a wall must meet the surface at 38 deg or less; the error
  gives the height that fits.

## Blunt free edges

`check_thickness` counts every straight knife edge as a wall: a chisel wing
tip, the ridge of a pointed vault, a keel, a feather tapered to nothing or an
offset rib that runs out in a sliver fails the round however the numbers are
tuned. The rule, which every Design Contract carries: **every point, chisel,
keel and V underside ends in a flat land at least one print minimum across**
(0.8 mm at a 0.4 nozzle). The print minimum comes from the nozzle, never from
a geometry's `wall_min_mm`, which sizes load-bearing sections.

- `pd.blunt_tip(host, tip, toward)` finds where the host first spans one
  minimum wall across, back from `tip` along `-toward`, and cuts it square
  there. `reach` is how far sideways the cut goes: cover the whole edge of a
  chisel or ridge (`reach=12` for a 20 mm ridge). A land that would face down
  off the bed is refused: turn the part so the tip points up or sideways, or
  rests on the bed.
- `pd.rib_end(rib, end, toward)` trims a rib, fin or offset layer you
  modelled yourself at `end`, before you fuse it to the host, so no sliver is
  left where a trim ran out. It refuses an end face narrower than one
  minimum wall.
- Never chamfer an edge to less than one minimum wall, and never ask a
  chamfer to meet a face in a knife edge.

## When a print gate fails

Every feature this library makes is tagged with the line that called it.
`check_thickness` and `check_overhang` name the tagged feature nearest each
failing region (`at feature band@part_wing.step.py:42 -- band-2 ...`), else
the nearest B-rep face, and say how far the region is past the limit. A tag
is where the feature was made, so add detail to the body in the pose
`gen_step()` returns; detail moved after it is made is named by face only.
Repair that feature: resize it, move it, or blunt the edge beside it. If the same
feature fails the next round too, `make_round` reports it as a repeated
print defect; read the report row before changing numbers again.

## Limits

`--limits [--nozzle N]` prints them for another nozzle. At 0.4 mm:

| Limit | Value | Wiki page |
|---|---|---|
| minimum wall, top flat or crest | 0.80 mm | `printing/wall-thickness-and-hollowing.md` |
| rivet, boss or dome across | 2.00 mm | `printing/fdm-minimum-feature-sizes.md` |
| raised band, rim or rib across | 0.90 mm | `printing/fdm-minimum-feature-sizes.md` |
| raised detail high | 0.50 mm | `printing/fdm-minimum-feature-sizes.md` |
| slit, groove or gap across | 0.50 mm | `printing/fdm-minimum-feature-sizes.md` |
| inset or engraved cut deep | 0.50 mm | `printing/fdm-minimum-feature-sizes.md` |
| material between two cut copies | 1.60 mm | `printing/wall-thickness-and-hollowing.md` |
| steepest face looking down | 45 deg gate, designed to 38 | `printing/overhangs-and-print-orientation.md` |

The Component Reviewer asks for detail within the same limits. A detail the
reviewer wants smaller than these cannot print: leave it out and say so in
your report rather than modelling it by hand.

## Rules

- A `PrintLimitError` is the repair: read the limit it names and change the
  size, the spot or the shape. Do not rebuild the refused feature by hand;
  the gates would fail it in the round instead.
- Put detail on the Component's own faces, clear of its edges. A feature
  whose footprint runs off the face, or where the host curves away more than
  its height, is refused.
- Two features that overlap are one solid only if the union is valid; the
  call raises otherwise. Space copies with the pattern helpers, which check
  the gap.
- Text, logos and knurling are not here; the wiki covers them
  (`modeling/text-patterns-and-surface-detail.md`).

## Self-check

```sh
"$WORKSHOP_PYTHON" .agents/skills/print-details/scripts/print_details.py --self-check [--nozzle 0.4] [--overhang-angle 45]
```

It checks that every size below a limit is refused with its limit and page,
then builds every feature at its minimum and default sizes, on a top face
and on a wall, imports the library from an installed copy, and runs the cad
skill's own `check_thickness --nozzle` and `check_overhang --angle` on each.
It exits non-zero on any failure. The Workshop test suite runs it; you need
not run it in a product run.
