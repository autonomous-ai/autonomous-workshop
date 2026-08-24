---
name: product-to-cad
description: Turn a product, toy, game component, enclosure, mechanism, or reference concept into attractive, manufacturable, 3D-printable CAD with explicit dimensions, provenance, fit and motion intent, release evidence, and honest physical limitations. Use for new STEP/STL/3MF designs, CAD redesigns, image-guided form development, multipart assemblies, print-in-place mechanisms, and preparing a design for Launchpad and fulfillment.
---

# Product to CAD

Create the product as an engineered artifact, not merely a plausible render.
Keep aesthetic judgment, geometry validation, print-process validation, and
physical proof as separate evidence streams.

## Workflow

1. Write a one-page build spec before modeling. State user, use, desired
   emotional character, printer/process, materials, bed envelope, safety
   boundary, expected parts, assemblies, fits, motions, and unresolved claims.
   Read [build-spec.md](references/build-spec.md).
2. Freeze the visual target. Record silhouette, proportions, primary/secondary
   forms, landmarks, interaction surfaces, seams, color/material breaks, and
   intended viewing angles. If a generated reference image is used, score its
   appeal before using it as the CAD target; never let CAD likeness grade the
   reference that CAD itself generated.
3. Label every dimension `observed`, `derived`, or `assumed`. Include a scale
   anchor and an uncertainty range. Put shared mating dimensions in one named
   parameter source; derive both sides from it.
4. Choose a construction family and print architecture deliberately: monolith,
   shell, split-and-join, print-in-place, fastened assembly, captive mechanism,
   or insert-assisted. Specify print orientation, supports, connector plan,
   access for assembly, and post-processing.
5. Model named parts and placed instances. Use stable datums, parameters, and
   semantic selectors. Prefer STEP/B-rep as the canonical design artifact;
   emit individual printable meshes and an assembled viewer mesh from it. Read
   the sibling [`cad`](../cad/SKILL.md) skill for engine operations and
   [`step-parts`](../step-parts/SKILL.md) for catalog parts, while treating their
   check scripts as diagnostics rather than final certification.
6. Render canonical orthographic and three-quarter views with fixed camera,
   lighting, materials, and engine version. Compare silhouette, proportion,
   landmark completeness, negative space, seam placement, and contact surfaces.
   Read [form-and-beauty.md](references/form-and-beauty.md).
7. Run cheap checks before expensive work: parse manifests, ensure expected
   parts exist, validate finite dimensions, B-rep validity, solid/shell counts,
   freshness, bounds, and obvious interference. Repair the cause and regenerate
   from a fresh isolated workspace; do not patch exported meshes by hand.
8. Run final process checks: strict mesh topology, assembly interference,
   calibrated clearances, declared motion sweeps, print-bed packing, slicer
   analysis for material/time/supports/thin walls, and project-specific audits.
   Read [calibration.md](references/calibration.md) and
   [release-evidence.md](references/release-evidence.md).
9. Emit one content-hashed project manifest and independent verification
   receipts. Bind every verdict to exact source, artifact, skill/tool, config,
   calibration, and renderer versions. A Workshop check marked `passed` must include
   the typed measurements and meet the numeric floor in
   [release-evidence.md](references/release-evidence.md); a generic
   `{"checked": true}` is never enough. Publish only when every required result
   is `passed`; `held`, missing, stale, malformed, or tool error blocks release.

## Non-negotiable evidence rules

- Never turn an exception, missing part, empty project, absent evaluator, or
  unknown measurement into zero interference or a pass.
- Never call a mesh printable from watertightness alone. Require slicer-backed
  process evidence and a calibrated printer/material profile.
- Keep beauty and likeness reviews independent from engineering gates. A
  beautiful render cannot waive topology, fit, safety, or manufacturing facts.
- Keep fatigue, snap compliance, friction, living-hinge life, food/contact
  safety, and print-in-place release `held` until simulation or physical coupon
  evidence supports the exact material/process.
- Preserve all failed receipts. Bound repair rounds by money, tokens, attempts,
  and wall time. A design may end with “no viable artifact.”

## Deliverables

Produce source, build spec, project manifest, STEP, per-part printable meshes,
assembled viewer mesh, canonical renders, verification receipts, slicer report,
assembly/print instructions, and an explicit unresolved-claims list. Keep large
generated binaries in artifact storage when the repository policy requires it.

Start from the copyable [build-spec template](assets/build-spec-template.md),
[CAD project example](assets/cad-project.example.json), and
[verification receipt example](assets/verification-receipt.example.json), then
pin independent validators with the
[validator policy example](assets/validator-policy.example.json). Their zero
hashes, incomplete policy, and `held` results are conspicuous placeholders,
never release evidence.
