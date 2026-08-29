# End-to-end acceptance

This directory owns acceptance checks that cross every Workshop component.

The committed suite uses deterministic local providers and must be safe in CI.
Production acceptance additionally runs the installed wheel from an unrelated
working directory, starts with `workshop wish`, verifies the durable event and
artifact chains, and confirms the authenticated Factory page. Production
credentials and run receipts belong only in ignored local runtime storage.

`test_deterministic_native_fidelity.py` is the required high-fidelity offline
gate. Run it with the locked project environment:

```bash
WORKSHOP_RUN_DETERMINISTIC_E2E=1 uv run --frozen python -m unittest \
  tests.end_to_end.test_deterministic_native_fidelity -v
```

It supplies a deterministic executable at the external Codex boundary and
deterministic HTTP responses at the outbound Factory boundary. The production
launcher, run-local stage finalizer, contracts, workflow gates, CAD verifier,
PDF validator, effect ledger, reconciliation, publication, and sealing remain
real. The test makes no network requests and uses no live credentials. It must
not be treated as evidence of model quality, physical manufacture, fit,
durability, delivery, or human response.

Those are the only approved seams: the executable selected by
`WORKSHOP_CODEX_BIN`, the two outbound Factory transports, and isolated host
environment values. Static policy rejects replacements for the launcher,
finalizer, contract readers, gates, CAD/PDF verification, checkpoint mutation,
or effect coordination.

The phase ledger reopens and hashes these production proofs:

- Wish: canonical Wish bytes, frozen effort and capability, every materialized
  input, private workspace marker, Wish gate, and first checkpoint transition.
- Invent: authored source, assignment and Invented contracts, Invent gate, and
  the exact identities received by Make.
- Make: folded creative contracts where applicable, the complete product/CAD
  manifest, fresh full-tier CAD evidence, Made contract, gate, and transition.
- Playtest: authored observations, sealed configs/results, Playtested and
  feedback identities, replayed CAD evidence, gate, and repair or forward edge.
- Release: exact package and PDF contract, omission or Playtest binding,
  release CAD replay, Factory intent ledger, import/readback/publication receipt,
  public manual hash, Release gate, and terminal checkpoint.

Passed-through phases must be wholly absent: no native turn, authored phase
source, phase artifact tree, contract, gate, or evidence may stand in for an
omitted Invent or Playtest. Spark retains folded Inventor provenance under Make;
Spark and Forge retain only the canonical Playtest-not-run record under Release.

The exact final clean-home local gate measured 934.883 seconds on macOS arm64
with Python 3.13.5. An immediately preceding warm-dependency full pass measured
905.149 seconds before the second credentials-wait tamper variant was added;
that final two-case effect/pending-outcome method measured 82.788 seconds in
isolation. The final two-pass Spark, Forge, and Quest route/proof matrix alone
measured 250.868 seconds. Every invocation creates fresh isolated Workshop
homes; "warm" refers only to already-present locked Python dependencies and the
OS filesystem cache. No production check or CAD result is cached, patched, or
skipped. The required `deterministic-e2e` CI job has a 30-minute ceiling and
writes its exact runner elapsed time to the GitHub job summary on every run so
CI performance remains visible.

## Authenticated real-Codex mock session

`tools/run_mock_session_e2e.py` is the opt-in context-and-integration tier. It
delegates to the installed, authenticated Codex executable and drives the
production Workshop session launcher, finalizers, gates, CAD and PDF checks,
sealing, release writer, effect ledger, reconciliation, publication, and
terminal checkpoint. A loopback Factory server replaces only the two outbound
HTTP transports. The wrapper adds one generic context-proof request; it does
not contain stage schemas, lifecycle recipes, or artifact-writing recipes.

Prerequisites are a supported `codex` on `PATH`, an active `codex login`, the
locked Python environment (including `build123d` and `cadgen`), permission to
bind a loopback port, and enough time for real model turns. Check prerequisites
without creating a Wish:

```bash
uv run --frozen python tools/run_mock_session_e2e.py --preflight-only
uv run --frozen python tools/run_mock_session_e2e.py --help
```

Run one selectable route explicitly:

```bash
uv run --frozen python tools/run_mock_session_e2e.py \
  --effort spark --turn-timeout 1800 --timeout 7200 \
  --report /tmp/workshop-mock-session-spark.json
```

The exact expected traces are Spark `Make -> Release`, Forge
`Invent -> Make -> Release`, and Quest
`Invent -> Make -> Playtest -> Release`; every route ends at terminal
published Release. The defaults are 1800 seconds per
Codex turn and 7200 seconds for the whole route; both are bounded CLI options.
Successful isolated state is removed unless `--keep` is supplied. Failures and
timeouts retain their private temporary state and print its location after
redacting recognizable credentials. Use retained state only for local
diagnosis; never upload or commit it.

`--report` writes the only upload-safe artifact. It contains the effort,
model/reasoning binding, exact stage trace and durations, one persistent
session identity with start/resume counts, verified context-proof count, the
number of temporary marker-based missing-terminal fallbacks, final checkpoint
hash/status, publication status, loopback protocol calls, and the fixed
`context-and-integration-only` evidence label. It excludes workspace and
host-state paths, prompts, transcripts, authored product bytes, and credentials.

The three evidence tiers are intentionally distinct:

- ordinary unit/integration CI is offline and tests focused contracts;
- the required deterministic E2E proves production-host fidelity against
  deterministic Codex and Factory boundary doubles;
- this scheduled/manual real-Codex tier proves persistent-session context use
  and current workflow integration.

None of them proves creative or research quality, exhaustive agent behavior,
physical printing, fit, durability, manufacture, shipment, delivery, or human
response. Full product validation remains separate.
