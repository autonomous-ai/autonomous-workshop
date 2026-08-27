# End-to-end acceptance

This directory owns acceptance checks that cross every Workshop component.

The committed suite uses deterministic local providers and must be safe in CI.
Production acceptance additionally runs the installed wheel from an unrelated
working directory, starts with `workshop wish`, verifies the durable event and
artifact chains, and confirms the authenticated Factory page. Production
credentials and run receipts belong only in ignored local runtime storage.

## Verification tiers

Workshop has three deliberately different end-to-end tiers:

1. The default deterministic suite runs offline in CI. It verifies lifecycle,
   contracts, gates, effects, persistence, and failure behavior without a live
   model:

   ```bash
   PYTHONPATH=src python -m unittest tests.end_to_end.test_native_full_run
   ```

2. The mock-session acceptance uses one authenticated, real Codex session but
   asks it to create only minimal context-derived artifacts. It verifies that
   the materialized `AGENTS.md`, skill descriptions, stage references,
   `STAGE.json`, and upstream files are present and understandable enough to
   drive the production finalizers and host lifecycle. Concept images and the
   private Factory import use loopback protocol fixtures; Codex has no network
   access and receives no fixture credentials. This test is skipped by default:

   ```bash
   .venv/bin/python tools/run_mock_session_e2e.py
   ```

   Prerequisites are Codex CLI 0.145.0 or newer and an authenticated local
   session (`codex login`). The active Python interpreter must also contain the
   repository's pinned `build123d` and `cadgen` CAD runtime; preflight rejects a
   bare system Python before creating a run. Defaults are a 300-second per-turn
   limit and a 1,800-second whole-run limit. Override them explicitly when
   diagnosing a slow local machine:

   ```bash
   .venv/bin/python tools/run_mock_session_e2e.py --turn-timeout 600 --timeout 3600 --keep
   ```

   `--keep` retains the isolated Workshop home after success. A failed or timed
   out run is always retained and its absolute diagnostic path is printed.
   `--preflight-only` checks the installed CLI and authentication without
   creating a run.

3. A full product run evaluates substantive model work: research, design,
   complex CAD, inspection, repair, Playtest judgment, and Release quality.
   Run it through the normal `workshop wish` command with the intended Wish.

A green mock-session result is context-and-integration evidence only. It does
not prove creative or research quality, physical printing, fit, durability,
manufacture, publication, shipment, delivery, or human response. It does not
replace either deterministic CI coverage or a full product run.

## Mock-session troubleshooting

- A preflight error means the runner has not created a product run. Install or
  update Codex, authenticate with `codex login`, and use the repository virtual
  environment so the production CAD verifier has `build123d` and `cadgen`.
- A context-record error identifies stale or missing production instructions,
  input paths, hashes, or agent-authored source files for one stage. Inspect the
  retained `.mock-session/packets`, `.mock-session/context`, and
  `.mock-session/turns.jsonl` files.
- A prohibited-activity error means the real session attempted web search or an
  unnecessary child-agent action. The acceptance directive intentionally keeps
  this tier small and offline.
- A Concept pre-render error means the session or skill regressed to waiting for
  host-drawn images before finalization. Image files are expected to be absent
  until the production host receives the finalized Concept proposal.
