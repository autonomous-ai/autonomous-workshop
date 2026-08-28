# Invent contract

Read `STAGE.json`. It binds the exact Wish, immutable Inventor roster,
universal blueprint, canonical assignment and Invented output paths, frozen
effort, and current checkpoint. Verify those bytes before acting. The blueprint
is an open-ended shared contract, not a product classification.

## Invent Goal and improvement loop

Create one native Codex Goal for this Invent attempt. Its objective is to
select the best-fit immutable Inventor, research, explore, judge, and fully
specify the strongest feasible concept for the Wish through that Inventor's
exact Taste and method.
Its stopping condition is a successful `invent` finalizer for the current
checkpoint.

Compare every roster entry before selecting. Use the selected project-scoped
custom agent for specialist work. The root Workshop Manager reviews and
synthesizes its output and remains responsible for the one stage proposal.

While pursuing the Goal:

1. **Observe:** Read the Wish, complete roster and custom-agent instructions,
   relevant skill resources, and any exact upstream evidence. Identify what
   needs factual research and what needs creative exploration. When
   `STAGE.json` names a `design_vault`, brief yourself on candidate
   mechanisms with `vault_tools.py guidance` before committing to one: each
   recorded risk carries the fix that worked.
2. **Act:** Use Codex-native search, browsing, file tools, and specialist
   subagents to research supported facts and explore materially different
   concepts. Save source provenance beside the claims it supports. Use the
   Inventor's declared skills and deterministic craft tools when relevant.
   Before selecting, specify each viable direction deeply enough to compare
   form, envelope, component breakdown, construction, interaction,
   feasibility, assumptions, and risks.
3. **Evaluate:** Compare concepts against the Wish, full Taste, novelty,
   coherent play, mechanical feasibility, printability, and inspectability.
   Ask independent native subagents to judge bounded questions when subjective
   tradeoffs matter; synthesize their evidence rather than averaging votes.
4. **Improve:** Address the largest weakness, challenge unsupported
   assumptions, and refine or replace the concept. Repeat research or review
   only when it can resolve a concrete gap.

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

The finalizer seals the concept as Invented schema 5 and enforces this
contract deterministically. Required `concept` fields (extra fields such as
`signature_decision`, `print_stance`, `assumptions`, or `risks` are allowed):

- `title`, `summary`: bounded text.
- `interaction`: what the owner physically does with the product; every
  component must either mate with another component or be named here.
- `envelope_mm`: `{length_mm, width_mm, height_mm}`, finite, within
  `(0, 2000]`.
- `mechanisms`: at most 16 unique slugs (`^[a-z][a-z0-9_-]{0,62}$`); may be
  empty for a purely static object. Each slug must resolve to a design-vault
  node (`vault_tools.py resolve <name>`, see the `design-vault` skill) or be
  declared under the optional `novel_mechanisms` list as
  `{"id": <slug>, "definition": <20 to 2000 characters>}`.
- `components`: 1 to 64 entries with exactly `key`, `name`, `form`, `duty`,
  `dimensions_mm`, `placement`, `interfaces`, `mates_with`, `signature`.
- `build_plan`: 1 to 16 groups, each exactly `{"group": <slug>, "parts":
  [component keys], "exit_criteria": <text>}`, in build order. Every
  component appears in exactly one group; put parts that must be measured
  against each other in the same group. Make seals one group at a time and
  stops at the first group it cannot seal.

The finalizer rejects, naming the rule in parentheses:

- **unbound** — `form`, `duty`, `placement`, or `interfaces` hedges a quantity
  (`roughly 20 mm`, `~4 mm`, `several`, `a few`, `enough`, `as needed`).
  State the number.
- **envelope** — a component's sorted dimensions exceed the sorted envelope.
- **component-orphan** — `mates_with` names an unknown component, the
  component itself, or the same mate twice.
- **signature** — not exactly one component carries `"signature": true`; the
  box is remembered by one object.
- **decoration** — a component with no mate in either direction whose key or
  name never appears in `interaction`. Give it a role or remove it.
- **mechanism-unknown** — a mechanism that is neither a vault node nor a
  declared novel mechanism; **mechanism-not-novel** — a `novel_mechanisms`
  entry that resolves to an existing node.
- **build-plan** — a group names an unknown component, a component sits in
  two groups or in none, a group is empty, or a group name repeats.
- **vault-conflict** / **vault-requirement** — the resolved mechanisms plus
  every `constraints/*` node declare `conflicts-with`, or leave a `requires`
  unmet. Run `vault_tools.py check <nodes> --with-constraints` before
  finalizing. Risks reported there are not refusals; the host turns them into
  `vault_leads` for Make and Playtest.

Then run:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . invent --source <invent-source.json>
```

The deterministic finalizer derives the exact roster-bound assignment, binds
the chosen concept and research to it, preserves the exact authored bytes as
the sibling `source.json`, and writes both canonical assignment and Invented contracts plus
`agent-outcome.json`. It does not research, judge, assign a quality score, or
run the improvement loop. Complete the Invent Goal only after the command
succeeds, then return to the host. The host validates and seals the exact
Invent contract before checkpointing Make.
