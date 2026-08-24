# Bob's architecture

> **Legacy board-game architecture.** Bob's canonical profile now makes moving
> machines through `profile.py`. Nothing in this document is the kinetic custom
> Make callback; it is preserved as migration material.

This board-game laboratory was built on the shared Workshop. The design
separates the tiny customer promise from the machinery that fulfills it.

## One customer story, four Workshop concepts

```text
CUSTOMER

      WISH  --------------------  WAIT  ----------------  RECEIVE
        |                                                       ^
        |                                                       |
        v                                                       |
BOB, BACKSTAGE                                                  |

      TASTE + Bob's workflow                                      |
                 |                                                |
                 v                                                |
             MAKE <-> INSPECT ------------------------------------+
               |         |
               |         +-- board-game inspectors
               +------------ rules, play engine, CAD

      Internal: artifact + runtime + adapter + receipt
```

The storefront adapter is optional. It is Bob's current external destination,
not the customer's whole experience; fulfillment eventually produces the
physical delivery.

## The Workshop boundary

```text
Bob owns                                  Workshop owns
------------------------------            -------------------------------
TASTE.md                                  Taste loading + content binding
idea search and game rules       ----->   common Wish/Make vocabulary
simulation and table play                 reusable skill catalog
CAD generation and game gates    ----->   canonical artifact handling
frozen reward function                    shared inspection primitives
queue policy                     ----->   durable runtime and effect outbox
storefront metadata              ----->   adapter + typed receipt
```

Bob intentionally does not claim the Workshop's generic
`Inspection`/`InspectionResult` surface yet. His existing rule, simulation,
table, CAD, and reward inspectors have board-game-specific evidence. The
manifest advertises only the shared features Bob actually uses.

The general Workshop Make surface is `Wish -> Workbench.make() -> MakeResult`.
Bob's older board-game loop currently owns its specialized Make orchestration,
so it does not claim `workbench.make` either. This distinction keeps the
manifest honest while Bob still shares Taste, artifact handling, and runtime
infrastructure.

At the effect boundary the authority chain is:

```text
exact product bytes
      |
      v
artifact: `pack_artifact(...)` -> `PackedArtifact`
      |       artifact_sha256 + pack_sha256
      v
inspection: `inspect_pack(...)`
      |
      v
runtime records intent BEFORE HTTP
      |
      v
storefront adapter (`ShopDoor`)
      |
      v
receipt (`Stamp`) binds owner + artifact + history + listing
      |
      v
Bob may update `send.json` and his queue
```

No JSON projection, HTTP status alone, stdout, remote design id, or human
assertion can skip that chain. A timeout or 5xx leaves the runtime intent
unknown and blocks a duplicate effect until it can be reconciled. `PackedArtifact`,
`Clockwork`, `ShopDoor`, and `Stamp` are compatibility API names, not additional
Workshop concepts.

## Bob's Make and Inspection work

Bob's persisted queue uses stable historical state values:

```text
sparked -> researched -> ruled -> rules_gated -> simulated -> tabled
        -> briefed -> built -> build_gated -> reviewed -> published -> live

side states: repairing, parked, blocked, killed
tick state:  quota_wait
```

They map onto the Workshop story as follows:

| Workshop verb | Bob's durable states | What happens |
|---|---|---|
| `MAKE` | `sparked` through `built` | select a direction, write rules, create a real engine, play it, form a parts brief, build CAD |
| `INSPECT` | `rules_gated`, `simulated`, `tabled`, `build_gated`, `reviewed` | reject unclear, degenerate, dull, derivative, unsafe, or unprintable games |

After `reviewed`, Bob builds one content-addressed artifact. The runtime may
then invoke the storefront adapter to create a private draft or, when explicitly
authorized, make it public. Those are implementation actions rather than more
Workshop verbs.

The old `sparked` value is only Bob's persisted idea-selection state. It is not
an additional customer step or a shared Workshop API.

Gate order is economic policy. Nothing expensive happens before the game has
been played:

1. **Idea search (`sparked` / `researched`)** — a bandit chooses a design
   direction. The exact UTF-8 content and SHA-256 of root `TASTE.md` bind to
   both the ideator and triage requests and are recorded in `idea.json`.
2. **Rules (`ruled` / `rules_gated`)** — complete rules and bill of parts,
   followed by deterministic lint and a blind fresh-reader lens.
3. **Machine play (`simulated`)** — code plays at least 1,000 games and a
   policy ladder. Balance, completion, agency, coverage, drama, lead changes,
   and move scarcity are measured rather than narrated.
4. **Seated play (`tabled`)** — LLM seats choose only from engine-legal move
   indices, so they cannot cheat, misremember, or politely pretend a game is
   fun.
5. **Physical Make (`briefed` / `built`)** — only now does Bob spend on CAD.
   The build prints the mechanism the game stands on, with a mid-build abort
   point for a wrong silhouette.
6. **Physical Inspection (`build_gated`)** — mesh, bed, clearance, wall,
   support, and printability checks run deterministically.
7. **Reward Inspection (`reviewed`)** — isolated judges produce evidence for
   the frozen reward function. Stale verdicts fail by artifact SHA-256. Missing
   evidence fails closed.
8. **Artifact and storefront effect** — `harness.send` validates the page kit,
   produces the canonical artifact, and either records a rehearsal or invokes
   the compatibility API `Sender`.

The frozen reward specification is in `docs/REWARD.md`. Its hard gates cover
completeness, simulation integrity, degeneracy, novelty evidence, safety, and
buildability. A score must meet the total threshold and every dimension floor.
Generators never see the evaluator weights or judge prompts.

## Loops and files

```text
                         evidence
                            ^
                            |
   Scholar + Librarian --> MAKE/INSPECT --> market + human play
          |                 |                         |
          v                 v                         v
       corpus/           games/                    ledger
          \                 |                         /
           +----------> weekly Meta <---------------+
                            |
                            v
                   prompts, lessons, proposals

   Architect reads outside engineering and files proposals for Meta.
```

No loop needs direct agent-to-agent messaging. Files are the message bus:

- `corpus/` holds history, design-book notes, and bandit directions.
- `games/<slug>/` holds the exact artifacts for one game.
- `state/QUEUE.json` decides what moves next and owns leases.
- `state/REWARD_LEDGER.jsonl` records spend and evidence.
- `state/inventor-workshop.sqlite3` is the runtime effect ledger; the filename is
  retained for compatibility.
- `games/<slug>/send.json` is an operator projection, never authority by itself.
- `games/<slug>/pack/` contains the current artifact archive and rehearsal
  report; the directory name is a persisted compatibility interface.

One launchd tick advances one step and exits. The order is integrity audit,
daily spend, lease, closest-to-finish game, study fallback, then weekly
architecture fallback. Quota exhaustion is a state with a retry time, not an
exception loop. A separate watchdog alarms when the heartbeat is stale.

## External-effect modes

The scheduler accepts one autonomous route:

```text
BOB_SEND_VIA=workshop
```

`BOB_SEND_DRY_RUN=1` is the default. It still builds the artifact, writes
`pack/manifest.json`, and writes a `send.json` rehearsal with
`send_authority: none`; it creates no remote listing.

With `BOB_SEND_DRY_RUN=0`, the compatibility API `Sender` creates a private
draft. Public publication is a
separate, explicitly priced action (`bob send <slug> --price-cents ...` or
`BOB_SHOP_PUBLIC=1` for the scheduled loop). An ambiguous public action is
reconciled by readback and never blindly repeated.

`BOB_SEND_VIA=box` is not an autonomous mode. The historical text2game server
name `box` exists only behind manual `bob export`. It cannot write effect
authority or advance Bob.

## Compatibility edge

New Bob code emits Workshop names. A narrow adapter can read older deployments:

- legacy `Foundation`/`Core` source and `Clockwork` file names
- Portal/Panda credentials and endpoint settings
- publish-prefixed environment settings
- `launch.json`, `published.json`, `launch_payload/`, and `publish_payload/`
- the old `harness.publish` module and `bob publish` command

Every fallback is conflict-checked. Multiple independent sources or state files
are split authority and stop the effect. Compatibility names never authorize a
manual `box` observation as a completed effect.

## Self-improvement authority

The weekly Meta loop may improve prompts, lessons, corpus material, and
proposals. Code changes go through review. It may never edit the frozen reward,
root `TASTE.md`, the owner-evidence archive, baselines, state, or the integrity
auditor. Repeated prose lessons must graduate into deterministic checks.

This keeps Bob's creativity flexible while the evaluator, Taste, artifact
identity, budgets, and effect authority remain difficult to game.
