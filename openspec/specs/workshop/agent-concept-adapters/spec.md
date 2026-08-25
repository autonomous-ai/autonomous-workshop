## Purpose

Adapters that satisfy Concept's existing wish-research, concept-images, and exploded-view-check ports by dispatching through a shared agent door, so one configured agent can serve Concept's capabilities on the same terms it serves Make and Playtest.

## Requirements

### Requirement: Each adapter is a faithful, drop-in implementation of Concept's existing port

An agent-backed adapter SHALL satisfy the exact same callable contract Concept already relies on for that capability — the same request shape in, the same result shape out, the same failure surfaces. Wiring an agent-backed adapter in place of the existing single-shot one SHALL NOT require any change to Concept, `ConceptContext`, or `ConceptImages`.

#### Scenario: Concept cannot tell which kind of adapter it was given

- **WHEN** Concept is wired with an agent-backed wish researcher, artist, or inspector in place of the existing single-shot one
- **THEN** Concept runs exactly as it does with the existing adapter, applying the same validation and sealing rules to the result

#### Scenario: A researched breakdown from the agent-backed researcher still must be attributed

- **WHEN** the agent-backed wish researcher returns a breakdown
- **THEN** every fact in it must still carry a source or a recorded decision, exactly as the existing wish-research attribution rule already requires

### Requirement: Each adapter calls the door under Concept's own capability name, never a new one

An agent-backed adapter SHALL call the shared door using the role name that capability already carries in a `Need` — `wish-research`, `concept-images`, or `exploded-view-check` — and SHALL NOT introduce a different role name for the same capability.

#### Scenario: The wish-research adapter uses the wish-research role

- **WHEN** the agent-backed wish researcher runs
- **THEN** it calls the shared door with role `wish-research`

#### Scenario: The image and inspection adapters use their own capability's role

- **WHEN** the agent-backed artist or inspector runs
- **THEN** each calls the shared door with role `concept-images` or `exploded-view-check` respectively

### Requirement: Concept-images requests stay one image per call

The agent-backed artist SHALL request and return exactly one image per `ConceptImageRequest`, written into that request's own workspace location, matching the ordering and anchoring the existing artist contract already provides — each image after the first still anchors on the ones already drawn.

#### Scenario: One request produces one image

- **WHEN** the agent-backed artist receives one `ConceptImageRequest`
- **THEN** it returns exactly one image for that request, written to the path the request specifies

### Requirement: Exploded-view inspection reports only offered component keys

The agent-backed inspector SHALL report only component keys the request actually offered, and SHALL NOT report a key the request did not name as visible.

#### Scenario: An unoffered key is never reported

- **WHEN** the agent-backed inspector examines an exploded view
- **THEN** every key in its answer is one of the keys the request offered

### Requirement: Concept keeps taking exactly one implementation per capability

Adding an agent-backed alternative SHALL NOT change Concept's existing shape of taking exactly one `WishResearcher`, one `ConceptArtist`, and one `ExplodeInspector` at a time. Choosing which implementation serves a capability is a caller's wiring decision, made once, outside Concept.

#### Scenario: A Workshop is wired with one implementation per capability

- **WHEN** a Workshop is configured
- **THEN** each of Concept's three capabilities is satisfied by exactly one adapter, agent-backed or not
- **AND** nothing inside Concept selects or blends between two candidates for the same capability
