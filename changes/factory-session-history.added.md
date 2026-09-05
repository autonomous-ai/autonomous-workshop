- Ship a run's redacted build session with the Factory import when the run
  was started with `workshop wish --disclose-session` (run authorization
  schema 3, `history_disclosure_requested`). The host projects the main Codex
  rollout into a Claude-Code-shaped `conversation.jsonl` at the archive root:
  the Wish as the opening prompt, host stage Goals, visible replies, and tool
  calls with bounded outputs; reasoning, developer instructions, runtime
  events, banners, and subagent traffic are omitted, host paths and secrets
  redacted, and the Factory's replay caps applied. The shop replays it as the
  listing's turns; the publish readback records `history_turns`.
