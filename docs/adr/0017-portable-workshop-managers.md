# ADR 0017: Portable Workshop Manager runtimes

- Status: Accepted
- Date: 2026-08-27
- Owners: Runtime, Workflow, CLI
- Relates to: ADR 0012 (native session), ADR 0016 (effort routes)

## Context

Workshop's production Manager is one native Codex session per Wish. Claude Code
and Grok Build should plug into the same host boundary without becoming a
second Python agent framework and without reviving Match-as-a-turn or required
Playtest. An earlier adapter branch targeted a superseded lifecycle and reused
ADR number 0013, which on `main` already means manual-first Release.

## Decision

Freeze one Manager runtime on each new run (`manager_id` on the host
checkpoint, default `codex`). The CLI accepts `--manager {codex,claude,grok}`.
Resume cannot switch Managers.

A `NativeSessionLauncher` port owns start/resume, session checkpoint filename,
and subprocess isolation. Codex remains the default and is behavior-compatible
with ADR 0012/0016. Claude Code and Grok Build are experimental adapters until
a private Forge Wish completes on each.

Host authority is unchanged: effort routes, `STAGE.json`, deterministic gates,
Factory publication, and credentials. Adapters must not emulate Goals in
Python. One native Goal is active at a time; Inventors remain native subagents.

Canonical Inventor source stays under `inventors/`. Codex still materializes
`.codex/agents/*.toml` as the identity binding. `MANAGER.json` records which
runtime the run froze.

## Alternatives considered

### Merge `codex/grok-manager-runtime`

Rejected: 69 commits behind, Match/Playtest lifecycle, ADR 0013 collision.

### Make Grok or Claude the default

Rejected: Codex is the implemented production Manager.

## Consequences

`workshop wish` without `--manager` still starts Codex. Doctor treats Codex as
required and Claude/Grok as optional adapter health. Unknown Manager ids fail
closed before Wish materialization.

## Compatibility and migration

Older checkpoints without `manager_id` resume as Codex. New runs write
`manager_id` and `MANAGER.json`.

## Verification

Deterministic launcher tests with fake CLIs, registry tests, CLI `--manager`
plumbing, and the existing Codex native host/E2E suite.
