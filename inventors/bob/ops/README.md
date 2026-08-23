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
| `launchd/ai.autonomous.bob.plist.in` | Template for `python3 bob.py tick` every 1800s. Logs to `state/logs/tick.log`. PATH includes `~/.local/bin` (where `claude` lives — launchd gives agents a bare PATH). |
| `launchd/ai.autonomous.bob.watchdog.plist.in` | Template for running `watchdog.sh` hourly at :07. |
| `watchdog.sh` | dead-man switch. Alarms via Telegram when `state/DAYBOOK.json` (the tick heartbeat) is missing or >6h stale, or when a fresh `Traceback` appears in the tail of `tick.log`. Rate-limited by marker files in `state/` so one dead night is one DM, not twelve. |
| `render_launchd.py` | Safely binds the current checkout, service-user home, and validated Foundation source into a plist template using `plistlib`; paths containing spaces or XML metacharacters are not shell-substituted. |
| `install.sh` | renders both plists for the current checkout into `~/Library/LaunchAgents`, validates them, then `launchctl bootstrap`s them. Refuses if `bob.py`, the harness, or the shared `../../foundation/src/inventor_core` runtime is missing — a broken deploy must fail at install time, not silently every 30 minutes. Idempotent (re-run = redeploy). |
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

Bob is deployed from this monorepo under `inventors/bob/`, with `foundation/` at
the repository root. The runtime adapter resolves `../../foundation/src` without
a pip install. A nonstandard layout may set
`BOB_CORE_SRC=/absolute/path/to/foundation/src`; `ops/install.sh` verifies that pin
and persists the resolved path in the scheduled tick's environment before loading
either agent. Publication then writes the private Foundation SQLite outbox at
`state/inventor-core.sqlite3`.

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
workflow file must live at the *git repo root* (`.github/workflows/`)
for GitHub to pick it up; the copy here is the source of truth the integrator
promotes.

## The CAD venv (build stage + mesh gate)

The vendored `skills/cad` toolchain (see `skills/PROVENANCE.md`) needs
Python ≥3.10 with `cadgen==0.4.19`:

```bash
python3.12 -m venv .venv-cad
.venv-cad/bin/pip install cadgen==0.4.19
echo "BOB_CAD_PY=$PWD/.venv-cad/bin/python" >> .env
```

Without `BOB_CAD_PY` the pipeline still runs: the builder falls back to the
JSON parts map and the build gate records "mesh checks SKIPPED" as a warning
— never a silent pass.
