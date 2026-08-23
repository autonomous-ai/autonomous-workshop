# Eve

Eve is an experimental autonomous inventor for 3D-printable board games. Her
creative loop combines a staged game pipeline with a great-books study practice,
an audited reward ledger, and bounded self-improvement. Model work is delegated
through the Claude CLI and is never invoked by the offline test suite.

[`TASTE.md`](TASTE.md) is Eve's one creative constitution. Workshop binds its
exact content and SHA-256 identity into every creation/study agent prompt and
refuses a shadow Taste path or an in-flight edit.

Eve now uses the shared [`../../workshop`](../../workshop/README.md) at two real execution
boundaries: Eve's Make stage seals the exact artifact bytes, and Send uses
Workshop's canonical Pack, Clockwork, Sender, Shop Door, owner-bound Stamp, and
ambiguous-effect fence. Eve's JSON
queue remains the sole authority for her creative stages and reward law; the
Workshop database is Send infrastructure, not a second lifecycle store.
Make also writes the deterministic `project.json` required by the current
Shop Door. At final selection, after panel and playtest evidence exists, Eve
refreshes that Workshop seal and requires the safely staged Pack to carry the
exact same artifact hash.

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
| `eve/workshop_bridge.py` | exact artifact identity, Pack, Clockwork, and Sender bridge |
| `eve/send.py` | static catalog staging plus the Workshop Shop Door draft flow |
| `eve/launch.py`, `eve/publish.py` | compatibility-only aliases for older extensions |
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
PYTHONPATH=. python3 bin/eve send <shipped-game-slug>
```

`tick` is offline-safe unless `--run-agent` is supplied. `drive` is the real
executor and may invoke configured model agents. Use `EVE_MOCK_AGENTS=1` only
with explicit fixtures when exercising agent paths without a wallet.

Run the deterministic test suite with the pinned test dependencies:

```bash
python3 -m pip install -r requirements-test.txt
PYTHONPATH=.:../../workshop/src PYTHONWARNINGS=error python3 -m pytest -q
```

`requirements.txt` installs the repository-root `inventor-workshop` package. A
source-tree smoke can instead put `../../workshop/src` on
`PYTHONPATH`, as shown for tests.

On macOS, [`ops/README.md`](ops/README.md) explains the optional 30-minute
launchd schedule and independent watchdog. Installing it is an explicit
deployment action; cloning this repository does not start a service. The
installer binds the service to the exact repository-root `../../workshop/src` tree, so a stale
globally installed Workshop cannot satisfy the scheduled runtime by accident.

## Current release boundaries

- `ship` is still an inventor-local stage, not proof of a Workshop
  `CadReleaseBundle` or fulfillment contract. The Workshop send product
  intentionally has only the stage `send-ready`; it never
  mirrors or advances Eve's queue.
- Send remains draft/manual. Clockwork persists the intent before POST and will
  not retry an ambiguous import, but the current Shop Door still needs scoped
  inventor credentials and server-side content-bound idempotency before
  unattended Send is safe.
- New successful imports write `games/<slug>/sent.json` containing the exact
  `send_id`, Pack identity, and Workshop Stamp. Every attempt also updates
  `_send.json`, a readable projection whose authority is
  `state/clockwork.sqlite3`; projections never authorize a retry.
  Existing `inventor-workshop.sqlite3`, `inventor-foundation.sqlite3`, and
  `inventor-core.sqlite3` histories continue in place. Seeing more than one
  candidate file fails closed so effect history cannot split.
- A slug is permanently bound to its first selected artifact bytes. Until Workshop
  has an atomic logical-product revision contract, corrected Pack bytes
  require a new slug; editing files can never bypass an unresolved old intent.
- Historical `published.json` responses remain recognized as already imported
  and are not silently rewritten into stronger Workshop receipts.
- Fulfillment is an external Door whose backend contract was
  not available in the audited organization repositories.
- Self-improvement code changes remain proposals for human review; model roles
  must not rewrite the live queue, reward law, or release floor.

The migration order and exact definition of “Workshop-connected” are in
[`../../workshop/docs/MIGRATION.md`](../../workshop/docs/MIGRATION.md).

## Shop Door configuration migration

New deployments use `EVE_SHOP_API`, `EVE_SHOP_TOKEN`, and
`EVE_SHOP_OWNER_ID`. The former `EVE_PORTAL_*`, `EVE_STORE_*`, and
`PANDA_OWNER_ID` names remain guarded fallbacks. If canonical and former names are
both present, their values must match; Eve refuses to guess between two Shop
identities or credentials. `EVE_AUTO_SEND` similarly accepts
`EVE_AUTO_LAUNCH` and `EVE_AUTO_PUBLISH` as guarded fallbacks.
