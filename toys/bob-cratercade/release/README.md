# Cratercade

Cratercade is a small mechanical lunar pinball machine. Launch one glass marble, work the two thumb flippers, rebound from three movable craters, and aim up the ramp into the sample bucket. A captured marble tips the bucket and raises its connected flag. Lift out the marble, drop it into the adjacent hopper, and the empty bucket returns by gravity while the marble rolls through a covered return to the front collection cup.

The 320 × 480 mm playfield separates into six tiles for a 200 mm class FDM printer. Two mission layouts reuse the same three craters and two curved guides. There are no electrical parts or automatic ball feeder.

This package contains a digital design. Motion verification was disabled for this handoff: assembly access, retention through all operating states, and working motion remain unverified. See [Verification scope](VERIFICATION-STATUS.md). CAD clearances and print-orientation checks do not establish physical print quality, rubber-band force, reliable rolling, successful capture, containment or durability. Complete the physical commissioning below before play. No physical prototype or human playtest is claimed.

## Files and coordinates

`cad/cratercade.step` is the assembled reference. Print the individual `cad/part_*.step` files in their supplied print poses; do not use the assembled reference as a print plate. Matching `.step.py` files and the `cad/parts/`, `cad/assemblies/` and `cad/params.py` sources describe the components and their assembly.

Dimensions are millimetres. Viewed from above with the player at the front, X increases to the right and Y increases away from the player. The playing surface is Z = 0; +Z is above the deck. Rotation 0° is the supplied board orientation, and positive angles turn counterclockwise when viewed from above. The feet set a nominal 6° incline with the player end lower.

## Materials, hardware and tools

Use the following hardware sizes. M4 screws and nuts are M4 × 0.7. Use the specified thin nuts; ordinary full-height M4 nuts change the bearing and retention stacks.

| Item | Specification |
| --- | --- |
| Countersunk screws | ISO 10642 M4 × 16, 90° head, 2.5 mm hex socket; length includes the head. Qualified head envelope is at most Ø8.96 × 2.48 mm. |
| Socket-head screws | ISO 4762 M4 × 25, 3 mm hex socket; length is measured under the Ø7 × 4 mm head. |
| Nuts | ISO 4035 / DIN 439 M4 thin hex nuts, 7 mm across flats, nominal 2.2 mm thick. |
| Axle | One straight Ø4 mm beech dowel, cut square to 96 mm. Screen actual diameter to 3.9–4.1 mm. |
| Rubber bands | Three working Lee #16 bands and three spares: nominal relaxed lay-flat length 63.5 mm, width 1.5875 mm, wall thickness 0.79375 mm. One band serves each flipper and one serves the launcher. The right flipper uses two turns of one band. A size number alone does not establish section or force. |
| Marbles | Three nominal 16 mm glass marbles suggested: one in play, two spares. Individually screen to 15.5–16.5 mm diameter and 4–7 g mass. |
| Clear panels | Clear PET sheet, 0.2–0.5 mm thick; see the 16-piece cut list below. The CAD represents 0.35 mm sheet. |
| Feet | Four felt pads, 54 × 32.18 × 1.5 mm, and suitable craft adhesive for the pads. Trim flush to each horizontal foot base. |
| Scorekeeping | Pencil and paper or a small card. |

Fastener quantities are installation quantities, without spares:

| Assembly | M4 × 16 countersunk | M4 × 25 socket | Thin M4 nuts |
| --- | ---: | ---: | ---: |
| Deck seam straps and feet | 36 | 0 | 36 |
| Fixed playfield routes and five mission pieces | 38 | 0 | 38 |
| Flippers and their guards | 5 | 2 | 7 |
| Launcher | 7 | 0 | 7 |
| Jackpot mechanism and ramp | 11 | 0 | 11 |
| Return, hopper and collection cup | 22 | 0 | 22 |
| Main structure and mechanism subtotal | **119** | **2** | **121** |
| Canopy, excluding apron | 58 | 16 | 74 |
| Subtotal excluding apron | **177** | **18** | **195** |
| Two apron shells, independently rooted to deck | 4 | 0 | 4 |
| Complete installation | **181** | **18** | **199** |

The canopy subtotal contains eight top-shoe cross bolts, two rear-adapter cross bolts, 24 roof-cell mount bolts and 24 roof-panel clamp bolts, all M4 × 16, plus eight M4 × 25 post roots, four M4 × 25 hinge pivots and four M4 × 25 latch pivots. Each added pivot uses one thin nut. Do not count the inactive mission holes as additional fasteners.

Tools: 2.5 mm and 3 mm hex keys, a 7 mm nut driver or spanner, calipers, a small scale, scissors suitable for PET, a fine saw for the dowel, and deburring tools or fine abrasive. Physical launch-work commissioning also needs a calibrated low-force gauge and a travel scale. Keep hardware out of rolling passages. Tighten onto the intended lands without crushing printed plastic; recheck free motion after tightening.

## Printing and printed inventory

Start with a 0.4 mm nozzle, 0.20 mm layers, four perimeters and five top/bottom layers, then inspect the actual prints. Use sound structural PLA or PETG for ordinary parts; the canopy parts are specified as PETG. Print the **jackpot rocker and trim block in solid PLA at 100% infill**. Their balance calculation assumes PLA at 1.24 g/cm³; changing material or using sparse infill changes the balance and requires physical requalification.

All stems below name `cad/part_<stem>.step`. Where several stems share a row, the quantity is stated for each or explicitly as a group. The six deck files are different. The front and middle long perimeter walls are also different; do not replace them with repeated copies of one file. The two access receivers are handed: use `access_receiver` for reset and `access_receiver_load` for loading.

| Printed file stem(s) | Quantity |
| --- | --- |
| `deck_0_0`, `deck_1_0`, `deck_0_1`, `deck_1_1`, `deck_0_2`, `deck_1_2` | 1 each; 6 tiles |
| `seam_strap` | 6 |
| `seam_strap_short` | 1 |
| `foot_front`, `foot_front_right` | 1 each |
| `foot_rear` | 2 |
| `perimeter_side_160`, `perimeter_side_160_right` | 1 each; front sides |
| `perimeter_side_160_middle`, `perimeter_side_160_middle_right` | 1 each; middle sides |
| `perimeter_side_152`, `perimeter_side_152_right` | 1 each; rear sides |
| `perimeter_rear` | 2 |
| `launch_divider_lower`, `launch_divider_upper` | 1 each |
| `orbit_inner_wall`, `orbit_outer_wall` | 1 each |
| `return_guide_left`, `return_guide_right` | 1 each |
| `mission_crater` | 3 |
| `mission_guide` | 2 |
| `flipper_left_rotor`, `flipper_right_rotor` | 1 each |
| `flipper_left_guard_base`, `flipper_right_guard_base` | 1 each; include the apron floor extensions |
| `flipper_left_guard`, `flipper_right_guard` | 1 each |
| `flipper_pedestal`, `flipper_sleeve` | 2 each |
| `launcher_housing`, `launcher_rod`, `launcher_guide_cap`, `launcher_band_guard`, `launcher_anchor` | 1 each |
| `jackpot_rocker`, `jackpot_frame`, `jackpot_trim`, `landing_ramp` | 1 each |
| `jackpot_axle_cap` | 2 |
| `return_hood_0`, `return_hood_1`, `return_hood_2`, `return_hood_3` | 1 each |
| `return_floor_0`, `return_floor_1`, `return_floor_2`, `return_floor_3` | 1 each |
| `hopper_funnel`, `hopper_left`, `hopper_right`, `collection_cup` | 1 each |
| `canopy_frame`, `canopy_cap` | 4 each |
| `access_receiver` | 1; rear-left reset receiver |
| `access_receiver_load` | 1; front-right loading receiver |
| `access_frame`, `access_cap` | 2 each; one per access door |
| `access_hinge_sleeve`, `access_latch_sleeve`, `access_lever` | 4 each; two per access door |
| `canopy_post_middle` | 4 |
| `canopy_post_front_left`, `canopy_post_front_right`, `canopy_post_rear_left`, `canopy_post_rear_right` | 1 each |
| `canopy_rear_adapter_left`, `canopy_rear_adapter_right` | 1 each |
| `canopy_post_cap` | 8 |
| `canopy_roof_splice` | 2 |
| `canopy_end_join_front`, `canopy_end_join_rear` | 1 each |
| `apron_left`, `apron_right` | 1 each |

The main structure and mechanism contain 69 printed occurrences, the canopy adds 48, and the two apron shells add two: **119 printed occurrences from 78 file types**. PET panels, hardware, dowel and bands are additional purchased or cut parts. Print only one set of the five movable mission pieces.

Keep the supplied print poses. Decks print playing-face down, with underside ribs upward; straps print flat with locating pins upward. Feet print on their deck-bearing faces. Walls and mission obstacles print on their bases. The launcher rod now has a common flat underside and a sloped collar for its supplied flat print pose. The jackpot rocker prints on its continuous lower datum, the trim on its counterbored face, and the ramp upright on its flush toe and supporting base. Return hoods print roof-down; use the supplied inverted poses for return floor lids and hopper pieces. Canopy posts, top shoes and end mullions have intentional inverted print poses; apron shells print roof-down. Access receivers, moving frames and caps use their supplied flat poses. Hinge sleeves print with their axes vertical; latch sleeves print flange-up. Latch levers print broad top face down, with the pads and indexing dog upward. Do not rotate a part merely to resemble its installed position.

Remove burrs from bearing bores, slots, countersinks, return junctions and PET channels without enlarging a fit indiscriminately. Discard cracked or delaminated loaded parts. Keep the ramp toe and deck seams smooth enough that a marble does not catch on a raised lip.

## Clear PET cut list

Cut all pieces from the same qualified 0.2–0.5 mm sheet and deburr the edges.

| Panel | Quantity | Finished blank and cuts |
| --- | ---: | --- |
| Ordinary roof | 4 | 156 × 140 rectangle; remove a 16 × 16 square at each corner and a centred 9 mm wide × 11 mm deep notch at the midpoint of each of the four edges. |
| Access-door roof | 2 | Start with the same roof cuts. On the inboard long edge, add two notches, each 28 mm deep × 19 mm high, centred 28 and 112 mm from the front short edge of the blank. This is the right edge for the rear-left reset door and the left edge for the front-right loading door. |
| Side | 6 | 131.4 × 96.4 rectangles. |
| Front/rear end | 4 | 148.4 × 96.4 rectangles. |

Roof sheets are captured between their separate printed frame and cap. The side and end sheets locate in post and mullion channels. Do not replace these panels with an open frame during play.

## Assembly

Read the full sequence before installing bands. Keep all marbles out while assembling. The underside must remain accessible until the mounting nuts and return floor lids are fitted. Support the deck on padded edges or a suitable stand when turning it; do not carry or support it by the canopy, flag, flippers or launcher.

### 1. Deck and feet

Lay out the six tiles with column 0 on the left and column 1 on the right. Row 0 is the player end. Join them with locating pins upward on the seven underside seam straps. One short strap is intentional; it belongs at (88, 320), rotated 90°.

| Strap | Centre X, Y | Rotation | Type |
| --- | --- | ---: | --- |
| 0 | 160, 100 | 0° | Standard |
| 1 | 160, 258 | 90° | Standard |
| 2 | 160, 404 | 0° | Standard |
| 3 | 91, 160 | 0° | Standard |
| 4 | 296.5, 160 | 0° | Standard |
| 5 | 88, 320 | 90° | Short |
| 6 | 240, 320 | 90° | Standard |

Use four M4 × 16 screws per strap, inserted from the playing face, and thin nuts underneath. Seat all pins before progressively tightening the screws. Do not force a misregistered tile onto a pin. Check for a flat rolling transition at every seam; the physical commissioning target is no more than 0.20 mm vertical step.

Install the front-left foot at (48, 10), the distinct front-right foot at (272, 20), and the two identical rear feet at (48, 460) and (272, 460), with two M4 × 16 screws and nuts each. The asymmetric front locations and two front foot files are intentional. Attach one felt pad to each table-contact face. The completed deck should sit without rocking and rise away from the player.

### 2. Fixed playfield and canopy post roots

Install the perimeter wall segments in their front, middle and rear positions, followed by the two rear rails. Fit the lower and upper launch dividers, both upper-orbit walls and both lower return guides. Each printed piece uses two M4 × 16 screws and two thin nuts. These 14 fixed pieces use 28 pairs in total.

The screw head lands on these playfield parts are Z = 6 inside their access wells, not on the top of a 24 mm wall. Fully seat the heads on the countersinks and hold the nuts against the underside of the deck. Install the canopy posts at the wall interfaces while these nuts and wells are accessible; the canopy post steps are described in step 7.

The right launch lane is centred at X = 299. Its free-standing divider begins at Y = 180.25 and ends at 414; the open transition beside the launcher is intentional. Do not add a filler wall there. The upper orbit has a 24 mm nominal clear corridor and turns back toward (230, 432). The two lower guides lead toward the flippers; use the handed left and right files.

### 3. Flippers and launcher

Place the left and right flipper guard bases, including their apron floor extensions, on the deck before installing the rotors. Install a pedestal at each pivot, (88, 72) and (232, 72). Lower the correct handed rotor onto its pedestal and insert its sleeve from above. The sleeve flange stays above the rotor. Fit one M4 × 25 pivot screw and a thin nut beneath the deck at each pivot.

The pivot screw clamps the sleeve and pedestal stack. It must not squeeze the rotor directly. Check unloaded free travel before adding bands: the left rotor moves +46° from rest and the right moves −46°, each stopping against its intended stops. The nominal rotor bore is Ø7.5 around a Ø7 sleeve, with 0.6 mm axial clearance above and below the rotor. Remove burrs if necessary; do not tighten away that clearance.

Fit one band around the left fixed and moving posts as a single loop. Fit one band around the right pair as **two turns of the same band**, both retained below the post caps. Keep the two turns orderly and clear of the rotating arm and printed edges. The fixed posts are at (32, 43) left and (255, 44) right. At rest the moving posts are at (88, 42) and (232, 42). Install the handed guard covers and their five M4 × 16 screw/nut pairs: three on the left and two on the right. These fasteners retain the guard bases and their 3 mm floor extensions. The upper apron shells go on after the bands and guard covers, with four separate screws rooting their columns directly to the deck. Install them before lowering the front end-panel assembly into their blind PET slots.

For the launcher, attach the housing with two M4 × 16 screws and nuts. Leave **both the guide cap and band guard removed**. Lower the rod into the open housing along −Z, engaging the travel-stop lug in its closed slot. The knob, strike head and lug prevent sliding the assembled rod in from the front; do not force that path.

Install the one adjustable anchor in the lowest preload position first: its band-post centre is (274, 130), with its mounting screw at (274, 120). The two alternate post positions are Y = 136 and 142, using screw holes at Y = 126 and 132. There is one anchor, not three. Fit one band between the fixed anchor post and the moving rod post. At rest the moving post is (274, 70); pulling the knob toward the player moves it in −Y by at most 18 mm, limited by the hard stop.

Load the guide-cap thin nuts from the nearest open ends of the housing before fitting the cap with its two screws. Load the band-guard nuts from the left into their side pockets, then fit the band guard with its two screws. The anchor uses one screw/nut pair, giving seven pairs for the complete launcher. Confirm that the band remains under its caps and that the rod reaches both stops without scraping. Leave it at rest until the enclosure is complete.

### 4. Ramp, bucket, flag and axle

Mount the jackpot frame with four M4 × 16 screws and nuts at (114, 356), (114, 418), (200, 356) and (200, 418). Leave the ramp off while installing the common rocker.

The bucket, hub, crossbar and flag are one printed rocker. Prepare its trim clamp on the bench before lowering the rocker between the frame towers. Insert the 96 mm dowel along +X from the left through the first tower, rocker and second tower. Fit the two axle caps, each with two M4 × 16 screws and thin nuts. The caps retain the dowel ends; they must not force the rocker sideways or eliminate its end clearance.

For that bench preparation, fit the solid-PLA trim block underneath the flag arm. Its nominal local Y coordinate is **−42 mm relative to the axle**, corresponding to board centre **(182, 334)** at rest. Insert its M4 × 16 clamp screw upward through the trim block and arm slot and fit the nut on top of the arm. Mark this starting position. Tighten the clamp before checking balance.

After the rocker and axle caps are installed, lower the ramp into its deck recesses and mount it with two pairs at (122, 338) and (166, 338). The ramp runs from Y = 274 to 377.2, with its rolling floor rising from Z = 0 to 40. Its exit sits above the bucket entry; do not sand that designed drop away.

The axle is at (144, 376, 26). An empty rocker should rest at 0° with the flag down; a captured marble should tip it to the −28° stop and raise the flag. Verify this physically with the screened marble range. Moving the trim toward the player, farther from the axle, increases empty restoring torque and makes tipping harder. Moving it toward the axle has the opposite effect. Adjust only while empty, keep the clamp fully supported in its slot, and retighten before each test. Do not add unqualified ballast or hold the flag down during play.

### 5. Hopper, covered return and collection cup

Install the hopper funnel at (84, 412), capturing its flange with the left and right clamps and four M4 × 16 screw/nut pairs. Its mounting coordinates are (74, 376), (94, 376), (74, 436) and (94, 436). Its throat passes through the deck into return section 0.

Before fitting a return hood to the deck, load its two floor-lid thin nuts downward through the open tops of the tall hexagonal wells. These eight nuts become inaccessible from above once the hoods meet the deck. Fit the four hoods under the deck in numerical order: section 0 runs from the hopper to (24, 324), section 1 continues to (24, 194), section 2 to (24, 84), and section 3 turns toward the front cup at (160, 0). Use their eight separate deck mounting screw/nut pairs. Match the numbered floor lids to the same hoods. Before closing the lids, inspect all neighboring deck nuts and remove debris; no nut or screw tip may project into the rolling corridor.

Fit the collection cup with its two M4 × 16 pairs at (134, 58) and (186, 58). The deck drain opening is X = 145–175, Y = 18–39.5. Keep this opening and the covered return outlet clear.

Close the four floor lids with their eight dedicated M4 × 16 pairs. These screws insert upward from below the floor into the retained nuts above their mounting tabs. The nominal return passage is 22 mm wide × 20 mm high. Align successive sections without a raised rolling edge. The return, hopper and cup together use 22 pairs. Floor lids are removable access panels; do not glue them closed.

### 6. Mission pieces

Install one of the complete layouts below. Every crater or guide uses two M4 × 16 screws and two thin nuts. Tighten evenly and ensure the piece rests flat. The five installed pieces use ten pairs; save no extra pieces for the second layout because it reuses these same five.

### 7. Canopy and apron

Fit the apron shells as described below before installing the front end assembly. Prepare the front and rear end assemblies before rooting their posts. Slide each end's two PET rectangles horizontally into the loose end posts and centre mullion; the mullion's integral upper bracket prevents dropping these panels in from above. Use the correct handed front and rear posts. The two rear adapters connect the rear upright bodies at Y = 480 to their roots at Y = 464; seat each upright in its adapter and install its horizontal M4 × 16 screw and thin nut.

Root the two end assemblies and four identical middle posts using M4 × 25 socket-head screws at X = 5 and 315, Y = 48, 192, 336 and 464. Fit their thin nuts beneath the deck before access is restricted. Support the loose centre mullions until roof screws retain them. With all eight top shoes still off, drop the six side PET rectangles into the open side channels and seat their lower edges. Install the eight top shoes and their horizontal M4 × 16 screw/nut pairs. Fit the two centre roof splices at the interior row junctions.

Before the roof cells cover the joints, slide the thin roof-mount nuts into the side-loading traps on the top shoes, splices and end mullions, from each outer-X mouth toward its screw centre. The trap floors support the nuts when the corner screws are removed. On the bench, make four ordinary roof cells and two captive access-door modules: the front-right loading door and rear-left reset door. Capture each notched roof sheet between its frame and cap using four M4 × 16 panel-clamp screws and nuts. On the access doors, these clamps belong to the moving frame; the lower receiver stays attached to the roof supports.

Each door has two hinge sleeves and two indexed latch levers with sleeves, retained by four M4 × 25 screws and four thin nuts. Insert each hinge sleeve into the moving eye first, then place the eye and sleeve between the receiver clevis cheeks and install the pivot screw and nut. The Ø7 sleeve cannot pass through the Ø4.5 clevis screw bore. For each latch, load the thin nut into its side pocket, place the lever on the pillar, insert the flanged sleeve through it and install the screw. Tightening clamps the sleeve stack while leaving the lever free to lift and turn. Keep the indexing dog intact.

Install the six roof positions in two columns and three rows, with cell origins at X = 0 or 160 and Y = 48, 192 or 336. The enclosure uses the taller supplied posts and end mullions: their upper datum is Z = 124, and the complete roof/access modules sit 24 mm above their local source datums. Use the 96.4 mm high side/end PET blanks listed above; shorter panels leave an opening and must not be used. Each ordinary frame or access receiver has **four separate corner mount screws**; fit all four M4 × 16 screws from above into the preloaded nuts. Open the access door to reach its receiver mounts. These corner mounts and all panel clamps remain fitted during ordinary loading and reset.

Operate the two latches independently: lift a lever 3.3 mm, turn it one quarter-turn, then lower its dog into the OPEN index. Repeat for the other lever before swinging the door outward to its 120° hard stop. To close, lower the door onto its seating pads, then lift, turn and lower each lever into LOCK. The lever's long axis runs front-to-back when locked and across the board when open. Never force a turn with the dog seated. The open door rests against its stop under gravity; it is not locked against knocks or inversion. Keep fingers clear of the hinges and closing edges.

Fit the left and right upper apron shells after the flipper guard bases, rotors, bands and guard covers are installed. Their four M4 × 16 screw/nut pairs root the shell columns directly to the deck at (22, 12), (150, 10), (170, 10) and (174, 47). The columns pass through clearance holes in the floor extensions. The nominal tail openings are 10.1 mm high, with 12 mm overlap in plan and stepped inner pockets. Check that the thumb tails move without rubbing. The apron and all PET panels are part of the enclosure and must be installed before a launch or band-loaded flipper stroke.

## Mission layouts and mounting holes

Coordinates are board X, Y. The crater datum is its centre. A guide datum is its CAD placement point, **not the midpoint between its screw holes**: its holes are offset 3.5 mm toward its open side in the unrotated orientation. At 0° a guide opens toward the player (−Y); at 90° it opens toward the right (+X).

| Mission | Piece | Datum X, Y | Angle | Two screw-hole centres |
| --- | --- | --- | ---: | --- |
| A — Tranquility Approach | Crater 1 | 60, 200 | 0° | (50, 200), (70, 200) |
| A | Crater 2 | 240, 200 | 0° | (230, 200), (250, 200) |
| A | Crater 3 | 220, 280 | 0° | (210, 280), (230, 280) |
| A | Guide 1 | 90, 280 | 90° | (93.5, 270), (93.5, 290) |
| A | Guide 2 | 210, 160 | 0° | (200, 156.5), (220, 156.5) |
| B — Far-Side Slalom | Crater 1 | 120, 180 | 0° | (110, 180), (130, 180) |
| B | Crater 2 | 220, 240 | 0° | (210, 240), (230, 240) |
| B | Crater 3 | 60, 280 | 0° | (50, 280), (70, 280) |
| B | Guide 1 | 170, 220 | 90° | (173.5, 210), (173.5, 230) |
| B | Guide 2 | 227.5, 300 | 0° | (217.5, 296.5), (237.5, 296.5) |

The playfield mounting system contains **48 distinct holes across both layouts**: 28 fixed-route holes, ten Mission A holes and ten Mission B holes. Exactly **38 are occupied in either complete layout**. The ten inactive mission holes remain unused. These counts concern playfield modules, not the additional structural, mechanism or canopy holes.

For fixed-route identification, the 28 fixed holes form these pairs:

| Part | Hole pair |
| --- | --- |
| Left front / middle / rear side | X = 5; Y pairs (80, 140), (240, 300), (400, 452) |
| Right front / middle / rear side | X = 315; same Y pairs |
| Left rear rail | (28, 475), (144, 475) |
| Right rear rail | (180, 475), (296, 475) |
| Lower divider | (275.5, 196), (275.5, 252) |
| Upper divider | (275.5, 344), (275.5, 404) |
| Inner orbit | (275.0452, 430.1963), (256.0545, 433.5449) |
| Outer orbit | (301.7383, 458.7383), (222.1881, 455.2650) |
| Left lower return guide | (28, 150.2), (53.2, 122.48) |
| Right lower return guide | (254.9, 155.8), (251.96, 124.72) |

These coordinates identify holes already present in the supplied tiles. They are not a general drilling grid.

To change missions, remove the marble and let all controls rest. Open the access doors where they provide the needed reach; remove ordinary roof cells as needed using their four corner screws. If a complete access module must come off, follow the supported module procedure under Service and access. Support the deck so the thin nuts are accessible. Remove both screws from one module, lift it along +Z, move it to the new listed datum and orientation, and reinstall the same pair of screws and nuts. Move one piece at a time and verify both holes before tightening. Remove a return floor lid temporarily if it restricts underside service access, then replace it. Check all five pieces against the table and refit every cover before play.

## Physical commissioning before play

1. **Inspect the build.** Confirm tile alignment, stable feet, seated countersinks, retained thin nuts and deburred passages. Verify that the glass marble is undamaged and within the specified diameter and mass range. Remove all loose hardware and tools.
2. **Check unloaded bearings before fitting the bands.** Each flipper and the launcher rod must move to their intended hard stops without binding. The jackpot rocker must turn freely on the dowel. Resolve a pinched bearing or rubbing part before adding band load.
3. **Check the closed controls.** With bands, guards, apron and canopy fitted, test each flipper separately and together. Each must return to rest and keep its band beneath the post caps throughout travel. Start the launcher at its Y = 130 anchor setting and with a short pull. Confirm smooth return, intact stops and no rubbing or escaping band. A correct nominal band size does not prove correct force.
4. **Measure launcher performance.** The design's launch-work ceiling is 0.012 J and is not a measured result. Measure pull force at closely spaced travel positions using a calibrated low-force gauge. Estimate work by adding average force over each interval multiplied by that interval's travel in metres: W ≈ Σ[(F₁ + F₂) / 2] × Δx. Qualify the actual build, including the highest permitted preload/travel combination, and assess containment before normal play. Do not infer low energy from the 18 mm stop alone. Do not use stronger substitute bands or enlarge travel to compensate for poor rolling.
5. **Check gravity return without firing.** At the assembled incline, place one screened marble in the hopper and verify that it reaches the front cup without shaking, pushing or a second marble. Repeat with the smallest and largest intended marbles. Also roll each size into the central drain from several positions across its width and confirm that it reaches the accessible front of the cup. The digital drain check establishes a nominal route beside the return hood, not reliable settling from every entry position. Inspect any catch through the removable floor lids and correct the actual obstruction.
6. **Check the jackpot while the controls remain at rest.** With the rear-left reset door open against its 120° stop, place a screened marble gently in the bucket and keep fingers away from the axle and stops. It must tip fully and raise the flag. Lift only the marble: the empty assembly must lower the flag and return unaided. Repeat at both ends of the intended 4–7 g range, adjusting and securing the trim if necessary. Close the door and seat both latches in LOCK before a launch.
7. **Check the doors.** With the machine empty and controls at rest, check both independent lift-turn-lower latches, hinge freedom, closed seating and the 120° stops. Confirm that each open door rests against its stops on the inclined board, both indexing dogs seat fully and the closed PET edges remain captured. Check loading and reset reach gently; do not force a finger past a tight edge. Correct rubbing or unstable open support before use.
8. **Check enclosure and play routes.** With every cover fitted, progressively test short, controlled launches. Verify containment at the roof, side/end sheets, loading cell, apron and thumb openings. Confirm that marbles roll across seams, pass the launch transition and orbit, reach both flippers and return guides, climb the ramp and enter the bucket without an unsafe rebound. Repeat for both mission layouts. Stop if a marble escapes, a joint shifts, a band rubs, or a part cracks. Check that the taller enclosure stays upright and its posts, mullions, roof joints and captured panel edges do not visibly shift or flex open during handling and progressive low-energy commissioning. Support and carry the board by its base; the canopy is not a handle. Enclosure stiffness and tip stability have not been physically tested.

These are required physical checks, not results provided by the CAD. After basic function is established, record failures and wear over at least 100 cycles of each control and 100 jackpot/reset trials. These counts are a commissioning plan, not a completed durability test or a service-life rating. Reliable scoring shots and the feel of the controls also need testing on the actual build.

## Loading, play and reset

Use only one marble in the machine. Set both controls at rest before opening a door. Unlock the front-right loading door using the independent lift-turn-lower latches described above and swing it to its 120° stop. Leave all four receiver corner mounts and all panel clamps fitted. Lower the marble through the opening and release it gently above the launch lane at approximately **(299, 100, 40)**; raise the fingers a short distance, move them toward the centre of the open aperture, then withdraw upward past the frame. Let the marble settle ahead of the strike face before closing and locking both latches. The resting strike face is at **Y = 70**; a 16.5 mm marble tangent to it has centre Y = 78.25, Z = 8.25. These dimensions identify the cradle, not a request to insert fingers into it. Check actual settling during commissioning.

Pull the launcher toward the player and release it. Begin with a short pull at the lowest qualified anchor setting. Work the two thumb flippers to hit craters and send the marble toward the ramp. A drain into the front collection cup ends that launch. If the marble rests at a front corner, use one finger through the outside opening to ease it slightly back from the low front lip, then nudge it toward the centre. Pinch it from both sides through the two front-corner openings, lift it vertically out of the cup, and load it by hand for the next launch; the machine does not feed itself.

For a jackpot, the marble must remain captured in the sample bucket and the flag must rise. This ends the launch. With controls at rest, unlock the rear-left reset door and swing it to its 120° stop. Reach through the opening to the bucket's two rounded sidewall finger reliefs. Grip **only the marble** near its equator, lift it clear and carry it to the adjacent hopper at **(84, 412)**. Keep fingers clear of the bucket stops and axle. Removing the weight lets the empty bucket and flag return by gravity; verify that return during commissioning. Do not push the flag or rotate the bucket as a reset action. The hopper sends the marble through the covered return to the front cup. Withdraw the hand, close the door and lock both levers before the next launch. Finger comfort and reliable handling must be established on the actual build.

### Scoring

Each player receives three launches. Keep a separate score for each launch and add the three for the game.

| Visible event | Points |
| --- | ---: |
| Contact a crater | 1 for each distinct crater, at most once per launch |
| Enter the ramp and roll back to the field without a jackpot | 2, at most once per launch |
| Capture the marble in the bucket and raise the flag | 10; ends the launch |
| Mission B only: contact all three craters during one launch | 2 bonus points |

A drain ends the launch and preserves points already scored. A jackpot does not add the ramp-return points unless a separate earlier attempt actually returned to the field. Count visible contacts rather than assumed paths. Highest three-launch score wins. For a tie, each tied player takes one extra launch; repeat if needed. For solo play, keep separate best scores for Missions A and B.

## Service and access

Remove the marble and let the controls rest before service. Ordinary access uses the two hinged doors without removing hardware. The four ordinary roof cells lift upward after their four corner mount screws are removed; their separate panel-clamp screws keep each PET sheet captured. Removing an entire captive access module is an occasional service operation requiring support, as described below. Refit all mounts and close and lock both doors before actuating the machine.

For apron access, first open the loading door. Support the entire receiver module and its shared roof carriers while withdrawing its four corner mount screws individually through the open door; the thin mount nuts stay caged in the carriers. Move the withdrawn screws clear of the door sweep. While continuing to support the unfastened receiver, close the door and lock both levers. Lift this complete closed module upward, keeping the receiver, moving frame, PET, cap, clamps and all hinge/latch hardware together. Do not lift it by an open door. Remove the other front-row cell and both middle-row cells, keeping their panel clamps fitted. Support the front centre mullion as its last roof screws come out. Support and remove the now-loose centre splice at Y = 192 with its four caged nuts. Remove the cross screw/nut pairs from the four post shoes at Y = 48 and 192, then lift those shoes with their caged nuts. Lift out the two front side PET panels. Remove the two front post root screws through the open columns while holding their underside nuts. Hold the two front posts, two front PET panels and centre mullion together and lift this end assembly out of the apron slots. Keep loose carriers and nuts together for reassembly.

Support the empty board securely to reach its underside. Remove return floor 3 and hood 3 to expose the apron nuts; their two deck-root screws may stay in the deck while the hood slides downward off them. Hold and unthread the four apron nuts, withdraw the four apron screws from above, then lift the required shell off its guard-base floor. Controls and bands remain at rest until their guards are accessible. Reassembly reverses this sequence: apron before the supported front end assembly, side PET before shoes, and supported mullion/splice before reinstalling the four roof positions. Lower the closed loading module onto its supported carriers, open its door while holding the receiver, then reinstall all four corner mount screws into the caged nuts. Close and lock both levers only after the receiver is secure. Use the same supported closed-module method if the rear-left reset module must be removed.

For launcher service, first remove the right apron using that access sequence, then the guide cap and band guard. Keep the rod at its forward stop, hold the band and unhook it carefully; the band remains stretched even at rest. Lift the rod out along +Z; reinstall it along −Z with **both** covers off. Never force the oversized rod ends through a closed housing. Refit the band, cap, guard, apron and enclosure before actuation. Change the anchor only between sessions with the band unhooked, and requalify the resulting force and containment.

For flipper band replacement, follow the apron-access sequence above, then remove the matching guard while the machine is empty and at rest. Unhook the worn band and preserve the left single-turn/right double-turn routing. Check the pivot sleeve and stop faces before reassembly. Replace a damaged band with the specified section and recheck its complete travel after all guards are closed.

For a blocked return, remove the marble from the top if accessible, support the deck and remove the affected numbered floor lid. Clear the obstruction without driving tools through a closed chute. Inspect the adjoining lip and fastener tips; refit the lid and test gravity return before play. Keep floor lids removable.

For front-right foot service, withdraw its two loosened nuts toward the player (−Y), through the opposite foot openings. The +Y route is obstructed by the deck. Support the empty board before removing a foot.

For axle service, open the required roof and side access, support the empty rocker, remove the left axle cap and withdraw the dowel toward −X. To remove the rocker itself, first remove and lift out the ramp, then remove the caps and axle and lift the clamped rocker assembly upward. The installed ramp obstructs that lift. Service the trim on the bench; the deck prevents withdrawing its screw downward in place. The flag and bucket remain one component. Reassemble in reverse order with the same end clearance and secured trim setting, then repeat the empty/loaded balance checks.

Check hardware seating, PET edges, band condition, dowel straightness and moving-part wear before use. Stop using the machine if a cover is missing, a sheet is cracked, a part is loose, or a moving part fails to return. Keep small marbles, nuts and bands away from children who may mouth them; keep fingers out of the bucket stops, launcher mechanism and covered flipper linkage.

## What the digital evidence establishes

The source package represents real separate printed parts, qualified screw/nut envelopes, both mission layouts, the common bucket/flag axle, the enclosed return and removable covers. Targeted geometric checks examine assembly fit, fastener access, selected marble routes and prescribed mechanism poses. For example, selected playfield passages were sampled using a 22 mm clearance sphere; these are free-space checks along chosen paths, not simulated rebounds or proof that a launched marble follows those paths. Band sweeps represent nominal section and routing, not measured rubber mechanics.

Digital evidence can identify a collision or insufficient nominal passage. It cannot establish friction, actual printed fit, launch energy, a safe rebound envelope, successful human play or service life. The physical commissioning above remains mandatory.
