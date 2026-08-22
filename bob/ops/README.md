# ops — how Bob runs 24/7

Two launchd agents on one Mac. No cron, no daemon process: launchd fires a
fresh `bob.py tick` every 30 minutes, and a separate hourly watchdog alarms
if the ticks go quiet. The pattern is a direct port of text2cad's
cron + watchdog + Telegram mechanics (`docs/research/text2cad-lessons.md` §c),
which paid $430 to learn that harness silence — not bad products — is where
the money dies.

## The pieces

| File | Job |
|---|---|
| `launchd/ai.autonomous.bob.plist` | `python3 bob.py tick` every 1800s. Logs to `state/logs/tick.log`. PATH includes `~/.local/bin` (where `claude` lives — launchd gives agents a bare PATH). |
| `launchd/ai.autonomous.bob.watchdog.plist` | runs `watchdog.sh` hourly at :07. |
| `watchdog.sh` | dead-man switch. Alarms via Telegram when `state/DAYBOOK.json` (the tick heartbeat) is missing or >6h stale, or when a fresh `Traceback` appears in the tail of `tick.log`. Rate-limited by marker files in `state/` so one dead night is one DM, not twelve. |
| `install.sh` | copies both plists to `~/Library/LaunchAgents`, `launchctl bootstrap`s them. Refuses if `bob.py` is missing or `import harness` fails — a broken deploy must fail at install time, not silently every 30 minutes. Idempotent (re-run = redeploy). |
| `uninstall.sh` | boots both agents out and removes the plists. Keeps `state/` and `games/` — stopping the schedule never deletes work. Idempotent. |

## Install / operate

```sh
ops/install.sh                                    # install or redeploy both agents
tail -f state/logs/tick.log                       # watch the loop live
launchctl kickstart gui/$(id -u)/ai.autonomous.bob   # force a tick now
ops/uninstall.sh                                  # stop everything
```

Telegram alerts need `BOB_TELEGRAM_TOKEN` and `BOB_TELEGRAM_CHAT` — put them
in `.env` at the repo root (`watchdog.sh` sources it; launchd inherits almost
no environment). Without them the watchdog still runs and shouts to
`state/logs/watchdog.log` instead of DMing.

## Why these numbers

- **1800s tick**: the unit of work is one queue step, cheap to kill and
  resume. text2cad's daily monolith lost the entire day's spend when its 3h
  ceiling killed a healthy run; thirty-minute steps bound the blast radius.
- **6h heartbeat threshold**: 12 missed ticks. Longer than any legitimate
  pause (quota back-off is 60 min, per CONTRACTS.md §6), short enough that a
  dead loop costs an evening, not text2cad's 4-night blackout.
- **Watchdog is a separate launchd job**: a dead process cannot report its
  own death. The independence is the feature.
- **Heartbeat = DAYBOOK.json mtime**: written by every tick even when the
  tick is a no-op (audit dirty, budget spent, no lease) — so "alive but
  idle" and "dead" are distinguishable, the exact failure text2cad's
  `.heartbeat`-before-idempotency-check ordering exists to catch.

## CI

`.github/workflows/ci.yml` runs the full stdlib unittest suite on Python 3.9
(the Mac's system python — the real runtime) and 3.12 (the future), with
`BOB_MOCK_AGENTS=1` so no test ever shells the real `claude`. Note the
workflow file must live at the *git repo root* (`inventors/.github/workflows/`)
for GitHub to pick it up; the copy here is the source of truth the integrator
promotes.
