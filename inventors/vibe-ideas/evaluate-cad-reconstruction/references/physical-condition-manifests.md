# Physical Condition Manifests

Use this reference when creating or auditing `physical_conditions.json`.

## Required Visual Pass

Before proposing physical conditions, render and inspect the model:

```bash
mkdir -p <project>/.eval_tmp/renders
python3 skills/step-to-cadquery/scripts/render_views.py <project>/<assembly-or-main>.step <project>/.eval_tmp/renders/assembly
```

Render separate part STEP files too when available. Use the 6 iso renders to understand the object and the 6 ortho renders to identify holes, slots, openings, contact faces, alignment axes, and hidden-looking interferences. If the project has no STEP file and cannot rebuild one, document that the render pass was unavailable; do not omit the visual-evidence step from the report.

Use the renders as input to condition proposal, not just as a final sanity check.

Generated render files are intermediate evaluation artifacts. They should be written under the evaluation temp directory and deleted after the final evaluation report is written.

## Canonical Parts vs Placed Instances

Physical correctness checks should normally run against placed instances, not only reusable base parts.

Definitions:

- `canonical_parts`: unique reusable shapes, for example one screw STL reused four times.
- `placed_instances`: every physical occurrence in assembly pose, for example `screw_0`, `screw_1`, `screw_2`, and `screw_3`.

Use canonical parts for unique-shape inventory and per-shape printability. Use placed instances for physical conditions because contact, clearance, collision, relative pose, axis alignment, and motion paths depend on the instance transform.

If a project exports only canonical part STEP/STL files, inspect the assembly code or STEP assembly structure to recover the instance transforms. When feasible, export temporary placed-instance STLs under:

```text
<project>/.eval_tmp/instances_stl/
```

Then use those placed-instance files in the manifest `parts` map. Do not compare assembly component count against the canonical part count. Compare it against the expected placed physical component count.

The final report should state when temporary placed instances were generated and should preserve the mapping summary after deleting `.eval_tmp`.

If no placed-instance files are available but the assembled STL contains disconnected mesh bodies, split them into temporary component STLs:

```bash
python3 skills/evaluate-cad-reconstruction/scripts/extract_placed_instances.py \
  <project>/<assembly>.stl \
  <project>/.eval_tmp/instances_stl \
  --json-out <project>/.eval_tmp/instances_stl/instances.json
```

Use the generated `parts` map from `instances.json` as manifest input, renaming `component_000`-style labels to semantic roles when the renders/spec make the mapping clear. This component extractor groups triangles by shared edges, matching the scorer's connected-component topology. It is useful for separated print-layout bodies and scattered kits, but it cannot recover semantic instances that touch, are fused, or only exist in STEP/CadQuery assembly metadata.

After component extraction, rerun the interaction-matrix step over the extracted components. Extraction should unlock pairwise checks, not only component-count checks. For every extracted component pair that is visibly seated, close, ordered, nested, or intended to fit, add a runnable `part_contact`, `part_clearance`, `part_collision`, `relative_pose`, or simple motion condition when the geometry supports it. If a fine-grained feature check is still impossible, keep that as the missing-helper note after the coarser pairwise relationship has been checked.

## Manifest Shape

```json
{
  "assembly": "model.stl",
  "canonical_parts": {
    "screw": "parts/screw.stl"
  },
  "parts": {
    "body": "instances_stl/body.stl",
    "lid": "instances_stl/lid.stl",
    "screw_0": "instances_stl/screw_0.stl",
    "screw_1": "instances_stl/screw_1.stl"
  },
  "conditions": [
    {
      "id": "lid_can_slide_on_body_without_collision",
      "category": "motion_path",
      "severity": "major",
      "check": "linear_motion_collision",
      "description": "Lid should slide onto the body along +Y.",
      "inputs": {
        "moving_part": "lid",
        "obstacle_part": "body",
        "translation": [0.0, 60.0, 0.0],
        "steps": 8
      }
    }
  ]
}
```

Paths are relative to the manifest file. Use stable part or instance names that describe physical role, not anonymous indexes when the role is known.

The scorer currently executes checks against the `parts` map. Therefore, for physical correctness, `parts` should contain the in-assembly placed instances whenever they differ from canonical reusable shapes. The optional `canonical_parts` map is report context for humans and for unique-shape inventory; do not rely on it for placed-pose checks unless the canonical is also the only placed instance.

When the only available STL is the assembled mesh and a condition needs a named `part` for whole-model sampled paths or openings, it is acceptable to map one proxy part name to the same assembly STL. The Layer 1 component-count mismatch penalty treats this exact single assembly-proxy part as report scaffolding, not as a claim that the project has only one physical placed instance. Use explicit `assembly_component_count` conditions for the intended connected-component inventory.

If the assembled STL has separated mesh islands, generate temporary component STLs with `scripts/extract_placed_instances.py` and use them for contact, clearance, collision, relative-pose, and motion checks whenever the component-to-role mapping is defensible. Do not leave a "placed-instance extraction missing" note before trying this STL component splitter.

A manifest that uses extracted components is incomplete if it only contains `assembly_component_count` and one `part_component_count` per extracted component while the components have an obvious physical relationship. Rebuild the interaction matrix with the extracted component names and add pairwise conditions before finalizing.

When running the full skill, this manifest is normally temporary. Write it under `<project>/.eval_tmp/physical_conditions.json` unless the user explicitly asks to keep manifests for debugging. The final evaluation report should copy the important manifest contents: design-intent inventory, interaction matrix summary, runnable conditions, condition results, and missing-helper notes.

## Thorough Proposal Checklist

Before writing runnable checks, produce a short design-intent inventory:

1. Parts and bodies:
   - Which exported STLs represent separate physical parts?
   - Which exported STLs are canonical reusable part shapes?
   - Which placed instances exist in the assembly, including repeated or mirrored bodies?
   - Which repeated instances are expected?
   - Which bodies must be fused into one print?
2. Separation correctness:
   - Expected connected components in the assembled STL.
   - Expected connected components inside each placed instance STL.
   - Whether the number of assembly components matches expected placed instances, not merely expected canonical part types.
   - Any print-in-place bodies that should remain separate but near/contacting.
3. Fit and clearance:
   - Lids, drawers, trays, dividers, pins, sockets, screws, holes, tabs, slots, dovetails, snaps.
   - Min/max clearance from `params.py` or spec.
   - Cylindrical fits where diameters are explicit.
4. Interference/collision:
   - Forbidden part overlap in assembled, storage, or print layout.
   - Collision along insertion/removal/sliding/rotation paths.
5. Contact and engagement:
   - Required seating/contact pairs.
   - Latches, tabs, supports, stops, hinge barrels, hooks, screw heads.
   - Expected and forbidden contact graph edges.
6. Motion paths:
   - Linear insertion/removal for drawers, dividers, lids, slides, cards.
   - Rotation for hinges, handles, doors, knobs, foldable bodies.
   - Assembly sequences where multiple checks must hold in order.
7. Functional geometry:
   - Openings, through-holes, containers, vents, cable paths, drainage, gripping surfaces.
   - Counted features such as honeycomb holes, screw holes, compartments, feet, dividers.
8. Unsupported or new-helper checks:
   - For every important relationship not covered by an existing helper, decide whether to implement a focused deterministic helper now, implement a useful proxy now, or leave a missing-helper note.
   - Flexible deformation, hinge fatigue, snap compliance, strength, fastener thread quality, ergonomics, and load-bearing checks are usually not fully measured by current helpers unless a specific proxy/helper is added.

Then produce an interaction matrix. Include every physical placed instance/body and every relevant external mating object named or implied by the spec, such as shelf board, wall, screw, hinge pin, egg, screwdriver, card, cable, or user hand path. For each pair, classify the relationship as one of:

- `separate`
- `fused`
- `clearance-fit`
- `contact`
- `forbidden-contact`
- `linear-motion`
- `rotation-motion`
- `contains/supports`
- `fastener/axis`
- `no interaction`

Every matrix entry except `no interaction` must map to at least one runnable condition, a newly implemented helper/proxy, or an explicit missing-helper note. Re-check the matrix against rendered iso and ortho views before finalizing.

When the matrix rows come from extracted STL components, first map each component to the best available semantic role using bbox, surface area, renders, and specs. If the role is uncertain, use generated names but still add measurable pairwise checks for close/contacting/ordered components. Record the mapping evidence in the final report.

For repeated parts, write the matrix at instance granularity. For example, a tablet stand with one canonical screw shape and four screws should list `screw_0`, `screw_1`, `screw_2`, and `screw_3` as separate rows/columns for contact and clearance checks.

## Mapping Intent To Helpers

Use `feature_count` for expected parts, placed instances, canonical part types, or named repeated features. Be explicit about which inventory is being counted.

Use `assembly_component_count` when the assembled STL should have a known number of connected bodies. For project print layouts with separate parts, this often equals the number of separate placed physical instances. It should not be compared against the number of canonical reusable part files unless there is no reuse.

Use `part_component_count` when a named placed instance or canonical part must be one connected mesh or intentionally multiple connected components.

Use `part_collision` for forbidden overlap at a static pose. This requires placed instances in their assembly poses. Avoid using it for a seated insert if contact/engagement at the installed pose is expected.

Use `part_clearance` for static minimum distance between two placed parts.

Use `part_contact` when two placed parts must touch or nearly touch.

Use `linear_motion_collision` for a straight insertion/removal/slide path where collision should never happen.

Use `linear_motion_clearance` for a straight path where a minimum distance profile is useful. If a removable part starts seated in a slot, a threshold of `0.0` may be appropriate unless the helper can ignore the initial seated step.

Use `rotation_motion_collision` for hinge, lid, handle, or knob sweeps around a known axis.

Use `axis_alignment` for coaxial pins/holes, hinge barrels, screw axes, or rails.

Use `relative_pose` for centroid/order checks along an axis when exact contact is not needed.

Use `opening_presence` for through-holes, containers, cable paths, vents, and open-top trays when the mesh is watertight enough for point-inside sampling to be meaningful. Define a line segment that should remain outside material.

Use `clear_path_proxy` for explicit straight paths through holes, slots, cable passages, peg windows, and other expected openings when `opening_presence` is unreliable on non-watertight, thin-shell, or highly perforated meshes. Provide one or more sample paths through known clear regions:

```json
{
  "id": "mounting_holes_have_clear_axes",
  "category": "fit_clearance",
  "severity": "major",
  "check": "clear_path_proxy",
  "description": "Representative mounting-hole centerlines should not hit mesh triangles.",
  "inputs": {
    "part": "body",
    "paths": [
      {"start": [-20.0, 0.0, -1.0], "end": [-20.0, 0.0, 6.0]},
      {"start": [20.0, 0.0, -1.0], "end": [20.0, 0.0, 6.0]}
    ]
  },
  "thresholds": {
    "min_clear_fraction": 1.0,
    "max_intersections_per_clear_path": 0
  }
}
```

The helper counts a path as clear when the segment intersects no more than `max_intersections_per_clear_path` triangles. Use `min_clear_paths` or `min_clear_fraction` to define the pass criterion; if neither is provided, `min_clear_fraction` defaults to `1.0`. This is a proxy: it verifies sampled straight paths only, not opening diameter, open area, shape fidelity, or downstream assembly usability. Keep severity aligned to the feature: mounting holes and cable paths may be `major`; decorative or broad window samples are usually `minor`.

For large meshes, the helper first filters triangles to the exact axis-aligned bounding box of each sampled segment before running segment-triangle intersection. Reports include candidate-triangle counts so slow or overly broad paths can be diagnosed without keeping temporary artifacts.

Use `vent_opening_proxy` for vent holes, perforated grilles, and slot fields when `opening_presence` is unreliable because the mesh is highly perforated or non-watertight. Provide explicit straight sample rays through representative expected openings:

```json
{
  "id": "cap_grille_has_open_flow_paths",
  "category": "functional_feature_preservation",
  "severity": "minor",
  "check": "vent_opening_proxy",
  "description": "Representative rays through the cap grille should pass through open slots.",
  "inputs": {
    "part": "cap",
    "rays": [
      {"start": [10.0, 0.0, 42.0], "end": [10.0, 0.0, 48.0]},
      {"start": [0.0, 10.0, 42.0], "end": [0.0, 10.0, 48.0]}
    ]
  },
  "thresholds": {
    "min_clear_fraction": 0.5,
    "max_intersections_per_clear_ray": 0
  }
}
```

The helper counts a ray as clear when it intersects no more than `max_intersections_per_clear_ray` sampled triangles. Use `min_clear_rays` or `min_clear_fraction` to define the pass criterion; if neither is provided, `min_clear_fraction` defaults to `0.5`. This is a proxy: it verifies sampled straight flow paths only, not total open area, hole count, hole diameter, grille shape, or airflow. Prefer `minor` severity unless the sampled openings are the only core physical function and the ray locations come from strong geometry/code evidence.

Use `vent_grid_open_area_proxy` when the part has a vent/grille field but individual opening rays are too tedious or brittle to author. This helper samples a rectangular grid of parallel rays across a specified patch:

```json
{
  "id": "body_grille_has_open_area",
  "category": "functional_feature_preservation",
  "severity": "minor",
  "check": "vent_grid_open_area_proxy",
  "description": "A sampled patch across the grille should contain representative through-flow paths.",
  "inputs": {
    "part": "body",
    "grid_origin": [-20.0, -1.0, 35.0],
    "u_vector": [40.0, 0.0, 0.0],
    "v_vector": [0.0, 0.0, 20.0],
    "ray_direction": [0.0, 1.0, 0.0],
    "ray_length_mm": 4.0,
    "rows": 5,
    "cols": 9
  },
  "thresholds": {
    "min_clear_fraction": 0.25,
    "max_intersections_per_clear_ray": 0
  }
}
```

`grid_origin` is one corner of the sample patch. `u_vector` and `v_vector` span the patch, and `ray_direction` plus `ray_length_mm` define the through-material probe. Use `min_clear_rays` or `min_clear_fraction`; if neither is provided, `min_clear_fraction` defaults to `0.25`. The helper reports clear ray count/fraction and min/max triangle intersections. This is a coarse proxy for open-area presence on perforated or non-watertight meshes; it does not validate exact hole count, individual hole dimensions, decorative pattern fidelity, or airflow. Keep severity `minor` unless the sampled patch and expected threshold come directly from project code or dimensions.

Use `cylindrical_fit` when the manifest can provide pin and hole diameters directly.

Use `spherical_fit` when the manifest can provide explicit ball and socket radii or diameters for a ball-joint, captured-ball, or snap-socket interface:

```json
{
  "id": "arm_ball_fits_socket",
  "category": "fit_clearance",
  "severity": "major",
  "check": "spherical_fit",
  "description": "Representative arm ball should be size-compatible with its socket cavity.",
  "inputs": {
    "ball_radius_mm": 3.0,
    "socket_radius_mm": 2.9
  },
  "thresholds": {
    "min_radial_clearance_mm": -0.2,
    "max_radial_clearance_mm": 0.15
  }
}
```

The helper reports radial and diameter clearance as `socket - ball`. Negative clearance can be intentional for snap-fit or captured-ball designs when the manifest sets an explicit allowed interference range. This is a proxy: it checks only size compatibility from provided dimensions. It does not validate socket-mouth geometry, clip compliance, retention force, friction, material fatigue, or swept articulation clearance.

Use `contact_graph` when multiple pairs have expected or forbidden contact relationships.

Use `assembly_sequence` when a real user action depends on ordered subchecks.

Use `hex_shaft_rotational_clearance` for a regular-polygon (hex by default) shaft/peg rotating inside a matching regular-polygon hole or pocket that shares the same angular reference, e.g. a hex axle inside a hex through-hole in a plate/frame, or inside a hex hub pocket. This is an analytic 2D cross-section proxy (no mesh sampling): it builds the peg and hole as regular N-gons from their across-flats dimensions and binary-searches the largest rotation, in each direction from the aligned pose, before a peg vertex leaves the (convex) hole polygon. If the peg clears the worst-case angle within one symmetry period (`180/sides` degrees, exactly halfway between two aligned positions), the fit is reported as unbounded/continuous rotation (`free_rotation_total_deg: 360.0`, `continuous_rotation_capable: true`).

```json
{
  "id": "axle_cannot_rotate_in_base_plate_hex_hole",
  "category": "motion_path",
  "severity": "critical",
  "check": "hex_shaft_rotational_clearance",
  "description": "The hex axle must be able to spin freely inside the base plate's hex through-hole for the gear train to rotate at all.",
  "inputs": {
    "peg_across_flats_mm": 4.0,
    "hole_across_flats_mm": 4.4,
    "sides": 6
  },
  "thresholds": {
    "min_total_rotation_deg": 360.0
  }
}
```

Use `min_total_rotation_deg` when the design intent is a free-spinning bearing fit (e.g. a shaft passing through a frame/plate hole). Use `max_total_rotation_deg` instead when the design intent is a tight/keyed, non-rotating fit (e.g. a hex shaft driving a hex hub pocket) and the check should confirm the fit stays appropriately snug. Reported measurements include `free_rotation_plus_deg`, `free_rotation_minus_deg`, `free_rotation_total_deg`, and `continuous_rotation_capable`.

This helper was added during evaluation of a 4-gear spur-train reconstruction where a mesh-based `rotation_motion_collision` sweep (0-60 deg) against the (large, ~6700-triangle) base plate mesh reported no collision at any sampled angle — contradicted by the analytic result (only ~24.6 deg of free play for AF 4.0 mm in AF 4.4 mm) and by hand geometry. The mesh check's `max_sample_triangles=1000` subsampling likely missed the small hex-hole-rim feature (<0.5% of the plate's triangles) entirely at some sampled angles. Prefer this analytic helper over `rotation_motion_collision` whenever the moving/obstacle pair is a polygonal peg-in-polygonal-hole fit with known across-flats dimensions and a large obstacle mesh, since it is exact and immune to that sampling failure mode.

Limitations: assumes the peg and hole share a common rotation axis and the same angular reference used at rotation 0 (true whenever both features are built from the same hex/N-gon vertex formula, as in this project). It does not model chamfers/lead-ins, print-tolerance variation, non-regular polygons, or out-of-plane tilt.

## Adding New Helpers

Do not treat the current helper set as closed. If a condition is important and can be measured deterministically from local data, add a helper instead of leaving a missing-helper note.

Use this triage:

| Decision | Use when | Expected action |
|---|---|---|
| `implement_now` | The check can be measured directly from available meshes, STEP-derived values, project params, transforms, or generated proxy meshes. | Add a helper to `physical_correctness_score.py`, expose it in `_run_condition`, document inputs/thresholds here, run it. |
| `proxy_now` | Exact measurement is hard, but a narrow local approximation gives useful evidence and can be described honestly. | Add a helper or manifest subcheck with conservative severity and clear limitations. |
| `missing_helper` | The check needs unavailable external geometry, material properties, true physics, subjective ergonomics, or a large solver. | Record an explicit missing-helper note in the final report. |

Helper design rules:

- Keep the helper deterministic and local.
- Prefer inputs that are explicit in the manifest: part names, axes, points, vectors, expected counts, diameter/radius values, distance thresholds, sampled path steps.
- Return concrete measurements, not only pass/fail.
- Mark weak proxies as `minor` unless they are strongly tied to the core function.
- Add a small representative test or rerun a manifest showing the new helper works.
- Do not add network calls, opaque LLM calls, heavy simulation, or broad new dependencies without explicit user approval.

Good candidates for new helpers:

- placed-instance export/count verification;
- named axis offset or hinge-pair alignment from assembly transforms;
- slot/tab insertion-envelope clearance;
- sampled support polygon or tipping proxy;
- repeated feature layout/count checks from known centers;
- simple thread proxy using pitch/diameter/axis when exact helical thread validation is unavailable;
- container capacity/opening proxy from sampled sections.

Poor candidates for quick helpers:

- true screw thread engagement under torque;
- snap fit retention with elastic deformation;
- fatigue life;
- material strength under real use;
- friction-only retention;
- ergonomics or user comfort;
- load-bearing simulation without validated material and boundary conditions.

## Severity Guidance

- `critical`: failure makes the artifact physically impossible or semantically wrong.
- `major`: failure likely breaks intended use or requires human review.
- `minor`: nuisance/risk, weak proxy, or incomplete helper coverage.

Prefer `major` for most fit, separation, and motion checks. Use `minor` for approximate diagnostic checks.

## Minimum Manifest Quality Bar

A manifest is incomplete if any of these are true:

- It lists parts but no relationships between them.
- It has only component-count checks for a multi-part functional object.
- It uses only canonical part STLs for contact, clearance, collision, relative-pose, or motion checks when the assembly contains repeated or transformed instances.
- It treats a mismatch between assembly component count and canonical part count as a defect without checking expected placed instance count.
- It was generated without first running or explicitly attempting the required render pass.
- It does not include an interaction matrix or equivalent pairwise relationship enumeration.
- It omits insertion/removal checks for removable inserts, drawers, lids, or slides.
- It omits rotation checks for hinges, handles, doors, or foldable mechanisms.
- It omits contact/engagement checks for latches, supports, hooks, or stops.
- It silently ignores important design-intent checks because no helper exists.
- It records a missing-helper note for a deterministic local check that could reasonably have been implemented as a focused helper during the evaluation.
