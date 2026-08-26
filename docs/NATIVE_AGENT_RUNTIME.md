# Native coding-agent runtime

This is the operating map for people and coding agents building Autonomous
Workshop. It is authoritative together with
[ADR 0012](adr/0012-codex-orchestrated-runtime.md) and the repository
[agent instructions](../AGENTS.md).

## Two different agent contexts

| Context | Purpose | Governing files |
|---|---|---|
| Repository builder | Builds, reviews, tests, or documents Workshop itself | root [`AGENTS.md`](../AGENTS.md) |
| Product run | Turns one exact Wish into one product in a persistent toy project | materialized [`.agents/product-run/AGENTS.md`](../.agents/product-run/AGENTS.md) and nested [`autonomous-workshop` skill](../.agents/product-run/.agents/skills/autonomous-workshop/SKILL.md) |

The root `AGENTS.md` is Codex's equivalent of repository-scoped contributor
guidance. It does not select a role or orchestrate a product. The product-run
constitution is copied into a separate toy project as that run's `AGENTS.md`; it
does not govern ordinary source-repository work.

## Runtime boundary

Every `workshop wish` first creates and populates one persistent toy project,
then launches one native Codex session in that directory before Match. That
same session performs all cognitive and tool-using work through Release:

```text
Wish -> Match -> Invent -> Make <-> Playtest -> Release -> Deliver
```

Codex owns understanding, native search, concept exploration, design, CAD and
artifact creation, render inspection, repair, AI Playtest judgment, manual
writing, and complete evidence-bound product-page content. Stages are durable
checkpoints, not separate model roles or one-shot API calls.

The root Codex session is the Workshop Manager. Native subagents are bounded
children it can use for parallel or specialist work; they do not create a
second product-run session or weaken the one-session continuity rule.

For each active Match, Invent, Make, Playtest, or Release attempt, the Manager
creates one native Codex Goal. Only one Goal is active. It binds one objective,
the current `STAGE.json`, proof artifacts and checks, and the verifiable
stopping condition that the stage finalizer succeeds. Codex observes, acts,
evaluates the actual artifact, and improves while pursuing that Goal. This is
native-agent behavior inside the Goal, not a Python loop. The Goal completes
only after the finalizer succeeds, then Codex returns to the host. Wish and
Deliver are host boundaries and do not receive agent Goals.

This follows Codex's official guidance for [durable
Goals](https://learn.chatgpt.com/use-cases/follow-goals) and [eval-driven
iteration](https://learn.chatgpt.com/use-cases/iterate-on-difficult-problems).

Python is the trusted host substrate only. It owns:

- Wish/run identity and exact input bytes;
- lifecycle order, Make–Playtest round budgets, invalidation, and one exclusive
  host mutation lock per run;
- native-session launch/resume, a scrubbed process environment, and an enforced
  exact-toy-root Codex permission profile that denies the surrounding checkout;
- typed contracts, artifact hashing, deterministic CAD/evidence gates, and
  durable checkpoints;
- authorization, credential isolation, idempotency, external adapters,
  reconciliation, and receipts.

Python does not choose research strategy, generate candidate concepts, act as
Inventors, judge semantic quality, run prompt chains, or implement a
reward loop. Model prose and self-assessment are proposals; only the host can
advance a gate.

## Start and resume

```text
workshop wish
    |
    v
host persists the canonical Wish and creates toys/<toy-id>/
    |
    +-- .workshop-product-run-root    immutable Codex project-root marker
    +-- AGENTS.md                     product-run constitution
    +-- .codex/agents/*.toml          project-scoped Inventor custom agents
    +-- .agents/skills/**             workflow and domain skills
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

`workshop resume <wish-id>` resumes the recorded session UUID in the same toy
project. Session memory is useful continuity, but the durable checkpoint,
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
    |       +-- exact embedded Taste judgment
    |       +-- required primary + optional additional Codex skills
    |       `-- hash-bound scripts/references/assets/deterministic tools
    |
    `-- optional independent inspection or Playtest subagents
```

The host projects every eligible Inventor into Codex's official
project-scoped custom-agent convention at `.codex/agents/<id>.toml`. Each file
binds the exact host-materialized identity, Taste, and declared skill paths.
That directory is the sole Inventor roster in the toy project. Codex owns
spawning, routing, waiting, and synthesis. Workshop does not spawn another
OS-level `codex` process: the host starts and resumes only the root product-run
session.

See the official Codex [Subagents and custom agents
documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
for the native file schema and orchestration behavior.

The source `inventors/<id>/` bundle contains:

- `TASTE.md`: creative judgment and rejection boundaries;
- schema-v8 `inventor.json`: stable source metadata and exact skill-tree
  hashes;
- required `skills/<id>-inventor/SKILL.md`: the specialist's primary procedure
  and resource routing;
- optional additional `skills/<id>-<specialty>/SKILL.md` trees;
- optional hash-bound scripts/references/assets and tested deterministic code:
  CAD generators, evaluators, or domain tools invoked by the native Inventor
  subagent.

The host admits only declared, validated, content-bound resources into the toy
project. Inventor code may implement specialist operations, but it may not
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

`inputs` contains the exact upstream contracts, artifact bindings, universal
blueprint, Inventor roster bindings, required checks, and canonical output
paths needed by the current stage. Codex must read it and must not edit it. A
stale proposal cannot be replayed because the host verifies both
`checkpoint_sha256` and `subject_sha256`.

The universal baseline comes from
`ToyBlueprint.required_playtest_checks()` and currently contains
`agent-playtest`, `mechanical-check`, and `printability-check`. Those are
Codex-authored digital assessments unless host-replayed evidence or an
authenticated physical receipt explicitly proves more. They cannot establish
successful printing, physical fit, durability, or human response by
themselves.

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
the current stage packet. It performs no improvement loop. After it succeeds,
Codex completes the active Goal and returns control. The host rereads the
proposal and artifact tree independently, reruns its trusted gates, seals all
accepted bytes, and alone decides the transition.

Playtest is the only backward transition: a verdict of `improve` or `block`
proposes Make and preserves exact evidence as feedback. The host applies the
round budget and invalidation; Codex interprets the feedback and performs the
repair in the next Make Goal. A new Make revision invalidates old Playtest and
Release evidence.

## Release and publication

Release replaces the former instruction-only stage because it owns more than an
instruction sheet. Codex prepares a complete schema-v3, page-ready package
rooted at `artifacts/release/package` with at least:

- `MANUAL.md`;
- canonical `product.json` with `kind=workshop.release-package`,
  `status=page-ready`, exact product/evidence hashes, evidence-bound claims,
  `title`, `summary`, `hero`, `cinematic`, `use_case`, one or more
  `story_blocks`, `what_arrives`, and `limitations`; each page section carries
  `headline`, `body`, `visual_direction`, and valid `evidence_refs`;
- any additional non-media supporting package files.

Codex authors the complete page copy and visual direction. It does not claim
publication, manufacture, physical performance, human response, or delivery.
The package cannot contain images, audio, video, remote-effect receipts, or
credentials. Factory transports the host-sealed page and model bytes without
creative enrichment.

The default CLI policy is private. `--publish` records explicit authority for
the host to promote the verified Factory page after the private import is
reconciled. Local credentials belong in the private
`$WORKSHOP_HOME/credentials/factory.env` file and are loaded lazily only after
the native turn exits. Codex 0.145.0 or newer runs with Workshop's strict
permission profile: all filesystem reads are denied by default, the exact
absolute toy project is writable, immutable instructions remain read-only,
only minimal tool paths are readable, and the surrounding checkout and sibling
toys stay denied. The immutable project-root marker also prevents builder
`AGENTS.md` inheritance, and dotenv files remain denied. Credentials
never enter the Codex subprocess, prompt, run artifacts, or status output.
Public publication is not evidence of physical manufacture or delivery.

## Materialized instructions and skills

Canonical product-run sources live at:

```text
.agents/product-run/AGENTS.md
.agents/product-run/.agents/skills/autonomous-workshop/**
src/workshop/make/skills/{cad,design-reference,image-to-cad,product-to-cad,step-parts}/**
inventors/<id>/{inventor.json,TASTE.md,skills/**}
```

At project creation the host also generates one deterministic
`.codex/agents/<id>.toml` for every eligible Inventor. It follows Codex's
project-scoped custom-agent schema and is derived from those exact source
bytes; it is not a second hand-written identity system.

Every Inventor declares one primary `<id>-inventor` skill tree. Additional
Inventor-prefixed trees and their scripts/resources are optional. Only exact
trees declared and hash-bound by the Inventor manifest are packaged,
materialized, and made available to a product run; none auto-run.

The installed package carries a byte-for-byte snapshot. At run creation the
host copies these into the toy project, hashes every instruction byte,
and binds that manifest to the run. Resume fails closed if the materialized
instructions changed. Do not install the project skill globally or maintain a
second hand-edited copy.

## Repository ownership

```text
toys/<toy-id>/                              persistent toy projects / Codex CWD
.agents/product-run/                        complete toy-project template source
  AGENTS.md                                 product-run constitution
  .agents/skills/autonomous-workshop/       native workflow instructions
inventors/<id>/                              reusable Taste, source manifest, and skills
src/cli/                                     parsing, presentation, and exit codes
src/workshop/runtime/                        session and trusted effect boundaries
src/workshop/workflow/native_run.py          trusted whole-run host composition
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
6. no credential reaches the native subprocess or its readable filesystem;
7. `--publish` is required for public promotion and the remote receipt binds
   the exact Release package; and
8. the run does not claim Deliver without physical receipts.

## Engine portability

| Manager runtime | Status |
|---|---|
| Codex | Implemented |
| Claude Code | Planned adapter |
| Grok Build | Planned adapter |

The stable seam is the persistent toy project, stage objective and proof
condition, `STAGE.json`, compact outcome protocol, start/resume adapter, and
bounded native-specialist delegation—not Codex prompt syntax or one vendor's
custom-agent file format. Every future adapter must preserve the root Manager
role, exact Inventor binding, host-owned gates, sandbox, checkpoint, and effect
authority.
