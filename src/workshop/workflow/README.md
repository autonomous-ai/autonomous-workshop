# Workflow

Owns frozen Spark/Forge/Quest sequencing, optional-stage pass-through, bounded
Make–Playtest feedback, durable checkpoints, and the
trusted whole-run host in `native_run.py`. The host composes native-session,
deterministic-gate, and authorized-effect boundaries without taking over Codex
reasoning. Stage contracts and deterministic tools remain in their owning
components.

The CLI calls Workflow's public start, resume, and status functions; Workflow
never imports the CLI.

Effort-aware runs use `workflow.effort` as deterministic route policy. It does
not perform reasoning: disabled stages simply have no turn, artifact, or gate.
