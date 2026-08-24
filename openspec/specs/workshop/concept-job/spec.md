## Purpose

Concept is the Workshop job that turns an abstract Wish into one concrete, visualized design before anyone builds geometry. It commits to what the product actually looks like — its locked physical facts and a consistent set of images — so that Make builds to a decided design instead of reinterpreting prose.

## Requirements

### Requirement: Concept is a Workshop job between Wish and Make

The Workshop SHALL recognize `concept` as a job in its own right, ordered after `wish` and before `make`. Every place that names or validates a Workshop job — a `Need`, a `Feedback.invalidates` entry, a run's current job, a blueprint's declared tasks, and the stage-transition rules — SHALL accept `concept` on the same terms as the other jobs.

#### Scenario: Concept appears in the job set

- **WHEN** the Workshop job set is enumerated
- **THEN** it contains exactly `wish`, `concept`, `make`, `playtest`, `instructions`, and `deliver`, in that order

#### Scenario: A run reaches Make only through Concept

- **WHEN** a run registered at stage `wish` advances
- **THEN** the only legal next stage is `concept`
- **AND** a run at stage `concept` may advance only to `concept` or `make`

#### Scenario: A blueprint must declare its Concept work

- **WHEN** a `ToyBlueprint` is assembled whose selected tasks name no `concept` task
- **THEN** assembly is rejected, because a blueprint must cover every Workshop job

#### Scenario: A Need may be raised against Concept

- **WHEN** a `Need` is constructed with job `concept`
- **THEN** it is accepted as a valid Workshop need

### Requirement: Concept receives the round's context and returns a sealed concept

The Concept job SHALL be a callable taking a `ConceptContext` and returning a `ConceptImages`. The `ConceptContext` SHALL carry the same bindings Make receives for that round — the `Wish`, the `Taste`, the `ToyBlueprint`, the round number, the total playtest rounds, an absolute workspace path, and any `Feedback` from the previous round — and SHALL reject a context whose workspace is not absolute or whose round is outside the run's round allowance.

#### Scenario: Concept runs before Make in every round

- **WHEN** the Workshop begins round N
- **THEN** it constructs a `ConceptContext` for round N and calls the Concept job
- **AND** it constructs the round's `MakeContext` only after Concept returns

#### Scenario: The concept is produced inside the round workspace

- **WHEN** Concept returns a `ConceptImages`
- **THEN** every image it names resolves to a regular file inside the workspace the context supplied
- **AND** a concept whose files fall outside that workspace is rejected

#### Scenario: A malformed context is refused

- **WHEN** a `ConceptContext` is constructed with a relative workspace path, a round below 1, or a round greater than the run's playtest rounds
- **THEN** construction fails with a contract error

### Requirement: Concept waits truthfully when it cannot draw

Concept SHALL NOT invent, describe, or placeholder a design it cannot actually visualize. When the capability needed to produce concept images is not configured, the job SHALL raise `WaitingFor` carrying a `Need` whose job is `concept` and whose instructions name the missing capability, and the Workshop SHALL park the run as waiting rather than proceeding to Make.

#### Scenario: No image provider is configured

- **WHEN** the Concept job runs with no concept image provider available
- **THEN** it raises `WaitingFor` with a `Need` for job `concept` and capability `concept-images`
- **AND** the run is recorded as waiting at job `concept`
- **AND** Make is not called for that round

#### Scenario: The provider fails to produce a required view

- **WHEN** the image provider returns without producing one of the required images
- **THEN** Concept fails rather than returning a partial concept
- **AND** no `ConceptImages` is handed to Make

#### Scenario: Waiting is reported with the round intact

- **WHEN** Concept waits in round N
- **THEN** the recorded run reports job `concept`, round N, and the raised needs

### Requirement: Later rounds refine the concept rather than restart it

When a round carries `Feedback` from a previous Playtest, Concept SHALL treat the previous round's concept as the design under revision: it SHALL apply the feedback as corrections to that design and SHALL preserve every feature the feedback did not challenge. Concept SHALL NOT produce an unrelated new design in response to feedback that asks for a change to the existing one.

#### Scenario: Round 1 has no prior concept

- **WHEN** Concept runs in round 1
- **THEN** its context carries no feedback
- **AND** it produces a concept from the Wish, Taste, and blueprint alone

#### Scenario: Feedback revises the standing design

- **WHEN** Concept runs in a round whose context carries feedback
- **THEN** the returned concept reflects each feedback item's requested change
- **AND** the parts of the design the feedback did not mention remain recognizably the same design

#### Scenario: Revision does not accumulate without bound

- **WHEN** consecutive rounds have each refined the previous round's concept up to the configured refine limit
- **THEN** the next round re-anchors from the design's locked facts instead of refining the drifting image further

### Requirement: A run records which concept its build came from

The Workshop SHALL record the sealed identity of the concept used for each round alongside the round's other evidence, so that a delivered product can be traced to the concept it was built to. A run that resumes after waiting SHALL restore the same concept identity rather than silently building against a different one.

#### Scenario: The concept identity is recorded

- **WHEN** Concept completes for a round
- **THEN** the run records that concept's content-addressed hash

#### Scenario: Resume carries the concept forward

- **WHEN** a run is resumed after parking downstream of Concept
- **THEN** the restored state names the same concept hash it recorded before parking
- **AND** a restored state naming a different concept is rejected
