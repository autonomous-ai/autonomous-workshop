# ops — how Eve runs 24/7

Two launchd agents on one Mac. No cron, no daemon process: launchd runs
`eve drive --steps 1` every 30 minutes, and a separate hourly watchdog alarms
if those one-step drives go quiet. The pattern is a direct port of Bob's ops
and of text2cad's cron + watchdog + Telegram mechanics
(`docs/research/text2cad-lessons.md` in
Bob's repo), which paid $430 to learn that harness silence — not bad products
— is where the money dies.

## The pieces

| File | Job |
|---|---|
| `launchd/ai.autonomous.eve.plist.in` | Template for `python3 bin/eve drive --steps 1` every 1800s. One scheduled run advances at most one real unit of work and logs to the historical `state/logs/tick.log`. PATH includes `~/.local/bin` (where `claude` lives — launchd gives agents a bare PATH). |
| `launchd/ai.autonomous.eve.watchdog.plist.in` | Template for running `watchdog.sh` hourly at :07. |
| `watchdog.sh` | dead-man switch. Alarms via Telegram when `state/DAYBOOK.json` (the drive heartbeat) is missing or >6h stale, or when a fresh `Traceback` appears in the tail of `tick.log`. Rate-limited by marker files in `state/` so one dead night is one DM, not twelve. |
| `render_launchd.py` | Safely binds the current checkout and service-user home into a plist template using `plistlib`; paths containing spaces or XML metacharacters are not shell-substituted. |
| `install.sh` | resolves the repository-root `../../src`, proves `/usr/bin/python3` imports that exact `inventor_workshop/__init__.py`, renders both plists for the current checkout into `~/Library/LaunchAgents`, validates them, then `launchctl bootstrap`s them. Refuses a missing or different Workshop — a broken deploy must fail at install time, not silently every 30 minutes. Idempotent (re-run = redeploy). |
| `uninstall.sh` | boots both agents out and removes the plists. Keeps `state/` — stopping the schedule never deletes work. Idempotent. |

## Install / operate

```sh
ops/install.sh                                        # install or redeploy both agents
tail -f state/logs/tick.log                           # watch the loop live
launchctl kickstart gui/$(id -u)/ai.autonomous.eve    # force a one-step drive now
ops/uninstall.sh                                      # stop everything
```

The installer binds launchd's `PYTHONPATH` and `EVE_WORKSHOP_SRC` to the exact
repository-root `../../src` tree and refuses unless the same `/usr/bin/python3` used
by launchd imports `inventor_workshop` from that exact file. This catches both a
missing runtime and a stale globally installed package before a future
Make tick reaches the Workshop artifact boundary. For a nonstandard layout,
set `EVE_WORKSHOP_SRC=/absolute/path/to/autonomous-workshop/src` when running
`ops/install.sh`. Existing deployments may temporarily keep `EVE_CORE_SRC`;
if both names are set they must resolve to the same directory or installation
fails closed.
Workshop's runtime database and retained exact artifacts live under `state/`
and are deliberately preserved by `ops/uninstall.sh`. Existing paths containing
`clockwork` or `pack` are persisted compatibility names.

Telegram alerts need `EVE_TELEGRAM_TOKEN` and `EVE_TELEGRAM_CHAT` — put them
in `.env` at the repo root (`watchdog.sh` sources it; launchd inherits almost
no environment). Without them the watchdog still runs and shouts to
`state/logs/watchdog.log` instead of DMing.

## Why these numbers

- **1800s one-step drive**: `drive --steps 1` advances at most one unit of
  work, cheap to kill and resume. text2cad's daily monolith lost the entire
  day's spend when its 3h ceiling killed a healthy run; thirty-minute steps
  bound the blast radius.
- **6h heartbeat threshold**: 12 missed scheduled drives. Longer than any
  legitimate pause, short enough that a dead loop costs an evening, not
  text2cad's 4-night blackout.
- **Watchdog is a separate launchd job**: a dead process cannot report its
  own death. The independence is the feature.
- **Heartbeat = DAYBOOK.json mtime**: written by every drive even when the
  internal tick is a no-op (audit dirty, no lease) — so "alive but idle" and
  "dead" are distinguishable, the exact failure text2cad's ordering exists to
  catch.

## CI

`.github/workflows/ci.yml` at the git repository root runs Eve's pytest suite
on Python 3.9 and 3.12. The pinned test requirements install the repository-root
Workshop package; no credentials are required, and mocked runtime/storefront
tests prove it blocks a duplicate POST after an ambiguous response.
