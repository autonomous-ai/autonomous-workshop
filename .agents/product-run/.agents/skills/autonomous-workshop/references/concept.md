# Concept contract

Read `STAGE.json`. It binds the exact Wish, Match assignment, selected
Taste, universal blueprint, and sealed Invent result. On a round that revises
a standing design it also carries that standing concept and the Playtest
feedback that invalidated it. Verify those bytes before acting.

Concept turns an invented idea into one decided, visualized design before any
geometry exists. You research the Wish, decide its physical facts, and author
one drawing instruction per required image role. First you finalize those
pre-render instructions and return control. Only then does the host draw the
images and seal the whole tree; it composes, scores, or chooses nothing itself.

## Concept Goal

Create one native Codex Goal for this Concept attempt. Its objective is to
research the Wish through your own search and browsing, decide the design's
physical facts, and author a complete brief, research record, and drawing
instructions. Its stopping condition is a successful `concept` finalizer for
the current checkpoint.

While pursuing the Goal:

1. **Research first.** Research the Wish before locking any physical fact.
   Do not settle an envelope, wall thickness, feature, print stance, fit
   target, or component before that research is done. On a refining round,
   reuse the standing concept's research rather than researching the Wish
   again.
2. **Decide, don't default.** Every fact the brief states — the object, its
   category, its envelope in millimetres, its wall thickness, its print
   stance, each distinctive feature, and each component's form, dimensions,
   placement, and interfaces — must trace to either a source your research
   recorded or a decision you made and recorded with its reason in the
   brief's assumptions. A fixed default standing in for a fact you never
   decided satisfies nothing. A feature that only restates the Wish's own
   objective decides nothing either.
3. **Break the object into its real parts.** The component breakdown is the
   parts the researched object actually has. A single component is
   legitimate only when your research concluded the design genuinely prints
   as one part, and you record that conclusion. Specify every component in
   its own right, including one hidden behind another in every view — text
   does not occlude, and a component's image is drawn from its own
   specification alone, never read off another image.
4. **Author one drawing instruction per role.** Roles are `front`, `top`,
   `bottom`, `exploded`, and one per component. `front` carries no reference;
   `top` and `bottom` reference `front` and ask for the same object unchanged
   from a different angle; `exploded` references `front`, `top`, and
   `bottom` and must separate every component, each wholly visible, none
   hidden; each component's instruction references `front` for material,
   finish, and form language only — never for shape, and never `exploded`.
   Every instruction carries the brief's physical facts as constraints. Ask
   for a neutral flat design-study presentation: no dramatic lighting, staged
   scene, reflections, background props, text, dimensions, logos,
   watermarks, people, or hands.
5. **Write back the researched constraints.** Author a derived-Wish record
   inside the concept tree carrying the routed Wish's own product identifier,
   objective, and context, together with the researched constraints. Never
   change the routed Wish's own words.

On a round that carries a standing concept and feedback that invalidated the
design, revise rather than restart: preserve every feature the feedback did
not challenge, and address only what it named. Do not accumulate open-ended
refinement past the host's stated allowance — re-anchor on the design's
locked facts instead of drifting further.

You cannot reach an image provider yourself; the sandbox has no network. The
host cannot start drawing until after you successfully run the `concept`
finalizer and return control. Missing rendered images before finalization is
the expected state, not a need or blocker. Do not wait for image paths in
`descriptor.json` to exist and do not mark the Goal blocked because they are
absent. After the finalizer succeeds, the host draws every image between turns
from your instructions verbatim and only after its structural checks pass.
Where the image provider is not configured, the host then parks the run waiting
on that capability — this is not a failure to route around; your accepted brief
and research survive the wait and the host resumes the same design once it is
configured.

Do not implement research, prompt composition, image generation, or judging
in Python. A deterministic script may validate structure; it does not decide
what the design is.

## Artifact and gate

Write the concept tree at the exact `concept_root` in `STAGE.json`:
`brief.json`, `research.json`, `prompts.json` (the drawing instructions,
keyed by role, `front`/`top`/`bottom`/`exploded`/`components.<key>`),
`descriptor.json` (each image's path, mirroring the same role keys), and
`derived_wish.json`. Each descriptor leaf is exactly `{"path":"..."}`; do not
add an image hash because no image exists yet. Do not write image files
yourself — the host draws them
into the tree from the finalized instructions. At this point the image paths
declared in `descriptor.json` are expected not to exist. Run the finalizer now,
before any rendered image exists:

```bash
python .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . concept --concept-root <STAGE concept_root>
```

The deterministic finalizer validates and hashes the five authored pre-render
JSON documents and writes the canonical pre-render proposal, `concept.json`,
plus `agent-outcome.json`. This proposal is not the rendered, sealed Concept
that Make consumes. It neither reads nor expects rendered image files. The
finalizer must succeed before the host calls the image provider. Complete the
Concept Goal only after it succeeds, then return to the host. The host
re-checks every structural rule, draws the images, and only then writes the
host-owned `sealed-concept.json` whose `concept_sha256` covers the brief, the
research, the drawing instructions, and every image together. Make consumes
that sealed contract and cannot proceed without it.
