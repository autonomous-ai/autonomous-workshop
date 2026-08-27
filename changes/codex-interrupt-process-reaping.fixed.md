- Reap every process group in the launch-identity-bound native Codex POSIX
  session when a Workshop command is interrupted by Ctrl-C or another graceful
  host unwind, including the built-in code-mode helper, while preserving an
  already checkpointed session for explicit `workshop resume` and refusing to
  signal a reused session leader.
