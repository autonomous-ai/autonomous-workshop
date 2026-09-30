---
title: Form and finish heuristics
tags: [industrial-design, fillet, chamfer, parting-line, seam, form, aesthetics, surface]
aliases: [edge treatment, radius consistency, visual quality, dieter rams, good design, split line, cosmetic seam]
sources:
  - https://firstmold.com/tips/fillets-and-chamfers/
  - https://www.protolabs.com/resources/design-tips/planning-for-parting-lines-in-injection-molding/
  - https://www.vitsoe.com/us/about/good-design
related: [product-aesthetics, printed-part-count, fillet-chamfer-pitfalls, handheld-ergonomics, colour-matching, post-processing-and-finishing, moulds-and-casting-from-prints]
updated: 2026-09-29
---

# Form and finish heuristics

Once the geometry is correct, how it reads — edges, seams, surface
continuity — decides whether the model looks like the product in the
reference or like a CAD exercise. These are industry rules for edges and
seams, stated so they can be applied as parameters. The design order above
them — direction, hierarchy, proportion, silhouette, CMF — is
[[product-aesthetics]].

## Edges: fillet or chamfer

- **Character**: fillets read as soft and safe, chamfers as sharp and
  technical. Most consumer products fillet their external edges and keep
  chamfers for particular functional or stylistic details. Match the
  reference: a product photographed with crisp bevels gets chamfers, even if
  fillets are easier.
- **Function**: fillets spread stress over a larger area than a chamfer of
  the same size, so they suit plastic parts under repeated load. Chamfers are
  better lead-ins for holes and locating pins, blunt an edge more cheaply, and
  make countersinks that fillets cannot.
- **Keep a constant wall**: on a shelled part, outer radius = inner radius +
  wall thickness (`R = r + t`), and an outer chamfer is the inner chamfer
  offset by the wall. Minimum inner radius 0.5 mm.
- Parametrise the radius once and reuse it across similar edges, so the edge
  family reads as one design.
- On the bed face of a printed part a fillet is an overhang, so use a chamfer
  there ([[joints#rules-that-are-easy-to-break]]). Kernel limits on fillets:
  [[fillet-chamfer-pitfalls]].

## Seams and parting lines

A parting line is where two halves meet: mould halves, or two printed shells.

- **Put it on a sharp edge.** Along a crisp edge the seam is camouflaged and
  a small mismatch is invisible.
- **Never across a smooth or curved surface.** Any mismatch there shows as an
  obvious step or ridge, and hiding it needs tolerances nobody can hold.
- For a moulded part the line follows where the surface tangent is parallel to
  the opening direction. For a printed split, choose the split plane so it
  lands on an existing edge or a deliberate groove, and keep it off
  cosmetic faces.
- A deliberate groove (a reveal) at the joint turns an unavoidable seam into
  a design line. Whether a seam should exist at all is
  [[printed-part-count#the-cosmetic-seam-trap]].

A seam placed for painting in separate colours:
[[post-processing-and-finishing]].

Parting lines and keys of a two-part silicone mould:
[[moulds-and-casting-from-prints]].

## Principles of restraint

Dieter Rams's ten principles (Vitsœ) are a widely quoted statement of
industrial design values: good design is innovative, useful, aesthetic,
understandable, unobtrusive, honest, long-lasting, thorough down to the last
detail, environmentally friendly, and as little design as possible — "less,
but better", concentrating on the essential and leaving out non-essentials.
For reference-image work, "thorough down to the last detail" and "as little
design as possible" pull the same way: reproduce the details the reference
shows, and do not invent decoration it doesn't.

## Checklist

- Edge treatment matches the reference (soft or crisp), with one radius
  parameter per edge family.
- Shell walls keep `R = r + t`.
- Every split between printed parts sits on an edge or a reveal, never
  mid-surface.
- Hand-contact edges are rounded ([[handheld-ergonomics]]); bed edges are
  chamfered.
