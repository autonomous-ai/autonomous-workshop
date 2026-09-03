# ADR 0042: Fix Concept views for CAD reconstruction

Status: accepted; implemented behind acceptance activation

## Decision

New Forge and Quest runs may freeze `invent-concept-v3.md`. The native Invent
turn authors the complete physical source plus one fixed-view instruction file.
The host deterministically derives exactly front, top, bottom, exploded, and
one isolated image per stable source component. The role graph is front;
top/bottom after front; exploded after all three overall views; then each
component after exploded. The existing 20-image ceiling therefore limits a v3
Concept to sixteen components.

The host owns a frozen prompt block adapted from the direct-view consistency
rules used by the sibling `panda-social-cc-agent` concept prompts: one unchanged
object, orthographic-like camera directions, neutral background and lighting,
matte readable surfaces, and no scene, text, annotations, people, props,
reflections, or dramatic lens treatment. Invent owns only appearance and
depiction notes; neither input may author derived prompts, roles, images, or
effect state.

Normalized numerical facts remain authoritative. Images are simple design
direction for later CAD reconstruction and make no claim of dimensional
accuracy, buildability, printability, or physical performance.

## Compatibility and activation

V1 keeps its historical six-file fixed contract and Concept v2 bytes. V2 keeps
its two-input adaptive role plan and Concept v3 bytes. V3 introduces Concept v4
bytes and a matching frozen deep-economics-v15 profile. Exact checkpoint
markers govern resume, so disabling v3 affects only creation of new runs and
never downgrades a frozen v3 run.

V3 remains disabled for ordinary creation until deterministic and authenticated
Forge and Quest acceptance evidence passes. Acceptance runs can opt in with
`WORKSHOP_INVENT_CONCEPT_V3_ACCEPTANCE=1`.

## Signature evidence

The anti-generic signature remains explicit text in the Invent source. Concept
does not generate an extra signature-experience image. Make still owns fresh
actual-state renders, blind schema-v4 signature review, and integrated CAD
verification; Concept pixels remain inadmissible as Make evidence.
