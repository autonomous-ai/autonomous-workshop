# Workshop architecture

Autonomous Workshop separates an inventor's creative identity from machinery
every inventor needs.

## The whole public model

```text
WISH  ------------------------ WAIT ------------------------>  RECEIVE
                                |
                                v
                   +---------------------------+
                   |         INVENTOR          |
                   |                           |
                   |  Taste guides every choice|
                   |                           |
                   |      MAKE <-> INSPECT     |
                   |        ^         |        |
                   |        + feedback+        |
                   +---------------------------+
```

Only four words belong to the Workshop's public design language:

- **Wish** — what someone wants;
- **Taste** — the inventor's creative judgment;
- **Make** — create or revise;
- **Inspect** — test the exact result and feed failures back into Make.

`Wait` and `Receive` describe the person's experience. They are not API types,
workflow stages, or progress theater.

## Alice on top of the Workshop

```text
                          Alice owns
                 +---------------------------+
                 | TASTE.md                  |
Wish ----------->| prompts + creative choices|
                 | niche-specific inspection |
                 +-------------+-------------+
                               |
                               | imports
                               v
                         Workshop owns
                 +---------------------------+
                 | Make + Inspect contracts  |
                 | reusable making skills    |
                 | artifacts + evidence      |
                 | runtime + integrations    |
                 +---------------------------+

Workshop  -X->  Alice
```

To build Ada, add `inventors/ada/`, define Ada's Taste and workflow, and reuse
the same Workshop contracts. Do not copy Alice's state machine. Dependency is
one-way: inventors import Workshop; Workshop never imports an inventor.

## What an inventor owns

An inventor owns everything that should make its output recognizable:

- its root `TASTE.md`;
- its niche and audience;
- prompts, roles, tools, and model choices;
- candidate generation and repair policy;
- stricter domain inspections;
- learning from verified external outcomes.

An inventor may name domain phases precisely—research, rules, CAD, simulation,
playtest, print, or safety review. Those are part of its craft, not new shared
Workshop concepts.

## What the Workshop owns

The Workshop owns behavior that should be correct in the same way for every
inventor:

- preserve a bounded Wish and exact Taste bytes;
- create in a fresh workspace under an enforced budget;
- identify immutable product artifacts;
- bind every Inspection and evidence file to the exact artifact;
- persist state, revisions, leases, and hash-chained events;
- record an outside effect before executing it;
- hold ambiguous effects for reconciliation instead of blind retry;
- keep credentials out of artifacts, prompts, events, and source.

## Make and Inspect form a loop

`Workbench.make()` returns a `MakeResult` with the made artifact's identity and
creation provenance. `Workbench.inspect()` returns an artifact-bound
`Inspection`.

```text
                 feedback: what failed and why
             +----------------------------------+
             |                                  |
             v                                  |
Wish + Taste ---> Make ---> immutable artifact ---> Inspect
                    |                              |
                    +---- creation provenance     +---- exact evidence
```

Missing, stale, malformed, timed-out, or unsupported evidence is not a pass.
When a required check fails, the useful result is feedback for another Make
attempt or an explicit stop.

Creation provenance is part of Make, not a fifth public concept. Existing
`MakerMark` files remain readable; new code may call the same record
`MakeProvenance`.

## The small internal model

The implementation has a few literal types. They are not extra user-facing
stages.

```text
Artifact  -> immutable product identity + exact transferable payload
Runtime   -> state + leases + budgets + retries + durable outside effects
Adapter   -> one provider boundary
Receipt   -> verifiable evidence returned by that provider
```

### Artifact

An artifact keeps two identities separate:

- `artifact_sha256` identifies the logical file tree;
- `payload_sha256` identifies the exact transferred bytes.

Deterministic ordering, timestamps, permissions, limits, inventory, and secret
scanning make the transferable payload reproducible. Inspection remains bound
to the logical artifact, while an outside receipt can bind both identities.

### Runtime

The runtime provides SQLite transactions, revision-fenced transitions,
hash-chained events, bounded leases, budget accounting, and a durable outbox.

For an outside effect it must:

1. persist the exact request and stable idempotency identity;
2. commit that intent before calling a provider;
3. use a separate attempt fence when executing;
4. validate the returned receipt against the intent, request, artifact, and
   payload;
5. hold timeouts and unclear outcomes for reconciliation.

An HTTP success or local Boolean never proves an outside outcome.

### Adapter and receipt

An adapter is ordinary integration code for a model, CAD tool, evaluator,
printer, catalog, or fulfillment service. It owns provider authentication and
transport details. A receipt is the typed, authenticated result of an outside
effect.

Provider-specific models stay behind the adapter. Workshop does not import a
backend's database models or turn a remote service into local state authority.

## Exact evidence

An Inspection result names its evaluator, pinned version and configuration,
observation time, artifact hash, evidence path, and evidence hash. The evidence
path must exist in a sealed manifest.

```text
product bytes ----- SHA-256 ----+
                                |
evidence file ----- SHA-256 ----+--> Inspection --> decision
                                |
evidence manifest - SHA-256 ----+
```

Review evidence may be retained separately from customer-facing product bytes,
but both identities remain linked in the runtime. See
[INSPECTION_EVIDENCE.md](INSPECTION_EVIDENCE.md).

## Repository boundary

```text
inventors/<id>/
  TASTE.md              human-owned creative constitution
  inventor.json         identity, entry point, and checks
  README.md             thesis, operation, and limits
  src/ or harness/      inventor-owned workflow
  tests/                inventor checks

src/inventor_workshop/
  make.py               Wish -> MakeResult
  inspection.py         artifact-bound evidence
  artifacts.py          logical artifact identity
  pack.py               transferable artifact bytes (legacy module name)
  runtime.py            state and outside effects
  integrations.py       provider adapter contracts
  taste.py              exact creative constitution

skills/                 versioned making knowledge
schemas/                portable data contracts
tests/                  shared Workshop contract tests
```

The old `Clockwork`, `Sender`, `Door`, `Stamp`, `PackedArtifact`, and
`pack_artifact()` names remain compatibility aliases for existing inventors and
persisted data. They are not the architecture developers need to memorize.

## Extension rules

An inventor may strengthen inspections, add domain phases, choose providers,
and keep stronger local machinery while adopting Workshop at a tested
boundary. It may not silently edit Taste, treat unknown evidence as pass,
detach evidence from artifact bytes, bypass budgets or leases, or retry an
ambiguous non-idempotent effect.
