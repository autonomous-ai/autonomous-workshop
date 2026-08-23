# Eve

Eve is an experimental autonomous inventor for 3D-printable board games. Her
creative loop combines a staged game pipeline with a great-books study practice,
an audited reward ledger, and bounded self-improvement. Model work is delegated
through the Claude CLI and is never invoked by the offline test suite.

[`TASTE.md`](TASTE.md) defines Eve's creative constitution and links the
protected owner-ruling log used by her operating loop.

Eve now uses the shared [`../../foundation`](../../foundation/README.md) at two real execution
boundaries: the CAD builder records a content-addressed Foundation artifact manifest,
and the Panda draft adapter uses Foundation's canonical packet builder, durable SQLite
publication outbox, owner-bound receipt, and ambiguous-effect fence. Eve's JSON
queue remains the sole authority for her creative stages and reward law; the
Foundation database is publication infrastructure, not a second lifecycle store.

## How Eve works

One `drive` invocation advances at most one real unit of work, then exits. The
meta-loop chooses work in this order:

1. finish the oldest in-flight game;
2. study one book when the daily study cadence is due;
3. run the weekly self-improvement review;
4. run the weekly ship-cadence check;
5. invent a game only when the other loops are current and capacity is free.

The game pipeline is:

```text
queued -> novelty -> rules -> brief -> draft -> build -> panel -> playtest -> ship
any nonterminal stage ---------------- stated terminal failure -----------> killed
```

Deterministic novelty, rules, and print gates run in code. Agent stages must
write structured JSON into the game folder; free-form prose is not accepted as
a stage result. The fun gate requires recorded LLM-table or human evidence, and
the reward ledger is audited before a scheduled drive can advance work. A game
leaves the queue only by shipping or by being killed with a stated reason.

The main components are:

| Path | Responsibility |
|---|---|
| `eve/meta.py` | scheduler, heartbeat, cadence, gate dispatch, reward recording |
| `eve/driver.py` | executes one planned agent/gate unit and checks its output contract |
| `eve/queue.py` | staged game records and local claims |
| `eve/gates.py`, `eve/playtest.py` | deterministic release and fun checks |
| `eve/books.py`, `eve/corpus.py` | reading loop and novelty/design knowledge |
| `eve/reward.py`, `eve/improve.py` | auditable reward history and bounded improvement proposals |
| `eve/core_adapter.py` | Foundation artifact, canonical packet, and durable Panda-outbox boundary |
| `eve/publish.py` | static catalog renderer plus Foundation-backed Panda draft adapter |
| `.claude/agents/` | role definitions for invention, rules, CAD, panels, playtest, and audit |
| `ops/` | launchd templates, safe renderer, installer, and watchdog |

[`DESIGN.md`](DESIGN.md) describes the full intended four-loop system and
reward model. It includes future behavior as well as implemented behavior; this
README and the tests are the shorter operating contract for the current code.

## Run it locally

From this folder:

```bash
python3 -m pip install -r requirements.txt
PYTHONPATH=. python3 bin/eve seed
PYTHONPATH=. python3 bin/eve status
PYTHONPATH=. python3 bin/eve tick
PYTHONPATH=. python3 bin/eve drive --steps 1
PYTHONPATH=. python3 bin/eve audit
```

`tick` is offline-safe unless `--run-agent` is supplied. `drive` is the real
executor and may invoke configured model agents. Use `EVE_MOCK_AGENTS=1` only
with explicit fixtures when exercising agent paths without a wallet.

Run the deterministic test suite with the pinned test dependencies:

```bash
python3 -m pip install -r requirements-test.txt
PYTHONPATH=.:../../foundation/src PYTHONWARNINGS=error python3 -m pytest -q
```

`requirements.txt` installs the repository-root `autonomous-inventor-core` package. A
source-tree smoke can instead put `../../foundation/src` on
`PYTHONPATH`, as shown for tests.

On macOS, [`ops/README.md`](ops/README.md) explains the optional 30-minute
launchd schedule and independent watchdog. Installing it is an explicit
deployment action; cloning this repository does not start a service. The
installer binds the service to the exact repository-root `../../foundation/src` tree, so a stale
globally installed Foundation cannot satisfy the scheduled runtime by accident.

## Current release boundaries

- `ship` is still an inventor-local stage, not proof of a Foundation
  `CadReleaseBundle` or Factory fulfillment contract. The Foundation publication
  product intentionally has only the stage `publication-ready`; it never
  mirrors or advances Eve's queue.
- Publication remains draft/manual. Foundation persists the intent before POST and
  will not retry an ambiguous import, but Panda still needs scoped inventor
  credentials and server-side content-bound idempotency before unattended
  publication is safe.
- New successful imports write `games/<slug>/published.json` containing the
  exact Foundation `intent_id` and `PublicationReceipt`. Every attempt also updates
  `_core-publication.json`, a readable projection whose declared authority is
  `state/inventor-core.sqlite3`; projections never authorize a retry.
- A slug is permanently bound to its first selected artifact bytes. Until Foundation
  has an atomic logical-product revision contract, corrected publication bytes
  require a new slug; editing files can never bypass an unresolved old intent.
- Historical `published.json` responses remain recognized as already imported
  and are not silently rewritten into stronger Foundation receipts.
- Factory/Store fulfillment is an external adapter whose backend contract was
  not available in the audited organization repositories.
- Self-improvement code changes remain proposals for human review; model roles
  must not rewrite the live queue, reward law, or release floor.

The migration order and exact definition of “Foundation-connected” are in
[`../../foundation/docs/MIGRATION.md`](../../foundation/docs/MIGRATION.md).
