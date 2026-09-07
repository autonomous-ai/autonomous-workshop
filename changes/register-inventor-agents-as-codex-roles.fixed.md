- The Codex launcher now registers every materialized Inventor custom agent
  (`.codex/agents/<id>.toml`) as a Codex agent role through
  `agents."<id>".config_file`, on start and on resume, because Codex CLI
  0.153.4 does not discover project-scoped custom agents on its own. The
  Manager's `spawn_agent` therefore exposes `agent_type` for every roster
  Inventor instead of parking with a dispatch need. See ADR 0054.
