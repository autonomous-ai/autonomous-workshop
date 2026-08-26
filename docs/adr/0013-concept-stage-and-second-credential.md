# ADR 0013: Concept stage and the second image-provider credential

- Status: Accepted and implemented
- Date: 2026-08-26
- Owners: Concept, Make, Workflow, and Integrations component maintainers

## Context

ADR 0012 established the native-runtime boundary this decision operates
within: one native Codex session owns cognitive and tool-using work, and a
narrow trusted host owns lifecycle, exact-byte gates, durable state, and
external effects. Under that boundary, `main`'s Invent stage produces
`InventedV2.concept` and `.research` as free-form `Mapping[str, Any]` with no
structural contract — only `title` and `summary` are length-checked. Make's
entire design input is that object plus the Wish text and a lane blueprint,
yet Make's own shared skills already instruct the agent to "freeze the visual
target" before building, with no stage that does that freezing.

A prior implementation solved this with Python: prompt builders, a
Python-spawned agent door, and a hardcoded OpenRouter/OpenAI adapter pair.
ADR 0012 forbids each of those mechanisms by name — Python prompt chains,
Python-spawned agent processes, and Python-side candidate generation are not
extension points. That design cannot be ported; it must be rebuilt as a real
stage with a deterministic host gate, the shape ADR 0012 already prescribes
for cognitive work.

## Decision

Concept becomes the sixth run stage, between Invent and Make:

```text
Wish -> Match -> Invent -> Concept -> Make <-> Playtest -> Release -> Deliver
```

It is mandatory — every run reaches it — and it is a real artifact-owning
stage, not a hardened field on `InventedV2`: a concept is a tree (images, a
descriptor, a research record), and the drawing effect must happen between a
gate that validates the brief and a binding that hands it to Make, which is
the before/effect/after shape of a stage, not a validation rule inside one.

In the Concept turn, Codex researches the Wish through its own web search —
the sandbox has no other network access — and writes a `ConceptBrief` (object,
category, envelope in millimetres, wall thickness, features, print stance,
per-component form/dimensions/placement/interfaces, fit target, and
assumptions), a research record (each finding bound to a source with an
excerpt hash and retrieval time, or a recorded decision with its reason), and
one drawing instruction per required image role
(`front`/`top`/`bottom`/`exploded`/one per component). The host validates
that structure; it does not write, score, or choose any of it. The agent
authors the drawing instructions verbatim — this is what makes the design
admissible under ADR 0012: moving prompt text into the agent's output, rather
than composing it in Python, makes the same creative work legal, because the
agent has the Wish, the Taste, and the research a Python template never did.

Codex cannot reach an image provider itself — the `workshop-product-run`
permission profile disables the sandbox network entirely, so this is not a
policy choice but a physical one. A new host integration,
`src/workshop/integrations/concept_images.py`, draws each image between native
turns once the structural gate passes: it transports the agent-authored
instructions verbatim, attaches only the references the concept itself named,
verifies the returned bytes, and writes them into the concept tree. It
composes nothing. This mirrors the Release/Factory publisher exactly: the
host's `evaluate_concept_stage` (gate `concept.sealed-v1`) validates the
brief, research, and drawing instructions first — refusing here, before any
image spend, if the brief decided nothing — then calls the effect inside gate
evaluation, then builds evidence and `additional_artifacts` over the whole
resulting tree. One gate decision seals the brief, research, drawing
instructions, and every image together into one `concept_sha256`.

The adapter's credential lives at `$WORKSHOP_HOME/credentials/concept-images.env`
(0600 inside a 0700 directory), read lazily only after a native turn exits
and never entering the Codex subprocess environment — the same isolation
`factory.env` already establishes. **This is a second model/API credential
beyond the developer's own Codex subscription, required for every run**,
since Concept is mandatory. When the credential is absent, the
missing-credential exception propagates out of gate evaluation and the host
converts the otherwise-accepted proposal into a `waiting` outcome with a
concrete `Need`, writing a wait file bound to the checkpoint exactly like
`release-effect-wait.json`. The run does not skip Concept and does not
proceed to Make without a sealed concept; `workshop resume` re-checks the
credential and draws the remaining images in the same session once it is
configured, without re-deriving the accepted brief.

`NativeMade` gains a required `concept_sha256` binding it to the exact concept
it was built from. Because Concept is mandatory, this field is required, not
optional. Make additionally checks that its declared `product.json`
components correspond one-to-one with the concept brief's components, and
refuses any product file whose bytes match a concept image — replacing the
deleted vision-model exploded-view inspector, which needed a second model call
inside a turn and cannot exist under ADR 0012's boundary. No component image
inherits shape from another image, so an omission in the exploded view
corrupts nothing downstream; that trade-off is deliberate (see the change's
`design.md`, decision D4).

A failed Playtest verdict may name `concept` in a `Feedback` item's
`invalidates` list, routing the run back through a fresh Concept turn —
carrying the standing concept and that exact feedback — before Make runs
again. Feedback that invalidates only the build leaves the standing concept
unchanged and skips Concept for that round.

## Alternatives considered

### Harden `InventedV2.concept`/`.research` in place

Rejected. Invent is the only stage that owns no artifact tree; giving it one
for images, a descriptor, and a research record makes it a different stage in
all but name, and still leaves nowhere for a between-turn effect to live
inside a single-gate stage.

### Two native turns — author, then inspect the drawn images

Rejected. It doubles turn cost against the 32-turn ceiling and breaks the
one-gate-per-stage rule that keeps a stage's seal coherent over exactly the
bytes its gate reviewed.

### Draw images inside the Make turn

Rejected. It is impossible — the Make turn's sandbox has no network either —
and wrong even if it were possible: the design would no longer be decided
before geometry exists.

### Keep a vision-model exploded-view inspector, relocated to the Make boundary

Rejected. The two checks answer different questions: the deleted inspector
protected each component *image* from being drawn off an exploded view that
omitted it; the Make-boundary component check protects the product's *part
list*. Since the brief is complete in text and governs Make, substituting one
for the other would let a bad component image ship silently while Make itself
still passes.

## Consequences

Workshop's quick-start promise that it "does not require a second model API
key" is no longer true for any run — it needs a Codex subscription and a
configured image-provider credential. Docs across the repository state this
plainly rather than hiding it; a run without the credential parks at Concept
with a concrete need instead of failing outright or silently skipping the
stage.

Nothing verifies that a drawn image depicts what its instruction asked for —
the host may not read pixels, and a second model grading the first is exactly
the mechanism ADR 0012 removed. This is accepted: the brief governs Make, not
the pictures, so a wrong image misleads a human reader without corrupting the
geometry. Component images also lose the pose and arrangement cue the
exploded view used to give them, since no image may inherit shape from
another; this is cosmetic and accepted.

Adding a stage costs a sixth entry across the hardcoded per-stage tables in
`workflow/agent_run.py`, `workflow/stage_gates.py`, and `workflow/native_run.py`,
plus a mirrored `concept` subcommand in the run-local
`stage_proposal.py` finalizer that must produce byte-identical canonical JSON
to `src/workshop/concept/native.py`. Materialized instruction bytes changed
(the workflow skill's `references/concept.md` was added, `SKILL.md` was
edited, and every Inventor's `<id>-inventor/SKILL.md` gained a Concept
stage-contribution bullet), so any run parked mid-flight before this change
fails resume closed and must be restarted, by the same rule ADR 0012 already
establishes for changed materialized instructions.

## Compatibility and migration

No persisted run state outlives this change silently: a checkpoint bound to
the pre-Concept lifecycle fails closed on resume because its materialized
instructions no longer match. Parked runs must be restarted, not resumed. This
is stated in the changelog fragment rather than mitigated, matching ADR
0003's rule that a reader reports an explicit unsupported status instead of
silently upgrading old evidence.

## Verification

- One Concept turn produces a brief, research record, and drawing
  instructions that the `concept` finalizer hashes into a canonical pre-render
  contract without requiring image files. After rendering, the host writes a
  distinct `sealed-concept.json` binding the complete tree for Make.
- `evaluate_concept_stage` refuses a brief that decided nothing before any
  image is drawn, and refuses a drawing-instruction set missing a required
  role.
- A missing `concept-images.env` credential converts an otherwise-accepted
  Concept proposal into a `waiting` outcome with a concrete `Need`, and
  `workshop resume` completes the draw and advances without re-deriving the
  brief.
- `NativeMade.concept_sha256` is required and matches the sealed concept it
  was built from; a declared component with no counterpart in the concept
  brief, or a product file whose bytes match a concept image, fails the Make
  gate.
- A `Feedback` item naming `concept` in `invalidates` routes the next round
  through a new Concept turn carrying the standing concept and that feedback;
  a build-only failure does not.
- No image-provider credential ever reaches the Codex subprocess environment
  or its readable filesystem.
- A run parked before this change fails resume closed rather than silently
  continuing under stale materialized instructions.
