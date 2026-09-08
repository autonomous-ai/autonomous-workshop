# ADR 0060: The host records a person's decision and the next packet carries it

- Status: Accepted
- Date: 2026-09-08
- Owners: Native run host and CLI maintainers

## Context

A native Manager stops truthfully with a `need` when only a person can
decide: the likeness gate's own policy makes it stop rendering and ask
before any delivery below the 0.90 floor, the Make protocol asks for
authorization past its one repair and one rereview, and a component or
measurement question may need an owner's word. Three such needs in two days
(goose runs 1 and 2, 2026-09-08) had no way to be answered. `STAGE.json`
carried no field for it, `workshop resume` accepted no note, and Wish text
and references are sealed by hash. The only outcomes were to stop, or to
resume and watch the Manager rerun its probes and ask again.

## Decision

`workshop resume <wish> --decide "TEXT"` records the decision before the
resume, under the run's mutation lock, as one line in an owner-only ledger
in private host state (`host-decisions.jsonl`, mode 0600, kind
`autonomous-workshop.host-decision`) with the checkpoint, stage, round,
status and open needs at that moment, a source label, and the text (1 to
2000 printable characters, newlines allowed). Both stage packet writers
then list the newest ten under `inputs.host_decisions`, each carrying a
fixed `meaning` sentence, so the Manager reads the answer with its next
`STAGE.json`. The product-run constitution tells the Manager what a
decision is and is not: act on it where the protocol provides a human
decision path (a recorded likeness acceptance through
`verify_project --likeness-accept-mismatch` with the text as the reason, an
authorization, a component choice), continue the same Goal, and never treat
it as a waiver of a deterministic gate or an expansion of authority.

The decision is bound into `inputs`, never into the stage subject: an
answer to a Goal does not start a new one, so `subject_sha256` is unchanged
and an active Goal continues on resume.

## Alternatives considered

- Editing `WISH.json` or the sealed references: rejected, every checkpoint
  re-verifies them and the Wish is the person's sealed intent.
- A host-side waiver flag on `verify_project`: rejected, the Manager must
  still produce the proposal and record the acceptance in the pipeline
  record; the host only relays the decision.
- A free-form note file in the workspace: rejected, the workspace is the
  Manager's, and an unlisted file is indistinguishable from tampering.

## Consequences

- A person can answer a need from the CLI or from a Telegram bridge that
  drives the CLI; the answer is durable and auditable.
- Existing runs see the field on their next resume without a constitution
  change, since the packet is rebuilt on resume; the constitution rule
  reaches only runs materialized after this change, so an older run relies
  on the entry's own `meaning` text.
- Decisions are untrusted data to the Manager for every purpose other than
  the decision they state.

## Compatibility and migration

Runs without a ledger list an empty `host_decisions`. No checkpoint,
budget, sealed artifact or session binding changes.

## Verification

`tests/workflow/test_agent_run.py` covers the ledger's mode, order and
validation; `tests/workflow/test_native_host.py` starts a run, resumes it
with `--decide`, and checks the ledger, the packet entry and the unchanged
subject; `tests/cli/test_cli.py` checks the CLI records before it resumes.
