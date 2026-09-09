- Let the Claude Manager run its stage. The launcher passed only
  `--permission-mode acceptEdits`, which auto-denies every prompting tool under
  `--print`, so Bash was refused and no stage whose finalizer runs a script
  could ever complete: a run could author CAD sources and then stall forever
  before generation, export, rendering, verification, and `agent-outcome.json`.
  The mode is now `auto`.
- Deny mutation of host-owned bytes in the Claude Manager's run root
  (`STAGE.json`, `WISH.json`, `AGENTS.md`, `MANAGER.json`, `.agents/**`,
  `.claude/**`) for `Edit`, `Write`, and `NotebookEdit`. `acceptEdits` had
  auto-approved those writes, so the host/agent boundary the Grok Manager
  enforces was previously absent here. Reads stay allowed: the Manager must
  read `STAGE.json` every turn.
- Build those deny rules as absolute paths under the exact run root. Claude
  Code silently ignores a bare filename or a `**/`-prefixed glob in a
  permission rule, so the Grok Manager's `Edit(STAGE.json)` spelling would have
  produced a rule that reads as protection while protecting nothing.
- Record the Claude session id as soon as the CLI reports it rather than after
  a successful turn. A turn that failed previously left the checkpoint holding
  a placeholder id the CLI never created, so every later `workshop resume`
  failed with "No conversation found" and the run could not be continued at
  all.
- Report the CLI's own diagnosis on a failed Claude turn instead of only
  "Claude Code reported an error turn".
