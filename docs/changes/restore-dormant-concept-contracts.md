# Dormant Concept contracts restored

Workshop now packages compatibility-only Concept schema v1 and route-aware
schema v2 contracts for `invent` and `spark-make` provenance. The dormant
component validates strict bounded source, exact routed-Wish and creative
provenance, repair freshness, pre-render roles, already-present image bytes,
and structural brief/research/drawing completeness.

This change does not activate Concept. Spark remains `Make -> Release`, Forge
remains `Invent -> Make -> Release`, and Quest remains
`Invent -> Make -> Playtest -> Release`. There is no Concept stage, Goal,
native turn, packet, checkpoint, gate, wait, transition, Make binding, provider
adapter, credential read, or external effect. Structural evidence does not
claim visual quality, buildability, printability, physical testing,
publication, manufacture, or delivery.

Future work may add an owning-stage pre-render finalizer and a durable
authorized image-effect boundary, then version Forge/Quest Invent and Spark's
folded Make as compound creative boundaries. It must not introduce a
standalone Concept stage.

## Verification record

The completed change passed these commands on 2026-08-30:

- `PATH="$PWD/.venv/bin:$PATH" PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -t . -p 'test_*.py'` — 627 tests passed; 18 were skipped by their existing opt-in conditions.
- `PATH="$PWD/.venv/bin:$PATH" WORKSHOP_RUN_DETERMINISTIC_E2E=1 .venv/bin/python -m unittest tests.end_to_end.test_deterministic_native_fidelity.DeterministicNativeFidelityTest.test_canonical_effort_routes_are_repeatable_and_leave_durable_proof` — the canonical Spark/Forge/Quest route matrix passed.
- `PATH="$PWD/.venv/bin:$PATH" .venv/bin/python tests/packaging/installed_wheel_cli_acceptance.py` — the isolated, no-dependency installed-wheel acceptance passed.
- `UV_CACHE_DIR=/tmp/autonomous-workshop-uv-cache /Users/macbookpro/.grid/bin/uv run --no-project --with build==1.3.0 python3 -m build --sdist --outdir /tmp/autonomous-workshop-sdist /Users/macbookpro/Documents/ai-chain/_hardware/autonomous-workshop` — the sdist built successfully; both packaged Concept schema SHA-256 digests matched the source files exactly.
- `PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m unittest discover -s tests/architecture -p 'test_*.py'` — 33 architecture and policy tests passed.
- `PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m unittest discover -s tests/packaging -p 'test_*.py'` — 7 packaging tests passed.
- `.venv/bin/python tools/scan_secrets.py` — `secret-scan: clean`.
- `openspec validate restore-dormant-concept-contracts --strict` — the change was valid.
- `git diff --check` — passed with no whitespace errors.
