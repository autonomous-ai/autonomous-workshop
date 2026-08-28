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
