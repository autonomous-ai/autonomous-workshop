# Native coding-agent runtime

This is the operating map for people and coding agents building Autonomous
Workshop. It is authoritative together with
[ADR 0012](adr/0012-codex-orchestrated-runtime.md) and the repository
[agent instructions](../AGENTS.md).

## Two different agent contexts

| Context | Purpose | Governing files |
|---|---|---|
| Repository builder | Builds, reviews, tests, or documents Workshop itself | root [`AGENTS.md`](../AGENTS.md) |
| Product run | Turns one exact Wish into one product in a private workspace | materialized [`.agents/product-run/AGENTS.md`](../.agents/product-run/AGENTS.md) and [`autonomous-workshop` skill](../.agents/skills/autonomous-workshop/SKILL.md) |

The root `AGENTS.md` is Codex's equivalent of repository-scoped contributor
guidance. It does not select a role or orchestrate a product. The product-run
constitution is copied into a separate run root as that run's `AGENTS.md`; it
does not govern ordinary source-repository work.

## Runtime boundary

Every `workshop wish` launches one native Codex session before Match. That same
session performs all cognitive and tool-using work through Release:

```text
Wish -> Match -> Invent -> Make <-> Playtest -> Release -> Deliver
```

Codex owns understanding, native search, concept exploration, design, CAD and
artifact creation, render inspection, repair, AI Playtest judgment, manual
writing, and factual product-page content. Stages are durable checkpoints, not
separate model personas or one-shot API calls.

The root Codex session is the Workshop Manager. Native subagents are bounded
children it can use for parallel or specialist work; they do not create a
second product-run session or weaken the one-session continuity rule.

Python is the trusted host substrate only. It owns:

- Wish/run identity and exact input bytes;
- lifecycle order, Make–Playtest round budgets, invalidation, and leases;
- native-session launch/resume and a scrubbed process environment;
- typed contracts, artifact hashing, deterministic CAD/evidence gates, and
  durable checkpoints;
- authorization, credential isolation, idempotency, external adapters,
  reconciliation, and receipts.

Python does not choose research strategy, generate candidate concepts, act as
Inventor profiles, judge semantic quality, run prompt chains, or implement a
reward loop. Model prose and self-assessment are proposals; only the host can
advance a gate.

## Start and resume

```text
workshop wish
    |
    v
host persists the canonical Wish and creates a private run root
    |
    +-- AGENTS.md                     product-run constitution
    +-- .agents/skills/**             workflow and domain skills
    +-- catalog/inventors/**          immutable declared specialist bundles
    +-- WISH.json                     exact Wish
    +-- STAGE.json                    current host-written stage packet
    |
    v
host starts one native Codex CLI session and records its session UUID
    |
    v
Codex authors run-local artifacts and finalizes one compact proposal
    |
    v
host independently validates exact bytes, seals artifacts, and advances
```

`workshop resume <wish-id>` resumes the recorded session UUID in the same
workspace. Session memory is useful continuity, but the durable checkpoint,
sealed manifests, and reconciled receipts remain authoritative. If memory and
files disagree, the files win.

## Native subagents and Inventors

Match and specialist execution use the agent runtime's own delegation rather
than a Workshop scheduler:

```text
root Codex session: Workshop Manager
    |
    +-- optional bounded Match/candidate subagents
    |
    +-- selected Inventor subagent
    |       +-- exact TASTE.md judgment
    |       +-- optional inventor-owned Codex skills
    |       `-- hash-bound scripts/references/assets/deterministic tools
    |
    `-- optional independent inspection or Playtest subagents
```

V1 creates these specialists dynamically and briefs them from exact
host-materialized bytes. It does not depend on unfinished or undocumented
named custom-role configuration. It also does not spawn another OS-level
`codex` process: the host starts and resumes only the root product-run session.

The source `inventors/<id>/` bundle separates four concerns:

- `TASTE.md`: creative judgment and rejection boundaries;
- `inventor.json`: identity, eligibility, capabilities, and declared extension
  inventory;
- optional `skills/<inventor-skill>/SKILL.md`: specialist procedures and how to
  use its resources;
- optional hash-bound scripts/references/assets and tested deterministic code:
  CAD generators, evaluators, or domain tools invoked by the native Inventor
  subagent.

The host admits only declared, validated, content-bound resources into the run
workspace. Inventor code may implement specialist operations, but it may not
call an agent runtime, schedule prompts, select lifecycle transitions, waive a
gate, access credentials, or perform external effects.

The root Manager owns delegation, synthesis, the current `STAGE.json`, and the
single finalizer invocation. Child agents may analyze or author bounded
run-local artifacts, but they cannot advance a stage. The outer Workshop host
remains the actual lifecycle, gate, and effect authority.

## The `STAGE.json` protocol

Before every native turn, the host atomically writes a read-only `STAGE.json`.
It binds the current stage to the current checkpoint and gate subject. Its
top-level fields are:

```text
schema_version, kind, product_id, stage, checkpoint_sha256,
subject_sha256, next_transition, round, max_rounds, inputs
```

`inputs` contains the exact upstream contracts, artifact bindings, catalog
snapshot, lane blueprint, required capabilities, and canonical output paths
needed by the current stage. Codex must read it and must not edit it. A stale
proposal cannot be replayed because the host verifies both
`checkpoint_sha256` and `subject_sha256`.

The Wish gate is host-validated before the first native Match turn. Deliver is
also host/effect work; native stage packets currently cover Match, Invent,
Make, Playtest, and Release.

## Run-local proposal finalizer

The product workspace contains:

```text
.agents/skills/autonomous-workshop/scripts/stage_proposal.py
```

After Codex has authored the current stage's source files or artifact tree, it
runs that standard-library tool for exactly one stage:

```bash
python .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . match --source <match-source.json>

python .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . invent --source <invent-source.json>

python .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . make \
  --product-root <product-root> \
  --cad-project-path <path-inside-product-root> \
  --cad-verification-path <path-inside-product-root>

python .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . playtest \
  --source <playtest-source.json> \
  --evidence-root <evidence-root>

python .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . release \
  --package-root artifacts/release/package
```

The tool does no research, reasoning, model calls, or gate advancement. It
validates authored inputs, hashes the exact run-local bytes, writes the
canonical stage contract, and atomically writes `agent-outcome.json` bound to
the current stage packet. Codex then returns control. The host rereads the
proposal and artifact tree independently, reruns its trusted gates, seals all
accepted bytes, and alone decides the transition.

Playtest is the only backward transition: a verdict of `improve` or `block`
proposes Make and preserves exact evidence as feedback. A new Make revision
invalidates old Playtest and Release evidence.

## Release and publication

Release replaces the former instruction-only stage because it owns more than an
instruction sheet. Codex prepares a local factual package rooted at
`artifacts/release/package` with at least:

- `MANUAL.md`;
- canonical `product.json` with product facts, evidence-bound claims, page
  metadata, and pending Factory enrichment;
- any additional non-media factual package files.

The agent does not claim Factory copy, images, publication, manufacture, or
delivery. The package cannot contain remote-effect receipts or credentials.

The default CLI policy is private. `--publish` records explicit authority for
the host to promote the verified Factory page after the private import is
reconciled. Credentials remain in the host process and never enter the Codex
subprocess, prompt, run artifacts, or status output. Public publication is not
evidence of physical manufacture or delivery.

## Materialized instructions and skills

Canonical product-run sources live at:

```text
.agents/product-run/AGENTS.md
.agents/skills/autonomous-workshop/**
src/workshop/make/skills/{cad,product-to-cad,step-parts}/**
inventors/<id>/{inventor.json,TASTE.md,skills/**}
```

Inventor skill trees are optional. Only exact trees declared and hash-bound by
the Inventor manifest are packaged, materialized, and made available to a
product run; none auto-run.

The installed package carries a byte-for-byte snapshot. At run creation the
host copies these into the private workspace, hashes every instruction byte,
and binds that manifest to the run. Resume fails closed if the materialized
instructions changed. Do not install the project skill globally or maintain a
second hand-edited copy.

## Repository ownership

```text
.agents/product-run/                         product-run constitution source
.agents/skills/autonomous-workshop/          native workflow instructions
inventors/<id>/                              specialist identity and declared extensions
src/cli/                                     thin host commands
src/workshop/runtime/                        session and trusted effect boundaries
src/workshop/workflow/                       lifecycle and checkpoint protocol
src/workshop/<stage>/                        contracts and deterministic gates
src/workshop/make/skills/                    reusable Make domain skills
src/workshop/integrations/                   credential-bearing host adapters
tests/<component>/                           component tests
```

The `src/` layout and single `workshop` namespace stay. The `cli` package is an
installed sibling under `src/`; tests remain under top-level `tests/`.

## Acceptance bar

The native-runtime cutover is healthy only when deterministic tests and a real
private Wish demonstrate that:

1. one session id spans every native stage;
2. stale checkpoint or subject hashes are rejected;
3. changed artifact bytes fail their next gate;
4. failed Playtest evidence returns to a new Make round and invalidates
   downstream work;
5. Release claims exactly match passing evidence;
6. no credential reaches the native subprocess;
7. `--publish` is required for public promotion and the remote receipt binds
   the exact Release package; and
8. the run does not claim Deliver without physical receipts.

## Engine portability

Codex is the first supported engine. The stable seam is the private workspace,
`STAGE.json`, compact outcome protocol, start/resume adapter, and a bounded
native-specialist delegation primitive—not Codex prompt syntax or one vendor's
named-role configuration. A future Claude Code, OpenCode, Pi, or Hermes adapter
must preserve the same root Manager identity, exact Inventor bundle,
host-owned gates, sandbox, checkpoint, and effect authority.
