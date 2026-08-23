# CAD parameters

Read this file when the user asks to parameterize a STEP model, or when designing or reviewing source parameters.

## No viewer, no controls

The toolchain has no viewer control surface or animation playback. `gen_step()`
may still declare `params` — they travel into the GLB package metadata for
whoever opens the artifact downstream — but nothing here reads them back,
renders a pose, or plays a sweep. Everything below is about parameters as a
**source** contract.

## Principle

Parameters are part of the model contract. A good parameter makes design intent explicit, maps to named geometry or motion, stays inside a valid range, and gives both users and LLMs enough context to predict what changing it will do.

Prefer parameter logic that preserves the mechanism or part constraints over logic that merely produces a valid-looking shape at one value.

## Parameter Brief

Before coding, write a compact internal parameter brief:

- What geometry or motion each parameter controls.
- Units, defaults, min/max, step size, and whether the value is dimensionless.
- Which named features, datums, pivots, axes, faces, or local selector refs each parameter affects.
- Which values are independent inputs and which are derived from constraints.
- What validation proves the parameter is correct.

For assemblies and mechanisms, identify fixed pivots, moving pivots, link lengths, gear ratios, axes, joint limits, and branch choices before creating controls.

## Naming

Use snake_case semantic names that describe intent, matching the build123d Python source convention:

- Prefer `wall_thickness`, `bearing_clearance`, `hinge_angle_deg`, `lid_open`, `gear_ratio`, `link_travel`.
- Avoid names like `offset2`, `magic_scale`, `fix_angle`, `slider_a`, unless the source model itself uses a meaningful matching term.
- Encode units in names only when the value could otherwise be ambiguous, such as `_deg`, `_sec`, or `_mm` suffixes.
- Keep sidecar parameter ids aligned with the Python source parameters they mirror, and keep source constants, manifest feature ids, UI labels, and comments aligned enough that an LLM can trace a control to geometry.
- Module schema field names such as `schemaVersion`, `manifest.step.path`, and `durationSeconds` are fixed by the step-module schema; the snake_case convention applies to the parameter and feature ids you define.

## Defaults And Bounds

Defaults should produce a useful, valid model or pose. Bounds should protect the model from impossible, self-intersecting, or misleading states.

- Use physically valid ranges where possible: joint limits, positive dimensions, manufacturable wall thickness, realistic clearances.
- Clamp in code even when the UI already declares `min` and `max`.
- Make `step` match the useful precision of the underlying model, not just the UI.
- Use booleans for true binary state, selects for discrete modes, colors for style-only values, and numbers only for ordered quantities.
- Keep debug parameters available when useful, but label them as inspection controls if they do not represent real design degrees of freedom.

## Derive, Do Not Drift

Compute dependent values from the real constraints:

- Use pivots, axes, centers, bounds, and measured link lengths instead of eyeballed translations.
- Compose assembly transforms around the correct local datum or joint, not around visual centers unless that is the actual design datum.
- For linkages, solve the kinematics from fixed pivots and link lengths. Do not interpolate through impossible intermediate points.
- For gears, preserve pitch-circle relationships, tooth counts, and angular ratios instead of tuning rotations by sight.
- For repeated features, derive positions from count, pitch, radius, and pattern axes.

If a parameter changes a source-level CAD generator, regenerate STEP and validate the exported geometry — that is the only way a parameter change is confirmed here.

## Features And Refs

Named features are the bridge between parameters and geometry.

- Label source parts and assembly children explicitly.
- Expose sidecar `manifest.features` with stable local refs such as `#o1.2`; keep file identity in `manifest.step.path`.
- Prefer feature ids like `lid`, `hinge_pin`, `input_gear`, `lower_rocker`, not occurrence ids as public names.
- In code, group constants and transforms by feature role so the logic reads like the mechanism.
- Resolve and inspect refs when a parameter targets a specific face, edge, part, pivot, or assembly child.

## Validation

Validate parameter behavior at representative values:

- Defaults.
- Min and max.
- Mid travel.
- Boundary or branch-change poses.
- Values involved in user-reported failures.

Use deterministic checks first:

- `scripts/inspect refs --facts --planes --positioning` for scale, labels, frames, and major datums.
- `scripts/inspect frame`, `measure`, or `align` for pivots, axes, mating faces, and distances.
- Source-level assertions for derived dimensions or joint limits when practical.

**There is no renderer in this toolchain**, so a parameter sweep cannot be
reviewed by looking at it. The sidecar is still worth declaring — it travels
with the STEP for whoever opens it downstream — but every claim about a pose
has to come from geometry:

- Assert derived dimensions and joint limits in the source, at the poses that
  matter (both end stops, not just the rest pose).
- Use `scripts/inspect frame` / `measure` / `align` on a generated pose to check
  pivots, axes and mating distances.
- Use `scripts/check_motion` with a manifest for anything that inserts, slides,
  hinges or latches; it sweeps the declared path with exact booleans and is the
  only thing here that answers whether a motion is possible or blocked.

## Common Failure Patterns

- Eyeballed keyframes that violate real link lengths or mating constraints.
- Interpolating between two valid poses through invalid intermediate geometry.
- Transforming a part around its bounding-box center instead of its hinge, mate, or local frame.
- Letting a debug scale or offset create collisions outside the real design envelope.
