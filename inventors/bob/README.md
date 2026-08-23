# Bob

Bob invents 3D-printable board games. He runs 24/7 on one Mac, studies five
thousand years of games and the best design books ever written, invents games
that could not exist before 3D printing, plays each one thousands of times
before a human ever sees it, and publishes the survivors to
[autonomous.ai/factory](https://www.autonomous.ai/factory) as an AI creator —
full product page, buy button, print-on-order. Quality over quantity: one
good game per week beats ten mediocre ones per day.

Two receipts started this: two chess sets sold on the Factory before Bob
existed. People pay for games you can hold.

[`TASTE.md`](TASTE.md) defines Bob's creative constitution and links its
protected owner-evidence ledger.

## How Bob works

```
bob.py tick   (launchd, every 30 min)
  └─ audit clean? budget left? quota clear?
       └─ advance ONE step of ONE game        (invent loop, closest-to-publish first)
            else: study one history/book unit  (scholar + librarian loops)
            else: weekly architecture sweep    (architect loop)
```

A game moves through: spark → rules → **machine-played** (≥1,000 simulated
games, policy ladder) → **LLM-tabled** (seated players choosing moves by index
through the real engine — they cannot cheat and cannot be polite) → parts
brief → CAD build → deterministic print gate → judged → **published
automatically** when the frozen reward function says it's ready. Every stage
gets cheaper-to-kill the earlier it is; nothing expensive happens before the
game has been played.

The reward function (docs/REWARD.md) is frozen and checksummed. Generator
agents never see its weights — they get playtest findings, not a score to
flatter. Sales, human "can we play again?" reports, and the owner's verbatim
verdicts outrank everything a model believes about its own work.

Self-improvement runs weekly with authority tiers: prompt/lesson edits land
directly, code changes become PRs, and touching the reward, the taste file,
or the baselines reverts the whole session. Repeated lessons must graduate to
code — never advisory text twice.

## Layout

| Path | What |
|---|---|
| `ARCHITECTURE.md` | the full design + the research it stands on |
| `docs/REWARD.md` · `docs/CONTRACTS.md` | the frozen reward spec · module contracts |
| `docs/research/` | 8 research reports (Anthropic engineering, sibling inventors, game science, publish contract) |
| `harness/` | queue, budgets, reward, ledger, bandit, runner, integrity, publish, telegram, novelty |
| `loops/` | invent, playtest+simmetrics, tablerun, scholar, architect, meta |
| `.claude/agents/` | the roster: ideator, rules writer, lenses, engine writer, table seats, judges, scholar, librarian, architect, improver, auditor |
| `corpus/` | what Bob has learned about games (cards, study queues, direction arms) |
| `knowledge/` | TASTE.md (owner's words, append-only), lessons, proposals |
| `state/` | queue, reward ledger, bandit, daybook — the durable memory |
| `games/<slug>/` | one game: idea, rules, engine, sim reports, table transcripts, parts, page kit |
| `ops/` | launchd plists, install/uninstall, watchdog |

Bob uses the repository-level `foundation/` for two production contracts. Every
publish payload is a canonical, content-addressed Foundation packet (including the
embedded `_inventor-artifact.json`), even in autonomous dry-run mode. The live
Panda path runs through Foundation's durable SQLite publication outbox, which records
an effect intent before HTTP, blocks retries after timeouts/5xx responses, and
requires an owner-, history-, listing-, price-, currency-, SKU-, packet-, and
artifact-bound receipt before Bob records `live`. Bob's creative queue and CLI
remain his own; `state/inventor-core.sqlite3` is the publication safety ledger.
The Foundation product identity is stable per Bob slug. If an import is ambiguous,
editing the source cannot allocate a fresh retry lane; corrected bytes require
a new slug until Panda exposes a content/idempotency receipt.

## Run it

```bash
cd inventors/bob
python3 -m unittest discover -s tests      # everything green, no network, no tokens
python3 bob.py seed                        # first run: bandit arms + study queues
python3 bob.py tick                        # one step, by hand
python3 bob.py status                      # queue, spend, heartbeat
ops/install.sh                             # go 24/7 (launchd) — ops/uninstall.sh reverts
```

Publishing starts in dry-run (`BOB_PUBLISH_DRY_RUN=1` default). Going live
needs the `bob` marketplace account credentials in `state/panda-auth.json` —
minting that account is a one-time human act (docs/research/publish-contract.md §2).
The dry-run `published.json` is stamped `publication_authority: none`: it is a
rehearsal report, not an effect receipt. After credentials are installed, run
`BOB_PUBLISH_DRY_RUN=0 python3 bob.py publish <slug>` to replace it with a
Foundation-backed draft receipt; the queue safely remains in `published` while the
durable Foundation outbox prevents duplicate imports.
`published` is a waiting state and is never scheduled into `live`. After an
ambiguous Foundation-recorded flip, run `python3 bob.py reconcile-public <slug>`;
the command never resends `/publish` (its marketplace readback is GET; auth
may rotate first). A human admindash click made without Bob's
price-bound Foundation intent cannot be proven from Panda's current response and
therefore does not advance the queue. Only an authenticated receipt for the
same Foundation intent, owner, artifact, history, active USD listing, price, and SKU
advances Bob to `live`.

The checked-in `g0003` / Clearance draft is historical and intentionally
stranded: it was imported before Foundation recorded publication intents, carries no
Foundation artifact identity, and its Panda receipt belongs to Dee rather than a Bob
principal. Bob will neither adopt it nor retry that slug. Its current owner
must resolve, unpublish, or archive the legacy draft separately; deployment
must provision and pin a distinct Bob marketplace principal, then re-import
the product under a new slug so Foundation records the first effect.

The official Panda origin is pinned by default. Staging requires both
`BOB_PANDA_API` and an explicit comma-separated
`BOB_PANDA_ALLOWED_ORIGINS`; an unpinned override fails closed. The monorepo
layout is resolved automatically, or a deployment may set
`BOB_CORE_SRC=/absolute/path/to/foundation/src`.

Every auto-publish pings Telegram with the listing link and a one-tap
UNPUBLISH. The human is a kill switch, not a turnstile.

## The rules Bob lives by

1. The evaluator is the product; the generator is a replaceable mutation operator.
2. Budgets live in code. An agent that can read its budget will negotiate with it.
3. Nothing expensive before the game has been played (6 wasted CAD repair rounds taught this).
4. A verdict binds to the version it judged, by hash.
5. An absent verdict is a FAIL, never a pass.
6. Kill early, kill cheap, and write the reason down — the reason is training data.
