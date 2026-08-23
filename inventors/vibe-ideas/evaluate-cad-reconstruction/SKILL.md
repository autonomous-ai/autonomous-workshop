---
name: evaluate-cad-reconstruction
description: Use when evaluating reconstructed CadQuery/STL/STEP projects for printability, physical correctness, functional usability, assembly separation, fit/clearance, collisions, motion paths, missing features, or when generating/running physical_conditions.json manifests.
---

# Evaluate CAD Reconstruction

## Purpose

Evaluate reconstructed CAD projects as project-scale artifacts, not isolated meshes. Use the repo's deterministic scorers for printability and physical correctness, and use an explicit condition manifest so LLM judgment proposes checks while scripts execute measurable geometry tests.

For a user-facing explanation of how scores are calculated and interpreted, read `references/scoring-guide.md`.

## Standard Workflow

1. Inspect the project layout before scoring:
   - `spec.md`, `README.md`, reconstruction reports, `params.py`, `main.py`, part folders, exported `.stl`, `.step`, `.3mf`.
   - Identify the assembled STL, canonical/reusable part STLs, and placed assembly instances. Prefer project-level scoring whenever multiple files exist.
   - Do not assume one part STL equals one physical assembly instance. Some projects export only canonical geometries and reuse them multiple times in the assembly.
2. Create an evaluation workspace for intermediate files:
   - Put generated renders, temporary manifests, split-part STLs, placed-instance STLs, proxy meshes, temporary exports, and per-metric raw JSON under a temporary evaluation directory, for example `<project>/.eval_tmp/`.
   - Do not write intermediate files directly into the project root unless the user explicitly asks for debug artifacts.
   - The only file that should remain after the skill finishes is the final evaluation report, for example `<project>/evaluation_report.json` or a user-requested aggregate report.
3. Run printability:
   ```bash
   python3 skills/evaluate-cad-reconstruction/scripts/score_printability.py <project-or-manifest>
   ```
   Treat printability as a success-rate/risk score, not a binary verdict. The current scorer ignores build-volume/dimension checks, tries best orientation, and only harshly penalizes clearly bad non-watertight meshes.
4. For physical correctness, first generate or review a temporary `physical_conditions.json`.
   - Before proposing checks, render the model with `skills/step-to-cadquery/scripts/render_views.py` and inspect the generated PNGs as visual context.
   - If a project has reusable/canonical parts, export or otherwise identify the placed instances before writing part-to-part checks. Physical checks such as contact, clearance, collision, relative pose, and motion paths need the instance geometry in assembly pose, not only the base canonical STL.
   - If the assembled STL has disconnected components but no placed-instance files, split those components before falling back to whole-assembly checks:
     ```bash
     python3 skills/evaluate-cad-reconstruction/scripts/extract_placed_instances.py \
       <project>/<assembly>.stl \
       <project>/.eval_tmp/instances_stl \
       --json-out <project>/.eval_tmp/instances_stl/instances.json
     ```
     Use the generated component STLs as temporary manifest `parts` when they match physical bodies. Rename component keys in the manifest to semantic names when the role is clear from renders/specs; otherwise keep the generated names and state the mapping evidence in the final report.
     Extraction is not complete after adding `part_component_count` checks. After extraction, rebuild the interaction matrix over the extracted components and add every obvious pairwise check enabled by the split, such as `part_contact`, `part_clearance`, `part_collision`, `relative_pose`, or simple motion checks. Only leave a missing-helper note for the remaining feature-level relationship after adding the coarser pairwise check that is already measurable.
   - If no manifest exists, author one from design intent and geometry evidence.
   - For the required checklist and schema, read `references/physical-condition-manifests.md`.
   - If an important measurable check is not supported yet, add a focused helper to `cad_reconstruction_eval/physical_correctness_score.py` and expose it through the manifest check dispatcher before falling back to a missing-helper note.
5. Run physical correctness:
   ```bash
   python3 skills/evaluate-cad-reconstruction/scripts/score_physical_correctness.py --condition-manifest <project>/.eval_tmp/physical_conditions.json
   ```
6. Evaluate feature retention with an LLM-only report.
   - Read `references/feature-retention.md`.
   - Rerun project code, rebuild exports, and render assemblies/parts/variants when that helps assess preserved features.
7. Write one final report:
   - Scores/classes for printability, physical correctness, and feature retention.
   - Failed, inconclusive, and unused/missing checks.
   - Any conditions the LLM believes are important but still cannot be measured after considering a focused helper implementation.
   - Include enough raw metric details and condition results in the final report that the deleted intermediate JSON files are not needed for interpretation.
8. Clean up:
   - Delete only files created for the evaluation run.
   - Preserve user/project source files and pre-existing exports.
   - Remove the temporary evaluation directory after the final report has been validated.

## What To Inspect

Use all available project evidence, not just STL names. Visual inspection is mandatory for physical correctness check proposal:

```bash
mkdir -p <project>/.eval_tmp/renders
python3 skills/step-to-cadquery/scripts/render_views.py <project>/<assembly-or-main>.step <project>/.eval_tmp/renders/assembly
```

If separate part STEP files exist, render them too, using prefixes that match the part names. If no STEP exists, state that visual rendering via `skills/step-to-cadquery/scripts/render_views.py` could not be run and use available STL/3MF viewers or generated STEP exports if the project can rebuild them. Do not silently skip visual context.

- `spec.md` for intended parts, motion, fit, material, and manufacturing assumptions.
- `README.md` for user-facing purpose and exported file conventions.
- `*_reconstruction_report.md` for source listing details and reconstruction intent.
- `params.py` for clearances, diameters, counts, hinge sizes, latch dimensions.
- `main.py` and `parts/` or `features/` for assembly children, instances, unions, cuts, and named features.
- Exported `*_parts/*.stl` for canonical or actual separate parts. Check whether they are reusable canonicals or placed instances.
- The assembled `.stl` for connected component count and accidental fusion.
- Temporary placed-instance STLs for physical checks when the assembly reuses canonical parts through transforms, mirrors, arrays, or repeated `cq.Assembly.add(...)` calls.
- Temporary rendered iso views for gestalt, intended exposed surfaces, and obvious missing features.
- Temporary rendered ortho views for holes, slots, openings, alignment, contact faces, and possible hidden interferences.

## Canonical Parts vs Placed Instances

Distinguish these two concepts before scoring:

- `canonical_parts`: unique reusable shapes, such as one screw STL used four times.
- `placed_instances`: each physical occurrence in the assembled pose, such as `screw_0`, `screw_1`, `screw_2`, and `screw_3`.

Use canonical parts for:

- per-unique-shape printability;
- checking that a reusable part mesh is valid;
- checking expected unique part types.

Use placed instances for physical correctness:

- assembly component count;
- part contact, clearance, and collision;
- relative pose and axis alignment;
- motion path checks;
- checking that repeated/mirrored bodies do not overlap.

If only canonical part files exist, inspect `main.py`, assembly metadata, transforms, and renders. When feasible, export temporary placed-instance STLs under `<project>/.eval_tmp/` and use those as the manifest `parts`. Do not report an assembly-vs-part-count mismatch as a defect when the mismatch is explained by canonical reuse.

If only an assembled STL exists and its intended bodies are disconnected, use `scripts/extract_placed_instances.py` to split connected mesh islands into temporary component STLs. This is a fallback component extractor, not semantic STEP assembly recovery: it cannot separate touching/fused bodies, and generated names are size-ordered labels until the evaluator maps them to roles.

After extraction, do a second physical-reasoning pass. Map extracted components to roles when possible, compute which components are close, touching, nested, ordered, or intended to fit, and add pairwise conditions for those relationships. A report that only checks extracted component counts is incomplete when the extracted components visibly interact.

## Physical Correctness Categories

Group physical correctness checks under these categories:

- `separation_correctness`: parts that should be separate stay separate; parts that should be fused are fused.
- `fit_clearance`: inserts, lids, pins, slots, screws, snap features, and sliding interfaces have plausible clearance.
- `interference_collision`: forbidden overlap or collision does not happen.
- `contact_engagement`: required touching, seating, capture, or engagement exists.
- `motion_path`: intended insertion/removal/sliding/rotation/folding paths are feasible.
- `part_inventory`: expected bodies or repeated features exist.

Functional feature preservation is a separate metric. Do not bury missing functional features inside printability.

## Feature Retention

Feature retention is LLM-judged. It asks whether the reconstructed project preserves the intended user-facing and functional features of the source/design, independent of whether the mesh is printable or physically assembled correctly.

For feature retention:

- read `references/feature-retention.md`;
- use specs, reports, source descriptions, source images/renders if present, code, params, part files, and generated renders;
- rerun the reconstruction project when useful to rebuild missing exports, isolate parts, inspect generated assemblies, or test parameter-driven feature variants;
- render the assembled model, separate parts, and important variants before scoring when STEP/STL/3MF outputs can be produced;
- report evidence and uncertainty rather than pretending the score is deterministic.

## Check Selection Rule

When proposing physical checks, enumerate intended physical relationships first, then map each relationship to a helper. Do not start from the helper list and stop early.

Before writing the manifest, make an interaction matrix:

- rows: every physical part/body, including repeated instances and optional/demo bodies;
- columns: every other part/body plus the environment object if relevant, such as wall, shelf, screw, hinge pin, egg, tool, cable, card, drawer bay, or user-removable insert;
- each cell: `separate`, `fused`, `clearance-fit`, `contact`, `forbidden-contact`, `linear-motion`, `rotation-motion`, `contains/supports`, `fastener/axis`, or `no interaction`.

Every non-`no interaction` cell must become either a runnable condition or an explicit missing-helper note. Use the rendered views to confirm that visually apparent interactions from tabs, slots, holes, lids, drawers, hinges, latches, ribs, openings, and supports are represented.

If component extraction was run, rebuild this matrix using the extracted components before finalizing the manifest. Do not stop at `assembly_component_count` plus one `part_component_count` per component. For every extracted component pair with a small measured gap, visual seating, overlap risk, or fit intent, add at least one runnable pairwise condition unless the relationship truly requires unavailable external geometry or a new helper.

For every separate part ask:

- Should it be separate or fused?
- Does it insert into, slide on, rotate around, fold with, latch to, screw into, hang from, contain, or support another part?
- What path would a user take to assemble/remove it?
- Which faces/features must touch, clear, or avoid each other?
- Which repeated features must exist in a countable way?

For every reusable/canonical part ask:

- How many placed instances should exist?
- Are the instance transforms, mirrors, rotations, and translations represented in the assembly?
- Are physical checks using instance names, not only canonical names?

If a relationship cannot be measured by current helpers, first decide whether it is implementable with a small deterministic helper. If it is implementable from available local geometry, code, parameters, or generated proxy meshes, write the helper and run it. Only leave a missing-helper note when the relationship requires unavailable external geometry, material properties, real physics, subjective ergonomics, or a large solver outside the scope of the evaluation run.

A physical manifest is not complete until the interaction matrix has been checked against both the design docs and the renders.

## Extending Physical Helpers During Evaluation

The helper list is not fixed. When the LLM identifies an important physical condition that is not covered, classify it:

- `implement_now`: deterministic, local, and narrow. Examples: count expected instances, verify a named axis offset, sample a slot/opening path, check a known diameter clearance, compare a measured distance profile, detect component fragmentation, validate simple ordered placement.
- `proxy_now`: not exact, but a useful local approximation can be implemented and reported as a proxy. Examples: simple tipping-support polygon proxy, coarse insertion-envelope collision, sampled screw-axis alignment without thread validation.
- `missing_helper`: not reliably measurable from available local data. Examples: true thread engagement, snap compliance, flexible deformation, fatigue, material strength, friction retention, load-bearing under a real device unless a suitable simulation/proxy has been explicitly implemented.

For `implement_now` and useful `proxy_now` cases:

1. Add the helper function to `cad_reconstruction_eval/physical_correctness_score.py`.
2. Add the `check` name to `_run_condition`.
3. Document expected `inputs`, `thresholds`, limitations, and severity guidance in `references/physical-condition-manifests.md`.
4. Add a focused test or run a representative manifest that proves pass and fail behavior when practical.
5. Include the new helper name, measurements, and limitations in the final evaluation report.

Keep new helpers small and deterministic. Do not add a broad dependency, long-running solver, network service, or subjective LLM-only judgment inside the deterministic scorer without explicit user approval.

## Auto-Improvement Loop

Use this loop when asked to improve the evaluator itself over a batch of projects:

1. Run the skill on a batch and leave only final `evaluation_report.json` files in each project.
2. Aggregate the reports:
   ```bash
   python3 skills/evaluate-cad-reconstruction/scripts/aggregate_evaluation_reports.py \
     <projects-root> \
     --out-dir skills/evaluate-cad-reconstruction/loop_runs/<iteration-name>
   ```
   Or create a dry-run iteration with an executable Codex prompt:
   ```bash
   python3 skills/evaluate-cad-reconstruction/scripts/run_codex_improvement_loop.py \
     <projects-root> \
     --iterations 1
   ```
   To run Codex automatically, add `--run-codex`. The driver uses `codex exec` with `workspace-write` sandboxing; it does not bypass sandboxing.
3. Read `loop_report.md` and identify:
   - repeated missing-helper themes;
   - false-positive signals;
   - low-score causes;
   - unused checks;
   - failed checks.
4. Choose one narrow improvement target per iteration.
5. Implement one deterministic helper, proxy, scoring-policy fix, or manifest-generation rule.
6. Rerun only the affected projects plus a small regression set.
7. Update docs/tests and record before/after score changes.

Do not combine multiple unrelated helper changes in one loop. If the aggregate report points to several issues, rank them and handle the highest-impact deterministic one first.

## Current Helper Checks

Supported manifest `check` values as of this skill version:

`assembly_component_count`, `part_component_count`, `part_collision`, `part_clearance`, `part_contact`, `linear_motion_collision`, `linear_motion_clearance`, `rotation_motion_collision`, `axis_alignment`, `relative_pose`, `opening_presence`, `clear_path_proxy`, `vent_opening_proxy`, `vent_grid_open_area_proxy`, `feature_count`, `cylindrical_fit`, `spherical_fit`, `contact_graph`, `assembly_sequence`, `hex_shaft_rotational_clearance`.

When a project needs a new deterministic check, implement it rather than treating this list as complete.

## Bundled Implementation

The scorer implementation lives inside this skill:

- `cad_reconstruction_eval/printability_score.py`
- `cad_reconstruction_eval/usability_score.py`
- `cad_reconstruction_eval/physical_correctness_score.py`
- `scripts/score_printability.py`
- `scripts/score_usability.py`
- `scripts/score_physical_correctness.py`
- `scripts/extract_placed_instances.py`
- `references/feature-retention.md`

The repository may also provide compatibility wrappers at `scripts/score_*.py` and `autoimprove/common/*_score.py`, but prefer the skill-local scripts when using this skill.

Unsupported/removed:

- `part_bbox_overlap`
- any bbox/dimension/build-volume scoring

## Known Pitfalls

- Do not use bbox overlap as evidence of physical failure; bbox checks were removed because they were too noisy.
- For installed inserts, collision at step 0 may represent intended engagement. Prefer a clearance profile or an `assembly_sequence` that distinguishes seated contact from path obstruction.
- Do not treat `assembly connected components != canonical part file count` as a physical defect. It is a defect only when compared against the expected placed instance count or expected physical component count.
- For living hinges and flexible parts, geometry checks can only approximate correctness. Implement simple geometry proxies when useful, but record missing-helper notes for bend radius, fatigue, and elastic feasibility unless a real helper has been added.
- For single STL projects, connected components may reveal separate floating bodies, but the design may intentionally contain repeated loose print-in-place pieces. Read the spec before treating this as a failure.
- For non-watertight meshes, printability impact depends on repair severity. Minor repairable boundary issues are risk, not automatically impossible.

## Output Style

Be explicit about evidence. Say which source files informed the evaluation, which checks ran, and which design-intent checks remain unmeasured. When a score is low, tie it to concrete failed conditions, not vague "usability" language.

The final report must be self-contained enough to survive cleanup. Do not require a colleague to inspect deleted render PNGs, temporary manifests, raw per-metric JSON files, or generated proxy meshes to understand the result.
