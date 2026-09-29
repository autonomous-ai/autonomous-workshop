---
title: Assembling a kit of supplied parts
tags: [assembly, pose, datum, placement, determinant, bom, clash, reverse-engineering, kit]
aliases: [assemble stl kit, print plates to assembly, placement verdict, datum pair audit, inside out solid, designer photos]
sources:
  - skills/step-to-source/references/assembling.md
  - skills/step-to-source/scripts/source_plan
  - "experience: kit assemblies whose pose was mis-read from bounding boxes, mirrored by a det -1 matrix, or rotated twice"
related: [kit-assembly-clash-diagnosis, authoring-from-a-reference, mesh-measurement, cad-container-formats, linkages]
updated: 2026-09-23
---

# Assembling a kit of supplied parts

An assembly owes two proofs: **every part is the right part**, and **every part
is in the right place**. Looking at it proves neither. Each proof comes from a
stated source and a check that fails when it is wrong. The proof list and
commands stay in `skills/step-to-source/references/assembling.md`. Reading and
fixing clashes is in [[kit-assembly-clash-diagnosis]].

## Where a pose can come from

| what the files hold | verdict | where the pose comes from |
|---|---|---|
| each part at its own offset, at different heights | `assembled` | the files. Record each offset as a named placement **before** the references are released |
| two or more parts at, or centred on, the origin | `recentred` | nowhere in the files: datums and mates, derived with `cadfits` |
| every part on Z = 0, packed on plates in its best print orientation | `print_plates` (`assumed`) | nowhere in the files: the designer's photos or manual, then datums |

- **Overlap in plan decides nothing.** A pin inside a frame's box is nested in
  an assembly too. One interference check separates a real assembly from
  plates: in an assembly something touches something, and on a plate nothing
  does.
- **The `assembled` verdict can be wrong.** A folder of plain per-part exports
  also sits "not at the origin, at differing heights", because CAD part
  origins are routinely offset from the bounding box (on a mounting face, a
  bore axis or a symmetry plane). Two cheap refutations: a mirrored pair that
  is an *exact* mirror about x = 0 and overlaps at the origin cannot be two
  parts in their assembly positions, since they would sit on opposite sides of
  the body; and two gears of a meshing bevel pair whose bounding boxes are
  each equal in two of three axes are modelled about the same axis, while a
  meshing bevel pair must have perpendicular axes.
- **A kit layout is not an assembly.** If the verdict is `print_plates` or
  `recentred`, the combined file is a layout, and "is it assembled correctly?"
  has the answer no, whatever its README says. Quote the evidence (every part
  on Z = 0, offsets spanning several plates, no part touching another).
  Running `interfere` on a layout proves only that the parts were laid out
  apart.
- **A supplied CAD assembly file may carry the poses** even when no geometry
  converts from it ([[cad-container-formats#assembly-files-carry-the-poses]]).
  Check it before concluding that the pose must come from photos.
- **A kit with a linkage is not a placement job.** It means measuring every
  mate, solving the mechanism, and one faceted CAD build, which can take hours.
  One automaton kit took about 3 h. State the cost up front in one line, and
  show a mesh render of the solved pose beside the designer's photos before any
  `gen`.

## Finding the designer's source

For `recentred` and `print_plates`, look for build photos, a manual or the
product page before asking the user how the parts go together:

- **Search the part file names plus the mechanism.** Distinctive file names
  together with the product type usually find the design on the first search.
- **Model-hosting sites often refuse scripted fetches** (Cloudflare 403 to
  both `WebFetch` and `curl`). The reader proxy `https://r.jina.ai/<page url>`
  returns the page as text: the description, every step caption and every
  image URL. Download the images from those URLs directly. Use a browser tool
  only when the proxy also fails.
- **Apply EXIF orientation before looking.** Phone build photos store their
  rotation in EXIF, so open them with `PIL.ImageOps.exif_transpose`. Crop at
  full resolution for detail (tooth counts, which face a gear's hub is on).
  Thumbnails hide it.
- **Read captions as constraints.** "Should be tight, use glue" and "really
  really tight" describe a designed press fit to report rather than fix. "Make
  sure left and right are symmetric before putting on the gears" defines a
  mirrored crank pose.
- **Photos settle front and back, and the parts confirm it**: a back wall
  carries the motor hole and cable notch; recesses sit where a frame foot and a
  housing fin drop in.

Before any number, write down the **fixed root**, what each moving part
**turns about and on what**, and the **variants**, with exactly which parts
differ between them.

## Right part

- **Identify bodies by label, never by where a bounding box sits.**
  Nearest-centre ownership went wrong even at the carried stage: a thin rib on a
  centre body sat closer to an inner wing panel's centre than to its own. Use
  an explicit table.
- **Assert the bill of materials.** Keep a role → count table per variant,
  taken from the designer's part list or the supplied file set, and assert that
  the built labels match it exactly: nothing missing, nothing extra, no
  duplicate. Two supplied files with one name are two roles
  (`front_gear_a`, `front_gear_b`).
- **Do not model parts the kit does not contain.** Place their axis and state
  the omission (for example, a motor that is not in the kit). That also keeps
  a powered claim out of the handover.

## Datums, frames and orientation

Keep three kinds of number apart:

| kind | where | example |
|---|---|---|
| **datum** of a part, in that part's own frame | the part's parameter block | `BASE_BRACKET_BORE_X = (-16.74, 27.76)` |
| **derived placement** | the assembly, as 4 × 4 matrices from datums, with no literals | `frame_shift = bracket_bore − frame_bore` |
| **assembly choice** (not a datum) | its own labelled block | `GEAR_FACE_GAP = 0.1`, a crank advance, scanned phases |

- **Write the frame beside every datum.** A value measured in a rotated frame
  and then rotated again is the most expensive mistake here. A ring centre
  rotated twice made a pose solve die with
  `brentq: f(a) and f(b) must have different signs`, far from the cause.
- Convert datums measured in mesh coordinates into the part frame once, then
  keep only the part-frame value. Measure mating datums on the mesh if it still
  exists ([[mesh-measurement#which-source-to-trust-for-which-number]]).
- **Orientation comes from a direction that is part of the design**, never
  from an angle chosen by eye: the normal of a face known to point along an
  axis, the plane normal of a link set (the crank axis), the bisector of two
  mirrored feature families (the hinge lines of a symmetric body), or a full
  frame of three directions when a part is also flipped.
- **Every placement matrix has determinant +1.** A frame built from three
  directions can come out mirrored. A det −1 matrix turns the solid inside out
  (negative volume, for example −507.9 mm³), and `interfere` then reports the
  mating part's *whole* volume as the clash.

## Seat by one datum pair, audit every other pair

Place each fixed part by one datum pair. Every other pair the design implies
becomes a check, collected in an `audit()` that runs before any geometry is
built. It is algebra and takes milliseconds:

```text
frame bore 2 over bracket bore 2        within 0.15
frame foot depth = recess depth         within 0.1
drive fin width = recess width          within 0.2
pinion to gear centre = m·(z1+z2)/2     within 0.2
```

On a correct kit the pairs agree within about 0.1 mm (a 53.7 × 10 foot in a
54 × 10 recess, a 41.7 crank-web span in a 41.75 gap, matching bore pitches).
A pair that misses by millimetres means a datum taken from the wrong face, or a
flipped part.

**Seat on the span that actually holds the part.** A mount base 16.8 long does
not fit a pocket mouth 16.3 wide, but the pocket undercuts to 17.1, so centre
the base in the undercut span.

## Moving parts are solved, never typed

- Write each kinematic loop as a **residual** (for example, the distance from
  a crankpin to the pocket it drives, minus the link length).
- Choose the one free input with a physical meaning and **solve** for it (the
  crank angle at which the centre body hangs level, by `brentq` on body
  pitch). Solve the dependent angles with `least_squares`.
- **Audit the residual against the real play.** With a half-pitch crank
  advance a loop can be over-constrained. A link slot allowing ±0.75 mm
  accepted a centre link that came out 0.28 mm long.
- **Render the pose before trusting it.** A rotation about +Y takes +X to −Z.
  A link angle written `a1 − a0` instead of `a0 − a1` left every link hanging
  down, and no residual caught it, because the loop still closed.

See [[linkages#solving-closure-numerically]] for the general method.

## Keys and teeth by scan

- **Scan angles; do not compute them.** Rotate one part's section against its
  mate's in small steps and take the zero-overlap angle
  ([[mesh-measurement#principles-that-make-mesh-readings-exact]]).
- **D bores:** map the part's flat direction (a parameter) onto the shaft's
  flat as it stands after the shaft was placed. Confirm with the scan: overlap
  must be minimal at 0°.
- **Meshing gears:** the axis distance is the pitch-radius sum, `m·(z1+z2)/2`,
  even when a measurement disagrees within the clearance (27.86 measured, 28.0
  used). Scan the tooth phase at that distance and record it with its evidence
  (`4.16 mm2 at 0, 0.0 at ±4.09°`). **A phase belongs to its centre distance**:
  moving a pinion to 28.0 moved its phase from 9.75° to 1.25°.
- **Mirrored cranks driving meshing gears** meet tooth on tooth. Half a pitch
  (`360°/z/2`) is the offset that meshes, and it is a named parameter, not a
  fudge ([[gears#mesh-phasing]]).
