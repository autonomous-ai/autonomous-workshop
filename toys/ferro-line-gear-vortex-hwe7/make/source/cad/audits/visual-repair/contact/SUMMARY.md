# Current sampled contact audit

All **238/238** samples pass: two arms × seven meshes × 17 states. Maximum measured separation is **3.33149893365259e-07 mm**, below the unchanged 0.000001 mm limit. Maximum absolute overlap is **1.45371362322014e-06 mm³**, below the unchanged 0.001 mm³ limit. All sample keys, pair counts, loaded phases, half-turn transforms, source snapshots and result hashes were audited.

The diagnostic constructs exact BRep geometry from current SHA-bound source snapshots and tests each mesh separately at fixed centers over one relative tooth-pitch interval. The coverage includes both sun-to-first-planet meshes and every neighboring planet pair. It establishes sampled flank contact for this diagnostic.

It does **not** establish continuous contact between samples, simultaneous coupled assembly motion, insertion/retention, torque transmission, physical fit or print readiness. Current formal round-4 motion remains **UNVERIFIED** (exit 3, no condition results). Current operating presentation and independent review 2 remain pending.

Raw records are in `runs/all17-r1/`. The independent read-only binding audit is `../visual-repair-documentation/contact-audit.json`. Historical six-gear evidence is not promoted.
