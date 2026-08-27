## Purpose

Defines a fast local acceptance tier that uses one real Codex session to verify that the complete Workshop pipeline supplies understandable stage context and can process minimal context-derived agent outputs through production lifecycle boundaries.

## ADDED Requirements

### Requirement: Mock-session E2E uses a real persistent Codex session
The mock-session E2E runner SHALL launch the installed Codex runtime through the production native-session protocol and SHALL reuse the resulting session identity for every resumed cognitive stage in one Wish-to-Deliver run. It MUST NOT replace Codex with a scripted executable, recorded transcript, structured model call, in-process stage agent, or directly returned stage outcome.

#### Scenario: Complete local mock-session run
- **WHEN** a contributor runs the documented mock-session E2E command with an authenticated supported Codex installation
- **THEN** one real session starts at Match, resumes through every later cognitive stage in production order, and reaches the private Deliver boundary

#### Scenario: Session identity changes
- **WHEN** any later stage starts a different Codex session instead of resuming the original session identity
- **THEN** the mock-session E2E run fails with the expected and observed session bindings

### Requirement: Production context remains the source of stage behavior
The real Codex session SHALL receive the normal materialized product-run `AGENTS.md`, declared skill trees and descriptions, Inventor roster, `WISH.json`, host-written `STAGE.json`, prior accepted artifacts, and normal stage prompt. A generic test-mode overlay MAY request minimal mock work and prohibit expensive or external activity, but it MUST NOT restate stage-specific input schemas, output schemas, finalizer commands, lifecycle transitions, or ownership rules that the production instructions are responsible for teaching Codex.

#### Scenario: Required production context is sufficient
- **WHEN** Codex handles a stage in mock-session mode
- **THEN** it discovers the applicable production instructions and current stage packet, chooses the stage-appropriate minimal output behavior, and finalizes without receiving a duplicated stage recipe from the test harness

#### Scenario: Skill description or context is insufficient
- **WHEN** the materialized skill description, referenced instruction, stage input, prior artifact, or declared resource needed to handle the stage is absent, unreadable, stale, contradictory, or not discoverable from the normal context
- **THEN** the stage fails with diagnostics identifying the unresolved production context instead of the overlay supplying the missing rule

### Requirement: Every stage supplies verifiable context-use evidence
Before finalizing each cognitive stage, Codex SHALL write a bounded mock-session context record bound to the current stage, checkpoint, subject, production instruction files consulted, stage inputs used, selected minimal-output strategy, and agent-owned outputs produced. The local runner SHALL verify every declared path and digest against the exact run workspace and current `STAGE.json`; model prose alone SHALL NOT satisfy this proof.

#### Scenario: Context proof matches the stage
- **WHEN** a stage finalizes successfully
- **THEN** its context record is bound to the current checkpoint and subject, names the applicable production instructions and inputs, and its output inventory matches the agent-owned files submitted to the finalizer

#### Scenario: Codex uses stale or invented context
- **WHEN** a context record cites a missing path, wrong digest, prior checkpoint, unrelated stage input, or output that was not actually produced
- **THEN** the mock-session E2E runner rejects the stage even if its proposed outcome otherwise passes a host gate

### Requirement: Mock work preserves production ownership and ordering
Mock-session mode SHALL reduce only the substantive agent work: research depth, creative exploration, geometry complexity, narrative depth, and independent qualitative iteration. Codex SHALL still author valid agent-owned stage inputs and invoke the materialized production finalizer, while the production host SHALL still parse proposals, run deterministic gates, perform configured effects, seal artifacts, mutate checkpoints, apply invalidation, and choose transitions. Mock-session helpers and fixtures MUST NOT create host-owned evidence, sealed artifacts, effect receipts, or checkpoints.

#### Scenario: Concept crosses the pre-render boundary
- **WHEN** Codex completes the mock Concept turn
- **THEN** the pre-render Concept proposal and context proof exist, declared rendered image paths and the sealed Concept do not yet exist, and the host subsequently creates those outputs through the production Concept effect path

#### Scenario: Minimal Make output is accepted
- **WHEN** Codex selects and adapts the minimal Make strategy from the current Wish, Concept, and Inventor context
- **THEN** the production CAD verifier executes on the exact resulting files and the normal Make and Playtest gates consume its evidence

#### Scenario: Helper crosses an ownership boundary
- **WHEN** a mock-session helper or fixture creates host-owned evidence, a sealed artifact, an effect receipt, or a lifecycle checkpoint
- **THEN** the E2E run fails its write-ownership assertions

### Requirement: External effects are local, deterministic, and credential-safe
The mock-session E2E run SHALL make no live web-search, image-provider, Factory, publication, manufacture, postage, carrier, or other remote request. Where the full lifecycle requires an external protocol, the runner SHALL use a local deterministic protocol fixture while retaining the production adapter, coordinator, validation, persistence, idempotency, reconciliation, and receipt logic. Fixture secrets MUST remain outside the Codex subprocess environment and agent-readable workspace.

#### Scenario: Concept and Release require external protocols
- **WHEN** the mock-session run reaches Concept rendering and private Release import
- **THEN** production integrations communicate only with local deterministic endpoints and complete their normal host-owned processing

#### Scenario: Codex attempts external work
- **WHEN** the session uses web search, calls a non-local network endpoint, or requests a credential for mock artifact generation
- **THEN** the run fails and reports the stage and prohibited activity

#### Scenario: Fixture credential isolation
- **WHEN** the runner inspects the session launch environment, prompts, context records, and agent-owned files
- **THEN** no image-provider or Factory fixture secret is present

### Requirement: The local command is bounded and diagnostic
The repository SHALL provide one documented opt-in command that performs preflight checks, runs the mock-session E2E scenario in an isolated temporary Workshop home, enforces per-turn and whole-run budgets, and emits a concise stage trace with elapsed time and failure diagnostics. It SHALL fail fast when Codex is missing, unsupported, unauthenticated, or when required local protocol fixtures cannot start.

#### Scenario: Successful bounded run
- **WHEN** the local command completes within its configured budget
- **THEN** it reports the Codex model and reasoning effort, one start and subsequent resumes, all visited stages, per-stage durations, context-proof status, final checkpoint, and total elapsed time

#### Scenario: Run exceeds its budget
- **WHEN** a turn or the whole acceptance run exceeds the configured local budget
- **THEN** the runner terminates safely, preserves redacted diagnostics and the isolated workspace for inspection, and returns a nonzero status

#### Scenario: Prerequisite is unavailable
- **WHEN** Codex is missing, too old, or not authenticated
- **THEN** the runner exits before creating a misleading partial success and explains the prerequisite that failed

### Requirement: Mock-session evidence has a narrow acceptance meaning
Mock-session E2E success SHALL mean only that a real Codex session could discover and interpret the supplied context well enough to drive minimal valid outputs through the production pipeline. It MUST NOT be reported as evidence of product quality, exhaustive agent behavior, successful research, physical printing, fit, durability, manufacture, publication, shipment, delivery, or human response, and it MUST NOT replace the offline deterministic E2E suite.

#### Scenario: Local acceptance succeeds
- **WHEN** the mock-session E2E command reaches Deliver
- **THEN** its summary labels the run as context-and-integration acceptance and explicitly distinguishes it from deterministic CI coverage and full product validation

#### Scenario: Default CI runs without Codex credentials
- **WHEN** the normal offline test suite runs in CI
- **THEN** the mock-session scenario is skipped unless explicitly enabled and the deterministic E2E suite remains independently required
