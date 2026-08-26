# Native coding-agent runtime

This is the operating map for people and coding agents building Autonomous
Workshop. It is authoritative together with
[ADR 0012](adr/0012-codex-orchestrated-runtime.md), its portable-runtime
amendment [ADR 0013](adr/0013-portable-workshop-managers.md), and the repository
[agent instructions](../AGENTS.md).

## Two different agent contexts

| Context | Purpose | Governing files |
|---|---|---|
| Repository builder | Builds, reviews, tests, or documents Workshop itself | root [`AGENTS.md`](../AGENTS.md) |
| Product run | Turns one exact Wish into one product in a persistent toy project | materialized [`AGENTS.md`](../.agents/product-run/AGENTS.md), `MANAGER.json`, and the selected projection of the canonical [`autonomous-workshop` skill](../.agents/product-run/.agents/skills/autonomous-workshop/SKILL.md) |

The root `AGENTS.md` is repository-scoped contributor guidance. It does not
select a Manager or orchestrate a product. The Manager-neutral product-run
constitution is copied into a separate toy project as that run's `AGENTS.md`;
the host also writes immutable `MANAGER.json` and the selected runtime's native
instruction entrypoint. Those product-run files do not govern ordinary
source-repository work.

## Runtime boundary

Every `workshop wish` first creates and populates one persistent toy project,
then launches one native session in the selected Manager runtime before Match.
Codex is the CLI default; `--manager claude` selects Claude Code. That same
runtime-native session performs all cognitive and tool-using work through
Release:

```text
Wish -> Match -> Invent -> Make <-> Playtest -> Release -> Deliver
```

The Claude adapter, CLI selection, deterministic projection, isolated API-key
profile, sandbox policy, stream attestation, and same-session
resume binding are implemented and covered by deterministic tests. A real
private Claude Wish has not yet completed the live acceptance bar below; the
implementation is therefore not yet described as production-validated.

The selected Manager owns understanding, native search, concept exploration,
design, CAD and artifact creation, render inspection, repair, AI Playtest
judgment, manual writing, and complete evidence-bound product-page content.
Stages are durable checkpoints, not separate model roles or one-shot API
calls.

The root coding-agent session is the Workshop Manager. Runtime-native
subagents are bounded children it can use for parallel or specialist work;
they do not create a second product-run session or weaken the one-session
continuity rule.

For each active Match, Invent, Make, Playtest, or Release attempt, the Manager
creates one native Goal through the selected Manager's goal control. Only one
Goal is active. It binds one objective, the current `STAGE.json`, proof
artifacts and checks, and the verifiable stopping condition that the stage
finalizer succeeds. The Manager observes, acts, evaluates the actual artifact,
and improves while pursuing that Goal. This is native-agent behavior inside
the Goal, not a Python loop. The native Goal reaches its stopping condition
only after the finalizer succeeds; the Manager then completes that native
control and returns to the host. This return is distinct from durable host
acknowledgement: an adapter Goal sidecar remains active until the host validates
the exact checkpoint-bound proposal. Wish and Deliver are host boundaries and
do not receive agent Goals.

For Codex, this follows its official guidance for [durable
Goals](https://learn.chatgpt.com/use-cases/follow-goals) and [eval-driven
iteration](https://learn.chatgpt.com/use-cases/iterate-on-difficult-problems).
Claude Code uses the same Workshop Goal contract through its native goal and
agent controls. The adapter sends `/goal <condition>` as the complete standard
input payload to `claude -p --input-format text` for a new attempt. An
interrupted attempt resumes with fixed ordinary continuation prose because
Claude restores the active Goal and another `/goal` would replace it. A private
stage/checkpoint-bound Goal sidecar records `prepared`, `active`, `returned`,
and host-acknowledged `completed`; Python does not emulate the Goal loop.

Python is the trusted host substrate only. It owns:

- Wish/run identity and exact input bytes;
- lifecycle order, Make–Playtest round budgets, invalidation, and one exclusive
  host mutation lock per run;
- native-session launch/resume, an allowlisted process environment, and an enforced
  exact-toy-root policy owned by the selected adapter that denies the
  surrounding checkout and fails closed when isolation is unavailable;
- typed contracts, artifact hashing, deterministic CAD/evidence gates, and
  durable checkpoints;
- authorization, credential isolation, idempotency, external adapters,
  reconciliation, and receipts.

Python does not choose research strategy, generate candidate concepts, act as
Inventors, judge semantic quality, run prompt chains, or implement a
reward loop. Model prose and self-assessment are proposals; only the host can
advance a gate.

## Start and resume

The diagnostic command checks installation, the minimum version, and the
selected Manager's authentication prerequisite without starting a paid model
turn. Codex checks its existing CLI login; Claude checks that
`ANTHROPIC_API_KEY` is available for the isolated Claude profile:

```bash
workshop doctor                    # Codex, the default
workshop doctor --manager claude   # Claude Code
```

```text
workshop wish [--manager codex|claude]
    |
    v
host persists the canonical Wish and creates toys/<toy-id>/
    |
    +-- .workshop-product-run-root    immutable project-root marker
    +-- AGENTS.md                     Manager-neutral constitution
    +-- MANAGER.json                  selected projection and Manager identity
    +-- WISH.json                     exact Wish
    +-- STAGE.json                    current host-written stage packet
    |
    +-- Codex projection
    |     +-- .codex/agents/*.toml
    |     `-- .agents/skills/**
    |
    `-- Claude Code projection
          +-- CLAUDE.md               imports the canonical AGENTS.md
          `-- .claude/                generated plugin, agents, and skills
    |
    v
host starts one selected Manager CLI session and records its private session id
    |
    v
Manager authors run-local artifacts and finalizes one compact proposal
    |
    v
host independently validates exact bytes, seals artifacts, and advances
```

The alternatives in the diagram are mutually exclusive for one run.
`MANAGER.json` and the schema-v4 host checkpoint persist the selection before
the first native turn. Codex stores its private session binding in
`codex-session.json`; Claude Code uses immutable `claude-session.json` plus a
mutable `claude-goal.json` attempt sidecar. The sidecar remains `active` across
an interrupted transport and becomes `completed` only after the host validates
the exact checkpoint-bound proposal. All live under the host-only state root,
not in the agent-visible toy project.

`workshop resume <wish-id>` has no Manager selector. It loads the persisted
Manager and resumes that runtime's recorded session id in the same toy project.
It never falls back to another runtime or starts a replacement just because a
checkpoint exists for a different adapter. Session memory is useful
continuity, but the durable checkpoint, sealed manifests, and reconciled
receipts remain authoritative. If memory and files disagree, the files win.

## Native subagents and Inventors

Match and specialist execution use the agent runtime's own delegation rather
than a Workshop scheduler:

```text
root selected-Manager session: Workshop Manager
    |
    +-- optional bounded Match/candidate subagents
    |
    +-- selected Inventor subagent
    |       +-- exact embedded Taste judgment
    |       +-- required primary + optional additional projected skills
    |       `-- hash-bound scripts/references/assets/deterministic tools
    |
    `-- optional independent inspection or Playtest subagents
```

The host projects every eligible Inventor into the selected runtime's native
agent format. Codex receives `.codex/agents/<id>.toml` and the corresponding
`.agents/skills/**` trees. Claude Code receives a host-generated plugin rooted
at `.claude/`, with `.claude/agents/<id>.md`, `.claude/skills/**`, and the
namespace declared by `MANAGER.json`. Each projected agent binds the exact
host-materialized identity, Taste, and declared skill paths. That selected
directory is the sole Inventor roster in the toy project. The Manager owns
spawning, routing, waiting, and synthesis. Workshop does not spawn another
OS-level coding-agent process: the host starts and resumes only the root
product-run session.

See the official Codex [Subagents and custom agents
documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
for Codex's native file schema and orchestration behavior. The Claude adapter
uses empty filesystem setting sources, private host-state directories, disabled
built-in agents, one exact host-projected plugin, strict empty MCP configuration,
and explicit tools. Claude's own bundled unnamespaced skills and slash commands
may still appear in init; because init does not distinguish their origin, the
adapter treats them as version-bound vendor surface and never as projected
plugin inventory. Before accepting a turn, the adapter attests the exact loaded
plugin, exact projected agent roster, exact normalized
`Agent,Bash,Edit,Skill,WebFetch,WebSearch,Write` tool roster, every expected
projected namespaced skill in both reported skill/command sets, no unexpected
namespaced entries, empty MCP, API-key source, model, session, all reported load
errors, and terminal result. The plugin tree is validated and hash-bound before
launch.

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
paths needed by the current stage. The selected Manager must read it and must
not edit it. A stale proposal cannot be replayed because the host verifies both
`checkpoint_sha256` and `subject_sha256`.

The universal baseline comes from
`ToyBlueprint.required_playtest_checks()` and currently contains
`agent-playtest`, `mechanical-check`, and `printability-check`. Those are
Manager-authored digital assessments unless host-replayed evidence or an
authenticated physical receipt explicitly proves more. They cannot establish
successful printing, physical fit, durability, or human response by
themselves.

The Wish gate is host-validated before the first native Match turn. Deliver is
also host/effect work; native stage packets currently cover Match, Invent,
Make, Playtest, and Release.

## Run-local proposal finalizer

The selected projection contains one exact copy of the proposal tool:

| Manager | Proposal tool |
|---|---|
| Codex | `.agents/skills/autonomous-workshop/scripts/stage_proposal.py` |
| Claude Code | `.claude/skills/autonomous-workshop/scripts/stage_proposal.py` |

After the Manager has authored the current stage's source files or artifact
tree, it runs that standard-library tool for exactly one stage. In the examples
below, `<proposal-tool>` means the exact path from the table and immutable
`MANAGER.json`:

```bash
python <proposal-tool> \
  --run-root . match --source <match-source.json>

python <proposal-tool> \
  --run-root . invent --source <invent-source.json>

python <proposal-tool> \
  --run-root . make \
  --product-root <product-root> \
  --cad-project-path <path-inside-product-root> \
  --cad-verification-path <path-inside-product-root>

python <proposal-tool> \
  --run-root . playtest \
  --source <playtest-source.json> \
  --evidence-root <evidence-root>

python <proposal-tool> \
  --run-root . release \
  --package-root artifacts/release/package
```

The tool does no research, reasoning, model calls, or gate advancement. It
validates authored inputs, hashes the exact run-local bytes, writes the
canonical stage contract, and atomically writes `agent-outcome.json` bound to
the current stage packet. It performs no improvement loop. After it succeeds,
the Manager completes the native Goal and returns control. The host then
validates the exact checkpoint-bound proposal and acknowledges the adapter's
durable Goal attempt before any gate mutation. It still rereads the proposal
and artifact tree independently, reruns its trusted gates, seals all accepted
bytes, and alone decides the transition.

Playtest is the only backward transition: a verdict of `improve` or `block`
proposes Make and preserves exact evidence as feedback. The host applies the
round budget and invalidation; the Manager interprets the feedback and performs
the repair in the next Make Goal. A new Make revision invalidates old Playtest
and Release evidence.

## Release and publication

Release replaces the former instruction-only stage because it owns more than an
instruction sheet. The Manager prepares a complete schema-v3, page-ready
package rooted at `artifacts/release/package` with at least:

- `MANUAL.md`;
- canonical `product.json` with `kind=workshop.release-package`,
  `status=page-ready`, exact product/evidence hashes, evidence-bound claims,
  `title`, `summary`, `hero`, `cinematic`, `use_case`, one or more
  `story_blocks`, `what_arrives`, and `limitations`; each page section carries
  `headline`, `body`, `visual_direction`, and valid `evidence_refs`;
- any additional non-media supporting package files.

The Manager authors the complete page copy and visual direction. It does not
claim publication, manufacture, physical performance, human response, or
delivery. The package cannot contain images, audio, video, remote-effect
receipts, or credentials. Factory transports the host-sealed page and model
bytes without creative enrichment.

The default CLI policy is private. `--publish` records explicit authority for
the host to promote the verified Factory page after the private import is
reconciled. Local credentials belong in the private
`$WORKSHOP_HOME/credentials/factory.env` file and are loaded lazily only after
the native turn exits.

Codex 0.145.0 or newer runs with Workshop's strict permission profile: all
filesystem reads are denied by default, the exact absolute toy project is
writable, immutable instructions remain read-only, only minimal tool paths are
readable, and the surrounding checkout and sibling toys stay denied.

Claude Code 2.1.246 or newer starts in an isolated non-bare profile with empty
filesystem setting sources, private `0700` `HOME`, `CLAUDE_CONFIG_DIR`, and
`CLAUDE_CODE_TMPDIR`, an available sandbox, the same exact-root/read-only-
instruction boundary, no shell network, disabled built-in agents, one generated
plugin, strict empty MCP, explicit tools, and the host system prompt. Its normal
user/project settings, agents, skills, hooks, memory, connectors, browser
control, plugins, and normal keychain/OAuth login path are not selected.
Claude's bundled unnamespaced skills and slash commands can remain visible as
version-bound vendor surface, not projection evidence. The init event must attest the exact
plugin, exact projected agents, exact normalized tool roster, all projected
namespaced skills, `/goal`, no unexpected namespaced entries, empty MCP,
API-key authentication, matching session/model/policy, and no reported load
errors before the turn is accepted.

OS-, MDM-, and server-managed Claude policy is deliberately part of the host
trusted computing base. Managed settings, managed `CLAUDE.md`, plugins, hooks,
and administrator policy can still apply at higher precedence. Claude's native
`/goal` command rejects `disableAllHooks`, so Workshop cannot use that setting;
empty filesystem setting sources exclude ordinary user/project hooks, while
managed hooks may still execute with the host user's authority. This profile
does not protect against a malicious or compromised host administrator.

The immutable project-root marker prevents builder-instruction inheritance,
and dotenv files remain denied. Codex uses its CLI-owned login environment. The
Claude parent process receives only `ANTHROPIC_API_KEY` for provider
authentication; Workshop intentionally does not admit `ANTHROPIC_AUTH_TOKEN`
or `CLAUDE_CODE_OAUTH_TOKEN`. Workshop explicitly binds
`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=0`: in Claude Code 2.1.246, enabling that
vendor feature silently forces the effective permission mode from `dontAsk`
to `default`, which fails the launch attestation. Instead, Claude's sandbox
credential policy denies the API key to Bash; ordinary hooks and stdio MCP are
absent from this profile, and managed hooks remain host-TCB code. On Linux,
the sandbox's deny-read-root policy also keeps `/proc` outside the explicit
read roots, so Workshop does not rely on the scrub feature's PID namespace.
Managed hooks run with the host user's authority and may inspect the API key or
other host-readable files; the adapter does not claim to sandbox trusted
administrator policy.
Claude's session and subagent transcripts remain plaintext beneath the private
configuration directory; `cleanupPeriodDays: 36500` prevents routine cleanup
from stranding the bound `--resume` session, so `0700` host-state permissions
are the at-rest boundary. Workshop does not add Factory credentials to either
Manager environment, prompt, sandbox-readable filesystem, run artifacts, or
status output; trusted managed hooks and host administrators are outside that
guarantee. Public publication is not evidence of physical manufacture or
delivery.

## Materialized instructions and skills

Canonical product-run sources live at:

```text
.agents/product-run/AGENTS.md
.agents/product-run/.agents/skills/autonomous-workshop/**
src/workshop/make/skills/{cad,design-reference,image-to-cad,product-to-cad,step-parts}/**
inventors/<id>/{inventor.json,TASTE.md,skills/**}
```

At project creation the host also generates one deterministic
`MANAGER.json` and exactly one runtime-native projection:

| Materialized concern | Codex | Claude Code |
|---|---|---|
| Instruction entrypoint | `AGENTS.md` | `CLAUDE.md` importing `AGENTS.md` |
| Inventor agents | `.codex/agents/<id>.toml` | `.claude/agents/<id>.md` |
| Workflow/domain/Inventor skills | `.agents/skills/**` | `.claude/skills/**` |
| Adapter support | strict policy passed by the CLI | isolated non-bare profile plus generated `.claude/.claude-plugin/plugin.json` and explicit host policy |

The host passes the Claude projection as the one explicit plugin directory;
Codex uses its project-scoped agent convention. Both projections are derived
from the same exact canonical source bytes. They are not second hand-written
identity or skill systems, and generated files must not be edited independently.

Every Inventor declares one primary `<id>-inventor` skill tree. Additional
Inventor-prefixed trees and their scripts/resources are optional. Only exact
trees declared and hash-bound by the Inventor manifest are packaged,
materialized, and made available to a product run; none auto-run.

The installed package carries a byte-for-byte snapshot. At run creation the
host copies these into the toy project, hashes every instruction byte,
and binds that manifest to the run. Resume fails closed if the materialized
instructions changed. Do not install the project skill globally or maintain a
second hand-edited copy.

## Asset evolution

### Implemented now: immutable per-run projections

The source of truth is the canonical root material: each
`inventors/<id>/inventor.json`, `TASTE.md`, and declared `skills/**` tree, plus
the product-run constitution/workflow skill and Make-owned domain skills. A
new Wish uses the latest validated bytes in the current source checkout or the
installed package snapshot. The host then generates the selected Manager's
project projection, records `MANAGER.json`, and binds every input path, mode,
size, and hash in the schema-v4 run checkpoint.

An active run does not follow later source changes. It resumes from its exact
materialized constitution, Taste, skills, native-agent files, Manager id, and
runtime-policy binding. A changed projection fails closed instead of being
silently refreshed. This preserves reproducibility and makes sealed artifacts,
gate evidence, effect receipts, and released history meaningful. Updating a
canonical Inventor or skill therefore affects future Wishes today, not an
already-running or released Wish.

### Target work: controlled upgrades between session epochs

Controlled upgrades for active runs are not implemented yet. The target
default is a host-enforced `follow-stable` policy evaluated at safe stage
boundaries, never during a native turn. It would resolve only a validated asset
release, seal the old projection, record an exact old-to-new hash transition,
apply invalidation rules, and start a new Manager session epoch bound to the
refreshed bytes. A project could explicitly pin a release for reproduction.
The old epoch and its evidence would remain auditable rather than being
rewritten.

“Latest validated stable” is a promoted channel, not repository `HEAD`.
Self-improvements and root asset edits first become candidates. Deterministic
schema validation, exact skill-lock verification, Manager-compatibility checks,
and regression tests must pass before the host atomically promotes one
content-addressed release. `follow-stable` resolves only that promoted release;
it never consumes an unreviewed self-edit or raw Git branch tip.

The upgrade must distinguish compatibility from semantic identity changes:

- a compatible skill, script, reference, asset, or deterministic-tool refresh
  may retain the same Inventor identity and exact Taste, while invalidating and
  rerunning every affected downstream artifact and gate;
- a changed `TASTE.md`, Inventor identity/manifest meaning, selected Manager,
  or incompatible workflow contract is semantic invalidation. It must return
  to an appropriate earlier decision boundary—potentially Match/Invent—or
  require a new Wish/run rather than pretending to be a skill refresh.

No future upgrade mechanism may hot-swap instructions or tools mid-turn,
continue under an unbound native session, silently rewrite a released package,
or alter historical evidence, receipts, or publication records.

## Repository ownership

```text
toys/<toy-id>/                              persistent toy projects / Manager CWD
.agents/product-run/                        canonical Manager-neutral source bundle
  AGENTS.md                                 product-run constitution
  .agents/skills/autonomous-workshop/       portable workflow source
inventors/<id>/                              reusable Taste, source manifest, and skills
src/cli/                                     parsing, presentation, and exit codes
src/workshop/runtime/managers.py             Manager registry and shared adapter port
src/workshop/runtime/{codex,claude}.py        concrete native session adapters
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

Deterministic Claude adapter, projection, CLI, checkpoint, and failure-path
tests pass. Live private-Wish acceptance is still pending because it requires
Claude Code at or above the documented version floor plus a real
`ANTHROPIC_API_KEY` in the host environment. The native-runtime cutover is
production-validated only when deterministic tests and a real private Wish
demonstrate that:

1. one selected-Manager session id spans every native stage;
2. one host-projected Inventor agent and at least one host-projected namespaced
   skill are each actually invoked, rather than merely reported in init;
3. stale checkpoint or subject hashes are rejected;
4. changed artifact bytes fail their next gate;
5. failed Playtest evidence returns to a new Make round and invalidates
   downstream work;
6. Release claims exactly match passing evidence;
7. sandboxed Bash cannot read the API key, Linux `/proc` environment, network,
   paths outside the run root, or any Factory/host-effect credential that
   Workshop controls;
8. `--publish` is required for public promotion and the remote receipt binds
   the exact Release package; and
9. the run does not claim Deliver without physical receipts.

## Engine portability

| Manager runtime | Status |
|---|---|
| Codex | Implemented |
| Claude Code | Adapter, CLI, and projection implemented; live private-Wish acceptance pending |
| Grok Build | Planned adapter |

The stable seam is the persistent toy project, stage objective and proof
condition, `STAGE.json`, compact outcome protocol, start/resume adapter, and
bounded native-specialist delegation—not prompt syntax or one vendor's
custom-agent/plugin file format. Every future adapter must preserve the root
Manager role, exact Inventor binding, host-owned gates, fail-closed sandbox,
checkpoint, same-manager resume, and effect authority.
