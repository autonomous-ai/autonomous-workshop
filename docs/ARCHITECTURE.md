# Autonomous Workshop architecture

Autonomous Workshop turns one person's Wish into one evidence-backed physical
product design. It is a thin workflow harness over a native coding-agent
runtime, not a Python agent framework.

## Product scope

The first version makes playthings for grown-ups (14+) in five lanes:

- `classics-made-yours` — known games and puzzles as exceptional personal
  editions;
- `invented-games` — new rules, strategy, mysteries, and tactile problems;
- `moving-machines` — mechanisms and kinetic objects;
- `holdable-science` — physical expressions of science and mathematics;
- `little-worlds` — personal places, characters, objects, and memories made
  miniature.

Every result must be materially shaped by the Wish, feel designed rather than
decorated, and be represented no more strongly than its evidence permits.

## Lifecycle

```text
Wish -> Match -> Invent -> Make -> Playtest -> Release -> Deliver
                            ^          |
                            +----------+
                              feedback
```

- **Wish** preserves the person's exact words and explicit constraints.
- **Match** selects one eligible immutable Inventor persona for that Wish.
- **Invent** explores and records one bounded product concept with research
  provenance where needed.
- **Make** creates the actual product tree, CAD project, assemblies, and
  deterministic CAD verification.
- **Playtest** inspects and simulates that exact Made revision. Evidence-linked
  failures return to Make within a bounded round budget.
- **Release** creates `MANUAL.md`, canonical product facts, evidence-bound
  claims, page metadata, and the factual package used to create a Factory page.
- **Deliver** owns separately authorized manufacture, hands-on QA, packing, and
  carrier evidence. Until those receipts exist, the run waits truthfully.

Release replaces the old instruction-only name because the output is broader than
a manual. It owns the complete factual publication package while keeping
Factory-generated copy/media and authenticated publication outside the agent.

Customer Reviews happen after delivery and may inform a later Wish or revision.
They do not mutate a completed run.

## One native Manager session per Wish

`workshop wish` creates a private workspace and starts one native Codex session
before Match. The same session handles discovery, research, concept work, CAD,
inspection, repair, Playtest judgment, manual writing, and product-page facts.
`workshop resume` continues the exact recorded session id.

That root Codex session is the Workshop Manager. It may dynamically delegate
bounded matching, specialist creation, or independent inspection to native
subagents. Those children are part of the Manager's native agent tree; they are
not separately launched OS-level Codex processes, Python workers, or lifecycle
sessions. The root Manager receives each host stage packet, synthesizes child
work, and submits the one proposal the host verifies.

Stage names are host checkpoints, not Python workers or model personas. During
Match, the Manager may ask native children for bounded candidate-fit analysis,
then makes one evidence-based selection. V1 passes exact materialized persona
bytes during dynamic delegation and does not depend on an unfinished or
undocumented named custom-role registry.

An Inventor is a native specialist bundle:

- `TASTE.md` defines creative judgment, preferences, and rejection boundaries;
- `inventor.json` defines stable identity, lane/eligibility, declared
  capabilities, and the exact optional extension surface;
- optional inventor-owned Codex skill trees contain `SKILL.md` for specialist
  workflow and tool routing;
- their optional scripts, references, assets, CAD generators, evaluators, and
  other tested deterministic tools provide specialist craft.

The selected native Inventor subagent reasons and invokes those declared
resources. Custom code never becomes a prompt loop, agent scheduler, lifecycle
engine, semantic gate, or credential-bearing effect path. Child output remains
a proposal: the root Manager reviews it, and the host still verifies exact
bytes and advances the gate.

The durable workspace is authoritative. Session memory never overrides exact
files, manifests, gate receipts, or effect receipts.

## Trust boundary

### Native Codex owns

- root-session Workshop management, native subagent delegation, and synthesis;
- understanding the Wish and Match reasoning;
- native search and source provenance;
- concept exploration and design decisions;
- use of CAD, product-to-CAD, STEP-parts, rendering, and other materialized
  skills;
- creation and repair of product files;
- AI Playtest perspectives and evidence-linked feedback;
- `MANUAL.md`, factual Release content, and page metadata;
- a compact proposal for the next host transition.

### The Python host owns

- Wish/run identity, private roots, immutable inputs, and durable checkpoints;
- validation, hashing, and capability limits for every materialized Inventor
  bundle and declared extension;
- legal transition order, leases, round budgets, and invalidation;
- Codex session start/resume and environment scrubbing;
- public contracts, exact-byte manifests, deterministic CAD/evidence gates,
  and artifact sealing;
- authorization, credential isolation, idempotency, external adapters,
  reconciliation, and receipts.

Python never performs creative candidate generation, semantic judging, prompt
chaining, persona simulation, repair reasoning, or a score/reward loop. Codex
does not advance its own gate or perform credential-bearing effects.

## Workspace protocol

The host materializes the product-run constitution, workflow skill, Make
domain skills, Wish, and exact declared Inventor bundles into a private run
root. Before each native turn it writes read-only `STAGE.json` with:

```text
schema_version, kind, product_id, stage, checkpoint_sha256,
subject_sha256, next_transition, round, max_rounds, inputs
```

The packet binds exact upstream contracts and canonical output paths for only
the current stage. Codex authors substantive files and then invokes the
run-local, standard-library finalizer:

```text
.agents/skills/autonomous-workshop/scripts/stage_proposal.py
```

The finalizer validates authored input, hashes exact bytes, writes the
canonical stage contract, and atomically writes `agent-outcome.json`. It does
not call a model or pass a gate. The host verifies the proposal binding, rereads
the whole artifact tree, reruns trusted checks, seals accepted bytes, and alone
advances the durable checkpoint.

If a Playtest verdict is `improve` or `block`, the proposal returns to Make and
preserves feedback evidence. A changed Make revision invalidates old Playtest,
Release, and Deliver evidence.

## Evidence boundaries

| Evidence | May support | Does not prove |
|---|---|---|
| Native research with cited sources | factual design assumptions | that a source is current if it was not checked |
| AI simulation | executable rules, termination, measured strategy or pacing proxies | human enjoyment or comprehension |
| Independent model inspection | a recorded prediction about clarity, novelty, or Taste fit | human preference or physical behavior |
| CAD/kernel verification | topology, dimensions, required files, and exact computed geometry properties | successful physical printing or durability |
| Slicer analysis | predicted printability under an exact machine/material/profile | a successful print or surface quality |
| Host Factory receipt | reconciled remote draft/publication state for exact hashes | manufacture, shipment, or delivery |
| Deliver receipts | the exact production, QA, packing, or carrier event observed | a later event or customer experience |
| Customer Review | what one verified recipient reported | universal preference or an earlier Playtest fact |

Unknown, missing, stale, malformed, mismatched, or timed-out evidence cannot
pass. A model's confidence is never independent evidence.

## Release and Factory

The local Release package is rooted at `artifacts/release/package` and contains
at least:

- substantive UTF-8 `MANUAL.md`;
- canonical `product.json` with exact Made/Playtest identities, factual product
  fields, claims copied from exact Playtest evidence, and Factory enrichment
  marked pending.

Local Release data may describe the product but cannot contain credentials,
remote receipts, generated marketing media, or claims that Factory enrichment
already happened. The host validates and seals the package before importing it.

The CLI default is private. `--publish` records explicit prospective authority
for the host to promote the exact verified Factory page after private import
and authenticated readback. Factory credentials are never copied into the run
workspace or Codex process. A public page is not a Deliver receipt.

## Shared implementation

```text
inventors/<id>/
  TASTE.md                 immutable creative point of view
  inventor.json            identity, eligibility, capabilities, extension manifest
  skills/<inventor-skill>/ optional inventor-owned Codex skill tree
    SKILL.md               specialist workflow and tool routing
    scripts/               optional deterministic specialist tools
    references/            optional specialist reference material
    assets/                optional immutable templates and references

.agents/
  product-run/             run-only constitution source
  skills/autonomous-workshop/
                            run workflow and proposal finalizer

src/
  cli/                     thin user-facing host commands
  workshop/
    product/               lanes and blueprints
    wish/                  exact customer-intent contract
    match/                 persona catalog and assignment contract/gate
    invent/                concept contract/gate
    make/                  Made/CAD contracts and deterministic gates
      skills/              canonical reusable Make domain skills
    playtest/              evidence, feedback, and Playtested contract/gate
    release/               local package and Release contract/gate
    deliver/               physical-effect contracts
    workflow/              lifecycle/checkpoint protocol
    artifacts/             immutable artifact identity
    runtime/               native session and trusted state/effect boundaries
    integrations/          host-only external adapters
    contributors/          Taste and persona catalog tooling

tests/<component>/         tests mirror component ownership
```

The installed distribution is `autonomous-workshop`; application imports begin
with `workshop`. The `workshop` command lives in the sibling `src/cli/` package.
Keeping both under `src/` prevents repository tools, fixtures, and tests from
being imported accidentally.

Dependencies follow the product flow. Stage components own narrow contracts
and deterministic gates. `workflow` alone owns sequencing. `runtime` owns
session/state boundaries. `integrations` owns credential-bearing adapters. The
CLI composes those surfaces and contains no product reasoning.

## Engine portability

Codex is the first supported native engine. The adapter seam is session
start/resume, native specialist delegation, and the run workspace protocol—not
the content of Codex prompts or one vendor's named-role configuration. A later
Claude Code, OpenCode, Pi, or Hermes adapter must preserve the same root Manager
identity, exact Inventor bundle, `STAGE.json`, exact-byte gates, authorization,
and effect isolation.
