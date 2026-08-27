# Native coding-agent runtime

This is the operating map for people and coding agents building Autonomous
Workshop. It is authoritative together with
[ADR 0012](adr/0012-codex-orchestrated-runtime.md),
[ADR 0013](adr/0013-manual-first-release.md), and the repository
[agent instructions](../AGENTS.md). ADR 0013 supersedes ADR 0012's page-first
Release details.

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
Wish -> Match -> Invent -> Make <-> Playtest -> Release
                 ^                    |
                 `-- concept revision-'

Release -- handoff to Operations --> Printing -> Deliver -> Review
```

Codex owns understanding, native search, concept exploration, design, CAD and
artifact creation, render inspection, repair, AI Playtest judgment, printable
manual design, and bounded evidence-linked Release facts. Stages are durable
checkpoints, not separate model roles or one-shot API calls.

The root Codex session is the Workshop Manager. Native subagents are bounded
children it can use for parallel or specialist work; they do not create a
second product-run session or weaken the one-session continuity rule.

For each active Match, Invent, Make, Playtest, or Release attempt,
the Manager creates one native Codex Goal. Only one Goal is active. It binds one objective,
the current `STAGE.json`, proof artifacts and checks, and the verifiable
stopping condition that the stage finalizer succeeds. Codex observes, acts,
evaluates the actual artifact, and improves while pursuing that Goal. This is
native-agent behavior inside the Goal, not a Python loop. The Goal completes
only after the finalizer succeeds, then Codex returns to the host. Wish is a
host boundary and does not receive an agent Goal. Factory publication is the
host-owned effect portion of Release.

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
host persists the canonical Wish and creates
$WORKSHOP_HOME/runs/<wish-id>/workspace/
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

A native turn timeout or explicitly recognized provider-transport disconnect
does not require a person to rerun the command after the session UUID has been
checkpointed. The launcher reports only those two cases through the typed
`CodexRecoverableInvocationError` boundary, and only after proving that the
previous launcher's dedicated POSIX process session is empty. This includes
Codex's built-in code-mode host even though that helper creates a separate
process group inside the session. Product-run agents and custom tools are
forbidden from daemonizing, detaching, creating a new process session, or
intentionally leaving background work behind; the portable host boundary
cannot prove quiescence for a process that deliberately escapes it. While
retaining the same exclusive run lock, the host counts the
failed attempt, preserves the unchanged stage packet, waits a bounded
exponential delay with deterministic per-run jitter, and resumes that exact
session for another turn. This continuation consumes the existing
32-turn command budget and the normal Make-Playtest round budget; it does not
create a separate retry budget. The delay is capped at 30 seconds and prevents
a persistent provider outage from becoming a reconnect storm.

An interruption before the exact session identity is bound fails closed rather
than automatically creating a second root session. Failed-turn events, unknown
or malformed event streams, unsafe process termination, wrong session identity,
contracts, gates, authorization, credentials, and external effects are not
recoverable native-turn categories. If the interrupted turn already wrote a
checkpoint-bound `agent-outcome.json`, the host evaluates that proposal once
through the normal gate before considering any continuation. Provider
transport classification uses only exact anchored diagnostics on the private,
bounded launcher channel; generic or unrecognized stderr fails closed.

The launched process session is owned by an idempotent guard outside the event
parser's ordinary `Exception` classification. A graceful host unwind such as
Ctrl-C (`KeyboardInterrupt`) or `SystemExit` therefore terminates and reaps the
dedicated Codex process session across all of its process groups before
propagating the interruption. The host binds the session leader to its
launch-time process creation identity; ambiguous identity or numeric SID reuse
fails closed without signaling the replacement session. User cancellation is
not converted into an automatic transport retry: if the exact
session identity was already checkpointed, a later explicit `workshop resume`
continues it; otherwise the run remains fail-closed. No portable subprocess
guard can run after an uncatchable host death such as `SIGKILL` or power loss.

The JSONL event channel is reduced incrementally rather than accumulated as a
turn transcript. Each individual event has a hard byte limit and is decoded,
validated, classified into safe progress, and then discarded; an oversized or
malformed record still fails closed. A legitimate long turn may emit more than
that limit in aggregate because cumulative bytes consume no growing host
buffer. The one-hour process timeout, isolated-process cleanup, per-message
limit, and whole-run native-turn budget remain the surrounding resource bounds.

### Privacy-safe progress status

`workshop status <wish-id>` is read-only and never opens or resumes Codex. While
a native turn runs, the host reduces Codex JSONL events to one of eight coarse
classes: `starting`, `running`, `reasoning`, `tool`, `subagent`, `finalizing`,
`completed`, or `failed`. `running` is a five-second host heartbeat that means
only that the launched Codex process is still alive; it does not infer what the
model is doing. The host atomically stores only the current checkpoint binding,
attempted stage and attempt number, cumulative attempted-turn count, start time,
and last safe activity time in a private `0600` host-state record. Status
reports those fields plus elapsed seconds; it never stores or displays prompts,
messages, reasoning, tool arguments or output, paths, agent identities, thread
ids, or credentials.

Foreground `workshop wish` and `workshop resume` commands also render those
same content-free classes while the native turn is active. Repeated event
classes are collapsed, high-churn activity is rate-limited, and the five-second
liveness signal is printed at most once every 30 seconds. Long turns therefore
remain visibly alive without copying native event volume into the outer log. In
`--json` mode all live progress is flushed to stderr; stdout remains exactly one
final machine-readable JSON receipt. The renderer describes completed agent
messages only as progress reports: their content is neither exposed nor
interpreted as proof that the current stage is actually finishing.

All progress delivery is serialized on a bounded daemon queue; observer-owned
code never runs on the launcher thread. Terminal delivery waits only briefly
for a healthy local sink so ordinary status is deterministic. A permanently
stalled sink is then abandoned without delaying completion or failure of the
native turn. The queue is size-bounded, coalesces excess active updates, rejects
new active updates after terminal activity, and always orders the latest
terminal class last. Telemetry failure remains non-authoritative and cannot
change a lifecycle result.

Progress is diagnostic metadata, not gate evidence. A missing, stale,
malformed, tampered, wrong-mode, or symlinked progress record is shown only as
`unavailable`; Workshop neither trusts its fields nor lets it invalidate an
otherwise valid lifecycle checkpoint. The next host-owned native attempt may
replace unusable telemetry safely. `native_turns` is the durable cumulative
attempt count when trusted progress is available, including from read-only
status calls, rather than the number of turns launched by the status command.
Automatic timeout/transport continuations increment both `native_turns` and the
current stage-attempt number exactly like any other native turn. A separate
private generation floor makes those counters monotonic: a callback abandoned
by an earlier launcher may finish late, but its older record is no longer
trusted and cannot roll status backward.

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

The Wish gate is host-validated before the first native Match turn. Native
stage packets cover Match, Invent, Make, Playtest, and Release; the host alone
performs Release's authenticated publication effect.

## Run-local proposal finalizer

The product workspace contains:

```text
.agents/skills/autonomous-workshop/scripts/stage_proposal.py
```

After Codex has authored the current stage's source files or artifact tree, it
runs that deterministic tool for exactly one stage:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . match --source <match-source.json>

"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . invent --source <invent-source.json>

"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . make \
  --product-root <product-root> \
  --cad-project-path <path-inside-product-root> \
  --cad-verification-path <path-inside-product-root>

"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . playtest \
  --source <playtest-source.json> \
  --evidence-root <evidence-root>

"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
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

Playtest owns the backward transitions. A verdict of `improve` or `block`
preserves exact evidence and uses each feedback record's explicit invalidation
boundary to propose Make or Invent. `["playtest", "release"]` is an
implementation repair; `["invent", "make", "playtest", "release"]` is a
fundamental concept revision. If actionable findings use both, the broader
Invent revision wins. The host follows these authored markers without judging
their prose and applies one shared bounded round budget to both routes.

A Make repair keeps the sealed Invent result authoritative. A concept revision
receives the exact prior Invented and failing Playtested/feedback bytes with
independent hashes, then invalidates every downstream product revision. New
Make or Invent bytes invalidate their old downstream evidence.

## Invent-to-Make design handoff

Invent owns the product concept from research through selection. Its
`STAGE.json` binds the exact Wish, Match assignment, selected Taste, universal
blueprint, and canonical output path. Codex researches the Wish through its
own native capabilities, explores materially different directions, judges
them through the selected Inventor's Taste and method, and seals one
`NativeInvented` result containing:

- `concept` — the selected product direction and the physical facts Make must
  preserve, including its form, envelope, components, construction, intended
  interaction, assumptions, and unresolved risks; and
- `research` — the sources, findings, and provenance that support the selected
  direction.

Make receives that exact sealed Invent contract in its own `STAGE.json` and
must build from it rather than reinterpret the Wish from scratch. The Made
contract binds the accepted Invent identity, while the host rehashes exact
product bytes and reruns deterministic CAD checks before advancing. No image
provider, separate drawing effect, or second model credential sits between
Invent and Make.

The host CAD gate has two claim-bound tiers. Its default/full tier reruns the
materialized verifier with fresh generation, exports, strict fit, mesh, and
wall-thickness checks. A Made revision may use the lower
`digitally-verified-not-print-ready` tier only when two independently sealed
declarations agree: root `product.json.status` has that exact value and the
declared CAD-verification JSON contains the literal boolean
`final_pipeline.print_ready_claim: false`. Either declaration alone is a
contract mismatch and cannot waive a check. The lower tier adds only
`--skip-thickness`; generation, layout, fit, local spec audits, mount, motion,
kernel validation, interference, exports, and mesh checks remain gates. The
host receipt and stage-gate evidence record the lower tier, the distinct
verifier mode, and that it is not print-ready eligible. Historical or
unstructured receipts continue through the full tier when their product
metadata does not separately request the lower tier.

Make and Playtest replay evidence are persisted under separate host-owned
stage paths, so a Playtest timeout or rejection cannot overwrite the accepted
Make receipt needed by a later resume. A Made revision accepted before the
two-declaration policy may resolve only the exact historical
`digitally-verified-pending-physical-playtest` status plus literal false CAD
claim mismatch, and only when its immediate Make predecessor, checkpoint
history, exact contract/product hashes, schema-v1 CAD receipt, verifier hash,
and full command all agree. Playtest then reruns the full verifier, including
thickness, in isolation. That compatibility receipt remains ineligible for a
print-ready claim: stronger geometric replay does not erase the legacy
product's explicit uncertainty about slicing, physical printing, or fit.

## Terminal published Release

Codex prepares `artifacts/release/package` with at least:

- a self-contained printable `MANUAL.pdf` designed for the physical box;
- canonical `product.json` bound to the exact product, passing Playtest
  evidence, claims, contents, and limitations; and
- optional editable source or accessible text companions.

The current contract pair is NativeRelease schema v2 with `MANUAL.pdf` and
product schema v4/`manual-ready`. Legacy NativeRelease schema v1 remains
readable only with `MANUAL.md` and product schema v3/`page-ready`; legacy bytes
retain their original validation and hashes.

The materialized `manual-design` skill guides print-format choice, customer
copy, product-derived visuals, guided first use, complete reference, care and
safety, grayscale readability, and page-by-page visual review. Codex may use
embedded fonts, vectors, or raster images but cannot use external PDF
dependencies, active content, credentials, or remote receipts. The trusted
host parses, bounds, rehashes, and seals the exact PDF; it never scores beauty
or promotes digital evidence into a physical claim.

The PDF worker supports Linux and macOS. Linux requires `RLIMIT_AS`; macOS
skips only fully unbounded memory limits that Darwin cannot lower. Both retain
CPU, file, timeout, parser, and render bounds; other platforms fail closed.

Release completes only after the host replays full-tier,
thickness-checked, print-ready CAD, validates the exact `MANUAL.pdf`, imports
the exact CAD/manual handoff, publishes it, and verifies public page and manual
readback hashes. Missing credentials or a remote outage leaves Release waiting
and resumable; the durable effect ledger reconciles before retry. Local credentials belong in the private
`$WORKSHOP_HOME/credentials/factory.env` file and are loaded lazily only after
the native turn exits. Codex 0.145.0 or newer runs with Workshop's strict
permission profile: all filesystem reads are denied by default, the exact
absolute toy project is writable, immutable instructions remain read-only,
only minimal tool paths plus the identity-bound Workshop Python runtime and
launched Codex executable are readable, and the surrounding checkout and
sibling toys stay denied. The Codex grant is file-only and lets its built-in
sandboxed filesystem helper re-execute the already trusted binary for native
file tools such as `apply_patch` and `view_image`; it does not expose
`$CODEX_HOME` or the Codex package directory. The immutable project-root
marker also prevents builder `AGENTS.md` inheritance, and dotenv files remain
denied. Credentials never enter the Codex subprocess, prompt, run artifacts, or
status output.
Public publication is not evidence of physical manufacture or delivery.
For PDF-first publication, the host also downloads the exact immutable
`<project_url>MANUAL.pdf` from Factory's pinned public CDN without credentials
and hash-compares it with the sealed Release before accepting remote draft or
public evidence. The verified URL is exposed in status; this proves remote
manual bytes, not printing or box insertion.

Factory assigns an import with no category to its first active category.
Workshop therefore sends Factory's canonical `toys` slug explicitly instead
of accepting that order-dependent default. The authenticated private readback,
durable receipt, publication preflight, and public readback must all preserve
the same slug. If `toys` is no longer active, the import fails closed; Workshop
does not fall back to an unrelated category. Historical receipts that never
claimed a category remain readable under their original request semantics.

## Materialized instructions and skills

Canonical product-run sources live at:

```text
.agents/product-run/AGENTS.md
.agents/product-run/.agents/skills/autonomous-workshop/**
src/workshop/make/skills/{cad,design-reference,image-to-cad,step-parts}/**
src/workshop/release/skills/manual-design/**
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
$WORKSHOP_HOME/runs/<wish-id>/workspace/    private product run / Codex CWD
$WORKSHOP_HOME/state/<wish-id>/             trusted checkpoints and effects
toys/<inventor>-<slug>/                     sanitized public examples only
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
src/workshop/release/skills/manual-design/   reusable Release manual skill
src/workshop/integrations/                   credential-bearing host adapters
tests/<component>/                           component tests
```

The repository-owned
[`manual-design` skill](../src/workshop/release/skills/manual-design/) is
materialized into product runs; it is not a second workflow engine.

The `src/` layout and single `workshop` namespace stay. The `cli` package is an
installed sibling under `src/`; tests remain under top-level `tests/`.

## Acceptance bar

The native-runtime cutover is healthy only when deterministic tests and a real
private Wish demonstrate that:

1. one session id spans every native stage;
2. stale checkpoint or subject hashes are rejected;
3. changed artifact bytes fail their next gate;
4. failed Playtest evidence returns to Make or Invent exactly as its structured
   feedback declares, consumes the shared round budget, and invalidates the
   selected dependency chain;
5. every sealed Made result remains bound to the exact accepted Invent result
   it was built from;
6. Release claims exactly match passing evidence and its exact `MANUAL.pdf`
   passes bounded structural validation;
7. no credential reaches the native subprocess or its readable filesystem;
8. terminal Release requires exact full-tier print-ready CAD, validated
   `MANUAL.pdf`, and authenticated public readback bound to those hashes; and
9. the executable Workshop run ends at Release and makes no claim of physical
   printing, delivery, or review.

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
