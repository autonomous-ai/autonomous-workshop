- Grok Build headless turns now use always-approve (`bypassPermissions`)
  instead of `dontAsk`, so shell commands required for CAD and the stage
  finalizer are not cancelled in non-interactive sessions. Live progress
  names the selected Manager instead of always saying Codex.
