# Native coding-agent runtime

This document is the operating map for contributors and builder agents working
on the Autonomous Workshop repository. It is authoritative together with
[ADR 0012](adr/0012-codex-orchestrated-runtime.md) and the repository
[agent constitution](../AGENTS.md).

## Two different coding-agent roles

Do not confuse these actors:

| Actor | Purpose | Instructions |
|---|---|---|
| Builder agent | Builds, reviews, tests, and documents this repository | root [`AGENTS.md`](../AGENTS.md), especially “Coding agents building this repository” |
| Product-run agent | Is launched by `workshop wish` to turn one exact Wish into one product | [`.agents/product-run/AGENTS.md`](../.agents/product-run/AGENTS.md) and [the product-run skill](../.agents/skills/autonomous-workshop/SKILL.md) |

The builder agent implements the harness. It is not the agent that Matches,
Invents, Makes, or Playtests a customer's product. The product-run agent works
in an isolated run root; it does not maintain the Workshop repository.

## The boundary in one sentence

Autonomous Workshop is a thin, deterministic host around one native coding
agent session per Wish: Codex does the cognitive and tool-using work, while the
Workshop host owns identity, lifecycle order, durable state, gates, budgets,
and authorized external effects.

This is not a Python agent framework with Codex calls inside it. Python must not
decide how to research a Wish, fan out creative candidates, impersonate stage
roles, or run its own model-judging loop. Those are native-agent jobs.

## Start and resume sequence

```text
user runs `workshop wish`
        |
        v
host validates and persists the exact Wish bytes
        |
        v
host creates a private run root
  - exact Wish
  - AGENTS.md
  - .agents/skills/autonomous-workshop/**
  - .agents/skills/{cad,product-to-cad,step-parts}/**
  - catalog/inventors/<id>/{inventor.json,TASTE.md}
  - durable host checkpoint
        |
        v
host starts one native Codex session before Match
        |
        v
Codex orchestrates Match -> Invent -> Make <-> Playtest
                              -> Instructions -> Deliver
        |
        v
host verifies each compact outcome and alone advances the checkpoint
```

The initial session is a real native Codex CLI session rooted in the isolated
run workspace. It uses the contributor's existing local Codex authentication.
The host records the session UUID as soon as Codex reports it. `workshop
resume` resumes that exact UUID; it does not reconstruct the run by starting a
fresh model call for every stage.

One Wish has one cognitive session. Stage names are lifecycle checkpoints, not
separate model personas or separate Python agents.

## Who owns what

| Owner | Responsibilities |
|---|---|
| Native Codex session | understand the Wish, inspect files, Match, research, explore concepts, design, use CAD and other skills, create artifacts, inspect results, repair failures, write Instructions, and propose the next transition |
| `workshop.workflow` | legal stage order, Make–Playtest round limit, invalidation, compact outcome protocol, and durable run checkpoint |
| `workshop.runtime` | native-session launch/resume, sandbox and environment boundary, session checkpoint, leases, budgets, receipts, and recovery |
| Lifecycle components | narrow public contracts and deterministic tools/gates owned by `wish`, `match`, `invent`, `make`, `playtest`, `instructions`, and `deliver` |
| `workshop.integrations` | credential-bearing, idempotent external adapters invoked only by the trusted host after authorization |
| `cli` | user-facing host entry points; it launches or resumes the native session but contains no product reasoning |

Codex can call narrow local Workshop tools for work that must be exact: schema
validation, artifact hashing, CAD generation or inspection, seeded simulation,
gate evaluation, checkpoint proposals, and effect-intent preparation. The
return value of a model is never itself a passed gate.

## Run workspace and skill materialization

The canonical product-run instructions are checked in at:

```text
.agents/product-run/AGENTS.md
.agents/skills/autonomous-workshop/SKILL.md
.agents/skills/autonomous-workshop/references/**
```

The repository root `AGENTS.md` contains shared architecture and a section for
builder agents; it is not copied wholesale into product runs. The built
distribution carries an exact byte-for-byte snapshot of the product-run
constitution and skill. Before a run starts, the host materializes them into
the private run root:

```text
<run-root>/AGENTS.md
<run-root>/.agents/skills/autonomous-workshop/SKILL.md
<run-root>/.agents/skills/autonomous-workshop/references/**
<run-root>/.agents/skills/{cad,product-to-cad,step-parts}/**
<run-root>/catalog/inventors/<id>/{inventor.json,TASTE.md}
```

The host copies `.agents/product-run/AGENTS.md` to `<run-root>/AGENTS.md`, then
hashes all materialized instruction bytes and binds the hash to the run. Resume
fails closed if the materialized instructions have changed. Do not maintain a
second hand-edited copy and do not install the project skill globally under a
user's Codex home.

Make owns the canonical domain-skill sources in `src/workshop/make/skills/`;
the run tree is a generated immutable snapshot. Inventor folders are personas,
not subprocess packages: Match reads their exact manifest and Taste bytes, and
the native session performs the work in that selected point of view.

Substantive output also lives in the run workspace. Agent messages contain only
a bounded outcome envelope: current stage, status, changed artifact paths and
hashes, needs, gate references, and proposed transition.

## Security and effects

The Codex child process receives a scrubbed environment and never receives
Factory passwords, publication tokens, payment credentials, or carrier
credentials. It may create a local draft or effect intent. Only the host can
execute an authenticated effect after verifying explicit authority, exact
artifact hashes, idempotency, and reconciliation.

Native search and repository tools are deliberate capabilities. Broad
unrestricted filesystem access, ignored repository rules, secrets in prompts,
and direct authenticated publication are not.

## Rules for builder-agent changes

Before adding Python, ask whether the code is one of these:

- a typed public contract;
- a deterministic validator, generator, or measurement tool;
- a durable checkpoint, budget, lease, or invalidation rule;
- a sandbox/session boundary;
- an authorization, idempotency, receipt, or reconciliation boundary;
- a provider adapter behind one of those boundaries.

If it is research strategy, planning, creative exploration, role selection,
prompt chaining, model judging, or repair reasoning, it belongs in the native
session and its repo skill—not in a new Python orchestration loop.

Do not extend the transitional `CodexStructuredRunner` stage agents. They exist
only until equivalent native-session paths are covered and can be removed.

## Where changes go

```text
.agents/product-run/AGENTS.md                  product-run constitution source
.agents/skills/autonomous-workshop/           native workflow instructions
src/cli/                                      host command entry points
src/workshop/runtime/                         native runtime and trusted state
src/workshop/workflow/                        lifecycle/checkpoint protocol
src/workshop/<stage>/                          stage contracts and exact tools
src/workshop/make/skills/                     domain skills owned by Make
src/workshop/integrations/                     external effect adapters
tests/<same-component>/                        component tests
tests/end_to_end/                              whole native-run acceptance
```

The `src/` layout stays. `workshop` is the one library namespace; component
folders do not move to repository-root Python packages. `cli` is a sibling
installed package under `src/`, and all CLI tests stay under top-level `tests/`.

## Engine portability

Codex is the first supported native engine. The stable seam is the run
workspace, compact outcome protocol, and start/resume adapter—not Codex prompt
syntax. A future Claude Code, OpenCode, Pi, or Hermes adapter must preserve the
same host-owned identity, gates, checkpoint, sandbox, and effect rules.

## Migration rule

ADR 0012 is the direction of travel even while transitional Python stage code
still exists. When old code and this boundary disagree, do not copy or extend
the old cognitive orchestration. Move the caller to the native-session path,
retain any useful deterministic contract or tool, add recovery tests, and then
delete the bypass once compatibility is proven.
