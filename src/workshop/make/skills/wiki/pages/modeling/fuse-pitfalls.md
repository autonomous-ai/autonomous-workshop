---
title: Fuse pitfalls - pieces that share faces, and empty unions
tags: [fuse, union, boolean, coincident, shared-face, colour-region, occ]
aliases: [union failure, fuse lost a solid, pairwise fuse, multi-argument fuse, fuse in one call, empty fuse, fuse returned empty, union smaller than operand, shared face fuse, colour region union, fold a fuse]
sources:
  - "experience: a revolved-envelope cut that returned the uncut volume on one of two mirrored parts"
  - "experience: a blank sharing a revolved base's wall radius, and a raised region subtracted back from its host, both fused invalid"
  - "experience: a multi-colour figure's torso vanished in a pairwise fuse; a web self-intersected after a group cut; a shared cone left open edges"
  - "experience: a sculpt rebuilt from hundreds of lofted lobes fused into a right-volume solid that BRepAlgoAPI_Check called self-intersecting; fused one at a time it checked clean"
  - "experience: five leaves rooted on one point fused to an empty compound; two lofts meeting at one near-tangent point fused to a 56 mm3 solid"
  - "experience: two prisms extruded from one base face fused to an empty compound and a pocket silently vanished"
related: [boolean-pitfalls, kernel-validity, revolve-seam, loft-organic-bodies, inflated-forms, occt-boolean-options]
updated: 2026-10-12
---

# Fuse pitfalls - pieces that share faces, and empty unions

A union is the boolean people trust most and check least. Pieces built to meet
exactly (colour regions, a trimmed limb, an inlay and its host) give OCC its
weakest input, and a fuse that drops material raises nothing. Cuts, tools and
near-tangent surfaces in general are [[boolean-pitfalls]].

## Fusing pieces that share faces

Parts built as colour regions (an arm trimmed to the torso, an inlay cut out of
its host) meet on faces they share exactly, and OCC handles that badly in
these measured ways:

- **Neither one call nor a pairwise fold is safe on its own.** Folding
  `u = u.fuse(s)` over a figure's body pieces dropped the whole torso once a
  forearm trimmed by it was added: the volume halved in one step, with no
  error, where one multi-argument `fuse(a, *rest)` returned the right volume.
  But on a body of a few hundred B-spline faces, one call over every piece
  handed back a single solid of exactly the right volume that
  `BRepAlgoAPI_Check` reported **self-intersecting** (`BRepCheck_Analyzer`
  called it valid), and the same pieces fused one at a time checked clean.
  Spheres and scaled spheres fail either way through their seams
  ([[revolve-seam]]). Prefer the multi-argument fuse; whichever you use,
  assert that the running volume never drops, that the body ends as one
  solid, and that `BRepAlgoAPI_Check` passes, before believing the result.
- **Solids inside one argument are not fused with each other.** Pieces passed
  together as one `Compound` argument stay separate solids, so a bridge fused
  to that compound later cannot join them. Give each piece its own argument.
- **Cutting a fused multi-solid group self-intersects.** Two disjoint arm webs
  fused first and then cut by the arm pieces came back `selfIntersecting`; the
  same cut applied to each web on its own was valid. Cut each primitive, then
  fuse the survivors of one role in a single call.
- **A surface carried on by a second solid breaks the union.** A neck cone
  continued upward as the clipping cone of the helmet above it (one conical
  surface, two solids, or just their shared end disc) left open edges in the
  fused part. Nest instead: the second surface 0.3 mm inside the first and
  starting 0.2 mm below its end, so the solids overlap rather than touch.

A blank whose plan arc had a revolved base's own radius fused invalid (arc
0.3 mm inside: clean), and so did `host - (tip - host)`: subtract only inlays
cut *out of* the host; a raised region already excludes it. Do not fuse an
analytic primitive onto a loft that already follows it (a fitted sphere onto
the lofted knob it was fitted to): the near-coincident surfaces fail the fuse,
so keep the primitive as a datum.

Seat a trimmed piece into its host by a few tenths (trim it by the host shrunk
0.3 mm) rather than exactly to its skin: the later cut then has overlap to work
with instead of a coincident face.

A filler cut down to whatever is left between two nearly touching faces (a web
between an arm and a waist it almost meets) ends as a sliver bounded by
near-coincident surfaces and comes back `selfIntersecting`, while the same
filler across a real gap is valid. Leave the filler out where the gap it fills
is under about 1.5 mm.

## A fuse can come back empty: assert every step

Fusing several solids that all start from one point (five leaves rooted on a
knob's centre) returned an empty compound on the fifth fuse: no exception, a
valid shape, zero volume, and every later cut on the part ran on nothing. The
leaves' root caps were near-coincident. Start each one a little way out along
its own direction (still inside the knob), and after every fuse assert one solid
and a volume larger than before:

```python
grown = fan + leaf
assert len(grown.solids()) == 1 and grown.volume > fan.volume, "fuse came back empty"
```

Two prisms extruded from the same base face in different directions (one
straight, one oblique) did the same: the fuse returned an empty compound, the
pocket cut with it removed nothing, and only `interfere` caught the leftover
material. Start the second prism a little way off the shared face.

It need not come back empty. Two lofts that met at a single near-tangent
point fused into **one valid solid of 56 mm³ from operands of 50 000 and
5 400**: the one-solid half of the guard passed it, and only the volume half
catches it. A union is never smaller than its larger operand — assert that.

A model assembled from many roles wants the same guard once, where the roles
are labelled: every role holds material, or the build stops.

## A cut can silently do nothing: assert it removed material

The same failure has a subtractive twin. A plate cut by a large solid of
revolution (a shade envelope, to leave a conformal foot) came back **unchanged**
on one of two mirror-image parts: valid, one solid, the uncut volume, and the
part then overlapped the shade by 530 mm³ while its twin was correct. Assert
after every cut that matters that the volume dropped:

```python
body = plate - envelope
assert body.volume < plate.volume - 1.0, "the cut did nothing"
```

For a mirror-image pair, build one side and mirror it (`left.mirror(Plane.YZ)`
in the frame whose mid-plane is the mirror), then take it back into its own
frame. The pair is then exact by construction, and the second side never
repeats the booleans that can fail on it.
