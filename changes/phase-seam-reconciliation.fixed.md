- Reconcile the documentation with the code at every phase seam: routes are
  Spark `Wish -> Make -> Release` (default), Forge
  `Wish -> Invent <-> Make -> Release`, and Quest
  `Wish -> Invent <-> Make <-> Playtest -> Release` with a direct
  Playtest -> Invent edge; the CLI flags are `--workflow`, `--agent`,
  `--model`, and `--effort` (reasoning level, default medium); the token cap
  defaults to 30,000,000; every turn of a token-budgeted Codex run ends at a
  60-minute emergency watchdog (ADR 0051) while the profile's minute
  boundaries and 8-turn cap are pacing; reasoning effort is Wish-wide;
  compaction is 64k for Spark and 256k for deep routes; Claude and Grok are
  experimental adapters; there is no Concept stage and Match is folded into
  the first creative stage; Invent seals JSON only; Quest Release uses
  NativeRelease v2 / product.json v4 as its current contract. ADR statuses
  now use the allowed vocabulary, the README lists all 15 Inventor bundles
  and 29 public toys, and an architecture test enforces that.
- Companion code changes in the same reconciliation: Make and Release refuse
  Workshop-internal title/summary vocabulary (`Wish`, `Taste`, `Inventor`,
  `playtest`, `finalizer`) with the same 300-character stripped title rule, backward transitions are
  refused on the final lifecycle round, Invent validates
  `vault_lead_responses`, Spark Make packets carry `vault_leads`, and every
  Manager's `MANAGER.json` records `agent_directory` as `.codex/agents`.
