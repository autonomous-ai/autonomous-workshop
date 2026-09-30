---
title: Design for assembly
tags: [assembly, dfa, part-count, fastener, snap-fit, symmetry, self-locating]
aliases: [dfma, boothroyd dewhurst, minimum part count, design efficiency, assembly cost, poka-yoke]
sources:
  - https://en.wikipedia.org/wiki/Design_for_assembly
  - https://www.fabflow.app/blog/design-for-assembly-dfa-complete-engineering-guide
  - https://www.denix.osd.mil/soh/denix-files/sites/21/2016/03/02_MIL-STD-1472F-Human-Engineering.pdf
related: [printed-part-count, joints, feature-build-order, handheld-ergonomics]
updated: 2026-09-23
---

# Design for assembly

Every part a printed design adds is a part to print, orient, clear, fit and
retain. Design for assembly (DFA) is the industrial method for removing
parts and making the rest go together one way only. [[printed-part-count]]
decides whether to split a printed body. This page decides whether a separate
part should exist at all, and how the survivors should assemble.

## The minimum-part-count test (Boothroyd–Dewhurst)

The Boothroyd–Dewhurst method (1977) asks three questions of every part. A
part is theoretically necessary only if one answer is yes:

1. Does it **move relative** to the parts already assembled?
2. Must it be a **different material** (or isolated from the others)?
3. Must it be **separate** so the others can be assembled, or for service?

Every part that answers no to all three is a candidate to merge into a
neighbour. Screws, spacers, clips and brackets are the usual casualties. For
a printed design, a merged part is often simply a feature on the part next to
it: a boss instead of a standoff, an integral pin instead of a pin plus
socket, a living hinge or print-in-place joint instead of two halves and a
pin ([[joints#revolute-joints]]).

## Design efficiency

```text
design efficiency = (3 s × theoretical minimum part count) / total assembly time
```

Three seconds is the ideal time to handle and insert one easy part. Above
60 % is excellent, 40–60 % good, 20–40 % fair, and below 20 % poor. The index
exposes assemblies whose parts are fiddly (long insertion times) as well as
too many.

## Guidelines for the parts that remain

- **Fewer parts, fewer fasteners.** Replace screws with snap-fits,
  press-fits or tab-and-slot features where the loads allow. A fastener is the
  part that answers no to all three questions most often. MIL-STD-1472F asks
  the same of maintainable equipment: minimise the number and diversity of
  fasteners, and make each fastener's location obvious when more than one type
  is used.
- **Self-locating and self-fastening.** Parts should guide themselves into
  place (chamfers, pilots, bosses in holes) and hold without an extra
  fastener.
- **Symmetric, or obviously asymmetric.** A part that is symmetric about its
  insertion axis (and end to end) needs no orienting. If it cannot be
  symmetric, make it obviously asymmetric so it cannot go in wrong. In the
  Boothroyd–Dewhurst tables, handling time grows with the rotation needed to
  orient a part: alpha symmetry (about the insertion axis; a plain cylinder is
  360°, a fully asymmetric part 0°) adds up to about 4 s, and beta symmetry
  (end to end; a washer is 180°, a headed bolt 0°) up to about 4.5 s.
- **Chamfers on every insertion.** Little or no resistance to insertion; a
  lead-in on the hole or the pin. A 30° chamfer gives a capture radius about
  3× the clearance, and tapered edges of 5–15° guide rectangular parts.
- **Top-down assembly.** Build the stack from one direction onto a base part,
  so gravity holds each part while the next goes in.
- **No tangling, no nesting** of loose parts (springs, open clips).

## Applying it to a printed model

1. List every part with its three answers in the spec BOM. A part that
   answers no everywhere is merged, or its survival is justified.
2. Give every separate part a single assembly direction and a keyed
   orientation (a single flat, an asymmetric tab), and check it with the
   joint's `clear` and `blocked` conditions ([[joints#the-two-conditions-every-joint-owes]]).
3. Prefer snaps and captured pins over glue. A glued joint answers "must be
   separate" with no, which means it should usually have been one printed
   part.
4. Put the chamfer on the socket or the pin as a feature in the source, not
   left to post-processing.
