- Rename the CLI selectors to `--workflow` and `--agent`, add frozen
  `--model` and model `--effort` choices, and default Codex to Sol/high and
  Claude Code to Opus 5/high.
- Exhaustively mock every supported workflow/agent/model/effort combination
  through `workshop start`, `workshop wish`, immutable run configuration, and
  the native-launcher boundary without invoking a model.
