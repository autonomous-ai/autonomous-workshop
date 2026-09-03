## MODIFIED Requirements

### Requirement: Authenticated mock sessions validate current selectable routes
The authenticated real-Codex mock-session runner SHALL validate Spark, Forge, and Quest using their current frozen stage-specific launcher economics while retaining one native session identity and the canonical lifecycle route.

#### Scenario: Forge acceptance follows direct Make
- **WHEN** authenticated Forge acceptance runs
- **THEN** its trace is `Invent -> Make -> Release` in one session
- **AND** it contains one high-reasoning Make Goal finalized normally
- **AND** it contains no proof turn, proof marker, proof receipt, or source-handoff phase

#### Scenario: Quest acceptance follows direct Make
- **WHEN** authenticated Quest acceptance runs
- **THEN** its trace is `Invent -> Make -> Playtest -> Release` in one session
- **AND** direct high-reasoning Make advances to unchanged medium-reasoning Playtest and Release boundaries
- **AND** no proof state is fabricated

#### Scenario: Stage reasoning changes by contract
- **WHEN** a deep acceptance trace is audited
- **THEN** one model and one session identity are required across turns
- **AND** high reasoning is expected for Invent and Make
- **AND** medium reasoning is expected for later stages

### Requirement: Acceptance audit rejects fabricated proof state
The acceptance helper SHALL reject current Forge/Quest traces that write `.make-proof-ready.json`, write under `review/early-proof/`, or create host-owned proof-acceptance state.

#### Scenario: A helper fabricates a proof marker
- **WHEN** a current-profile acceptance helper writes `.make-proof-ready.json`, a proof-acceptance receipt, or host proof state
- **THEN** acceptance fails rather than masking the production contract

#### Scenario: Make uses private CAD scratch
- **WHEN** current Make writes temporary engineering bytes under its agent-owned `.cad-scratch/` directory
- **THEN** the ownership audit permits those Make-only writes
- **BUT** the permission does not extend to host state or historical proof paths
