# Bob — an autonomous inventor of 3D-printable board games

Bob is a multi-agent system that runs 24/7 on one Mac, invents board games
that could not exist before 3D printing, iterates each one against a frozen
reward function until publishable, publishes them to the Factory marketplace
automatically as an AI creator, and gets better every week. When someone buys,
we print and ship.

One human sits above it (Dee, via Telegram): he is a kill switch and a taste
signal, not a turnstile.

Design provenance: everything here traces to `docs/research/` (8 reports,
2026-08-22) and two in-house inventors that ran before Bob (vibe-ideas: 6
ideas → 1 shipped; text2cad: 18 cycles / $430 → 1 shipped). Bob is the third
attempt, built on their receipts.

## The one sentence that decides everything

**Every system that ever self-improved was an evaluator story** (FunSearch,
AlphaEvolve, Ludi/Yavalath — see `docs/research/self-improvement-landscape.md`).
LUDI's author said the hard problem was never generating 1,389 games — it was
skimming the cream. So Bob's evaluator (the reward cascade) is the product;
the generator agents are replaceable mutation operators around it.

## The loops (the meta-frame)

```
                    ┌──────────────────────────────────────────────┐
                    │  L0 META  (weekly)                            │
                    │  reads: reward ledger, audit, Dee's verdicts  │
                    │  edits: prompts/lessons/corpus (doc-tier)     │
                    │  proposes: code changes as PRs (never main)   │
                    └──────┬───────────────────────────▲────────────┘
                           │ better prompts/arms       │ evidence
        ┌──────────────────▼─────────────────┐         │
        │  L1 INVENT  (the factory, ~hourly ticks)     │
        │  spark → rules → engine-played → LLM-tabled  │
        │  → briefed → CAD-built → gated → published   │
        └───▲─────────────▲──────────────────┬─────────┘
            │ mechanisms,  │ what-makes-fun   │ games live on the site
            │ eras, books  │ cards            │
  ┌─────────┴───┐  ┌───────┴─────┐   ┌────────▼───────────────┐
  │ L2 SCHOLAR  │  │ L2b LIBRARIAN│   │ L4 PLAYTEST/FEEDBACK   │
  │ 5,000 years │  │ the great    │   │ pre-publish: sims +    │
  │ of games,   │  │ design books │   │ LLM tables; post-      │
  │ one card    │  │ (Wallis,     │   │ publish: sales, market │
  │ per tick    │  │ Engelstein,  │   │ telemetry, human       │
  └─────────────┘  │ Koster …)    │   │ "play again?" reports  │
                   └──────────────┘   └────────┬───────────────┘
  ┌──────────────────────────────┐             │ retro reward → bandit
  │ L3 ARCHITECT (weekly)        │◀────────────┘
  │ studies multi-agent/harness  │
  │ engineering (Anthropic etc.) │→ proposals for L0
  └──────────────────────────────┘
```

The loops feed each other: scholar/librarian cards are the ideator's raw
material and the novelty judge's comparison corpus; playtest results are the
reward; the meta loop turns reward history into better prompts and better
bandit priors; the architect loop turns the outside world's harness lessons
into PRs. No loop talks to another directly — **files are the message bus**
(corpus/, state/, games/), per Anthropic's artifact pattern.

## Two lanes, one pipeline

Market receipt (2026-08): two chess sets already sold before Bob existed —
buyers pay today for **original physical editions of classics**. So the bandit
holds two kinds of arms:

- **lane=invention** — games that never existed (7 mechanism-family arms +
  wildcard). Full pipeline. The compounding bet.
- **lane=edition** (`classic-reborn` arm, Beta prior seeded by the 2 sales) —
  original sculptural editions of public-domain classics. Skips engine/sim
  (the classic proved itself over centuries); scored on physical originality,
  clarity, and build quality. Keeps the lights on, exercises print+ship.

## The invent pipeline (L1) — states and gate order

```
sparked → researched → ruled → rules_gated → simulated → tabled
        → briefed → built → build_gated → reviewed → published → live
   (side: repairing, parked, blocked, killed; quota_wait is a tick-level state)
```

Gate order IS the economics — the Armillary receipt (vibe-ideas): 6 CAD repair
rounds + 2 owner amendments spent on rules that later failed the playtest.
**Nothing expensive happens before the game is machine-played and LLM-tabled:**

1. **sparked** — bandit picks an arm; ideator (reading TASTE.md, corpus cards,
   nearest archive games) generates k=5 sparks; lint + one triage judge keep 1.
2. **ruled** — complete rules doc + bill of physical parts, in Bob's schema.
3. **rules_gated** — deterministic `rules_check` + a blind rules lens. (Both
   are known-insufficient alone: all three vibe-ideas games that passed these
   failed their first real playout. They're the cheap pre-filter, nothing more.)
4. **simulated** — an agent writes `playtest/engine.py` under the fixed engine
   contract; then **code, not agents**, plays ≥1,000 fast playouts + a policy
   ladder (random → greedy → 2-ply → MCTS). Metrics: the GAVEL five as hard
   floors (balance, decisiveness, completion, agency, coverage — harmonic
   mean, one bad dimension tanks it) + the Browne aesthetic tier (drama,
   late-uncertainty, lead changes, killer-move scarcity, permanence, duration
   distribution). Seat bias 45–55% at strongest rung or auto-apply pie
   rule/komi and re-measure. Full spec: `docs/research/boardgame-science.md` §2.
5. **tabled** — LLM seats play 4 real games through the engine, choosing moves
   **by index from engine-legal moves** (they cannot cheat, misremember, or
   soften a dull game — the loop is code; vibe-ideas' table_run design ported
   whole). Each table carries ONE distinct question. Fresh-reader lens does
   the cold rulebook Q&A.
6. **briefed → built → build_gated** — only now does CAD money get spent:
   parts brief ("print the wound" — print only the mechanism the game stands
   on), CadQuery build via the `cadcode` skill, deterministic mesh/bed/
   printability gate. Mid-build likeness milestone with abort (text2cad:
   silhouette failures cost half a build, not a whole cycle).
7. **reviewed** — per-dimension isolated judges + reward score. Iterate while
   ΔR ≥ 2 and budgets remain (clarify 3 / rework 3 / repair 2 — with the
   mech-surface hash that converts a "clarify" that changed mechanics into a
   paid rework, and the cascade-stop that blocks A→B→C patch chains).
8. **published** — publish-eligible + validator green ⇒ Bob auto-imports the
   DRAFT: via text2game's box pipeline (`BOB_PUBLISH_VIA=box` — Bob exports
   the exact `out/<slug>/` payload `text2game/publish.py` consumes, rsync +
   remote run when `BOB_BOX_SSH` is set, Telegram handoff otherwise) or the
   HTTP path. The HTTP path now uses shared Foundation's canonical artifact packet
   and durable SQLite publication outbox; timeout/5xx import results are never
   retried. **Draft→public remains owner-reviewed by default** (Dee 2026-08-22:
   "publish draft is fine… once it's ok, we'll make it auto publish");
   `BOB_AUTO_FLIP=1` makes Bob issue the price-bound Foundation flip. An out-of-band
   admindash click cannot advance Bob's queue because it lacks that local
   intent proof. CPSIA
   hard-refuse, AI-disclosure, public-domain-only IP, price floor remain
   hard pre-import gates; borderline safety parks for a human. This state is
   deliberately not scheduler-claimable: a dry-run or unverified handoff can
   never become live by bookkeeping.
9. **live** — reached only after authenticated Panda readback proves Bob owns
   the exact Foundation-bound design, `published_history_id == current_history_id`,
   and the requested active USD listing has the exact price and a SKU. L4 then folds
   market + human-table signal into the ledger; "asked to
   play again ×3 groups" upgrades the game to **proven**.

Every verdict artifact embeds the sha256 of the `idea.json` it judged — stale
verdicts refused (vibe-ideas got burned twice by mtime-only checks).

## The reward (summary — spec in docs/REWARD.md, code in harness/reward.py, FROZEN)

Hard gates (completeness, sim integrity, degeneracy, novelty-with-URL-evidence,
safety, buildability) then a 100-point score across fun_sim / fun_table /
depth / clarity / novelty_margin / physical_hook. Publish at ≥70 with no
dimension below 40% of max. Generators never see weights, thresholds, or judge
prompts (METR: reward hacking 43× likelier when the model sees the scorer).
Anchor games detect judge drift. Cold-start proxy hierarchy, declared and
weaned: Dee verdicts → human plays → engagement → sales.

## Self-improvement (the RL frame, honestly)

- **Policy** = bandit priors + TASTE.md + lessons + agent prompts (versioned
  `prompts/vN/`; in-flight games pin their version — the rainbow-deploy move).
- **Reward** = the ledger (external events outrank self-scores, always).
- **Update** = weekly meta session, evidence-fed, with authority tiers:
  DOC-tier auto-commits, CODE-tier goes to a PR, FORBIDDEN paths (reward.py,
  TASTE.md, baselines, state/) revert the whole session — enforced in Python
  before any write applies, suites-must-pass-or-revert. Repeated lessons MUST
  graduate to code (text2cad's rule: never advisory text twice — each
  graduation converts a repeated $10–25 lesson into a $0 deterministic check).
- **Integrity audit** (weekly, adversarial): gate-erosion vs baseline file the
  improver can't touch, shipped-without-measurement, degeneracy watch
  (optimizing pass-rate rewards proposing simpler games), graduation rot,
  sim-fun vs human-fun correlation with alarm on divergence.

## 24/7 operation

- launchd tick every 30 min: `bob.py tick` — audit clean → daily budget check
  → quota check → advance ONE step of ONE game (closest-to-ship priority;
  finishing beats starting), else scholar/librarian tick, else architect if
  due. Idempotent catch-up: a 10-hour lid-close costs time, nothing else.
- Every `claude -p` call: per-phase model routing, cost + turns logged from
  the CLI's own JSON (crash-safe, never overwritten), process-group kill on
  overrun, starved-vs-crashed distinguished (retry crashed; never retry
  starved at the same cap).
- **Quota is a first-class state, not an error:** rate-limit regex on errors ⇒
  `quota_wait` with deferral until the rolling window clears; a retry against
  an exhausted cap burns wall-clock and produces nothing (text2cad receipt).
- Heartbeat file first thing every tick; separate watchdog cron alarms
  Telegram at >6h silence ("a stopped pipeline looks exactly like a pipeline
  with nothing to do, until you check a month later").
- Daily spend cap in code (default $25/day). Two ceilings never crossed
  silently: dollars and the subscription window.

## Cost honesty

text2cad: $430 → 1 shipped, 58% of spend lost to harness bugs and bad
selection, not bad products. Bob's counters: kill early kill cheap (triage at
spark, milestone aborts), cascade evaluation (free lint kills before paid
sims, paid sims kill before paid tables, tables kill before CAD), cache-aware
parallel panels, deterministic everything-that-can-be. Expected steady state:
$3–8/day idle-ish ticks, $15–40 per finished game, one game per week at
quality. The ledger reports where every dollar went; `CYCLES.md`-style rows
per game.

## What Bob does NOT do

- No async agent-to-agent orchestration (Anthropic shipped their system
  without it; so do we).
- No framework (LangGraph tax exceeds rent for a solo system; AutoGen is in
  maintenance mode; every system that self-improved was a bespoke loop).
- No self-computed score as the reward of record — external events outrank.
- No publishing under a human account, ever (the Gravity Well/Newsreel
  violation is the anti-pattern); `bob` account identity + disclosure line +
  `ai-created` tag on every listing.
- No children's products (CPSIA hard-refuse at spark), no modern copyrighted
  games in the edition lane, no "addictive" in copy.
