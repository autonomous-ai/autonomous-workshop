# Native coding-agent runtime

This is the operating map for people and coding agents building Autonomous
Workshop. It is authoritative together with
[ADR 0012](adr/0012-codex-orchestrated-runtime.md),
[ADR 0013](adr/0013-manual-first-release.md),
[ADR 0014](adr/0014-terminal-published-release.md),
[ADR 0015](adr/0015-defer-playtest.md),
[ADR 0016](adr/0016-selectable-effort-routes.md),
[ADR 0019](adr/0019-frozen-spark-economics-profile.md),
[ADR 0020](adr/0020-signature-experience-evidence.md),
[ADR 0021](adr/0021-compacted-spark-and-signature-review.md),
[ADR 0022](adr/0022-blind-review-before-final-verification.md),
[ADR 0023](adr/0023-bounded-spark-turn-and-semantic-review.md),
[ADR 0031](adr/0031-bind-deep-profile-and-bound-first-proof.md),
[ADR 0032](adr/0032-restore-make-depth-and-blindly-review-first-proof.md), and the repository
[agent instructions](../AGENTS.md). ADR 0013 supersedes ADR 0012's page-first
Release details; ADR 0014 supersedes their optional-publication and
executable-Deliver details; ADR 0016 supersedes ADR 0015's one fixed route.

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
freezes its effort, then launches one native Codex session in that directory
for the first enabled creative stage. That same session performs all cognitive
and tool-using work through Release:

```text
Spark: Wish -> Make -> Release
Forge: Wish -> Invent <-> Make -> Release
Quest: Wish -> Invent <-> Make <-> Playtest -> Release

Release -- handoff to Operations --> Printing -> Deliver -> Review
```

Codex owns understanding, native search, concept exploration, design, CAD and
artifact creation, render inspection, repair, printable manual design, and
bounded Release facts. Stages are durable
checkpoints, not separate model roles or one-shot API calls.

The root Codex session is the Workshop Manager. Native subagents are bounded
children it can use for parallel or specialist work; they do not create a
second product-run session or weaken the one-session continuity rule.

New Codex Spark projects freeze `spark-economics-v3.md` and run that one
session at low reasoning effort with a 64k automatic context-compaction ceiling
across Make and Release plus a 20-minute boundary per native turn. A timeout
uses the existing bounded recovery path to resume the exact session, Goal,
stage packet, and workspace; the boundary is not a stage deadline or a gate
waiver. New Forge and Quest projects freeze `deep-economics-v5.md`: Invent
starts with 20 minutes at high reasoning and a recoverable continuation gets
10 minutes at medium to seal existing work. Make starts with an eight-minute
medium proof phase at 24k, then the same Goal resumes at high reasoning for a
normal 30-minute turn after its checkpoint-bound proof marker exists.
Playtest and Release use medium, and every stage compacts at 24k. One CLI
invocation launches at most eight native turns across all stages. Make's first
persisted deliverable is the smallest exact causal/kinematic proof plus neutral
held/signature blockout evidence under the declared CAD project; the complete
part tree comes only after an independent native critic blindly reads those
images and checks the revealed Wish's exact held-form constraints. The marker
ends only that process turn; it is neither a gate nor a stage transition. Their extra work earns one
distinctive signature experience rather than gratuitous part or mechanism
count. Frozen deep-v4 runs retain high Invent/Make, medium later, 16k Make and
24k other-stage compaction, and their 12/30-minute Make boundaries. Frozen deep-v3 runs retain their high-Invent, medium-later 24k profile;
deep-v2 runs retain the effective all-high thread binding they started with;
deep-v1 and older runs retain their prior profile. A frozen v2 Spark
remains low with 64k compaction
and the historical timeout; v1 stays low without a Workshop-specified
compaction setting; an older unmarked Spark stays high. A host upgrade therefore
cannot change checkpoint-bound runtime policy. These profiles do not waive or
reduce any CAD, PDF, evidence, Playtest, or publication gate.

For each active Invent, Make, Playtest, or Release attempt,
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
- lifecycle order, retry budgets, invalidation, and one exclusive
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

A Wish command is a finite job, not a daemon. The host rejects new Wish
creation when macOS reports that it is running beneath a `grid.serve.*`
keepalive service, because every clean command exit would otherwise relaunch
the caller and allocate a different Wish id. Long-running foreground Wishes
must use Grid's bounded one-shot runner. Read-only status and explicit resume
retain their normal behavior.

A native turn timeout or explicitly recognized provider-transport disconnect
does not require a person to rerun the command after the session UUID has been
checkpointed. The disconnect may arrive either on the private launcher
diagnostic channel or in Codex's documented `turn.failed` / top-level `error`
JSONL shape. The launcher reports only those two cases through the typed
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
session for another turn. Two consecutive recoverable turn failures stop the
current command early with the same session checkpointed; an explicit
`workshop resume` starts a fresh two-failure recovery window. Every such turn
also consumes the existing 32-turn command budget. The delay is capped at 30
seconds and prevents a persistent provider outage or repeated profile-bound
timeout from becoming an unattended reconnect storm.
The one automatic recovery turn receives a fixed, non-cognitive instruction to
inspect and reuse existing bytes, keep the root Manager on the critical path,
avoid restarting broad exploration or depending on a child agent, run the
remaining essential deterministic checks, and prioritize the stage finalizer.

The private session checkpoint also binds the Codex CLI version and exact
runtime-policy hash. Deep-v3 and deep-v4 runs bind one immutable whole-profile
identity, allowing their promised stage-specific reasoning, compaction, and
turn boundaries without changing the persistent thread's security policy. A package manager may replace the installed CLI while a
long native turn is running. Resume accepts that drift only when the saved
checkpoint is intact, every Wish, constitution, path, permission-profile,
feature, and thread binding is unchanged, and the installed CLI is a strictly
newer supported version in the same major line. The resumed process receives
the newly computed current sandbox policy. Same-version policy drift, CLI
downgrades, major-version migrations, and malformed checkpoints still fail
closed.

An interruption before the exact session identity is bound fails closed rather
than automatically creating a second root session. Failed-turn events that do
not begin with an exact allowlisted provider-transport diagnostic, unknown or
malformed event streams, unsafe process termination, wrong session identity,
contracts, gates, authorization, credentials, and external effects are not
recoverable native-turn categories. If the interrupted turn already wrote a
checkpoint-bound `agent-outcome.json`, the host evaluates that proposal once
through the normal gate before considering any continuation. Provider
transport classification uses only exact anchored diagnostics on private,
bounded native channels. Diagnostic bytes select the typed category and are
then discarded; they are never persisted, returned, or treated as model
output. Generic or unrecognized diagnostics fail closed.

Codex has a suspected terminal-event compatibility issue that is not reproduced
by the currently retained mock-session rollouts. As a temporary fail-open, a
new exact regular in-run finalization marker that survives the bounded grace
period releases control only after the launcher safely reaps the complete
process session and has a valid bound session identity. The marker is not turn
or gate evidence. The host still parses the checkpoint/subject-bound proposal,
rehashes every cited artifact, runs the normal deterministic gate, and rejects
malformed, stale, or invalid bytes. If no proposal exists, an otherwise clean
missing-terminal outcome is temporarily recoverable only if that invocation
observed the valid native thread identity: the already checkpointed exact
session may resume under the unchanged checkpoint, subject, Goal, lock, and
bounded native-turn budget. Pre-identity wrapper or preflight failures, unsafe
reaping, malformed events, explicit failed turns, and other failures remain
fail-closed. The retained Quest failure was a test-wrapper packet-snapshot
collision, not evidence of an omitted terminal event. See
[`docs/backlog/codex-missing-turn-completed-after-subagents.md`](backlog/codex-missing-turn-completed-after-subagents.md).

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
buffer. The frozen per-run process timeout (20 minutes per v3 Codex Spark turn;
one hour for prior profiles), isolated-process cleanup, per-message limit, and
whole-run native-turn budget remain the surrounding resource bounds.

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

When a Manager's terminal event includes usage, Workshop also keeps one small
host-private aggregate by stage. Gross input and output remain separate. When
the runtime supplies the complete detail, schema v3 additionally preserves
cached input, cache-write input, and reasoning output; the public summary
derives uncached input and non-reasoning output without double-counting any
subset. Every view reports its own turn coverage as measured, partial, or
unavailable. Schema-v1 aggregates that collapsed both directions and schema-v2
aggregates without cache detail remain readable, but missing splits are never
guessed. This best-effort telemetry stores no prices, prompts, transcripts, or
reasoning content and cannot block or advance the lifecycle.

## Native subagents and Inventors

Inventor selection and specialist execution use the agent runtime's own
delegation rather than a Workshop scheduler:

```text
root Codex session: Workshop Manager
    |
    +-- optional bounded selection/candidate subagents
    |
    +-- selected Inventor subagent
    |       +-- exact embedded Taste judgment
    |       +-- required primary + optional additional Codex skills
    |       `-- hash-bound scripts/references/assets/deterministic tools
    |
    `-- optional independent inspection subagents
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

The Wish gate is host-validated before the first enabled native turn. Native
stage packets for new runs cover only the stages enabled by the frozen effort;
the host alone
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
  [--source <spark-creative-source.json>] \
  --product-root <product-root> \
  --cad-project-path <path-inside-product-root> \
  --cad-verification-path <path-inside-product-root>

"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . release \
  --package-root artifacts/release/package

"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . need --stage <current-stage> --status waiting \
  --reason "<one concrete condition required to continue>"
```

The standalone Match command is frozen-run compatibility. Effort-aware Invent
seals selection and invention together; Spark Make requires the optional source
shown above and seals selection, compact invention, and Made contracts together.

The tool does no research, reasoning, model calls, or gate advancement. It
validates authored inputs, hashes the exact run-local bytes, writes the
canonical stage contract, and atomically writes `agent-outcome.json` bound to
the current stage packet. It performs no improvement loop. After it succeeds,
Codex completes the active Goal and returns control. The host rereads the
proposal and artifact tree independently, reruns its trusted gates, seals all
accepted bytes, and alone decides the transition.

The `need` command is the non-ready exception: it writes one checkpoint-bound
`waiting` or `failed` reason with no artifact or transition, and the host stops
without treating chat prose as state. The bounded reason remains in private
checkpoint state and is printed by both the immediate command receipt and
later `workshop status`; a resume clears the satisfied waiting condition before
reactivating the same stage. Product-run instructions reserve this path for a
concrete operator or environment condition that prevents safe progress;
ordinary unfinished work and repairable validation or finalizer failures stay
inside the active Goal.

If a normal native turn returns before the Goal writes `agent-outcome.json`,
the host does not invent a result or require an immediate operator command. An
already checkpointed exact session is resumed automatically with the unchanged
stage subject and receives a fixed instruction that its finalizer has not yet
written the required proposal. Three consecutive normally returned turns
without a proposal stop the invocation early, mark progress failed, and report
the exact `workshop resume <wish-id>` command while preserving the checkpoint.
An explicit resume starts a fresh three-turn unfinished-work window in that
same root session. The independent 32-turn invocation budget still bounds all
native turns, including gate repairs and provider-transport continuations.
This unfinished-work continuation is not a lifecycle stage attempt. Missing
session identity and either bound exhaustion still fail closed.

Provider timeouts and recognized transport interruptions also stop an
invocation after two consecutive recoverable failures; an explicit resume
starts a fresh two-failure window.

For current Make and Playtest checkpoints, an otherwise bound proposal whose
agent-authored contract or artifact tree cannot be safely reopened is not
accepted and does not terminate the run. The host quarantines the exact
proposal in private state, records one of a fixed set of failure classes,
includes the rejection hash and actionable feedback in the next stage subject,
and resumes the same native session. Each checkpoint has an independent
32-rejection ceiling. A host-state conflict still fails closed. Current
Playtest finalizers also reopen and bind every canonical config before writing
`agent-outcome.json`, reducing the chance that an invalid proposal reaches the
host gate. Make applies the same bounded rejection path if a tool materializes
files after the finalizer inventories the product tree but before the host
performs its independent exact-file readback. Before that inventory, the Make
finalizer prunes empty directories when permitted and safely removes regular
files from `__cadgen__` runtime-cache trees inside the declared CAD project.
The independent `--fresh` verifier intentionally deletes and rebuilds those
cache bytes; sealing cache, lock, progress, or temporary files would guarantee
drift even when stable geometry reproduces. Some native sandboxes allow file
unlink but deny directory unlink. A remaining empty directory contains no
content-addressable bytes, so the finalizer and trusted host both ignore it
instead of blocking Make. STEP/STL/GLB exports, source, measurements, product
renders, every other file, symlinks, special nodes, and unsafe cache content
remain exact and fail-closed.
Frozen older finalizers may still require every empty directory to disappear.
Before their next Make resume, the trusted host holds the exclusive run lock
and prunes only real empty directories beneath the canonical current product
root. No native process is active; files and links are never removed or
followed. This compatibility cleanup does not rematerialize or mutate frozen
instructions.
The current Make finalizer additionally requires valid chromatic RGB/RGBA
presentation PNGs at `<cad-project>/snap/iso.png` (at least 800 px per side)
and `<cad-project>/snap/signature.png` (at least 1200 by 800 px). The latter
shows exact STL poses or views chosen to make the signature experience legible
without copy. The finalizer also requires hash-bound
`<cad-project>/snap/SIGNATURE-REVIEW.json` from one bounded independent native
visual critic. The critic first receives only the exact images and separately
records its unprompted held-object, volumetric-form, subject, action, and spatial
or causal relationship reads. Only then does the same critic learn the Wish and
canonical concept and compare each dimension plus the concept's anti-generic
signature with the promise. The hash-bound evidence confirms an
unmistakable, desirable final product; schema v6 also enumerates every explicit
positive and negative held-form requirement with blind visual evidence and
requires no blocking visual defect. One critic performs no more than two
rounds. Before this review, Make runs the fixed print-preflight mode: every
declared printable is generated, strict-fit checked, exported, mesh checked,
and thickness checked at the final 0.4 mm nozzle profile. The review binds the
passing preflight hash. Native iteration relies on source-closure freshness and
does not delete protected `__cadgen__` directories; the trusted host owns the
authoritative isolated `--fresh` rebuild. Make then performs one integrated final verifier, so a
printability repair cannot invalidate an already-spent visual read. The
materialized final verifier refuses to begin final-mode geometry work until the
canonical schema-v6 review and exact image hashes exist, then records the review
hash in its report. The finalizer rejects a second
final `snap/` family outside the declared CAD project. Those explicit paths are archived under
`make/verification/renders/`; the family is the only one eligible for automatic
README hero selection. Diagnostic silhouettes elsewhere remain evidence and
cannot be promoted accidentally.
The finalizer also requires the submitted verification report to be inside the
declared CAD project. This cheaply proves the agent verified the same
self-contained directory the host will later copy into isolation and rebuild.
It parses only the current report record and requires final mode, a passing
headline, a successful thickness row, and no thickness-skip flag. A prior pass
below a current failure or a locally omitted gate cannot become a Made proposal.
The run-local finalizer independently checks the bound preflight report, its
fixed 0.4 mm profile, and coverage for every `part_*.step.py` printable before
accepting the same proposal.

Host-selected product artifacts share the package contract's 95 MiB per-file
limit while the durable run retains its 128 MiB cumulative referenced-artifact
budget. This allows real CAD and render files larger than the former 16 MiB
contract mismatch without making storage unbounded.

For Invent, the finalizer also preserves the exact authored source bytes as
`source.json` beside the assignment and Invented contracts. The host requires
that artifact and independently proves that its selection, ranking, concept,
and research derive the two sealed contracts, so a post-finalizer source edit
cannot hide behind unchanged contract prose.

For Quest and frozen pre-ADR-0015 runs, Playtest owns its backward transitions. A
verdict of `improve` or `block`
preserves exact evidence and uses each feedback record's explicit invalidation
boundary to propose Make or Invent. `["playtest", "release"]` is an
implementation repair; `["invent", "make", "playtest", "release"]` is a
fundamental concept revision. If actionable findings use both, the broader
Invent revision wins. The host follows these authored markers without judging
their prose and applies one shared bounded round budget to both routes.

New Forge and Quest runs also freeze the Make-to-Invent revision capability.
When Make proves that the exact sealed concept prevents any conforming build,
the active Make Goal preserves a canonical evidence tree and proposes an exact
`NativeMakeInventRevision` contract. The host rehashes that evidence, binds the
Wish, assignment, and Invented identities, records a failed Make gate, consumes
the same shared round budget, invalidates Invent and every downstream stage,
and starts a new Invent Goal with the request. This route is block-only: normal
CAD defects remain Make's responsibility. Spark has no standalone Invent stage,
and older frozen runs without the capability marker cannot acquire the edge on
resume.

A Make repair keeps the sealed Invent result authoritative. A concept revision
receives the exact prior Invented plus either failing Playtested/feedback bytes
or the Make revision request, with independent hashes, then invalidates every
downstream product revision. New Make or Invent bytes invalidate their old
downstream evidence.

## Creative handoff and compound selection

Forge and Quest Invent own the product concept from roster selection through
research and final direction. Their `STAGE.json` binds the exact Wish, complete
Inventor roster, universal blueprint, and canonical assignment and Invented
paths. The one Invent finalizer seals both `NativeMatchAssignment` and
`NativeInvented`. Spark performs the same bounded selection and compact concept
handoff inside Make, sealing assignment, Invented, and Made contracts from one
turn. Python never chooses the Inventor or concept. The `NativeInvented` result
contains:

- `concept` — the selected product direction and the physical facts Make must
  preserve, including its form, envelope, components, construction, intended
  interaction, assumptions, and unresolved risks; and
- `research` — the sources, findings, and provenance that support the selected
  direction.

Forge/Quest Make receives that exact sealed Invent contract in its own
`STAGE.json`; Spark creates and consumes the compound creative source within
Make. The Made
contract binds the accepted Invent identity, while the host rehashes exact
product bytes and reruns deterministic CAD checks before advancing. No image
provider, separate drawing effect, or second model credential sits between
Invent and Make.

The host CAD gate retains two claim-bound tiers for historical protocols. Its
default/full tier reruns the
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
metadata does not separately request the lower tier. New direct-Release runs
require full-tier, print-ready-eligible CAD at Make and cannot advance on the
lower tier.

For frozen older runs, Make and Playtest replay evidence remain persisted under
separate host-owned stage paths. A Made revision accepted before the
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
- canonical product schema v5 bound to the exact Made product, contents,
  limitations, and `playtest_status: not-run`;
- canonical `PLAYTEST-NOT-RUN.json`, with no Playtest claims; and
- optional editable source or accessible text companions.

Spark/Forge use NativeRelease schema v3 with `MANUAL.pdf` and product schema
v5/`manual-ready`. Quest uses NativeRelease schema v2/product schema v4 bound
to passing Playtest evidence. Legacy NativeRelease schema v1
remains readable only with `MANUAL.md` and product schema v3/`page-ready`;
historical bytes retain their original validation and hashes.

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
and resumable; the durable effect ledger reconciles before retry. Local
credentials belong in the private `$WORKSHOP_HOME/credentials/factory.env`
file and are loaded lazily only after the native turn exits. One Workshop-owned
Factory service account publishes every Inventor's Release; Inventor provenance
remains independently sealed in the product facts and never selects
credentials. Codex 0.145.0 or newer runs with Workshop's strict
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
src/workshop/make/skills/{cad,design-reference,electromechanical-integration,
                          image-to-cad,step-parts}/**
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
4. each new run follows exactly its frozen Spark, Forge, or Quest route, with
   no artifacts or gates for passed-through stages;
5. every sealed Made result remains bound to the exact accepted Invent result
   it was built from;
6. Spark/Forge Release records Playtest as `not-run`; Quest Release binds its
   passing evidence; every exact `MANUAL.pdf` passes structural validation;
7. no credential reaches the native subprocess or its readable filesystem;
8. terminal Release requires exact full-tier print-ready CAD, validated
   `MANUAL.pdf`, and authenticated public readback bound to those hashes;
9. an optional Git snapshot can be retried after terminal Release and preserves
   every sealed Invent/Make/Playtest attempt, Make product render, revision
   request, and evidence tree without copying native-session or credential
   state; and
10. the executable Workshop run ends at Release and makes no claim of physical
    printing, delivery, or review.
11. a v3 Codex Spark run uses frozen low reasoning, its 64k compaction ceiling,
    and a 20-minute boundary per native turn across both active stages; v2, v1,
    and unmarked historical runs retain their prior exact runtime-policy
    bindings; and
12. a deep-v5 Codex Forge or Quest run uses bounded high Invent with decisive
    medium recovery, an eight-minute medium Make proof phase followed by
    high-reasoning final Make, medium later stages, 24k compaction, a 30-minute
    normal boundary, an eight-turn CLI invocation cap, and a checkpoint-bound
    proof-turn marker with no gate authority, while older exact runs retain
    their original profile.

## Engine portability

| Manager runtime | Status |
|---|---|
| Codex | Implemented default |
| Claude Code | Experimental adapter |
| Grok Build | Experimental adapter |

The stable seam is the persistent toy project, stage objective and proof
condition, `STAGE.json`, compact outcome protocol, start/resume adapter, and
bounded native-specialist delegation—not Codex prompt syntax or one vendor's
custom-agent file format. Every future adapter must preserve the root Manager
role, exact Inventor binding, host-owned gates, sandbox, checkpoint, and effect
authority.
