# ADR 0044: Portable autonomous stage objectives

- Date: 2026-09-07
- Status: Implemented protocol; non-Codex live acceptance remains experimental
- Supersedes: the Codex-specific Goal interface requirement in ADR 0017 for
  new runs containing `manager-runtime-v1.md`

The Sonnet trial discovered that the common instructions required a Codex Goal
API that Claude's native tools did not expose. It searched for that API before
product work. The common constitution also hardcoded the Codex roster path.

New runs freeze a runtime reference that defines one native stage objective.
Codex keeps its actual Goal API. Other Managers pursue the same objective in
their persistent native session, with native task tracking when available.
No fake Goal file, Python reasoning loop, model call or scheduler is added.
The host selects the portable launch prompt only for the new capability;
unmarked runs retain their exact previous launch prompt and materialized files.

MANAGER.json supplies roster paths. The agent resolves ordinary design choices
from Wish/Taste/evidence, saves work in the run workspace, and returns a stage
proposal or typed need without requiring builder chat. Mandatory independent
review remains mandatory; it is explicitly excluded from advice to avoid
blocking on optional creative delegation. Goal/task completion never advances
a host gate. All CAD, artifact, review, manual and publication contracts remain.

This removes an interface mismatch; it does not establish that every model or
experimental adapter can complete every Wish. A missing necessary tool or
independent-review capability still requires a truthful waiting outcome.
