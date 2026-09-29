---
title: Fluid fittings and pneumatics in printed parts
tags: [pneumatic, hose-barb, push-fit, tubing, channel, soft-actuator, pump, valve, pressure, leak]
aliases: [hose barb, barbed fitting, barb connector, tube stretch, push-to-connect, push in fitting, one-touch fitting, instant fitting, quick connector, pneumatic fitting, pu tubing, polyurethane tubing, silicone tubing, air line, internal channel, fluid channel, printed manifold, airtight print, leak tight print, pneunet, pneu-net, soft actuator, soft pneumatic actuator, soft gripper, diaphragm pump, air pump, solenoid valve, pressure relief, burst pressure, hydrostatic test, hoop stress]
sources:
  - https://fluid-components.nordsonmedical.com/files/fluid-components-nordsonmedical-com/Technical%20Information/Barb%20Information/barb-styles.pdf (tube expansion by barb series: 8–17 % with clamp, 18–34 % silicone/PVC, 20–50 % stiff PU/PVC, 25 %, 35 %, 50 %, 42–69 %)
  - https://medtechintelligence.com/column/ask-the-engineer-designing-molded-hose-barbs/ (barb OD and sharpness govern pull-off; single barb for soft tubing, several for a broad durometer range)
  - https://industrialmonitordirect.com/blogs/knowledgebase/hose-barb-geometric-standards-dimensional-reference (included barb angle 5–15°, 8–10° common; via search excerpt)
  - https://www.industrialspec.com/about-us/blog/detail/barb-connectors-in-depth-design-and-function (barbs are low-pressure fittings; higher expansion holds higher pressure)
  - https://content2.smcetech.com/pdf/KQ2.pdf (SMC KQ2: tube OD 3.2–16 mm, nylon/soft nylon/PU, −100 kPa to 1.0 MPa, proof 3.0 MPa, −5 to 60 °C, M5 with gasket, R threads with sealant)
  - https://www.amazon.com/SMC-Green-Polyurethane-Tubing-Length/dp/B0065RQOFC (SMC TU 4 mm OD × 2.5 mm ID PU, 95 Shore A; via search excerpt)
  - https://arxiv.org/pdf/2608.13233 (airtight FDM TPU: three 0.32 mm wall lines beat two 0.8 mm lines, 110 % flow, 0.1 mm layers, dry filament, 30–40 % fan; cast silicone ~5 mm walls, bonded interfaces fail ~200 kPa)
  - https://arxiv.org/pdf/2312.01135 (FDM TPU bellows leak rate at 100 kPa rises with layer height 0.1 → 0.3 mm)
  - https://www.academia.edu/28773801/High_Force_Soft_Printable_Pneumatics_for_Soft_Robotic_Applications (Yap et al. 2016, FDM NinjaFlex actuators, 1.2 mm minimum airtight wall; via search excerpt)
  - https://arxiv.org/pdf/2605.25109 (review: fast PneuNet gaps between chambers, internal walls more compliant, 50 ms at 345 kPa, > 10^6 cycles, 1/10 volume; conventional needs ~3× pressure, 8× volume)
  - https://formlabs.com/white-papers/desktop-millifluidics-with-sla-3d-printing/ (SLA channels resolve at 700 µm, 500 µm optimal, 50 µm layers, ≥ 50 mL flush through < 1 mm channels, round beats sharp-cornered)
  - https://forgelabs.com/design-guides/fdm (FDM minimum hole 1 mm vertical, 2 mm horizontal; via search excerpt)
  - ISO 228-1 (G pipe thread: G1/8 28 TPI = 0.907 mm, G1/4 19 TPI = 1.337 mm)
  - Shigley's Mechanical Engineering Design, ch. 3 (thin-walled pressure cylinders, σ_t = p r / t)
  - https://en.wikipedia.org/wiki/Hydrostatic_test (liquid test because gas stores expansion energy; test at 143–167 % of working pressure)
  - ASME B31.3 §345.4.2 and §345.5 (hydrostatic test ≥ 1.5 × design pressure, pneumatic ≥ 1.1 ×; via search excerpt)
related: [sealing-and-ingress-protection, perimeters-infill-and-strength, layer-anisotropy, heat-set-inserts, printed-threads, fdm-hole-accuracy, overhangs-and-print-orientation, moisture-and-drying, motor-drivers-and-flyback, small-dc-motors, power-path-design, resin-printing-design, flexures-and-living-hinges]
updated: 2026-09-23
---

# Fluid fittings and pneumatics in printed parts

Small air or water plumbing in a printed part fails at three places: the
tube-to-part joint, the printed wall, and the pressure source that can exceed
what either holds. Read this before drawing a barb, a fitting port, an
internal channel, a soft actuator or a pump mount. Static seals, O-ring glands
and wall perimeter counts for water are in
[[sealing-and-ingress-protection]]; this page extends them to tubes, channels
and pressure.

## Tube-to-part joint: pick by pressure

| joint | pressure | tube | notes |
|---|---|---|---|
| printed hose barb | low; unrated until a coupon is tested | soft silicone, PVC, soft PU | cheapest; add a clamp or cable tie for anything real |
| bought barb or bought push fitting threaded into the part | to the fitting rating (KQ2: 1.0 MPa) | nylon / PU to the fitting's OD | the part's thread and seal become the weak link |
| tube bonded into a printed socket | low | PU, PVC | permanent; needs a solvent or adhesive that wets both |

Push fittings grip the tube **OD**; barbs seal on the tube **ID**. Tube is
sold by OD × ID: common metric PU pneumatic sizes follow the push-fit ODs
(SMC KQ2 accepts ø3.2, 4, 6, 8, 10, 12, 16 mm), e.g. 4 × 2.5 mm, 95 Shore A.
Read the ID from the tube datasheet, never assume it.

## Hose barb geometry

The tube stretches over a barb crest and the elastic hoop force seals it:

```text
expansion   e = (D_barb - ID) / ID       D_barb crest diameter, ID tube bore
```

Nordson's barb families set e by tube stiffness:

| tube | expansion used |
|---|---|
| any, with a hose clamp | 8–17 % |
| silicone, PVC, TPE (low profile, clamp or tie) | 18–34 % |
| semi-rigid (easy assembly) | about 25 % |
| stiff PU and hard PVC | 20–50 % |
| flexible tube, high pressure | 35–50 % |

- More expansion holds more pressure and pull-off but needs more push-on
  force; stiff PU at 50 % is hard to assemble by hand.
- Crest sharpness governs pull-off as much as OD. A printed crest is rounded
  by the nozzle, so a printed barb holds less than a moulded one at the same e:
  go to the upper half of the range, or clamp.
- Lead-in flank at a shallow included angle (5–15°, 8–10° common) and a steep
  or square return face behind each crest.
- One barb suits soft tube; several barbs cover a wider durometer range.
- The shank between crests is about the tube ID, and the bore through the barb
  sets the flow restriction: keep the barb's wall ≥ the minimum printed wall
  ([[wall-thickness-and-hollowing]]).
- **Print a barb standing up** (axis along Z): every layer is a ring parallel
  to the seal, the hoop stress runs along the layers, and the stub cannot snap
  at a layer line when the tube is bent. A barb lying in X-Y crosses layers at
  every crest and breaks off at the root ([[layer-anisotropy]]).

## Push fittings and threaded ports in printed bodies

A bought push-to-connect fitting is the reliable joint; the design problem is
the port it screws into.

- **Parallel thread + face seal, not taper thread.** Taper (R, NPT, BSPT)
  threads seal by wedging, and the wedge splits a printed boss. Prefer a
  parallel thread (M5, G1/8) with the fitting's own gasket or an O-ring
  against a flat face.
- **Thread source**: M5 is below and M6 at the printed-thread floor
  ([[printed-threads#size-limits]]); use a brass heat-set insert
  ([[heat-set-inserts]]) or tap a solid boss. G1/8 (0.907 mm pitch) is also
  finer than the 1.0 mm printed-pitch floor, so tap it too; G1/4 (1.337 mm
  pitch) can be printed and is still better tapped for a gasket seal.
- **The seal face must be a top face.** The gasket seals on the spot face
  around the port: make that face horizontal (a top surface, ideally ironed)
  and wider than the gasket. A heat-set insert leaks around its knurl, so the
  gasket must bridge insert and plastic, or pot the insert in epoxy.
- **Do not print a spigot for a push fitting.** Its collet bites and its
  O-ring seals on the tube OD at the maker's tolerance; a printed stub is
  neither round nor smooth enough.
- Respect the fitting's temperature range (KQ2: −5 to 60 °C) and the tube's
  minimum bend radius near the port; leave straight tube length in front of
  the fitting for the insertion depth.

## Leak-tight printed walls and channels

A pneumatic wall is a pressure boundary built from extrusion lines. Beyond the
perimeter counts in [[sealing-and-ingress-protection#making-the-printed-wall-itself-watertight]]:

- **More, narrower wall lines beat fewer, wider ones.** In a TPU actuator
  study a 0.96 mm wall of three 0.32 mm lines was airtight where a 1.6 mm wall
  of two 0.8 mm lines leaked; one or two lines never sealed reliably, three
  was the balance. Set wall line count in the design, not wall thickness
  alone ([[perimeters-infill-and-strength]]).
- Over-extrude slightly (that study: 110 %; ≤ 105 % left gaps), use thin
  layers (0.1 mm; leak rate rose steeply at 0.3 mm), and dry the filament:
  wet TPU foams and leaks ([[moisture-and-drying]]).
- Channels are **solid-walled**: no infill touches a channel wall, so model
  the wall as a sleeve of known line count around the channel.
- **Hoop stress sets orientation.** A pressurised tube of radius r and wall t
  carries `σ = p r / t` around its circumference. Vertical channels load
  their walls along the layers; horizontal channels pull their top and bottom
  across the layers, the weak direction. Run pressurised channels vertically
  where possible, and derate horizontal ones by the cross-layer factor.
- **Minimum channel size**: FDM horizontal holes resolve from about 2 mm,
  vertical from 1 mm; below that stringing blocks the bore. SLA resolves
  round channels down to 0.5–0.7 mm at 50 µm layers but must be flushed (≥ 50
  mL of IPA through a sub-mm channel, Formlabs); keep channels ≥ 1 mm and
  short enough to flush ([[resin-printing-design#hollowing-drains-and-vents]]).
- **Horizontal channels print as teardrops** (point up, 45° roof), exactly
  like horizontal bores ([[fdm-hole-accuracy#horizontal-holes-teardrops-and-horiholes]]).
  Round sections flow best; a teardrop costs a little flow area, a diamond or
  triangle more, and sharp-cornered sections print less reliably in resin.
- **Bends**: route a channel as straight runs joined by generous radii, never
  mitred corners; a mitre traps stringing (FDM) and resin (SLA). A channel
  that rises at ≥ 45° is self-supporting in any direction. Put a straight
  clean-out line to a plugged port at every bend you cannot see through.

## Soft pneumatic actuators

A soft actuator bends because one side stretches and the other does not:

- **PneuNet**: a row of chambers in an elastomer, with an inextensible
  **strain-limiting layer** (paper, fabric, a stiffer elastomer) along one
  side. Inflation lengthens the chamber side; the limited side makes it bend.
- **Fast PneuNet**: gaps between adjacent chamber walls and **internal walls
  thinner (more compliant) than the outer walls**, so the inner walls push on
  each other instead of the outer skin ballooning. The reported design bent to
  a near-circle in 50 ms at 345 kPa, needed about a tenth of the volume change
  and survived > 10^6 cycles; the conventional layout needed about 3× the
  pressure and 8× the volume for the same bend.
- **Cast silicone** (Ecoflex, Dragon Skin, Elastosil class) stretches
  furthest. Cast it in a printed mould around cores; thin walls fail to fill
  (one study needed about 5 mm for enclosed geometry), and the bonded seam
  between separately cast halves is where it bursts (about 200 kPa there).
  Mould rules: [[moulds-and-casting-from-prints]].
- **Printed TPU** actuators skip the mould and take higher force; Yap et al.
  report a 1.2 mm minimum airtight NinjaFlex wall. TPU's strain limit is far
  lower than silicone's, so geometry (bellows, folds) supplies the motion
  ([[flexures-and-living-hinges]]).
- Working pressures in the literature run from tens to a few hundred kPa;
  burst depends on wall, material and bond quality. Treat any burst number as
  something to measure on a coupon, not a value to design to.

## Pumps and valves are powered loads

- A small diaphragm pump is a DC motor ([[small-dc-motors]]); a solenoid valve
  is an inductive load that needs a flyback diode and a driver
  ([[motor-drivers-and-flyback#flyback-freewheel-diodes]]). Both go through
  the electromechanical-integration workflow and the power path
  ([[power-path-design]]).
- Mount pumps on soft feet: they vibrate, and the vibration loosens barbs.
- An actuator needs a way **out** as well as in: a 3/2 valve to exhaust, or a
  bleed orifice. A pump alone holds pressure only through its check valve.

## Pressure safety

- **Choose a source that cannot burst the part.** A pump's dead-head
  (blocked-outlet) pressure is the most the system can see if a valve sticks.
  Make it less than the weakest joint's tested burst divided by a margin, or
  add a relief valve; then no control fault can over-pressurise the part.
- **Test with water, not air.** Gas stores expansion energy and a failed
  printed vessel throws fragments; a liquid releases almost nothing.
  Codes test hydrostatically at 1.5 × design pressure and allow pneumatic
  tests at only 1.1 × for this reason (ASME B31.3). Proof-test printed
  pressure parts filled with water, then leak-test with air under water.
- Keep the pressurised volume small, the pressure low, and eyes out of line
  with any printed pressure part until it has passed its proof test.

## Checks

```python
import math
e = (D_BARB - TUBE_ID) / TUBE_ID
assert E_MIN <= e <= E_MAX, f"barb expansion {e:.0%} outside the tube's range"
assert BARB_AXIS == "Z", "print barbs standing up"
assert not (PORT_THREAD in ("M5", "M6") and PORT_SOURCE == "printed"), "insert or tap below M8"
assert PORT_THREAD_TYPE == "parallel" and PORT_SEAL_FACE_IS_TOP
# channel wall under pressure (thin-wall hoop stress), derated if horizontal
sigma = P_MAX * (CH_D / 2) / CH_WALL                  # MPa with P in MPa, mm
allow = S_MATERIAL * (Z_FACTOR if CH_HORIZONTAL else 1.0) / SAFETY
assert sigma <= allow, f"hoop stress {sigma:.2f} MPa over {allow:.2f}"
assert CH_WALL_LINES >= 3, "fewer than three wall lines leak"
assert CH_D >= (2.0 if CH_HORIZONTAL else 1.0), "channel below FDM minimum"
# pressure source bounded by the weakest tested joint
assert PUMP_DEADHEAD_KPA * MARGIN <= BURST_TESTED_KPA or HAS_RELIEF_VALVE
assert PROOF_TEST_KPA >= 1.5 * P_WORK_KPA and PROOF_MEDIUM == "water"
```
