# Running Bob around the clock

Two macOS launchd agents keep Bob moving. One starts a fresh `bob.py tick`
every 30 minutes; the other runs an independent watchdog. `launchd` is the
operating-system name, not Workshop vocabulary.

```text
launchd tick -> audit -> budget -> lease -> one MAKE/INSPECT step
                                                  |
watchdog <----------- state/DAYBOOK.json heartbeat+
```

## Files

| File | Job |
|---|---|
| `launchd/ai.autonomous.bob.plist.in` | run `python3 bob.py tick` every 1,800 seconds |
| `launchd/ai.autonomous.bob.watchdog.plist.in` | run the watchdog hourly |
| `watchdog.sh` | alarm on a missing/stale heartbeat or a fresh traceback |
| `render_launchd.py` | bind validated checkout and Workshop paths using `plistlib` |
| `install.sh` | validate, render, and bootstrap both agents |
| `uninstall.sh` | stop both agents without deleting `state/` or `toys/` |

## Install and operate

```sh
ops/install.sh
tail -f state/logs/tick.log
launchctl kickstart gui/$(id -u)/ai.autonomous.bob
ops/uninstall.sh
```

Telegram alerts use `BOB_TELEGRAM_TOKEN` and `BOB_TELEGRAM_CHAT` from Bob's
`.env`. Without them the watchdog still records warnings in
`state/logs/watchdog.log`.

Bob normally lives under `inventors/bob/` with the shared Workshop at the
repository root. The adapter finds `../../src` automatically. A
different deployment may set:

```text
BOB_WORKSHOP_SRC=/absolute/path/to/autonomous-workshop/src
```

`ops/install.sh` validates and persists that source for scheduled ticks.
Legacy `BOB_FOUNDATION_SRC` and `BOB_CORE_SRC` are compatibility reads only;
different simultaneous values are refused.

## Runtime and storefront configuration

Production configuration should use the canonical names:

```text
BOB_SEND_DRY_RUN=0
BOB_SEND_VIA=workshop
BOB_SHOP_PUBLIC=0
BOB_SHOP_API=https://panda-social-api.autonomous.ai/api/v1
BOB_SHOP_ALLOWED_ORIGINS=https://panda-social-api.autonomous.ai
BOB_SHOP_OWNER_ID=<Bob owner id>
```

The provider hostname is historical; Bob's storefront adapter class retains the
compatibility name `ShopDoor`.
The default scheduled action sends a private draft. `BOB_SHOP_PUBLIC=1` also
requests the explicitly priced public action after Inspection passes.

Runtime files are:

```text
state/shop-auth.json                  storefront credentials, mode 0600
state/inventor-workshop.sqlite3       runtime products and durable intents
toys/<slug>/pack/                    canonical artifact + rehearsal
toys/<slug>/send.json                operator projection
```

The `pack/` and `send.json` paths, plus the `PackedArtifact` type and
`Clockwork` database API, are persisted compatibility names rather than
Workshop concepts.

Older `portal-auth.json`, `panda-auth.json`, `inventor-foundation.sqlite3`,
`inventor-core.sqlite3`, `launch.json`, `published.json`, and old payload
directories continue in place
only when they are the single authority. If more than one candidate exists,
Bob stops and asks the operator to resolve it.

The old text2game server variables support only an explicit manual
`bob export`. Scheduled ticks never export, SSH, or turn that server's output
into a receipt. Its historical server name, `box`, survives only at this
compatibility edge.

## Why these intervals

- **30-minute tick:** one resumable unit limits the damage from a failed run.
- **6-hour heartbeat threshold:** twelve missed ticks, longer than normal quota
  backoff but short enough to catch a dead night.
- **Independent watchdog:** a stopped worker cannot report its own death.
- **DAYBOOK heartbeat:** updated even on a clean no-op, distinguishing idle
  from dead.

## CAD environment

The vendored CAD skill needs Python 3.10+ with `cadgen==0.4.19`:

```bash
python3.12 -m venv .venv-cad
.venv-cad/bin/pip install cadgen==0.4.19
echo "BOB_CAD_PY=$PWD/.venv-cad/bin/python" >> .env
```

Without `BOB_CAD_PY`, Bob can still develop from the JSON parts map, but the
build Inspection records mesh checks as skipped rather than silently passing.
