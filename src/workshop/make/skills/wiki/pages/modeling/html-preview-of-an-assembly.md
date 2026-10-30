---
title: Previewing an assembly in an HTML viewer
tags: [preview, viewer, html, three-js, glb, unit, transparency, camera, animation]
aliases: [html preview, three.js viewer, preview mesh units, GLB assembly transform, occurrence matrix, exploded preview, display floor, preview transparency, ghost housing, shader invalidation, needsUpdate, orbit damping, OrbitControls, camera preset, preview animation controls, playback slider]
sources:
  - skills/cad/scripts/packages/cadgen/src/cadgen/_internal/glb_mesh_payload.py
  - skills/cad/scripts/packages/cadgen/src/cadgen/_internal/glb.py
  - "experience: an opaque display floor hid underside parts translated downward in an exploded preview"
  - "experience: changing a preview material's transparency flag without shader invalidation left it visually opaque despite passing property checks"
  - "experience: a camera reset retained orbit inertia, and stopping preview playback overwrote a range input before its event handler read the new value"
related: [frames-and-rotations, step-file-format]
updated: 2026-10-10
---

# Previewing an assembly in an HTML viewer

A project that shows its assembly in a browser (a Three.js page over the
internal GLB render package) is building a preview, never a deliverable: STEP
is the only file handed over, and the GLB under `__cadgen__/` is internal
viewing data. Nothing a preview shows proves B-rep equivalence, clearance,
physical fit or an access path; the gates do. What follows keeps the preview
honest about what it draws.

## Preview meshes and assembly poses use different units

In cadgen's internal component render packages, GLB prototype vertices are
in metres (`CAD_TO_GLB_SCALE = 0.001`). The assembly descriptor's occurrence
translations and bounding boxes remain in CAD millimetres. Occurrence matrices
are serialized row-major, with the translation at indices 3, 7 and 11.

A viewer must choose one scene unit before applying the poses. For a scene in
millimetres, scale each prototype by 1000 **before** applying its occurrence
matrix. For a scene in metres, retain the prototype scale and multiply only
the occurrence translation by 0.001. Scaling an already assembled scene whose
vertices are in metres and translations in millimetres preserves the mismatch:
small components stay scattered at full-size placement distances.

For Three.js, whose `Matrix4.fromArray()` reads column-major storage, the
millimetre-scene placement is:

```javascript
component.scale.setScalar(1000);
component.updateMatrix();
component.applyMatrix4(new THREE.Matrix4().fromArray(occurrence.transform).transpose());
```

Compare the un-exploded scene's minima, maxima and extents with the assembly
descriptor, allowing its tessellation and bounding-box tolerances. This catches
unit and matrix-convention errors even when orbit controls make the scene look
plausible. It checks the preview's placement, nothing more.

## Exploded previews need a separate display floor

An underside part translated downward for an exploded view can disappear
behind an opaque scene floor even though it remains visible in the scene graph.
Checking occurrence counts or camera bounds alone misses this rendering defect.
Move the display floor below the exploded parts or hide it in that mode; never
move the CAD assembly datum to correct a display-only occlusion.

With Z up, use the invariant `floor_z < min(part_world_bbox.min.Z)` across the
visible exploded parts. Restore the display floor when returning to the seated
view. This floor is presentation geometry, not a print bed or a support surface
used to establish physical fit.

## Transparent previews require shader invalidation and image review

In Three.js standard materials, opaque rendering is a shader variant, not
only a blend-state setting. Changing an already rendered material's
`transparent` flag can leave the opaque shader active. When the flag changes,
set `material.needsUpdate = true`; changing only `opacity` is not sufficient
to establish a transparent housing preview. For a ghost housing, also disable
`depthWrite` so the display shell does not mask internal parts.

```javascript
if (material.transparent !== ghost) {
    material.transparent = ghost;
    material.needsUpdate = true;
}
material.opacity = ghost ? 0.12 : 1;
material.depthWrite = !ghost;
```

A check that reads `material.opacity` or `material.transparent` can pass
while the rendered shell remains opaque. Inspect the rendered image with a
known internal occurrence in view, then return to the opaque mode and confirm
the normal exterior. This verifies presentation behavior only; transparency
does not prove a real access path, clearance or NFC read performance.

## Preview controls must consume input before synchronizing state

When a range input stops playback, capture its new value before calling any
stop or UI-sync routine. Synchronizing the UI from the old animation state
can replace `event.target.value`; reading it afterward silently rejects the
user's change. The invariant is input value → stop animation → apply captured
value → synchronize controls. Verify at more than one non-default value.

An explicit camera preset must also clear residual orbit damping before it
positions the camera. Otherwise a correct camera pose drifts on later frames
because old angular deltas are still pending. With Three.js OrbitControls,
temporarily disable damping and call `update()` to consume the deltas, then
assign the new target and camera position, update again, and restore damping.
Verify a preset immediately after dragging, not only after a fresh page load.

Keep camera framing fixed during mechanism playback unless following the
moving part is intentional. Changing the silhouette's current bounding box
must not implicitly zoom the whole assembly every animation frame. Use a
separate display envelope that covers the intended motion; this is a camera
aid, not collision or physical-fit evidence.
