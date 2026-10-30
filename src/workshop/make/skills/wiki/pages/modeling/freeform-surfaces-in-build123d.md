---
title: Freeform surfaces in build123d
tags: [surface, gordon, filling, ruled, bezier, thicken, shell, sewing, draft, freeform]
aliases: [make_gordon_surface, gordon surface, curve network, ocp_gordon, make_surface, make_surface_patch, BRepOffsetAPI_MakeFilling, filling surface, n-sided patch, coons patch, tangent cap, make_surface_from_curves, ruled surface, BRepFill, make_bezier_surface, bezier patch, make_surface_from_array_of_points, Solid.thicken, thicken sheet, shell from faces, solid from shell, sew faces, sew_faces, draft angle, ConvexPolyhedron, split_by_perimeter, surface modeling]
sources:
  - https://build123d.readthedocs.io/en/latest/tutorial_surface_modeling.html
  - https://build123d.readthedocs.io/en/latest/tutorial_surface_heart_token.html
  - https://build123d.readthedocs.io/en/latest/tutorial_spitfire_wing_gordon.html
  - https://github.com/gumyr/build123d/releases (v0.10.0, v0.11.0, v0.11.1 notes)
  - https://github.com/gongfan99/ocp_gordon/wiki/Gordon-Surface-Misalignment
  - "toolchain: build123d 0.11.1 topology/two_d.py (Face.make_* constructors, Shell sewing), topology/three_d.py (Solid.thicken, Solid.draft, Solid(Shell)), operations_part.py (thicken, draft); ocp_gordon 0.2.2; OCP 7.9.3"
  - "experience: cold scratch tests of every constructor - a pillow curve network, a twisted 4-edge hole, a G1 cylinder cap, a gapped cube, a sheet thickened past its radius, a mirrored pillow closed with ruled bands"
related: [nurbs-bspline-basics, bspline-height-fields, loft-pitfalls, loft-organic-bodies, smooth-skin-from-a-field, inflated-forms, build123d-operations-and-export, sweeps-and-helices, kernel-validity, occt-shape-healing, fillet-chamfer-pitfalls, text-patterns-and-surface-detail]
updated: 2026-10-12
---

# Freeform surfaces in build123d

A freeform body is made as faces, sewn into a closed shell, closed into a
solid (or a sheet thickened into a skin). In build123d 0.11.1 every
constructor below ran in 0.4 s or less. What fails is topology, mostly
silently: a wrong shape that reads `is_valid == True`, or an invalid solid
with a correct volume. Each section gives the contract, the observed failure
text and the asserts.

## Chooser: shape need to operation

| need | operation | result |
|---|---|---|
| surface through a grid of crossing curves (wing, hull, seat, pillow top) | `Face.make_gordon_surface(profiles, guides)` | one B-spline face |
| fill an n-sided hole from its edges, optionally through points | `Face.make_surface(wire, points)` | filling face, C0 to the boundary |
| fill a hole tangent to its neighbours (cap a tube, corner blend) | `Face.make_surface_patch([(edge, face, C1)], points)` | G1 filling face |
| straight-line band between two curves (side wall, bevel) | `Face.make_surface_from_curves(e1, e2)` | Face (edges) or Shell (wires) |
| small hand-placed control net, at most 25 x 25 | `Face.make_bezier_surface(net, weights)` | through the corner poles only |
| height field or scanned grid | `make_surface_from_array_of_points`, better a net: [[bspline-height-fields]] | approximating face |
| ordered closed sections, filled | `Solid.make_loft`: [[loft-pitfalls]], [[loft-organic-bodies]] | solid |
| ordered sections, open skin | `Shell.make_loft` | shell, no caps |
| constant-thickness wall from a sheet | `Solid.thicken(face_or_shell, t)` | skin solid |
| closed body from faces | `Solid(Shell(faces))` | solid |
| convex body from points (0.11) | `ConvexPolyhedron(points)` | faceted hull |
| trim a sheet by a curve lying on it (0.11 for Face/Shell) | `face.split_by_perimeter(wire, Keep.INSIDE)` | face |
| moulding taper on planar sides | `Solid.draft(faces, plane, angle)` / `draft()` | solid |

Bodies from a field: [[smooth-skin-from-a-field]], [[inflated-forms]]; along a path: [[sweeps-and-helices]].

## Gordon surfaces interpolate a curve network

`make_gordon_surface` (0.10, pure-Python `ocp_gordon`; 0.01 s for 3 x 3 curves,
0.4 s for 17 x 17) fits one B-spline face through two families of curves.
Contract, from the docstring and tests:

- At least two profiles and two guides; only the first or last of a family may
  be a point (a pointed end).
- Every profile meets every guide once; both ends of each profile lie on the
  outer guides and both ends of each guide on the outer profiles.
- Order and direction do not matter: shuffled families and reversed curves
  built the same surface. Swapping which family is `profiles` flipped the
  normal, so assert the normal before thickening.
- Closed profiles (periodic splines) give a tube; the face's two closed edges
  cap it: `Solid(Shell([tube] + [Face(Wire([e])) for e in closed_edges]))`.
- A 2 x 2 network of boundary curves is a Coons patch: the interior takes its
  shape only from interior curves.

Failures (subclasses of `ocp_gordon`'s `GordonInterpolationError`):
`IntersectionError: U-directional B-spline 1 and V-directional B-spline 0
don't intersect!` for a profile 0.01 mm above the guides or ending 1 mm short
(1e-4 mm passed; `tolerance=` up to 0.1 did not rescue 0.01 mm);
`CompatibilityError: At least one B-spline has no intersection at the
beginning.` for profiles overrunning the outer guides by 5 mm;
`InvalidInputError` for fewer than two profiles. So both families come from
one table of node points, never from two sets of measurements:

```python
nodes = [[(x, y, z(x, y)) for x in xs] for y in ys]   # one table
profiles = [Edge.make_spline(row) for row in nodes]
guides = [Edge.make_spline(list(col)) for col in zip(*nodes)]
top = Face.make_gordon_surface(profiles, guides)
assert top.is_valid
assert max(top.distance_to(p) for row in nodes for p in row) < 1e-6
```

## A Gordon surface leaves its curves between the nodes

The face passes through every node within 1e-7 mm, but between nodes it
departs from the input curves: 1e-14 mm on a symmetric 3 x 3 network, 2e-4 on
5 x 5, 5e-3 on 9 x 9, 1.4e-2 on closed rings. `tolerance=` did not change it.
The cause is the reparameterization to an iso-parametric network (ocp_gordon
wiki). Uniform `parameters=` on `Edge.make_spline` made one shared edge exact
(1e-8 mm) but left 5e-3 mm on the boundary of a 9 x 9 network: not a fix.

The consequence: two patches built separately against one shared curve do not
sew at the default 1e-6, and `Shell([left, right])` raises `TypeError: Unable to
create Shell, invalid input type`. Using the first face's edge as the second
patch's guide failed the same way. What works:

1. One Gordon surface over both regions, then `split(Plane..., Keep.BOTH)`:
   the halves share their edge exactly.
2. `mirror()` for a symmetric partner: exact.
3. `BRepBuilderAPI_Sewing(tol)` with `tol` above the measured gap (1e-4 sewed
   the 2e-4 case); the edge tolerance grows to the gap
   ([[occt-topology-and-tolerance#tolerance]]).

## Filling a hole: make_surface

`Face.make_surface(exterior, surface_points, interior_wires)` wraps
`BRepOffsetAPI_MakeFilling` (degree 3, at most 8th degree, 9 segments).

- **Pass a Wire.** With `surface_points`, a list of edges, even in order,
  fails `RuntimeError: non planar face is invalid`. build123d builds the
  filler twice (edges, then points); with loose edges, whose corner vertices
  coincide but are not shared, the second build returns a face bounded by one
  edge. In a `Wire` the same edges worked shuffled or with one reversed.
- An open boundary or a 0.5 mm gap: the same `RuntimeError`. Closed 3-, 4-,
  5-sided and single-circle wires all worked.
- Points are met approximately: one apex within 4e-4 mm, nine points of a
  bump within 4.5e-3, 221 points on a smooth dome within 4e-6. A point outside
  the boundary is ignored silently (37 mm away, face valid). Assert the
  distance to every point.
- The face's boundary edges are new edges (not `IsSame` the inputs), within
  1e-15 mm of them, so neighbours still sew.
- An `interior_wires` wire floating 6 mm off the surface was accepted as a
  hole. Project first: `w = wire.project_to_shape(face, (0, 0, -1))[0]`, then
  `face.make_holes([w])`.

## Tangent caps: make_surface_patch

`make_surface_patch(edge_face_constraints=[(edge, face, level)],
point_constraints=[...])` sets a continuity per edge. On a cylinder's top rim
with an apex point, `C0` made a kinked cap, `C1` a cap leaving the rim tangent
(rim normal radial within 0.004), and `C2` failed `RuntimeError: Error building
non-planar face with provided constraints`. `Solid(Shell([side, cap,
bottom]))` was valid. Use `C1`; assert the rim normal.

## Ruled surfaces: make_surface_from_curves

- Edge plus edge returns a Face; wire plus wire returns a **Shell** (the
  annotation says Face); a mix raises `TypeError: Both curves must be of the
  same type (both Edge or both Wire).`
- Points join by parameter ([[loft-pitfalls#sections-match-by-index]]): one
  curve reversed gave a bow-tie, `is_valid == True`, area 574 against 839.
- Wires of 2 and 1 edges: the first edge was ruled to the whole other edge and
  the second dropped, with no error. Equal edge counts are not checked.
- A face's boundary wire and its mirror run opposite ways: two of four band
  faces were invalid (`BRepCheck_UnorientableShape`), the sewn shell was
  manifold, the solid invalid with exactly the right volume, and a 1 mm fillet
  on it then **segfaulted** the interpreter in `ChFi3d_FilBuilder`. Build bands
  edge by edge, `[Face.make_surface_from_curves(e, e.mirror(Plane.XY)) for e in
  top.edges()]`, or `Face.extrude(e, (0, 0, -h))`; both closed a valid pillow.

## Bezier patches and point grids

`make_bezier_surface` takes 2 to 25 poles per direction (`ValueError: The
maximum number of control points is 25`; `At least two control points must be
provided`), optional weights, and passes through the corner poles only (an
interior pole lay 2.5 mm off). Two patches with an identical shared pole row
sew into one shell. Larger nets and C2 joins: [[smooth-skin-from-a-field]].

`make_surface_from_array_of_points` approximates (tol 1e-2 met 1.1e-2, 1e-3
met 1.3e-3) and rings on height grids
([[bspline-height-fields#fitting-through-the-grid-rings]]). Two silent traps:
`smoothing=` fails `ValueError: B-spline approximation failed` unless
`max_deg >= 5`; and ragged rows give a valid face of garbage (the array is
sized from row 0; 0-40 mm data spanned -284 to 375 mm). Assert a rectangular
grid and the bounding box.

## Thicken makes a skin, not a body

- `Solid.thicken(face_or_shell, depth)` offsets along the face normal;
  `normal_override` flips a single face's direction. `Face` and `Shell` have no
  `thicken` method. The functional `thicken(faces, amount, both=...)` thickens
  each face separately and fuses (0.06 s against 0.002 s for one
  `Solid.thicken(Shell(faces))`, same solid here).
- `depth=0` raises `ValueError: Null TopoDS_Shape object`.
- A closed shell thickens into a hollow skin: a sphere shell of r 10 by 1 mm
  gave 4/3 pi (11^3 - 10^3), not a filled ball.
- Past the concave radius it does not raise. A B-spline sheet of radius about
  5 thickened 4.9 mm inward returned `is_valid == False` with a plausible
  volume; an analytic cylinder face of r 5 thickened 8 mm inward returned a
  *valid* skin of the reflected r 3 cylinder.
- A pointed Gordon face (point profile) thickened invalid on one side and
  valid on the other.
- Offset surfaces slow every later boolean on large skins; offset the control
  net instead ([[smooth-skin-from-a-field#crisp-parts-and-sheets-beside-the-skin]]).

```python
skin = Solid.thicken(sheet, t)
assert skin.is_valid and len(skin.solids()) == 1
assert abs(skin.volume - sheet.area * t) < 0.2 * sheet.area * t   # t << radius
```

## Closing faces into a solid: Shell, then Solid

- `Shell(faces)` sews at the `BRepBuilderAPI_Sewing` default of 1e-6 and
  takes no tolerance. It fixes orientation (all faces flipped, or one, still
  gave a valid cube).
- A gap of 1e-5 mm or more, or a duplicate face, raises `TypeError: Unable to
  create Shell, invalid input type`. `Face.sew_faces(faces)` returns the
  groups ([5, 1] on a gapped cube), which names the face that is off.
- A missing face still makes a Shell (`is_manifold == False`); `Solid(shell)`
  is then invalid with volume 6400 of 8000, since
  `ShapeFix_Solid.SolidFromShell` never checks closure.
- `Solid(list_of_faces)` raises `AttributeError: 'list' object has no
  attribute 'IsNull'`.
- Sewing at 0.02 closed a 0.01 mm gap but left an edge tolerance of 0.0105.
  Share edges instead: reuse Edge objects, mirror, or split one surface.

```python
shell = Shell(faces)
assert shell.is_manifold
body = Solid(shell)
assert body.is_valid and body.volume > 0 and len(body.solids()) == 1
```

## Draft takes planes, cylinders and cones only

`Solid.draft(faces, neutral_plane, angle)` and the `draft()` operation (0.10)
refuse other faces: `ValueError: Face ... has unsupported geometry type
BSPLINE. Only PLANAR, CYLINDRICAL, and CONICAL faces are supported.` Tangent
chains come along: drafting only the planar sides of a box with filleted
vertical edges gave the same solid as listing the fillets too. With the top
edges filleted first it failed, `DraftAngleError: Draft could not be added to
a face.` Draft first, fillet after; a freeform body gets its taper from the
surface itself (leaning guides, shrinking sections).

## Other additions in 0.10 and 0.11

`ConvexPolyhedron(points)` hulled 200 points in 0.06 s into 396 planar faces:
faceted, not smooth. `Face.split_by_perimeter` trimmed a Gordon face by a
projected oval, inside plus outside equal to the whole. `Face.wrap` and
`wrap_faces`: [[text-patterns-and-surface-detail]]. `Face.uv_face` is the
parameter domain as a planar face; `Face(Plane)` replaces `make_plane()`.

## Checks

`is_valid` on every constructed face, not only the final solid; the distance
to every node, constraint point and boundary curve against a stated tolerance;
`shell.is_manifold` before `Solid(shell)`, then `is_valid`, `volume > 0`, one
solid and the volume against an independent estimate ([[kernel-validity]]).
Never fillet or boolean a solid that failed `is_valid`: the fillet can crash
the interpreter instead of raising.
