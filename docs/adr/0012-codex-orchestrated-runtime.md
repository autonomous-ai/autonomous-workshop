# ADR 0012: Codex-orchestrated native runtime

- Status: Accepted
- Date: 2026-08-26
- Owners: Workflow, Runtime, and lifecycle component maintainers
- Superseded in part by: ADR 0013 and ADR 0014

## Context

Autonomous Workshop is intended to harness a world-class coding agent using a
contributor's local subscription. The earlier Python implementation called
Codex for bounded structured answers from separate stage agents. That made
Python responsible for prompts, role views, candidate loops, semantic judging,
and repair strategy while reducing Codex to a response generator.

The useful boundary is the inverse: one native coding-agent session owns the
cognitive and tool-using work, while a small trusted host retains lifecycle,
exact-byte gates, durable state, security, and external effects.

## Decision

One Wish uses one persistent native Codex session. `workshop wish` creates and
populates a private product project at
`$WORKSHOP_HOME/runs/<wish-id>/workspace`, then launches the session with that
directory as its working directory before Match. `workshop resume`
continues the recorded session id through:

```text
Wish -> Match -> Invent -> Make <-> Playtest -> Release -> Deliver
```

The trusted host implementation is `workshop.workflow.native_run`. The CLI is
only its command-line adapter and does not own lifecycle or session behavior.

The host materializes a run-only `AGENTS.md`, the `autonomous-workshop` workflow
skill, Make domain skills, the exact Wish, and immutable declared Inventor
bundles. It projects every eligible Inventor into the official Codex
project-scoped custom-agent convention under `.codex/agents/`. Before each
native stage it writes a read-only `STAGE.json` bound to the current checkpoint
and gate subject.

The root Codex session is the Workshop Manager. It uses native subagents where
useful for bounded Match analysis, selected-Inventor work, and independent
inspection. Codex owns spawning, routing, waiting, and synthesis from the exact
project-scoped custom agents; Workshop does not launch separate OS-level Codex
processes or schedule a parallel agent system in Python.

The host may automatically continue a native stage turn only for a typed
launcher timeout or explicitly recognized provider-transport interruption
from the private launcher channel or Codex's documented terminal-error event,
only after the launcher's dedicated POSIX process session is proven empty, and
only when the exact session UUID is already durably checkpointed. It keeps the
exclusive run lock, applies bounded deterministic-jitter backoff, resumes that
same UUID against the unchanged stage subject, and charges the attempt to the
existing bounded native-turn budget. At most two consecutive recoverable turn
failures continue automatically in one command; an explicit operator resume
starts a fresh two-failure window against the same checkpoint. An unbound
interruption, unrecognized failed-turn event, unknown exit, unsafe termination,
contract/gate failure, or authorization/effect failure remains terminal for
that command. This recovery is transport control, not a Python reasoning or
improvement loop. The automatic recovery turn receives only fixed critical-path
control: reuse existing bytes, avoid restarting broad exploration, do not make
finalization depend on a child agent, and prioritize the remaining checks and
stage finalizer.

The portable cleanup guarantee covers every process group inside the launcher's
dedicated POSIX process session, including Codex's built-in code-mode helper.
Product-run instructions therefore forbid custom tools from daemonizing,
detaching, creating a new process session, or intentionally leaving background
work behind. The Codex adapter accepts only anchored recognized provider
diagnostics from private, bounded launcher or native-event fields. Those bytes
select a typed category and are immediately discarded. Generic diagnostics
remain an unknown failure and fail closed.

Codex uses native inspection, editing, shell, search, rendering, applicable
skills, and specialist delegation to perform Match reasoning, research,
concept selection, design, CAD, Playtest, repair, manual writing, and factual
product-page work. Substantive output stays in the run workspace.

For each Match, Invent, Make, Playtest, or Release attempt, Codex
creates one native Goal whose stopping condition is successful stage
finalization. Only one Goal is active at a time. Codex performs the observe,
act, evaluate, and improve cycle inside that Goal; Python does not emulate the
Goal or implement a reward, judge, research, or repair loop. Wish validation
and Deliver effects remain host boundaries and do not create agent Goals.

After authoring one stage, Codex invokes the materialized deterministic
`stage_proposal.py` finalizer. It validates and hashes exact bytes, writes the
canonical stage contract, and produces a checkpoint-bound
`agent-outcome.json`. The host independently rereads all cited bytes, reruns
trusted checks, seals accepted artifacts, and alone advances the checkpoint.
Make manifests and host gates bind every exact file and reject links or special
nodes. Byte-free directories are not artifacts; the finalizer prunes them when
permitted but does not fail merely because the native sandbox denies directory
unlink after derived cache files have been safely removed.
For a concrete operator or environment blocker, the same finalizer may instead
write one checkpoint-bound `waiting` or `failed` need with no artifact or
transition. The host applies that typed non-ready result, persists its bounded
reason in private checkpoint state, exposes it in immediate and later status
receipts, and stops. Resume clears a satisfied wait before reactivating the
same stage. Chat prose is not workflow state, and ordinary unfinished or
repairable work cannot use this exception.

### Host ownership

The outer Workshop host owns:

- Wish/run identity, lifecycle order, Make–Playtest rounds, invalidation, one
  exclusive host mutation lock per run, and durable checkpoints;
- native-session start/resume, scrubbed environment, and an enforced
  workspace-only filesystem permission profile;
- contracts, exact-byte manifests, deterministic CAD/evidence gates, and
  artifact sealing;
- authorization, credential isolation, idempotent effect intents, external
  adapters, reconciliation, and receipts;
- classification of waits, failures, unknown outcomes, and bounded recovery.

### Native-agent ownership

Codex owns:

- Workshop management, native subagent delegation, and synthesis;
- understanding the Wish and selecting a suitable immutable Inventor bundle;
- research, source provenance, concept exploration, and design;
- CAD/artifact creation, native tool and skill use, inspection, and repair;
- AI Playtest judgment and evidence-linked feedback without overriding
  deterministic results;
- the Release package (originally `MANUAL.md` and schema-v3 page content;
  superseded for new runs by the manual-first contract in ADR 0013), with every
  claim bound to sealed Made or Playtest evidence;
- compact needs and proposed transitions.

Model prose and self-assessment are untrusted. Python does not run a parallel
prompt chain, semantic judge, persona subprocess, candidate fan-out, or reward
loop.

An Inventor bundle keeps judgment in `TASTE.md`, stable source metadata and
exact skill-tree bindings in schema-v8 `inventor.json`, and may include an
inventor-owned Codex skill tree with `SKILL.md`, scripts, references, assets,
CAD generators, evaluators, or other tested deterministic tools. The host
projects those exact bytes into `.codex/agents/*.toml`, the sole run roster. A
native Inventor subagent reasons and invokes these resources. Custom code
cannot become an agent orchestrator, lifecycle engine, gate, or effect path.
The root Manager reviews child work; the host alone advances the checkpoint.

### Effects

Codex never receives effect credentials and cannot directly create remote
Factory state, publish, purchase, manufacture, buy postage, ship, or contact a
carrier. The CLI default is private. `--publish` records explicit prospective
authority for the host to promote the exact verified Factory page after
reconciled private import.

An ambiguous effect is reconciled before retry. If completion or absence
cannot be proved, the run stops unknown/needs-human. Publication never counts
as physical delivery evidence.

Every external adapter persists an intent and stable idempotency key before
the effect, reconciles completion through authenticated readback, and binds its
receipt to the exact request and artifact hashes. A command exit code or model
claim is never proof of publication, manufacture, shipment, or delivery. When
authenticated readback cannot prove either completion or absence, the adapter
must stop at unknown rather than retrying blindly.

## Alternatives rejected

### One structured model call per stage or reward step

Rejected because it discards native session continuity and requires Python to
reimplement reasoning and tool orchestration that the coding agent already
provides.

### Let Codex own lifecycle gates and effects

Rejected because prompt content or model error could bypass phase order,
artifact identity, authorization, idempotency, or reconciliation.

### Use the session transcript as durable state

Rejected because sessions can be truncated, unavailable, or inconsistent with
tool-written files. Exact workspace bytes and host receipts are authoritative.

### Build a custom Python search or multi-agent framework

Rejected because it duplicates the native runtime, increases attack surface,
and makes future engine substitution harder. This does not reject the coding
agent runtime's own bounded subagents.

## Consequences

Codex can do nearly all creative and diagnostic work with the same tools a
developer uses, while Workshop remains small and fail-closed. The filesystem
protocol and host gates provide an adapter seam for future Claude Code,
OpenCode, Pi, or Hermes runtimes.

Workshop deliberately inherits improvements to Codex's reasoning, tools,
Goals, and subagents instead of replacing them with a parallel framework. Its
own durable value is the product workflow, Inventor Taste, artifacts, evidence,
gates, and safety boundaries.

Python stage agents, profile subprocesses, `CodexStructuredRunner`, and numeric
Invent/reward loops are not part of the supported architecture and must not be
reintroduced as compatibility extensions. Useful deterministic contracts and
tools remain at their owning component boundaries.

## Verification

- One end-to-end Wish reuses one session id across all native stages.
- Each active cognitive stage uses one native Goal and completes it only after
  the deterministic finalizer succeeds.
- Native Inventor children use exact hash-bound bundles without launching a
  second root Codex process.
- Child agents and Inventor tools cannot advance gates or receive effect
  credentials.
- Resume uses the exact workspace and rejects changed materialized instructions.
- Stale checkpoint/subject bindings and changed artifact bytes fail closed.
- Failed Playtest evidence returns to Make or Invent according to its explicit
  structured invalidation boundary, consumes one shared round budget, and
  preserves the exact prior design and evidence lineage.
- Make and Playtest rerun host-owned CAD verification on exact bytes.
- Release claims exactly match the passing Playtest evidence.
- The native subprocess never receives effect credentials.
- Public promotion requires `--publish` and returns a reconciled, hash-bound
  receipt.
- Deliver cannot advance from mocked, digital, or page-only evidence.
