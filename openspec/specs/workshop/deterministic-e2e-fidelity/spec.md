## Purpose

Define an offline deterministic end-to-end standard that proves the real work
inside every enabled Workshop phase, rather than accepting a phase name or a
route-level success signal as evidence of production fidelity.

## Requirements

### Requirement: Deterministic E2E coverage preserves phase internals

For every phase a deterministic E2E scenario claims to cover, the suite SHALL
enter through the production lifecycle and execute that phase's production
input packet, agent-owned source boundary, materialized finalization,
proposal parsing, contract validation, deterministic gates, evidence or effect
persistence, artifact sealing, checkpoint mutation, and transition. A phase
fixture that directly returns an accepted contract, gate result, evidence
object, effect receipt, or completed transition MUST NOT count as E2E coverage.

#### Scenario: A phase reports completion without its proof chain

- **WHEN** a deterministic run reports that an enabled phase completed but one
  of its required production proposal, contract, gate, durable artifact,
  evidence/effect record, or checkpoint transition is absent
- **THEN** the phase-proof assertion fails and names the missing phase-owned
  proof

#### Scenario: An internal phase mechanism is replaced

- **WHEN** deterministic E2E code substitutes a workflow dispatcher, stage
  evaluator, finalizer, contract reader, deterministic verifier, sealing path,
  checkpoint transition, or effect coordinator
- **THEN** the fidelity policy rejects the scenario as deterministic E2E
  coverage

### Requirement: Wish coverage proves the exact host boundary

The suite SHALL start each canonical run through the production Wish entry
point. Wish coverage SHALL prove that the exact Wish bytes and frozen effort
are persisted, that the host-owned Wish gate records its decision, that the
private product workspace and immutable run assets are materialized, and that
the first enabled phase is derived from the frozen effort. Wish coverage MUST
NOT be satisfied by constructing a later-stage checkpoint directly.

#### Scenario: Accepted Wish starts a frozen route

- **WHEN** a deterministic Spark, Forge, or Quest run starts from an accepted
  Wish
- **THEN** the persisted Wish hash equals the submitted bytes, the effort is
  immutable, the Wish gate exists, and the first native turn targets Make for
  Spark or Invent for Forge and Quest

#### Scenario: Wish proof is removed

- **WHEN** the persisted Wish, Wish gate decision, materialized capability
  binding, or frozen effort proof is missing or changed
- **THEN** the deterministic run fails before later phase artifacts can be
  accepted as a complete route

### Requirement: Invent coverage proves selection and invention separately

For Forge and Quest, Invent coverage SHALL process the production read-only
stage packet containing the exact Wish, complete eligible Inventor roster,
universal blueprint, and canonical output paths. The deterministic native
boundary MAY author fixed ranking, assignment, research, and concept source
bytes, but the materialized finalizer and host SHALL construct, validate,
hash, gate, and seal both the roster-bound assignment and Invented contract.
The Made phase MUST receive those exact sealed identities.

#### Scenario: Forge or Quest completes Invent

- **WHEN** the deterministic native process authors valid Invent source and
  invokes the materialized Invent finalizer
- **THEN** production processing seals an assignment bound to the offered
  roster, seals an Invented contract containing concept and research, records
  the Invent gate, advances the checkpoint, and passes the exact identities to
  Make

#### Scenario: Invent source bypasses selection provenance

- **WHEN** the authored source selects an unavailable Inventor, omits required
  ranking or research/concept content, cites stale stage bindings, or changes
  after finalization
- **THEN** production parsing or gating rejects Invent and no downstream Made
  artifact is accepted

### Requirement: Make coverage proves real artifact construction and verification

Make coverage SHALL begin from the exact accepted Invented identity, or for
Spark SHALL create the folded ranking, assignment, compact Invented source,
and product source within the one Make turn. The deterministic native process
MAY author a minimal valid product tree and replayable CAD project, but the
materialized Make finalizer SHALL derive the Made contract and manifest, and
the production host SHALL rerun fresh, export, strict-fit, mesh, and
wall-thickness verification against the exact authored bytes before sealing
the Made revision and advancing the checkpoint. A fabricated CAD receipt or
preaccepted Made object MUST NOT count as Make coverage.

#### Scenario: Valid Make source is accepted

- **WHEN** the native process authors the minimal valid product metadata, CAD
  source, assembly outputs, and verifier declaration and then invokes the Make
  finalizer
- **THEN** production code derives the Made contract, recomputes its artifact
  manifest, runs the full print-ready CAD gate, persists evidence bound to the
  Made/product/verifier hashes, seals the exact tree, and advances to the next
  enabled phase

#### Scenario: Spark performs folded creative work

- **WHEN** Spark enters Make without a prior Invent turn
- **THEN** the same Make proposal separately proves and seals assignment,
  compact Invented provenance, and Made output before the Make gate passes

#### Scenario: CAD fails from authored input

- **WHEN** agent-owned CAD source causes the production verifier to fail
- **THEN** the failure is persisted at the Make boundary, the checkpoint does
  not advance, and a later native turn repairs source under the bounded attempt
  rules without a fabricated passing receipt

### Requirement: Playtest coverage proves evidence, verdict, and repair behavior

Quest Playtest coverage SHALL receive the exact sealed Made revision and rerun
the production deterministic CAD verifier against it. The native boundary MAY
author fixed observational evidence and structured findings, but production
contracts SHALL validate evidence bindings, derive the verdict, persist the
Playtest gate and evidence, and either advance the passing revision or execute
the declared invalidation boundary. A phase-wide passing Playtest stub MUST NOT
count as coverage.

#### Scenario: Quest Playtest passes the current Made revision

- **WHEN** valid Playtest source and deterministic checks agree on a passing
  current Made revision
- **THEN** the production Playtested contract, CAD evidence, gate decision,
  sealed evidence tree, and checkpoint transition all bind the same Made and
  verifier identities

#### Scenario: Quest Playtest requests a Make repair

- **WHEN** valid feedback declares an implementation repair boundary
- **THEN** production processing persists the failed verdict and feedback,
  invalidates Playtest and Release outputs but preserves Invent, returns to
  Make within the shared round budget, and accepts Release only after a new
  Made revision passes a later Playtest

#### Scenario: Quest Playtest requests an Invent revision

- **WHEN** valid feedback declares a fundamental concept revision boundary
- **THEN** production processing preserves the failing evidence lineage,
  invalidates Invent and every downstream revision, and returns the exact prior
  Invented and Playtested bindings to the next Invent turn

### Requirement: Release coverage proves the complete terminal effect chain

Release coverage SHALL begin from the exact current Made revision and either
Quest's passing Playtest identity or Spark/Forge's canonical not-run record.
The deterministic native process MAY author a fixed release package, but the
materialized finalizer and production host SHALL validate the package
contract, `MANUAL.pdf`, bounded claims, product metadata, Playtest binding or
omission, and full-tier CAD replay. Production Factory integration SHALL then
persist intent, authenticate, import, reconcile, publish, perform authenticated
and public readback, hash-compare the CAD/manual bytes, persist its receipt,
and alone mark Release terminal.

#### Scenario: Spark or Forge publishes a truthful direct Release

- **WHEN** a valid direct-Release package is finalized for the current Made
  revision
- **THEN** production validation accepts canonical `playtest_status: not-run`
  bytes with no Playtest claims, replays print-ready CAD, verifies the PDF,
  publishes exact bytes, records public hash readback, and completes Release

#### Scenario: Quest publishes an evidence-bound Release

- **WHEN** a valid Quest package cites the current passing Playtest evidence
- **THEN** its allowed claims, package hashes, CAD replay, Factory request,
  public readback, receipt, and terminal checkpoint bind that exact evidence
  and Made revision

#### Scenario: Publication outcome is ambiguous

- **WHEN** the remote transport persists an import or publication but its
  immediate response is lost
- **THEN** production reconciliation reads back the stable idempotent effect
  before retrying, avoids duplicate import or promotion, and completes only if
  the exact remote hashes are proven

#### Scenario: Release credentials are missing

- **WHEN** a valid proposal reaches the host-owned Factory effect without
  configured credentials
- **THEN** Release waits with its exact pending proposal and effect intent, the
  native turn is not rerun on resume, and only the deferred host effect
  continues after credentials become available

### Requirement: Passed-through phases are proven absent

The canonical route matrix SHALL derive enabled phases from the immutable
production effort definitions. A passed-through phase SHALL create no native
turn, Goal, authored source, finalized contract, gate, evidence, or synthetic
success. Absence assertions SHALL be phase-specific and SHALL coexist with the
folded provenance required by the first active creative phase.

#### Scenario: Spark omits Invent and Playtest

- **WHEN** Spark reaches terminal Release
- **THEN** no Invent or Playtest phase proof exists, while Make contains the
  separately sealed folded assignment and Invented identities and Release
  contains the canonical Playtest-omission record

#### Scenario: Forge omits Playtest

- **WHEN** Forge reaches terminal Release
- **THEN** Invent and Make each have their complete production proof chains,
  no Playtest phase proof exists, and Release contains only truthful omission
  facts

#### Scenario: Quest enables Playtest

- **WHEN** Quest reaches terminal Release
- **THEN** Release contains no not-run placeholder and binds the complete
  passing Playtest proof chain

### Requirement: Test doubles are limited to process-external boundaries

The deterministic suite SHALL replace live cognition only with an executable
that speaks the supported native protocol and SHALL replace Factory only at
its outbound remote transports. External doubles SHALL create only outputs
owned by the external dependency they represent. They MUST NOT write
host-owned contracts, gates, CAD/PDF evidence, sealed artifacts, checkpoints,
effect state, or receipts, and host credentials MUST NOT enter the native
process environment or readable workspace.

#### Scenario: One native session spans enabled phases

- **WHEN** a canonical route runs offline
- **THEN** production runtime discovery and event parsing observe one start
  followed by resumes of one stable session identity, each turn receives the
  production read-only stage packet, and each enabled turn invokes the
  materialized finalizer

#### Scenario: External double crosses ownership

- **WHEN** the native executable or Factory transport directly creates a
  host-owned proof or lifecycle state file
- **THEN** ownership assertions fail even if the route otherwise reaches
  Release

#### Scenario: Host credentials are configured

- **WHEN** deterministic Factory credentials are available through the
  production host credential path
- **THEN** the native executable's environment and readable files reveal none
  of their names or values

### Requirement: Fidelity guards track topology, proof, and repeatability

The required CI suite SHALL mechanically reject internal patching, compare
covered routes and transitions with the production effort definitions, and
verify each enabled phase's complete proof inventory. Equivalent canonical
runs from clean homes SHALL produce equivalent route decisions, source-owned
content, sealed content identities, and effect requests apart from explicitly
bounded host metadata.

#### Scenario: Production topology changes

- **WHEN** an effort adds, removes, or redirects a phase, repair edge, or
  wait/resume boundary
- **THEN** CI identifies the uncovered route or edge and fails until the
  corresponding phase-deep fixture and proof assertions are updated

#### Scenario: Required phase artifact is removed

- **WHEN** a finalizer output, gate decision, evidence record, sealed artifact,
  effect receipt, or checkpoint proof is removed from a completed run
- **THEN** the phase-proof guard fails at the owning phase rather than accepting
  the unchanged stage trace

#### Scenario: Canonical run is repeated

- **WHEN** the same Spark, Forge, or Quest fixture runs twice from clean
  isolated homes without network access
- **THEN** both runs have equivalent enabled phases, transitions, decisions,
  artifact ownership, content hashes, and effect identities except for
  documented bounded metadata

### Requirement: Deterministic fidelity remains an evidence-bounded CI gate

The repository SHALL document and run a focused offline deterministic E2E
command as a required CI job separate from unit tests and live native-runtime
acceptance. The documentation SHALL state the measured runtime, approved
external seams, phase-proof inventory, and that success does not evaluate
reasoning quality or prove physical printing, fit, durability, manufacture,
delivery, or human response.

#### Scenario: CI runs without live services

- **WHEN** the deterministic fidelity job runs with no live Codex, Factory,
  network, or real customer credential
- **THEN** every canonical and failure scenario uses only approved external
  doubles while executing the covered production phase internals

### Requirement: Deterministic route traces exercise active Invent Concept behavior

The required deterministic end-to-end suite SHALL execute marked Forge and Quest through the production stage packet, materialized compound Invent finalizer, trusted host validation, durable image-effect boundary with deterministic transport doubles, sealed Concept gate, Concept-bound Make finalizer and gate, downstream Release behavior, and exact terminal publication doubles. Stage traces SHALL remain Forge `Invent -> Make -> Release` and Quest `Invent -> Make -> Playtest -> Release`; Concept activity SHALL appear only as artifacts, effect state, and gate evidence owned by Invent.

#### Scenario: Marked Forge completes deterministically
- **WHEN** the deterministic Manager authors valid compound Invent source and every image role reconciles
- **THEN** the trace contains one Invent turn and one Invent gate with a sealed Concept identity
- **AND** Make consumes that identity without a Concept stage event

#### Scenario: Marked Quest completes deterministically
- **WHEN** Quest passes its active Invent Concept boundary and current Playtest rules
- **THEN** the trace preserves the exact four active stages and Concept-bound lineage through Make and Playtest

### Requirement: Deterministic failures cover source, effect, and downstream integrity

The suite SHALL prove fail-closed behavior for stale or malformed pre-render source, post-finalizer source mutation, missing roles, partial completion, duplicate or changed image bytes, absent authorization or credentials, provider rejection, timeout before transmission, ambiguous post-transmission outcome, authenticated reconciliation, stale effect receipt, changed sealed Concept, Made binding mismatch, component mismatch, copied Concept pixels, and stale revision input. Doubles MUST exist only at the outbound provider transport and other established remote boundaries.

#### Scenario: An image response becomes ambiguous
- **WHEN** the deterministic transport simulates transmission followed by an unresolvable disconnect
- **THEN** the run waits at Invent with an unknown effect and performs no blind retry

#### Scenario: Concept changes during Make
- **WHEN** a sealed Concept byte is mutated after the Make packet is written
- **THEN** the real Make gate rehash rejects the proposal

### Requirement: Frozen-route absence remains covered

The deterministic matrix SHALL continue to prove that Spark and unmarked historical fixtures do not acquire active Concept artifacts, effects, packet fields, gate checks, or contract bindings after installed code changes.

#### Scenario: Spark runs beside marked Forge and Quest
- **WHEN** the complete effort matrix executes
- **THEN** Spark remains `Make -> Release` with its existing folded creative contract
- **AND** no Concept provider double is called for Spark
