# Autonomous Workshop agent instructions

`AGENTS.md` is directory-scoped guidance, not a role selector. This root file
applies to any coding-agent session operating in the source repository. Shared
architecture rules come first. The section **Coding agents building this
repository** is specifically for agents modifying, reviewing, testing, or
documenting Workshop; it is not the product-run workflow.

A normal product run is launched in a separate persistent toy project. The host
materializes the canonical `.agents/product-run/` sources there as the selected
Manager's native agent and skill projection, plus immutable `MANAGER.json`.

## Shared runtime architecture

Autonomous Workshop is a thin, trustworthy workflow harness around a native
coding-agent runtime. Codex and Claude Code are implemented Manager runtimes;
later runtimes use the same boundary. One product run gives the
selected runtime the cognitive and tool-using work. The Workshop host retains
lifecycle order, durable state, deterministic gates, budgets, and authorized
external effects.

The selected root native session is the Workshop Manager. It may use that
runtime's native subagents for bounded parallel or specialist work, including
matching and working as the selected Inventor. Those agents remain children of
the one product-run session; they are not Python workers or separately launched
Manager processes.

All implementation and product-run work must preserve these boundaries:

- `workshop wish` persists the exact Wish, creates a private run workspace, and
  launches one native coding-agent session before Match.
- `workshop resume` resumes that exact session id. Stages are durable lifecycle
  checkpoints, not separate one-shot model sessions or personas.
- The selected native Manager performs Match reasoning, research, concept exploration,
  creation, inspection, and repair with its own tools and applicable skills.
- The universal digital Playtest baseline is `agent-playtest`,
  `mechanical-check`, and `printability-check`, as returned by
  `ToyBlueprint.required_playtest_checks()`. Manager-authored assessment is not
  evidence of successful printing, physical fit, durability, or human response
  unless a host-replayed check or authenticated physical receipt proves it.
- Every active Match, Invent, Make, Playtest, or Release attempt uses one native
  Goal with one objective, proof artifacts, and a verifiable stopping
  condition: the current stage finalizer succeeds. Only one Goal is active at a
  time. The Manager works toward it by observing, acting, evaluating exact output,
  and improving. That loop is native-agent behavior, not a Python program.
  Wish and Deliver remain host boundaries rather than agent Goals.
- An Inventor is a declared specialist bundle. `TASTE.md` governs creative
  judgment; `inventor.json` identifies the specialist and binds its exact
  extension trees; the required `<id>-inventor` skill defines its
  primary method, while optional additional Inventor-prefixed skill trees may
  contain scripts, references, assets, and tested deterministic tools for
  specialist craft. Custom code may not become an agent scheduler,
  prompt loop, lifecycle engine, or effect path.
- The host materializes every eligible Inventor in the selected runtime's
  official project-scoped agent/skill layout recorded by `MANAGER.json`, bound
  to its exact identity, Taste, and skill bytes. That projection is the sole
  Inventor roster in a run. The Manager owns native spawning, routing, and
  synthesis. The root session alone receives
  host stage authority and submits a stage proposal; child agents cannot
  advance gates or perform external effects.
- Python is narrow trusted substrate: typed contracts, deterministic tools and
  gates, artifact hashing, checkpoints, exclusive run-mutation locks, budgets, sandbox/session
  boundaries, authorization, idempotency, receipts, and reconciliation.
- External-effect credentials never enter the native agent subprocess. The
  host alone performs authorized Factory, payment, manufacture, postage,
  carrier, or other authenticated effects.
- Model prose and self-scores are proposals. Only host-verified exact bytes,
  deterministic checks, and reconciled receipts advance a gate.

## Coding agents building this repository

This section is for agents building the Workshop itself. It does not tell the
per-Wish product-run agent how to Invent, Make, or Playtest a product.

Do not add a second Python agent framework. Python stage agents, structured
model calls, profile subprocesses, and Python-owned scoring or reward loops are
not extension points. Never add Python prompt chains, browsing strategy,
candidate fan-out, model judges, stage-role views, or repair reasoning.

Read `docs/NATIVE_AGENT_RUNTIME.md`, ADR 0012, and ADR 0013 before changing the CLI,
runtime, workflow, product-run instructions, or lifecycle orchestration. The
native-session path is the production architecture. Preserve useful
deterministic contracts and tests; do not reintroduce removed cognitive
orchestration as a compatibility layer.

## Repository ownership

- `src/cli/`: argument parsing, output formatting, and exit codes only.
- `src/workshop/runtime/`: native engine adapters and trusted state/effect
  boundaries.
- `src/workshop/workflow/`: lifecycle protocol, checkpoints, invalidation,
  Make–Playtest round budgets, and the trusted whole-run host composition.
- `src/workshop/<stage>/`: stage-owned public contracts and deterministic tools.
- `src/workshop/make/skills/`: reusable domain skills owned by Make.
- `.agents/product-run/`: canonical Manager-neutral template source projected
  only into a toy project; its nested workflow skill is intentionally invisible
  to repo-builder sessions.
- `.agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py`:
  run-local standard-library finalizer for exact stage contracts and outcome
  proposals; it does not reason or advance gates.
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
cognitive work, reads the current immutable `STAGE.json`, and uses the
run-local proposal finalizer to propose compact outcomes to the host. It does
not use the builder-only section above as a product workflow, modify the
Workshop source as part of making a toy, or bypass host-owned gates and effect
authority.
