# Autonomous Workshop agent instructions

`AGENTS.md` is directory-scoped guidance, not a role selector. This root file
applies to any coding-agent session operating in the source repository. Shared
architecture rules come first. The section **Coding agents building this
repository** is specifically for agents modifying, reviewing, testing, or
documenting Workshop; it is not the product-run workflow.

A normal product run is launched in a separate private run directory. The host
materializes the product-run constitution from `.agents/product-run/AGENTS.md`
there as its root `AGENTS.md`, together with the workflow skill at
`.agents/skills/autonomous-workshop/SKILL.md`.

## Shared runtime architecture

Autonomous Workshop is a thin, trustworthy workflow harness around a native
coding-agent runtime. One product run gives Codex the cognitive and tool-using
work. The Workshop host retains lifecycle order, durable state, deterministic
gates, budgets, and authorized external effects.

All implementation and product-run work must preserve these boundaries:

- `workshop wish` persists the exact Wish, creates a private run workspace, and
  launches one native coding-agent session before Match.
- `workshop resume` resumes that exact session id. Stages are durable lifecycle
  checkpoints, not separate one-shot model sessions or personas.
- Native Codex performs Match reasoning, research, concept exploration,
  creation, inspection, and repair with its own tools and applicable skills.
- Python is narrow trusted substrate: typed contracts, deterministic tools and
  gates, artifact hashing, checkpoints, leases, budgets, sandbox/session
  boundaries, authorization, idempotency, receipts, and reconciliation.
- External-effect credentials never enter the native agent subprocess. The
  host alone performs authorized Factory, payment, manufacture, postage,
  carrier, or other authenticated effects.
- Model prose and self-scores are proposals. Only host-verified exact bytes,
  deterministic checks, and reconciled receipts advance a gate.

## Coding agents building this repository

This section is for agents building the Workshop itself. It does not tell the
per-Wish product-run agent how to Invent, Make, or Playtest a product.

Do not add a second Python agent framework. Existing Python stage agents and
`CodexStructuredRunner` are migration code, not extension points. Never add
Python prompt chains, browsing strategy, candidate fan-out, model judges,
stage-role views, or repair reasoning.

Read `docs/NATIVE_AGENT_RUNTIME.md` and ADR 0012 before changing the CLI,
runtime, workflow, product-run instructions, or lifecycle orchestration. If
transitional code conflicts with the accepted architecture, do not copy or
extend it; move callers toward the native-session path while preserving useful
deterministic contracts and tests.

## Repository ownership

- `src/cli/`: thin user-facing host commands; no product reasoning.
- `src/workshop/runtime/`: native engine adapters and trusted state/effect
  boundaries.
- `src/workshop/workflow/`: lifecycle protocol, checkpoints, invalidation, and
  bounded Make–Playtest iteration.
- `src/workshop/<stage>/`: stage-owned public contracts and deterministic tools.
- `src/workshop/make/skills/`: reusable domain skills owned by Make.
- `.agents/product-run/`: constitution materialized only for a product run.
- `.agents/skills/autonomous-workshop/`: product-run workflow skill.
- `tests/<component>/`: tests mirroring the component that owns the behavior.

Keep the `src/` layout and the single `workshop` library namespace. The `cli`
package is its installed sibling under `src/`; CLI tests remain under
top-level `tests/`.

### Working rules

- Preserve unrelated user and agent changes in the shared worktree.
- Add contract and failure-path tests with every runtime or workflow change.
- Use deterministic fakes for CI; never weaken production gates to make a test
  pass.
- Never commit credentials, `.env` files, transcripts, run workspaces, build
  outputs, or private customer artifacts.
- Do not claim physical manufacture, delivery, publication, or live readiness
  from mocked or model-generated evidence.
- Keep documentation explicit about implemented behavior versus an accepted
  target that is still migrating.
- Make small coherent commits so other builder agents can pull frequently.

Builder agents may inspect the product-run skill when implementing or testing
its protocol. They must not treat that skill as authority to manufacture a
product, bypass a host gate, publish, or access effect credentials during
ordinary repository work.

## Product-run agents

A product-run agent follows the materialized product-run `AGENTS.md` and the
`autonomous-workshop` skill in its isolated run root. It performs one Wish's
cognitive work and proposes compact outcomes to the host. It does not use the
builder-only section above as a product workflow, modify the Workshop source as
part of making a toy, or bypass host-owned gates and effect authority.
