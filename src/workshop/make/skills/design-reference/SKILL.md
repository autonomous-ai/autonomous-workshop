---
name: design-reference
description: Research Internet sources for analogous parametric CAD construction patterns and authoritative design specifications, recording URLs, revisions, licenses, claims, and evidence. Use when image-to-CAD or CAD work benefits from prior designs or sourced design facts. Do not use it for purchasable component geometry; use step-parts for that.
---

# Design references

Research the Internet before selecting a construction design. Use authoritative
sources for specifications and licensed analogous designs for construction
patterns; never replace the user's reference image, dimensions or requested
exterior with the nearest-looking result.

## Boundary

- Use this skill for shape archetypes, feature ordering, parametric CAD idioms,
  mechanism construction examples, and sourced design constraints.
- Use manufacturer documentation, standards, or an official technical source
  for numerical specifications. A third-party analogous model is not authority
  for the user's dimensions, ratings or scale.
- Use `step-parts` for a bought motor, bearing, fastener, board, connector or
  other standard component the model must physically fit. Download its canonical
  STEP into `<project-dir>/ref/`, derive the seat with `$cad`'s `cadmount`,
  declare it in `measure/mounts.json`, and run `check_mount`.
- Use `$electromechanical-integration` when the question includes power,
  control, wiring, electrical ratings, exact lamp/socket contacts or removable
  powered interfaces. A design repository is not electrical authority.
- A design reference is not proof of likeness, manufacturability, assembly or
  physical fit. Those claims remain with the project gates.

## Internet research workflow

1. Read and measure the user's evidence first. Name the one or two exact design
   questions research must answer; do not browse with only a product-category
   query.
2. Write a research contract for each question: required facts, acceptable
   source authority, geometry or operation uncertainty, packaging constraints,
   license needs, and the condition that would reject a candidate.
3. Search the Internet with form, feature and operation terms. For example,
   search `tapered shell vent slots parametric CAD`, not merely `enclosure`.
4. Review no more than five strong candidates. Prefer, in order:
   - manufacturer documents, standards and official technical pages for
     dimensions, ratings and compatibility facts;
   - repositories with source CAD or build123d/CadQuery/OpenSCAD code, an
     explicit license, and an immutable commit or release for construction
     patterns;
   - authoritative CAD/kernel documentation for operation-specific questions.
5. Record every used result and meaningful rejection: query, stable URL,
   repository plus commit/release when available, license/use, exact claim or
   specification taken, relevant feature, construction lesson, and status
   (`used`, `rejected`, `miss`, or `unavailable`).
6. Compare the evidence against the research contract, select the design, and
   re-measure every user-specific dimension from the user's image/spec. Do not
   copy an analogous model's placement, scale or silhouette.

A login wall or network failure is `unavailable`, never a miss. A page with no
explicit permission may support a factual citation or visual comparison, but
its code or geometry may not be copied. If no useful source exists, record the
query as a miss and author the design from the user's evidence plus official CAD
operation documentation. A weak analogy is worse than no analogy.

## Build-spec record

Add each used or outcome-defining result to build-spec section **6d** with:

- research query and status;
- source authority/type;
- stable URL and revision/commit/release when available;
- relevant feature;
- exact specification or constraint taken, with units and applicability;
- construction lesson used;
- license/use.

Section 6g then compares the evidence and records the selected construction
design. Project-local `measure/check_spec.py` checks that every selected design
has the required source URL, claim/specification and license record; final CAD
verification does not re-fetch the Internet.

## Integration with image-to-cad

Research after the overall read and feature tree have named the construction
question, and before section 6g selects the design or the feature-operation
table is written. The research must leave enough sourced specifications and
construction evidence for CAD to build without choosing among alternatives.
