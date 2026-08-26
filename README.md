# Autonomous Workshop

You wish for a toy that doesn't exist. A few days later, it arrives at your door. 

Not from a shelf. From your imagination.

Welcome to Autonomous Workshop, where human and AI Inventors make toys the world has never seen.

[![A peek inside the Autonomous Workshop: how a Wish becomes a toy, from Match and Invent through Make, Playtest, Release, Deliver, and Reviews](docs/images/workshop-floorplan.svg?version=release-stage-v1)](docs/images/workshop-floorplan.svg)

## Meet some of the inventors

Here are five, one for each kind of toy. Many more are coming, and you can
[build your own](#build-your-own-inventor).

### Alice — reinvent the classics

Chess, go, dominoes, puzzles — games everyone already knows, made into a set
that is yours. Alice never touches the rules. She changes what the pieces are,
so the set is about you. It is judged as an object, not as a game.

![2030 San Francisco Chess Set](docs/images/alice-sf-chess.jpg)
*2030 San Francisco Chess Set*

### Leo — invent games that don't exist yet

Brand new games, invented for one wish: new rules, new pieces, a new reason to
sit at a table. Leo is the only inventor allowed to invent rules. Before
Release, his AI players must finish the required seeded games and expose
broken rules, loops, exploits, and weak strategies. Whether customers want to
play again is learned later from Reviews, after they receive the game.

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

Requires Python 3.11 or newer and an installed, signed-in Codex CLI. Workshop
uses the developer's existing Codex subscription; it does not require a second
model API key.

```bash
git clone https://github.com/autonomous-ai/autonomous-workshop.git
cd autonomous-workshop

uv run workshop doctor
uv run workshop wish \
  "I wish for a wind-up version of my dog that walks across my desk"
```

Every Wish starts one native Codex session in a private run workspace. The same
session Matches an Inventor, researches and Invents the concept, builds and
repairs the CAD, Playtests the exact product, then writes the Release package:

```text
Wish -> Match -> Invent -> Make <-> Playtest -> Release -> Deliver
```

Release is deliberately broader than “instructions.” It contains `MANUAL.md`,
canonical product facts, evidence-bound claims, page metadata, and the factual
input for Factory to create the customer-facing product page. The default is
private. Add `--publish` only when the verified page should be promoted to a
public Factory listing:

```bash
uv run workshop wish --publish \
  "I wish for a pocket-size moon-phase machine I can turn by hand"
```

Factory credentials remain in the host environment and are never passed into
Codex. Publication does not claim that a physical toy was printed, packed, or
delivered. Deliver waits until separately authorized production and shipment
receipts exist.

The command prints a Wish ID. Use that ID to inspect or continue the same
session after a process interruption:

```bash
uv run workshop status <wish-id>
uv run workshop resume <wish-id>
```

If a deterministic gate fails or a capability is missing, the run waits with a
concrete need. It never starts a replacement session or treats model prose as
proof.

## How the runtime is divided

Codex does nearly all product work: discovery, Match judgment, research,
concept exploration, design, CAD iteration, artifact inspection, AI Playtest,
repair, manual writing, and factual product-page content.

The root Codex session is the Workshop Manager. It can use Codex-native
subagents for bounded Match analysis, the selected Inventor specialist, and
independent inspection while remaining the one session the host starts and
resumes. Workshop does not launch a second Codex process or schedule those
agents in Python.

The Python host is intentionally narrow. It preserves identity and exact
bytes, enforces lifecycle order and round budgets, launches/resumes the native
session, validates contracts and deterministic evidence, isolates credentials,
and performs authorized external effects idempotently. It does not contain a
parallel Python agent, profile subprocess, prompt chain, semantic judge, or
reward loop.

See [Native coding-agent runtime](docs/NATIVE_AGENT_RUNTIME.md) for the full
boundary and [Workshop architecture](docs/ARCHITECTURE.md) for component
ownership.

## Build your own Inventor

An Inventor is a declared native specialist bundle. Every one has `TASTE.md`
for creative judgment plus a small `inventor.json` for identity, eligibility,
capabilities, and exact extension inventory. It may also own a `SKILL.md`,
within an inventor-prefixed Codex skill tree, with scripts, references, assets,
or tested deterministic CAD/domain tools. The root Manager dynamically briefs
a selected native subagent from the exact host-materialized bundle.

Inventor code supplies specialist operations, not orchestration: it cannot
launch agents, choose Workshop stages, pass gates, or perform authenticated
effects. Bundled Inventors use concise Codex skills; add scripts or other
custom logic only when the craft is genuinely specialist.

```bash
uv run workshop create inventor \
  --taste ./TASTE.md \
  --lane moving-machines
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

- [Alice](inventors/alice/TASTE.md) — personal heirloom editions of known games
- [Leo](inventors/leo/TASTE.md) — original games whose personalization changes play
- [Bob](inventors/bob/TASTE.md) — kinetic machines where the mechanism is the spectacle
- [Ivy](inventors/ivy/TASTE.md) — science and mathematics made physically legible
- [Eve](inventors/eve/TASTE.md) — real people, spaces, and objects made into little epics

Read [Build an Inventor](docs/BUILD_AN_INVENTOR.md) for the catalog contract.

## Code map

The installed distribution is `autonomous-workshop`. Python code imports the
`workshop` package, and the `workshop` command is implemented by the sibling
`src/cli/` package. The `src/` layout keeps repository-only files from being
imported accidentally.

Shared code is organized by architecture component under `src/workshop/`:
`product`, `wish`, `match`, `invent`, `make`, `playtest`, `release`,
`deliver`, `workflow`, `artifacts`, `runtime`, `integrations`, and
`contributors`. Make owns the single installed copy of its locked skills at
`src/workshop/make/skills/`; portable schemas live with the component that owns
their contract. Shared tests mirror those component names under `tests/`.
The trusted whole-run host is `src/workshop/workflow/native_run.py`; the
`src/cli/` package only parses commands, presents results, and chooses exit
codes.

Runtime also owns the non-Python product-run assets in `.agents/product-run/`
and `.agents/skills/autonomous-workshop/`. Packaging copies those exact bytes
into the installed distribution; they are the constitution and workflow skill
for a product run, not instructions for coding agents building this repository.

See [Workshop architecture](docs/ARCHITECTURE.md#shared-implementation) for the
ownership and dependency rules.

## Check it works

```bash
uv run workshop doctor
PYTHONPATH=src python -m unittest discover -s tests -t . -p 'test_*.py'
uv run workshop inventors --root inventors
uv run workshop check inventors
python .agents/skills/autonomous-workshop/scripts/stage_proposal.py --help
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
