# Feature Retention

Use this reference for the LLM-only feature-retention metric.

## Definition

Feature retention scores whether the reconstruction preserves the intended functional and user-facing features described by the available design brief/spec/source evidence. It is separate from:

- printability: can the mesh likely be printed?
- physical correctness: do the parts fit, separate, move, contact, or avoid collision correctly?

Feature retention asks: did the reconstruction keep the right object semantics, feature inventory, visual read, roles, counts, placement, and important parametric intent?

Do not compare against unavailable original CAD, exact source B-rep, or unmeasured source dimensions. For from-scratch resemblance rebuilds, judge against the stated design intent and available source descriptions/images, not exact geometric fidelity to a source model.

## Evidence To Gather

Read:

- `spec.md`
- `README.md`
- `*_reconstruction_report.md`
- original prompt/source notes if present
- `params.py`
- `main.py`, `parts/`, `features/`, `assemblies/`, `validation.py`
- exported `.step`, `.stl`, `.3mf`, and part exports
- rendered images under `renders/`, or generate them if absent

The LLM may rerun the reconstruction project to gather evidence. Use this when exports are stale/missing, when a feature is generated only by code, when part exports are needed, or when a parameter variant would clarify whether a feature is genuinely preserved.

Examples:

- rerun the project check/export command used by that project;
- rebuild `.step`/`.stl` outputs;
- render the assembly and important separate parts;
- temporarily vary a documented parameter to verify feature generation, then restore the file;
- isolate a part or feature module if the project exposes a part builder.

Do not permanently change project behavior while evaluating unless the user asks for a fix. If files are edited only to probe a parameter variant, restore them or clearly report the temporary change.

## Rendering For Feature Retention

Use rendered views as evidence, not decoration. Prefer:

```bash
mkdir -p <project>/.eval_tmp/feature-retention-renders
python3 skills/step-to-cadquery/scripts/render_views.py <project>/<assembly-or-main>.step <project>/.eval_tmp/feature-retention-renders/assembly
```

Also render separate part STEP files or rebuilt part exports when feature evidence is local to a part. If only STL/3MF exists, use an available renderer/viewer workflow and state what was used. If no render can be produced, state that limitation and rely more heavily on code/spec evidence.

Use iso views for overall object identity and visual read. Use ortho views for feature counts, holes, slots, ribs, tabs, channels, openings, side-specific placement, and symmetry.

Generated renders, isolated part exports, parameter-variant exports, and probe outputs are intermediate evaluation artifacts. Keep their conclusions and referenced observations in the final evaluation report, then delete the generated files.

## Feature Inventory Procedure

Create a feature inventory before scoring:

1. Source/design features:
   - list required functional features from spec/source description/images;
   - include visible style-defining features when they affect object identity.
2. Reconstructed features:
   - list what the code and renders show;
   - include counts, side, orientation, placement, and whether each feature is parametric.
3. Compare:
   - `preserved`: feature is present with the same role and plausible placement;
   - `altered`: feature exists but role, scale, count, side, or shape is meaningfully changed;
   - `missing`: expected feature is absent;
   - `hallucinated`: extra feature changes the object's purpose or could confuse use;
   - `uncertain`: evidence is insufficient.

Feature classes to consider:

- containers, compartments, trays, shelves, channels, hooks, handles, knobs;
- holes, screw mounts, slots, vents, cable paths, drainage, honeycomb/perforation grids;
- hinges, latches, snaps, dovetails, clips, tabs, rails, dividers, drawers;
- decorative-but-identifying elements such as ribs, texture panels, bevel families, accent grooves;
- repeated feature counts and layout patterns;
- parametric controls that preserve important source variants.

## Scoring

Start from 10 and subtract by severity:

- critical missing/incorrect core function: cap at 4;
- major missing/altered functional feature: subtract 1.5 to 3;
- minor visual/style/count deviation: subtract 0.2 to 1;
- uncertainty alone: no deduction. Record it in `uncertain_features` or `notes`, but only subtract when the uncertainty is evidence of a likely missing/altered/hallucinated feature.

Suggested classes:

- `excellent`: score >= 9
- `good`: score >= 8
- `review`: score >= 5
- `poor`: score < 5

Use judgment. A simplified feature can still be preserved if it serves the same role and matches the intended design well enough. A beautiful but semantically different feature should score poorly.

## Report Schema

When running the full skill, feature retention should be folded into the final evaluation report instead of leaving a separate `feature_retention_report.json`. Use this schema inside the final report, or write a temporary JSON file under `<project>/.eval_tmp/` and delete it after merging:

```json
{
  "score": 8.0,
  "class": "good",
  "evidence": [
    "spec.md",
    "params.py",
    "temporary front ortho render observation"
  ],
  "feature_results": [
    {
      "feature": "front drawer pull scoops",
      "expected": "each drawer has a handle-free finger scoop",
      "observed": "drawer.py cuts a cylindrical scoop; front render shows one per drawer",
      "status": "preserved",
      "severity": "major",
      "evidence": ["spec.md", "parts/drawer.py", "front ortho render"]
    }
  ],
  "missing_features": [],
  "altered_features": [],
  "hallucinated_features": [],
  "uncertain_features": [],
  "rerun_actions": [
    "rebuilt assembly STEP",
    "rendered assembly and body/lid parts"
  ],
  "notes": []
}
```

Keep evidence concrete. A report is weak if it only says "looks good" without tying each important feature to source/design evidence and observed reconstruction evidence.
