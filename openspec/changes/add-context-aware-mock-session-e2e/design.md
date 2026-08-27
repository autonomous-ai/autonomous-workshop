## Context

See `proposal.md` for motivation and `specs/workshop/context-aware-mock-session-e2e/spec.md` for the observable contract.

The current deterministic full-run test replaces the native Codex dependency and can therefore prove host behavior but not whether the real session can find and correctly interpret the materialized product-run instructions. The opposite extreme is a complete live product run, where research, image creation, CAD iteration, Playtest reasoning, and Release writing dominate elapsed time. The desired tier must preserve the native session and its real context while intentionally making its substantive output trivial.

This design is subordinate to the native-runtime boundary in ADR 0012: one Codex session owns cognition and tool use; the host retains lifecycle, deterministic gates, durable state, credentials, and effects. The test cannot add a Python stage agent or a second lifecycle implementation.

## Goals / Non-Goals

**Goals:**

- Detect broken skill descriptions, undiscoverable resources, missing `STAGE.json` inputs, bad cross-stage context, incorrect finalizer sequencing, and start/resume integration with one real Codex session.
- Make the common local acceptance run much faster than producing a credible product while retaining all production boundaries that exposed yesterday's bug.
- Produce actionable, stage-specific evidence explaining what context Codex used and where a failure occurred.
- Keep the mode opt-in, isolated, credential-safe, and reproducible enough to compare lifecycle behavior across local runs.

**Non-Goals:**

- Judge creative quality, research quality, sophisticated subagent routing, realistic CAD complexity, visual quality, or resilience across all possible Wishes.
- Treat model-authored context records as trusted semantic proof; the host validates their filesystem and checkpoint bindings, not the truth of prose claims.
- Change normal `workshop wish` behavior or add a generally available production bypass for cognitive work.
- Replace the stricter offline deterministic E2E fidelity work in `enforce-deterministic-e2e-fidelity`.

## Decisions

### 1. Add a separate opt-in acceptance tier

The new scenario will live beside end-to-end tests but carry an explicit live-Codex marker and a dedicated local runner command. Normal unit and deterministic E2E commands will not select it. The runner will create a fresh temporary Workshop home and a fixed, deliberately simple Wish, then call the same production Wish/resume composition used by the CLI.

This separation makes its requirements honest: it needs a local authenticated Codex runtime and has latency/model variability, while deterministic CI remains offline and repeatable.

**Alternative considered:** Replace the deterministic native executable with real Codex in the existing E2E. Rejected because it would make CI credentialed, slower, and nondeterministic while weakening a different kind of coverage.

### 2. Inject only a generic mock-work directive at the native executable boundary

The runner will select a small pass-through executable as `WORKSHOP_CODEX_BIN`. For version queries and process execution it delegates to the contributor's real Codex binary. For each start/resume turn it appends one bounded generic directive to the normal production prompt:

- this is context-and-integration acceptance mode;
- read and follow the normal materialized instructions and current `STAGE.json`;
- do the minimum valid, clearly marked mock work for the current stage;
- write the generic context-use record;
- do not use web search, remote services, broad exploration, or unnecessary subagents;
- invoke the normal finalizer and return.

The directive will not describe stage fields, artifact schemas, finalizer subcommands, transition names, Concept image ordering, or other production knowledge. Thus a broken production skill remains broken in this run. The pass-through must preserve real JSONL events, session identifiers, goal behavior, launch/resume arguments, permission profile, model, effort, and runtime checkpoint binding.

**Alternative considered:** Put exact mock steps in a test-only skill. Rejected because a second description of the phase protocol could allow the acceptance run to succeed when the production skill is incomplete—the primary bug class this tier exists to catch.

**Alternative considered:** Ask for mock behavior only in the Wish text. Rejected because the Wish is product intent, not runtime control, and relying on it would blur prompt-injection and workflow-instruction boundaries.

### 3. Use model-authored context records with deterministic host verification

Each turn will produce one small test-only context record outside canonical stage output paths. Its schema will include:

- current stage, checkpoint digest, and subject digest copied from `STAGE.json`;
- production instruction paths consulted with exact byte hashes;
- the subset of `STAGE.json` input keys and artifact paths used;
- a short fixture strategy identifier and explanation;
- agent-owned output paths and byte hashes;
- explicitly deferred expensive activities.

The runner will independently hash the files, verify bindings against the current packet, require a stage-specific minimum set of input keys derived from the production packet/topology, and compare the output inventory with the finalizer proposal. The record is evidence that relevant bytes were located and connected to actual output; it is not trusted proof of deep semantic understanding.

To avoid teaching stage behavior through the test, minimum input expectations will be derived mechanically from the current `STAGE.json` and accepted upstream artifact references, not copied into the Codex prompt. A failure retains the packet, redacted turn diagnostics, and context record.

**Alternative considered:** Infer understanding from a successful finalizer alone. Rejected because a lucky static fixture can finalize without exposing which inputs were missing or ignored.

### 4. Let Codex create minimal outputs through production skills

There will be no Python function that returns Match, Invent, Concept, Make, Playtest, or Release contracts. Codex uses the normal skill and finalizer for each stage, but is encouraged to choose intentionally small content:

- a single obvious Inventor assignment and compact invention;
- a minimal Concept with recorded test assumptions and small prompt set;
- simple valid geometry produced through the declared Make tooling;
- concise evidence-linked Playtest results that retain all required checks;
- a minimal valid manual and page-content package.

The fixed Wish and eligible test inputs will be selected so the simplest correct behavior is fast. Make still runs the production CAD verifier. The runner inventories writes around each turn and rejects mock helpers that author host-owned paths.

**Alternative considered:** Give Codex pre-completed stage JSON files to copy. Rejected because copying can bypass interpretation of upstream context and would be likely to recreate the deterministic fixture's blind spot.

### 5. Use local protocol servers for host-owned remote effects

The runner will start deterministic loopback-only image-provider and Factory protocol fixtures on ephemeral ports and configure the normal host credential paths to use them. Production adapters, validation, image writing, sealing, effect ledgers, idempotency, readback, and receipts remain active. The fixtures implement only the remote endpoints and return fixed payload bytes.

The native process environment remains scrubbed. Tests assert the loopback secrets are absent from prompts, workspace inputs, context records, and Codex process probes. Outbound access is denied by the existing Codex permission profile; observed web-search events fail the scenario.

The canonical scenario ends at private Deliver with no publication request. Focused acceptance scenarios may later cover wait/resume or publication, but they must use the same boundaries and remain explicitly selected.

**Alternative considered:** Patch Concept and Factory workflow classes. Rejected because those patches would hide the orchestration and ownership ordering this test must exercise.

### 6. Bound runtime without pretending it is deterministic

The initial profile will use the production launcher's real configured model and effort so the session checkpoint truthfully binds what ran. Savings come from the generic minimal-work directive and simple Wish, not from silently rewriting CLI arguments. The runner will expose explicit supported model/effort options only if the production launcher is updated to bind those values honestly end to end.

Budgets will cover each native turn and the whole run. On timeout, the runner terminates only its owned process tree, preserves the temporary run under an explicitly reported diagnostic location, redacts secrets, and exits nonzero. The success report includes per-stage durations and token/usage data when the native event protocol exposes them, but acceptance assertions avoid brittle exact time or token thresholds beyond configured ceilings.

**Alternative considered:** Replay cached model responses for later stages. Rejected because that stops testing session continuity and context interpretation.

### 7. Keep cross-tier responsibilities explicit

The deterministic E2E tier remains the authoritative offline mechanics and topology check. The mock-session tier adds live context/routing confidence. A full product run remains necessary for substantive agent and artifact-quality evaluation. Documentation and result labels will state this three-tier model so a fast green acceptance run cannot be mistaken for physical or product-quality evidence.

## Risks / Trade-offs

- **[Risk] Six real turns can still be slower or more variable than desired.** → Use a simple Wish, minimal-work directive, no web/subagents, strict budgets, per-stage timing, and optimize production skill discoverability when a stage remains slow rather than bypassing it.
- **[Risk] The generic directive itself changes model behavior.** → Keep it stage-agnostic, version it, show it in diagnostics, and prohibit it from containing contract or transition knowledge.
- **[Risk] Context records can be fabricated by the model.** → Validate every path, digest, checkpoint/subject binding, input key, and output byte independently; describe the remaining semantic limitation accurately.
- **[Risk] A model may generate minimal content that is structurally valid but semantically odd.** → Choose a trivial fixed Wish, assert only contract/gate behavior, and keep quality evaluation out of scope.
- **[Risk] Local protocol fixtures drift from external providers.** → Reuse the same transport-contract fixtures as deterministic integration tests and keep live provider conformance in separate integration acceptance.
- **[Risk] A pass-through Codex wrapper can accidentally alter runtime arguments or events.** → Test byte-for-byte argument forwarding apart from the prompt append, delegate version reporting unchanged, and assert the production checkpoint's runtime binding and one-session identity.
- **[Risk] Test-mode code becomes a production cognitive shortcut.** → Keep the runner and wrapper under test tooling, require an explicit opt-in marker, and add architecture tests preventing production CLI commands from selecting mock-session mode.

## Migration Plan

1. Define the live-Codex marker, opt-in command, context-record schema, redaction rules, and architecture guard that keeps mock mode out of production CLI paths.
2. Implement and characterize the pass-through wrapper against the installed Codex start/resume JSONL protocol without adding stage-specific instructions.
3. Add the isolated runner, preflight checks, fixed simple Wish, process budgets, and one-session trace collection.
4. Add loopback Concept-image and Factory protocol fixtures while retaining their production adapters and effect state.
5. Drive Match through Deliver, adding only minimal Wish/resource choices needed for real production skills to create cheap valid artifacts; retain the real CAD verifier.
6. Add per-stage context records, deterministic validation, write-ownership assertions, prohibited-activity checks, and retained redacted diagnostics.
7. Document the three verification tiers and measured local runtime, then keep the new test opt-in unless a suitably credentialed scheduled environment is deliberately configured.

Rollback removes the opt-in runner, wrapper, and test-only records without changing production lifecycle data or normal Wish behavior.
