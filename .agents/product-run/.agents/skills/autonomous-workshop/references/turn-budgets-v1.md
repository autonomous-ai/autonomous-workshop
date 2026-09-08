# Persistent native-turn budget v1

> **Precedence.** When `MANAGER.json` carries a reasoning effort and
> `token-budget-v1.md` is materialized, the token budget supersedes these turn
> counts, the effort is Wish-wide, and the profile minute figures (including
> the twenty-minute Spark watchdog named below) are pacing targets; every turn
> then runs under a 60-minute emergency watchdog. See `token-budget-v1.md`.

For Codex, the host charges one turn before each native start or resume:
six turns per stage and twelve across the product. A turn is a full native
execution window containing many model messages and tools, not a tool call,
review round, or lifecycle revision. Errors, timeouts and crashes remain
charged. Explicit resume never resets the count; stage revisits share the same
stage allowance. Host-only verification and publication retries use no turn.

These counts replace aggregate native-execution clocks, not the launcher's
frozen timeout. Spark retains a twenty-minute watchdog per turn. This is a
bounded launch allowance, not a token or dollar cap. Missing token usage stays
unavailable, never zero or estimated. All engineering and publication gates
remain mandatory. Other adapters retain their frozen budget policy.
