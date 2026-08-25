# Digital Playtest and Deliver evidence

Every check returns `passed`, `failed`, or `held`, plus exact artifact hash,
tool and version, configuration hash, timestamps, structured measurements,
limitations, and captured errors. Missing or malformed output is `held`.

Minimum AI Playtest evidence:

- project schema, expected inventory, path safety, and artifact freshness;
- B-rep validity and expected solid/shell count per canonical part;
- strict mesh topology per printable output;
- assembly transforms, forbidden interference, and intended contacts;
- calibrated fit checks for every declared mate;
- declared motion samples and collision results, failing closed on boolean error;
- bed packing, not merely each part's individual footprint;
- slicer-backed profile, orientation, supports, thin-wall warnings, time,
  material, and machine envelope;
- deterministic renders and independent form/beauty review;
- project-specific rules, safety checks, and unresolved physical claims.

## Core receipt measurements

These are engine-neutral minimums, not a complete validation protocol. A
validator configuration may require stricter thresholds and extra fields. A
core check may be `passed` only when all fields on its row have the stated JSON
type and meet the pass condition:

| Check ID | Required measurements and pass floor |
|---|---|
| `manifest` | `inventory_valid` (boolean) is `true` |
| `brep` | `valid_solids` (integer) >= 1; `invalid_solids` (integer) = 0 |
| `mesh-topology` | `watertight_parts` (integer) >= 1; `non_manifold_edges` (integer) = 0 |
| `dimensions` | `measured_parts` (integer) >= 1; `out_of_tolerance` (integer) = 0 |
| `interference` | `poses_tested` (integer) >= 1; `forbidden_intersections` (integer) = 0 |
| `bed-packing` | `beds_used` (integer) >= 1; `out_of_bounds_parts` (integer) = 0 |
| `slicer` | `profiles_checked` (integer) >= 1; `slicer_errors` (integer) = 0; `support_material_grams` (finite number) >= 0 |
| `form-review` | `views_reviewed` (integer) >= 3; `blockers` (integer) = 0 |
| `safety` | `hazards_found` (integer) = 0; `review_scope` is a non-empty string |

Counts are parsed observations, not self-authored promises. The evidence file
must retain the per-part, per-pose, per-view, or per-hazard detail behind each
aggregate. A one-part threshold does not waive the manifest's full inventory.

Physical claims are not Playtest result IDs. Deliver binds the exact print,
printer/material/calibration inputs, hands-on QA measurements, packing, and
shipment receipts. A single Deliver test does not waive any other critical
claim, and its absence must never be filled by an AI prediction.

Do not accept these substitutions:

- triangle area for wall thickness;
- bounding-box adjacency for assembly connectivity;
- a process exit code without parsed measurements;
- a self-authored narrative for deterministic geometry evidence;
- one successful pose for a full motion envelope;
- rigid interference analysis for compliance, fatigue, friction, or release.

Passing Playtest requires a content-hashed manifest and digital receipts from
the exact current artifacts. Any source/config/tool change invalidates
downstream receipts until regenerated. Deliver later binds physical production
and QA to those approved bytes.
