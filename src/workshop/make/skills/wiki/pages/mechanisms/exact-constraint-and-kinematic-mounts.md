---
title: Exact constraint and kinematic mounts
tags: [constraint, kinematic-coupling, degree-of-freedom, over-constraint, locating, datum, preload, repeatability]
aliases: [exact constraint design, kinematic design, kinematic mount, kinematic coupling, maxwell coupling, kelvin coupling, kelvin clamp, three-groove coupling, ball and groove, cone groove flat, 3-2-1 fixturing, overconstraint, over constrained, over-constrained, redundant constraint, elastic averaging, diamond pin, relieved pin, locating pin, round and diamond pin, pin and slot, three-point support, three legs, wobbly table, rocking, repeatable location, quasi-kinematic, gruebler, grubler, kutzbach, mobility]
sources:
  - Slocum, A., "Kinematic couplings: A review of design principles and applications", Int. J. Machine Tools and Manufacture 50(4), 2010 (https://web.mit.edu/2.70/Reading%20Materials/Kinematic%20coupling%20review%20article.pdf) — ECD rule, 3-2-1 fixturing, Kelvin and Maxwell couplings, Maxwell's stability condition, groove normals bisecting the coupling triangle, 45° contact, instant centres outside the triangle, preload by bolts, springs or magnets, round-plus-diamond pallet pins, quasi-kinematic couplings (dowels 5 µm → QKC 1.5 µm), plastic hemispheres in wooden grooves an order of magnitude better than an H-bar locator, sheet-metal vees tens of µm
  - https://en.wikipedia.org/wiki/Kinematic_coupling (Kelvin: tetrahedron 3 + vee 2 + flat 1; Maxwell: three vees, symmetric, thermal centre)
  - https://en.wikipedia.org/wiki/Chebychev%E2%80%93Gr%C3%BCbler%E2%80%93Kutzbach_criterion (M = 6(N − 1 − j) + Σf, planar 3(N − 1 − j) + Σf; special geometry can defeat the count)
  - "https://www.eng-tips.com/threads/what-is-diamond-pin.75148/ (diamond pin contacts at the ends of a diameter perpendicular to the line between the pins; via search excerpt)"
related: [shafts-and-bearings, linear-guides-and-slides, gdt-basics, tolerance-stack-up, dowel-pins-and-press-fits, magnets-and-strap-slots, stability-and-tipping, fdm-joining-split-prints, hinges-and-pin-joints, flexures-and-living-hinges, fit-derivation, design-for-assembly, linkages, creep-and-stress-relaxation]
updated: 2026-09-23
---

# Exact constraint and kinematic mounts

A rigid body has six degrees of freedom: three translations and three
rotations. **Exact constraint design**: use exactly as many independent point
constraints as the degrees of freedom you mean to remove — six to fix a part,
five for a revolute joint, fewer for a slide. Every constraint beyond that is
a redundant one, and printed parts meet it as binding, rocking, a lid that
fits only one way round, or a bearing pair that drags. Read this page when
locating a lid, module, cartridge or removable part; when a joint or guide
binds although every clearance "should" work; and before adding a second pin,
a fourth foot or a second axial stop.

## Count constraints, not features

Each contact between two parts is one or more point constraints, each acting
along its contact normal:

| contact | constraints | freedoms left |
|---|---|---|
| ball on flat | 1 | 5 |
| ball in V-groove (two flanks) | 2 | 4 |
| ball in cone or trihedral socket | 3 | 3 (a ball joint) |
| round pin in round hole (short) | 2 | 4 |
| round pin in slot | 1 | 5 |
| long pin in hole, or two coaxial bearings | 4 | 2 (turn and slide) |
| flat on flat | 3 | 3 |

- A fixed part needs six **independent** constraints. Independent means the
  six normals are not degenerate: no two coincide, no three lie in one plane
  and meet in a point or are parallel, no four are coplanar or concurrent or
  parallel (Maxwell's condition). Three contacts on one straight line do not
  fix rotation about it.
- For a linkage, count mobility with Grübler–Kutzbach:
  `M = 6(N − 1 − j) + Σf` (spatial) or `M = 3(N − 1 − j) + Σf` (planar),
  N bodies including ground, j joints, f freedoms per joint. A result lower
  than the motion you need means redundant constraints that only exact
  dimensions can satisfy. Special geometry can defeat the count (a planar
  four-bar is over-constrained as a spatial linkage and works only because its
  axes are parallel), so compute the constraint rank as well ([[exact-constraint-and-kinematic-mounts#write-the-count-as-an-assert]]).

## Over-constraint in printed assemblies

A redundant constraint is satisfied only if two independently toleranced
dimensions agree. FDM holds a few tenths of a millimetre, so they will not
([[tolerance-stack-up]]). The part then either cannot assemble, is forced in
and binds, or rests on a subset of its contacts and rocks between them.

| symptom | redundant constraint | exact-constraint fix |
|---|---|---|
| four feet rock | 4 supports for 3 freedoms (z, tip, tilt) | three feet, or one foot compliant |
| two dowels will not both enter | 2 round pins = 4 constraints for 3 in-plane freedoms | one round pin + one slot or diamond pin |
| shaft drags, bearings warm | axial stop at both supports | fix one bearing, float the other ([[shafts-and-bearings#axial-location-fixed-and-floating]]) |
| slide binds mid-stroke | two rails both guiding the same direction | one guiding rail, one supporting rail ([[linear-guides-and-slides#measure-to-the-right-rail]]) |
| hinge stiff after assembly | three or more knuckle bores on one axis in two parts | clearance on all but one knuckle pair, or a single long bore ([[hinges-and-pin-joints]]) |
| lid fits one way only | perimeter lip + pins + snaps all locating | locate by pins; give the lip clearance |
| split print halves misalign | dowels + a tongue-and-groove seam | pins locate, seam gets clearance ([[fdm-joining-split-prints#connectors]]) |

The alternative to exact constraint is **elastic averaging**: many compliant
contacts, each deforming a little, whose average locates the part. It carries
more load and spreads contact stress, but its accuracy is only as good as the
compliance allows, and it must not load a sensitive part (a bearing, a PCB).
A snap-fit lid with a flexible lip is elastic averaging; choose it
deliberately, not by accident.

## 3-2-1 location

To locate a part against a fixture or a housing:

1. primary face on **three** points (sets z, tip, tilt),
2. secondary face against **two** points (sets one translation and yaw),
3. tertiary face against **one** point (the last translation).

This is the datum reference frame of [[gdt-basics#datums]]. Put the three
primary points as far apart as the part allows; the part is stable only while
its load stays inside their triangle ([[stability-and-tipping#a-base-that-rocks-is-not-a-polygon]]).
Point contacts deform and add friction as the part is pushed into the
secondary and tertiary stops, so 3-2-1 is less repeatable than a kinematic
coupling that seats in one motion.

## Kelvin and Maxwell couplings

A kinematic coupling locates one part on another with exactly six contacts,
and seats under one preload.

- **Kelvin** (cone–groove–flat): ball 1 in a cone or trihedral socket (3),
  ball 2 in a V-groove pointing at the socket (2), ball 3 on a flat (1). The
  socket is the fixed point, so thermal growth and print shrinkage move the
  part about a known centre. The socket carries three contacts and the highest
  stress.
- **Maxwell** (three grooves): three V-grooves on one part, three balls on the
  other, two contacts each. Symmetric, easier to make, and its thermal centre
  is the coupling centroid.

Maxwell geometry rules (Slocum):

- Orient each groove so its **axis bisects the angle of the triangle** formed
  by the three ball centres at that ball; the bisectors meet at the in-centre
  (for an equilateral triangle, all grooves point at the centre).
- Contact normals at **45°** to the coupling plane give balanced stiffness.
- Stability check: the plane of the two contact normals at each ball contains
  that ball's instant centre; it must lie **outside** the coupling triangle.
- Make the triangle as large as the part allows; tipping resistance scales
  with its in-radius.

Achieved repeatability depends on contact stiffness, friction and wear. Hard
steel or ceramic reaches micrometres or better; formed sheet-metal vees reach
tens of micrometres; even plastic hemispheres in wooden grooves beat a
conventional pin-and-slot locator by about an order of magnitude. A coupling
is typically two to three times more accurate than the parts it is made from.

## Printed kinematic mounts

- Use **purchased steel balls** (bearing balls) pressed or glued into one
  part; print the grooves. Or form each groove from two parallel steel dowels
  laid in a printed cradle ([[dowel-pins-and-press-fits]]), which gives hard,
  straight flanks.
- A ball on printed plastic is a high-stress point contact: the plastic
  dents and creeps ([[creep-and-stress-relaxation]]). Keep preload modest, or
  give the contact a metal face; expect repeatability to degrade over the
  first seatings and then settle.
- Print grooves with their axis in the XY plane and flanks at 45° so they
  need no support ([[overhangs-and-print-orientation]]); add a relief at the
  groove root so the ball never touches it.
- **Seating needs the flanks to beat friction.** A ball on a flank inclined
  at α to the coupling plane slides down under preload only if `tan α > μ`.
  At 45° that is μ < 1, which printed plastic on steel meets; at shallow
  flanks it may hang off-centre.
- Grooves in a printed part must be long enough for the ball to find them
  from the part's worst placement error, plus a lead-in.

## Preload: gravity, magnets, springs

A kinematic coupling locates only while every contact stays loaded.

- **Gravity** suffices for a module that sits on a horizontal base.
- **Magnets** suit lightly loaded interfaces and removable lids: pocket them
  per [[magnets-and-strap-slots#magnet-pockets]], place the attraction at or
  near the coupling centroid, and leave a gap between the magnets at the
  seated position so the magnets never become a seventh contact.
- **Springs or bolts through spring stacks** give higher preload
  ([[springs]]). A bolt clamped hard face-to-face over-constrains the coupling.
- Apply preload inside the coupling triangle, ideally through its centroid.
  An external moment M lifts a ball when it exceeds about
  `F_preload · r_in`, where r_in is the in-radius of the ball triangle.

## Locating pins: one round, one diamond or slot

The usual way to locate a plate, lid or module in its plane:

- The face (three pads or a flat) sets z, tip and tilt.
- A **round pin** in a round hole sets x and y.
- A second pin sets only rotation: a **diamond (relieved) pin** whose two
  contact lands lie on the diameter **perpendicular** to the line between the
  pins, or a round pin in a **slot** whose long axis lies **along** that
  line. The slot is easier to print than a diamond pin.
- Rotation error ≈ `(clearance of pin 2) / (pin spacing)` radians, so put
  the pins as far apart as possible.
- Hole and pin sizes come from `cadfits` ([[fit-derivation]]), and the slot
  width is a fit on the pin, its length a clearance larger than the pin-spacing
  tolerance ([[tolerance-stack-up]]).
- Two round pins in two round holes need the two spacings to agree within the
  clearance; in print they seldom do.

## Joints and bearings are constraints too

A revolute joint should remove exactly five freedoms. Two radial bearings
remove four (two translations, two tilts); one axial stop removes the fifth.
A second axial stop is redundant: fixed-and-floating
([[shafts-and-bearings#axial-location-fixed-and-floating]]). A prismatic
joint should remove five: one rail that guides plus a second surface that
only supports ([[linear-guides-and-slides]]). A flexure removes constraints
by stiffness, so the same counting applies with compliant directions left
free ([[flexures-and-living-hinges]]).

## Write the count as an assert

Represent each point contact as a unit normal `n` through a point `p`. Its
constraint line in Plücker form is `(n, p × n)`; the rank of the stacked
lines is the number of independent constraints.

```python
import numpy as np

def constraint_rank(contacts):
    """contacts: list of (point_xyz, normal_xyz). Returns (rank, redundant, dof_left)."""
    rows = []
    for p, n in contacts:
        n = np.asarray(n, float); n /= np.linalg.norm(n)
        rows.append(np.concatenate([n, np.cross(np.asarray(p, float), n)]))
    rank = np.linalg.matrix_rank(np.array(rows), tol=1e-9)
    return rank, len(rows) - rank, 6 - rank
```

- A kinematic mount: six contacts, rank 6, redundant 0.
- A revolute joint: rank 5, and the free motion (null space) is the joint axis.
- A redundant count above zero is a design decision, recorded with the
  compliance that absorbs it (elastic averaging) or the clearance that
  releases it.

## Checks

```python
rank, redundant, dof_left = constraint_rank(CONTACTS)
assert dof_left == DOF_INTENDED, f"{dof_left} free DOF, wanted {DOF_INTENDED}"
assert redundant == 0 or ELASTIC_AVERAGING_ACCEPTED, f"{redundant} redundant constraints"
assert math.tan(flank_angle) > mu_contact, "ball will hang on the groove flank"
assert F_preload * r_in > M_external, "external moment lifts the coupling"
assert n_axial_stops_per_shaft == 1, "shaft located at both supports"
```
