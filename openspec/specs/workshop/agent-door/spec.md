## Purpose

A real agent door: one capability that runs a named, budgeted role against an actual tool-using agent process and returns its structured result, so any Workshop job that needs an acting agent — not just a single API call — has one real, consistently-shaped thing to configure.

## Requirements

### Requirement: The door runs one named role per call in a fresh, isolated workspace

The door SHALL accept a role name, a JSON-safe request mapping, and a budget in micros, and SHALL execute the configured agent process bound to a workspace directory created fresh for that call. It SHALL NOT reuse a workspace across two different calls, and SHALL NOT let one call observe files left behind by another.

#### Scenario: A call gets a fresh, empty workspace

- **WHEN** the door executes a role
- **THEN** the agent process runs bound to a workspace that contains nothing left over from any earlier call

#### Scenario: Concurrent calls never share a workspace

- **WHEN** two calls run at the same time, for the same or different roles
- **THEN** each runs in its own workspace, and neither can read or write the other's files

### Requirement: Only role-appropriate access is granted, and an unconfigured role fails closed

The door SHALL grant the launched process only the tool and file access configured for the requested role. A role with no configuration SHALL be refused before any process is launched, naming the unconfigured role.

#### Scenario: An unconfigured role never launches a process

- **WHEN** the door is asked to run a role it has no configuration for
- **THEN** it raises an error naming that role
- **AND** no agent process is launched

#### Scenario: A role's access is bounded by its own configuration

- **WHEN** the door executes a configured role
- **THEN** the process it launches carries only the tool and file access that role's configuration grants, never another role's

### Requirement: The result must be the agent's own structured output, never a guess

A call SHALL succeed only when the agent process itself emits exactly one structured JSON result. The door SHALL NOT infer, complete, or fabricate a result from partial output, and SHALL NOT return a result for a role the process did not itself finish.

#### Scenario: No structured result means the call failed

- **WHEN** the agent process exits without emitting a structured result for its role
- **THEN** the door raises an error naming the role
- **AND** it returns no result for that call

#### Scenario: A malformed result fails clearly

- **WHEN** the agent process emits output that does not match the role's declared result shape
- **THEN** the door raises an error naming the role and describing the mismatch, rather than returning the malformed value

### Requirement: Every call is bounded by wall-clock time and by its budget, and the bound is enforced, not advisory

The door SHALL terminate a role's process if it exceeds either the configured wall-clock bound or the caller's `budget_micros` ceiling, and SHALL fail that call rather than letting it run unbounded.

#### Scenario: A run that exceeds its time bound is stopped

- **WHEN** a role's process is still running once its configured wall-clock bound elapses
- **THEN** the door terminates the process
- **AND** it raises an error naming the role and the bound that was exceeded

#### Scenario: A run that would exceed its budget is stopped

- **WHEN** a role's process would spend beyond the `budget_micros` given for that call
- **THEN** the door terminates the process before exceeding it
- **AND** it raises an error naming the role and the budget that was exceeded

### Requirement: Actual cost and duration are always reported, even on failure

The door SHALL report the actual wall-clock time and cost a call consumed, whether the call succeeded, failed, or was terminated for exceeding its bounds, so budgets stay auditable across both outcomes.

#### Scenario: A failed call still reports what it spent

- **WHEN** a role's call fails for any reason after the process started
- **THEN** the door's error or result still carries the actual time and cost that call consumed up to that point

### Requirement: A crashed or misbehaving process fails the call, never a fabricated success

A non-zero exit, a timeout, or a malformed result from the agent process SHALL surface as an error naming the role. The door SHALL NOT retry a failed role silently into an invented success, and SHALL NOT return a partial result as if it were complete.

#### Scenario: A crashed process fails the call

- **WHEN** the launched agent process exits with a non-zero status
- **THEN** the door raises an error naming the role and the process's own failure
- **AND** it does not return a result for that call

### Requirement: Construction requires an explicit, caller-supplied agent process, never a hardcoded one

The door SHALL require the caller to supply the launch command (and any per-role configuration) for the agent process at construction, and SHALL reject construction without one. No vendor, binary, or model is assumed.

#### Scenario: Construction without a launch command is rejected

- **WHEN** the door is constructed with no launch command configured
- **THEN** construction fails
- **AND** no door instance is produced

### Requirement: The process launcher is an injectable seam

The mechanism that actually starts and communicates with the agent process SHALL be an injectable dependency of the door, so a deterministic substitute can serve every documented role without starting a real process or reaching the network.

#### Scenario: A substitute launcher serves every role deterministically

- **WHEN** the door is constructed with a substitute process launcher instead of one that starts a real agent process
- **THEN** every documented role can still be run through the door
- **AND** no real process is started and no network call is made
