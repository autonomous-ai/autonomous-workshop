# Cybercab reference and mechanism specification

This is a mechanised reference adaptation. Coordinates are x0 at tail, x180 at nose, y0 at centreline and z0 at floor. The one supplied side photograph establishes the silhouette; unseen width, underside, latch and drive are designed. No logo, lettering, modern branded livery or commercial kit geometry is reproduced.

## Observed reference ledger

| Status | Evidence | Design consequence |
|---|---|---|
| Observed | `wish-references/ref-01-cybercab-side.png`, SHA256 d1fd9d7374d34bb011e693808d669bc3d05c20eff4834a7809c6553d02f167bd | Authoritative visible reference |
| Measured | Foreground alpha bbox x91,y50,width1524,height509 pixels, image-to-cad measurement in `../../research/image-measurement.json` | Ratio2.994 gives60.12 mm height when authored length is180 mm |
| Observed, approximate hand landmarks | Rear wheel centre(390,414), front(1346,441), upper roof near(815,55), tapering nose at image right | Preserve wheelbase and low fastback read; these are not automatic landmark detections |
| Observed | Gold angular body, swept dark greenhouse, large dark/disc wheel forms, diagonal side lines | Gold body and two black window inserts carry the principal colour landmarks |
| Inferred | Bilateral symmetry and four wheels; transverse shape unseen | No claim that width78 mm or roof section was measured from photograph |
| Authored |180 ×78 ×60 mm envelope, equal33 mm wheels, level axle centres | Mechanism adaptation rectifies photographic perspective rather than claiming prototype scale |
| Omitted | Opening doors, interior, tiny lamps, fine trim and lettering | Avoid fragile or unsupported detail; no function is implied for omitted features |

The current side polygon runs through (0,39),(3,40),(30,47),(45,52),(60,56),(82,59.5),(97,60),(110,58),(125,51),(140,42),(150,37),(175,29.5),(180,25),(180,9),(5,9), in millimetres. These are authored coordinates guided by the reference, not direct prototype measurements. Wheel arches retain a preserved upper strip and provide at least2 mm radial clearance around the16.5 mm wheels. Their rear relief is adapted for the nose-down print orientation. Dark window inserts replace the earlier proposed paint-only finish.

## Part tree and interfaces

Eight printed occurrences from six unique geometries: one chassis, one body, one front axle with integral wheel, one rear axle with integral wheel, two keyed end wheels and two identical window inserts. Purchased elastic is the ninth assembly occurrence, represented by an installed envelope and never a printed part. Window inserts are1.4 mm thick in1.6 mm recesses and require plastic-compatible adhesive; no unverified press fit is claimed. Optional rear tyre loops supplement grip.

The chassis floor spans z9..12, with central clearance x24.5..125,y±6.5 for the low elastic strand. Journal centres are x34/148,y±27,z16.5; shafts are6 mm and journal bores6.5 mm, with5 mm bearing lands. Wheel track is70 mm, assembled wheelset width77 mm. The rear spool radius is4.2 mm, width9 mm, with a loose open finger; the front anchor is atx134. Source parameters and measured exported solids govern final interfaces.

Four T rails at x71/108,y±20 capture the body sleeves vertically. Their closed −X sleeve ends limit forward shell movement; the integral chassis thumb latch engages a body striker to limit rearward movement. Press the latch inward1.9 mm, slide shell−4 mm and lift for service. The rectangular tooth occupies x104..107,y12..15.2,z9..23 and has no closing ramp. Hold the latch during closure and opening; automatic snap closure is not an operating instruction. The positive vertical chain is body→sleeve lower lips→T heads→stems→chassis. Exact checks must show locked retention and a collision-free depressed-latch/service sequence; a written description alone is not proof.

Nominal sidewall is2.4 mm; inner roof is offset vertically3.6 mm, which is not identical to surface-normal roof thickness. Dedicated thickness checks remain necessary. The chassis latch bends in its XY printing plane; its1.9 mm source deformation is a geometric service state, not a material fatigue model. Each axle prints upright on its integral wheel; the separate end wheel prints socket-up. Use a brim to stabilise the tall axle on its broad wheel bed contact. Bond each 3.4 mm square key into the derived 3.9 mm socket after dry fitting; adhesive axial retention and strength are physically unverified. The shell prints nose-down with internal axial buttresses and a flat nose contact face. The thumb beam and tooth start on the chassis print plane, isolated by a clearance slot. These stances require exact thickness and overhang checks. Window inserts print flat. No general support-free claim is made.

## Elastic drive and limits

The loop extends longitudinally between front anchor and rear finger. Rolling backward wraps the loop on the rear spool; elastic contraction is intended to rotate the rear wheels forward. Loose rear engagement is intended to drop the spent loop rather than reverse-wind. The purchased round-cord envelope in `elastic_lib.py` has nominal radius0.7 mm and twelve chords per semicircle with rounded joins. Its installed centreline chord perimeter is219.184 mm at0° and229.631 mm at−90°. These lengths do not specify a relaxed purchase length or a material strain limit; physical tension and stiffness remain unknown. Begin physical commissioning with one-quarter rear-wheel turn and do not exceed that commissioning limit. No powered physical quarter-turn run has been demonstrated. Full rigid rotational clearance checks do not establish permission for full-turn elastic winding. Stop on binding, snagging, whitening, latch damage or slip. Purchased-loop dimensions remain provisional until physically fitted; no certified elongation, force, fatigue life, run distance or traction performance is asserted. The envelope path length increases10.447 mm from0° to−90°; this is geometric path change, not strain measured from a known relaxed loop.

## Vault lessons and response

`rubber-band-motor` resolves to `mechanisms/rubber-band-motor`; recorded checks are in `../../research/vault-check.json`. Short journals and0.5 mm diametral clearance address axle-journal-friction, followed by an unpowered physical roll check. Optional traction loops and conservative winding address traction-loss. A listed replaceable band and quarter-turn commissioning address band-fatigue without inventing a safe material limit. The backward-roll instruction addresses wind-direction-ambiguity. Hand-accessible latch and loose-loop rehooking address tool-dependent reset. XY beam orientation addresses interlayer-loaded-root but does not prove fatigue. Exact-state drive and shell-service sweeps must address unswept-drive-cycle. Wall and support gates answer underbuilt-shell and support-dependent-geometry. The explicit adaptation ledger answers likeness-wall without changing the reference or claiming a gate waiver.

## Research lineage

[Science Buddies rubber-band car activity](https://www.sciencebuddies.org/stem-activities/rubber-band-car) supports elastic axle propulsion and separating wheel traction from axle friction. [Science Buddies challenge FAQ](https://www.sciencebuddies.org/science-fair-projects/engineering-challenge-2024-FAQ) explains why tied rear elastic can tighten again after unwinding. Accessed2026-09-08; page revisions unspecified; publisher rights retained, no external CAD copied. Normal-TLS step.parts queries for rubber band, plain bearing and axle returned zero items; JSON receipts are in `../../research/catalog-*.json`. A successful empty search is not proof that no catalog component exists. Custom printed journals avoid dependence on unavailable supplier geometry.

## Audit targets

The following machine-readable values are design targets for exact-source/export checks, not a claim that each check already passed.

```json
{
  "length": 180,
  "width": 78,
  "height": 60,
  "shaft_d": 6,
  "bore_d": 6.5,
  "wheel_r": 16.5,
  "rear_x": 34,
  "front_x": 148,
  "axle_z": 16.5,
  "journal_w": 5,
  "spool_r": 4.2,
  "anchor_x": 134,
  "printed_occurrences": 8,
  "unique_printables": 6,
  "wall": 2.4,
  "roof_vertical": 3.6,
  "rail_release": 4.0
}
```

Winding convention: backward rolling is negative rotation about global +Y. The geometric powered release runs from−90° to0° for forward +X travel. Rear loop centreline radius5.1 mm clears the radial finger and its printable buttress in the sampled installed envelope. The tensioned material shape and loaded contact remain unqualified. At−90° the rear semicircle lies behind the finger toward−X. This installed geometric envelope does not qualify material deformation or prove loaded contact. Rear endpoints are(39,±5.1,16.5) mm at0° and(34,±5.1,21.5) mm at−90°; front endpoints remain(134,±4.2,14.5) mm.

### Print repair: keyed end wheels
The assembly now has eight printed occurrences, six unique printable files. Each wheelset is split into one wheel with upright axle and a separate end wheel. A 3.4 mm square key enters a derived 3.9 mm square socket with 0.25 mm clearance per face; bond after dry assembly and keep adhesive out of journals. The key transfers torque; adhesive axial retention remains physically unverified. Print each axle on its integral wheel with +Y upward and the end wheel with its socket facing up. The rear spool has a tapered underside and the finger has a supporting rib. Arch relief opens to the skirt bottom to eliminate a thin tip. This supersedes earlier integral-wheelset print instructions.
