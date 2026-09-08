- Add `workshop wish --agent {codex,claude,grok}` (introduced as `--manager`
  and renamed by ADR 0043) so a run freezes one native Manager runtime. Codex
  remains the default and production path. Claude Code and Grok Build are
  experimental adapters to the same host gates that run a flat launcher under
  the legacy command clocks; resume cannot switch Managers.
