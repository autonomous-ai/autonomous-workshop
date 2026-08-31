# Invent contract

Read `STAGE.json`. It binds the exact Wish, immutable Inventor roster, compact
`inventor_discovery_index`, universal blueprint, canonical assignment and
Invented output paths, frozen effort, and current checkpoint. Verify those
bytes before acting. Rank the complete roster from the index first, then read
only the full custom-agent TOMLs for the best three candidates before choosing.
Do not dump, reread, or batch-load every full TOML: the host derives the index
from the exact bound Taste headers specifically to make complete-roster routing
cheap. The blueprint is an open-ended shared contract, not a product
classification.

## Invent Goal and improvement loop

Create one native Codex Goal for this Invent attempt. Its objective is to
select the best-fit immutable Inventor, research, explore, judge, and fully
specify the strongest feasible concept for the Wish through that Inventor's
exact Taste and method.
Its stopping condition is a successful `invent` finalizer for the current
checkpoint.

Before exploring broadly, name the concept's **signature interaction**: the
single physical moment that makes the Wish feel surprising, playful, or
magical, and the **anti-generic signature** that prevents it from collapsing
into an ordinary themed object. Spend depth on making those two ideas coherent
with a feasible mechanism. Additional features earn their place only when they
strengthen that core.

Before ranking, also name the **hardest-to-fake magic**: the perceptual reveal,
motion, rule, transformation, or emotional moment whose loss would make the
Wish generic. Compare every roster entry and select the Inventor whose Taste
and primary method own that magic. Manufacturing convenience is not creative
ownership: one-piece, support-free, or familiar CAD constraints can be solved
with the shared domain skills. Treat selecting only for those conveniences as
a red flag when another Inventor owns the promised perception, movement, rules,
or reveal. Use the selected project-scoped custom agent for specialist work.
The root Workshop Manager reviews and synthesizes its output and remains
responsible for the one stage proposal.

While pursuing the Goal:

1. **Observe:** Read the Wish, complete roster index, the top three full
   custom-agent instructions, relevant skill resources, and any exact upstream evidence. Identify what
   needs factual research and what needs creative exploration.
2. **Act:** Use Codex-native search, browsing, file tools, and specialist
   subagents to research supported facts and explore materially different
   concepts. Save source provenance beside the claims it supports. Use the
   Inventor's declared skills and deterministic craft tools when relevant.
   Before selecting, specify each viable direction deeply enough to compare
   form, envelope, component breakdown, construction, interaction,
   feasibility, assumptions, and risks.
3. **Evaluate:** Compare concepts against the Wish, signature interaction,
   anti-generic signature, full Taste, novelty,
   coherent play, mechanical feasibility, printability, and inspectability.
   Ask independent native subagents to judge bounded questions when subjective
   tradeoffs matter; synthesize their evidence rather than averaging votes.
4. **Improve:** Address the largest weakness, challenge unsupported
   assumptions, and refine or replace the concept. Repeat research or review
   only when it can resolve a concrete gap.

Use bounded breadth: develop a few materially different directions far enough
to expose their mechanisms, choose once the evidence distinguishes them, then
stop generating alternatives. Do not browse when the remaining decisions are
deliberate design choices rather than factual uncertainties.

For Forge and Quest, earn every component before sealing the concept. Identify
the one hardest causal or kinematic relationship and describe the smallest
exact geometry that can falsify it at the start of Make. Prefer a concept whose
signature magic survives with fewer independent parts, contacts, and coupled
motions. Complexity is justified only when removing it destroys the promised
experience; decorative detail, duplicated mechanisms, and extra simultaneous
motions are not depth. A concept that cannot name a cheap decisive proof is not
ready to seal—simplify it while preserving the anti-generic signature.
Also name the minimum held-view and signature-view blockout that would falsify
the intended form. It must prove volumetric identity and the view-specific
composition without labels, product copy, color, or decorative detail.

Codex owns the research strategy, concept generation, judging, and iteration.
Do not implement deep research, candidate fan-out, model judging, scoring,
reward, or repair loops in Python. Deterministic scripts may inspect facts or
artifacts but do not decide what to invent.

Do not claim geometry, safety, movement, fit, printability, or player response
that has not been checked. Make assumptions and unresolved risks explicit so
Make and Release can verify them.

## Artifact and gate

Write one authored JSON source with exactly `selected_inventor_id`, `ranking`,
`concept`, and `research`. `ranking` must cover every immutable roster Inventor
exactly once, place the selected Inventor first, and give a bounded rationale
for each position. The selected `concept` is Make's sealed design authority, so it must contain the
physical decisions needed to build without a separate design stage: object and
category, envelope and wall thickness, print stance, distinctive features,
each component's form, dimensions, placement, and interfaces, intended
interaction, assumptions, and unresolved risks. Bind researched claims to the
supporting entries in `research`; label deliberate design decisions as such.
If `STAGE.json.inputs.invent_concept_capability` is present, read its bound
`references/invent-concept-v1.md` and author its exact five-file pre-render
tree as part of this same Goal. The selected Inventor owns specialist design
content; the root Manager checks cross-file component and mechanism coherence
and remains responsible for the one finalizer call. Then run the packet-matched
form:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . invent --source <invent-source.json>
```

For a marked compound Invent, append:

```bash
  --concept-root <STAGE.json.inputs.concept_root>
```

The deterministic finalizer derives the exact roster-bound assignment, binds
the chosen concept and research to it, preserves the exact authored bytes as
the sibling `source.json`, and writes both canonical assignment and Invented
contracts plus `agent-outcome.json`; for a marked run it also derives v2
provenance, validates and preserves the exact pre-render tree, and lists the
complete authored set in that same outcome. It does not research, compose
instructions, render, access credentials, judge, assign a quality score, run
the improvement loop, or move a checkpoint. Complete the Invent Goal only
after this one command succeeds, then return to the host. The host independently
validates, renders through its authorized durable effect boundary, seals exact
bytes, and only then passes the Invent gate to Make.
