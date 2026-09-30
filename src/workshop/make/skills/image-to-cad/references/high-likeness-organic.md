# High-likeness organic subjects

Read this file when the subject is an animal, figurine, character, toy, or any
body whose likeness lives in its silhouette rather than in its dimensions —
and always when the user has named an explicit 90-95 % likeness target.

Step 6 of `SKILL.md` chooses a construction family from the form. This file
lists what the spec must then carry for an organic subject. Why each rule
exists — decoration versus core mass, spirals that self-intersect, the two
wrong ways to clear an interference, the section vocabulary a station table
needs — is in `skills/wiki/pages/image-reading/organic-likeness.md`
(`wiki show organic-likeness`). Every rule exists because the deterministic
gates pass the failure it describes.

## The spec's completeness gate, before CAD starts

For any explicit 90-95 % likeness target, a short intent document, prompt-style
visual target, or placement-only table is not a build spec; it is a flow
failure because the CAD step will invent primitive stand-ins. The spec must
include, at minimum: view coverage and reconstruction notes, a measurement
audit including tool limitations, observed side/front station tables for the
main organic silhouette, a scale anchor with ratios, printable-part
decomposition, connector/shared dimension tables when modular, one build123d
operation row per feature with numbers and risks, named parameters that own
shared dimensions, a proportion ledger, and a verification checklist. If those
sections cannot be populated from the images, stop and measure/probe the images
again before writing CAD.

## What the spec must name

- **Silhouette mass separate from surface decoration**, core solids first; any
  full-depth band or spike field names its boolean/overlap limit.
- **Decorations as skins**: tangent or with visible clearance, non-overlapping;
  overlapping groups fused and revalidated. Small cues get a clearance at least
  equal to their radius. Optional cues wait until body, head, perch and tail
  clear `inspect interfere`.
- **Collision-safe first versions** of tight curls, crests and dorsal markers.
- **A maximum visible gap or contact constraint for every defining feature**, in
  the actual assembly pose. Never clear an interference by floating a cue or by
  moving a feature along the hidden axis.
- **A placement table** for every head/body, tail/body, limb/body and
  feet/perch contact: `clearance`, `intentional seated contact` or `cosmetic
  near-contact`, with a minimum/maximum contact allowance. Run `inspect
  interfere` on the full assembly; a failure is a failed output, and it must
  pass before any likeness score is claimed.
- **Station tables with cross-section shape and landmark rails**, not radius
  only; defining blades with at least three depth stations; limbs as tapered
  segment lofts with joint transition masses; colour shells from measured
  boundary curves.
- **Defining cues in a form family that matches the image** — safe primitives
  only as temporary gate probes.
- **Risky swept features validated as the emitted part entry.** A passing
  interference check does not rescue a `validate` failure on the same run;
  record it as failed, update the spec/skill lesson, and start the next version
  fresh.
