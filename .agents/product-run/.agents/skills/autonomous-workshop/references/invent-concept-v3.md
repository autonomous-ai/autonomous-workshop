# Invent Concept v3: fixed CAD-reconstruction views

This capability applies only when its exact path and hash appear in
`STAGE.json.inputs.invent_concept_capability`. It replaces the v1 six-file and
v2 adaptive visual-plan authoring surfaces for this frozen run. It does not add
a lifecycle stage or transfer host effect authority to the native session.

## Ownership boundary

Author exactly two design inputs:

1. `drafts/invent-source.json`, containing the selected Inventor, complete
   ranking, physical concept, and research.
2. The exact `STAGE.json.inputs.visual_instructions_path`, containing only a
   shared appearance description and concise depiction notes for the fixed
   views.

Do not author derived roles, prompts, projections, descriptors, manifests,
image bytes, effect intents or receipts, gates, CAD, STEP, or STL. The
installed finalizer validates both authored inputs and deterministically
derives the pre-render Concept. Exit as soon as the finalizer succeeds; the
host performs image effects only after the native turn exits.

The source uses the same complete physical schema as Invent Concept v2. It must
contain exactly `selected_inventor_id`, `ranking`, `concept`, and `research`.
The `concept` must fully state the physical object, category, summary,
signature interaction, anti-generic signature, intended experience,
non-negotiable constraints, numeric `envelope_mm`, `print_stance`, and one
through sixteen stable components. Every component has exactly:
`key`, `name`, `purpose`, `form`, `measurements`, `placement`, `interfaces`,
`assembly_relationship`, and `signature_contribution`. It must also include
`interaction_trace`, `make_proof_target`, `constraints`, `decisions`,
`assumptions`, and `unresolved_risks`. Research sources and findings must be
jointly empty or jointly populated, with every build-critical external fact
traceable to a cited finding and every deliberate numeric decision explained.

Stable component keys are lowercase kebab identifiers for product-level parts,
not CAD variants or repeated instances. The fixed image inventory is exactly:

- front
- top
- bottom
- exploded
- one isolated image for each stable component, in source order

With the four overall views, the 20-image ceiling permits at most sixteen
components. Invent does not choose, add, remove, or reorder image roles.

## Fixed visual instructions

Use this exact JSON shape. The component keys and their order must exactly
match `concept.components`. The exploded note must name every component key.
Notes describe how to depict already-declared facts; they must not introduce
features, dimensions, components, materials, or mechanisms absent from the
physical source.

```json
{
  "schema_version": 3,
  "kind": "autonomous-workshop.fixed-concept-view-instructions",
  "appearance": "Matte warm-white shell with a muted blue core and crisp part boundaries.",
  "views": {
    "front": "Make the defining front seam legible.",
    "top": "Make the top aperture and footprint legible.",
    "bottom": "Make the flat print underside legible.",
    "exploded": "Separate shell and core; show every mating face and assembly relationship."
  },
  "components": {
    "shell": "Show the complete shell alone with its capture ledge unobscured.",
    "core": "Show the complete core alone with its keyed interface unobscured."
  }
}
```

The host-owned prompt protocol renders one unchanged object with direct
orthographic-like camera directions, pure white or very light neutral
background, flat neutral light, restrained matte materials, and crisp readable
construction. It forbids scenes, text, dimensions, arrows, labels, logos,
watermarks, people, hands, props, dramatic perspective, reflections, and depth
of field. Front establishes appearance; top and bottom reference front;
exploded references all three; each isolated component references exploded.

## Finalize

Use the packet-bound instruction path exactly. Do not pass `--concept-root` or
`--visual-plan`.

```sh
python .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . invent \
  --source drafts/invent-source.json \
  --visual-instructions artifacts/invent/visual-instructions.json
```

If both authored inputs exist, finalize immediately. If validation fails,
repair only the smallest rejected input and retry. Do not rerank, restart
research, delegate, review, polish, or reopen concept exploration unless the
host explicitly returns the stage through a lifecycle revision.
