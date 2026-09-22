# Gear Vortex construction specification

[assumed] Dimensions are millimeters. This invented sculpture follows the text Wish; no reference image was attached. Its intended identity is the dark 14 mm through-hole, passive orange core and two shrinking brass gear spirals on a continuous matte-black field. Identity remains subject to fresh independent rendered review. There is no emitter, motor, magnet or handle.

## Datum, gears and envelope

[assumed] The wheel origin is global (0,-25,120). Local x maps to global X, local y to global Z, and local z to negative global Y. Each printed part starts at bed Z0 within 220 x 220 x 220.

[assumed] Two arms are complete 180-degree copies. Each carries14/15/18/20/22/23/26 teeth, invoking the explicit fewer/larger-gear fallback rather than meeting11–21 per arm. Centers follow r=37.5exp(0.2049theta), theta=0..3.2825391564912385. Each arm spans188.0756397534 degrees. Pitch distances from sun outward are37.5,21.75,24.75,28.5,31.5,33.75,36.75 mm. Bounded alternatives do not prove global impossibility or waive the dense-disc identity requirement.

[assumed] Gears use module 1.5, 20-degree pressure angle, 0.85m addendum, 1.25m dedendum and 5 mm face width. Each flank loses 0.18 mm at the pitch circle. Five swept spokes alternate handedness; nominal normal web width is 2.6 and radial root rim 3. Smallest hub OD7.2/bore4.7 runs on a 4 mm post with 0.35 radial play. Raised seats are 0.3 high; caps leave 0.4 axial freedom.

[inferred] The qualified seven-gear source calculation gives minimum tip chord0.8463804119 mm, ideal contact ratio1.2881928333 and nonneighbor planet-envelope gap3.8941615285 mm nominal/3.1941615285 mm after two0.35 mm journal excursions. Maximum center-distance residual is2.8422e-14 mm. These are analytical results, not CAD contact or physical proof. Nominal radius94.2491178524, OD188.4982357049 and height214.2491178524 mm. Including both main and planet radial play gives swept radius94.9491178524, OD189.8982357049, height214.9491178524 and pedestal clearance11.0508821476 mm. Planned wheel rearY=-25 to stem radius6 gives19 mm axial separation; unchanged core/stand placements still require current assembly checks.

## Core, grip and axle

[assumed] The stationary 36-tooth sun has OD56.55, five curved spokes and local Z3.3..8.3. The rotating bezel is OD70/ID58, 4 high and 6 radially wide at Z14.3..18.3. Mounting centers are (0,+31.5) and (0,-31.5), with 7 mm bosses extending inward from the ring. Carrier pillar bodies are separately 5.6 mm diameter; their upper ends remain 4 mm. Thus ID58 is locally interrupted by the bosses. Two 4.4 mm holes receive 4 mm pillar ends; caps begin Z18.7.

[assumed] The orange annulus is OD55, D-opening18 and thickness1 at Z-1.7..-0.7. Nominal spacing behind the sun spokes is 4; captured axial float must stay within 3–5. Its D-flat x8.3 engages the axle flat x8.1. Ambient illumination supplies its appearance. Carrier thickness is3, arms7 wide and main bore18.3. An integral black annulusOD188/ID58 fills localz0..3 around the logarithmic ribs. Its29 mm inner radius leaves the orangeOD55 core visible; original hub links cross that opening. The plate adds darkness and roundness, not additional gears. There are14 planet posts and two bezel pillars. Opposing carrier posts and pillars, including thread starts, are complete half-turn copies.

[assumed] The hollow axle is OD17.6/bore14, Z-38.5..16. Rear thread length is 27 and front length7.3, with custom pitch3.6/depth0.6. Both ends of each threaded section have 1 mm tapered external leads. A V runout at print-local Z27±1.2 has minimum radius8, leaving nominal wall1 around the bore. Exact wall thickness remains an inspection obligation.

[assumed] The repaired OD23 shoulder spans Z-2.7..-1.7, thickness1. Its 4.4 mm ramp starts at Z-7.1 with radius8.1, supported by the D-flat. The shoulder front remains -1.7, preserving orange placement and optical spacing. Three hollow main caps, OD23 and height7.2, start at Z8.7, -18.7 and -38.5. Female thread radial clearance is 0.15.

[assumed] Small caps are OD7.2, height4.8, custom pitch2.4/depth0.4 and radial clearance0.15. Their inlet/outlet flares expand 0.8 radially over 1.2 axially. Thread fit, loosening, strength and torque remain physically unverified.

## Repaired stand

[assumed] The roof-down pedestal is OD105, height14, nominal wall/roof3 and cavityOD99. Its three 14-degree entry slots are restricted to radial band49..51.35, preserving the central boss. Minimum entry wall1.15 requires exact inspection.

[assumed] The lid has a 3 mm plate, total height8.6, baffle radius49.25 and three 12-degree tabs locked by 30-degree rotation. Tab section (r,z) is (48.75,2.8),(50.85,5.1),(50.85,6.3),(48.75,8.6): outer flat height1.2 and flank angle47.602562 degrees. Matching groove tip radius51.1 leaves wall1.4; its tip spans Z4.85..6.55 and root Z2.276190..9.123810. Verify insertion and closed capture. No anti-rotation detent is claimed. The 24 x 6 x 1 finger recess leaves a 2 mm roof and nominal 6 mm bridge. Use solid ballast pieces.

[assumed] The pedestal retains its 8.4 mm D socket/flat x3.4 and 12.4 mm stem recess. A D-conical transition runs from Z10.2 (radius4.2, flat3.4) to Z13 (radius6.2, flat6.2), replacing the flat shoulder. It begins below the circular stem flare at Z11..13 and keeps the expanding flat at 45 degrees.

[assumed] The stem is OD12 with an 8 mm D tenon, flat3.2 and length8; its root is global Z3. The upper shoulder is Z107.5 and the 7 x 6 x 3 tongue ends at Z110.5, below the sightline. Collar OD25, width12 and D-bore18/flat8.3 are centered at global (0,0,120). These keyed gravity seats are removable and are not carrying handles.

[assumed] The brass rim has top OD99, radial top width1.2, height1.2 and flat bottom width1.0. Actual source placement is Z12.69..13.89 on the receiving groove flank, 0.11 below the earlier nominal Z12.8..14 placement. Its receiving groove opens 1.6 wide at Z14, narrows to 1.4 at Z12.9, then closes at a V apex Z12.165. Nominal remaining roof is 1.165 and V flank angle46.397 degrees. That 0.11 mm seating drop is already included in the assembly placement; physical retention is unverified. Foot trim is OD17/ID12.4, height2 at Z14..16. Stand builders assign black except for the two brass trims.

## 8. Mechanism and verification

Power boundary: hand input at the bezel; no functional electrical load. This is a manually driven compound planetary train with a fixed sun, two carrier-mounted chains and two mirrored arms. The declared translation and rotation tables use the same kinematic parameters as the source placement.

Feasibility assertions are implemented in `validation.audit()` before construction. For example, the pitch-centre condition is:

```python
assert abs(hypot(*CENTERS[0]) - M*(SUN_TEETH + TEETH[0])/2) < 1e-8
```

Provenance tags distinguish design-selected values `[assumed]`, derived geometric results `[inferred]`, and native measurements `[observed]`. Design values are editable in `params.py`; tags do not imply physical testing.

Close the ballast lid, seat stem/collar, capture the keyed axle with two support caps, then add orange, carrier, sun and front main cap. Add planets and caps, followed by bezel and its two caps. Reverse these paths for removal. Lift by the base; remove wheel and stem before opening the lid.

[assumed] The coupon uses production 4 mm posts/4.7 bores, seats, threads and a14/15 pair at21.75 centers. Print the coupon, one extra14T, one extra15T and two caps. The separate coupon posts sit at x±10.875 mm. Historical16/18 coupon geometry is not current production. No physical coupon, print, user trial, coast or strength result is claimed.

[inferred] For carrier angle C and stationary sun, planet index i=0 at the inner end has relative factor (-1)^i36/z_i and world factor 1+(-1)^i36/z_i. Positive-drive initial phase adds (-1)^(i+1)(i+1)*0.48/z_i to PHASES. Reversal consumes backlash. CAD contact, a coupled cycle, fine tooth contact, insertion and retention need separate evidence under the current motion policy. Preserve complete mirrored solids, including spoke and thread orientation.

Repaired parts require renewed build, visual, thickness and overhang checks, followed by assembly verification. No threshold is lowered. Measured failures require repair; interrupted or cancelled checks are UNVERIFIED. Existing first-round failures describe the old geometry. The old six-gear math-audit is historical. Current analytical qualification is ../../visual-repair-qualified-candidates.json, robust branch; it does not certify the changed BReps, assembly, print geometry or motion.

[inferred] The2mm spiral-wrap envelope condition applies between nonmeshing planets on the spiral arms. The sun is the hub, not a successive wrap: its nearest nonmeshing planet has 1.1200966507 mm nominal tip-envelope gap and0.4200966507 mm after both main and planet 0.35 mm journal excursions. No2mm sun-to-nonmeshing-planet gap is claimed.

[inferred] Assembly repairs: the carrier bezel pillars are5.6mm diameter, independently of the7mm bezel bosses. At radius31.5 this leaves0.425mm nominal radial clearance to the sun tip envelope and0.075mm after0.35mm main-journal excursion. The front axle thread is now clipped to the continuous x8.1 D-flat so keyed sun and orange parts can pass its crests. Thread engagement remains physically unverified.

[observed] Historical six-gear assembly: Existing materialized CAD measurements in ../../core-dimensions/measurements.jsonl report an orange-to-sun-spoke plane gap of 4 mm, orange thickness 1 mm, sun and all 12 planet face widths 5 mm, bezel height 4 mm, bezel nominal outer/inner radii 35/29 mm, orange outer radius 27.5 mm, planet bore radius 2.35 mm and post radius 2 mm. These measurements concern the copied assembled STEP and the named selectors; they do not establish all geometry gates, physical translucency, bearing friction or printed fit. These prior measurements must not be promoted to current14-planet evidence; current source/assembly rebinding and verification are pending.


## Current inventory, exact layout and evidence state

[assumed] Current sculpture has44 leaf occurrences. There are21 printable roles: seven planet sizes, sun, carrier, bezel, orange annulus, small cap, hollow axle, main cap, pedestal, lid, stem, support collar, two trims and coupon. Sculpture uses two of each planet size and16 small caps (14 planets plus2 bezel); three main caps. Coupon kit adds a plate, one14T, one15T and2 small caps:49 printed pieces total,18 small caps total. No isolated gear is added.

[assumed] Exact ArmA center/phase table follows; ArmB copies each complete solid by180 degrees. Loaded phase is nominal phase plus positive-drive offset. Hands alternate negative/positive from the inner end; do not replace complete-half-turn duplication by tooth-phase equivalence.

|Teeth|X mm|Y mm|Nominal phase rad|Positive-drive offset rad|Hand|
|---:|---:|---:|---:|---:|---:|
|14|37.5|0.0|0.22439947525641335|-0.03428571428571429|-1|
|15|35.87309337606704|21.689068095171887|0.04002936222264469|0.064|1|
|18|21.420558914052613|41.781025382213016|0.3244642572276242|-0.08|-1|
|20|-4.980873717822746|52.51482037674069|0.07385525480778199|0.096|1|
|22|-35.98585763777823|46.95235939950222|0.12895513399309627|-0.10909090909090909|-1|
|23|-61.26252663182039|24.588269778736763|0.0645155331752616|0.1252173913043478|1|
|26|-72.7455099051878|-10.321665700200548|0.12942642114129627|-0.12923076923076923|-1|

[inferred] New14T and15T window radial spans1.525/2.275 mm and sampled tangential apertures1.6953/1.9043 mm are source-profile checks only; new exact wall/overhang/mesh gates are pending.14T lies below the14.53 matching-rack undercut threshold; this is a directly printed involute<HOME> profile, with positive ideal active-roll minima, not a claim of undercut-free rack manufacture.

[observed] Workflow status: Seven-gear visual repair implemented in source; new geometry and independent visual verification pending. Earlier audits are historical snapshots. Formal motion at assemblyr3 was UNVERIFIED, not passed. No print-ready or physical-performance claim. The previous independent review rejected the sparse six-gear silhouette. Current fourteen gears and black field require fresh independent identity review; backing alone is not proof of density.

[observed sources] Wish: ../../../../../WISH.json; completed repair handoff: ../../visual-repair-design-supplement.md; exact qualified values: ../../visual-repair-qualified-candidates.json (robust); bounded screen: ../../visual-repair-search-summary.json. Previous design/, core-dimensions/, mesh-contact/ and old motion reports remain revision-specific historical evidence.
