# Bounded stand assembly audit

Inspected the assembled `product/gear_vortex/gear_vortex.step.py` using the materialized CAD `inspect refs`, `measure`, `frame`, and one explicitly requested pair-only `interfere` operation. Assembly STEP SHA-256 at inspection: `ab495b282869f4d764327c12a795636617f7f1dc77a4903f1ea9dae5be1dff7d`. Evidence applies to those bytes; subsequent repairs require corresponding renewed checks. No product source or STEP was changed by this audit.

## Measured failure requiring repair

`inspect interfere ... --refs o1.11,o1.12` measured a carrier/sun overlap of **2.7840567146234676 mm³**, exceeding the tool's default 1.0 mm³ threshold. Both occurrences were selected explicitly: `o1.11 carrier_black`, `o1.12 sun_yellow`. Exactly one pair was tested, with zero skipped pairs, zero truncation, and no tool errors. Exit code was 2.

Clash bounds are X −0.585671555…+0.585671555, Y −33.3000001…−28.2999999, Z 91.7249999…148.2750001 mm. These locate the interference at the two vertical carrier pillars alongside the sun's upper and lower tooth tips. The proposed narrower-pillar change belongs to the parent assembly repair; this audit did not implement or verify it. Raw report: `carrier-sun-interference.json`.

## Stand interface measurements

All 15 requests in `measurement-requests.jsonl` completed successfully in `measurements.jsonl`. Distances below are the documented tool's projection on the specified axis, not arbitrary face-origin Euclidean distances.

| Interface | Face selectors | Measured result |
|---|---|---|
| Stem root on lid | o1.3.f6 / o1.2.f24 | Opposed planes both Z=3; zero Z gap |
| Collar saddle on stem shoulder | o1.4.f6 / o1.3.f7 | Opposed planes both Z=107.5; zero Z gap |
| Stem root D-flat / pedestal socket | o1.3.f5 / o1.1.f39 | X=3.2 / 3.4; 0.2 mm clearance |
| Stem tongue / collar socket X wall | o1.3.f10 / o1.4.f10 | X=3.5 / 3.7; 0.2 mm clearance |
| Stem tongue / collar socket Y wall | o1.3.f11 / o1.4.f11 | Y=3.0 / 3.2; 0.2 mm clearance |
| Foot trim on pedestal | o1.6.f3 / o1.1.f2 | Both Z=14; zero Z gap |
| Axle D-flat / collar bore flat | o1.7.f35 / o1.4.f8 | X=8.1 / 8.3; 0.2 mm clearance |
| Rear cap / collar rear face | o1.8.f2 / o1.4.f2 | Y=6.3 / 6.0; 0.3 mm axial gap |
| Front support cap / collar front face | o1.9.f3 / o1.4.f4 | Y=−6.3 / −6.0; 0.3 mm axial gap |
| Orange disc / sun rear face | o1.10.f2 / o1.12.f4 | Y=−24.3 / −28.3; 4.0 mm axial gap |

The stem frame is translated to (0,0,3) with its axis vertical. The collar frame is translated to (0,6,120); its local Z axis maps to global −Y. These agree with the mating planes above.

## Central passage

The axle's continuous cylindrical inner face `o1.7.f32` has measured analytic radius 7.0 mm, axis direction (0,−1,0), and centerline X=0, Z=120. Its axial extent is Y=−41…13.5, a 54.5 mm through-bore. The collar cylinder `o1.4.f7` is coaxial, with radius 9 mm and flat X=8.3. The stem tongue top `o1.3.f12` is at Z=110.5, 9.5 mm below the bore axis and therefore 2.5 mm below the nominal 14 mm optical passage. This clearance is derived from the measured axis-to-plane distance and analytic bore radius.

These selected interfaces support the intended 14 mm clear passage through the axle/stand. They do not establish complete assembly freedom from optical occlusion or interference by every other occurrence. Full assembly checks remain the parent gate's responsibility.

## Limits

No full-assembly interference or validation was run. No assembled still-image packet was available in the assembly artifact paths at the end of this audit; this report makes no assembled visual-inspection claim. It does not establish physical fit, retention under load, print readiness, or motion performance.

Occurrence bounds for rotated round bodies are loose transformed boxes and must not be interpreted as exact diameters. In particular the rotated lid's enlarged reported X/Y bounds are not evidence of an oversized lid. Analytic cylinder radii and planar mating datums were used for the measurements above.
