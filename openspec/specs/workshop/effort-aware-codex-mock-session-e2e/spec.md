## Purpose

Defines a bounded acceptance tier in which authenticated Codex interprets the materialized effort-aware Workshop context and drives minimal valid outputs through the real production lifecycle without making live external effects.

## Requirements

### Requirement: Each acceptance run uses one real persistent Codex session
The mock-session E2E SHALL launch a supported authenticated Codex runtime through the production native-session protocol. For one Wish, it SHALL start exactly one session at the first enabled creative stage and resume that exact session identity at every later enabled agent stage. It MUST NOT substitute a scripted native executable, recorded response, structured model call, in-process stage agent, or directly injected stage outcome.

#### Scenario: Route completes in one session
- **WHEN** a contributor runs an enabled mock-session route with a supported authenticated Codex installation
- **THEN** the first enabled creative stage starts one real session and every later enabled stage resumes its recorded identity through terminal Release

#### Scenario: Session identity changes
- **WHEN** a later stage starts a new session or resumes an identity other than the checkpoint-bound session
- **THEN** the run fails with the expected and observed session bindings

### Requirement: Production context remains the source of stage behavior
Codex SHALL receive the normal materialized product-run `AGENTS.md`, declared skills and references, Inventor roster, exact Wish, current host-written `STAGE.json`, accepted upstream artifacts, and production stage prompt. A versioned acceptance overlay MAY request minimal mock work and prohibit costly or external activity, but it MUST NOT restate stage-specific input schemas, output schemas, finalizer subcommands, lifecycle transitions, ownership rules, or effort routing.

#### Scenario: Materialized context is sufficient
- **WHEN** Codex handles an enabled stage
- **THEN** it discovers the applicable production instructions and stage inputs, authors stage-appropriate minimal output, and invokes the normal materialized finalizer without a duplicated recipe from the test overlay

#### Scenario: Required context is missing or contradictory
- **WHEN** a required production instruction, declared skill, stage input, or accepted upstream artifact is absent, stale, unreadable, undiscoverable, or contradictory
- **THEN** the stage fails with diagnostics identifying the unresolved production context instead of the overlay supplying the missing rule

#### Scenario: Prohibited agent activity is observed
- **WHEN** the native event stream shows web activity, a non-loopback external request, credential solicitation, or unnecessary subagent delegation
- **THEN** the acceptance run fails and identifies the responsible stage and activity

### Requirement: Acceptance coverage matches the frozen effort routes
The acceptance tier SHALL cover the exact enabled stage topology of all current effort modes. Spark SHALL visit Make and Release; Forge SHALL visit Invent, Make, and Release; Quest SHALL visit Invent, Make, Playtest, and Release. No route SHALL create a standalone Match or Concept turn, and passed-through stages MUST NOT create an authored source, contract, gate, evidence receipt, or native turn.

#### Scenario: Spark route is accepted
- **WHEN** the acceptance runner executes a Spark Wish
- **THEN** Make folds the roster-bound assignment and compact Invented contract into its proposal, Release records canonical Playtest `not-run`, and the trace is exactly Make then Release

#### Scenario: Forge route is accepted
- **WHEN** the acceptance runner executes a Forge Wish
- **THEN** Invent folds Inventor selection into its proposal, Release records canonical Playtest `not-run`, and the trace is exactly Invent, Make, then Release

#### Scenario: Quest route is accepted
- **WHEN** the acceptance runner executes a Quest Wish without repair feedback
- **THEN** Invent folds Inventor selection into its proposal and the trace is exactly Invent, Make, Playtest, then Release with Release bound to passing Playtest evidence

#### Scenario: Passed-through stage leaves residue
- **WHEN** a route produces a Match or Concept turn, an omitted Invent or Playtest artifact, or evidence representing an omitted stage as passed
- **THEN** the route fails topology and truthful-omission validation

### Requirement: Every enabled stage supplies byte-bound context-use evidence
Before finalization, Codex SHALL write one bounded test-only context record bound to the current stage, checkpoint digest, subject digest, consulted production instruction bytes, used `STAGE.json` inputs, selected minimal-output strategy, and agent-owned outputs. The runner SHALL independently validate every path and digest, using final output bytes and run-root stage bindings only; model prose or stale intermediate bytes MUST NOT satisfy the proof.

#### Scenario: Context proof matches accepted output
- **WHEN** a stage passes its production gate
- **THEN** its context record matches the current packet, cites applicable run-root instructions and inputs, and binds the final source bytes submitted by the finalizer

#### Scenario: Output changes after proof is recorded
- **WHEN** a cited output is modified between context-record creation and host validation
- **THEN** the stage fails even if an earlier version of the source had the recorded digest

#### Scenario: Proof cites a non-run binding
- **WHEN** a context record cites a checkout file, harness fixture, missing path, stale checkpoint, unrelated input, or output outside the current run root
- **THEN** the runner rejects the record with the mismatched binding

### Requirement: Mock work preserves production ownership, gates, and terminal Release
Acceptance mode SHALL reduce only substantive agent work. Codex SHALL author valid agent-owned sources and invoke the run-local finalizer; the production host SHALL parse proposals, reread exact bytes, execute contracts and gates, rerun full-tier CAD verification in every applicable Make, Playtest, and Release gate, validate the Release PDF, seal artifacts, mutate checkpoints, and complete required Factory publication with authenticated public hash readback. Test helpers MUST NOT write checkpoints, gates, sealed artifacts, verifier evidence, effect intents, receipts, or other host-owned state.

#### Scenario: Minimal output passes production boundaries
- **WHEN** Codex authors the smallest valid context-derived artifact set for an enabled stage
- **THEN** the normal finalizer and production host gates accept or reject it without a mock-specific production shortcut

#### Scenario: Release reaches the current terminal state
- **WHEN** a route's Release proposal is valid and the local Factory protocol completes import, publication, reconciliation, and public byte readback
- **THEN** the checkpoint reaches terminal published Release with receipts bound to the exact CAD, package, page, and manual bytes

#### Scenario: Helper crosses a write boundary
- **WHEN** an acceptance helper or protocol fixture writes an agent proposal or any host-owned artifact, checkpoint, evidence, intent, or receipt
- **THEN** the run fails its write-ownership audit

#### Scenario: Codex finalizes but omits its terminal event
- **WHEN** Codex writes a new exact regular checkpoint-bound `agent-outcome.json` but does not emit `turn.completed` before the bounded finalization grace expires
- **THEN** the launcher safely reaps the complete process session and returns control to the normal host proposal reader, which independently accepts or rejects the exact bytes through unchanged production gates

#### Scenario: Missing terminal has no exact proposal marker
- **WHEN** the terminal event is absent, no new exact regular proposal exists, the process session is safely reaped, and the exact native session identity was already checkpointed
- **THEN** the outcome is recoverable only by boundedly resuming that same session under the unchanged checkpoint, subject, Goal, and mutation lock

#### Scenario: Missing terminal cannot be recovered safely
- **WHEN** the terminal event is absent and the session identity was never bound, cleanup is unsafe, the event stream is malformed, or Codex reports an explicit failed turn
- **THEN** the native session remains fail-closed

### Requirement: External effects are local, deterministic, and credential-isolated
The mock-session E2E MUST NOT call a live Factory, provider, publication, manufacture, postage, carrier, or other external service. Required Factory behavior SHALL use deterministic loopback responses only at the production adapter's outbound remote transport seams, while retaining credential parsing, idempotency, durable intent, reconciliation, receipt validation, publication, and exact public readback. Fixture credentials MUST remain absent from prompts, native process environments, agent-readable workspace files, context records, and diagnostics.

#### Scenario: Factory publication uses loopback transport
- **WHEN** Release requires import and public promotion
- **THEN** the production Factory coordination communicates only through the configured loopback transport and verifies the returned public bytes

#### Scenario: Fixture secret reaches Codex-readable state
- **WHEN** a fixture credential appears in a prompt, native process environment, agent-owned file, context record, or unredacted diagnostic
- **THEN** the acceptance run fails its credential-isolation audit

#### Scenario: Live external target is requested
- **WHEN** any acceptance transport attempts a non-loopback destination
- **THEN** the run stops before the request and reports the destination class without exposing credentials

### Requirement: Execution is opt-in, bounded, diagnostic, and non-required
The repository SHALL provide a documented local command with preflight checks, explicit effort selection, isolated private state, per-turn and whole-run budgets, safe owned-process termination, redacted retained failure diagnostics, and a concise stage report. The live scenario SHALL remain excluded from ordinary credential-free CI and repository automation. Operator-run credentialed execution SHALL support Spark, Forge, and Quest, while offline harness and policy tests remain eligible for ordinary CI.

#### Scenario: Local route succeeds
- **WHEN** an authenticated contributor explicitly runs one effort route within its budgets
- **THEN** the report includes the frozen effort, Codex model and reasoning effort, stage trace and durations, one start plus expected resumes, context-proof count, terminal checkpoint, publication result, and total elapsed time

#### Scenario: Operator runs the route matrix
- **WHEN** an operator invokes the credentialed command independently for Spark, Forge, and Quest
- **THEN** it produces independently reported scenarios without adding repository automation or making the live tier a required pull-request check

#### Scenario: Prerequisite is unavailable
- **WHEN** Codex is missing, unsupported, or unauthenticated, or the loopback fixture cannot start
- **THEN** preflight exits nonzero before reporting a partial acceptance success and names the failed prerequisite

#### Scenario: Runtime budget is exceeded
- **WHEN** a native turn or complete route exceeds its configured budget
- **THEN** the runner terminates only its owned process tree, preserves redacted diagnostics and isolated state, and exits nonzero

### Requirement: Acceptance evidence has a narrow meaning
A successful mock-session run SHALL mean only that authenticated Codex discovered and interpreted supplied context well enough to author minimal valid outputs through production boundaries for the selected route. Reports and documentation MUST NOT present success as evidence of creative quality, research quality, exhaustive agent behavior, physical printing, fit, durability, manufacture, shipment, delivery, or human response, and MUST distinguish this tier from deterministic CI and full product validation.

#### Scenario: Acceptance report is emitted
- **WHEN** a mock-session route reaches terminal Release
- **THEN** its report labels the result as context-and-integration acceptance and states the evidence limitations

#### Scenario: Ordinary CI runs without Codex credentials
- **WHEN** the required offline test suite runs
- **THEN** no live Codex scenario or credential is required and deterministic E2E remains independently enforced
