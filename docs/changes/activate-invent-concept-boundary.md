# Activate the Invent Concept boundary

New Forge and Quest runs now freeze `invent-concept-v1.md`. During their
existing Invent Goal, the Manager and selected Inventor author one Invented
contract plus an exact five-file pre-render Concept source. The run-local
finalizer seals that compound proposal once; it does not render images or gain
credentials.

After the native turn exits, the host repeats the deterministic checks, records
durable role intents, invokes the pinned image adapter, installs exact returned
bytes, writes sanitized `sealed.json` and `effect.json`, and advances the same
Invent checkpoint directly to Make. Missing configuration and safe or ambiguous
provider failures persist a private Invent wait that resumes without repeating
Invent cognition. Unknown post-transmission operations are not blindly resent.

Marked Make uses schema-v2 `made.json` bound to the sealed Concept and effect,
requires stable component keys, and rejects copied Concept pixels anywhere in
the product tree. Make-to-Invent revision evidence carries the standing Concept
identities. Spark and unmarked historical runs keep their frozen protocol and
schema-v1 Made behavior.

Verification uses focused contract, finalizer, host-gate, effect-ledger,
integration, compatibility, packaging, archive, deterministic external-runtime,
and full offline tests. Deterministic image and Factory doubles prove lifecycle,
identity, recovery, and byte handling only. They do not prove aesthetic quality,
that a product is buildable from Concept art, physical manufacture, delivery, or
live-provider success.

## Verification record

The implementation was verified on 2026-08-31 with:

- `PATH=/Users/macbookpro/Documents/ai-chain/_hardware/autonomous-workshop/.venv/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m unittest` — 662 offline tests passed; 25 opt-in tests were skipped.
- `PATH=/Users/macbookpro/Documents/ai-chain/_hardware/autonomous-workshop/.venv/bin:/usr/local/bin:/usr/bin:/bin WORKSHOP_RUN_DETERMINISTIC_E2E=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m unittest tests.end_to_end.test_deterministic_native_fidelity.DeterministicNativeFidelityTest.test_canonical_effort_routes_are_repeatable_and_leave_durable_proof` — the repeatable Spark/Forge/Quest route matrix passed with no Concept lifecycle stage and no Spark image calls.
- Focused deterministic cases for missing credentials, partial safe retry, provider rejection, ambiguous no-resend, stale receipts, component mismatch, copied pixels, and sealed-tree tamper passed through the external runtime and outbound adapter double.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m unittest tests.end_to_end.test_native_full_run` — all 19 lifecycle compatibility cases passed.
- `PATH=/Users/macbookpro/Documents/ai-chain/_hardware/autonomous-workshop/.venv/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python tests/packaging/installed_wheel_cli_acceptance.py` — isolated installed-wheel acceptance passed.
- `UV_CACHE_DIR=/tmp/autonomous-workshop-uv-cache /Users/macbookpro/.grid/bin/uv run --no-project --with build==1.3.0 python3 -m build --sdist --outdir /tmp/autonomous-workshop-activation-sdist /Users/macbookpro/Documents/ai-chain/_hardware/autonomous-workshop` — the sdist built, and six activation contract/marker/runtime files were byte-compared with their source copies.
- `.venv/bin/python tools/scan_secrets.py` — `secret-scan: clean`.
- `openspec validate restore-dormant-concept-contracts --strict` and `openspec validate activate-invent-concept-boundary --strict` — both changes validated.
- `git diff --check` — passed.

The deterministic Spark/Forge/Quest route matrix was rerun on 2026-08-31 with
`WORKSHOP_RUN_DETERMINISTIC_E2E=1` and passed. The required authenticated
real-Codex mock-session acceptance remains open. The first Forge retry against
local Concept-image and Factory doubles used `gpt-5.6-terra` at high effort
through an in-memory test-only launcher override; it completed Invent in
290.86 seconds but its following Make proof turn exited 126 because the
mock-session wrapper incorrectly required a final context record at the
intermediate proof boundary. The wrapper now accepts only the exact
checkpoint-bound Make marker and retains strict context validation for normal
finalization. A second Terra/high Forge retry completed Invent in 313.01
seconds and the Make proof boundary in 152.97 seconds, both in the same native
session. The local Codex transcript was subsequently recovered: final Make
returned an exact `waiting` outcome because the independent rereview found the
alternate loose wave/radial state visually ambiguous after the one permitted
focused repair. It therefore never produced a terminal Forge receipt. Quest
and the partial-role real acceptance remain unattempted. No live-provider
request was made, and no live-provider success, visual quality, buildability
from Concept imagery, manufacture, delivery, or physical result is claimed
from the deterministic doubles.
