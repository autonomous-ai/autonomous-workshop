# Autonomous Workshop

You wish for a toy that doesn't exist. A few days later, it arrives at your door. 

Not from a shelf. From your imagination.

Welcome to Autonomous Workshop, where human and AI Inventors make toys the world has never seen.

[![A peek inside the Autonomous Workshop: a pluggable coding-agent runtime manages a Wish through Match, Invent, Make, Playtest, Release, Deliver, and Reviews](docs/images/workshop-floorplan.svg?version=agentic-runtime-toys-v2)](docs/images/workshop-floorplan.svg)

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

Requires Python 3.11 or newer and one supported Manager runtime:

- a signed-in Codex CLI 0.145.0 or newer; or
- Claude Code 2.1.246 or newer with `ANTHROPIC_API_KEY` available in the host
  environment.

Codex can use the developer's existing Codex subscription. Claude runs in an
isolated non-bare profile with empty filesystem setting sources and private
`0700` home, configuration, and internal-temp directories. Workshop selects
API-key authentication rather than `claude auth login` or the normal
keychain/OAuth path, and it does not admit `ANTHROPIC_AUTH_TOKEN` or
`CLAUDE_CODE_OAUTH_TOKEN` to the bounded process environment. Init must report
`ANTHROPIC_API_KEY` as its source. Codex is the default, so existing commands
keep their behavior.

The Claude adapter, CLI selector, projection, isolation policy, and resume
binding are implemented and covered by deterministic tests. A real private
Claude Wish has not yet completed the repository's live acceptance bar, so
treat Claude support as pre-live-validation and start with an unpublished
private Wish.

Claude's OS-, MDM-, or server-managed policy remains part of the trusted host
boundary. Managed settings, instructions, plugins, hooks, and administrator
policy can still apply. Claude's native `/goal` command requires its hook
machinery, so Workshop cannot set `disableAllHooks`; empty filesystem setting
sources exclude ordinary user/project hooks, while managed hooks remain in the
host trust boundary. They run with the host user's authority and, with Claude's
subprocess scrub disabled for `/goal` compatibility, may inspect the API key or
other host-readable files. Workshop does not protect a run from a malicious or
compromised host administrator. Claude session transcripts are plaintext and
retained in the private Workshop state directory long enough to preserve
`--resume`; its `0700` filesystem permissions are the at-rest boundary.

```bash
git clone https://github.com/autonomous-ai/autonomous-workshop.git
cd autonomous-workshop

uv run workshop doctor
uv run workshop wish \
  "I wish for a wind-up version of my dog that walks across my desk"
```

Set `ANTHROPIC_API_KEY` in the host environment, then select Claude Code
explicitly for both its prerequisite check and a new Wish:

```bash
uv run workshop doctor --manager claude
uv run workshop wish --manager claude \
  "I wish for a wind-up version of my dog that walks across my desk"
```

Every Wish first creates one persistent toy project under `toys/`, populates
its Manager-neutral product-run constitution, skills, exact Inventor roster,
and immutable `MANAGER.json`, and then starts one native session in the
selected runtime with that project as its working directory. The same session
Matches an Inventor subagent, researches and Invents the concept, builds and
repairs the CAD, Playtests the exact product, then writes the Release package:

```text
Wish -> Match -> Invent -> Make <-> Playtest -> Release -> Deliver
```

For each active Match, Invent, Make, Playtest, or Release attempt, the selected
Manager creates one native Goal with one objective, proof artifacts, and a
verifiable stopping condition: the current stage finalizer succeeds. Only one
Goal is active at a time. While pursuing it, the Manager observes the current
artifact, acts with its native tools and subagents, evaluates exact output, and
improves it. This is native coding-agent work inside the Goal, not a Python
loop. The host checkpoint stays the durable authority, and Wish and Deliver
remain host boundaries.

For Claude, each new attempt sends the exact text `/goal <condition>` over
standard input to `claude -p --input-format text` under that isolated profile.
If the process is
interrupted, resume sends fixed continuation prose so Claude keeps the restored
active Goal instead of replacing it with another `/goal`. A private Goal
sidecar records `prepared`, `active`, `returned`, and `completed`, binds that
choice to the stage and host checkpoint, and marks completion only after the
host validates the proposal.

The universal digital Playtest baseline is `agent-playtest`,
`mechanical-check`, and `printability-check`. These are Manager-authored
assessments unless the host replays deterministic evidence or a physical
receipt explicitly proves more. AI evidence never proves a successful print,
physical fit, durability, or human response.

Release is deliberately broader than “instructions.” The Manager writes
`MANUAL.md` and canonical schema-v3 page-ready product data: evidence-bound hero,
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
only outside a native agent turn. Workshop does not add them to the selected
Manager environment, prompt, or sandbox-readable filesystem; trusted managed
hooks and host administrators are outside that guarantee. Publication does not
claim that a physical toy was printed, packed, or delivered. Deliver waits
until separately authorized production and shipment receipts exist.

The command prints a Wish ID. Use that ID to inspect or continue the same
session after a process interruption:

```bash
uv run workshop status <wish-id>
uv run workshop resume <wish-id>
```

The Manager is selected once, persisted in the run checkpoint, and reported by
`status`. `resume` deliberately has no Manager selector: it resumes the exact
Codex or Claude Code session that created the run and fails closed if its
hash-bound runtime policy or materialized instructions changed.

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
| Claude Code | Adapter, CLI, and projection implemented; live private-Wish acceptance pending |
| Grok Build | Planned adapter |

Every adapter must preserve the same toy-project, stage-objective, checkpoint,
gate, and effect boundaries.

The root coding-agent session plays the **Workshop Manager** role. Codex uses
project-scoped custom agents and Claude Code receives agents and skills from its
host-generated project plugin. Both adapters expose bounded Match analysis, the
selected Inventor specialist, and independent inspection through their native
agent controls. A real Claude turn invoking a projected Inventor agent and a
projected namespaced skill is still part of the pending live acceptance bar; a
successful init event alone is not that proof. An Inventor is our friendly
product-language name for one of those normal native specialist roles, not a
second agent framework. The root remains the one session the host starts and
resumes; Workshop does not schedule agents in Python.

The materialized `autonomous-workshop` skill is the Manager's workflow
playbook—stage order, artifact protocol, gates, and authority boundaries. It is
not a separate “Workshop Manager agent.”

The Python host is intentionally narrow. It preserves identity and exact
bytes, enforces lifecycle order and round budgets, launches/resumes the native
session under an exact-toy-root, fail-closed policy owned by the selected
runtime adapter, validates contracts and deterministic evidence, isolates
credentials, and performs authorized external effects idempotently. It does
not contain a parallel Python agent, profile subprocess, prompt chain,
semantic judge, or reward loop.

See [Native coding-agent runtime](docs/NATIVE_AGENT_RUNTIME.md) for the full
boundary and [Workshop architecture](docs/ARCHITECTURE.md) for component
ownership.

## Build your own Inventor

An Inventor is one canonical specialist source bundle. Every one has
`TASTE.md` for creative judgment plus a small schema-v8 `inventor.json` for
stable source metadata and exact skill-tree hashes. Each Inventor owns one
required primary skill named `<id>-inventor`; it may declare additional
Inventor-prefixed skills with scripts, references, assets, or tested
deterministic CAD/domain tools.

At Wish creation the host deterministically projects that same source into the
selected runtime's native convention: `.codex/agents/<id>.toml` with skills
under `.agents/skills/` for Codex, or the generated Claude Code plugin's
`.claude/agents/<id>.md` with skills under `.claude/skills/`. `MANAGER.json`
identifies the one projection that is authoritative for the run. The root
Manager spawns the selected native agent from those exact, hash-bound bytes.
For Codex, this follows the official [subagent and project-scoped custom-agent
convention](https://learn.chatgpt.com/docs/agent-configuration/subagents).

Inventor code supplies specialist operations, not orchestration: it cannot
launch agents, choose Workshop stages, pass gates, or perform authenticated
effects. Bundled Inventors use concise portable skill sources; add scripts or
other custom logic only when the craft is genuinely specialist.

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

- [Alice](inventors/alice/TASTE.md) — personal heirloom editions of known games
- [Leo](inventors/leo/TASTE.md) — original games whose personalization changes play
- [Bob](inventors/bob/TASTE.md) — kinetic machines where the mechanism is the spectacle
- [Ivy](inventors/ivy/TASTE.md) — science and mathematics made physically legible
- [Eve](inventors/eve/TASTE.md) — real people, spaces, and objects made into little epics

Read [Build an Inventor](docs/BUILD_AN_INVENTOR.md) for the specialist contract.

## Asset evolution

Today, the canonical source of truth is the root Inventor bundle—its
`inventor.json`, `TASTE.md`, and declared `skills/**`—together with the
canonical product-run and Make skill sources. The `.codex/**` or `.claude/**`
trees and `MANAGER.json` inside a toy project are generated projection files,
not independent copies to edit. A new Wish uses the latest validated canonical
bytes available from the current checkout or installed Workshop package.

An active run behaves differently by design today: all of its instructions,
Taste, skills, native-agent definitions, and Manager selection are hash-pinned
when the run is created. Resume uses those materialized bytes and fails closed
if they change. Updating a root Inventor or skill therefore improves future
Wishes now; it does not yet refresh an established run or rewrite released
artifacts, evidence, receipts, or publication history.

A controlled upgrade path for active runs is **target work, not implemented
behavior**. The intended default is `follow-stable`: at each safe host
checkpoint, resolve the latest validated asset release, seal the prior
projection, record old and new hashes, and start a new Manager session epoch.
Projects may explicitly pin a release for reproduction. A compatible skill or
tool refresh retains the Inventor identity and Taste while invalidating and
rechecking affected downstream work. A Taste or Inventor-identity change
forces Match/Invent reassessment; a Manager change is an explicit handoff.
Released history remains bound to its original bytes, while continued work
becomes a new product revision. Workshop will never hot-swap unvalidated files
during a native turn or silently rewrite released evidence and receipts.

Here, “latest validated stable” means a promoted, content-addressed asset
release—not raw Git `HEAD`. Self-improvements first become candidates, then
must pass deterministic schema, exact skill-lock, Manager-compatibility, and
regression checks before atomic promotion. `follow-stable` resolves only that
promoted channel, never an unreviewed self-edit or branch tip.

## Repository structure

The installed distribution is `autonomous-workshop`. Python code imports the
`workshop` package, and the `workshop` command is implemented by the sibling
`src/cli/` package. The `src/` layout keeps repository-only files from being
imported accidentally.

- [`toys/`](toys/) contains the persistent toy projects and is the working
  directory for each native runtime session. Every toy project contains its
  product-run `AGENTS.md`, immutable `MANAGER.json`, the selected Codex or
  Claude Code projection, its exact Inventor roster, and its Wish-to-Release
  artifacts.
- [`.agents/product-run/`](.agents/product-run/) is the canonical
  Manager-neutral product-run source bundle. The host copies its constitution
  to the toy root and projects its workflow skill into the selected runtime's
  native skill directory before that runtime starts.
- [`inventors/`](inventors/) contains reusable Inventor sources: manifest,
  Taste, required primary skill, and any additional specialist skills or tools.
- [`src/cli/`](src/cli/) owns command parsing, presentation, and exit codes.
- [`src/workshop/`](src/workshop/) is the narrow trusted host, organized by
  Wish, Match, Invent, Make, Playtest, Release, Deliver, workflow, runtime,
  contracts, gates, and integrations.
- [`src/workshop/make/skills/`](src/workshop/make/skills/) holds the canonical
  shared CAD and making skills.
- [`tests/`](tests/) mirrors the component ownership and contains the full
  deterministic and installed-package acceptance suite.
- [`docs/`](docs/) contains the architecture, runtime protocol, evidence, and
  contributor guides.

Trusted checkpoints, receipts, credentials, and effect state live outside the
coding-agent working directory under `$WORKSHOP_HOME/state/<toy-id>/`. A toy
project remains useful and inspectable without exposing host authority. New
runtime-created toy projects are ignored by Git by default; only explicitly
reviewed showcase or historical projects should be allowlisted for a commit.

Shared code is organized by architecture component under `src/workshop/`:
`product`, `wish`, `match`, `invent`, `make`, `playtest`, `release`,
`deliver`, `workflow`, `artifacts`, `runtime`, `integrations`, and
`contributors`. Make owns the single installed copy of its locked skills at
`src/workshop/make/skills/`; portable schemas live with the component that owns
their contract. Shared tests mirror those component names under `tests/`.
The trusted whole-run host is `src/workshop/workflow/native_run.py`; the
`src/cli/` package only parses commands, presents results, and chooses exit
codes.

Runtime also owns the canonical non-Python product-run source bundle in
`.agents/product-run/`, including its nested workflow skill. Packaging copies
those exact source bytes into the installed distribution. Nesting the skill
inside that source bundle keeps it invisible to coding agents building this
repository; the host exposes it only after projecting it into the selected
Manager's skill directory in an isolated toy-project root.

See [Workshop architecture](docs/ARCHITECTURE.md#shared-implementation) for the
ownership and dependency rules.

## Check it works

```bash
uv run workshop doctor
uv run workshop doctor --manager claude  # when using Claude Code
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
