---
title: Frames, planes and rotations
tags: [plane, frame, rotation, transform, build123d, sign-error, rodrigues, glb, unit]
aliases: [Plane.rotated, local frame, coordinate frame, rotate a plane, twist, sweep angle, inverse map, preview mesh units, GLB assembly transform, preview transparency, shader invalidation, orbit damping, preview animation controls]
sources:
  - skills/cad/references/build123d-modeling.md ("Rotating a plane"; before the move)
  - "toolchain: Plane.rotated() composes in world axes (reproducible on any non-global plane)"
  - "experience: a hand-derived rail frame with one flipped sign buried a face 6 mm inside its housing"
  - "experience: an opaque display floor hid underside parts translated downward in an exploded preview"
  - "experience: changing a preview material's transparency flag without shader invalidation left it visually opaque despite passing property checks"
  - "experience: a camera reset retained orbit inertia, and stopping preview playback overwrote a range input before its event handler read the new value"
  - skills/cad/scripts/packages/cadgen/src/cadgen/_internal/glb_mesh_payload.py
  - skills/cad/scripts/packages/cadgen/src/cadgen/_internal/glb.py
related: [build123d-selectors, loft-organic-bodies, loft-pitfalls]
updated: 2026-10-06
---

# Frames, planes and rotations

## Plane.rotated() composes in world axes

`Plane.rotated()` composes its matrix in **world axes, not the plane's own**.
On a plane whose axes are not the global ones this is the single most
expensive trap in the library, because the result is a valid solid of the
wrong shape.

For a spanwise aerofoil section — `x_dir=(-1,0,0)`, `z_dir=(0,1,0)`, i.e.
local +x rearward and the normal along +Y — `plane.rotated((0, 0, twist))`
reads like a pitch and is actually a **yaw about world Z**. Measured on a
200 mm chord: a 20° "twist" put the trailing edge at `(812.0, -68.4, 99.4)`
when it should be at `(812.1, 0.0, 168.4)`. The section slid 68 mm sideways
out of its own spanwise station and rose nothing.

Nothing downstream catches it. The loft succeeds, the solid is closed,
watertight and free of self-intersections, and `scripts/inspect refs --facts`
passes it. Only looking at a render finds it.

## Build the frame from direction vectors

```python
# incidence about the span axis, then yaw the whole frame
t, s = math.radians(twist_deg), math.radians(sweep_deg)
x_dir  = Vector(-math.cos(t) * math.cos(s), -math.cos(t) * math.sin(s), math.sin(t))
normal = Vector(-math.sin(s), math.cos(s), 0.0)
plane = Plane(origin=Vector(*origin), x_dir=x_dir, z_dir=normal)
```

The same applies to rolling a section about a swept member's own axis: use a
Rodrigues rotation about that axis rather than `Plane.rotated()`.

## Write the inverse and assert the round trip

A frame you derive by hand has two sign choices per axis and no feedback: a
wrong one still builds, still validates, and only surfaces as a clash
somewhere else. Measured on a rail placed by `Rot(0, -elev, 0)`: writing
`+z*sin` where the rotation gives `-z*sin` buried the rail's rear face 6 mm
inside the housing, and six downstream placements — a catch, a slot, two pins,
a slider — had been positioned against the bad map before `inspect interfere`
found it.

```python
def to_world(x, y): ...
def to_local(X, Y): ...
assert all(math.isclose(a, b, abs_tol=1e-9)
           for a, b in zip((3.0, 5.0), to_local(*to_world(3.0, 5.0))))
```

Two lines, and they fail at import time instead of six features later.

## A loft station frame from a lateral reference, never from Z

```python
def _station_wire(centre, tangent, half_h, half_w):
    t = Vector(*tangent).normalized()
    x = Vector(0, 1, 0).cross(t)          # lateral reference
    if x.length < 1e-6:                   # only if the spine runs along Y
        x = Vector(0, 0, 1).cross(t)
    plane = Plane(origin=Vector(*centre), x_dir=x.normalized(), z_dir=t)
    return (plane * Ellipse(half_h, half_w)).wire()
```

The obvious frame — `x_dir = Z × tangent` — degenerates the moment the spine
turns vertical, and a curled tail, a hook, a handle or an S-bend all do that.
`Z × t` goes to zero there and the loft fails or twists. A lateral reference
(`Y × t`) stays well conditioned for any spine that stays roughly in the XZ
plane, which is what a side-view-driven station table always produces.

Note what the frame does to the ellipse's arguments: with `x_dir` in the XZ
plane, `Ellipse(a, b)` takes **a = half-height, b = half-width**. Getting this
backwards produces a body that is correct in silhouette from the side and
wrong from the front, which one view will not show you.

## Rotating a body that sits off the origin

A body offset from the origin must be rotated about **its own** axis: build it
at the origin, rotate, then translate. Rotating in place about global Z flies
it across the model. Repeated features placed by a helper that only translates
its prototype must have the *prototype* rotated, not the ring.

## Internal preview meshes and assembly poses use different units

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
plausible. It is a preview-placement check, not proof of B-rep equivalence,
assembly clearance or physical fit. The render package remains internal viewing
data; STEP remains the CAD deliverable.

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
