# Seventeen-sample contact audit result

All **102 discrete BREP measurements** across six adjacent gear pairs meet the unchanged limits: distance ≤1e-6 mm and common volume ≤0.001 mm³. Exactly **48 new midpoint samples** were measured; the **54 original samples** were reused without alteration. No phase correction is indicated for this source snapshot.

| Teeth | Total samples | New samples | Maximum gap mm | Maximum common mm³ |
|---|---:|---:|---:|---:|
| 36/16 | 17 | 8 | 1.53822177742213e-07 | 0 |
| 16/18 | 17 | 8 | 1.77635683940025e-15 | 1.47889730471604e-06 |
| 18/20 | 17 | 8 | 0 | 0 |
| 20/22 | 17 | 8 | 5.59436665017959e-08 | 0 |
| 22/24 | 17 | 8 | 0 | 0 |
| 24/26 | 17 | 8 | 0 | 0 |

Global maximum gap: **1.5382217774221251e-07 mm**, from the reused sun 36/planet 16 sample (old index 7; dense index 14). Global maximum common volume: **1.4788973047160396e-06 mm³**, from the reused 16/18 nominal sample. The added samples have maximum gap **5.5943666501795884e-08 mm** (20/22 at dense index 7) and maximum common volume **0 mm³** as reported by the kernel.

The maximum per-point interval travel bound is **0.32581751934691017 mm** along its arc, with chord displacement **0.32580934148586405 mm**. Both are below 0.35 mm. This occurs at the 16-tooth tip radius 13.275 mm and angular interval 0.02454369260617026 rad. See `MIDPOINT-METHOD.md` for every gear's radii, angular steps and travel bounds.

Evidence: `midpoint-results.jsonl`, `midpoint-results.json`, and merged `contact-results-17.json`. The merged rows explicitly distinguish original and added measurements. Original source hashes remain unchanged; `midpoint-product-comparison.json` confirms the live gear construction files and relevant parameter values matched the snapshot at audit start.

Relative-pair signs remain driver +d, follower −(za/zb)d. This is a fixed-center geometry diagnostic only; it creates no operating animation and does not replace the root whole-cycle motion gate. The sun must remain stationary in the product world frame. Sampling does not establish continuous contact, physical fit, or print readiness.
