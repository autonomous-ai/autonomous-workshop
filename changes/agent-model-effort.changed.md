- Rename the CLI selectors to `--workflow` and `--agent`, add frozen
  `--model` and model `--effort` choices, and default Codex to Sol and
  Claude Code to Opus 5. The initial high default was lowered to medium for
  both (see `default-reasoning-effort.changed.md`).
- Exhaustively mock every supported workflow/agent/model/effort combination
  through `workshop start`, `workshop wish`, immutable run configuration, and
  the native-launcher boundary without invoking a model.
