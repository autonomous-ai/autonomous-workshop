# Run Workshop without a builder chat

Current runner interface:

```sh
.venv/bin/python run_wish_codex.py --wish 'make a beherit from berserk' --workflow spark --effort medium --dry-run
.venv/bin/python run_wish_codex.py --wish 'make a beherit from berserk' --workflow spark --effort medium --yes
.venv/bin/python run_wish_codex.py --wish 'a rubber-band-powered pinball toy' --workflow spark --model astra --effort ultra --max-tokens 100000000 --dry-run
.venv/bin/python run_wish.py --wish 'make a beherit from berserk' --agent claude --model sonnet --workflow spark --effort high --dry-run
.venv/bin/python run_wish_codex.py --resume <wish-id> --yes
```

`run_wish.py` defaults to Claude/Sonnet/high/Spark; `run_wish_codex.py` defaults
to Codex/Astra/medium/Spark. `--workflow` selects Spark/Forge/Quest; `--effort`
selects reasoning. `ultra` requires Codex with `astra` or `gpt-6-astra`; the
runner validates this through the same runtime policy as the CLI. The
underlying CLI uses `--agent`. Runner aliases
`--manager` and `--reasoning-effort` translate to the current spelling;
old `--effort spark` is rejected. OpenRouter override is not supported by the
new host CLI, so `--openrouter` fails explicitly rather than silently routing
somewhere else. The runner no longer loads gateway credentials from `.env`.

Resume uses the host's frozen runtime, model and reasoning; do not supply
replacement selection flags. It ignores CONFIG's token limit on resume.
An explicit `--max-tokens N` sets the total allowance while preserving charged
usage. New Codex products use the host's default input-plus-output token cap;
Claude does not have equivalent measured-token enforcement. The stale local
`budgets-v2.md` reference was removed from the source template. Existing product
workspaces are untouched and retain their frozen instructions.

Both runners pass `--strict`: waiting returns nonzero. Inspect status and resume
the same id rather than blindly creating another Wish. `--yes` authorizes the
normal host publication path if credentials and all gates permit it; it never
starts physical printing. `--dry-run` only prints the command.

Validation here checks command construction against the actual current CLI,
resume immutability, explicit budget forwarding, unsupported settings and real
runner entrypoints without launching a paid native session. Claude's earlier
local roster/silent-timeout fixes are not present in this pulled source; the
historical records below are not current live acceptance claims.

## Local Codex installation

Both runners check for an optional isolated Codex 0.153.4 installation under
`~/.local/share/workshop/codex-0.153.4/` and select its native executable only
when that file exists and `WORKSHOP_CODEX_BIN` is unset. That isolated path is
absent on this workstation as checked on 2026-09-10. The installed native
executable below reports Codex 0.153.4; select it explicitly for either runner
or direct `python -m cli` commands:

```sh
export WORKSHOP_CODEX_BIN="$HOME/.local/lib/node_modules/@openai/codex/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex"
"$WORKSHOP_CODEX_BIN" --version
```

The explicit override takes precedence. Dry-run displays the selected override
without launching or resuming a product. Paths are workstation-specific;
confirm the executable exists and reports the supported version locally.

## Historical local validation before pull (2026-09-07)

A new Claude/Sonnet Spark run started from `run_wish.py --yes`, with the portable
stage reference frozen into its workspace and no builder-chat follow-up. It
persisted the creative source and delegated CAD through a native subagent, but
had no STEP/STL after 21 minutes 7 seconds. The benchmark was interrupted by the
builder, preserving its session and checkpoint; this is not a completed Make
or an end-to-end acceptance pass. The run's observed model id was
`claude-sonnet-5` (selected through the `sonnet` alias).

The subsequent schema-navigation clarifications and silent-CLI timeout fix
passed local tests but were added after that run started. They have not yet
passed a fresh live Sonnet acceptance run. Shared contracts and tests establish
portability of the interface, not equal speed or quality across models.

A subsequent live Claude run exposed a host projection mismatch: MANAGER.json
named `.claude/agents` while only Codex TOMLs existed. ADR 0045 fixes the
materializer and exact-binding path for new Claude runs, with a real-roster test
rather than metadata-only coverage. Frozen failing runs are preserved.


### Homebrew Python sandbox repair (2026-09-07)

The native runtime grants the exact Python framework binary, launcher alias
traversal directories, and linked standard-library dependencies read-only.
A matching pre-fix session policy can resume with the same session identity;
unrelated policy or checkpoint changes remain rejected. An already-running
host must exit before it can load this code update. Resume preserves spent
tokens and the frozen model selection.

The opt-in local sandbox test (no model call) is:

```sh
WORKSHOP_SANDBOX_TEST_BIN="$WORKSHOP_CODEX_BIN" .venv/bin/python -m unittest tests.runtime.test_python_framework_policy
```

It checks a real CAD STEP export, finalizer startup, and denial of an `.env`
fixture inside the managed sandbox. It does not claim a completed product gate.
