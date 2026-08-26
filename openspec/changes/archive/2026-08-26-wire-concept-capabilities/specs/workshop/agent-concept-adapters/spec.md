## MODIFIED Requirements

### Requirement: Each adapter is a faithful, drop-in implementation of Concept's existing port

An agent-backed adapter SHALL satisfy the exact same callable contract Concept already relies on for that capability — the same request shape in, the same result shape out, the same failure surfaces. Wiring an agent-backed adapter in place of the existing single-shot one SHALL NOT require any change to Concept, `ConceptContext`, or `ConceptImages`. The only agent-backed adapter this capability now covers is the wish-research one; `concept-images` and `exploded-view-check` are satisfied by the HTTP adapters specified elsewhere.

#### Scenario: Concept cannot tell which kind of adapter it was given

- **WHEN** Concept is wired with the agent-backed wish researcher in place of a differently-sourced one
- **THEN** Concept runs exactly as it does with any other implementation, applying the same validation and sealing rules to the result

#### Scenario: A researched breakdown from the agent-backed researcher still must be attributed

- **WHEN** the agent-backed wish researcher returns a breakdown
- **THEN** every fact in it must still carry a source or a recorded decision, exactly as the existing wish-research attribution rule already requires

## REMOVED Requirements

### Requirement: Each adapter calls the door under Concept's own capability name, never a new one

**Reason**: This requirement covered role-naming for all three agent-backed adapters. Two of them (`AgentConceptArtist`, `AgentExplodeInspector`) are deleted; the one that remains gets its own, narrower requirement below.
**Migration**: See the new "The wish-research adapter calls the door under its own capability name" requirement.

#### Scenario: The wish-research adapter uses the wish-research role

- **WHEN** the agent-backed wish researcher runs
- **THEN** it calls the shared door with role `wish-research`

#### Scenario: The image and inspection adapters use their own capability's role

- **WHEN** the agent-backed artist or inspector runs
- **THEN** each calls the shared door with role `concept-images` or `exploded-view-check` respectively

### Requirement: Concept-images requests stay one image per call

**Reason**: The agent-backed image adapter (`AgentConceptArtist`) is deleted. It was never wired into any Workshop; `concept-images` is now satisfied by exactly one implementation, the OpenRouter-backed artist, whose own one-image-per-call behavior is already specified under `workshop/concept-artist-openrouter`.
**Migration**: No caller migration is needed — nothing depended on the agent-backed image adapter. A caller configuring `concept-images` continues to use the OpenRouter-backed artist directly.

#### Scenario: One request produces one image

- **WHEN** the agent-backed artist receives one `ConceptImageRequest`
- **THEN** it returns exactly one image for that request, written to the path the request specifies

### Requirement: Exploded-view inspection reports only offered component keys

**Reason**: The agent-backed inspector (`AgentExplodeInspector`) is deleted. It was never wired into any Workshop; `exploded-view-check` is now satisfied by exactly one implementation, the OpenAI-compatible inspector, which already reports only offered keys.
**Migration**: No caller migration is needed — nothing depended on the agent-backed inspector. A caller configuring `exploded-view-check` continues to use the OpenAI-compatible inspector directly.

#### Scenario: An unoffered key is never reported

- **WHEN** the agent-backed inspector examines an exploded view
- **THEN** every key in its answer is one of the keys the request offered

## ADDED Requirements

### Requirement: The wish-research adapter calls the door under its own capability name

The wish-research adapter SHALL call the shared door using the role name that capability already carries in a `Need` — `wish-research` — and SHALL NOT introduce a different role name for it.

#### Scenario: The wish-research adapter uses the wish-research role

- **WHEN** the agent-backed wish researcher runs
- **THEN** it calls the shared door with role `wish-research`

### Requirement: The wish-research adapter sends the same task instructions and attribution rules the deleted HTTP researcher used to send

The agent-backed wish researcher SHALL include, in its door request, the research task instructions and attribution rules (every decided fact names a source or a recorded decision, never both, never neither) that were previously sent only by the now-deleted HTTP wish researcher. A launched agent process SHALL NOT be expected to already know the wish-research contract by role name alone.

#### Scenario: The door request carries the research instructions

- **WHEN** the agent-backed wish researcher runs
- **THEN** the request it hands to the door includes the research task instructions and attribution rules text

### Requirement: The shared agent door's environment constructor configures the wish-research role only

Building the shared agent door from the environment SHALL configure only the `wish-research` role. It SHALL NOT read or require any `concept-images` or `exploded-view-check` tool, path, or wall-clock environment configuration, since no adapter calls the door under those roles.

#### Scenario: Building the door requires no image or inspection configuration

- **WHEN** the shared agent door is built from the environment
- **THEN** construction succeeds using only the launch command and the wish-research role's own tool, path, and wall-clock configuration

#### Scenario: A missing wish-research configuration still fails closed

- **WHEN** the shared agent door is built from an environment missing the wish-research role's configuration
- **THEN** construction fails, naming the wish-research role
