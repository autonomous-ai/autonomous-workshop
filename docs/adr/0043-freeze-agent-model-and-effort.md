# ADR 0043: Freeze agent, model, and reasoning effort

- Status: Accepted
- Date: 2026-09-05
- Owners: CLI, Runtime, Workflow, and Daydream maintainers
- Supersedes: ADR 0016's public `--effort` route spelling, ADR 0017's public
  `--manager` spelling, and the reasoning-level portion of Codex economics
  profiles for new runs

## Context

The CLI used `--effort` for Spark, Forge, and Quest even though those values
select a lifecycle, not a model reasoning level. It also exposed the runtime as
`--manager` while operators think of Codex, Claude Code, and Grok Build as the
agent they are starting. Neither the model nor its reasoning effort was a
first-class choice, and Claude Code did not receive its supported `--model` and
`--effort` flags.

Model selection must not depend on mutable user configuration or silently
change when a run resumes. Existing product runs must retain the exact runtime
policy they began with.

## Decision

The public start surfaces are:

```text
--workflow spark|forge|quest
--agent codex|claude|grok
--model <model-or-supported-alias>
--effort low|medium|high|xhigh|ultra
```

`workshop start`, `workshop daydream`, and `workshop wish` use the same agent,
model, and reasoning vocabulary. `--workflow` is absent from `daydream`
because a standalone daydream does not execute a product lifecycle.

As of 2026-09-09, `ultra` is supported only with Codex `gpt-6-astra`
(including its `astra` alias), matching the installed Codex 0.153.4 model
catalog. It is passed literally, not mapped to `xhigh` or `max`. Frozen
runtime selection and native launch validation both enforce this restriction.

Codex defaults to `gpt-5.6-sol` at `medium`; `astra`, `sol`, `terra`, and `luna`
are friendly aliases for their exact Codex model ids. Claude Code defaults to
`claude-opus-5` at `medium`; `opus` and `opus-5` resolve to that exact id. Grok
Build retains its pinned `grok-4.6` model and exposes no reasoning-effort
control until its CLI has an equivalent stable contract.

On 2026-09-07 the new-selection reasoning default changed from high to medium.
The model defaults are unchanged. Omitting `--effort` with `--model astra`
now selects Astra/medium. Explicit overrides and frozen run selections retain
their exact reasoning levels; this is not a migration of existing sessions.

For each new product run, the host writes schema-v2 `MANAGER.json` containing
the canonical agent, model, and reasoning effort. That file is immutable,
included in the run input manifest, and revalidated on every checkpoint read.
Resume reconstructs the launcher from those exact bytes unless the operator
has explicitly recorded the supported reasoning override below. Schema-v1
`MANAGER.json` remains readable and continues through the historical
stage-shaped Codex reasoning profiles.

The selected reasoning effort is Wish-wide for new schema-v2 projects. It
overrides the low/medium/high reasoning values in the older Codex economics
profiles, while those profiles continue to govern workflow topology,
compaction, turn boundaries, proof handoffs, and quality gates. Model effort
never changes deterministic evidence requirements or effect authority.

Daydream receives the same resolved runtime choice as the product run created
from it. Daydream remains a separate native session and does not weaken the
one-session rule for the subsequent Wish-wide product run.

Codex receives `--model` plus `model_reasoning_effort`; Claude Code receives
`--model` plus `--effort`. Their private native session checkpoints bind the
selection under each adapter's compatibility rules.

### Explicit reasoning override on resume

As of 2026-09-10, `workshop resume ID --effort medium` can change subsequent
native Manager turns of an unfinished Codex product that originally froze
`token-budget-v1.md`, `budgets-v1.md`, and schema-v2 `MANAGER.json`. Other
supported reasoning values use the same frozen-model validation as new runs.
The operator must wait until the current host invocation stops; the exclusive
run lock rejects a concurrent change. There is no automatic effort change.

The host atomically stores an owner-only `reasoning-effort.json` history,
bound to the exact product, Wish, initial Manager bytes, model, initial effort,
budget profile, workspace, private state root and native thread. Each change
records its previous and new effort, UTC request time, lifecycle checkpoint
and native runtime configuration hash. Repeating the current choice is
idempotent. Omitting the flag preserves the most recent explicit choice,
including after a failed launch. Invalid history or session bindings fail
closed on status and resume.

The original `MANAGER.json`, Wish, materialized instructions, stage evidence,
usage and saved token cap are unchanged. The existing profile-bound native
configuration already allows per-turn reasoning changes, so the override
does not rebind or replace the Codex session. Later instruction-only host tool
refreshes can keep the override; a different frozen budget profile requires
separate migration support and is refused. Historical sessions without this
profile, including token-budget adoption from an older run, are unsupported.

Run receipts and status report the effective setting as `effort` and preserve
the original selection as `initial_effort` when an override exists. The native
continuation prompt names both settings so the original Manager file cannot
be mistaken for the current launch policy. Earlier turns are never relabeled.

## Consequences

- `--effort forge` becomes `--workflow forge`.
- `--manager codex` becomes `--agent codex`.
- `workshop start pico-press --agent codex --model astra --effort high` uses
  `gpt-6-astra` at high effort for both daydream and build.
- `workshop start pico-press --agent claude` resolves to
  `claude-opus-5` at medium effort.
- Status and run receipts expose `workflow`, `agent`, `model`, and `effort`.
- Existing schema-v1 runs remain resumable without acquiring new defaults.

## Verification

- CLI tests cover the new flag names, Codex aliases, manager-specific defaults,
  and rejection of unsupported combinations.
- Runtime tests prove Codex and Claude command construction includes the exact
  selected model and reasoning effort.
- Claude checkpoint tests reject model drift on resume.
- Workflow tests prove schema-v2 `MANAGER.json` is hash-bound and that a new
  run's selected effort overrides a legacy stage reasoning default.
- Override tests prove an ultra-to-medium change resumes the exact thread with
  the same native configuration hash, survives retries and instruction-only
  rebinds, preserves usage and frozen bytes, and rejects invalid private records.
- Schema-v1 parser coverage proves historical runtime configuration remains
  represented as legacy rather than silently defaulted.
