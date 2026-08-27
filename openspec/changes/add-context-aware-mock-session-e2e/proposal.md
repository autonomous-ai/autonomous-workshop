## Why

The offline deterministic E2E suite can verify host mechanics but cannot detect failures caused by what a real Codex session can actually discover and understand from the materialized `AGENTS.md`, skill descriptions, `STAGE.json`, and prior-session context. A full creative product run covers that gap but is too slow and expensive for routine local validation, so regressions such as yesterday's Concept finalization/image-generation deadlock can survive until a live run.

## What Changes

- Add an opt-in, local "mock-session E2E" tier that runs the production Wish-to-Deliver pipeline through one real Codex session and the normal start/resume lifecycle.
- Give that session the normal product-run context plus a clearly isolated test-mode instruction that asks Codex to validate and interpret the current inputs, then produce the smallest context-appropriate mock artifact set instead of doing research, creative iteration, image generation, or full CAD work.
- Require the real session to invoke the materialized stage finalizer and let production host contracts, effects, gates, sealing, checkpoints, waits, and transitions process its output; the harness must not inject accepted stage results at an internal boundary.
- Record per-stage context-read and fixture-selection evidence so the test proves that required files and referenced inputs were present, readable, internally consistent, and understood well enough for Codex to select the correct stage behavior.
- Keep mock payloads deterministic and cheap, but keep stage routing context-derived: the test overlay may expose reusable fixture resources and constraints, but must not duplicate the production workflow instructions or directly tell Codex which host transition to force.
- Add a local command, runtime budget, diagnostics, and fail-fast assertions for session continuity, stage coverage, unexpected web/tool work, missing context, invalid finalization, and ownership/order violations.
- Keep the existing offline deterministic E2E suite as the CI-default mechanics test; the real-session mock E2E is an opt-in acceptance test and does not weaken, replace, or become evidence for physical manufacture or quality.

## Capabilities

### New Capabilities

- `workshop/context-aware-mock-session-e2e`: Defines a fast, opt-in acceptance run using one real Codex session to verify materialized context, skill routing, stage finalization, and the complete production lifecycle with minimal mock artifacts.

### Modified Capabilities

None.

## Impact

- Affects local end-to-end test tooling and fixtures under `tests/end_to_end/`, native-run test configuration, product-run test overlays, and contributor documentation.
- Exercises the production Codex launcher, persistent session checkpoint, materialized instructions and skills, `STAGE.json` protocol, stage proposal tool, host gates/effects, artifact sealing, and lifecycle transitions.
- Introduces no alternate Python agent framework and no production shortcut around native Codex or host authority.
- Requires a real local Codex installation and authenticated session, but should require no image-provider, Factory, manufacture, publication, or other external-service credentials.
