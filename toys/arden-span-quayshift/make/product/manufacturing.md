# Manufacturing assumptions — QUAYSHIFT

This is a ten-part CAD prototype: eight architectural modules, one tray and one
ferry. Every part is one connected solid and one material/color. The five-color
palette adds no printed subparts, inserts or glue joints. No physical sample,
sliced production job, material qualification or human handling result is claimed.

## Measured nominal inventory

Dimensions and volumes below come from the [exact CAD report](cad/measure/physical-validation.json),
whose source hash matches `cad/quayshift_lib.py` when this document was prepared.
These are CAD measurements, not measurements of manufactured objects. The current
ferry is 26 × 24.5 × 20 mm overall, with a 12 × 18 mm cabin plan, a tapered
lower hull, a flat stern and a recessed foredeck. The diameter 26 mm × height
26 mm swept cylinder remains a conservative containing proxy; it is not the
actual ferry height. The
machine-readable [inventory](inventory.json) records the source and evidence hashes,
per-part volume, dimensions, palette and print orientation.

| ID | Part | Upright bounding box, mm | CAD volume, cm³ | Color | Authored print stance |
|---|---|---:|---:|---|---|
| A | High bridge A | 95.2 × 31.2 × 74 | 88.592 | limestone | Rear face down |
| B | High bridge B | 95.2 × 31.2 × 80 | 90.612 | terracotta | Rear face down |
| C | Low gate | 95.2 × 31.2 × 48 | 54.991 | limestone | Rear face down |
| D | L-shaped courtyard | 63.2 × 63.2 × 70 | 99.092 | dark olive | Base down |
| E | Two-cell building E | 63.2 × 31.2 × 62 | 54.717 | terracotta | Base down |
| F | Two-cell building F | 63.2 × 31.2 × 58 | 51.879 | limestone | Base down |
| G | Tower G | 31.2 × 31.2 × 84 | 50.702 | dark olive | Base down |
| H | Tower H | 31.2 × 31.2 × 64 | 38.967 | terracotta | Base down |
| tray | Canal tray | 184 × 184 × 12 | 195.160 | dark petrol | Base down |
| ferry | Hand-moved ferry | 26 × 24.5 × 20 | 5.733 | ochre | Base down |

Total nominal solid volume: **730.444631 cm³**. A completely filled kit at the
assumed PLA density of 1.24 g/cm³ would contain **905.751 g** of polymer before
brims, supports or waste. This reference is not a slicer estimate.

The board is 184 × 184 × 12 mm, with a 32 mm cell pitch. The tallest architecture
module is 84 mm; standing on the 4 mm floor makes the complete town 88 mm high.
Each arch's play reservation remains three whole cells even though its feet
occupy only the two end cells.

## Proposed desktop FDM setup

Use a conventional 0.4 mm nozzle and an ordinary bed with at least 220 × 220 mm
usable area. This is a planning assumption, not a qualified printer/profile.
The tray's 184 mm square footprint leaves 18 mm per side on that bed before
adhesion margins; a proposed 5 mm brim would make it 194 mm square. Check actual
usable bed limits, clamps and printer exclusions in the eventual slicer.
Architecture can be distributed over additional same-color batches; no single
all-parts plate layout has been qualified.

A/B/C print on their planar rear faces: the authored `print_part()` applies
−90° around local X, then translates the minimum bounds to zero. Their print
boxes are respectively 95.2 × 74 × 31.2, 95.2 × 80 × 31.2 and
95.2 × 48 × 31.2 mm. D/E/F/G/H, tray and ferry use their base undersides.
The individual `part_*.step.py` sources already select these print stances;
do not apply the arch rotation a second time. The assembled STEP depicts play
positions and is not a single printable ten-solid object.

For a first slicing trial, assume PLA, 0.20 mm layers, nominal 0.45 mm line width,
four walls, four top/bottom layers and 20% infill. These are starting settings,
not certified settings or a guarantee of strength or dimensional accuracy.
The rear-down arch stance puts the opening profile into the layer plane; it
avoids asking an upright arch ceiling to bridge the entire passage. Inspect
all actual slicer overhangs, first-layer contact and support needs before a
manufacturing decision. No support-free or print-ready claim follows from these
notes. Material temperature and cooling must come from the selected material
and machine profile; none is specified here.

Separate color batches provide limestone A/C/F, terracotta B/E/H, olive D/G,
petrol tray and ochre ferry without an in-part color change. Allow for adhesion,
cleanup and any edge burrs on ferry contact surfaces. Preserve nominal passage
geometry; don't resize the ferry or architecture independently to hide a failed
fit. Check a manufactured high arch, low gate, corner and floor patch before
committing to a full production batch.

## Reproducible material and time scenarios

The following are explicitly assumed planning scenarios. The effective deposited
fraction includes walls, skins and infill together; **it is not the infill
percentage**. It has not been derived from a sliced toolpath. Feedstock includes
a 10% allowance for supports, brims and waste. Time assumes a constant effective
extrusion rate while depositing, then adds 20% for travel, heating and other
machine overhead. Real cooling limits, small-feature slowdown, bed changes,
support demand or rejects can exceed these allowances.

| Scenario | Effective fraction of CAD solid | Assumed depositing rate | Feedstock including 10% | Machine time including 20% |
|---|---:|---:|---:|---:|
| Low planning case | 0.35 | 6 mm³/s | 348.714 g | 15.623 h |
| Central planning case | 0.45 | 4.5 mm³/s | 448.347 g | 26.783 h |
| High planning case | 0.60 | 3 mm³/s | 597.796 g | 53.566 h |

Reproduce using `V = 730444.631` mm³, fraction `f` and rate `q`:

```text
feedstock_g = V × f × 1.10 ÷ 1000 × 1.24
machine_hours = V × f × 1.10 ÷ q ÷ 3600 × 1.20
```

These scenarios are not probability bounds. They exclude reprints beyond the
10% material allowance and contain no measured printer timing. Allow a separate
**45–90 minutes of human handling** as an unmeasured planning allowance for bed
changes, cleanup, checking, sorting and protective packing. Training, failed
parts or process qualification may require more.

For a transparent commercial sensitivity example only, assume filament at
US$20/kg, machine time at US$1/hour, 45 minutes handling at US$20/hour and US$4
packaging. The central scenario gives approximately US$8.97 + US$26.78 + US$15
+ US$4 = **US$54.75** before sales fees, overhead, rejects, shipping or margin.
Those unit rates are hypothetical inputs, not current quotes. The roughly
US$49 complete-gift target is therefore **not established as viable** by this
one-off FDM example. Batch process, labor and real production economics remain
unverified; no price or demand forecast is made.

## Normal protective packaging

Use an ordinary protective box with **220 × 220 × 105 mm internal space**.
Against the 184 × 184 × 88 mm town envelope this leaves 36, 36 and 17 mm total
clearance respectively. These are geometric allowances, not qualified cushioning
thicknesses. Keep the tray flat; individually support buildings in their town
positions with fitted paperboard/foam separators, protect the ferry in its own
pocket, and cushion roof masses against the lid. Restrain pieces so they cannot
strike their neighbors or load a bridge span during transport. Packaging adds
no printed mechanism and is outside the ten printed kit parts. No transit or
drop test, box sourcing or packaging prototype has been performed.

## Evidence limits

The source report checks geometry, continuous containing-cylinder route sweeps,
low-gate interference and sampled finger proxies. It does not establish actual
manufactured fit, comfortable hand access, stability of infilled parts,
adhesion, creep, wear, durability or fun. Uniform-solid support margins in the
inventory do not model infill distribution or warping. Facade-facing scope is
recorded in [the challenge notes](challenges/README.md); match the shown solution
poses rather than assuming every facing has equal hand access.

The product includes **three edited challenges**, not a completed 24-card deck.
This manufacturing note neither starts a print nor authorizes manufacture,
purchase or shipment.
