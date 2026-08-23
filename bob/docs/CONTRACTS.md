# Bob — module contracts (build against this, exactly)

This file is the single source of truth for module boundaries, file ownership,
schemas, and CLI verbs. A builder implements ONLY the files it owns. Shared
integration (`bob.py`) is written by the integrator, not by builders.

Language: Python 3.9-compatible, **stdlib only** for the harness (no pip deps).
Every module ships with tests under `tests/`. All state files are JSON with
atomic writes (write tmp + `os.replace`). All timestamps UTC ISO-8601.

Path root: everything below is relative to `bob/`.

---

## 1. State files (schemas)

### state/QUEUE.json — the game queue
```json
{
  "version": 2,
  "games": {
    "<slug>": {
      "slug": "…", "title": "…",
      "state": "sparked|researched|ruled|rules_gated|simulated|tabled|briefed|built|build_gated|reviewed|published|live|parked|blocked|killed",
      "direction": {"family": "<mechanism-family arm id>", "players": "2-4", "weight": "light|mid"},
      "budgets": {"clarify_used": 0, "rework_used": 0, "repair_used": 0},
      "reward": {"latest": 0.0, "history": [{"at": "…", "stage": "…", "score": 0.0, "components": {}}]},
      "lease": {"holder": null, "expires": null},
      "created": "…",
      "log": [{"at": "…", "from": "…", "to": "…", "note": "…"}]
    }
  }
}
```
Budgets: `CLARIFY_BUDGET=3`, `REWORK_BUDGET=3`, `REPAIR_BUDGET=2` — constants in
`harness/budgets.py`, never in prompts. Exhaustion ⇒ `parked` (never silent).

### state/REWARD_LEDGER.jsonl — append-only, one row per scored event
```json
{"at": "…", "slug": "…", "stage": "…", "kind": "iteration|publish|market|human_table",
 "score": 0.0, "components": {"fun_sim": 0, "fun_table": 0, "clarity": 0, "novelty_margin": 0, "buildability": 0},
 "delta": 0.0, "cost_usd": 0.0, "notes": "…"}
```

### state/BANDIT.json — UCB1 arms over design directions
```json
{"arms": {"<family-id>": {"pulls": 0, "reward_sum": 0.0, "last": null}}, "total_pulls": 0}
```

### state/DAYBOOK.json — per-day spend + tick heartbeat
```json
{"2026-08-22": {"ticks": 0, "cost_usd": 0.0, "steps": []}, "heartbeat": "…"}
```

## 2. Module ownership

| Module | Owns files | Public API (exact) |
|---|---|---|
| queue | `harness/queue.py` | `load()`, `save(q)`, `claim_next(loop_name) -> Step\|None`, `advance(slug, to_state, note)`, `release(slug)`, `park(slug, reason)`. File lock via `fcntl.flock` on `state/.lock`. Leases expire after `LEASE_MINUTES=45`. |
| budgets | `harness/budgets.py` | `spend(game_dict, kind) -> bool` (False = exhausted), constants. |
| reward | `harness/reward.py` | `hard_gates(evidence: dict) -> dict[str,bool]`, `score(components: dict) -> float`, `WEIGHTS`, `PUBLISH_THRESHOLD=70.0`, `MIN_DELTA=2.0`. **Frozen: `harness/integrity.py` records sha256 of this file; a changed hash fails `bob audit`.** |
| ledger | `harness/ledger.py` | `append(row: dict)`, `rows(since=None, slug=None) -> list`, `spend_today() -> float`. |
| bandit | `harness/bandit.py` | Thompson sampling over Beta posteriors (`random.betavariate`), ×0.9/week discount on effective counts, wildcard arm always present. `pick() -> str`, `update(arm, reward01: float)`, `retro_bonus(arm, bonus)`, `arms() -> dict`. Arms + priors from `corpus/DIRECTIONS.json` (classic-reborn seeds alpha=3,beta=2). |
| runner | `harness/agents.py` | `run_agent(name, prompt, *, model=None, max_minutes=15, cwd=None) -> AgentResult(text, cost_usd, minutes, transcript_path)`. Shells `claude -p` headless with `--output-format json` (parse `total_cost_usd`); per-phase model from env `BOB_<PHASE>_MODEL`; transcripts to `state/transcripts/<ts>-<name>.json`; kills process group on overrun (SIGTERM→SIGKILL, grace 5s); **honors `BOB_MOCK_AGENTS=1`: reads canned reply from `tests/fixtures/<name>.txt` — required for tests and dry runs.** |
| timebudget | `harness/timebudget.py` | port of Peter's `with_budget` ledger idea: `open_run(total_minutes)`, `step(cap_minutes) -> context manager`, `report()`. One ledger per repo at `state/.tick-budget.json`. |
| integrity | `harness/integrity.py` | `audit() -> list[str]` (reward hash pinned; improve-writable path allowlist; sim-vs-human divergence check from ledger; stale heartbeat). |
| telegram | `harness/telegram.py` | `send(text, buttons=None)`, `poll_decisions() -> list`; no-op with warning when `BOB_TELEGRAM_TOKEN`/`BOB_TELEGRAM_CHAT` unset. |
| publish | `harness/publish.py`, `harness/core_runtime.py` | Implements docs/research/publish-contract.md Path B through shared core. `build_zip` produces a secret-scanned canonical core packet with an embedded content-addressed manifest; `validate(slug) -> list[str]` also checks RULES.md, cover, copy caps, and the pinned Bob identity. `import_draft(slug)` uses `PandaPublicationCoordinator` + `state/inventor-core.sqlite3`, always requests draft, records the effect before HTTP, and persists `core_intent_id` in `published.json`; timeout/5xx/invalid-201 outcomes become unknown and cannot POST again. A legacy remote receipt without complete core intent/content identity is explicitly stranded: Bob cannot adopt its owner or safely retry its slug. The current owner must resolve that effect separately, then a distinct pinned Bob principal may re-import under a new slug. The core product key is stable per slug, so changing bytes cannot bypass an unknown intent; corrected bytes need a new slug until Panda supplies content/idempotency proof. `curate(slug)` retains Bob's use-case/story-block API. `flip_public(slug, price_cents)` reuses the same intent and requires core's exact owner/artifact/history/active-USD-listing/price/SKU readback; `reconcile_public(slug)` never resends `/publish` and performs only auth rotation plus GET readback for a core-recorded ambiguous flip. `unpublish(slug)` remains the reversible kill switch. `BOB_PUBLISH_DRY_RUN=1` still produces and verifies the core packet without network; its `published.json` carries `publication_authority: none`, so arming real effects promotes it through the core outbox instead of treating the rehearsal as an idempotency receipt. |
| invent loop | `loops/invent.py` | `tick(step) -> None`: state-machine dispatch table `STEP_HANDLERS: dict[state, handler]`; each handler = compose prompt (from `.claude/agents/` file + game dir) → `run_agent` → validate output → write artifacts under `games/<slug>/` → score via reward → advance/park. |
| scholar loop | `loops/scholar.py` | `tick() -> None`: alternate two lanes — history lane pops `corpus/STUDY_QUEUE.json` (agent bob-scholar), book lane pops `corpus/BOOK_QUEUE.json` (agent bob-librarian). Card written to `corpus/cards/<lane>-<id>.md`, `corpus/INDEX.md` updated, unit marked done. Librarian honesty rule lives in BOOK_QUEUE.json comment. |
| architect loop | `loops/architect.py` | `tick() -> None`: weekly; reads sources list `knowledge/SOURCES.md`, runs bob-architect, appends `knowledge/architecture-notes.md`, files proposals to `knowledge/PROPOSALS.md`. |
| playtest kit | `loops/playtest.py`, `loops/simmetrics.py` | `build_engine(slug)`, `simulate(slug, n=500) -> SimReport` (lead_changes, closeness, policy_ladder {random,greedy,lookahead1} winrates, fpa, length_dist, decision_density), `llm_table(slug, seats) -> TableReport`. Engine contract: `games/<slug>/playtest/engine.py` exposes `new_game(n_players, seed)`, `legal_moves(s)`, `apply(s, m)`, `is_over(s)`, `winner(s)`, `score(s, p)`. |
| meta loop | `loops/meta.py` | `improve() -> None`: weekly self-improvement session; MAY edit only: `.claude/agents/*.md`, `knowledge/lessons.md`, `corpus/**`, `knowledge/PROPOSALS.md`; code changes → branch + PR, never main. Path allowlist ENFORCED in code before any write is applied. Never edits: `harness/reward.py`, `knowledge/TASTE.md`, `state/**`, `harness/integrity.py`. |
| ops | `ops/launchd/ai.autonomous.bob.plist.in`, `ops/render_launchd.py`, `ops/watchdog.sh`, `ops/install.sh`, `ops/uninstall.sh` | installer renders the current checkout into a launchd StartInterval 1800s job → `bob.py tick`; watchdog daily: heartbeat >6h stale ⇒ Telegram alert. |

## 3. CLI (`bob.py`, integrator-owned)

```
bob.py tick            # one step of one loop (invent-priority, then scholar, then architect if due)
bob.py status          # queue + budgets + today's spend + heartbeat
bob.py improve         # run meta-loop improve session now
bob.py audit           # integrity checks (exit 1 on violation)
bob.py publish <slug>  # draft-publish a game at awaiting_owner→approved
bob.py seed            # first-run: seed corpus study queue + bandit arms
bob.py daemon install|uninstall|status
```

Tick preconditions (in order, all in code): `audit()` clean → `spend_today() < BOB_DAILY_BUDGET_USD` (default 25.0) → lease available. Any failure = logged no-op, exit 0.

## 4. Env (all optional except none)
`BOB_DAILY_BUDGET_USD=25` · `BOB_MOCK_AGENTS` · `BOB_PUBLISH_DRY_RUN=1` ·
`BOB_TELEGRAM_TOKEN/CHAT` · `BOB_<PHASE>_MODEL` (PHASE ∈ IDEATE, RULES, LENS,
ENGINE, TABLE, BRIEF, BUILD, JUDGE, SCHOLAR, ARCHITECT, IMPROVE) ·
`BOB_HOME` (defaults to repo `bob/`).

## 5. Testing bar
Every module: **stdlib `unittest`** tests (no pytest on this box), no network,
no real `claude` calls (`BOB_MOCK_AGENTS=1`). Run: `python3 -m unittest discover -s tests -v`
from `bob/`. Each test file is self-contained: builds its own temp BOB_HOME via
`tests/util.py:make_home()` (integrator-owned helper; until it exists, create
temp dirs inline with tempfile). Python 3.9-compatible syntax ONLY (no `match`,
no `X | Y` type unions).
E2E: `tests/test_e2e_dry.py` drives one game from `sparked` to `published`
(dry-run publish) with mocked agents and asserts ledger rows + budget behavior.

## 6. Cross-module rules for builders
- Import only modules whose API is pinned in §2 — code to the contract, not to
  the other builder's implementation.
- Every state write is atomic (tmp + os.replace) under the fcntl lock.
- Every error message says what to do next, never a bare traceback string.
- No module reads env at import time; read inside functions (testability).
- `harness/novelty.py`: `bgg_candidates(title, keywords) -> list[dict]` — BGG
  XML API2 search (stdlib urllib), 24h file cache in `state/bgg_cache/`,
  returns top-5 {name, year, bgg_id, url}; network errors return `[]` with a
  warning field, never raise (novelty judge then works from corpus only and
  says so).
- Rate-limit/quota: `harness/agents.py` detects `usage limit|limit reached|rate limit`
  in CLI errors → raises `QuotaExhausted`; callers set DAYBOOK `quota_until`
  (now + 60 min) and the tick loop no-ops until then. Never retry into a wall.
