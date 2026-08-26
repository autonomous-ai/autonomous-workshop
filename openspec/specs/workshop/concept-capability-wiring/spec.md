## Purpose

The one committed entry point that assembles Concept's three capabilities into a ready-to-use Concept job, choosing HTTP adapters for image generation and exploded-view inspection and the agent door for wish-research, so no caller needs to hand-construct this mix themselves.

## Requirements

### Requirement: The entry point wires images and exploded-view-check to the HTTP adapters and wish-research to the agent door

Building Concept's capabilities through this entry point SHALL satisfy `concept-images` with the existing OpenRouter-backed artist and `exploded-view-check` with the existing OpenAI-compatible inspector, and SHALL satisfy `wish-research` with the agent-door-backed researcher. It SHALL NOT substitute a different implementation for any of the three, and SHALL NOT leave any of the three unconfigured.

#### Scenario: A default call wires the expected implementation to each capability

- **WHEN** the entry point is called with a fully configured environment
- **THEN** the returned Concept capability draws images and inspects exploded views through the HTTP adapters
- **AND** it researches wishes through the agent-door adapter

#### Scenario: The returned capability is usable as Concept's job directly

- **WHEN** the entry point's result is installed as a Workshop's Concept capability
- **THEN** a Wish can be researched, drawn, and inspected through it exactly as through any other fully configured Concept job

### Requirement: Construction fails closed, naming whichever capability's configuration is missing

If any of the three capabilities' required configuration is absent, constructing through this entry point SHALL fail before any of the three is exercised, and the failure SHALL name which capability's configuration is missing. It SHALL NOT return a Concept capability that is only partially configured, and SHALL NOT substitute a default or placeholder for the missing configuration.

#### Scenario: Missing image-generation configuration fails before any capability runs

- **WHEN** the environment has no configuration for the OpenRouter image adapter
- **THEN** the entry point fails, naming the concept-images capability
- **AND** no wish-research or exploded-view-check call is made

#### Scenario: Missing agent-door configuration fails before any capability runs

- **WHEN** the environment has no launch command configured for the agent door
- **THEN** the entry point fails, naming the wish-research capability
- **AND** no concept-images or exploded-view-check call is made

#### Scenario: Missing exploded-view-check configuration fails before any capability runs

- **WHEN** the environment has no configuration for the exploded-view inspector
- **THEN** the entry point fails, naming the exploded-view-check capability
- **AND** no wish-research or concept-images call is made
