# Mintfin

Mintfin is a mint axolotl-dragon with eight articulated body segments, coral feather gills, a raised fan tail and interchangeable happy and sleepy faces. The design follows the supplied numerical description; no reference image was supplied. The exported neutral happy figure measures 133 × 168.593784 × 93 mm, including the assumed 0.05 mm cured adhesive film under its face details. It fits the 133 × 169 × 93 mm target. The spare face and coupons are separate kit items. Motion remains unverified.

This is a digital prototype. All 48 distinct components have passing isolated geometry, applicable wall, support and visual checks. The current combined STEP has 75 valid solids and no reported clashes across 216 tested pairs at the native tool’s 1 mm³ overlap threshold. All 75 production STEP files passed native geometry validation. Motion remains UNVERIFIED: the earlier full check exhausted its allowance, and the corrected sleepy-face withdrawal was cancelled without a verdict. The current assembly round records motion UNVERIFIED after its allowance was exhausted. Independent visual review passed with the underside attachment views. No physical printing, snap force, pose-holding friction, magnet pull force, fatigue, adhesive strength or durability has been tested. Do not treat the files as a print-readiness claim.

## File map

- `../parts/*.step`: the 75 occurrence-named production files, in millimeters and their intended bed orientation. Each file represents one physical piece and carries its sealed color. For a full kit, print each of these files once. Use these production files when importing into a compatible slicer.
- `part_<role>.step.py`: the 48 editable component generators. `params/`, `parts/` and `features/` contain their shared dimensions and construction.
- `mintfin_spec.md`: dimensions, interface definitions, design history and verification limits.
- `measure/`: recorded checks. Any final `GEOMETRY-NOTES.md` identifies checks left unverified.
- The generated `mintfin.step` combined view shows one figure, its spare face and the coupons. Use the 75 production files in `../parts/` for individual pieces. Static validation does not establish motion or physical performance.

The figure itself has no display base. A spare expression and coupons shown beside it are kit contents, excluded from the figure’s target dimensions.

## Parts and materials

The kit uses 48 distinct geometries and 75 printed pieces. The table counts pieces already represented in the 75 production files; do not multiply those files by these quantities. Front/rear barrel halves are different pieces.

| Part files / group | Print quantity | Color |
|---|---:|---|
| Head front and rear | 1 each | Mint |
| Body 01–08, front and rear | 1 of each: 16 total | Mint |
| Belly 01–08 | 1 each | Cream |
| Left and right legs | 2 each | Mint |
| Claw | 12 | Charcoal |
| Left and right gills | 1 each | Coral |
| Left, middle and right horns | 1 each | Charcoal |
| Common spike / front spike | 7 / 1 | Charcoal |
| Tail left and right | 1 each | Coral |
| Face plate | 2 | Cream |
| Eye / highlight | 2 / 2 | Charcoal / white |
| Nostril | 4 | Charcoal |
| Happy mouth / tongue | 1 / 1 | Charcoal / coral |
| Sleepy lid / sleepy mouth | 2 / 1 | Charcoal |
| Coupon ball half / socket | 2 / 1 | Coral / mint |

Use nine nominal 8 × 1 mm disc magnets: three in the head and three in each expression. Adhesive is needed for construction seams, fixed decorations and magnets; choose one compatible with the actual printed material and magnet coating. Physical fit and adhesive performance require testing.

Requested colors are mint `#a9cdbe`, cream `#e6d6c3`, coral `#ee8c7d`, charcoal `#3d4138` and white `#f6f5ef`. Stock labels green, beige, orange, dark_gray and white may appear in production filenames. Filament colors require a physical swatch match.

## Print and test first

The design settings are a 0.4 mm nozzle, 0.2 mm layers and a 220 × 220 mm bed. Each individual part supplies its intended orientation; support-free geometry checks do not prove a successful print. Keep joint surfaces, slots and magnet pockets free of adhesive or finishing buildup.

Start with the coupon. Bond its two identical ball halves along their flat sagittal faces, preserving the spherical seam. The resulting ball is 9 mm in diameter with a 4.2 mm neck; the female cavity is 9.25 mm. The retaining mouth intentionally obstructs rigid insertion: the socket fingers must flex. Check insertion, recovery, wear and pose holding in the actual material. If it cracks, permanently spreads, binds or will not hold, revise the shared fit and regenerate the mating parts before making the full model.

The adjacent magnet pocket is 8.15 mm in diameter and 1.2 mm deep. Test the real magnet and adhesive allowance; a nominal 1 mm disc sits 0.2 mm below its opening. Neither this pocket nor CAD geometry establishes magnetic force.

## Assembly

1. Pair each numbered barrel’s front and rear halves, largest near the head and smallest near the tail. Dry-check the planar construction seams, then bond each pair. Keep adhesive away from balls, sockets, retaining mouths and finger slots. Bond the head halves on their broad transverse seam and the tail halves on their sagittal seam. Each tail half has one shallow glue reservoir; keep adhesive clear of the ball and neck.
2. Attach one cream belly patch per barrel. The first six bond to the lower front faces; the last two lie horizontally on their underside seats. Belly01 is the distinct 42 mm-wide patch. Belly08 centers at Y126.6 mm; bond only its backed forward half, Y125.5–126.6. Its rear half overhangs below the socket housing with 0.475 mm vertical clearance. Keep this overhang and all socket fingers free of adhesive. Attach the distinct front spike behind the head and the seven common spikes to the remaining crown seats. Keep all decorations clear of the moving joints.
3. Bond each gill and horn to its matching head seat. Attach the front legs to barrel 01 and the rear legs to barrel 04. Check all four soles on a flat surface before curing. Bond three claws to each paw’s flat toe face, with their bases level with the sole.
4. Make both expressions on separate cream plates. Happy uses two eyes with white highlights, the larger smile and coral tongue; sleepy uses two closed lids and the smaller mouth. Each face gets two nostrils. The assembly assumes a 0.05 mm cured adhesive film beneath the details bonded directly to each cream plate. Keep eye/highlight and mouth/tongue relative placement together; the film is adhesive, not a printed spacer. Achieving this thickness and bond strength has not been tested. Use the generated happy and sleepy state views for placement. Their geometry and colors come from the actual model; independent appearance review passed.
5. Check polarity against the same head before permanently bonding all nine magnets. Keep the discs recessed and permanently retained. These magnets and small printed pieces must not remain loose.
6. Once coupon testing succeeds and fixed bonds have cured, connect the body chain and tail using the compliant snap action. Support each socket locally. Stop if any finger cracks or remains spread; a rigid CAD retention result would not establish safe insertion force.
7. Seat one expression in the indexed rim. To exchange it, lift outward along the tilted face normal without levering on the eyes or lids. Magnetic holding and repeated swaps require physical testing.

The intended joint targets are 25° upward bend and ±20° twist. Motion remains UNVERIFIED; no motion range or simultaneous pose combination is certified by this guide.

The supplied state views show the actual model geometry and colors. They are still images and do not prove motion.

The fixed legs bond at two perpendicular inward surfaces. Nominal contact area is 44.325 mm² per front leg and 21.623 mm² per rear leg. These geometric areas do not establish bond strength.

## Project fit/print audit

From this CAD directory, run `"$WORKSHOP_PYTHON" validation.py`. This existing source-level audit checks shared connector dimensions, the nine ball/socket clearance and retaining-mouth equations, neck feasibility at the target bend, magnet-pocket backing, coupon base stock, eight-segment/four-leg counts, named leg attachment owners, and the belly/socket separation arrangement. It reads the shared source parameters without rebuilding solids. Pair numbered front/rear halves and assemble them in the order above; the 75 occurrence-named production files form the physical inventory. These arithmetic checks supplement the native per-solid geometry and bed-footprint checks; they do not prove physical snap fit, motion, adhesion or print readiness.

Final integrated verification returned UNVERIFIED: build, fit and specification audits passed, but motion exhausted the shared geometry allowance and the subsequent native inspection batch did not run. Earlier static checks remain separate evidence and do not turn this final result into a pass. See `measure/verification-pipeline.md` and the sealed geometry notes.

## Included evidence

The delivery includes `measure/verification-pipeline.md` and `measure/geometry-inspection.json` for the final UNVERIFIED result. Earlier completed static evidence is retained in `measure/assembly-native-final.json`, `measure/signature-native-final.json`, `measure/production-native-ledger.json` and `measure/production-export-ledger.json`. The figure-envelope measurement is in `measure/envelope-final.json`; attachment and adhesive-film findings are in `measure/leg-attachment-audit.json` and `measure/face-adhesive-film.json`. `measure/socket-wall-evidence.md` distinguishes nominal wall dimensions from the exhaustive minimum-wall check that remains unverified. Historical `design/` paths in the specification refer to development records; the included files above provide the preserved delivery evidence.
