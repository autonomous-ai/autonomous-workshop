# Socket wall evidence audit

This read-only audit covers J00–J08 on the current written socket-bearing STEP files. Existing native analytic radii establish a **2 mm nominal radial difference for all nine housings**. They do not establish an exhaustive minimum across the relieved roots, slit margins, bond seams or later cut surfaces. The saved evidence contains no identified, unrepaired, current material-wall failure below2 mm. An exhaustive final lower bound remains **unverified**; this is neither an exhaustive socket-wall PASS nor a new measured failure.

No product source or STEP was edited; no build, new geometry measurement, native client, motion sweep or print gate was run. Existing1.2 mm general thickness passes cannot qualify the separate Wish socket-wall requirement of2 mm. Native `validate` proves topology/positive solid validity, not wall thickness.

## Current exact native evidence

Selectors below belong to the named isolated STEP, not the assembled object. Outer-cylinder radius minus spherical-cavity radius is exact from native analytic metadata; it is a reference difference, conditional on intact housing stock.

| Joint / housing | Current native radii and selector evidence | Actual relieved-boundary evidence already saved | Final claim permitted |
|---|---|---|---|
| J00 / head rear | R7.125 outer `#f33`, R5.125 cavity `#f31`; mouthR4.4 `#f47`. [STABLE-FACE-DETAILS.jsonl](STABLE-FACE-DETAILS.jsonl). Difference2. | [FINAL-FINGER-GEOMETRY.json](FINAL-FINGER-GEOMETRY.json) records the separate outer host clearanceR7.425, root web endingY43.5, and open slot centers after that web. Current head code adds socket after host clearance; lateral gill ramps are separate from central socket. This is construction/support evidence, not a final all-face2 mm scan. | Nominal2 confirmed; exhaustive root/finger lower bound unverified. |
| J01 / body01 | R7.125 outer `#f40`, R5.125 cavity `#f24`, mouthR4.4 `#f48`. [NATIVE-BODY12-LEDGER.json](NATIVE-BODY12-LEDGER.json). | [J01-LAND06/REPORT.json](J01-LAND06/REPORT.json) and [actual-wall-probe](J01-LAND06/actual-wall-probe.json) document removal of both measured thin incoming-cap remnants by the2 mm axial root opening. Native openingD8.947766 `#f11`; cylindrical outer-to-opening radial difference2.651117 mm. Root opening, J01Y57.85 and lip3.227856 remain in current source. Absence of the identified cap remnants is local evidence, not a scan of all new boundaries. | Nominal2 confirmed; identified historic cap failure repaired; exhaustive lower bound unverified. |
| J02 / body02 | R6.875 outer `#f35`, R4.875 cavity `#f30`; mouthR4.15 circle `#e98`. [NATIVE-BODY12-LEDGER.json](NATIVE-BODY12-LEDGER.json). | Applied J01 anterior relocation has saved actual cap-to-trimmed-cavity minimum2.024898792 mm with midpoint inside material. Retained roof/branch relief has measured cutter-to-cavity distance2.009762030 mm in [BODY02-REAR-CANDIDATE.json](BODY02-REAR-CANDIDATE.json). Both local constructions remain. These closely bound selected root regions only. | Nominal2 and targeted root distances above2 supported; exhaustive lower bound unverified. |
| J03 / body03 | R6.875 outer `#f27`, R4.875 cavity `#f23`; mouthR4.15 `#e78`. [NATIVE-BODY3-GILLS-LEDGER.json](NATIVE-BODY3-GILLS-LEDGER.json). | Parent-clearance subtraction and straight construction-seam opening are present in current source. No saved targeted distance from all resulting exterior root faces to actual cavity faces was found in this bounded evidence set. | Nominal2 confirmed; actual relieved-root lower bound unverified. |
| J04 / body04 | R6.75 outer `#f57`, R4.75 cavity `#f22`; mouthR4.025 `#f27`. [NATIVE-BODY456-PAW-LEDGER.json](NATIVE-BODY456-PAW-LEDGER.json). | [J04-LAND06/REPORT.json](J04-LAND06/REPORT.json) records actual remaining incoming cap to trimmed outgoing cavity2.248292722 mm; midpoint is inside material. Current J04Y90.525, land0.6 and the body04 rear construction retain the measured repair. Body05 front later changed independently; do not reuse its old volume. | Nominal2 and selected remaining root cap above2 supported; exhaustive lower bound unverified. |
| J05 / body05 | R6.625 outer `#f44`, R4.625 cavity `#f9`; mouthR3.9 `#e21`. [NATIVE-BODY456-PAW-LEDGER.json](NATIVE-BODY456-PAW-LEDGER.json). | J04 candidate report found no incoming-cap face in body05rear; incoming envelope ends before seamY96.8. This establishes absence of that particular risk face, not a measured2 mm bound on every root/opening face. Subsequent front-half plate changes are outside that rear branch. | Nominal2 confirmed; no identified surviving incoming cap; exhaustive lower bound unverified. |
| J06 / body06 | R6.625 outer `#f15`, R4.625 cavity `#f13`; mouthR3.9 `#e44`. [NATIVE-BODY456-PAW-LEDGER.json](NATIVE-BODY456-PAW-LEDGER.json), `J06_rear_socket`. | Current rear has parent clearance and seam-opening cuts. Current front also has straight through-openingD3.277194. Native dimensions and1.2 general-wall result do not determine the minimum socket wall next to those cuts. | Nominal2 confirmed; relieved-boundary lower bound unverified. |
| J07 / body07 | R6.625 outer `#f16`, R4.625 cavity `#f3/#f21`; mouthR3.9 `#f14`; rear root openingR3.790531. [NATIVE-BODY78-LEDGER.json](NATIVE-BODY78-LEDGER.json). | [BODY07-REPAIR/REPORT.json](BODY07-REPAIR/REPORT.json) and [probe.json](BODY07-REPAIR/probe.json): final side-face-to-actual-cavity minimum2.186094963 mm after the45° ramp joins the existing slit. The0.920034753 mm pair is across slit air (midpoint OUT); zero adjacent-face distances mark the opening. Removed pad volumes are all0. Current rear branch matches the applied final polygon. | Nominal2 and targeted side-wall distances above2 supported; open-edge distances are not material thickness. Exhaustive lower bound unverified. |
| J08 / body08 | R6.625 outer `#f9`, R4.625 cavity `#f8`; mouthR3.9 `#f10`; root openingR4.408018 `#f6`, depth1.2. [NATIVE-BODY78-LEDGER.json](NATIVE-BODY78-LEDGER.json). | Derived outer-to-straight-root-opening radial difference2.216982 mm. Source stock endsY126.6; slit beginsY127; current axial mouth land0.6 and lip3.086086. These analytic/plane facts do not examine all relieved transition boundaries. | Nominal2 and root-opening radial difference above2 confirmed; exhaustive lower bound unverified. |

## Exact identity check

Each current STEP hash was compared with the saved native ledger (head with its existing refs/validation binding); all matched. No native import or validity check was repeated.

| Joint | File | Current SHA256 | Saved native identity |
|---|---|---|---|
| J00 | `part_head_rear.step` | `67eb7c391a97c149ec2923af9d5695eef171ead9640fed2fb165ccc6b5555afe` | Matches |
| J01 | `part_body_01_rear.step` | `8695b988cd1796f159d6dc9490820002aee44244de74ff244b8211df9915b628` | Matches |
| J02 | `part_body_02_rear.step` | `5711deaefeb6f9639e4179682c95af2b1adf51f1ed1877053324abdf7972ff3c` | Matches |
| J03 | `part_body_03_rear.step` | `d4984f798cc7fc875be54d025d611ae1ada363680d7b70b4111c2d76289ac3d5` | Matches |
| J04 | `part_body_04_rear.step` | `d19ceeee84e86f0480b3b9bcc273548240fa5ec8bf2b30cee1d99153c18fe5b3` | Matches |
| J05 | `part_body_05_rear.step` | `03fe0e0e609077e107215a86c58b16cfab97d38e3c97f0bf2da9f5979bccbeed` | Matches |
| J06 | `part_body_06_rear.step` | `149e9f0343b2248df9fb863fb5f90a2039672dce6f92f91521248dad347f35c6` | Matches |
| J07 | `part_body_07_rear.step` | `963d1aaa635c78d03d51f1649de1231e28f6a5684085095a02f336683263e913` | Matches |
| J08 | `part_body_08_rear.step` | `7883b38a00ee801e4728ae442f51076a3bd4db65d2025570b32e3fe17e43ece6` | Matches |

## Historical finger audit and source reconciliation

`FINAL-FINGER-GEOMETRY.json` is a historical source snapshot, not a current all-socket wall certificate. Its explicit qualification already says “provided later masks do not reach this free zone” and “final local wall inspection remains required.” Current source identity compared with that audit is below. Changed files include later J04/J08 land decisions and body07 repair; the old J04/J08 endpoints must not be quoted as current. Finger support length is not wall thickness and literal slit length is not effective free beam length.

| Current source | SHA256 | Versus historical finger audit |
|---|---|---|
| `parts/body.py` | `d796a764581db8f9534b70d6779112a9b65e1b15debdb55922a8a675301bd172` | changed |
| `parts/head.py` | `d1d425d1b610e218e7d0431f31f90ca2f04febc1a4f5733bda3a48dfce5771f1` | same |
| `features/joints.py` | `140c62f66916a97a6d402c335ef814e51e69e6246126248d3694cf0cd916510a` | same |
| `params/__init__.py` | `5178488740bcbb55910ba851bad3743db5e8c002f3892b3014e71a3c5f71e6fe` | changed |
| `params/body.py` | `2610ee3d4d8114b974b2e3810675a0392267eefb2d18400adda10509bbe95c64` | same |
| `params/face.py` | `e8eeb2fd077269fd6cdc2127602498b1d2245dc991f98b9f235c91286427cd56` | same |

Source reading confirms: `features/joints.socket` builds radius `cavity/2+WALL`, with `WALL=2`; body stock likewise adds a cylindrical housing before subtracting parent clearance. Body cuts subsequently include spherical/mouth cavities, cross slits, seam openings, selected rear ramps and foot clearances. Head construction includes its root web and later decoration masks. Those operations mean the initial radius difference alone cannot prove all final material ligaments. Preload pads are additions; their intentional interference is not an external wall-thickness defect. Open slits and intentionally open cavity/seam edges can have zero or sub2 face distances through air; they must not be counted as a solid wall without material classification.

## Measured failures reconciled

- Earlier J01 candidate with an unshifted center produced a real1.3646 mm body02 root wall. The applied anterior shift is supported by the subsequent2.024899 mm actual-cavity measurement; the failing candidate is historical.
- The J01 work also found two body01 cap remnants with a1.160845 mm centroid-to-cavity material distance. The final2 mm root opening removes both remnants. Current native opening diameter independently matches the resulting construction.
- Earlier body07 root cap distance0.537708 mm and the prior-v2 thin ledges were replaced by the final ramp/opening. Final side faces are2.186095 mm from the actual cavity, while the0.920035 mm pair lies in air. Treating that air gap as a current wall failure would be incorrect.
- Earlier mouth-lip general-wall failures led to current axial lands. Their later1.2 mm gate passes resolve those general-wall findings, but do not establish the separate2 mm requirement everywhere.

No new repair is prescribed from an unmeasured suspicion in this audit. The remaining evidence gap is the exhaustive lower bound on every final relieved socket boundary; it must be disclosed as unverified unless separately measured. No physical compliance, strength or print readiness is claimed.
