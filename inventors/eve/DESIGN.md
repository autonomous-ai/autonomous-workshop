# Eve — autonomous board-game inventor

Eve is an autonomous, 24/7 multi-agent system that invents **3D-printable**
board games that have never existed before, carries each one through rules,
print, and fun checks until it is *actually good*, then uses the Workshop runtime
and storefront adapter to create a draft on the Autonomous site. The moment it sells, we print and ship it — the chess
sets already sold (two of them; the SF set is one) are the early proof of
that loop, and they are the bar Eve is aiming at.

Eve is the **meta-loop**: a workshop steward that continuously provisions and
feeds a set of smaller loops, each of which studies one thing or advances one
game. The loops feed each other — a study loop's output is a gate another loop
is held to; a playtest failure is a lesson that graduates into the harness.
The system never stops inventing.

Quality over quantity. The cadence target is **one game shipped per week**,
with a daily floor on *progress* (a game advances at least one stage every
day), never a daily floor on *shipping*.

This document is the design. It is written first and the code follows it. The
code's job is to make the design's invariants *mechanically* true, not to
aspire to them.

---

## 1. Why Eve (and why not "generate 100 games")

The org already has two working inventor pipelines to learn from:

- **vibe-ideas** — a board-game inventor built around a strict *rules gate*:
  one `/bg` call advances exactly one idea one step, a deterministic
  no-LLM build gate, blind lens panels, an owner gate, and a self-improvement
  loop where repeated lessons "graduate" into code.
- **text2cad** — a trend→product inventor with a hard *novelty bar*
  ("does not exist on sale, checked by search with a URL"), real measured COGS,
  and a lessons ledger.

Both proved the same thing the Anthropic multi-agent research teaches us:
**capability scales with how many tokens you spend, and multi-agent systems
win by spending enough tokens with independent, compressed context windows.**
A pipeline that replaces an idea the moment it hits an infrastructure fault
never finishes anything (vibe-ideas' explicit lesson). The unit of work must be
**the game**, not the turn; a game only leaves the queue by shipping or by
being killed with a stated reason.

Eve takes the next step beyond both: instead of a single pipeline, it is a
**self-improving meta-loop** with an explicit reward function, so it not only
invents games but keeps improving the system that invents them.

---

## 2. The loops

Eve is four running loops coordinated by a supervisor (the meta-loop). Each
loop has its own purpose, cadence, and output. The arrows are the *feed* — one
loop's output changes what another loop is held to.

```
         ┌────────────────────────────────────────────────────────────────┐
         │  META-LOOP (Eve's workshop) — supervisor, 24/7                 │
         │  schedules loops + per-game pipeline steps                     │
         │  owns rewards, ledger, cadence, self-improvement               │
         └───┬────────────────────────────────────────────────────────────┘
   feed     │  provision / supervise         feed (policy: thresholds,
   (corpus) ▼                                prompts, taste, blocks)
     ┌────────────────┐   ┌──────────────────┐   ┌──────────────────────┐
     │ LOOP A         │   │ LOOP B           │   │ LOOP D               │
     │ board-game     │   │ multi-agent      │   │ great-books study    │
     │ history study  │   │ architecture     │   │ (bibliophile)        │
     │ (historian)    │   │ study (archivist)│   └──────┬───────────────┘
     └──────┬─────────┘   └───────┬──────────┘          │ design principles
            │ novelty axes        │ harness/prompt      │ + target-area
            │ + saturation map    │ lessons + evals     │ learnings -> rules
            ▼                     ▼                     ▼ lens + ideator
     ┌───────────────────────────────────────────────────────────────────┐
     │ LOOP C — per-game invention pipeline (one game at a time)          │
     │ invent ▶ rules ▶ playtest + COGS feedback ▶ repair                │
     │                       MAKE ◀▶ INSPECT                             │
     └───────────────────────────────────────────────────────────────────┘
     (B and D also feed the SAME improvement path: every repeated loss or
      repeated book/arch lesson graduates into Eve's own policy.)
```

### Loop A — board-game history study (the *historian*)
Studies the board games of thousands of years (from Senet and Go through
Monopoly to modern Euros) as a **design corpus**, not trivia. Outputs:

- a **mechanics taxonomy** with the *design space it opens* — what each
  mechanic's decision space is, what it costs, who it's for;
- a **saturation map** — which ideas, mechanics, themes are already owned
  (the novelty axes we must avoid);
- canonical examples per mechanic so the inventor can say
  "this is like X plus Y, which no one has combined".

**Feed:** Loop A's corpus is the ground truth for the **novelty gate** in
Loop C (an invented idea must be *new against the corpus*, not just new to
Eve).

### Loop B — multi-agent architecture study (the *archivist*)
Studies the science/engineering of multi-agent systems continuously
(Anthropic's engineering posts — *How we built our multi-agent research
system*, *Effective harnesses for long-running agents*, *Demystifying evals
for AI agents* — plus evals, RL, and agent harnesses). Outputs:

- **architecture lessons** — concrete changes to Eve's own harness, prompts,
  agent roles, and eval methodology;
- **evals notes** — how to grade Eve honestly (task / trial / grader / outcome,
  grade the *outcome* not the transcript, run multiple trials).

**Feed:** Loop B is Eve's *second-order learner*. Its lessons change Eve's own
policy (the thing that is being improved), which is what makes Eve a
self-improving system rather than a fixed pipeline.

### Loop D — the great-books study (the *bibliophile*)
Studies the best writing about tabletop and board gaming — the hobby's
history and culture, its design theory, and its science — as a *library*, not
a shelf. It is Loop A's richer sibling: where Loop A studies *games*, Loop D
studies *writing about games*. The reading list is seeded from the owner's
canonical shelf (`corpus/seed/books.json`): Wallis, du Sautoy, Livingstone,
Engelstein, Koster, Elias/Garfield/Gutschera, and Solis. Outputs:

- **long-lived design principles** — distilled, permanent residue
  (`add_principle`) that outlives any single game or lesson;
- **target-area learnings** — concrete insights tagged to the part of the
  pipeline they change (rules, brief, ideator, playtest, fun), which feed
  Loop C's lenses and can graduate into Eve's own harness the same way
  Loop B's lessons do.

**Cadence:** slow and steady by design — at most one book worked per day
(`study_tick`), one book at a time, and a book is only marked done after its
learnings are recorded. This is deliberately the *slowest* loop; its value is
long-lived, and it shares the quality-over-quantity rule. When the seed shelf
is exhausted the meta-loop replenishes it from a growing canon.

**Feed:** Loop D is Eve's third self-improvement input. Repeat a book learning
twice and it MUST graduate into code (the same ladder as Loop B and Loop C's
empirical loss); its principles become the long-lived standard the rules lens
and the ideator are held to.

### Loop C — the per-game invention pipeline
One game at a time, advanced one stage per meta-loop step. Stages:

1. **Invent** — propose a novel concept against Loop A's corpus; pass the
   novelty gate (must be new, with a stated "like X plus Y" identity).
2. **Rules** — complete rules + bill of pieces + art direction; mechanical
   rules check; engine playtest (thousands of scripted games: does it end,
   does the first seat win, does looking ahead help); LLM-player table.
3. **Brief** — every dimension in mm, every interface between pieces, the
   print plan. (CAD build hooks reuse the org's `cadcode` skill so Eve stays
   a client of proven tooling rather than reimplementing it.)
4. **Build** — per-piece CAD; frozen reference renders; fit checks.
5. **Gate** — deterministic, no-LLM: watertight, one body, bed fit, overhang,
   bill match, interference. (The no-LLM rule is the org's hard lesson: an
   agent that can read its own gate can negotiate with it.)
6. **Panel** — independent lenses, blind to each other: printability, fidelity,
   playability.
7. **Playtest + fun gate** — the load-bearing measurement. **FUN = a player
   asks to play again**, first against real LLM-players, ultimately against
   humans in the org's `PLAYTEST.md` protocol (≥3 groups). No fun-pass, no
   release — this is where Eve refuses to ship a "tuned" but un-fun game.
8. **Artifact + storefront effect** — a game that passed every check becomes a
   content-addressed artifact, then the runtime invokes the storefront adapter
   to create a **draft** (one-click human review flips it live), with its
   rules, renders, and measured COGS; a sale starts
   print-and-ship. The 3D-printable body (fits the real bed, watertight,
   cheap COGS) is a gate, not a hope: the printed game *is* the product.

**Feed:** every playtest failure and COGS outlier is a **lesson** that either
repairs *that game* (bounded repair rounds) or graduates into Eve's harness
(from lowest to highest leverage: prompt → brief → block → gate → planner),
per the org's graduation ladder. Playtest and COGS are the two *measured*
signals that keep Eve honest.

---

## 3. The reward function (self-improvement as RL)

Eve treats each game as an **episode**, each stage-advance as a **step**, and
sending a good game as the **terminal** that ends the episode with reward.
The meta-loop's objective is to **maximize expected discounted return per unit
time** while holding the quality bar fixed — it must get *better at inventing*
over its lifetime, not faster at shipping slop.

### 3.1 Why RL framing, not just "goals"

The org's own failure modes are exactly the RL failure modes:

- a reward that only counts *shipped* games rewards flooding cheap slop →
  reward release of inspected quality only, and hold the bar fixed;
- a reward that can be inflated by the agent writing its own score →
  the ledger is *written by code*, never by a model, and audited;
- rewarding progress forever → an agent that loops forever polishing →
  terminal requires *external* fun evidence.

So Eve's reward is a **shaped, discounted return** with a large terminal term,
a hard external requirement (fun gate) before terminal, and non-negative
penalties for wasted budget so exploration has a cost.

### 3.2 Components

Each component is a **grader** (in the evals sense) over the episode. Values
are per-episode constants; the *actual* numbers in `reward.py` are the live
configuration.

| component | signal | reward | kind |
|---|---|---|---|
| `novelty_pass` | new against Loop A corpus | +1.0 | required before any further reward |
| `rules_pass` | mechanical + lens + engine playtest green | +2.0 | stage reward |
| `fun_pass` | real/per-protocol playtest shows FUN | +4.0 | **highest** — load-bearing |
| `print_pass` | deterministic build gate green | +1.5 | stage reward |
| `cogs_ok` | measured COGS within budget | +1.5 · (budget/measured cap) | shaped, money-aware |
| `ship` | inspected artifact released after all checks (terminal) | +10.0 | terminal |
| `repair_fail` | a repair round exhausted budget | −0.5 | per incident |
| `rework` | a rules rework round | −0.3 | per incident |
| `dead_game` | killed with a stated reason | −2.0 | terminal, cheap kill |

The return for a game is a **discounted sum** of step rewards (`γ ≈ 0.95`),
so a game that reaches terminal with fewer failed rounds scores higher than an
equal game that thrashed. This is the "keep improving until it's perfect"
pressure — but perfect is *measured*, not asserted.

### 3.3 How the reward drives self-improvement

- The **reward ledger** is the single source of truth for how Eve is doing,
  written only by `reward.py` from the queue's own recorded state
  (never from a model's self-report). `audit.py` verifies the ledger against
  the queue, so nobody can inflate a score.
- **`improve.py`** reads the ledger to find the dominant *loss source* — the
  stage whose failures cost the most discounted reward (e.g. rule-gate kills
  at +2.0 stage cost, or fun-gate rejects at +4.0 + repair cost). It then
  proposes a change to the *policy* aimed at that loss: a taste rule, a
  threshold, a block, a prompt change, or a new metric.
- Changes are gated by the org's tiering: **DOC tier** (lessons/notes) is
  applied directly; **CODE tier** (gates, thresholds, prompts, agents) becomes
  a branch + PR a human reads; **FORBIDDEN** (taste, thresholds baseline, the
  ledger, the queue) is never touched by a model.
- **Loop B (archivist)** and **Loop D (bibliophile)** feed the same
  improvement path from *research* instead of from *empirical loss*: their
  lessons propose harness/prompt/evals changes and design-principle tweaks.
  Together these are Eve's three self-improvement inputs — one from evidence
  (Loop C), two from theory (Loop B: how to build the system; Loop D: how
  games have actually worked for thousands of years) — into one policy.

### 3.4 Cadence vs reward

Cadence is a *constraint*, not a reward term. Eve must ship ≥1 game/week and
advance a game by ≥1 stage per day. The reward law **does not** include time;
shipping slow is fine, shipping slop is not. The scheduler enforces cadence;
the reward schedules quality.

---

## 4. Reliability & honesty (the harness)

The org's hard-won rules, applied to Eve:

- **The unit of work is the game, not the turn.** A game lives across many
  steps; it leaves only by shipping or by a stated kill.
- **State is in code, not prompts.** The queue decides what runs next; a model
  cannot read/negotiate its own budget. Claims + leases guard against
  concurrent drivers; a dead driver releases its game.
- **Gates are deterministic and no-LLM.** A model that can read its own gate
  will tune to it. Build/integrity gates are code.
- **Blind panels.** Lenses that rate a game are independent and cannot see
  each other's verdicts, so one agent can't be talked into another's opinion.
- **Grade the outcome, not the transcript.** Release requires external fun
  evidence; "we thought it was fun" is not a measurement.
- **Multiple trials.** Playtest runs many scripted and player-table games, not
  one anecdote.
- **Self-improvement has guardrails.** Improve.py can't edit taste,
  thresholds, its own ledger, or its own scores; CODE-tier changes need a
  human reader. A lesson repeated twice MUST graduate into code.

---

## 5. File map

```
eve/
  DESIGN.md            this document
  README.md            how to run it
  AGENTS.md            rules agents must follow
  eve/                 Eve's Python engine (state/reward logic lives here)
    __init__.py
    meta.py            the 24/7 supervisor: scheduler, provisioning, journal
    queue.py           the game queue: state, claims, leases (unit = game)
    reward.py          the reward function + ledger + audit
    gates.py           deterministic no-LLM gates (novelty, rules, print)
    playtest.py        scripted engine + LLM-player table + fun measurement
    corpus.py          Loop A: board-game history study
    arch.py            Loop B: multi-agent architecture study
    books.py           Loop D: great-books study (bibliophile)
    improve.py         self-improvement session (loss-directed, tiered)
    workshop_bridge.py exact artifact identity and durable runtime bridge
    send.py             compatibility-named storefront draft flow
    launch.py           compatibility aliases only
    journal.py         append-only event narration
    config.py          .env / defaults loading
  .claude/agents/      Claude Code subagent definitions (the roles)
  games/<slug>/        one game per directory
  corpus/seed/         the bundled history + great-books study seeds
  loops/               loop state (arch, books, corpus checkpoints)
  TASTE.md             root creative constitution; exact runtime authority
  tools/               standalone scripts (inspect, send, audit, dashboard)
  bin/                 eve / eve-daemon entry points
  tests/               pytest suite for the deterministic parts
```

The loops deliberately reuse the org's two proven repos where they already
edge forward: CAD build is a client of the `cadcode` skill (vibe-ideas), the
fun protocol is the org's `PLAYTEST.md`, and the Workshop adapter reaches the
current Vibe storefront. The compatibility API is still named `Sender`; Eve does
not reimplement those systems, but orchestrates and improves around them.
