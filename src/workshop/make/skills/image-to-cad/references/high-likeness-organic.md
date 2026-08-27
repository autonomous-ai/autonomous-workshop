# High-likeness organic subjects

Read this file when the subject is an animal, figurine, character, toy, or any
body whose likeness lives in its silhouette rather than in its dimensions —
and always when the user has named an explicit 90-95 % likeness target.

Step 6 of `SKILL.md` chooses a construction family from the form. This file
covers what happens after that choice on an organic subject: how surface
decoration is kept out of the core solid, which contacts have to be declared
before the assembly is posed, and what a station table needs beyond a radius.
Every rule here exists because the deterministic gates pass the failure it
describes.

For high-likeness figurines, separate **silhouette mass** from **surface
decoration** in the spec. Build and validate the large organic core solids first:
torso, head, tail, limbs, perch/base. Then add colour bands, wrinkles, ridges,
scales, spikes, beads, and texture as shallow surface details with bounded
penetration, or as separate labelled visual skins. Do not specify a full-depth
band or spike field that cuts through a lofted body unless the table also names
the boolean/overlap limit that keeps the resulting solid non-self-intersecting.

For any explicit 90-95% likeness target, the **spec itself has a completeness
gate before CAD starts**. A short intent document, prompt-style visual target,
or placement-only table is not a build spec; it is a flow failure because the
CAD step will invent primitive stand-ins. The spec must include, at minimum:
view coverage and reconstruction notes, a measurement audit including tool
limitations, observed side/front station tables for the main organic silhouette,
a scale anchor with ratios, printable-part decomposition, connector/shared
dimension tables when modular, one build123d operation row per feature with
numbers and risks, named parameters that own shared dimensions, a proportion
ledger, and a verification checklist. If those sections cannot be populated
from the images, stop and measure/probe the images again before writing CAD.

If the details are separate labelled solids, place them as true surface skins:
tangent or with a tiny visible clearance from the core, and non-overlapping with
each other. Do not assume "same visual module" hides collisions. The CAD
interference gate walks leaf solids inside compounds; a compound of overlapping
colour patches, tail joints, eye discs, mouth beads, or bark rings still fails
`inspect interfere`. If a decoration must overlap to be manufactured as one
body, boolean-fuse that local group into one validated solid before review;
otherwise keep it outside the core with clearance.

For tight decorative curls, do not start with a swept Archimedean spiral. A tube
following a small-radius spiral can self-intersect while still looking like the
right construction. Use a collision-safe approximation first — a torus/partial
ring, a few non-touching arcs, or an obviously separated raised spiral line —
and only refine to a real spiral after validation and interference pass. The
same applies to crest and dorsal markers: when the surface height is uncertain,
place the first version clearly outside the core, not "almost embedded".

For bead rows, pupils, nostrils, separate jaw skins, torus tails, and other small
visual cues, specify a clearance at least equal to the small detail's radius
unless the pieces are locally fused and revalidated. Tiny decorative overlaps
still fail `inspect interfere`; do not spend a run on a connector stem, bead row,
or stripe that is optional for silhouette until the primary body, head, perch,
and tail curl clear the gate.

Do not solve interference by making the object explode visually. For a
high-likeness target, a gap between a cue and its core is a defect whether or
not anything renders it. If a required cue reads as floating — eye discs,
mouth beads, jaw patches, dorsal spikes, crest, stripes, or tail curl — the next
spec must group that cue with its local core and prove the local group before
assembling the whole model.

Do not solve interference by moving a required feature out of the reference
pose. A side-view part can be shifted along the hidden depth axis and still pass
the side silhouette while becoming wrong in 3D: a tail no longer rooted in the
body, toe pads no longer gripping the branch, or colour bands standing off the
skin as rods. For 90-95% likeness, the spec must name maximum visible gap or
contact constraints for every defining feature, and CAD must satisfy those
constraints in the actual assembly pose.

A complete station table still needs the right section vocabulary. For a
90-95% organic target, radius-only elliptical stations are insufficient when
the reference shows a flattened flank, keel, cheek, brow, or asymmetric belly;
record the cross-section shape and landmark rails at each station. Sparse ruled
ellipse lofts tend to produce a faceted barrel even when their side envelope is
correct. Likewise, a defining blade such as a casque, crest, ear, or fin is not
allowed to become a constant-depth extruded side polygon: give it at least three
depth stations and loft the rounded volume. Capsule chains are acceptable only
as pose/contact probes for limbs; a reviewable high-likeness limb needs tapered
segment lofts and explicit joint transition masses. Conformal colour shells
also need measured boundary curves in side/profile space; intersecting a shell
with repeated full-height slabs produces technically conformal but visually
uniform bands.

Local groups are not enough; the assembly placement also needs a preflight. For
any high-likeness figurine with head/body, tail/body, limb/body, or feet/perch
contacts, the spec must include a placement table with the intended relation and
a minimum/maximum contact allowance for each pair. Run `inspect interfere` on
the full assembly and, if it fails, treat the run as a failed output.

Do not replace a defining silhouette with a generic safe primitive when the
target is 90-95% likeness. Safe approximations are acceptable only as temporary
gate probes; in the delivered spec, defining cues must use a form family that
matches the image.

Do not trust a risky swept organic feature because a standalone helper or
approximation once looked plausible. Tail spirals, curled tubes, horns, and
crest chains must be validated as the actual emitted part entry before the
combined assembly can be considered reviewable. A passing interference check
does not rescue a `validate` failure on the same run; record it as failed,
update the spec/skill lesson, and start the next version fresh.

Likewise, a visual assembly pose is not allowed to rely on large overlaps.
For every seated module in a multi-part figurine — head into body, tail into
body, limb into body, foot on perch — write one row that names whether it is
`clearance`, `intentional seated contact`, or `cosmetic near-contact`. If it is
not a real connector, leave a visible air/contact relation rather than sinking
the parts into each other. The downstream CAD run must be able to pass
`inspect interfere` before any likeness score is claimed.
