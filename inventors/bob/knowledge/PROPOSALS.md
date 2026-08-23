# Proposals

Designs agreed on paper, not yet built. Each entry is dated, names the
problem with its receipt, and pins the design far enough that the builder
does not re-litigate it. A proposal graduates by being implemented and
noted here with the commit.

---

## 2026-08-22 — Subprocess isolation for agent-written engines

**Status: proposed, not implemented.** Interim mitigation shipped the same
day: source lint in `loops/playtest.load_engine` (import whitelist +
banned-token refusal, `ENGINE_IMPORT_WHITELIST` / `ENGINE_BANNED_TOKENS`).
The lint is a tripwire, not a wall — Python source scanning cannot be made
sound against a determined generator, so this proposal is the real fix.

### Problem (review 2026-08-22, MAJOR)

`games/<slug>/playtest/engine.py` is written by a generator agent and
exec'd IN-PROCESS by `playtest.load_engine` (`spec.loader.exec_module`).
The process has full user privileges, so a reward-seeking engine can:

- monkeypatch the scorer: `loops.simmetrics.simulate` is looked up at call
  time, so `import loops.simmetrics as sm; sm.simulate = lambda *a, **k:
  <all-pass report>` fabricates a green sim gate;
- write `state/QUEUE.json` or `state/REWARD_LEDGER.jsonl` directly,
  defeating the frozen-reward design end to end.

METR receipt: reward hacking is 43x likelier when the model can see or
touch the scorer. The whole "generators never see the scorer" architecture
is void while generator code runs in the scorer's address space.

### Design

One runner process per engine, speaking JSON over stdio; the scorer never
imports the engine.

1. **Runner script** `loops/engine_runner.py` (stdlib only). Launched as
   `subprocess.Popen([sys.executable, "-I", runner_path, engine_path],
   ...)` — `-I` (isolated) drops env-var injection, user site-packages,
   and cwd from `sys.path`.
2. **Protocol**: newline-delimited JSON requests/responses on stdio.
   Methods mirror the eight-call engine contract plus two batch calls:
   - `new_game`, `player_to_move`, `legal_moves`, `apply`, `is_over`,
     `winners`, `scores`, `observation`, `meta` (ASSUMPTIONS + IDEA_SHA);
   - `playout` — run a whole game inside the runner given seat policy
     NAMES, seed, and move cap, returning the game row (`length`,
     `terminated`, `winners`, `branchings`, `scores_trace`). This keeps
     the sim battery at O(1) round-trips per game instead of O(moves) —
     the 1,000-game batch does millions of `apply` calls and per-call RPC
     would turn minutes into hours;
   - `batch` — n playouts in one request, for the probe and mirrors.
   Policy implementations (`random`/`greedy`/`lookahead1`) move into (or
   are imported by) the runner so playouts stay in-process there; the
   POLICIES table stays the scorer's single source of truth by shipping
   the runner a copy checked by the same tests.
3. **State stays in the runner.** `new_game`/`apply` return opaque integer
   state handles; the parent never deserializes a state object (engine
   states may be arbitrary picklable structures — or hostile ones).
   `observation` returns a string, already length-capped runner-side to
   the table loop's 2000-char fence.
4. **Containment**, set in `preexec_fn` (POSIX; Bob runs on macOS/Linux):
   - `resource.setrlimit(RLIMIT_CPU, ...)` — hard CPU ceiling per runner;
   - `resource.setrlimit(RLIMIT_AS, ...)` — address-space cap (512 MB);
   - `resource.setrlimit(RLIMIT_NOFILE, (8, 8))` — stdio plus nothing;
   - cwd = a fresh empty temp dir, so relative writes land nowhere;
   - `start_new_session=True` + the existing process-group kill from
     `harness.agents._kill_process_group` (the warm-daemon receipt).
   This does not stop absolute-path writes by a malicious engine — POSIX
   rlimits are not a filesystem sandbox — but combined with the source
   lint (no `open(`/`os.`/`__import__`) the residual risk needs a novel
   escape, not a one-liner. macOS `sandbox-exec`/seatbelt is the follow-on
   if the residual matters.
5. **Wall-clock per call** in the parent: `select` on the runner's stdout
   with a deadline (5 s per simple call, `move_cap`-scaled for playouts);
   a deadline miss kills the process group and surfaces as
   `EngineContractError("engine runner timed out")` — the invent loop
   parks the game exactly as it does for a lint refusal.
6. **Failure semantics**: runner crash, malformed JSON, or nonzero exit →
   `EngineContractError` with the stderr tail. Never retry in-process;
   never fall back to in-process exec (the fallback would be the hole).
7. **Call sites**: `playtest.load_engine` returns a `RemoteEngine` proxy
   exposing the same eight callables plus `ASSUMPTIONS`/`IDEA_SHA`, so
   `simmetrics.simulate` and `tablerun.run_tables` change only where they
   can exploit `playout`/`batch`. The IDEA_SHA staleness check moves to
   the `meta` call, still before any scoring.
8. **Tests**: fixture engines run unchanged through the proxy (contract
   parity suite); adversarial fixtures — engine that tries to write an
   absolute path, engine that busy-loops (CPU rlimit kills it), engine
   that prints garbage to stdout (protocol desync refused).

### Cost

One extra Python process per sim/table run (runner reuse within a run,
never across engines), a JSON hop per table turn (noise next to the LLM
seat call), and the `playout` batching work in simmetrics. Estimated a
day of build plus the parity suite.
