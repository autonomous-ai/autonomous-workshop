# ADR 0043: New runs freeze gpt-6-astra

- Status: Accepted
- Date: 2026-09-06
- Owners: Runtime and product-run protocol maintainers

## Context

Every Workshop run pins its Codex model in code: the launcher defaulted to
`gpt-5.6-sol`, passed it as `--model` with `--ignore-user-config`, and bound
it into the run's frozen `runtime_config_sha256`. The operator's own Codex
sessions on the same host already run `gpt-6-astra`, and the shop-side
pipelines have moved on as well. A live `codex exec` on `gpt-6-astra` at
`model_reasoning_effort="high"` (CLI 0.153.4) completed normally and
reported the same 258,400-token context window as `gpt-5.6-sol`, so the
256k deep compaction ceiling from ADR 0037 still fits.

## Decision

New runs freeze `gpt-6-astra`.

- `DEFAULT_WORKSHOP_MODEL` is `gpt-6-astra`; the launcher default, the
  installed-CLI acceptance check, and the runtime tests follow it.
- The `gpt-5.6-*` names remain in `ALLOWED_WORKSHOP_MODELS` so checkpoints
  recorded before this change still validate and tests can still exercise
  them explicitly.
- The per-stage reasoning schedule, turn boundaries, and the deep-economics
  profile are unchanged. The first Forge run on the new model is watched for
  compaction and turn-time drift before any profile is retuned.

## Compatibility and verification

- The model is part of each run's frozen runtime config, exactly as the
  Codex CLI version is. A run started on `gpt-5.6-sol` that has not
  completed cannot be resumed by a host whose launcher freezes
  `gpt-6-astra`; it fails closed with a runtime-config mismatch, the same
  outcome a CLI upgrade already produces. Completed runs are unaffected.
- No model override exists in the environment or CLI; changing the model is
  a code change on purpose, so a run's model is never a host-local surprise.
