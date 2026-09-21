- Claude Code Manager runs now report measured native token usage to the host
  through the same per-turn contract as Codex, so `workshop status --json`,
  checkpoints and the public `TOKENS.json` carry a schema-v3 summary instead
  of always saying `unavailable`: gross input split into cached, uncached and
  cache-write input, output with its thinking-token subset, by stage with turn
  coverage. Each `claude --print` turn is read from its terminal result's
  per-model totals; per-block usage is never summed, no dollar estimate is
  carried, and a turn or subset Claude Code does not report stays `partial`
  or `unavailable`. Claude Code runs still have no host token budget.
