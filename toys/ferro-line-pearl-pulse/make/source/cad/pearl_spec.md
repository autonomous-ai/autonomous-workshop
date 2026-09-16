# Pearl Pulse — current construction specification

Original text-derived mechanised jellyfish from WISH.json; no supplied photograph and no species-replica claim. All dimensions are original design decisions in millimetres. This document supersedes preliminary dimensions in the initial inventor handoff. `params.py` and the live part builders define the exact geometry.

Confidence tags: `[assumed]` identifies original engineering dimensions, selected fabrication settings or an untested performance target; it does not imply measurement from a reference image. `[inferred]` identifies an algebraic consequence of those dimensions. No physical measurement is claimed.

## Required read

A predominantly pearl-white, thin scalloped bell above a slim stand; eight slender articulated bead chains around four sinuous inner ribbons. Blush pink, pale blue and lavender accents use four actual filament colours total. A winding key below the bell stores rubber-band energy; a common sliding ring coordinates a 4 mm bell dip with outward/lifted tentacle roots. Hand pressing separates the follower from the cam and uses the same ring. Approximately 30 seconds of quiet pulsing is a design target, not measured performance. [assumed]

## Fixed and moving datums

- Foot Ø58×5.2, integrated hollow stand Ø10.2/bore Ø7.4 up to z97. Collar seats carrier at z75.2. A positive axial key fixes carrier rotation. [assumed]
- Carrier columns at R27.5, azimuth 112.5/202.5/337.5. Inner arms route through 67.5/157.5/337.5 and R20 arcs. Socket floors 1.2. Central annular stop top z84.3. [assumed]
- Frame top z104.6. Eight tangent pivots at R29, z91, every 45°. Fork gap 4.0, root thickness 3.2, pivot Ø2.4<HOME> bore Ø3.0. Pins have removable distal C-clips. [assumed]
- Sliding ring floor z88.3..89.5, radii 20.2..25.2. Guide bore 10.8, outer 16.4, height 5.5. Keeper z92.5..93.7, with eight horn-arm exit windows and two return-elastic passages. Three clipped pins at R21 and 22.5/157.5/292.5 retain it; local bosses keep material around the bores. The guide reaches the physical carrier stop after 4 mm. [assumed]
- Each rigid root has a 7 mm inward horn and an 18 mm downward chain anchor. Design relation `d=7 sin(theta)`; at d=4, theta=34.8499°, the anchor moves 10.2857 mm outward and 3.2282 mm up. Bead settling is unverified. [assumed]
- Three bell posts at R25.3 and 22.5/142.5/262.5 have actual bayonet heads. The bell seats 0.4 below its initial nominal datum: rest crown 117.6, rim 99.6; pressed crown 113.6, rim 95.6. No floating nominal pose. [assumed]

## Bell and corona

- Bell maximum Ø82, nominal 18 high; crown Ø54. Sixteen shallow radial scallops. Predominantly 1.2 mm wall, locally reinforced opening and wider concealed socket walls after numeric thickness failures. No vertical scallop height is claimed. [assumed]
- Pearl, blush and mist are three registered co-print solids; accent centres moved from (−72, −48) to (−65, −41) degrees to avoid cutting sockets into thin colour slivers. They are bonded material regions, not separate wedges to snap together. [assumed]
- Each of eight PIP strands is one root plus eight independently separate bead solids, pitch 7.2, width 6.4, height 7.7. Captive Ø2.4 pins in Ø3.2 eyes have 0.4 radial clearance and tapered retaining heads. Their source print layout, not the hanging assembly pose, is the print target. [assumed]
- Four flat-printed ribbons at R12, 45/135/225/315 degrees: length 54, width 5.2, thickness 1.2, sinusoid amplitude 2.2/wavelength 18 after a 2.4 mm straight mounting neck. Their root flanges rest on the yoke above its slots. [assumed]

## Drive and elastic interfaces

- Cam working plane `z96+x/7`, track R14. A spherical R0.6 follower is tangent at rest with centre `z98-0.6 sqrt(1+1/49)`. Manual pressing creates a separation; no clutch needed. [assumed]
- Cam/top 100, central web bottom 98.6. Shaft shoulder 97.4..98.6, square coupling 3.2 in 3.6 sockets. Small-chamfer octagonal upper journal fits a 4.6 bore and keeps 1 mm walls beside its retention slot. Positive cross-key and thrust washer prevent downward extraction. Stack upward clearance 0.2. [assumed]
- Cup working floor 101.2, stator face 102.0, nominal grease gap 0.8, minimum 0.6 at the axial limit. Primary annulus R5.6..9.0. Noncontact labyrinth is grease-retaining, not leakproof. [assumed]
- The central journal boss is relieved to z101.6 above the cup floor at z101.2, leaving 0.4 nominal axial clearance and 0.2 at the allowed upward endfloat. [assumed]
- Opposed underbell key lugs carry actual raised clockwise-from-below arrows. True corner sweep R23.20. Maximum 16 turns from relaxed; number specified in instructions rather than claimed as printed text. [assumed]
- Lower anchor locks +45° about Z and seats +0.2 vertically. Positive motor torque loads a fixed stop. Upper hook pocket floor 85.2 supports the rubber loop. Both hooks are real voids with removable loading paths. [assumed]
- One natural-rubber motor loop, relaxed doubled length 70, strip 4×1. Two return loops approximately 56 mm relaxed circumference, strip 1×0.4, girth-hitched through the fixed rounded slots and moving Ø1.8 eyes. Return contact separation approximately 31.5 at rest, 35.5 pressed before wraps. Hitch length/material response need physical calibration. [assumed]

## 8. Powered system / mechanism

### 8a. Drive and selected archetype

The non-electrical drive is a rubber torsion motor rotating a tilted face cam above a spring-return spherical follower. A sliding yoke carries the bell and captures the inward horns of the tangent-pivot tentacle roots. Return rubber loops pull the follower toward the cam; the grease annulus resists cam rotation. Hand pressing separates the follower from the cam and uses the same yoke linkage. This cam-follower arrangement provides a direct vertical output without an additional crank, coupler or geared escapement. The delivered `parts/drive.py`, `parts/moving.py` and `assemblies/pearl.py` implement this architecture; `README.md` describes its operation and service limits.

The motor band is anchored between the positively stopped lower bayonet anchor and the shaft's lower C-hook. The underbell key winds clockwise viewed from below; release lets stored rubber torque turn the cam in the opposite direction. The shaft shoulder, cross-key and thrust washer locate the rotary stack. Service uses the removable bell, clips, cross-key and lower anchor described in `README.md`. There are no electrical loads, wires or batteries.

### 8b. Governing parameters and output

`params.py` owns the shared dimensions; the dimensions above describe those same interfaces rather than a second independently adjustable mechanism.

| Parameter | Meaning | Value | Confidence |
| --- | --- | --- | --- |
| `STROKE` = 4.0 | Bell/yoke downward design travel | 4.0 mm | [assumed] |
| `HORN_LENGTH` = 7.0 | Fixed pivot to inward horn axis | 7.0 mm | [assumed] |
| `ROOT_LENGTH` = 18.0 | Fixed pivot to first chain axis | 18.0 mm | [assumed] |
| `PIVOT_R` = 29.0 | Fixed tangent pivot radius | 29.0 mm | [assumed] |
| `PIVOT_Z` = 91.0 | Fixed pivot height | 91.0 mm | [assumed] |
| `CAM_TRACK_R` = 14.0 | Follower working radius | 14.0 mm | [assumed] |
| `FOLLOWER_NOSE_R` = 0.6 | Spherical follower radius | 0.6 mm | [assumed] |
| `DRIVE_AXIAL_END_FLOAT` = 0.2 | Bounded upward rotary-stack clearance | 0.2 mm | [assumed] |

A cam revolution produces one depression and return. The ideal linkage relation is `d = HORN_LENGTH * sin(theta)`; the root-angle and anchor-travel values stated above follow algebraically. The pressed bead illustration is an authored static pose, not a solved gravitational equilibrium or a verified motion path. [inferred]

### 8c. Algebraic feasibility conditions

These source-parameter assertions express necessary geometric conditions. The project audit `measure/check_fit.py` checks shared clearances, the physical stop and finite-radius follower contact without constructing a motion sweep. The assertions do not prove insertion, retention under real load, friction performance or operating motion.

```python
import math
from params import (
    STROKE, HORN_LENGTH, GUIDE_BOTTOM, SUPPORT_STOP_Z,
    CAM_CENTER_CLEAR_R, CAM_TRACK_R, ROTOR_R, FOLLOWER_NOSE_R,
    GREASE_GAP, DRIVE_AXIAL_END_FLOAT, SLOT_HEIGHT, PIVOT_D,
)
assert 0 < STROKE < HORN_LENGTH
assert math.isclose(GUIDE_BOTTOM - SUPPORT_STOP_Z, STROKE)
assert CAM_CENTER_CLEAR_R + FOLLOWER_NOSE_R < CAM_TRACK_R
assert CAM_TRACK_R + FOLLOWER_NOSE_R < ROTOR_R
assert GREASE_GAP - DRIVE_AXIAL_END_FLOAT > 0
assert SLOT_HEIGHT > PIVOT_D
```

### 8d. Unverified physical behaviour

Rubber stiffness and torque, hitch consumption, grease rheology, joint friction, clip compliance, fatigue, silence, naturally settled bead shapes and timed runtime need physical verification. Approximately 30 seconds remains a target. Motion checking is disabled by the operator's immutable Make option; no motion manifest, sweep or animation is required or claimed in this spec. [assumed]

## Fabrication and evidence boundary

Same-family PETG in pearl #F4F1E8, blush #E6BFCB, mist #BCD5E5, lavender #C4BDD8. No paint, motor electronics, purchased rigid gearbox or artificial decorative motion. Standard nozzle 0.4; bed 220×220×220. Bell crown down, support upright, frame inverted, carrier/yoke/keeper/cup flat, cam top down, ribbons/retainers/shaft on broad faces, PIP strands in supplied flat layout. Exact numeric and native visual checks are recorded per source role. [assumed]

Motion verification is disabled by immutable MAKE-OPTIONS.json. No sweep, animation, independent motion review or successful motion claim. Still images show designed static states only. No physical print, tactile fit, endurance, sound or timed operation has been tested. Spark has no Playtest stage.
