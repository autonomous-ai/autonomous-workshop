---
title: Carved figures on split prints
tags: [organic, figure, relief, split, legs, ears, bevel, carousel]
aliases: [carousel horse, carved figure, split body halves, flat faced legs, leg knobs, joint knobs, counterbore joint, relief carving, carved ornament, harness relief, forelock, ears notch, v notch ears, split sliver]
sources:
  - "experience: a carved carousel figure printed as midplane halves with flat-faced legs"
  - "experience: the same figure's legs made to swing on shafts through the shoulders and hips"
related: [loft-organic-bodies, fillet-chamfer-pitfalls, boolean-pitfalls, overhangs-and-print-orientation, product-aesthetics]
updated: 2026-09-30
---

# Carved figures on split prints

A figure whose body prints as two halves on its midplane, with limbs printed
flat on their inner faces, has its own set of shapes that read wrong and
unions that fail. The body itself is [[loft-organic-bodies]]; this page is
what goes on it and under it.

## Limbs: an upper loft, then bones and knobs

A smooth loft through a folded knee or hock overshoots on the inside of the
bend. Loft only the gently bending upper limb (shoulder or haunch to the knee)
as one piece; below it, taper elliptic bones from joint to joint and put an
ellipsoid knob at each joint. Make every knob about 8 % larger than the bone
ends it meets: at exactly their size the bone's end ellipse lies on the knob's
equator, the union is tangent there and comes back invalid; at 5 % it held
until the pieces were bevelled, when the knob's, the bone's and the loft's
bevels met near-tangent and the fused limb failed the boolean self-
intersection check (`BRepAlgoAPI_Check`, what `inspect validate` runs) while
`is_valid` still passed. Assert that check in source. Cap the upper loft with
a knob too. A loft ends in a flat section, and wherever the flank is narrower
than the limb that flat end stands out of the body as a blade; the knob turns
it into a rounded shoulder or haunch.

## Letting a limb into the flank

Seat each limb in a counterbore the shape of the upper limb's side-view
outline grown by a margin, cut across the flank down to the limb's flat inner
face, and give the limb a root that is that same prism intersected with the
body's mass: it fills the counterbore flush with the flank, the joint line is
the outline, and a printed peg on the floor locates it. Cut the counterbores
after every feature added in that region, or a later addition refills them and
the limb collides.

## A limb that turns

A limb driven to swing keeps its carved joint line; only the fit changes.

- **Sweep the counterbore.** Cut it as the root's outline grown by a running
  clearance, turned about the limb's pivot through its whole swing in steps of a
  degree or so (the union of the turned outlines), across the flank from a
  floor a running gap under the limb's flat face. The joint line then opens to
  a crescent on one side at each end of the swing: under the elbow and in front
  of the stifle for legs that gather. Pivot the limb on the centre of its first
  station, where the root is a circle, and the crescent stays narrow near it.
- **Key it, don't peg it.** A D-socket from the flat face onto the shaft end,
  glued; its flat's direction set in the frame the limb is drawn in (a world
  direction less the figure's pitch in a pitched sculpt frame), the same world
  direction as the lever's socket on the other end of the shaft.
- **Turn the colour tools with it.** A hoof or cuff coloured by a tool drawn in
  the rest pose misses the limb once it has turned: the piece comes back empty
  and the assembly fails on a null shape. Turn the tool by the limb's angle.

## The flat inner face

Seen from the front the limbs' flat inner faces read as plates between them.
Bevel round each flat face steeper than 45° to it (0.8 across by 1.2 up is
56°) — the limb prints on that face, so the bevel is an overhang at the bed
and must clear the gate. Bevel element by element (each bone, knob and the
upper loft on its own half) and then fuse: the fused limb's outline has
concave corners where a knob meets a bone, and the kernel refuses the bevel
round it at any size ([[fillet-chamfer-pitfalls#bevel-the-pieces-then-fuse]]).

## Carved relief and carved lines

A harness strap, a saddle cloth, a lock of hair is a side-view outline pushed
across the body and intersected with the body grown by the relief height; a
carved line or nostril is the outline intersected with the shell between the
body grown by a little and the body shrunk by the depth. Both follow the
surface exactly and cost one grown body per height. Two ways it reads wrong:

- An outline pushed across the whole width covers everything under it: a
  forelock drawn in side view became a helmet over the whole forehead. Bound
  such a relief in plan as well — a tapering outline across the face, pushed
  along the head's own up-axis — so it stays a tuft.
- A raised ridge on a steep side surface (a brow over the eye) stands out
  sideways; from the front its end reads as a flat tab, like a blinker. Carve
  such lines as grooves.

## Ears across the split

A pair of ears straddling the split prints only if the V between them opens at
more than 45° from the split plane on each side: that face is a downward
overhang of each half's ear. With parallel outer faces the ears then close
into a ridge only half their thickness above the V, so a V that starts high
leaves a notched block (a crown from the front) and one that starts low cuts
the tips off. Lean each outer face out by a flare angle as well; the two faces
of an ear of half-thickness `T` at the notch meet at

    s = (T + s_n · tan θ) / (tan θ − tan α)

up the ear axis, for a notch at `s_n`, a V half-angle `θ` over 45° and a
flare `α`. Choose the notch height and the ear length so that `s` falls at the
leaf's tip and each ear ends in a point. A horse's ear is about a third of its
head's length; at a half it reads as a donkey's.

## A plate across the split

A mane or tail plate on the midplane locates the two halves, so each half
carries half of its groove. Cut square, that recess has a ceiling parallel to
the bed the half prints on, and where the plate leaves the body the ceiling
hangs from one side: the overhang gate calls it support. Roof it instead —
over every convex piece of the plate's outline that reaches the body, a draft
of that piece rising from the groove's floor at 50° to the split plane:

- **Draft the pieces, not the outline.** A tapered extrude of the whole
  outline (a union of capsules) returns a null shape; each capsule on its own
  drafts cleanly, and the drafts fuse.
- **Run each draft past its neighbours.** Consecutive capsules of a chain
  share an end circle, and their drafts lay the same cone over each other;
  the fuse leaves faces of a thousandth of a square millimetre that mesh with
  a crack. Extend each capsule a few tenths of a millimetre past both ends so
  neighbouring drafts cross, and stop each draft short of its ridge (85 %):
  a top face a tenth of a millimetre wide cracked the same way.
- **Equal radii end in a ridge.** A capsule whose ends differ drafts until the
  small end closes and stops on a flat top — a ceiling again. Bury only an
  even-radius tongue: trim the rest of the plate (locks, strands) at the body's
  side outline, where nothing buried of it would be seen. Cones along a
  tapering capsule also roof it, but their apexes piercing a thin skin left
  open edges in the mesh.
- **Centre the tongue on the host's surface line.** A tongue drawn a little
  inside the crest only grazes out of it, and the groove leaves the skin
  beside it a fraction of a millimetre thick; put the tongue's centre line on
  the section outline's crest (project the plate's points onto it), half in and
  half out, and keep its radius small where the host is narrow — the roof
  rises 1.2 mm per millimetre of radius at 50°.
- **Drop the slivers.** Where a roof passes just under a thin crest's skin it
  cuts a shaving loose; drop solids of a few cubic millimetres after the cut
  and assert nothing larger came off.
- **Every slot through the split face needs the same.** A pin's slot through a
  fin is a ceiling open to the side the pin comes from; a hip roof over the
  slot's rectangle, kept clear of any neighbouring hole, fixes it.

On the plate itself, bevel the face it prints on steeper than 45°
([[overhangs-and-print-orientation#the-fixes-in-the-order-worth-trying]]).

## Walls the print gate finds thin

The wall gate finds what the eye does not, and the same few shapes recur:

- **A limb root where the flank grazes the flat face.** The root fills the
  counterbore with the body's mass beyond the flat face; where the flank
  stands only a fraction of a millimetre past that face, the root there is a
  sheet. Keep the root to where the flank stands at least a wall's thickness
  past the face (the body's section at that offset, pushed across) and let a
  hairline show elsewhere.
- **A carved line that wraps under an edge.** A lip line pushed across the
  whole head also runs under the chin, and close above the chin's edge it
  leaves a lip thinner than two lines. Carve such lines on the sides only.
- **A cut near a nose or tip.** A nostril's round end within a couple of
  millimetres of the muzzle's front leaves a thin front wall; pull it back.
- **Grooves between converging strands.** Where a plume's strands draw
  together, the ridge between two grooves thins below a wall. Run a groove
  only where the strand spacing leaves a ridge of a millimetre beside it.
- **Relief edges on a surface that faces along the push.** Relief pushed
  across Y ends in slab walls; where the surface itself faces forward (a
  chest), those walls meet it at a grazing angle and the relief's edge is a
  knife. The same happens at a limb's joint line on the chest. Route straps
  and joint lines over surfaces that face sideways, or accept and record it.

## Ornament and the assembly path

Every ornament round changes what stands in the paths parts are fitted along:
a mane lock leaning back over the withers stood in the path of the wing
dropped onto its hinge; a full-width tail dock stood in the path of a pin
drawn out behind the saddle. Rerun the assembly sequence after each round,
and bound the ornament by the paths — a lock ends before the plane the fitted
part drops past; a tail's strands start drawn together at the dock, as a real
dock is narrow.

## Split slivers

Where a section's tip lies on the midplane the split leaves a zero-volume
sliver beside each half. Drop solids under a hundredth of a cubic millimetre
after the split and assert that nothing larger is left over.