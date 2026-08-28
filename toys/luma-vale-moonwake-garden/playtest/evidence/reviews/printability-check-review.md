# Independent printability-check review — Moonwake Garden

## Recommendation

**PASS** for digital print-readiness of the sealed Made revision. No Make repair is required by this check.

This is not evidence of a successful physical print. The snap fit, detent feel, PETG overhang behavior, dimensional shrinkage, fatigue, and support-free result remain physically unobserved and must stay qualified.

## Sealed subject and scope

- Playtest subject: `315ed802ae675a75367c0b9be4dc6bfc6ff8859885366227a81a009b0fe003c7`.
- Made contract: `artifacts/make/r0002/made.json`, SHA-256 `c19c13c6c9d71d2e38e95e4c56b380ba524b9466faf05ec223922c469b49d827`, Made identity `f02f4e2ee6273ecc7007ddea9fe772886615a9d4b97387213d4aeb1e0a707f8a`.
- Sealed product tree identity: `d31e05cf5a70714e41d2f26cf2bc7e4ef25a2cbd63545cda651a527c3f76874a`.
- CAD verification summary: `artifacts/make/r0002/product/cad-verification.json`, SHA-256 `e75b8c456a40312a25ad224f831b43113239f0ecb044cfd7b5f0cb79e7d943dc`.
- Full pipeline record: `artifacts/make/r0002/product/cad/moonwake_garden/measure/verification-pipeline.md`, SHA-256 `e691dcd7340c782586c486476bd19b7ccc95e9ce057fc0a7c8d118093c53dc8b`.

The actual print targets are exactly the three `part_*.step.py` entries. Each declares `PRINTABLE = True`; the combined `moonwake_garden.step.py` declares `PRINTABLE = False`. `assembled.step` and the three-shell `assembled.stl` are review assemblies, not one-piece slice targets. This boundary is consistent in the project README, source declarations, custom fit audit, and assembled sidecar.

## Audit findings

### 1. Bed stance and envelope — pass

The fresh final pipeline ran strict source fit on all three entries against a 220 × 220 × 250 mm bed and exited 0 (`verification-pipeline.md`, command 4). Each generator returns its broad rear face at Z=0.

I independently reread the sealed STL bytes and reran the canonical mesh checker on each shipped print target:

| print target | sealed STL SHA-256 | observed mesh envelope | bed / stance |
|---|---|---:|---|
| front garden mask | `33362fc1afb6f473ba6da19a375742068ad9df88a0b2927f8111e2c34daad835` | 84.0 × 76.0 × 2.2 mm | PASS; minimum Z is numerically zero |
| rear chassis | `3c34737691d268a24b99363955a3cca099f82ec1301a4c1a32ed6317a378d9f1` | 84.0 × 76.0 × 6.0 mm | PASS; minimum Z = 0 |
| sector rotor | `21cc3acf381a978083e76565999a2b24fc78a7e83c898c7ff8dc9bdf7a7c347e` | approximately 69.92 × 69.92 × 1.2 mm | PASS; minimum Z = 0 |

All three hashes match their entries in the sealed Made manifest. Their footprints are comfortably inside the declared bed. The complete assembled envelope remains 84 × 76 × 6 mm, as recorded in `assembled.step.json` (SHA-256 `7e24aa249b4615ef9345d5a3de3c974dec30f5f398deedaa804f874cecb0d7e3`).

### 2. Mesh integrity and one-part-per-target — pass

The sealed pipeline exported and checked every part STL (`verification-pipeline.md`, commands 12–20). My independent rerun on the same bytes found:

| target | triangles | boundary edges | non-manifold edges | pinched vertices | connected shells | signed volume |
|---|---:|---:|---:|---:|---:|---:|
| front garden mask | 7,680 | 0 | 0 | 0 | 1 | 9.89 cm³ positive |
| rear chassis | 13,816 | 0 | 0 | 0 | 1 | 6.53 cm³ positive |
| sector rotor | 1,404 | 0 | 0 | 0 | 1 | 3.51 cm³ positive |

All three also passed consistent winding and zero sliver-triangle checks. Thus each slicer-facing artifact is watertight, manifold, positively oriented, and one connected shell. The three connected shells in the assembled review STL are expected and are not substituted for the individual part checks.

The corresponding STEP bytes are separately sealed as:

- `part_front_garden_mask.step`: `d7169bb232ec64b012342561a1c495460e5019c9d3e288f1f7d511a6ec3276dd`
- `part_rear_chassis.step`: `9298787557eda744ce323b4e41a5654b495b9984f81ff8664ee55d4345b2f9a9`
- `part_sector_rotor.step`: `b15efcb1ac92fe89dfdeaeda19ae353bc30cd0fecfa2384374e2b906b809c054`

The fresh pipeline reports successful topology validation for the declared entries, and `fresh-output-reproducibility.json` (SHA-256 `df437a1c3f0199c2975eebe4710b6344efe6ae9936f0c954ee804f81c9f72e12`) binds byte-identical STEP and mesh results across two independent fresh builds.

### 3. Wall thickness and 0.4 mm nozzle findings — pass

All reports were measured on the sealed exported STLs with a 0.4 mm nozzle and an 0.80 mm two-line wall gate:

- Front mask: `measure/thickness-front_garden_mask.md`, SHA-256 `eb08de513996ea87cd668f357b9f10706821e0ab75af2f124d419a1430e7b20c`; 0 of 396,467 samples below the gate, median 1.60 mm.
- Rear chassis: `measure/thickness-rear_chassis.md`, SHA-256 `889fb37a48507a81c9536b9ac4bea242fb70cc6415bcf1ed32424f5081b143ed`; 0 of 326,436 samples below the gate, median 1.78 mm. One additional sample is within the report's ±0.08 mm measurement uncertainty, but it is not a failing sample. The 1% hollowability warning implies only 0.01 cm³ estimated savings and is not a print-readiness defect.
- Sector rotor: `measure/thickness-sector_rotor.md`, SHA-256 `ec1e8b322980db161460f343f4f513d88824f7e2741cc479dacfcdbe7aeff298`; 0 of 353,760 samples below the gate, median 1.20 mm.

The source also removes the former sub-nozzle grip islands by blending them into one 0.30 mm-deep trench with a continuous 0.90 mm floor, and the deterministic spec audit enforces a 1.8 mm minimum petal-chamfer ligament (observed 1.944357 mm).

### 4. Support-free geometry rationale — pass digitally, physically unverified

The broad-face-down construction is coherent for all three targets:

- The rotor is a 1.2 mm planar disk with through-cuts and a shallow top-side grip recess; it has no elevated downward-facing feature.
- The front mask is a 1.6 mm broad plate with vines and moon relief added upward. Its enlarged rear petal entries taper through only the first 0.30 mm using ruled 45° entries, avoiding a sharp unsupported underside.
- The rear chassis grows from a continuous Z=0 rear datum. The guide is seated on the rear annulus; thrust pads have explicit full-footprint cylindrical supports; collars and spindle are rooted in the base; the split snap profiles grow by short ruled transitions and have blunt pilots rather than horizontal cap ledges.

An independent facet scan of the shipped meshes found no elevated nearly-horizontal downward face on any print target. The rear snap transitions contain a very small sloped region (3.73 mm² total across four snaps) just beyond a nominal 45° normal threshold, but there is no horizontal ledge and its largest radial transition is roughly 0.223 mm over 0.20 mm height—less than one 0.4 mm extrusion line of lateral projection. That does not justify a digital block, but actual PETG support-free behavior remains printer/process dependent and unobserved.

### 5. Assembly limitations — correctly bounded

Nominal assembly geometry is coherent but not physically proven:

- Source-derived fits give 0.30 mm radial spindle clearance, 0.40 mm radial rotor-guide clearance, 0.10 mm radial snap-stem clearance, and 0.30 mm axial rotor clearance (`measure/check_fit.py`, which passed in pipeline command 5).
- `measure/motion_snap_proxy.json` (SHA-256 `32055aa1a6889927d6c02ceb3bb62b21c20689d09bc192bcafc069c80a0e61f4`) and `measure/snap-seating-check.md` (SHA-256 `736740a2323f663a2cdbc16d64b22a417da449adf09b207caa9feb0b5c3f3582`) show only that the compressed 3.2 mm proxy clears the four 3.4 mm holes.
- `measure/motion.json` (SHA-256 `1621fa43a99db9e36d5f852f6ce6834b0fe413eaae80d1965dea6e0e6bac9dd6`) separately shows that uncompressed heads block withdrawal and that the front captures the rotor. These are rigid collision results, not an elastic snap model.
- The head's exact maximum plan radius is 1.894111 mm inside a 1.950 mm relief, leaving only 0.055889 mm nominal radial clearance. That is geometrically positive but printer/process sensitive.

Accordingly, insertion force, snap survival, retention, removal, whitening, shrinkage, and detent behavior require same-material physical observation. Their absence does not contradict this digital pass because the sealed product makes no physical-fit claim.

### 6. Claim audit — pass

No reviewed artifact overclaims a physical print. `product.json`, both READMEs, the CAD brief, assembled sidecar, verification summary, reproducibility record, thickness reports, and snap proxy evidence consistently distinguish digital checks from physical outcomes. In particular, the Made contract explicitly says that no physical print, printer-process fit, or support-free outcome has been observed.

## Conclusion

The three actual sealed print targets have correct bed stance, fit the declared bed, are watertight/manifold/positive single-shell meshes, pass the 0.4 mm nozzle thickness gate, and have a credible broad-face-down support-free construction. The evidence is hash-bound and reproducible. **Verdict: pass**, with no implementation feedback. Carry the existing physical limitations forward unchanged into Release and do not describe this result as a successful print or verified physical assembly.
