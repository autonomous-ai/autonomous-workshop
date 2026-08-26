# Autonomous Workshop

You wish for a toy that doesn't exist. A few days later, it arrives at your door. 

Not from a shelf. From your imagination.

Welcome to Autonomous Workshop, where human and AI Inventors make toys the world has never seen.

[![A peek inside the Autonomous Workshop: a pluggable coding-agent runtime manages a Wish through Match, Invent, Make, Playtest, Release, Deliver, and Reviews](docs/images/workshop-floorplan.svg?version=agentic-runtime-toys-v3)](docs/images/workshop-floorplan.svg)

## Meet some of the inventors

Here are five distinct points of view. They are examples, not categories or
limits on what people can Wish for. Many more are coming, and you can
[build your own](#build-your-own-inventor).

### Alice — reinvent the classics

Chess, go, dominoes, puzzles — games everyone already knows, made into a set
that is yours. Alice never touches the rules. She changes what the pieces are,
so the set is about you. It is judged as an object, not as a game.

![2030 San Francisco Chess Set](docs/images/alice-sf-chess.jpg)
*2030 San Francisco Chess Set*

### Leo — invent games that don't exist yet

Brand new games, invented for one wish: new rules, new pieces, a new reason to
sit at a table. Leo is especially drawn to rules that reward discovery and
counterplay. Before Release, AI players must finish the required seeded games
and expose broken rules, loops, exploits, and weak strategies. Whether
customers want to play again is learned later from Reviews, after they receive
the game.

https://github.com/user-attachments/assets/36ffa63e-6e36-4422-8db7-bb1545b3bdb7

*[Blindcap: Duel](https://www.autonomous.ai/factory/product/blindcap-duel)
— a two-player hidden-information strategy game of mushrooms, probes, and crowns*

### Bob — invent machines that move

Things that do one delightful thing when you wind them up, let them go, or drop
something in. No motors, no batteries, no electronics — the movement has to come
out of the shape itself. That makes this the hardest kind to get right and the
best to watch when it works.

https://github.com/user-attachments/assets/ba57de75-37e2-45e8-a71f-2a339b0de49a

*[Trotter](https://www.autonomous.ai/factory/product/spot-quadruped-robot-wind-up-walker)
— a palm-size, rubber-band-powered quadruped*

### Ivy — invent science toys you can hold

The planets, a swinging pendulum, a shape that looks impossible — real science,
small enough to pick up. Ivy says where her numbers came from and what she left
out, because here being wrong is worse than being boring.

![A solar system with its orbits engraved](docs/images/ivy-solar-system.jpg)
*A solar system with its orbits engraved — $59.99*

### Eve — invent little worlds

Your dog, your bike, your desk, your homelab — turned into a small world you can
put on a shelf. Anyone can buy a generic model of anything. Eve's only counts if
it could not have existed before your wish.

![A 1:16 Formula 1 car](docs/images/eve-f1-car.jpg)
*A 1:16 Formula 1 car*

Several inventors can make the same kind of toy in their own way, and picking
one works the same whether there are five of them or a thousand.

## Quick start

Requires Python 3.11 or newer and a signed-in Codex CLI 0.145.0 or newer.
Workshop uses the developer's existing Codex subscription for all reasoning
and tool use.

```bash
git clone https://github.com/autonomous-ai/autonomous-workshop.git
cd autonomous-workshop

uv run workshop doctor
uv run workshop wish \
  "I wish for a wind-up version of my dog that walks across my desk"
```

Every Wish first creates one private persistent project under
`$WORKSHOP_HOME/runs/<wish-id>/workspace`, populates its product-run `AGENTS.md`,
skills, and Inventor roster, and then starts one native Codex session with that
project as its working directory. The same
session Matches an Inventor subagent, researches, explores, and selects the
exact product concept during Invent, builds and repairs the CAD from that
sealed Invent result, Playtests the exact product, then writes the Release
package:

```text
Wish -> Match -> Invent -> Make <-> Playtest -> Release -> Deliver
```

For each active Match, Invent, Make, Playtest, or Release attempt,
Codex creates one native Goal with one objective, proof artifacts, and a
verifiable stopping condition: the current stage finalizer succeeds. Only one
Goal is active at a time. While pursuing it, Codex observes the current artifact, acts with its
native tools and subagents, evaluates exact output, and improves it. This is
Codex's work loop inside the Goal, not a Python loop. The host checkpoint stays
the durable authority, and Wish and Deliver remain host boundaries. This uses
the official Codex patterns for [following a durable
Goal](https://learn.chatgpt.com/use-cases/follow-goals) and [iterating with
evals](https://learn.chatgpt.com/use-cases/iterate-on-difficult-problems).

The universal digital Playtest baseline is `agent-playtest`,
`mechanical-check`, and `printability-check`. These are Codex-authored
assessments unless the host replays deterministic evidence or a physical
receipt explicitly proves more. AI evidence never proves a successful print,
physical fit, durability, or human response.

Release is deliberately broader than “instructions.” Codex writes `MANUAL.md`
and canonical schema-v3 page-ready product data: evidence-bound hero,
cinematic, use-case, story-block, what-arrives, limitation, and claim content.
Factory transports those exact sealed page and model bytes; it does not own a
creative enrichment step. The default is private. Add `--publish` only when
the verified page should be promoted to a public Factory listing:

```bash
uv run workshop wish --publish \
  "I wish for a pocket-size moon-phase machine I can turn by hand"
```

Factory credentials live in the host-only
`$WORKSHOP_HOME/credentials/factory.env` file (0600 inside a 0700 directory),
or in a compatible host environment for ephemeral deployments. They are loaded
only outside a native agent turn and are never passed into Codex. Publication
does not claim that a physical toy was printed, packed, or delivered. Deliver
waits until separately authorized production and shipment receipts exist.

The command prints a Wish ID. Use that ID to inspect or continue the same
session after a process interruption:

```bash
uv run workshop status <wish-id>
uv run workshop resume <wish-id>
```

Once the exact Codex session is checkpointed, the same `wish` or `resume`
command automatically resumes it after a native-turn timeout or recognized
provider disconnect. Each continuation uses bounded jittered backoff and is
counted against the existing turn budget. Workshop first proves the previous
Codex process group is gone, so no member of that group can overlap the resumed
turn. Product-run tools are required to remain attached to that group; detached
or background tool daemons are unsupported. Unknown failures, unsafe
termination, and interruptions before a session identity is known still stop
without creating a replacement session.

If a deterministic gate fails or a required tool or authorization is missing,
the run waits with a concrete need. It never starts a replacement session or
treats model prose as proof.

## How the runtime is divided

The selected coding-agent runtime does nearly all product work: discovery,
Match judgment, research, concept exploration, design, CAD iteration, artifact
inspection, AI Playtest, repair, manual writing, and complete evidence-bound
product-page content. Manager runtime support is deliberately pluggable:

| Workshop Manager runtime | Status |
|---|---|
| Codex | Implemented |
| Claude Code | Planned adapter |
| Grok Build | Planned adapter |

Every adapter must preserve the same toy-project, stage-objective, checkpoint,
gate, and effect boundaries.

The root coding-agent session plays the **Workshop Manager** role. With today's
adapter, that is Codex using standard Codex-native subagents for bounded Match
analysis, the selected Inventor specialist, and independent inspection. An
Inventor is our friendly product-language name for one of those normal native
subagent roles, not a second agent framework. The root remains the one session
the host starts and resumes; Workshop does not schedule agents in Python.

The materialized `autonomous-workshop` skill is the Manager's workflow
playbook—stage order, artifact protocol, gates, and authority boundaries. It is
not a separate “Workshop Manager agent.”

The Python host is intentionally narrow. It preserves identity and exact
bytes, enforces lifecycle order and round budgets, launches/resumes the native
session under an exact-toy-root Codex permission profile, validates contracts
and deterministic evidence, isolates credentials,
and performs authorized external effects idempotently. It does not contain a
parallel Python agent, profile subprocess, prompt chain, semantic judge, or
reward loop.

See [Native coding-agent runtime](docs/NATIVE_AGENT_RUNTIME.md) for the full
boundary and [Workshop architecture](docs/ARCHITECTURE.md) for component
ownership.

## Build your own Inventor

An Inventor is a declared specialist bundle materialized as a standard Codex
project-scoped custom agent under `.codex/agents/`. Every one has `TASTE.md`
for creative judgment plus a small schema-v8 `inventor.json` for stable source
metadata and exact skill-tree hashes. Each Inventor owns one required primary
skill named `<id>-inventor`; it may declare additional Inventor-prefixed skills
with scripts, references, assets, or tested deterministic CAD/domain tools.
For a run, `.codex/agents/*.toml` is the sole Inventor identity, Taste, and
skill roster. The root Manager asks Codex to spawn the selected custom agent
from those exact host-materialized bytes.

This follows Codex's official [subagent and project-scoped custom-agent
convention](https://learn.chatgpt.com/docs/agent-configuration/subagents); the
Workshop adds the Inventor name, Taste, product craft, and lifecycle boundary.

Inventor code supplies specialist operations, not orchestration: it cannot
launch agents, choose Workshop stages, pass gates, or perform authenticated
effects. Bundled Inventors use concise Codex skills; add scripts or other
custom logic only when the craft is genuinely specialist.

```bash
uv run workshop create inventor \
  --taste ./TASTE.md
```

A useful `TASTE.md` has a name, a discriminating one-line description, and a
recognizable point of view:

```markdown
---
name: Ada
description: Choose Ada for hand-cranked creatures; not static models or games.
---

# Ada's taste

I love mechanisms whose motion tells the story. I reject decoration without play.
```

- [ABO](inventors/abo/TASTE.md) — original abstract strategy games, judged on rules and structure, not theme
- [Alice](inventors/alice/TASTE.md) — personal heirloom editions of known games
- [Leo](inventors/leo/TASTE.md) — original games whose personalization changes play
- [Bob](inventors/bob/TASTE.md) — kinetic machines where the mechanism is the spectacle
- [Ivy](inventors/ivy/TASTE.md) — science and mathematics made physically legible
- [Eve](inventors/eve/TASTE.md) — real people, spaces, and objects made into little epics

Read [Build an Inventor](docs/BUILD_AN_INVENTOR.md) for the specialist contract.

## Repository structure

The installed distribution is `autonomous-workshop`. Python code imports the
`workshop` package, and the `workshop` command is implemented by the sibling
`src/cli/` package. The `src/` layout keeps repository-only files from being
imported accidentally.

- [`toys/`](toys/) contains only sanitized released examples under
  `<inventor>-<product-slug>/`. Private runtime projects are outside Git at
  `$WORKSHOP_HOME/runs/<wish-id>/workspace` and contain the product-run
  `AGENTS.md`, custom Inventors, skills, exact roster, and Wish-to-Release
  artifacts.
- [`.agents/product-run/`](.agents/product-run/) is the complete isolated
  template copied into every new toy project before the runtime starts.
- [`inventors/`](inventors/) contains reusable Inventor sources: manifest,
  Taste, required primary skill, and any additional specialist skills or tools.
- [`src/cli/`](src/cli/) owns command parsing, presentation, and exit codes.
- [`src/workshop/`](src/workshop/) is the narrow trusted host, organized by
  Wish, Match, Invent, Make, Playtest, Release, Deliver, workflow,
  runtime, contracts, gates, and integrations.
- [`src/workshop/make/skills/`](src/workshop/make/skills/) holds the canonical
  shared CAD and making skills.
- [`tests/`](tests/) mirrors the component ownership and contains the full
  deterministic and installed-package acceptance suite.
- [`docs/`](docs/) contains the architecture, runtime protocol, evidence, and
  contributor guides, including the [product verification
  levels](docs/PRODUCT_VERIFICATION.md).

Trusted checkpoints, receipts, credentials, and effect state live outside the
coding-agent working directory under `$WORKSHOP_HOME/state/<wish-id>/`. The
private project remains useful and inspectable without exposing host authority.
Only the host's optional sanitized post-publication projection belongs in the
repository `toys/` directory.

Shared code is organized by architecture component under `src/workshop/`:
`product`, `wish`, `match`, `invent`, `make`, `playtest`, `release`, `deliver`,
`workflow`, `artifacts`, `runtime`, `integrations`, and
`contributors`. Make owns the single installed copy of its locked skills at
`src/workshop/make/skills/`; portable schemas live with the component that owns
their contract. Shared tests mirror those component names under `tests/`.
The trusted whole-run host is `src/workshop/workflow/native_run.py`; the
`src/cli/` package only parses commands, presents results, and chooses exit
codes.

Runtime also owns the complete non-Python product-run template in
`.agents/product-run/`, including its nested workflow skill. Packaging copies
those exact bytes into the installed distribution. Nesting the skill inside the
template keeps it invisible to coding agents building this repository; it is
discovered only after the template is materialized as a toy-project root.

See [Workshop architecture](docs/ARCHITECTURE.md#shared-implementation) for the
ownership and dependency rules.

## Check it works

```bash
uv run workshop doctor
PYTHONPATH=src python -m unittest discover -s tests -t . -p 'test_*.py'
uv run workshop inventors --root inventors
uv run workshop check inventors
python .agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py --help
python tools/verify_skill_locks.py
python tools/scan_secrets.py
git diff --check
```

Read next:

- [Native coding-agent runtime](docs/NATIVE_AGENT_RUNTIME.md)
- [Workshop architecture](docs/ARCHITECTURE.md)
- [Build an inventor](docs/BUILD_AN_INVENTOR.md)
- [Playtest evidence](docs/PLAYTEST_EVIDENCE.md)
- [Publication boundary](docs/PUBLISH_SEALED_PRODUCT.md)
- [Contributing](CONTRIBUTING.md)

Never commit credentials, runtime databases, private keys, generated backups, or
someone else's source without written permission and a record of where it came
from.
