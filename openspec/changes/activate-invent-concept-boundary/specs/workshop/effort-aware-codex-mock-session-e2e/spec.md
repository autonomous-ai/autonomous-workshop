## ADDED Requirements

### Requirement: Real Codex acceptance authors Concept inside the same Invent turn

The operator-run real-Codex mock-session acceptance tier SHALL demonstrate that one authenticated persistent session can read a marked Forge or Quest Invent packet, use the selected Inventor, author exact assignment/invention and complete pre-render Concept source, invoke the compound finalizer, return control without provider credentials, and resume the same session at Make after the host seals Concept images. It MUST NOT launch a Concept turn, a second root session, or a host-side cognitive worker.

#### Scenario: The host completes Concept rendering after Invent returns
- **WHEN** the real Codex turn finalizes valid pre-render source
- **THEN** host effect doubles render and seal the Concept outside the subprocess
- **AND** the same recorded session id resumes at Make with the sealed Concept packet binding

#### Scenario: The native turn tries to finalize incomplete source
- **WHEN** required Concept documents or roles are missing
- **THEN** the materialized finalizer fails inside the active Invent Goal
- **AND** no host renderer is called

### Requirement: Real Codex acceptance covers Invent effect wait and resume

The acceptance tier SHALL exercise at least one Concept image-effect wait in which the exact Invent proposal, checkpoint, session id, and durable effect state survive command exit. Resume SHALL reconcile completed operations, avoid resending ambiguous ones, finish any safely absent work, seal the exact Concept, and continue the original run without repeating Invent cognition.

#### Scenario: Resume follows a provider interruption
- **WHEN** rendering pauses after some roles are durably completed
- **THEN** status reports a wait at `invent` without exposing prompts, image bytes, operation ids, or credentials
- **AND** resume reconciles before continuing the same proposal

### Requirement: Acceptance assertions bind exact artifacts rather than transcript claims

The real-Codex tier SHALL verify success from the checkpoint-bound outcome, exact Concept source and image manifests, effect receipts, sealed Concept identity, Made Concept binding, and host gate evidence. Chat prose, terminal exit, provider response text, and model self-assessment MUST NOT substitute for those bytes.

#### Scenario: Codex claims completion without a valid compound proposal
- **WHEN** the session returns prose saying Concept is complete but required exact artifacts or receipts are absent
- **THEN** the run does not advance from Invent
