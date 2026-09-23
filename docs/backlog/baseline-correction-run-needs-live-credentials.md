# Baseline Correction Run (issue #40) needs a live-logged-in `claude` CLI

- Status: Blocked, not attempted — no fabricated baseline recorded
- Priority: High (blocks re-justification of the tickets #40 itself blocks)
- Temporary behavior: None; no Run was started

## What issue #40 asks for

One real Correction Run via `workshop fix --agent claude` on the Claude Code
Manager runtime (model `claude-opus-5`), producing a schema-2 `TIMING.json`
in a fresh Toy Archive, plus a write-up interpreting the measured/total/
unmeasured split and comparing it against the stale `ad-astra-antisol-v12`
and `-v13` traces. The issue is explicit that the deliverable is the
interpreted document, not code.

## Progress since the first attempt (commit 254efa28)

The Python-environment half of the original blocker is now resolved and is
**not** the remaining gap:

- `pip` is installable in this sandbox despite no `ensurepip`/`uv`, via
  `curl -sS https://bootstrap.pypa.io/get-pip.py | python3 - --user
  --break-system-packages` (PyPI is reachable; the system Python is
  externally-managed, so `--break-system-packages` is required).
- `python3 -m pip install --user --break-system-packages -e .` then installs
  the full dependency set (`cadgen`, `build123d`, `cadquery-ocp`, etc.) and
  the `workshop` console script cleanly.
- `workshop doctor` (with `~/.local/bin` on `PATH`) reports
  `claude   ready — Claude Code is available as an experimental Manager via
  --agent claude.` — the `claude` CLI binary itself is present and on PATH.

## Why it still could not be attempted here

`workshop doctor`'s "ready" check for `claude` is a static check (binary
present on `PATH`) — it does not check login state. Tracing
`src/workshop/runtime/claude.py`'s `ClaudeNativeSessionLauncher` shows the
real requirement: it shells out to a bare `claude --print --output-format
stream-json --permission-mode bypassPermissions ...` subprocess with a
strict allowlisted environment (`claude_subprocess_environment()` forwards
only `PATH, HOME, USER, ..., SSL_CERT_*` and a few workshop-internal vars).
**`ANTHROPIC_API_KEY` is deliberately not forwarded or read** — auth is
whatever OAuth/session credential the `claude` CLI has persisted under
`HOME`/`XDG_CONFIG_HOME` from an interactive `claude /login`, the same as a
human's local CLI. Confirmed empirically:

```
$ claude --print "say hi"
Not logged in · Please run /login
```

`~/.claude` in this sandbox has no `.credentials.json` or equivalent — this
session's own `claude` process is managed by the parent harness
(`CLAUDE_CODE_ENTRYPOINT=sdk-cli`, `CLAUDE_CODE_CHILD_SESSION=1`), not an
independently logged-in CLI, and none of the `CLAUDE_CODE_SESSION_ID` /
`CLAUDE_CODE_MESSAGING_SOCKET` / `CLAUDE_CODE_MESSAGING_TOKEN` /
`CLAUDE_CODE_EXECPATH` env vars it does have are read by `claude.py` or its
subprocess allowlist — there is no supported way to hand the launcher this
session's own credentials.

This matches the note already on record in commit 7a7e33b2 (issue #39) and
the first pass at this ticket (commit 254efa28): the remaining gap is a
missing interactive `claude /login` in this sandbox's `HOME`, not something
either ticket's code introduced, and not fixable by an unattended agent
session.

## What was verified instead

- `toys/ad-astra-antisol-v12` and `toys/ad-astra-antisol-v13` — the two
  stale traces this baseline is meant to replace — still carry schema-1
  `TIMING.json` (no `breakdown` field) and `TOKENS.json` with
  `status: "unavailable"`, consistent with the issue's claim that no
  current-codebase Claude baseline exists yet.
- The schema-2 timing/breakdown plumbing landed by #38/#39 is present on
  this branch and ready to receive a real run's output once one can be
  executed.
- Posting progress directly to GitHub issue #40 was also attempted and
  failed: the configured `gh` token has read-only issue access
  (`Resource not accessible by personal access token` on both the GraphQL
  `addComment` mutation and the REST `issues/40/comments` endpoint), so
  this backlog note is the only durable record of the attempt.

## Resolution criteria

Remove this entry once a session with both an installable Python
environment (now resolved, see above — `pip install -e .` works) and a
`claude` CLI already logged in (`claude /login` completed under this
sandbox's `HOME`, or an equivalent persisted credential file) has:

1. run `workshop fix --agent claude` (default model `claude-opus-5`) to
   completion on current code, producing a sealed Toy Archive with a
   schema-2 `TIMING.json`;
2. written up the measured/total/unmeasured split, the largest measured
   stage/operation items, and an explicit comparison against
   `ad-astra-antisol-v12`/`-v13`, naming any contradicted figure;
3. recorded the token record as `unavailable` (not zero) per the Claude
   runtime's known limitation; and
4. re-justified or recommended closure for each ticket blocked on #40.
