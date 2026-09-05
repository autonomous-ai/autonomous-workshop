## Purpose

Let a listing carry the build session behind it, in the shape the Factory replays, only when the run explicitly authorizes disclosure and with host redaction applied.

## ADDED Requirements

### Requirement: Session history ships only under explicit authorization
The system SHALL include `conversation.jsonl` at the root of the Factory import archive only when the run's authorization carries `history_disclosure_requested: true`. Authorization schema 2 SHALL read as `false`. The flag SHALL be settable by `workshop wish --disclose-session` and by an Inventor-account default.

#### Scenario: Default run ships no history
- **WHEN** a run is created without `--disclose-session` and without an account default
- **THEN** the import archive contains no `conversation.jsonl`
- **AND** the receipt records `history_turns: null`

#### Scenario: Authorized run ships history
- **WHEN** the authorization carries `history_disclosure_requested: true`
- **THEN** the import archive root contains `conversation.jsonl`
- **AND** the archive inventory check accepts it as the only `.jsonl`

### Requirement: History is a redacted host projection of the native session
The system SHALL build `conversation.jsonl` from the run's main-thread Codex rollout in Claude Code session shape: one opening user record carrying the exact Wish when Wish disclosure is granted or the public product summary otherwise; user records for host stage Goals; assistant records with text and `tool_use` blocks; user records with `tool_result` blocks; encrypted reasoning, developer messages, runtime events, and subagent payloads omitted or marked `isMeta`. Absolute host paths outside the workspace, credential-shaped strings, and secret-scanner matches SHALL be redacted. Output SHALL respect 200 turns, 5 000 entries, 512 KB per entry, and 12 MB total, and SHALL be ordered by rollout ordinal with stable record ids.

#### Scenario: Prompt derives from the opener
- **WHEN** the Factory derives the listing's originating prompt
- **THEN** it reads the opening user record's text
- **AND** the adapter still omits the import form's `prompt` field

#### Scenario: Oversized tool output survives as a turn
- **WHEN** a tool output exceeds 512 KB in the rollout
- **THEN** the emitted `tool_result` is trimmed below the cap
- **AND** the turn around it is preserved

### Requirement: Replayed turns are verified on readback
The system SHALL, after publish, read the design's turns with the owner token and record `history_turns` in the receipt and status; a count lower than the turns shipped SHALL be a warning, not a publication failure.

#### Scenario: Server drops a malformed entry
- **WHEN** the Factory replays fewer turns than shipped
- **THEN** publication remains successful
- **AND** status shows the shipped and replayed counts
