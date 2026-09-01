## Purpose

The host-side adapter that turns the drawing instructions a concept authored into the actual image set that concept ships. It is transport and verification only: it carries what the native session specified to an image provider, checks what comes back, and seals it — so the Workshop can visualize a design without the host ever deciding what the design looks like, and without a credential ever reaching the agent.

## Requirements

### Requirement: Concept provider execution remains unavailable while dormant

No Concept image adapter SHALL be executable in this change. Importing, parsing, or evaluating Concept contracts MUST NOT load provider configuration, read a credential, open a network connection, transmit private bytes, write effect state, or invoke an external effect. A future adapter may run only through a durable authorized host-effect boundary implemented before the compound creative-stage Concept boundary is activated.

#### Scenario: Dormant evaluation runs with provider credentials configured
- **WHEN** the contract parser or structural evaluator is invoked
- **THEN** it does not inspect or use those credentials
- **AND** it performs no provider request

#### Scenario: Rendering is requested before the effect boundary exists
- **WHEN** a caller attempts to execute Concept rendering through Workshop
- **THEN** the capability is unavailable and no transmission occurs
