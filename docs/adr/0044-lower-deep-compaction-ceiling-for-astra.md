# ADR 0044: Lower the deep compaction ceiling to 192k

- Status: Accepted
- Date: 2026-09-06
- Owners: Runtime, workflow, and product-run protocol maintainers
- Supersedes: the 256k ceiling from ADR 0037 for every deep profile from v9 on

## Context

ADR 0037 raised the automatic compaction ceiling of Forge and Quest sessions
to 256,000 tokens. That value sits above 90% of the 258,400-token context
window that both `gpt-5.6-sol` and `gpt-6-astra` report, so it never fired
by itself; deep sessions on sol survived long Make work only because Codex
compacted when the provider rejected an oversized request. The Ouray run of
2026-09-05 reached 225k of context and compacted six times that way.

The first Forge run on `gpt-6-astra` (ADR 0043) never compacted. Its Make
round 4 turn failed twice in a row at the first model call that started above
roughly 210k tokens: Codex reported `turn.failed` after seven to ten minutes
of silence, the host saw no transient transport diagnostic, and every resume
grew the thread by another 12k tokens with a cold prompt cache. Nothing on
the host side was at fault: no memory pressure, the weekly quota at 38%, and
the run's product state intact on disk. The error-driven compaction that
rescued sol is not a contract Workshop can rely on.

## Decision

`DEEP_AUTO_COMPACT_TOKEN_LIMIT` is 192,000 tokens, roughly 75% of the window,
leaving about 66k tokens for one call's reasoning and output before Codex
compacts. It applies to every deep profile from v9 through v13 and to
in-flight runs on those profiles when they resume.

This is not a new profile. The ceiling is a launcher setting passed as
`--config model_auto_compact_token_limit`; for deep runs the frozen
`runtime_config_sha256` binds the profile file hash and not the ceiling, so an
existing run keeps its identity, its bound thread, and its round budget. The
older 24k and 16k ceilings of v1 through v8 are unchanged.

## Consequences

- Deep sessions compact a few times per long Make instead of failing; that is
  the behaviour sol runs already had, now made explicit for astra.
- Interrupted astra runs on v9 to v13 resume with the lower ceiling and
  compact on their next completed model call.
- Compaction still costs working context. If a run shows repeated
  same-session recovery loss after compaction, tune the deep profile's prompts
  or lower the reasoning effort in a new profile version rather than raising
  the ceiling back toward the window.

## Verification

`tests/workflow/test_effort.py` pins the new constant; the launcher selection
tests in `tests/workflow/test_native_host.py` import it and prove v9+ profiles
receive it while v4 and earlier keep their legacy ceilings.
