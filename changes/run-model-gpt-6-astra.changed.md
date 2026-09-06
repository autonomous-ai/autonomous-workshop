- New runs freeze `gpt-6-astra` as the Codex model (was `gpt-5.6-sol`); the
  reasoning schedule, turn boundaries, and 256k compaction ceiling are
  unchanged, and `gpt-5.6-*` names stay accepted for runs recorded earlier.
  An incomplete run started on the old model cannot be resumed by the new
  host, the same fence a Codex CLI upgrade already applies (ADR 0043).
