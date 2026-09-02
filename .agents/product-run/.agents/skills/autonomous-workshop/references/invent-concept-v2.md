# Invent Concept v2: two authored inputs

This capability applies only when its exact path and hash appear in
`STAGE.json.inputs.invent_concept_capability`. It replaces the v1 six-file
Concept authoring surface for this frozen run. It does not add a lifecycle
stage or transfer any host authority to the native session.

## Ownership boundary

Author exactly two design inputs:

1. `drafts/invent-source.json`, containing the selected Inventor, complete
   ranking, physical concept, and research.
2. The exact `STAGE.json.inputs.visual_plan_path`, containing an ordered
   adaptive visual plan.

Do not author Concept projections, hashes, manifests, derived-Wish files,
descriptors, image bytes, effect receipts, gates, CAD, STEP, or STL. The
installed finalizer validates the two inputs and derives the pre-render
Concept. Exit after the finalizer succeeds; the host performs image effects
only after the native turn exits.

Use the exact fields below. Arrays may be empty only where the schema permits.
Stable component keys describe product-level parts, not CAD variants or
repeated instances.

```json
{
  "selected_inventor_id": "<selected-id>",
  "ranking": [
    {"inventor_id": "<id>", "rationale": "<why this rank fits the Wish>"}
  ],
  "concept": {
    "title": "<title>",
    "summary": "<bounded physical summary>",
    "object": "<held object>",
    "category": "<product category>",
    "signature_interaction": "<cause and visible/tactile effect>",
    "anti_generic_signature": "<exact form or relationship that must survive>",
    "intended_experience": "<user experience>",
    "non_negotiable_constraints": ["<constraint>"],
    "envelope_mm": {"length": 72, "width": 48, "height": 45},
    "print_stance": {
      "orientation": "<orientation>",
      "supports_required": false,
      "support_notes": "<notes or empty text>"
    },
    "components": [
      {
        "key": "shell",
        "name": "Shell",
        "purpose": "<purpose>",
        "form": "<specific volumetric form>",
        "measurements": {
          "description": "<what is measured>",
          "values_mm": {"length": 72, "width": 48, "height": 45}
        },
        "placement": "<placement>",
        "interfaces": "<interfaces>",
        "assembly_relationship": "<relationship>",
        "signature_contribution": "<contribution>"
      }
    ],
    "interaction_trace": [
      {
        "step": 1,
        "component_keys": ["shell"],
        "cause": "<user or mechanism cause>",
        "effect": "<observable result>"
      }
    ],
    "make_proof_target": {
      "claim": "<claim Make must prove>",
      "method": "<exact proof method>",
      "success_condition": "<passing observation>",
      "failure_condition": "<failing observation>"
    },
    "constraints": [
      {
        "id": "held-envelope",
        "description": "Held size",
        "value": "72 x 48 x 45 mm",
        "basis": {"kind": "decision", "id": "held-size"}
      }
    ],
    "decisions": [
      {
        "id": "held-size",
        "decision": "Use a 72 mm envelope",
        "reason": "Supports a deliberate one-hand interaction"
      }
    ],
    "assumptions": [],
    "unresolved_risks": ["<risk left for Make>"]
  },
  "research": {"sources": [], "findings": []}
}
```

Research sources and findings must be jointly empty or jointly populated.
Every externally grounded build-critical constraint cites a finding; every
finding cites existing source ids. A deliberate numerical constraint instead
cites a decision with a concrete reason.

## Adaptive visual plan

Declare 2 through 20 roles. The first role is the only `primary-form` role and
has no references. At least one later role is `signature-experience`. Optional
`assembly`, `alternate-view`, and `component` roles exist only when they convey
distinct necessary information. References name only earlier roles, in the
declared order, and subjects name only stable component keys.

```json
{
  "schema_version": 2,
  "kind": "autonomous-workshop.concept-visual-plan",
  "presentation": "Warm neutral studio light; matte mineral palette; constant scale.",
  "roles": [
    {
      "id": "held-form",
      "kind": "primary-form",
      "purpose": "Establishes the rounded held seed volume",
      "instruction": "Show the closed seed held between thumb and forefinger.",
      "appearance_references": [],
      "subject_components": ["shell"]
    },
    {
      "id": "star-reveal",
      "kind": "signature-experience",
      "purpose": "Shows the causal closed-to-open star transformation",
      "instruction": "Show closed, thumb action, and open aperture states at one scale.",
      "appearance_references": ["held-form"],
      "subject_components": ["shell"]
    }
  ]
}
```

For a multipart concept, add an assembly role only when an internal
relationship is otherwise invisible, for example:

```json
{
  "id": "captive-assembly",
  "kind": "assembly",
  "purpose": "Reveals the hidden captive-core relationship",
  "instruction": "Separate the shell halves only enough to explain core capture.",
  "appearance_references": ["held-form"],
  "subject_components": ["shell", "core"]
}
```

## Finalize

Use the packet-bound visual-plan path exactly. Do not pass `--concept-root`.

```sh
python .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . invent \
  --source drafts/invent-source.json \
  --visual-plan artifacts/invent/visual-plan.json
```

If both inputs exist, finalize immediately. If validation fails, repair only
the smallest rejected input and retry. Do not rerank, restart research,
delegate, or reopen concept exploration unless the host explicitly returns the
stage through a lifecycle revision.
