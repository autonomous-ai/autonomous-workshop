# Bob

Bob invents beautiful, 3D-printable board games. He studies game history,
develops new physical mechanisms, plays each design thousands of times, and
keeps only the games that survive deterministic checks and adversarial review.
[`TASTE.md`](TASTE.md) is his creative constitution.

Bob is one inventor built on the repository-wide Workshop. The
customer promise stays deliberately short:

```text
WISH  --------------------------  WAIT  ----------------------  RECEIVE
  |                                                                  ^
  +--> Bob's TASTE + workflow                                        |
              |                                                      |
              v                                                      |
       MAKE -> INSPECT -> PACK -> SEND -------------------------------+
```

`BOX` means the physical thing a customer receives. Bob's current adapter can
send a game to an optional Shop Door; manufacturing and delivery are the next
part of the customer path, not something this code pretends is complete.

## How Bob uses the Workshop

```text
Wish + TASTE.md
      |
      v
MAKE  Bob explores rules, mechanics, play engines, and printable geometry
      |
      v
INSPECT
      rules checks -> 1,000+ simulations -> seated LLM games -> CAD checks
      -> isolated judges -> frozen reward threshold
      |
      v
PACK  pack_artifact(...) -> PackedArtifact
      inspect_pack(...) verifies the exact bytes and SHA-256
      |
      v
SEND  Sender records intent in Clockwork before any remote effect
      |
      +--> private draft --> ShopDoor --> Stamp
      |
      +--> optional priced public send --> ShopDoor --> Stamp
```

Bob's inspectors are specific to board games; the Workshop supplies the shared
Taste binding, canonical pack, durable Clockwork, Sender, ShopDoor adapter, and
typed Stamp. A mutable JSON file, a remote design id, command output, or a human
assertion is never proof that sending succeeded.

The durable Bob state machine predates the Workshop language and keeps its exact
on-disk names for safe upgrades:

```text
sparked -> researched -> ruled -> rules_gated -> simulated -> tabled
        -> briefed -> built -> build_gated -> reviewed -> published -> live
```

Those are Bob's persisted queue values, not extra shared Workshop stages. In
the developer story they group naturally as:

- `MAKE`: idea search through CAD build
- `INSPECT`: rules, simulation, table, build, and reward checks
- `PACK`: canonical content-addressed artifact
- `SEND`: private draft, plus an optional explicit public Shop Door action

`bob.py tick` advances one step of one game. It runs an integrity audit first,
then checks budget and leases. When no game can move, Bob studies one source or
runs the weekly architecture loop. Files under `corpus/`, `state/`, and
`games/` are the message bus; agents never edit the queue or reward function.

## Layout

| Path | What it contains |
|---|---|
| `TASTE.md` | Bob's sole runtime creative constitution |
| `ARCHITECTURE.md` | the design, gates, loops, and Workshop mapping |
| `docs/REWARD.md` | the frozen board-game reward specification |
| `docs/CONTRACTS.md` | Bob's module and state contracts |
| `harness/` | queue, budgets, reward, ledger, Workshop adapter, send boundary |
| `loops/` | Make and Inspection work, playtests, study, architecture, improvement |
| `games/<slug>/` | one game's wishes, rules, engines, parts, reviews, and page kit |
| `state/` | durable queue, ledger, Clockwork, credentials, and heartbeat |
| `ops/` | launchd install, uninstall, and watchdog |

## Run Bob

```bash
cd inventors/bob
python3 -m unittest discover -s tests -t .
python3 bob.py seed
python3 bob.py tick
python3 bob.py status
ops/install.sh
```

The autonomous route is Workshop-only and defaults to an offline rehearsal:

```bash
BOB_SEND_DRY_RUN=1 python3 bob.py tick
BOB_SEND_DRY_RUN=0 python3 bob.py send <slug>
BOB_SEND_DRY_RUN=0 python3 bob.py send <slug> --price-cents 5900
```

The last command performs the optional public Shop Door action. The default
`bob send <slug>` stops at a private draft. `BOB_SHOP_PUBLIC=1` lets the
scheduled loop request the priced public action after Inspection is green.
After an ambiguous public send, `python3 bob.py reconcile-public <slug>` reads
back the recorded intent and never repeats the effect.

Canonical operator settings are:

```text
BOB_SEND_DRY_RUN=1
BOB_SEND_VIA=workshop
BOB_SHOP_PUBLIC=0
BOB_SHOP_API=https://panda-social-api.autonomous.ai/api/v1
BOB_SHOP_ALLOWED_ORIGINS=https://panda-social-api.autonomous.ai
BOB_SHOP_OWNER_ID=<Bob's pinned marketplace owner id>
BOB_WORKSHOP_SRC=/absolute/path/to/workshop/src   # nonstandard layouts only
```

The provider hostname retains its historical name; the canonical interface in
Bob's code is `ShopDoor`. Credentials live at `state/shop-auth.json` (mode
0600). Clockwork lives at `state/inventor-workshop.sqlite3`. New games emit
`games/<slug>/send.json` and `games/<slug>/pack/`.

Old names are accepted only at a conflict-checked compatibility edge:

- `BOB_PUBLISH_*`, `BOB_AUTO_FLIP`, `BOB_PORTAL_*`, `BOB_PANDA_*`,
  `PORTAL_OWNER_ID`, and `PANDA_OWNER_ID`
- `BOB_FOUNDATION_SRC` and `BOB_CORE_SRC`
- `portal-auth.json`, `panda-auth.json`, `inventor-foundation.sqlite3`, and
  `inventor-core.sqlite3`
- `launch.json`, `published.json`, `launch_payload/`, and `publish_payload/`
- `harness.publish` and `bob publish`

Bob continues one legacy authority in place. If canonical and legacy sources,
settings, credentials, projections, or state files disagree, he refuses to
send until an operator resolves the split.

The historical text2game server also happened to be called the "box." It is
not the customer's physical `BOX`. `bob export <slug>` may assemble its old
payload for manual investigation, but the autonomous loop never exports,
SSHes, or treats its stdout/design id as a Stamp. The obsolete
`mark-published` command fails closed.

The checked-in `g0003` / Clearance draft remains intentionally stranded. It
predates Bob's Workshop intent and artifact identity and belongs to a different
principal. Its current owner must resolve that remote draft separately; Bob
will not adopt it or retry the slug.

## The rules Bob lives by

1. The evaluator is the product; the generator is replaceable.
2. Budgets live in code, outside agent prompts.
3. Nothing expensive happens before the game has been played.
4. Every verdict binds to the exact artifact SHA-256 it inspected.
5. An absent verdict is a failure, never a pass.
6. Kill early, kill cheap, and record why—the reason becomes training data.
