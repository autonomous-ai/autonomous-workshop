# Heritage Horizon 2050

Assembly and printing guidance for the scale model. Digital evidence does not certify a physical print.

Heritage Horizon 2050 is an unofficial imagined 2050 interpretation of the user's Heritage Classic touring-cruiser brief, at **1:12 scale**. The low saddle, generous fenders, swept grips, windscreen and paired luggage surround an original electric-package proposal. It is not a manufacturer announcement or affiliated product. The model has no electronics. Lamps and the blue-gray windscreen are opaque printed geometry; there is no claim of clear glazing, chrome or functioning lights.

The intended interaction is to lift the motorcycle from its removable belly cradle, guide it upright while its two wheels turn, then replace it for display. Steering and suspension are fixed. The motorcycle cannot balance upright by itself when removed from the cradle.

## Parts and preparation

Print 22 plastic pieces from the 18 component source variants: four roles have distinct left/right source files; the other repeated pieces reuse one printable shape. There are 14 design roles. Use the supplied `part_*.step` files in their prepared print stances. The combined motorcycle file shows assembly placement and is not a one-piece printing layout.

Purchase two M3 × 30 socket-head screws and four ordinary ISO 4032 M3 hex nuts. These six hardware instances are not printable parts. Each axle uses two ordinary nuts tightened against one another as a jam pair; they are not thin jam-nut catalog parts. The previously considered nylon locknuts are excluded.

Have the driver for the purchased M3 socket screws, two spanners matching the purchased nuts, a suitable adhesive for the chosen print material, and deburring tools available. The source nut is 5.5 mm across flats. Follow the adhesive manufacturer's directions and curing time. Keep adhesive away from wheel bores, axle shafts and threads.

Remove print burrs from mating faces and holes without changing the intended clearances. Dry-fit the static parts before applying adhesive. If a wheel binds or a seam requires substantial force, inspect the print and the mating surfaces; do not force the assembly into shape. Fit and material-specific printing settings remain to be established with a physical prototype.

## Print orientation and quantities

The STEP entries already orient their geometry on the bed. The face descriptions below explain the intended stance; they are not additional rotations to apply in a slicer. Left and right refer to the assembled motorcycle, viewed from the rider's position.

| Role / component stem | Print quantity | Bed-facing surface | Suggested printed color |
|---|---:|---|---|
| `chassis_half`, `chassis_half_right` | 1 each | Flat motorcycle center seam | Charcoal |
| `swingarm_side`, `swingarm_side_right` | 1 each | Flat inner side; bag ledges build upward | Gray |
| `fork_leg` | 2 | Flat inner side profile | Gray |
| `fork_bridge`, `fork_bridge_right` | 1 each | Flat motorcycle center seam, including lamp half | Gray |
| `wheel` | 2 | Flat wheel side; spoke recess faces upward | Black |
| `tank_cover` | 1 | Flat bottom of storage cover | Teal |
| `seat_half`, `seat_half_right` | 1 each | Flat motorcycle center seam | Saddle brown |
| `pannier` | 2 | Broad outer face; inner mounting sockets face upward | Saddle brown |
| `front_fender` | 1 | Narrow side face; arch outline lies on the bed | Teal |
| `screen` | 1 | Broad rear face, with tongue coplanar | Opaque blue-gray |
| `handlebar` | 1 | Flat underside of the swept bar | Gray |
| `bar_riser` | 1 | Flat side profile | Gray |
| `footboard` | 2 | Broad flat underside | Charcoal |
| `plinth` | 1 | Broad base underside | Charcoal |

The support-free component strategy uses split chassis, bridge and saddle seams; separate fork legs, swingarm plates and footboards; and a planar swept handlebar with its own riser. Geometry was designed for a 0.4 mm nozzle. Use the final Manager-supplied CAD evidence for the exact revision's geometric checks; a digital overhang result does not establish real material behavior, bed adhesion, surface finish or physical fit.

## Assembly order

1. **Join the main chassis.** Match the left and right chassis halves at their flat center seams. Check the rear-fender arch, tank bosses and steering pocket line up. Apply adhesive only to the static mating faces, align and allow the seam to cure without twisting the frame.
2. **Fit the swingarm sides and footboards.** Place each rear side plate's root tab in its chassis pocket. The bag supports face outward. Keep the rear axle holes coaxial and the wheel gap open while the adhesive cures. Fit the footboards to their outer chassis ledges, with their broad tread faces upward.
3. **Build the front support.** Join the two bridge/lamp halves at their center seam. Fit the bridge tongue to the chassis steering pocket and the two fork legs to their side laps. The axle bosses face the front-wheel location. Allow these structural seams to cure before fitting or tightening axle hardware. Steering remains fixed straight ahead.
4. **Dry-check both wheels.** Place a wheel between each pair of supports. Nominal wheel width is 12.5 mm inside a 14.5 mm opening, leaving 1.0 mm on each side. Check the bore and arch are unobstructed. Wheel bores are nominally 3.5 mm around the 3 mm axle shaft; these are CAD dimensions, not measurements of printed parts.
5. **Install each axle and jam pair.** In the depicted assembly, the screw head is on the rider's right and the two nuts are on the rider's left. Pass the screw through support, wheel and opposite support. Fit the inner nut without drawing the supports inward or trapping the wheel. Hold the inner nut in position with one spanner and tighten the outer nut against it with the other. Do not use the wheel as a clamping spacer. Check that the wheel still turns freely and retains visible side clearance. No torque value is established for the printed supports.
6. **Fit the front fender.** Position it concentrically above the wheel and attach its static contacts at the fork pads. Keep adhesive off the tyre and axle. Check wheel rotation again; a fender rubbing a wheel needs correction before use.
7. **Fit the tank cover and saddle.** Seat the storage cover's two underside sockets over the chassis locating bosses and bond only at the ledges. Join the saddle halves at their center seam, then place the stepped underside onto its rider and rear ledges. The repaired saddle nose is deliberately cut back around the cover; do not fill this clearance or force the two surfaces together.
8. **Fit the touring equipment.** Match each pannier's two inner sockets to its outward bag supports and bond those static interfaces. Bond the riser to its bridge land and the handlebar's flat center underside to the riser before installing the screen. Then fit the screen tongue into the bridge pocket along its inclined plane. The bar sweeps rearward toward the rider; the screen rises above the front equipment.
9. **Display or roll under hand guidance.** Rest the chassis belly in the two cradle openings, with the base flat on the desk. The cradle is removable and receives no adhesive. To roll the model, lift it clear of the cradle and keep it upright by hand. If the cradle rocks, the bike leans unexpectedly, or a wheel binds, stop and inspect rather than assuming the digital model proves physical behavior.

## Axle retention: what the geometry establishes

The canonical source nut is one solid, 2.4 mm thick, with a 1.5 mm bore radius. The outside support span is 22.5 mm. A 30 mm shaft therefore leaves 7.5 mm beyond the support; two 2.4 mm nuts use 4.8 mm and leave 2.7 mm nominal protrusion.

Those measurements establish space for the parts. The catalog STEP files represent a smooth bore and shaft, not working helical threads. They do not establish real thread engagement, tightening preload, friction, resistance to loosening or successful physical retention. The jam-pair procedure must be verified on the printed model and purchased hardware. A digital stationary-axle or rotating-wheel joint is a kinematic description, not a force test. No claim of physical rolling, fit, durability or human-use testing has been made.

## Package and source-driven refinements

| Package quantity | Full-size design | Scale model |
|---|---:|---:|
| Design length | 2460 mm | 205 mm nominal |
| Width at grips | 930 mm | 77.5 mm |
| Touring-screen height | 1380 mm | 115 mm |
| Wheelbase | 1680 mm | 140 mm |
| Rider seat height | 690 mm | 57.5 mm nominal hard point |
| Wheel diameter | 648 mm | 54 mm |
| Tyre width | 150 mm | 12.5 mm |
| Belly clearance | 150 mm | 12.5 mm |

These are the design package values; final measured assembly bounds should come from the Manager's geometry report. The base extends below the wheel-ground plane and is excluded from vehicle height. The removable cradle base is 80 × 65 × 3 mm, with 26.6 mm-wide openings around the 26 mm belly.

Construction details:

- The tank cover starts at Z49 above the battery housing top Z48. Its lower sections at Z49, Z50 and Z52 use the same flat footprint, which supports the skirt before the dome contracts upward. Its two sockets accept the chassis bosses. The crest remains Z74.
- The saddle underside rises to Z63 over the rear fender, descends through the central transition, and reaches the rider ledge at Z54.5. Its forward clearance is projected through the whole saddle width so the nose is shorter than the initial unsplit proposal. That shortening is intentional and avoids an unsupported growing lip around the tank.
- The chassis steering housing now reaches Z71.2. The steering-pocket roof is Z69.2, leaving a 2 mm roof wall; the original nominal Z69 chassis description must not be treated as the exact current part envelope.
- The front fender is currently 14.5 mm wide, as given by the source extrusion, rather than the earlier 16 mm intent. Its inner and outer arch radii remain 30.2 and 33.2 mm.
- The grips retain the wide, rearward-swept package. The bar's centerline height is simplified to a plane near Z87, carried by a separate riser, to give a flat printable underside.

## 2050 technology ledger and evidence labels

| Item | Label | Meaning and evidence |
|---|---|---|
| Low seat, curved fenders, screen, swept bars and touring luggage | **Observed reference / design interpretation** | The documented manufacturer and dealer references informed the touring-cruiser character. They do not show an actual 2050 vehicle. |
| 24 kWh pack in a 69.7 L proposed envelope, target mass 96 kg | **Speculative 2050 assumption** | About 344 Wh/L gross envelope and 250 Wh/kg pack target. These numbers are an invented package assumption, not a measured or qualified battery. |
| Two visible cooling shoulders around the central electric package | **Speculative design** | Physically represented covers suggest thermal hardware; no heat-transfer or cooling-performance result is claimed. |
| Central electric drive, mechanical steering, telescopic fork and rear swingarm | **Conventional concept architecture** | The model depicts a plausible arrangement. It contains no motor, battery or operational suspension; it is not a validated full-size drivetrain design. |
| Source battery research | **Cited research trend** | The [DOE Battery500 progress update](https://www.energy.gov/cmei/articles/battery500-progress-update) reports cell research, including 350 Wh/kg progress and a 500 Wh/kg research aim. Cell results do not prove this vehicle's future pack performance. |
| Current touring-cruiser dimensions and equipment | **Cited comparison facts** | The [2025 manufacturer specification](https://www.harley-davidson.com/eu/en/motorcycles/2025/heritage-classic.html) supplied comparison dimensions and equipment. This model uses its own declared future package. |
| Opaque screen, inert lamp, printed colors | **Actual model representation** | No clear-glass, chrome, lighting, electrical or manufacturer-finish claim. |

The source research was recorded during the design handoff; these links are cited evidence, not newly checked research in this drafting task. No range, roadworthiness, certification, production feasibility, manufacturer endorsement or physical testing claim follows from this scale model.

The steering housing starts at X29.5 to leave a clear vertical tank approach. The neck follows a forward-routed polygon; shared saddle and swingarm clearance profiles relieve the chassis. Static seams require adhesive; motion checks do not prove adhesive strength or thread retention.

## Source and rebuild

The assembly entry is heritage.step.py. All dimensions are in params.py; part modules live in parts/, and placement lives in assemblies/product.py. The part_*.step.py entries define print stances. Ref contains the two canonical purchased hardware sources. Measure contains exact digital checks, and snap contains the final presentation.

Rebuild with the materialized CAD tool: scripts/gen heritage.step.py part_*.step.py --write. Verify with scripts/verify_project . --strict-fit --print-gates --nozzle 0.4. Bed envelope: --bed 220x220x220. No electronics or powered-load verification applies.


## Project fit/print audit

The project-specific audit is composed of the pre-geometry assertions in `validation.py`, the exact named interface checks in `measure/motion.json`, and the catalog-part mounting checks in `measure/mounts.json`. Run the assertions from this directory with `python validation.py` in the supplied CAD environment. The integrated verification command above runs the two manifest checks and the generic bed, body and source checks.

The shared axle diameter derives the wheel and support bore; the shared wheel width and side air derive the support gap. Tank pin diameter derives its socket once. The screen width, length and thickness each derive their socket using the shared screen clearance. Cradle opening is compared with the shared battery width before building. The named interfaces are the chassis center seam, swingarm root pockets, fork bridge tongues and side laps, tank pins/ledges, saddle ledges, pannier pins/shelves, footboard ledges, screen tongue, riser/bar lands, wheel bores, stationary axles, paired nuts and gravity cradle. These are also identified in the assembly steps above.

The 28 motion conditions check the complete wheel revolution and the reverse approach of each assembly interface. The assembly order puts the riser and bar before the screen, wheels before axles, and the nuts last. Reverse withdrawal paths test collision-free geometric access; the mounts manifest checks canonical hardware placement. This is an equivalent geometric fit audit, with the explicit limitations that neither adhesive curing nor threaded preload and friction are simulated. Physical retention and free rolling still require a prototype.
