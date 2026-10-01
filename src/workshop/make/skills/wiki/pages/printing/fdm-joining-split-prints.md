---
title: Splitting large prints and joining the pieces
tags: [split, join, connector, dowel, plug, dovetail, alignment-pin, glue, adhesive, seam, large-part, bed-size]
aliases: [cut tool, sectioning, alignment pins, keyed seam, tongue and groove, gluing prints, solvent welding, printing larger than the bed]
sources:
  - https://www.stratasys.com/siteassets/sdm/resources/design-guidelines/fdm/fdm_design_guidelines_2017-1.pdf
  - https://help.prusa3d.com/article/cut-tool_1779
  - https://jlc3dp.com/blog/split-large-prints
  - https://www.sovol3d.com/blogs/news/3d-printing-large-models-in-multiple-pieces-keys-glue-and-assembly-tips
  - https://www.baysingersadditivemanufacturing.com/splitting-and-assembling-large-files/
  - https://kingroon.com/blogs/3d-print-101/best-methods-to-bond-3d-prints-together
related: [printed-part-count, fit-derivation, fdm-print-orientation-for-strength, joints, exact-constraint-and-kinematic-mounts, interlocking-joinery-for-prints, push-pins-and-clip-fasteners]
updated: 2026-10-01
---

# Splitting large prints and joining the pieces

Whether to split at all is [[printed-part-count]]. This page is about how,
once the answer is yes.

## Reasons to section a part

Stratasys Direct lists five: the part is bigger than the build chamber; to
eliminate excessive support; to cut an overhanging feature off the top and
build it separately; to protect fragile features in post-processing; and to
build a fragile feature separately "in an orientation that produces a
stronger part" ([[fdm-print-orientation-for-strength]]). A bed-size split
is the first reason; the other four are reasons to split a part that fits.
An axle or shaft too long for the bed is a bed-size split with bending in it:
split it at the pivots it carries ([[shafts-and-bearings#an-axle-longer-than-the-bed]]).

## Where to cut

- Cut along a plane where possible, at the object's natural breaks
  (JLC3DP).
- Put the cut where the design already has a line: panel gaps, armour seams,
  belt lines, sharp changes of surface contour (Sovol). A cut through a
  smooth face shows forever.
- Each piece must then satisfy the overhang and orientation rules alone.
  Choose the cut so every piece has a flat face for the bed.

## Connectors

Woodworking interlocks (mortise and tenon, laps, box joints, scarfs, keys,
burrs) adapted to prints are in [[interlocking-joinery-for-prints]].

PrusaSlicer's cut tool generates them, and the same shapes are easy to
model:

| connector | what it is |
|---|---|
| plug | a peg on one half, its socket cut from the other |
| dowel | sockets in both halves, plus a separate printed pin |
| snap | a snap-fit peg on one half, its catch cut from the other |
| dovetail | a trapezoidal pin and tail on the cut plane, sliding together along one axis |

Each has width, depth and a **tolerance** that loosens the fit when it is too
tight. Frustum (tapered) plugs suit large objects, straight prisms small ones
(Baysinger). A dowel lets both halves print with their cut face on the bed,
because neither carries a peg. Dovetails interlock before the glue cures.

Two round pins over-constrain a joint; use one round and one diamond or slot:
[[exact-constraint-and-kinematic-mounts]].

**For a glued multi-part print, default to plugs.** A feature grown from one
part leaves nothing to cut, buy or lose, and no part can go on without its
locator. Keep the dowel for a joint whose halves must both print with the
cut face on the bed.

**A narrow seat limits a key by its width, not its depth.** A key needs a
wall on both sides, so a 2 mm rim cannot hold one however thick the part on
top of it is. Widen the capping part over its neighbour (a lid over the band
around the cup), and thicken it only where nothing moves: outside the sweep of
a rotating tab, and under the next part's clearance. Then key it from below.

**A part that stands proud of its host's edge cannot be pocketed there.** A
pocket needs a wall above it. Drop the part until its whole contact face lies
a wall inside the host, then give it a closed pocket open only along its way
in. Clipping the plug instead leaves half a joint.

**A tab butted into a notch is not a key.** A key captures its part on every
side but the one it came in from. A tab that touches one face of a notch open
on two sides, with its other gaps looser than the glue gap, is a glued butt
joint wearing a key's name. Test the claim: move the smaller part about twice
the glue gap in each of the 26 axis, edge and corner directions. A real key
leaves it free in only a handful, around its way out. A notched tab is free in
a third of them.

**Look for the key the geometry already has before adding one.** A part that
slides onto a non-round member (a cuff down a rectangular leg), sits in a
framed seat, or has another part's tenon passing through its window is
already located. Glue it and record why.

**A pin runs along the direction its part slides on.** Sockets in both halves
let the halves meet only along the pin axis, so a pin across that direction
makes the joint unassemblable. Take the axis from the part's free direction,
not from the contact face's normal. A shell half resting on a ledge can leave
along X and still jam along a face sheared a few degrees off X. A part whose
faces all run along its insertion axis, such as a badge in a framed
through-seat, has no face a pin can cross and stays glue-only. Prove each axis
by sweeping B off A along it with the pin in place.

A plate too thin for a blind socket and its floor can take a through-socket,
provided a part glued over it hides the exit.

**Put a printed peg on the part where it prints pointing up.** The same peg on
the other half of the joint can be a 5 mm cantilever sticking out sideways.
When a peg has to lie horizontal in both parts' print poses, turn its square
45° into a diamond. Then both the peg and its socket have 45° flanks and print
without support.

**A decal or thin cover can be the connector.** Run it back as a tenon of its
own outline, through a window in the layer it covers, and into the host. It
then locates that layer as well. A shield through a chest plate, or a mask
through a face aperture, locates two parts with one feature.

**Size a decal's plug to its host, not to the decal.** Keep the plug over the
region where the host is thick enough for the pocket plus its floor; skip the
thin skirt or lip. Shrink it about a millimetre inside the decal's outline:
the pocket then keeps its wall clear of the host's own edges and notches, and
the decal's rim hides it. Stop it a wall short of any other socket in the same
host.

**One peg can key a stack.** A peg that passes through a thin plate or sleeve
and ends in the part behind it locates all three. A leg peg through a 2 mm
yoke arm into a cup floor, or a buckle peg through a 1 mm belt into the cup it
sleeves, are two examples.

**A plug that carries torque must not be round.** A head or knob that is turned
by hand, such as a winding crown, needs a D or square plug to key it.

**A peg on a sloped face leaves a sliver in front of its socket.** When the
interface is not square to the peg axis (a loft surface, a slanted side), a
socket that starts at the peg's base plane leaves host material in front of
its mouth on the high side, and the peg's root runs through it. Start the
socket about a millimetre before the interface. Audit the whole peg, root
included, against the host: a clearance probe that starts past the interface
cannot see the sliver.

**Plugs entering one host from different faces can meet inside it.** Check each
pair of sockets for a wall between them, and clip one feature when there is
none.

## Clearance and glue

- Alignment pin to hole: **0.1–0.2 mm** gap (JLC3DP); **0.15–0.30 mm**, per
  side or total to be stated, with "no universal clearance" (Sovol). Derive
  it with `cadfits` like any other mate ([[fit-derivation]]) and test on a
  coupon.
- **Hydraulic lock**: a zero-clearance pin traps air and liquid glue, and
  the parts will not seat. Add relief channels or chamfered entries so
  excess adhesive escapes (Sovol).
- Tongue width at least 1.5–2 × the extrusion width; 0.5–1.0 mm
  fillets/chamfers on internal corners of the joint (Sovol).
- Mechanical keys locate; glue holds. A dowel or plug aligns two faces, a
  lap or tongue adds bonding area and resists shear.
- **Once a connector locates a joint, seat the glue faces flush.** A sliding
  clearance left there no longer positions anything. It only thickens the
  glue line, and CA does not fill a gap.

| material | adhesive | note |
|---|---|---|
| PLA, PETG | cyanoacrylate (10–60 s) or two-part epoxy (5 min–24 h) | model cement does not bond PLA or PETG (Sovol) |
| ABS, ASA | acetone solvent weld, or epoxy | (Sovol) |
| TPU and flexibles | polyurethane glue; it expands as it cures | (Kingroon) |
| most filaments | epoxy fills gaps between uneven faces | (Kingroon) |

Clean with isopropyl alcohol and lightly sand the faces first; clamp while it
cures, 30–60 s for CA (Kingroon). In Baysinger's test, glued parts broke in
the printed material rather than at the glue line. A good glued seam is not
the weak point: the layer lines next to it are.

## Checks

- Every piece fits the declared bed and has its own print orientation.
- Connector clearance comes from `cadfits`, with a glue-relief path.
- Every pin axis is its part's free assembly direction, shown by a sweep.
- Every peg prints pointing up, as a diamond, or as the face its part stands on.
- Sockets sharing a host keep a wall between them.
- No peg, root included, enters its host outside its socket.
- Sockets are reviewed in a section along the pin axis. A flat-shaded
  head-on render cannot show a blind hole: its floor shades like the face
  around it.
- The seam lies on an existing design line, or its visibility is recorded.
- The spec names the adhesive per material pair.
