# Autonomous Workshop

You wish for a toy that doesn't exist. A few days later, it arrives at your door.

Not from a shelf. From your imagination.

Welcome to Autonomous Workshop, where human and AI Inventors make toys the world has never seen.

[![A peek inside the Autonomous Workshop: a pluggable coding-agent runtime follows a selectable Spark, Forge, or Quest route before handing the released toy to Operations](docs/images/workshop-floorplan.svg?version=effort-routes-v1)](docs/images/workshop-floorplan.svg)

Workshop's executable workflow ends at a public Release: exact ready-to-print
CAD plus the in-box `MANUAL.pdf`. From there, Operations prints, packs,
delivers, and learns from customer Reviews—which can inspire the next Wish.

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
counterplay. Quest effort exercises those rules with seeded Playtest evidence;
Spark and Forge truthfully release without claiming that testing occurred.
Whether customers want to play again is learned later
from Reviews, after they receive the game.

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

Requires Python 3.11 or newer, `uv`, and a signed-in Manager CLI. Codex CLI
0.145.0 or newer is the default production path. Grok Build CLI `grok` 1.0.5
or newer is the experimental `--manager grok` path. Workshop uses one signed-in
session of the selected Manager for all reasoning and tool use.

### 1. Sign in to Codex

Install or update the [Codex CLI](https://learn.chatgpt.com/docs/codex/cli),
then sign in with ChatGPT and confirm the active authentication method:

```bash
codex login
codex login status
```

`codex login` opens the browser sign-in flow. See the official
[Codex authentication guide](https://learn.chatgpt.com/docs/auth) for API-key,
managed-workspace, and headless-device options.

### 2. Start a Workshop

```bash
git clone https://github.com/autonomous-ai/autonomous-workshop.git
cd autonomous-workshop

uv run workshop doctor
uv run workshop wish \
  --effort forge \
  "I wish for a wind-up version of my dog that walks across my desk"
```

`workshop doctor` checks the Inventor catalog, Codex version and sign-in,
packaged agent assets, and host-only Factory credential configuration without
printing secrets. Fix any reported need before expecting a run to complete.
Factory credentials belong to one Workshop-owned service account, not to the
person making a Wish or the Inventor selected during the first creative stage. They are required
only by the host when Release publishes the final CAD and manual; see the
[credential setup](docs/PUBLISH_SEALED_PRODUCT.md#credentials).

Starting `workshop wish` authorizes required public Factory publication of that
run's exact Release; there is no separate `--publish` mode. If credentials are
missing or publication cannot be reconciled, Release waits safely for
`workshop resume` instead of claiming completion.

Every Wish first creates one private persistent project under
`$WORKSHOP_HOME/runs/<wish-id>/workspace`, populates its product-run `AGENTS.md`,
skills, and Inventor roster, and then starts one native coding-agent session with that
project as its working directory. The default Manager is Codex; pass
`--manager claude` or `--manager grok` only to use an experimental adapter.
Choose how much creative depth the run gets:

```text
Spark: Wish -> Make -> Release                 (default)
Forge: Wish -> Invent -> Make -> Release
Quest: Wish -> Invent -> Make -> Playtest -> Release

Release -- handoff to Operations --> Printing -> Deliver -> Review
```

Pass `--effort spark`, `--effort forge`, or `--effort quest`. Omit `--manager`
to keep Codex. Inventor
selection is folded into the first active creative stage, so there is no
separate Match turn. Disabled stages pass through without a native turn,
artifact, gate, or fabricated evidence.

Each effort has its own exact route diagram.

#### Spark (default)

[![Spark: Wish, Make, Release, then Operations](docs/images/effort-spark.svg)](docs/images/effort-spark.svg)

#### Forge

[![Forge: Wish, Invent, Make, Release, then Operations](docs/images/effort-forge.svg)](docs/images/effort-forge.svg)

#### Quest

[![Quest: Wish, Invent, Make, Playtest, Release, then Operations](docs/images/effort-quest.svg)](docs/images/effort-quest.svg)

Workshop code ends after it verifies and publishes Release. Printing, physical
delivery, and customer Review remain part of the complete toy journey, handled
by the Operations team.

Release delivers three facts about the same exact bytes:

- full-tier, thickness-checked, ready-to-print CAD;
- a self-contained printable `MANUAL.pdf` for the box; and
- authenticated public Factory readback proving those CAD and manual hashes.

For each active Invent, Make, Playtest, or Release attempt,
Codex creates one native Goal with one objective, proof artifacts, and a
verifiable stopping condition: the current stage finalizer succeeds. Only one
Goal is active at a time. While pursuing it, Codex observes the current artifact, acts with its
native tools and subagents, evaluates exact output, and improves it. This is
Codex's work loop inside the Goal, not a Python loop. The host checkpoint stays
the durable authority, and Wish remains a host boundary. This uses
the official Codex patterns for [following a durable
Goal](https://learn.chatgpt.com/use-cases/follow-goals) and [iterating with
evals](https://learn.chatgpt.com/use-cases/iterate-on-difficult-problems).

Spark and Forge omit Playtest truthfully: Release records
`playtest_status: not-run` and carries no Playtest claims. Quest requires a
passing Playtest bound to the current Made revision. The host still
replays the deterministic full-tier CAD verifier during Make and again during
Release, but that digital verification never proves a successful physical
print, fit, durability, or human response.

Release centers the moment the owner opens the box. Codex designs a
self-contained printable `MANUAL.pdf`, renders and inspects every page, and
seals it with exact product facts and either the explicit Playtest omission or
Quest's bounded passing evidence. The manual must teach
the product without a website, video, QR code, or phone. The host then
revalidates full-tier, thickness-checked, print-ready CAD and publishes the
exact CAD package and manual through Factory. Public hash readback is part of
Release success; missing credentials or an unavailable site leaves the same
Release waiting for `workshop resume`.

Factory credentials live in the host-only
`$WORKSHOP_HOME/credentials/factory.env` file (0600 inside a 0700 directory),
or in a compatible host environment for ephemeral deployments. The deployment
configures one `FACTORY_USERNAME` / `FACTORY_PASSWORD` service-account pair;
Wish users never enter Factory credentials. They are loaded only outside a
native agent turn and are never passed into Codex. Publication does not claim
that a physical toy or its manual was printed, packed, or delivered. Printing,
delivery, and review belong to the Operations workflow after Workshop Release.

The command prints a Wish ID. Use that ID to inspect or continue the same
session after a process interruption:

```bash
uv run workshop status <wish-id>
uv run workshop resume <wish-id>
```

### Reproduce the Grok Spark example

[Horn Tip](https://www.autonomous.ai/factory/product/horn-tip) is a Pico Press
one-piece crescent desk rocker. It was created on Spark
(`Wish -> Make -> Release`) by the experimental Grok Build Manager. The
sanitized snapshot is
[`toys/pico-press-horn-tip/`](toys/pico-press-horn-tip/).

The native CLI is Grok Build TUI `grok` 1.0.5 or newer. The live run used
`grok 1.0.5 (5115b46bc909)` and model `grok-4.6`. Sign in, then:

```bash
grok login
grok --version

uv run workshop doctor
uv run workshop wish --manager grok --effort spark \
  "I wish for a tiny one-piece crescent desk rocker that tips with a fingertip"
```

`--effort spark` is already the default; pass it so the route is explicit.
Omit `--manager` and Workshop stays on Codex. If the first native turn stops
before Release, continue the same Wish with `uv run workshop resume <wish-id>`.
A later run of this Wish is the same Manager and Spark route, not a replay of
the exact Horn Tip CAD bytes.

While `wish` or `resume` is active, the foreground command prints only coarse,
content-free activity such as reasoning, tool use, and a throttled liveness
heartbeat. With `--json`, that live activity goes to stderr and stdout remains
one final JSON receipt.

Once the exact Codex session is checkpointed, the same `wish` or `resume`
command automatically resumes it after a native-turn timeout or recognized
provider disconnect. Each continuation uses bounded jittered backoff and is
counted against the existing turn budget. Workshop first proves the previous
Codex POSIX process session is empty, so no member of any process group in that
session can overlap the resumed turn. Product-run tools are required to remain
attached to that session; detached or background tool daemons are unsupported.
Unknown failures, unsafe
termination, and interruptions before a session identity is known still stop
without creating a replacement session.

If a deterministic gate fails or a required tool or authorization is missing,
the run waits with a concrete need. It never starts a replacement session or
treats model prose as proof.

## How the runtime is divided

The selected coding-agent runtime does nearly all product work: discovery,
Match judgment, research, concept exploration, design, CAD iteration, artifact
inspection, repair, printable-manual design, and bounded
evidence-linked Release facts. Manager runtime support is deliberately pluggable:

| Workshop Manager runtime | Status |
|---|---|
| Codex | Implemented default (`--manager codex`) |
| Claude Code | Experimental adapter (`--manager claude`) |
| Grok Build | Experimental adapter (`--manager grok`); Spark E2E: [Horn Tip](toys/pico-press-horn-tip/) |

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

The file must be named `TASTE.md`. Workshop preserves its exact bytes, derives
the Inventor id from the frontmatter name, creates the required specialist
skill, and validates the finished bundle before reporting success.

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
- [Mira Fold](inventors/mira-fold/TASTE.md) — compact tactile transformations with one hidden mechanical reveal
- [Pico Press](inventors/pico-press/TASTE.md) — tiny support-free toys built around one crisp repeatable motion ([Horn Tip](https://www.autonomous.ai/factory/product/horn-tip), Spark on Grok Build)
- [Tess Loop](inventors/tess-loop/TASTE.md) — flat-print modular systems that bloom into patterns and negative space

Read [Build an Inventor](docs/BUILD_AN_INVENTOR.md) for the specialist contract.

## Repository structure

The installed distribution is `autonomous-workshop`. Python code imports the
`workshop` package, and the `workshop` command is implemented by the sibling
`src/cli/` package. The `src/` layout keeps repository-only files from being
imported accidentally.

- [`toys/`](toys/) contains only sanitized released examples under
  `<inventor>-<product-slug>/`, including
  [`toys/pico-press-horn-tip/`](toys/pico-press-horn-tip/) from a Grok Spark
  run. Private runtime projects are outside Git at
  `$WORKSHOP_HOME/runs/<wish-id>/workspace` and contain the product-run
  `AGENTS.md`, custom Inventors, skills, exact roster, and Wish-to-Release
  artifacts.
- [`.agents/product-run/`](.agents/product-run/) is the complete isolated
  template copied into every new toy project before the runtime starts.
- [`inventors/`](inventors/) contains reusable Inventor sources: manifest,
  Taste, required primary skill, and any additional specialist skills or tools.
- [`src/cli/`](src/cli/) owns command parsing, presentation, and exit codes.
- [`src/workshop/`](src/workshop/) is the narrow trusted host, organized by
  Wish, Match, Invent, Make, Playtest, Release, workflow,
  runtime, contracts, gates, and integrations.
- [`src/workshop/make/skills/`](src/workshop/make/skills/) holds the canonical
  shared CAD and making skills.
- [`src/workshop/release/skills/manual-design/`](src/workshop/release/skills/manual-design/)
  holds the canonical in-box manual design and review skill.
- [`tests/`](tests/) mirrors the component ownership and contains the full
  deterministic and installed-package acceptance suite.
- [`docs/`](docs/) contains the architecture, runtime protocol, evidence, and
  contributor guides, including the [product verification
  levels](docs/PRODUCT_VERIFICATION.md).

Trusted checkpoints, receipts, credentials, and effect state live outside the
coding-agent working directory under `$WORKSHOP_HOME/state/<wish-id>/`. The
private project remains useful and inspectable without exposing host authority.
Factory publication is required for Release; only the later act of copying a
sanitized public example into the repository `toys/` directory is optional.

Shared code is organized by architecture component under `src/workshop/`:
`product`, `wish`, `match`, `invent`, `make`, `playtest`, `release`,
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
codex login status
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
- [Deferred Playtest evidence design](docs/PLAYTEST_EVIDENCE.md)
- [Publication boundary](docs/PUBLISH_SEALED_PRODUCT.md)
- [Contributing](CONTRIBUTING.md)

Never commit credentials, runtime databases, private keys, generated backups, or
someone else's source without written permission and a record of where it came
from.
