# ADR 0054: Register materialized Inventor agents as Codex agent roles

- Status: Accepted
- Date: 2026-09-07
- Owners: Codex runtime and product-run protocol maintainers

## Context

The host materializes every eligible Inventor into the run root as
`.codex/agents/<id>.toml`, the constitution names that directory the sole
Inventor roster, and the Match assignment binds the exact file. The runtime
documentation assumed Codex discovers those project-scoped custom agents on
its own.

It does not. Probing Codex CLI 0.153.4 with a throwaway run root showed that
`spawn_agent` exposes no `agent_type` parameter, `list_agents` reports only
the root agent, and an explicit `agent_type` fails with `unknown agent_type`
whether the run root is the working directory, a git root, or an explicitly
trusted project, and with `multi_agent_v2` on or off. Custom agents load only
from `$CODEX_HOME/agents/` or from an explicit
`agents."<name>".config_file = "<path>"` configuration entry; with either,
`agent_type` appears in the schema and the custom agent answers with its own
instructions.

Earlier runs hid the gap: their Managers spawned a generic subagent named
after the Inventor and carried on. The first pinned Spark run
(wish-20260907-053241-4d3a50df, ferro-line, `gpt-6-astra` at medium effort)
refused instead and parked at Make with a host need, which is the honest
outcome the constitution asks for.

## Decision

`inventor_agent_config_arguments(run_root)` lists every regular
`<id>.toml` in the run's `.codex/agents` directory and emits one
`--config agents."<id>".config_file="<absolute path>"` pair per file; the
Codex launcher appends those pairs to both the start and the resume command.
Symlinks, other file names, and a missing directory register nothing. The
key is accepted under `--strict-config`, and `--ignore-user-config` does not
suppress it.

The pairs are derived from files already hash-bound in the run manifest, so
they are not added to the launch-policy identity (`_runtime_config_sha256`);
sessions checkpointed before this change keep a valid binding and gain the
roles on their next resume.

## Consequences

- `spawn_agent` now offers `agent_type` with every roster Inventor, so the
  Manager can dispatch the exact host-materialized custom agent the
  constitution requires; a pinned run can no longer park on the missing
  selector.
- The runtime documentation no longer claims native project-scoped discovery;
  it describes the host registration.
- The parked microduck run keeps its need on record; the fix applies from its
  next resume or from a fresh run.
