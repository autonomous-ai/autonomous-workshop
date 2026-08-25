## ADDED Requirements

### Requirement: Concept does its work in one order: research, then brief, then images

Within a round, the Concept job SHALL research the Wish, lock the brief from that research, and only then draw. No image SHALL be requested before the brief is locked, and no fact SHALL be locked before the research that decides it has returned.

#### Scenario: Nothing is drawn before the brief is locked

- **WHEN** Concept runs a round
- **THEN** the wish-research capability is called before the brief exists
- **AND** the image capability is not called until the brief is locked

#### Scenario: A refining round starts from the standing research

- **WHEN** Concept runs a round carrying a concept from an earlier round
- **THEN** it does not research the Wish again
- **AND** it revises the standing brief instead of locking a new one

## MODIFIED Requirements

### Requirement: Concept waits truthfully when it cannot draw

Concept SHALL NOT invent, describe, or placeholder a design it cannot actually research or visualize. When a capability needed to produce a concept is not configured, the job SHALL raise `WaitingFor` carrying a `Need` for each missing capability whose job is `concept` and whose instructions name what is missing, and the Workshop SHALL park the run as waiting rather than proceeding to Make.

The capabilities Concept requires are the wish research its brief is derived from, the image provider its views are drawn by, and the exploded-view check its component views depend on. A missing researcher SHALL be reported on the same terms as a missing artist: Concept SHALL NOT fall back to default physical facts in place of research that did not happen.

#### Scenario: No image provider is configured

- **WHEN** the Concept job runs with no concept image provider available
- **THEN** it raises `WaitingFor` with a `Need` for job `concept` and capability `concept-images`
- **AND** the run is recorded as waiting at job `concept`
- **AND** Make is not called for that round

#### Scenario: No wish researcher is configured

- **WHEN** the Concept job runs with no wish-research capability available
- **THEN** it raises `WaitingFor` with a `Need` for job `concept` and capability `wish-research`
- **AND** the run is recorded as waiting at job `concept`
- **AND** no brief is locked and Make is not called for that round

#### Scenario: Several capabilities are missing at once

- **WHEN** the Concept job runs with no researcher, no image provider, and no exploded-view check
- **THEN** it raises `WaitingFor` carrying a `Need` for each of them
- **AND** the run is recorded as waiting at job `concept` with all of those needs

#### Scenario: The provider fails to produce a required view

- **WHEN** the image provider returns without producing one of the required images
- **THEN** Concept fails rather than returning a partial concept
- **AND** no `ConceptImages` is handed to Make

#### Scenario: Waiting is reported with the round intact

- **WHEN** Concept waits in round N
- **THEN** the recorded run reports job `concept`, round N, and the raised needs

### Requirement: A run records which concept its build came from

The Workshop SHALL record the sealed identity of the concept used for each round alongside the round's other evidence, so that a delivered product can be traced to the concept it was built to, and to the research that concept's facts were decided from. A run that resumes after waiting SHALL restore the same concept identity rather than silently building against a different one.

The Workshop SHALL also record the derived Wish the research produced, naming both it and the routed Wish it was derived from, so that the words a person actually wished and the constraints research added to them stay separable.

#### Scenario: The concept identity is recorded

- **WHEN** Concept completes for a round
- **THEN** the run records that concept's content-addressed hash

#### Scenario: The derived Wish is recorded beside the routed one

- **WHEN** Concept completes for a round
- **THEN** the run records the derived Wish carrying the researched constraints
- **AND** it records the routed Wish's hash unchanged

#### Scenario: Resume carries the concept forward

- **WHEN** a run is resumed after parking downstream of Concept
- **THEN** the restored state names the same concept hash it recorded before parking
- **AND** a restored state naming a different concept is rejected
