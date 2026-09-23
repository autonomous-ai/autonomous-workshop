# Core dimensions from current exported STEP

All 46 targeted `measure`/`frame` queries completed successfully. Values below come from measured STEP planar datums and analytic cylindrical surfaces, not product-source assertions. The inspected STEP is the byte-identical audit copy `current-assembly.step`, SHA-256 `b09ea2ab604b26262bea462a682304e0816cd87bb7c3a5fd4807b8d114d19997`. Its fresh references contain 45 occurrences, 40 leaves, 40 shapes and 6,098 faces. Part names were rediscovered after the assembly regrouping.

| Requested dimension | Measured geometry | Selector evidence |
|---|---|---|
| Central optical axial gap 4 mm | 4.0 mm between orange front plane Y=−24.3 and sun rear plane Y=−28.3 | o1.8.f2 / o1.9.f4 |
| Orange OD 55 mm | Analytic cylindrical R27.5, hence OD55 | o1.8.f1 |
| Orange thickness 1 mm | 1.0 mm | o1.8.f2 / o1.8.f3 |
| Bezel OD 70 mm | Analytic outer arc R35, hence nominal OD70; knurl cuts interrupt that cylinder | o1.23.2.f1 |
| Bezel ID 58 mm | Analytic inner wall R29, hence nominal ID58; see local boss intrusion below | o1.23.2.f484 (also f487 in face facts) |
| Bezel thickness 4 mm | 4.0 mm, Y=−43.3…−39.3 | o1.23.2.f2 / o1.23.2.f4 |
| Sun face width 5 mm | 4.9999999999999964 mm | o1.9.f4 / o1.9.f5 |
| All 12 planet face widths 5 mm | Each 4.9999999999999964 mm | Individual selectors in table below |
| All 12 planet bores 4.7 mm | Each analytic R2.35, hence ID4.7 | Individual selectors below |
| All 12 planet journal posts 4 mm | Each analytic R2.0, hence OD4.0 | Individual selectors below |

## All planet occurrences

| Planet name | Face-width selectors | Bore selector | Matching carrier post selector |
|---|---|---|---|
| gear_1_1_yellow | o1.11.f308 / f309 | o1.11.f307 | o1.23.1.f181 |
| gear_1_2_yellow | o1.12.f320 / f321 | o1.12.f319 | o1.23.1.f28 |
| gear_1_3_yellow | o1.13.f332 / f333 | o1.13.f331 | o1.23.1.f41 |
| gear_1_4_yellow | o1.14.f344 / f345 | o1.14.f343 | o1.23.1.f54 |
| gear_1_5_yellow | o1.15.f356 / f357 | o1.15.f355 | o1.23.1.f67 |
| gear_1_6_yellow | o1.16.f368 / f369 | o1.16.f367 | o1.23.1.f80 |
| gear_2_1_yellow | o1.17.f308 / f309 | o1.17.f307 | o1.23.1.f99 |
| gear_2_2_yellow | o1.18.f320 / f321 | o1.18.f319 | o1.23.1.f110 |
| gear_2_3_yellow | o1.19.f332 / f333 | o1.19.f331 | o1.23.1.f123 |
| gear_2_4_yellow | o1.20.f344 / f345 | o1.20.f343 | o1.23.1.f136 |
| gear_2_5_yellow | o1.21.f356 / f357 | o1.21.f355 | o1.23.1.f149 |
| gear_2_6_yellow | o1.22.f368 / f369 | o1.22.f367 | o1.23.1.f162 |

Matching post/gear identities use measured cylindrical centerlines in the current assembly. The 4.7/4.0 mm diameter difference gives 0.35 mm nominal radial clearance; that arithmetic is not a physical-fit test.

## Bezel opening distinction

The nominal circular inner wall is ID58. Mounting-boss faces `o1.23.2.f485` and `o1.23.2.f486` each measure R3.5; their axes lie at X=0, Z=88.5 and 151.5. A separate `measure --axis z` gives 63.0 mm center separation. The facing boss crowns therefore leave **63−3.5−3.5=56.0 mm** along the central vertical opening, at Z92…148. This audit does **not** claim an unobstructed full ID58 circular passage through the bezel. The parent was informed of this dimensional distinction. This audit does not decide whether the nominal ring ID or an unobstructed circular aperture is the intended design criterion.

## Stale cached reference evidence

The initial documented `inspect refs` query targeted `product/gear_vortex/gear_vortex.step.py` and reported STEP hash `ab495b282869f4d764327c12a795636617f7f1dc77a4903f1ea9dae5be1dff7d`, with 41 occurrences and 6,093 faces. At that same inspection the actual exported `gear_vortex.step` had SHA-256 `b09ea2ab604b26262bea462a682304e0816cd87bb7c3a5fd4807b8d114d19997`. Thus those initial cached refs were not evidence for the current export.

The current export was copied without changing bytes to this audit directory and inspected as a fresh raw STEP target through the documented tool. Fresh refs report its correct hash and 45 occurrences. Only these fresh selectors were used for the dimensional queries. The original mismatching output is retained as `refs.json`; fresh output is `current-refs.json`, with name discovery in `occurrences.json`. Exact query context and final live-STEP comparison are saved in `cache-discrepancy.json`. No product source or product cache was repaired or overwritten by this audit.

## Evidence and limits

`measurement-requests.jsonl` / `measurements.jsonl` contain 43 successful requests and responses. `bezel-boss-requests.jsonl` / `bezel-boss-measurements.jsonl` contain three more. `measured-summary.json` extracts the main dimensions, radii and selectors. `faces.json` and `planet-faces.json` retain the selector discovery facts.

This audit establishes the named static dimensions only. The 4 mm axial plane separation does not prove visibility through all other assembly solids. No full validation, full interference, motion check, stand recheck, source edit, physical test, or print-readiness verification was performed. Exact physical diameters were derived from analytic cylinder radii rather than loose transformed occurrence boxes or tessellation extrema. Final integrated verification remains root-owned.
