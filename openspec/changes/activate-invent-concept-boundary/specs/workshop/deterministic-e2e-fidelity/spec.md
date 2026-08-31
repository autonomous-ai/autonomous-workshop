## ADDED Requirements

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
