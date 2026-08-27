# Scenes of many repeated pieces

Read this file when the reference shows repeated, individually visible pieces —
a board and its men, a tray of parts, a rack, a tiled or populated surface.

A scene like this can match its broad archetype while missing most of what
defines it, and the single likeness number in Step 8 will not say so: the
outline is dominated by the frame, not by what sits inside it. The landmark
inventory below is scored per category for that reason, and the placement audit
runs before geometry rather than after.

**Multi-component scene landmark gate.** A scene with many repeated pieces can
match its broad archetype while missing most defining landmarks.
Before CAD starts, inventory the visible landmarks by category and give each a
count, placement rule, or ratio where the image supports one:

- outer silhouette and frame tiers;
- region boundaries and their layers;
- repeated-site density and exclusion zones, measured as rows/columns or
  occupied area rather than described as "many";
- repeated-piece count and distribution, including whether the layout is
  regular, sparse, clustered, or deliberately irregular;
- one silhouette checklist per defining module;
- rule- or prose-required accessories that are absent from the hero image.

The operation table must have a row for every landmark, and the verification
checklist must score the categories separately. Do not
assign a single 90-95% likeness number until every defining category has its own
finding.

When a reference shows a manageable number of repeated, individually visible
pieces (up to roughly 50), record their observed normalized centroids or a
traceable placement table. Do not replace an irregular photographed layout with
a grid sampler, farthest-point distribution, or random seed merely because the
count is correct. Those algorithms create a conspicuous new composition. Use a
procedural distribution only when the reference itself is procedural or when
the user asked for a new playable setup rather than a reproduction; record that
choice as `[assumed]`.

If those pieces must occupy legal sites, observed centroids are evidence, not
final assembly coordinates. Map
each centroid to one **unique** valid site, enforce every exclusion zone, and
record the displacement or a maximum allowed snap distance. Run a local audit
that proves count, uniqueness, site membership, and exclusion-zone clearance.
A visually plausible centroid can still occupy an excluded region;
full-assembly interference catches the collision late, while the placement
audit prevents it before geometry.

Any defining landmark whose bbox is under roughly 15% of the whole scene needs
a local verification target in the spec. A full-scene render cannot prove a
small feature even when it technically exists.
