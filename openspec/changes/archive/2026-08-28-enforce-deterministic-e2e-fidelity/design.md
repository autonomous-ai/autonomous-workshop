## Context

ADR 0016 freezes one of three routes for each new run:

```text
Spark: Wish -> Make -> Release
Forge: Wish -> Invent -> Make -> Release
Quest: Wish -> Invent -> Make -> Playtest -> Release
```

Match is folded into the first creative phase. Spark and Forge truthfully omit
Playtest; Quest enables the bounded Make–Playtest repair loop. Release is
terminal only after full-tier CAD replay, PDF validation, Factory publication,
and exact public hash readback.

The existing deterministic scenario has the correct process and transport
seams, but its assertions can still collapse a whole phase into “the fixture
authored inputs and the route advanced.” The reference implementation on
`feat/deterministic-e2e-test` sets the stronger standard: define the work and
durable proof owned by each phase, run every in-repository mechanism in that
phase, and mechanically reject a phase-wide replacement. This design carries
that standard forward to the current effort-aware topology, where Concept,
standalone Match, and Deliver are not active phases.

The architecture boundary remains unchanged. Native Codex owns cognitive and
tool-using work; a deterministic executable may supply fixed agent-owned bytes
in this suite. The Workshop host still owns contracts, gates, evidence,
checkpoints, credentials, effects, reconciliation, and terminal truth.

## Goals / Non-Goals

**Goals:**

- Make “E2E covers phase X” mean that every production-owned boundary inside X
  ran and left independently inspectable proof.
- Keep deterministic authorship realistic enough to drive the exact
  materialized finalizer for every enabled native turn.
- Prove folded creative contracts independently inside Spark Make and
  Forge/Quest Invent.
- Exercise full production CAD, PDF, Factory, invalidation, wait/resume, and
  checkpoint behavior from input-driven scenarios.
- Detect both lifecycle drift and within-phase proof drift in CI.

**Non-Goals:**

- Evaluating model reasoning, web research quality, Inventor Taste, native
  subagent behavior, manual aesthetics, or physical-product quality.
- Calling a live Codex runtime, Factory, or any other network service.
- Recreating the Manager's cognitive loop in Python or teaching the fake
  executable to decide lifecycle transitions.
- Activating dormant Concept, restoring standalone Match, or adding Deliver to
  the current topology.
- Replacing focused unit, component integration, installed-wheel, or live
  native-session tests.

## Decisions

### 1. Define one explicit proof ledger per phase

The suite will maintain declarative proof definitions for Wish, Invent, Make,
Playtest, and Release. Each definition separates five concerns:

1. production inputs and upstream identities the phase must receive;
2. paths the deterministic native process is allowed to author;
3. production mechanisms that must execute after authorship;
4. durable outputs that must exist and hash-bind to one another; and
5. negative mutations that must fail at this phase before a later effect.

The ledger is not a helper that marks a phase complete. It is an assertion
inventory evaluated against the completed workspace and private host state.
Every listed file is reread, hashed, parsed through its production contract
where applicable, and cross-checked against the checkpoint history and gate or
effect that accepted it.

A stage trace remains useful for ordering and session continuity, but it is
only an index into the ledger. It cannot satisfy phase coverage by itself.

Alternative considered: assert a generic `contract + gate + artifacts` tuple
for every phase. Rejected because the meaningful internals differ: Wish has no
native proposal, Make owns CAD evidence, and Release owns resumable external
effects and terminal publication.

### 2. Drive Wish through its real host-only sequence

Wish is not an agent Goal and therefore gets no fake native author function.
The canonical scenarios call the normal start entry point with exact Wish
bytes and an effort. The Wish proof assertion checks:

- canonical `WISH.json` bytes and the reported Wish hash;
- frozen effort and immutable effort-route capability binding;
- private workspace/materialized instruction manifests and read-only inputs;
- the Wish gate record and its checkpoint/history entry;
- the first generated `STAGE.json` is Make for Spark and Invent for
  Forge/Quest; and
- no native session existed before the Wish gate admitted the run.

Negative coverage removes or changes each of the Wish, effort, gate, and
materialized-binding proofs and confirms the phase ledger refuses to treat a
later terminal Release as a complete E2E run.

Alternative considered: begin tests from an `AgentRun` fixture at the first
native phase. Rejected because it bypasses exact Wish persistence, route
freezing, run materialization, and the first checkpoint transition.

### 3. Model Invent as several authored facts followed by production acceptance

For Forge and Quest, the fake executable's Invent handler will not write an
accepted Invented object directly. It will:

- read and validate the stage packet's Wish hash, roster order and hashes,
  universal blueprint, round, and canonical output paths;
- author ranking entries for every offered Inventor and select one roster
  member;
- author research provenance and a concept containing the physical facts Make
  needs; and
- call the materialized Invent finalizer with only that source path.

The proof ledger then confirms production code, not the fixture:

- constructs and validates the roster-bound assignment;
- constructs and validates the Invented concept/research contract;
- hashes and seals both outputs;
- records the Invent gate and checkpoint transition; and
- puts those exact assignment and Invented identities into Make's stage packet.

Negative cases vary agent-owned source: unavailable selection, incomplete
ranking, missing research/concept content, stale checkpoint/subject binding,
and post-finalizer source tamper. They must fail before Made or CAD evidence is
accepted.

Spark uses the same authored ranking and invention structures inside its Make
handler, but the proof ledger records assignment and Invented as distinct
contracts sealed by the compound Make proposal.

Alternative considered: one `author_invent()` function that returns a ready
accepted phase payload to the test. Rejected because that would hide whether
the materialized finalizer, compound contracts, and host gate still agree.

### 4. Make must build and verify exact bytes, not announce a Made result

The deterministic Make handler will author the smallest replayable,
print-ready product tree that exercises current production verification. Its
work is deliberately decomposed:

- validate the exact upstream assignment/Invented identity, or author the
  folded creative source for Spark;
- write product metadata and exact Wish/provenance bindings;
- write parametric CAD source and its project metadata;
- run or prepare the production-declared CAD project outputs needed by the
  materialized finalizer, without writing host evidence;
- write assembly exports and the agent-side verification declaration; and
- invoke the materialized Make finalizer with the product root, CAD project,
  verification declaration, and optional Spark creative source.

After the native turn exits, production Make processing must independently:

- parse the proposal and reread every manifest byte;
- validate Made against the accepted Invented identity;
- execute fresh generation, exports, strict fit, local audits, mount/motion
  checks where declared, mesh checks, and wall-thickness checks;
- persist full-tier CAD evidence with the exact Made, product artifact,
  verifier, command, and evidence-stage identities;
- seal the Made contract and product tree; and
- advance the checkpoint only after the gate passes.

The Make proof ledger checks representative required files as well as the full
manifest, file modes, source immutability across verifier replay, and absence
of host-owned CAD evidence from the native write inventory.

CAD rejection is caused by invalid authored source or declarations. The first
attempt must persist a production rejection at the same checkpoint; the next
native turn receives that rejection in its stage subject, repairs source, and
passes the real verifier. No `NativeCadGateEvidence` fixture or verifier patch
is permitted.

Alternative considered: cache one known passing CAD receipt to reduce runtime.
Rejected because generation, export, fit, mesh, thickness, and verifier
identity drift are central Make regressions this suite exists to catch.

### 5. Playtest must prove replay, evidence, verdict, and both invalidation widths

Quest's fake Playtest handler reads the exact sealed Made identity and authors
only the evidence/results and structured feedback source allowed to the native
phase. The production Playtest finalizer and host must:

- validate that every evidence item cites the current Made revision;
- rerun full CAD verification against the sealed product bytes;
- construct the Playtested contract and feedback records;
- persist the Playtest gate and separate CAD/evidence records;
- seal the evidence tree; and
- choose forward, Make-repair, or Invent-revision transition solely from valid
  structured invalidation markers within the shared round budget.

Three scenario families are required:

- pass: exact Made, Playtested, evidence, gate, and Release input identities
  agree;
- implementation repair: the failed Playtest and feedback are preserved,
  Invent remains sealed, Make/Playtest/Release are invalidated, a new Made
  revision is produced, and a later Playtest passes; and
- fundamental revision: the failed evidence lineage is preserved, Invent and
  every downstream revision are invalidated, and the next Invent packet binds
  the prior Invented and failing Playtested/feedback bytes.

The current ADR requires at least the Make-repair route in deterministic E2E;
the Invent-revision scenario is included because the production protocol
supports it and phase-deep coverage must not leave the wider invalidation path
hidden behind a generic repair test.

Alternative considered: cover only a passing Quest route plus a unit test of
invalidation. Rejected because the shared-round checkpoint history and
cross-phase artifact preservation are emergent whole-run behavior.

### 6. Release must traverse validation and each remote-effect substep

The deterministic Release handler authors a real minimal `MANUAL.pdf`, product
metadata, claims, and either the canonical Playtest omission bytes or Quest
evidence binding, then invokes the materialized Release finalizer. It does not
write an effect, receipt, or terminal checkpoint.

Production Release processing is proved in this order:

1. proposal and package manifest parsing;
2. Made and Playtest/omission identity validation;
3. PDF structure, page-box, extractable-text, active-content, dependency, and
   bounded-size validation;
4. full-tier print-ready CAD replay against the sealed Made bytes;
5. durable Factory intent and stable idempotency identity before network I/O;
6. production credential loading after the native process exits;
7. authenticated login, existing-design lookup, import, and private readback;
8. promotion and authenticated public readback;
9. public project/manual fetch and exact hash comparison;
10. durable receipt/effect state bound to request, CAD, package, manual,
    Playtest/omission, category, owner, and remote history identities; and
11. terminal Release checkpoint.

The stateful Factory transport owns only remote responses and remote state. It
asserts request shapes and can simulate import persisted before response loss,
promotion persisted before response loss, stale readback, wrong hash/category,
or irreconcilable state. Production reconciliation must decide whether to
read, retry, wait, fail, or finish.

Missing credentials produces a resumable Release wait after the proposal has
been consumed. Resume must perform no new native turn and continue only the
pending effect. Tampered pending proposals, effect records, sealed package
bytes, or remote hashes fail closed before terminal completion.

Alternative considered: return a final public Factory response from one fake
service call. Rejected because it abstracts the entire Release effect phase and
cannot prove intent-before-effect, idempotency, reconciliation, readback, or
receipt binding.

### 7. Preserve the process boundary and audit exact ownership

The deterministic native executable is selected through
`WORKSHOP_CODEX_BIN`; production `CodexNativeSessionLauncher` performs version
discovery, permission-profile construction, start/resume arguments, prompt
delivery, environment scrubbing, JSONL parsing, and session checkpointing. The
executable supports one stable session id and records a bounded trace per turn:

- start or resume mode and exact session id;
- phase, checkpoint and subject hashes;
- prompt and stage-packet hashes/read-only state;
- source paths read and paths written;
- finalizer invocation and return status; and
- whether forbidden credentials or host-owned paths were visible.

The ownership guard compares before/after workspace and host-state inventories.
Native writes are limited to phase-declared agent source paths,
`agent-outcome.json`, and artifacts written by the invoked materialized
finalizer. Factory doubles write no run files. Host-owned gates, evidence,
seals, checkpoints, effects, receipts, and terminal state must appear only
after production host processing.

Alternative considered: patch the launcher with an in-process fake agent.
Rejected because it bypasses command construction, sandbox/environment
isolation, JSONL parsing, stable session persistence, and real finalizer
execution in the product workspace.

### 8. Separate route coverage from phase-proof coverage

The route matrix derives enabled phases directly from `WORKSHOP_EFFORTS` and
asserts exact start/resume order for Spark, Forge, and Quest. A second guard
derives the union of enabled phases and supported repair/wait edges and compares
it with declared deterministic scenarios. A third guard evaluates the proof
ledger for each enabled phase and absence ledger for each passed-through phase.

This produces three different failure messages:

- topology drift: a route or transition is not traversed;
- proof drift: a traversed phase lacks a required production output; or
- ownership drift: a double authored output that belongs to the host.

Future Concept activation must add its own phase ledger, fixture authorship,
production effect boundary, scenarios, and tasks in the same change that alters
the effort definition. It cannot satisfy coverage merely by adding `concept`
to an expected stage list.

Alternative considered: generate proof expectations automatically from stage
names. Rejected because stage names do not encode each phase's contracts,
evidence, effects, or absence rules.

### 9. Keep failure scenarios input-driven and clean-run repeatability bounded

Every failure scenario mutates only agent-owned inputs, remote transport
responses/state, fixture credential availability, or an already persisted
artifact whose tamper resistance is under test. Internal return values are
never patched.

Each canonical route runs twice from clean homes. Comparison normalizes only
explicitly documented host metadata such as temporary absolute roots and
timestamps. It compares stage/edge decisions, source inventories, checkpoint
history shapes, sealed content hashes, verifier identities, effect request
identities, and remote call sequences. If a content hash legitimately embeds
an unavoidable run identity, the comparison records the derivation rather than
dropping that phase from repeatability.

Alternative considered: compare only final status and stage order. Rejected
because nondeterministic source, evidence, or effect identities could remain
hidden beneath the same route.

## Risks / Trade-offs

- **The fake executable becomes a second workflow engine** → Keep it limited
  to reading current inputs, authoring fixed phase-owned source, invoking one
  materialized finalizer, and emitting protocol events. It never selects a
  transition, runs a host gate, or creates host state.
- **The proof ledger becomes a brittle list of filenames** → Bind entries to
  owning contracts and cross-hashes, assert the full sealed manifest, and keep
  representative required paths for actionable diagnostics.
- **Real CAD and PDF verification make CI slow** → Use the smallest valid
  fixture and a separate required job; measure runtime, but never replace
  checks with cached success.
- **Factory emulation drifts from the service** → Assert production request and
  response shapes in the stateful transport and retain focused live-contract
  tests separately; keep all production adapter parsing active here.
- **Broad static mock detection has false positives or easy bypasses** → Pair
  AST policy checks with runtime path ownership, environment probes, phase
  proof mutation tests, and reviewable approved-seam declarations.
- **Frozen historical runs differ from current routes** → Target new-run
  Spark/Forge/Quest as canonical coverage and retain historical compatibility
  in focused workflow tests; do not reinterpret old checkpoints.

## Migration Plan

1. Convert the deterministic harness to explicit external seams and add the
   process/native ownership trace.
2. Add the Wish proof ledger and the detailed Invent handler/proof chain.
3. Add the detailed Make product/CAD fixture, real verifier chain, and
   input-driven rejection/repair case.
4. Add passing and rejecting Playtest evidence chains with Make and Invent
   invalidation widths.
5. Add the detailed Release package, PDF/CAD validation, stateful Factory
   protocol, wait/resume, reconciliation, tamper, and terminal proof chain.
6. Build Spark/Forge/Quest route and absence matrices over those phase helpers,
   then add topology, phase-proof, ownership, and repeatability mutation tests.
7. Document the measured command/runtime and enable the separate required CI
   job only after all phase-deep scenarios pass.

Rollback removes the deterministic harness, approved transport seam, and CI
job. It does not alter stored-run schemas or lifecycle semantics. Any
production transport seam added for the suite remains acceptable only if it is
narrow, externally oriented, and useful for deterministic component testing;
otherwise rollback removes it as well.
