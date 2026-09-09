# ADR 0056: Read a cut-out reference's silhouette from its alpha channel

- Status: Accepted
- Date: 2026-09-07
- Owners: Make gate and image-to-cad skill maintainers

## Context

The image-to-cad likeness gate (`check_likeness.py`) and the measurement
tool (`measure_image.py`) opened every reference with
`Image.open(path).convert("RGB")` and derived the subject's silhouette from a
luminance threshold around an estimated background. That is right for a
photograph. It is wrong for a cut-out: a PNG or WebP with a transparent
background carries its silhouette in the alpha channel, and the RGB values
under transparent pixels are whatever the encoder left there.

The fourth microduck run (wish-20260907-095852-07806a43) attached exactly
such a file, a single-duck crop inherited from a GitHub-hosted WebP with
alpha. The Manager proved the consequence with a bounded probe the host
reproduced: the gate admitted 4,083 fully transparent pixels as subject,
rejected 17,747 visible dark ones, and scored the reference's own alpha
outline at IoU 0.655 against the 0.90 floor. No model could have passed,
and the earlier duck runs scored against the same distorted target.

## Decision

`measure_image.alpha_mask(image)` returns `alpha > 127` when an image has an
alpha channel with any transparent pixel and `None` otherwise. Both tools use
it before any RGB conversion: a cut-out's silhouette is its alpha, with no
luminance threshold or shadow test applied and the mask notes saying
`"source": "alpha"`; an image with an opaque alpha channel, or none, is
scored as a photograph exactly as before. The gate's self-check gains a
transparent cut-out that must score 1.0 against its opaque twin and an
opaque-alpha image that must still be read by luminance. The likeness-gate
reference documents the rule. The skill lock is re-sealed; the vendored skill
carries the patch until upstream adopts it.

The floor is untouched. The waiting run receives the corrected tools through
`workshop resume --refresh-tools` (ADR 0052).

## Consequences

- The patched gate scores the microduck reference against its own outline at
  0.998.
- Every earlier likeness number measured against a cut-out reference was
  measured against a distorted target and should not be compared with
  numbers from the corrected gate.
- A photograph's behaviour is unchanged; only images that declare
  transparency are read differently.
