# CAD Reconstruction Evaluation Scoring Guide

This document explains how the `evaluate-cad-reconstruction` skill scores reconstructed CAD projects. It is meant for users who need to run the skill, interpret the reports, and decide which reconstructed models need human review.

The skill reports three separate scores:

- `printability`: how likely the exported mesh is to print successfully.
- `physical_correctness`: whether the in-scope parts are separated, connected, fitted, contacted, and movable as intended.
- `feature_retention`: whether the reconstruction preserved the intended object features and semantics.

Each score is on a `0..10` scale. Floating point scores are allowed.

## Score Classes

Printability and physical correctness use the same class labels:

| Score range | Class | Meaning |
|---|---|---|
| `8.0..10.0` | `easy` | Low-risk; probably acceptable unless the report contains important caveats. |
| `4.0..7.99` | `hard` | Risky or partially broken; should usually get human review. |
| `0.0..3.99` | `impossible` | Severe failure; likely unusable without repair or reconstruction. |

Feature retention uses a semantic class scale:

| Score range | Class | Meaning |
|---|---|---|
| `9.0..10.0` | `excellent` | Important features are preserved. |
| `8.0..8.99` | `good` | Mostly preserved, with small or moderate issues. |
| `5.0..7.99` | `review` | Several important features are altered or missing. |
| `< 5.0` | `poor` | Core object semantics or function are missing. |

## Project-Scale Scoring

Evaluate a project, not only one STL, whenever possible.

A reconstruction project often has:

- one assembled STL;
- separate part STLs;
- STEP files;
- `spec.md`, `README.md`, reconstruction reports, `params.py`, `main.py`, `parts/`, `features/`, or `assemblies/`;
- generated render images.

The assembled STL is useful for detecting accidental fusion, disconnected bodies, and final layout. Separate part STLs are useful for per-part printability and part-to-part physical checks. The docs/code/renders are necessary for deciding what should be checked.

Some projects export reusable canonical part files instead of one file per assembly occurrence. For example, a stand may have one `screw.stl` but four placed screws in the assembled model. Treat these separately:

- canonical parts are unique shapes;
- placed instances are physical occurrences in assembly pose.

Physical correctness checks should use placed instances whenever placement matters. Canonical part files alone are not enough for contact, clearance, collision, relative pose, or motion checks.

## Artifact Policy

The skill should leave only the final evaluation report.

During evaluation, generated files should go under a temporary evaluation directory such as:

```text
<project>/.eval_tmp/
```

Temporary files include:

- generated render PNGs;
- generated `physical_conditions.json`;
- raw `printability_report.json`;
- raw `physical_correctness_report.json`;
- temporary feature-retention JSON;
- split component STLs;
- placed-instance STLs exported from an assembly;
- proxy meshes for external objects;
- temporary STEP/STL/3MF exports;
- parameter-variant exports and probe outputs.

After the final report is written and validated, delete the temporary directory. Do not delete original project files, user-provided exports, source specs, code, or pre-existing assets.

The final report should be self-contained. It should include enough details from the raw metric reports, condition manifest, condition results, missing-helper notes, render observations, and feature-retention assessment that the intermediate files are no longer needed.

## Printability Score

Printability is a risk score, not a yes/no verdict. A mesh can have minor issues and still score highly if those issues are likely repairable or harmless for slicing.

Run:

```bash
python3 skills/evaluate-cad-reconstruction/scripts/score_printability.py \
  --assembly <project>/<assembly>.stl \
  --parts <project>/<part-a>.stl <project>/<part-b>.stl \
  --json-out <project>/.eval_tmp/printability_report.json
```

If the project has only one STL, pass it as `--assembly`.

### What The Script Measures

For each STL, the scorer measures:

- triangle count;
- bounding box and mesh extents, for reporting only;
- surface area and signed mesh volume;
- degenerate triangle count;
- watertightness and bad boundary/non-manifold edge count;
- connected component count;
- tiny disconnected components;
- best print orientation among six axis-aligned orientations;
- bed contact area in that best orientation;
- unsupported overhang area in that best orientation.

Build-volume, maximum dimension, and bbox-size checks are intentionally removed. A large model should not be penalized just because it exceeds a default printer volume.

### Orientation Handling

The scorer assumes the user can freely orient the part. It evaluates six axis-aligned orientations and chooses the one with:

1. lowest unsupported overhang fraction;
2. largest bed contact area as a tie-breaker.

The selected orientation is reported as `selected_orientation`.

This is still an approximation. It does not search arbitrary angled orientations, split a model, add supports, or simulate slicer-specific support generation.

### Per-Mesh Deductions And Caps

Each mesh starts from `10.0`.

Hard failures:

- empty mesh: score `0.0`;
- non-finite coordinates: score `0.0`;
- failed STL load: score `0.0`;
- zero thickness in any axis: cap at `3.0`;
- zero enclosed volume: cap at `3.0`;
- severe open/non-manifold boundaries: cap at `4.0`.

Non-watertight handling:

- A mesh is `watertight` when it has no bad boundary/non-manifold edges.
- If not watertight, the scorer computes:
  - `bad_edge_count`;
  - `bad_edge_length_mm`;
  - `bad_boundary_surface_ratio = bad_edge_length_mm / sqrt(surface_area_mm2)`.
- The mesh is treated as severe only if:
  - `bad_boundary_surface_ratio >= 0.50`, or
  - `bad_edge_count >= 32`.
- Minor non-watertight meshes are recorded as a risk factor, not automatically made unprintable.

Other deductions:

- degenerate triangles: `0.05` per triangle, capped at `1.5`;
- disconnected components: `0.4` per extra component, capped at `2.5`;
- tiny disconnected components: `0.5` each, capped at `2.0`;
- bed contact area below `25 mm^2`: subtract `2.0`;
- unsupported overhang fraction above `25%`: subtract up to `3.0`;
- unsupported overhang fraction above `10%`: subtract `0.8`;
- triangle count above `500,000`: subtract `0.8`.

### Project Printability Combination

The project score combines the assembly and part scores:

```text
project_score = 0.7 * worst_mesh_score + 0.3 * average_mesh_score
```

This intentionally weights the weakest part heavily, because one unprintable part can make the project fail.

Additional project-level behavior:

- no assembly STL supplied: risk factor;
- no STL files supplied: score `0.0`;
- assembly connected-component count differs from number of supplied part STLs: subtract `0.7`;
- any failed STL load caps the project at `1.0`;
- any zero volume/thickness hard failure caps the project at `3.0`;
- any severe open/non-manifold boundary caps the project at `4.0`.

If the supplied part STLs are canonical reusable shapes, the assembly connected-component count may legitimately exceed the number of part files. In that case, either:

- run printability with temporary placed-instance STLs if the component-count comparison matters; or
- note the canonical-reuse convention in the final report and do not treat the mismatch as a physical correctness defect.

For printability, canonical parts are often sufficient because the question is whether each unique shape can print. For physical correctness, placed instances are usually required.

## Physical Correctness Score

Physical correctness evaluates whether the in-scope geometry works as a physical object or assembly. It is not the same as printability and not the same as feature retention.

Examples:

- parts that should be separate are separate;
- parts that should be fused are one component;
- lids, drawers, inserts, pins, and sockets have plausible clearance;
- required contacts or seating relationships exist;
- forbidden collisions do not occur;
- intended linear or rotational motion paths are plausible.

Ball-and-socket interfaces can use `spherical_fit` as a narrow size proxy when ball and socket radii or diameters are known. It measures radial clearance or intentional interference only; full snap compliance, retention, and articulation sweep still require separate checks or missing-helper notes.

Run:

```bash
python3 skills/evaluate-cad-reconstruction/scripts/score_physical_correctness.py \
  --condition-manifest <project>/.eval_tmp/physical_conditions.json \
  --json-out <project>/.eval_tmp/physical_correctness_report.json
```

### Required Manifest

Physical correctness depends on `physical_conditions.json`. The LLM or reviewer must propose conditions from design intent first; the script then executes the measurable checks.

The manifest should include:

- `assembly`: assembled STL path, relative to the manifest;
- `parts`: named placed-instance STL paths when the assembly has repeated or transformed instances;
- optional `canonical_parts`: unique reusable part STL paths for report context;
- `design_intent_inventory`: short notes about expected parts, fits, contacts, motions, and missing helpers;
- `interaction_matrix`: every important part-to-part or part-to-environment relationship;
- `conditions`: runnable deterministic checks.

The scorer executes checks against `parts`. If a model reuses a canonical part multiple times, export temporary placed-instance STLs and put those instance paths in `parts`.

When only an assembled STL exists, run `scripts/extract_placed_instances.py` before giving up on part-to-part checks. It splits disconnected STL islands into temporary component STLs and emits a manifest-ready `parts` map. This enables clearance, contact, collision, relative-pose, and simple motion checks for separated print-layout bodies. It is not semantic assembly recovery: touching/fused bodies remain one component, and generated names should be mapped to roles from renders/specs before final reporting when possible.

After extraction, checking only component counts is not enough when components visibly interact. Rebuild the interaction matrix over the extracted components and add pairwise checks for close/seated/fitting/ordered components. Use a missing-helper note only for the remaining feature-level detail that cannot be measured by the available pairwise helpers.

If the manifest has only an assembled STL but needs a named whole-model target for sampled paths, openings, or grid proxies, `parts` may contain one proxy entry that points to the same file as `assembly`. That exact single assembly-proxy entry is not penalized as a component-count mismatch; intended physical inventory should still be checked with `assembly_component_count`.

Do not generate conditions only by looking at the helper list. First identify every relevant physical relationship from the spec, code, part files, and renders.

Before proposing conditions, render and inspect the model:

```bash
mkdir -p <project>/.eval_tmp/renders
python3 skills/step-to-cadquery/scripts/render_views.py \
  <project>/<assembly-or-main>.step \
  <project>/.eval_tmp/renders/assembly
```

If the system Python lacks CadQuery, run the same command through the project-approved `uv run --python 3.12 --with cadquery` workflow.

### Baseline Physical Score

The physical scorer starts with a baseline geometry/usability score:

- starts from `10.0`;
- no assembly and no parts: score `0.0`;
- no assembly STL: subtract `0.5`;
- failed assembly or part STL load: cap at `1.0`;
- if assembly component count differs from supplied `parts` count: subtract `1.0`;
- if an assembly has multiple disconnected components but no separate part STLs were supplied: subtract `0.5` per extra component, capped at `2.0`.

Then the condition results are applied.

Because of that baseline behavior, do not pass only canonical reusable part files as manifest `parts` for a physical correctness run when the assembly contains more placed instances. Doing so creates a false risk factor. Use placed-instance STLs, or run with explicit conditions and explain why the baseline part-count comparison is out-of-scope.

### Condition Severity

Each condition has a `severity`:

| Severity | Use when | Failure effect |
|---|---|---|
| `critical` | Failure makes the artifact physically impossible or semantically wrong. | Cap score at `4.0`. |
| `major` | Failure likely breaks intended use or requires human review. | Subtract `2.0`. |
| `minor` | Nuisance, weak proxy, or incomplete check. | Subtract `0.8`. |

Inconclusive checks subtract `0.3`.

A critical failure is also listed in `hard_failures`. Major and minor failures are listed in `risk_factors`.

### Implemented Physical Checks

Supported `check` values:

| Check | Purpose |
|---|---|
| `assembly_component_count` | Assembled STL has expected connected component count. |
| `part_component_count` | A named part has expected connected component count. |
| `part_collision` | Two named part meshes do or do not collide at their current pose. |
| `part_clearance` | Minimum distance between two parts is within a threshold/range. |
| `part_contact` | Two parts touch or nearly touch within a max contact distance. |
| `linear_motion_collision` | A moving part can translate along a vector without sampled collision. |
| `linear_motion_clearance` | A moving part has enough clearance along a sampled translation path. |
| `rotation_motion_collision` | A moving part can rotate about an axis without sampled collision. |
| `axis_alignment` | Two axes are plausibly coaxial/aligned. |
| `relative_pose` | One part is in the expected relative direction/order from another. |
| `opening_presence` | A sampled line segment remains outside material, useful for holes/openings when point-inside tests are reliable. |
| `clear_path_proxy` | Explicit sample paths through holes, slots, cable passages, or windows avoid triangle hits; useful when open/non-watertight meshes make inside/outside checks unreliable. |
| `vent_opening_proxy` | Explicit sample rays through vents/grilles avoid triangle hits; useful when open or perforated meshes make inside/outside checks unreliable. |
| `vent_grid_open_area_proxy` | Parallel grid sample rays estimate whether a specified vent/grille patch contains representative open paths. |
| `feature_count` | Expected named parts/features exist in the manifest. |
| `cylindrical_fit` | Pin/hole diameters have plausible clearance. |
| `contact_graph` | Multiple expected or forbidden contact relationships hold. |
| `assembly_sequence` | Ordered subchecks for a real assembly/use action. |
| `hex_shaft_rotational_clearance` | Analytic free-rotation window for a regular-polygon (hex) peg inside a matching regular-polygon hole/pocket, from across-flats dimensions. |

Removed/unsupported:

- `part_bbox_overlap`;
- build-volume, dimension, and bbox scoring.

### Important Physical Correctness Caveats

Some relationships are important but not fully measurable with the current helpers. The evaluator should first decide whether a focused deterministic helper or honest proxy can be implemented from local data. If so, the skill should add and run that helper. Use missing-helper notes only when the check is not reasonably measurable from the available project files, meshes, params, transforms, or generated proxy geometry.

Common examples:

- snap compliance;
- living hinge fatigue;
- flexible deformation;
- thread quality;
- material strength;
- load-bearing stiffness;
- ergonomics;
- friction retention;
- fits against missing external parts.

For open shells, `opening_presence` can be unreliable because it uses point-inside tests. For drilled holes, slots, peg windows, or cable passages, `clear_path_proxy` can provide a narrower physical proxy by tracing explicit sample paths through expected clear regions and counting paths that do not hit mesh triangles. For perforated vents or grilles, `vent_opening_proxy` provides the same kind of ray evidence with vent-specific reporting, and `vent_grid_open_area_proxy` samples a rectangular grid of parallel rays across a specified vent patch when exact opening centers are not reliable. Treat these proxy results as evidence of representative clear paths, not measurement of total open area, exact shape fidelity, airflow, or assembly usability. If a mesh is intentionally open or non-watertight and no reliable ray/grid region is available, prefer render/code/spec evidence for feature retention and avoid making physical correctness depend on the opening helper unless the result is clearly valid.

### New Helper Policy

The implemented helper list is expected to evolve. A new deterministic check should be added when it is:

- important to the object's physical correctness;
- measurable from local geometry, params, transforms, or generated proxy meshes;
- narrow enough to implement and validate during the evaluation run;
- able to return concrete measurements and limitations.

Examples include instance-count checks, slot/tab insertion proxies, hinge-axis alignment, support-polygon/tipping proxies, repeated-layout checks, or simplified thread diameter/pitch proxies.

Do not add a helper during evaluation when it would require unavailable material data, validated simulation, external geometry not present in the project, subjective ergonomic judgment, network services, or a large dependency. Report those as missing-helper notes.

## Feature Retention Score

Feature retention is LLM-judged. It asks whether the reconstruction preserved the intended object semantics and user-facing/functional feature inventory.

It should not compare against unavailable original CAD, exact source B-rep, or unmeasured source dimensions. Judge against the available evidence:

- project spec;
- README;
- reconstruction report;
- source descriptions/images if present;
- code and params;
- exported STEP/STL/3MF files;
- rendered images;
- validation scripts.

Run renders or rebuild exports when useful. The LLM can rerun part of the reconstruction project to inspect generated geometry, but it should not permanently change project behavior during evaluation.

### Feature Retention Scoring

Start from `10.0` and subtract by severity:

- critical missing or incorrect core function: cap at `4.0`;
- major missing/altered functional feature: subtract `1.5..3.0`;
- minor visual/style/count deviation: subtract `0.2..1.0`;
- uncertainty alone: no deduction.

Record uncertainty in `uncertain_features` or `notes`, but only deduct when the evidence indicates a likely missing, altered, or hallucinated feature.

### Feature Retention Categories

For each important feature, classify it as:

- `preserved`: feature is present with the same role and plausible placement;
- `altered`: feature exists but role, scale, count, side, or shape is meaningfully changed;
- `missing`: expected feature is absent;
- `hallucinated`: extra feature changes the object purpose or could confuse use;
- `uncertain`: evidence is insufficient.

A simplified feature can still be preserved if it serves the same role. A visually polished model can score poorly if it represents a different object or omits the core function.

## How To Interpret Reports

Each metric may produce a temporary JSON report while the skill is running. The final deliverable should merge these into one final evaluation report.

Printability report:

- `score`, `class`;
- `hard_failures`;
- `risk_factors`;
- `assembly` per-mesh report;
- `parts` per-mesh reports;
- measured mesh metrics and scorer assumptions.

Physical correctness report:

- `score`, `class`;
- `hard_failures`;
- `risk_factors`;
- `condition_results`;
- assembly and part geometry summaries;
- whether physical `parts` were canonical parts or placed instances;
- any new helper/proxy implemented during the run and its limitations;
- scorer assumptions.

Feature retention report:

- `score`, `class`;
- evidence files used;
- per-feature expected/observed/status entries;
- missing, altered, hallucinated, and uncertain feature lists;
- rerun/render actions;
- notes.

After these details are merged into the final report, delete the temporary per-metric reports.

When deciding what needs human review, prioritize:

- any score below `8`;
- any `critical` physical failure;
- severe printability hard failures;
- feature retention below `8`;
- reports with many missing-helper notes around the model's core function;
- reports with many easy-to-implement missing checks, because the evaluator likely needs helper expansion;
- cases where the score is high but the evidence is thin.

## Example Interpretation

If a single-part lid scores:

- printability `9.8`, with minor non-watertight edges;
- physical correctness `10.0`, with only one in-scope connected part;
- feature retention `10.0`, with all lid features preserved;

then it is likely acceptable. Missing fit checks against an absent bottom box or bow should be documented as out-of-scope/missing external geometry, not deducted.

If a multi-part phone holder scores:

- printability high after mesh repair;
- physical correctness low because a repaired part loses its intended shape or cannot fit;
- feature retention low because a support, slot, or clamp is missing;

then it should be sent to human review even if slicer repair makes the mesh technically printable.

## Recommended Workflow For A New Project

1. Inspect files:
   ```bash
   rg --files <project>
   ```
2. Render the STEP if available:
   ```bash
   mkdir -p <project>/.eval_tmp/renders
   python3 skills/step-to-cadquery/scripts/render_views.py <project>/<name>.step <project>/.eval_tmp/renders/assembly
   ```
3. Run printability:
   ```bash
   python3 skills/evaluate-cad-reconstruction/scripts/score_printability.py \
     --assembly <project>/<name>.stl \
     --json-out <project>/.eval_tmp/printability_report.json
   ```
4. Create or audit `<project>/.eval_tmp/physical_conditions.json`.
   - If the project reuses canonical parts, export placed-instance STLs under `<project>/.eval_tmp/instances_stl/` and use those in the manifest `parts`.
5. Run physical correctness:
   ```bash
   python3 skills/evaluate-cad-reconstruction/scripts/score_physical_correctness.py \
     --condition-manifest <project>/.eval_tmp/physical_conditions.json \
     --json-out <project>/.eval_tmp/physical_correctness_report.json
   ```
6. Build the feature-retention section using spec/code/render evidence.
7. Write the final self-contained evaluation report, for example `<project>/evaluation_report.json`.
8. Delete `<project>/.eval_tmp/`.
