<table width="100%">
  <tr>
    <td align="center" width="33%"><img src="docs/images/horn-tip.jpg" width="100%" alt="Horn Tip"></td>
    <td align="center" width="33%"><img src="docs/images/blindcap.gif" width="100%" alt="Blindcap: Duel"></td>
    <td align="center" width="33%"><img src="docs/images/alice-sf-chess.jpg" width="100%" alt="2030 San Francisco Chess Set"></td>
  </tr>
  <tr>
    <td align="center" width="33%"><img src="docs/images/trotter.gif" width="100%" alt="Trotter"></td>
    <td align="center" width="33%"><img src="docs/images/ivy-solar-system.jpg" width="100%" alt="Solar system with engraved orbits"></td>
    <td align="center" width="33%"><img src="docs/images/eve-f1-car.jpg" width="100%" alt="1:16 Formula 1 car"></td>
  </tr>
</table>

# Autonomous Workshop

Create your own autonomous AI Inventor. Shape its Taste, give it direction, and let it dream up and develop original toys and games for people to buy.

Autonomous Workshop is the engine behind this vision: anyone can build a toy studio around their own Inventors. The creator shapes taste and direction. The Inventor researches, invents, and makes. Autonomous brings the toys to the [shop](https://www.autonomous.ai/toys), with physical production, shipping, and customer support owned by Operations.

**Our first category is toys and games. Our focus is autonomous Inventors that people create and direct.** Conversation is the main creative interface; individual toy briefs and CAD edits support that relationship.

[![The Autonomous Workshop loop: Daydream, Invent (optional), Make, Playtest (optional), Release, Shop, Scoreboard](docs/images/inventor-loop.svg)](docs/images/inventor-loop.svg)

## The creator experience

The planned [**Manage Inventors** page](https://github.com/autonomous-ai/autonomous-workshop/issues/16) gives each creator a collection of Inventors. Click **Add Inventor**, start a conversation about the toys you want to put into the world, and develop a recognizable creative point of view together. Each Inventor has one persistent workspace:

- **Chat:** give direction, explore ideas, discuss a particular toy, and hear about meaningful progress and customer feedback.
- **Taste:** an editable `TASTE.md` that captures what the Inventor loves, rejects, and aims to make unmistakably its own. Clear lasting preferences from conversation become visible, versioned updates with undo; a request about one toy stays with that toy.
- **Inventions:** the Inventor's toy library, including ideas, work in progress, released products, revision history, units sold, and buyer ratings with review counts. A new revision can be in development while an earlier revision remains on sale.

Creators can have multiple Inventors with different tastes. Each works within explicit operating limits and publishing permissions. Creators return to see what their Inventors have made, learn from the results, and shape their next direction.

## How we are opening the Workshop

1. **Be the first creators.** We create and operate the initial Inventors ourselves, testing the same tools and product journey we intend to offer others.
2. **Invite creators.** A small group establishes its own Inventors and toy studios, helping us prove that distinctive toys and dependable fulfillment can work beyond our own team.
3. **Open creation to everyone.** Anyone can create and direct Inventors; shared quality requirements and operating controls apply as the community grows.

Our initial Inventors seed the shop and exercise the system. The long-term platform brings together many creators, their autonomous Inventors, and people who want to buy their toys.

## What works today and what comes next

- **Available in the CLI:** `workshop create inventor --taste ./TASTE.md` creates a specialist bundle from your exact Taste and connects its publishing account. `workshop start <inventor>` repeatedly dreams, builds, and attempts publication until stopped or its failure limit is reached. `workshop daydream <inventor>` lets you inspect an idea before building it. See the [Quickstart](#quickstart) and [Build an Inventor](docs/BUILD_AN_INVENTOR.md).
- **Implemented production boundary:** the host seals and checks each enabled stage, then publishes the accepted digital product and manual through Factory with authenticated readback. Operations owns physical production, hands-on checks, shipping, and customer support after that handoff. Publication alone does not prove manufacture or delivery.
- **Planned creator workspace:** the hosted Manage Inventors page, persistent creator chat, conversation-driven Taste revisions, and invention performance views described above.
- **Planned learning loop:** creator feedback and actual product outcomes inform future work. Today's notebook remembers previous ideas to avoid repetition; sales, playtests, and customer reviews do not yet flow back into it. Outcome feedback should improve an Inventor's judgment while preserving the creator's control over its Taste.

Internally, the sealed brief that begins one product run is still called a Wish. Existing Wish commands and frozen run contracts remain part of the engine; the consumer experience centers on creating and directing an Inventor.

## Quickstart

```bash
git clone https://github.com/autonomous-ai/autonomous-workshop.git
cd autonomous-workshop

codex login
uv run workshop doctor
```

When an Inventor is not yet connected, Workshop opens [Connect Inventor](https://www.autonomous.ai/toys/inventor/login) during `create` or `start`. Choose the Autonomous account that should publish this Inventor's toys, then approve the connection. Workshop continues in the terminal; if the browser does not open, follow the URL it prints.

Each Inventor has its own owner-only credential file under `$WORKSHOP_HOME/credentials/inventors/`. The browser returns only a short-lived, one-time authorization code; Workshop exchanges it directly with the Autonomous Toys API. Publishing credentials never enter a browser URL, product workspace, or coding-agent session. To choose a different account later, run `uv run workshop login <inventor-id>`.

One command runs the whole loop, and keeps running it. Pico Press daydreams one brand-new idea that fits its Taste, the host rejects anything too close to a toy already made, the survivor is sealed as the brief, the run makes and publishes it (✨ Spark, `Make -> Release`, with Codex as the Workshop Manager; the idea is already the concept), and then Pico Press dreams the next one:

```bash
uv run workshop start pico-press
```

It runs until you stop it: Ctrl-C, or from another terminal:

```bash
uv run workshop stop pico-press          # ends after the current step
uv run workshop stop pico-press --now    # interrupts now; the current run stays resumable
```

Three consecutive failed daydreams or builds stop the loop on their own. `--once` dreams and builds a single idea; `--max-ideas N` stops after N. `--workflow` goes deeper: 🔥 Forge adds Invent (`Invent -> Make -> Release`), 🗺️ Quest adds Invent and Playtest:

```bash
uv run workshop start pico-press --workflow forge
```

Want to see an idea before building? `workshop daydream pico-press` prints the card and stops. Build a saved idea later with `workshop start pico-press --idea <daydream-id>`.

To make just one product from your own idea, use `wish`:

```bash
uv run workshop wish "A small hand-cranked cam toy" --inventor soren-voss \
  --workflow spark --agent codex --model sol --effort high
```

`start <inventor>` is the ongoing Inventor-led loop; `wish "..."` creates one
product and stops. Omit `--inventor` on a Wish to let the Manager choose the
best match. `start <inventor> --once` dreams and builds one Inventor-generated
idea. `resume <wish-id>` continues the same unfinished product and session.

`--agent` chooses the Workshop Manager runtime; `--model` and `--effort` choose its model and reasoning level. Those choices apply to both the daydream and product run and are frozen for resume. Codex defaults to Sol at high effort; Claude Code defaults to Opus 5 at high effort. Friendly Codex aliases such as `astra` and `sol` resolve to exact model ids. Grok's first ✨ Spark run, from a typed brief, produced [Horn Tip](toys/pico-press-horn-tip/):

```bash
grok login
uv run workshop start pico-press --agent grok --workflow spark

# Or run Codex Astra at high reasoning effort:
uv run workshop start pico-press --agent codex --model astra --effort high
```

Every run prints a run ID (a Wish ID). Check on it or continue the same session:

```bash
uv run workshop status <wish-id>
uv run workshop resume <wish-id>
```

`start` and `wish` accept `--max-tokens N`, default **10,000,000** per Codex
product. Input plus output is counted across all enabled build steps, native
children, retries, and resumes. Cached input counts and is reported separately;
reasoning output is already part of output. `start` gives each product its own
allowance; the separate Daydream session is outside this build budget.

```bash
uv run workshop wish "A simple one-piece gravity desk rocker" --inventor soren-voss \
  --workflow spark --agent codex --model astra --effort medium --max-tokens 10000000
uv run workshop resume <wish-id> --max-tokens 15000000  # total cap, not extra tokens
```

Omitting `--max-tokens` on resume preserves the saved allowance. Providing it
explicitly adopts token budgeting for an eligible older run or changes its
total cap, retaining recovered prior usage. Token-budgeted runs no longer split
every twenty minutes; a one-hour emergency execution watchdog remains. Native
usage is observed after requests, so in-flight work can overshoot the threshold.
Missing usage is not free work. This is not a dollar cap. The local usage adapter
currently requires Codex 0.153.4; other Managers retain their existing policy.
Live acceptance passed for [Quiet Arc](https://www.autonomous.ai/toys/product/quiet-arc):
Spark / Codex / Astra / medium / Soren, including same-session recovery and
verified publication, used 6,893,962 observed tokens of the 10M allowance.
This validates one simple digital-product workflow, not physical manufacture
or every live parameter combination.

Long turns remain attached to the same session if the locally installed Codex
CLI receives a supported in-place update. Workshop still rejects downgrades,
major-version changes, and same-version policy drift.
Timeouts and exact recognized provider disconnects resume that same session;
unknown failed turns still stop safely for an explicit operator resume. A
terminal failure reports and privately records a bounded cause category,
recognized signature, safe provider code, and message size without retaining
the provider's free-form error text.

## Workshop Managers

One run is one native coding-agent session — the shop lead. Resume cannot switch Managers.

```bash
uv run workshop start pico-press --agent codex    # Sol + high; default
uv run workshop start pico-press --agent claude   # Opus 5 + high; experimental
uv run workshop start pico-press --agent grok     # experimental
```

| Manager | CLI | Status |
|---|---|---|
| [Codex](https://learn.chatgpt.com/docs/codex/cli) | `codex` | Default. Omit `--agent`. |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | `claude` | Experimental. |
| [Grok Build](https://docs.x.ai/build/overview) | `grok` | Experimental. Spark E2E: [Horn Tip](toys/pico-press-horn-tip/). |

## Inventors

Each Inventor expresses a specialist point of view. Several can make the same kind of toy in their own way. The bundled Inventors are our first studios and public examples; creators can already add their own through the CLI. The hosted creation and management experience is planned.

An Inventor is a declared specialist bundle: `TASTE.md` for creative judgment, `inventor.json` for identity and skill hashes, and a required `<id>-inventor` skill. Optional extra Inventor-prefixed skills may hold scripts, references, or tested deterministic tools. For a run, `.codex/agents/*.toml` is the sole roster. Inventor code cannot launch agents, choose stages, pass gates, or perform authenticated effects.

```bash
uv run workshop create inventor \
  --taste ./TASTE.md
```

The file must be named `TASTE.md`. Workshop preserves its exact bytes, derives the Inventor id from the frontmatter name, creates the required specialist skill, and validates the bundle.

```markdown
---
name: Ada
description: Choose Ada for hand-cranked creatures; not static models or games.
---

# Ada's taste

I love mechanisms whose motion tells the story. I reject decoration without play.
```

Read [Build an Inventor](docs/BUILD_AN_INVENTOR.md) for the specialist contract.

### Alice — reinvent the classics ([TASTE.md](inventors/alice/TASTE.md))

Chess, go, dominoes, puzzles — games everyone already knows, made into a set that is yours. Alice never touches the rules. She changes what the pieces are, so the set is about you.

![2030 San Francisco Chess Set](docs/images/alice-sf-chess.jpg)
*2030 San Francisco Chess Set*

### Leo — invent games that don't exist yet ([TASTE.md](inventors/leo/TASTE.md))

Brand new games, invented for one wish: new rules, new pieces, a new reason to sit at a table. Quest effort exercises those rules with seeded Playtest evidence; Spark and Forge truthfully release without claiming that testing occurred.

https://github.com/user-attachments/assets/36ffa63e-6e36-4422-8db7-bb1545b3bdb7

*[Blindcap: Duel](https://www.autonomous.ai/toys/product/blindcap-duel)
— a two-player hidden-information strategy game of mushrooms, probes, and crowns*

### Bob — invent machines that move ([TASTE.md](inventors/bob/TASTE.md))

Things that do one delightful thing when you wind them up, let them go, or drop something in. No motors, no batteries, no electronics — the movement has to come out of the shape itself.

https://github.com/user-attachments/assets/ba57de75-37e2-45e8-a71f-2a339b0de49a

*[Trotter](https://www.autonomous.ai/toys/product/spot-quadruped-robot-wind-up-walker)
— a palm-size, rubber-band-powered quadruped*

### Ivy — invent science toys you can hold ([TASTE.md](inventors/ivy/TASTE.md))

The planets, a swinging pendulum, a shape that looks impossible — real science, small enough to pick up. Ivy says where her numbers came from and what she left out, because here being wrong is worse than being boring.

![A solar system with its orbits engraved](docs/images/ivy-solar-system.jpg)
*A solar system with its orbits engraved — $59.99*

### Eve — invent little worlds ([TASTE.md](inventors/eve/TASTE.md))

Your dog, your bike, your desk, your homelab — turned into a small world you can put on a shelf. Eve's only counts if it could not have existed before your wish.

![A 1:16 Formula 1 car](docs/images/eve-f1-car.jpg)
*A 1:16 Formula 1 car*

### Sonora Reed — sculpt sound from geometry ([TASTE.md](inventors/sonora-reed/TASTE.md))

Passive acoustic toys whose playable voices come from visible printed ridges,
chambers, tracks, and resonant bodies—never electronics or decorative claims.

### Vela Bloom — make small shapes transform ([TASTE.md](inventors/vela-bloom/TASTE.md))

Compact rigid-link toys that deploy, iris, unfurl, or blossom through one
legible, collision-aware transformation with deliberate end states.

### Kestrel Knot — make continuity feel impossible ([TASTE.md](inventors/kestrel-knot/TASTE.md))

Topology-driven captive-motion toys built from open loops, crossings, braids,
and continuous routes whose geometry and clearances can be checked exactly.

### Orin Shadow — make geometry tell a second story ([TASTE.md](inventors/orin-shadow/TASTE.md))

Mechanical shadow-play toys whose held form casts a hidden creature, place, or
event under ordinary light. Orin authors the solid object, its negative space,
and its hand-powered projected transformation as one printable mechanism.

## Toys

Toys that already left the Workshop. After Factory publication, a sanitized snapshot lands in [`toys/<inventor>-<slug>/`](toys/). These are public examples, not private run workspaces.

![Horn Tip](docs/images/horn-tip.jpg)

| Toy | Inventor | Effort | Snapshot | Factory |
|---|---|---|---|---|
| Moonwake Turn | [Luma Vale](inventors/luma-vale/) | Spark | [`toys/luma-vale-moonwake-turn/`](toys/luma-vale-moonwake-turn/) | [moonwake-turn](https://www.autonomous.ai/toys/product/moonwake-turn) |
| Mooncoil Dragon | [Pico Press](inventors/pico-press/) | Spark | [`toys/pico-press-mooncoil-dragon/`](toys/pico-press-mooncoil-dragon/) | [mooncoil-dragon](https://www.autonomous.ai/toys/product/mooncoil-dragon) |
| Pocket Eclipse Menagerie | [Orin Shadow](inventors/orin-shadow/) | Spark | [`toys/orin-shadow-pocket-eclipse-menagerie/`](toys/orin-shadow-pocket-eclipse-menagerie/) | [pocket-eclipse-menagerie](https://www.autonomous.ai/toys/product/pocket-eclipse-menagerie) |
| Starling Gate | [Pico Press](inventors/pico-press/) | Spark | [`toys/pico-press-starling-gate/`](toys/pico-press-starling-gate/) | [starling-gate](https://www.autonomous.ai/toys/product/starling-gate) |
| Moonchase Fox | [Pico Press](inventors/pico-press/) | Spark | [`toys/pico-press-moonchase-fox/`](toys/pico-press-moonchase-fox/) | [moonchase-fox](https://www.autonomous.ai/toys/product/moonchase-fox) |
| Storm Reveal | [Mira Fold](inventors/mira-fold/) | ✨ Spark | [`toys/mira-fold-storm-reveal/`](toys/mira-fold-storm-reveal/) | [storm-reveal](https://www.autonomous.ai/toys/product/storm-reveal) |
| Saigon Skyline Chess | [Alice](inventors/alice/) | ✨ Spark | [`toys/alice-saigon-skyline-chess/`](toys/alice-saigon-skyline-chess/) | [saigon-skyline-chess](https://www.autonomous.ai/toys/product/saigon-skyline-chess) |
| Rainspell Dial | [Sonora Reed](inventors/sonora-reed/) | 🔥 Forge | [`toys/sonora-reed-rainspell-dial-three-field-sound-garden/`](toys/sonora-reed-rainspell-dial-three-field-sound-garden/) | [rainspell-dial-three-field-sound-garden](https://www.autonomous.ai/toys/product/rainspell-dial-three-field-sound-garden) |
| Eclipse Braid | [Kestrel Knot](inventors/kestrel-knot/) | ✨ Spark | [`toys/kestrel-knot-eclipse-braid/`](toys/kestrel-knot-eclipse-braid/) | [eclipse-braid](https://www.autonomous.ai/toys/product/eclipse-braid) |
| Moonwake Garden | [Luma Vale](inventors/luma-vale/) | 🗺️ Quest | [`toys/luma-vale-moonwake-garden/`](toys/luma-vale-moonwake-garden/) | [moonwake-garden](https://www.autonomous.ai/toys/product/moonwake-garden) |
| Horn Tip | [Pico Press](inventors/pico-press/) | ✨ Spark | [`toys/pico-press-horn-tip/`](toys/pico-press-horn-tip/) | [horn-tip](https://www.autonomous.ai/toys/product/horn-tip) |
| Quiet Arc | [Soren Voss](inventors/soren-voss/) | ✨ Spark | [`toys/soren-voss-quiet-arc/`](toys/soren-voss-quiet-arc/) | [quiet-arc](https://www.autonomous.ai/toys/product/quiet-arc) |
| Lunar Relay | [Bob](inventors/bob/) | ✨ Spark | [`toys/bob-lunar-relay/`](toys/bob-lunar-relay/) | [lunar-relay](https://www.autonomous.ai/toys/product/lunar-relay) |
| Orbit Gobbler | [Bob](inventors/bob/) | 🔥 Forge | [`toys/bob-orbit-gobbler/`](toys/bob-orbit-gobbler/) | [orbit-gobbler](https://www.autonomous.ai/toys/product/orbit-gobbler) |
| Comet Heist | [Leo](inventors/leo/) | 🗺️ Quest | [`toys/leo-comet-heist-twin-pulse-vault-run/`](toys/leo-comet-heist-twin-pulse-vault-run/) | [comet-heist-twin-pulse-vault-run](https://www.autonomous.ai/toys/product/comet-heist-twin-pulse-vault-run) |
| Cradle Crescent | [Bob](inventors/bob/) | — | [`toys/bob-cradle-crescent/`](toys/bob-cradle-crescent/) | [cradle-crescent](https://www.autonomous.ai/toys/product/cradle-crescent) |
| False Lantern | [Leo](inventors/leo/) | — | [`toys/leo-false-lantern/`](toys/leo-false-lantern/) | [false-lantern](https://www.autonomous.ai/toys/product/false-lantern) |

Horn Tip is a Spark run on Grok. A later run with the same brief is the same route, not a replay of those CAD bytes. Cradle Crescent and False Lantern are older snapshots.

Private runs live outside Git at `$WORKSHOP_HOME/runs/<wish-id>/workspace`. New
toy READMEs report best-effort gross, cached, and uncached Manager input plus
output and reasoning-output tokens by stage, alongside elapsed time from run
intake through authenticated Factory public readback. This is telemetry, never
a gate, and no dollar estimate is inferred. See
[`toys/README.md`](toys/) for what a snapshot includes and
[`docs/QUALITY_ECONOMICS.md`](docs/QUALITY_ECONOMICS.md) for the paired quality
and cost benchmark.

Forge and Quest now make the cheapest exact mechanism/form falsifier the first
persisted Make deliverable under `<cad-project>/review/early-proof/`, before the
complete part tree. Native Make iteration uses source-fresh print-preflight
without destructive cache cleanup; the trusted isolated host alone performs
the authoritative fresh rebuild before Made can advance. The v9 proof uses one
shared helper and three exact state entries that each expose one module-scope
`gen_step()`, and the host supplies exact
`$WORKSHOP_PYTHON`-prefixed generate, export, and render commands so Make does
not spend its bounded proof phase rediscovering package entrypoints. New deep
runs bind a private run-local cache, defer the broad CAD skill until final
Make, batch all mandatory proof reads, author source as the next durable action,
and execute proof commands as one foreground batch. A fixed-camera
`--state-sheet` renders the three exact state STLs and rejects visually
indistinguishable frames; rotating one unchanged mesh is only viewpoint
evidence. The root performs the cheap early direction check; the independent
blind critic remains at the final hash-bound Make review.

## Architecture

The floorplan of the shop. An Inventor's idea walks one frozen route; Operations takes the sealed Release and the shop sells it.

[![A peek inside the Autonomous Workshop: a pluggable coding-agent runtime follows a selectable Spark, Forge, or Quest route before handing the released toy to Operations](docs/images/workshop-floorplan.svg?version=daydream-v1)](docs/images/workshop-floorplan.svg)

```text
Daydream -> one liked idea -> a frozen effort route:

✨ Spark: Make -> Release                          (default)
🔥 Forge: Invent <-> Make -> Release
🗺️ Quest: Invent <-> Make <-> Playtest -> Release

Release -> Shop (order one, printed to order, photographed, ships in days)
Shop -> Scoreboard (views, orders, prints, returns) -> back to Daydream
```

Route diagrams: [Spark](docs/images/effort-spark.svg) · [Forge](docs/images/effort-forge.svg) · [Quest](docs/images/effort-quest.svg).

Every run is keyed by a Wish id. Passed-through stages create no turn, artifact, gate, or evidence; Spark and Forge record Playtest as `not-run`. The reverse arrows are evidence-bound repair routes that spend a shared revision budget, not free retries.

**Who does what.** The selected [Workshop Manager](#workshop-managers) does the product work in one persistent native session, one Goal at a time. Every step is one native Goal, Daydream included, and every Goal ends with a run-local finalizer writing `agent-outcome.json`, which is the only completion signal the host trusts. The Python host is narrow and trusted: identity, exact bytes, lifecycle order, budgets, session start and resume, deterministic gates, credential isolation, and authorized effects. There is no second agent framework, prompt chain, or reward loop.

**Two sessions, by design.** `workshop start` is a loop: dream, build, dream again. A daydream is its own short native session. It ends when the idea is sealed: linted, hashed, written to the Inventor's notebook, and rendered as the brief. Each liked idea then gets its own persistent build session, one per run, exactly as a typed brief would. The idea is an immutable input to the build, so Make can never quietly rewrite what it is building; daydreams can run on their own cadence; a saved idea can be built later, on any route or Manager, or rebuilt after a failed Make; and a build failure never touches the idea.

**What Make must prove.** Every printable part passes a fixed print preflight (bed fit, mesh validity, wall thickness at a 0.4 mm nozzle). One independent critic then reviews exact renders blind, before the brief is revealed, and the host rebuilds the CAD in isolation and seals the bytes. When a stage is truly blocked, it records a `Need:` that the receipt and `workshop status` show; nothing waits silently.

**What Release means.** Three facts about the same exact bytes:

- full-tier, thickness-checked, ready-to-print CAD
- a self-contained printable `MANUAL.pdf` for the box
- authenticated public Factory readback of those CAD and manual hashes

Workshop code ends there. Printing, delivery, and Review belong to Operations. Publication does not claim a physical print, pack, or delivery.

```text
inventors/          reusable Inventor sources (Taste, skills, tools)
toys/               sanitized public snapshots after Factory readback
.agents/product-run complete template copied into every new toy project
src/cli/            command parsing, presentation, exit codes
src/workshop/       trusted host: daydream, stages, workflow, runtime, gates, effects
tests/              component-mirrored deterministic suite
docs/               architecture, ADRs, and contributor guides
```

Private state stays outside the agent-visible checkout: `$WORKSHOP_HOME/daydreams/<inventor>/`, `$WORKSHOP_HOME/runs/<wish-id>/workspace`, and `$WORKSHOP_HOME/state/<wish-id>/`. Factory credentials live in `$WORKSHOP_HOME/credentials/inventors/<inventor-id>.env` (0600 inside a 0700 directory) and never enter the native agent's session.

Turn budgets, compaction ceilings, recovery windows, and the blind-review protocol are specified in [Native coding-agent runtime](docs/NATIVE_AGENT_RUNTIME.md). See also [Workshop architecture](docs/ARCHITECTURE.md), the [publication boundary](docs/PUBLISH_SEALED_PRODUCT.md), and [Playtest evidence](docs/PLAYTEST_EVIDENCE.md).

## Contributing

This is the shop floor for Workshop code and Inventor sources. To change the CLI, runtime, workflow, or product-run protocol, follow [CONTRIBUTING.md](.github/CONTRIBUTING.md). To add a specialist, start from [Build an Inventor](docs/BUILD_AN_INVENTOR.md).

```bash
uv run workshop doctor
PYTHONPATH=src python -m unittest discover -s tests -t . -p 'test_*.py'
```

Never commit credentials, runtime databases, private keys, generated backups, or someone else's source without written permission and a record of where it came from.

Licensed under [Apache-2.0](LICENSE).
