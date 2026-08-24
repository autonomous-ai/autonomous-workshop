# text2cad lessons for Bob

Source: `github.com/nohope88/text2cad`, cloned at `/tmp/bob-research-text2cad` (2026-08-22, HEAD `fb9bc30`). This is the in-house daily autonomous inventor loop (trend → 3D-printable product, one cycle/day on the "panda" box). Bob (board-game inventor) has the same shape: discover → spec → build → deterministic gate → LLM panel → repair → publish-as-draft → self-improve. Almost every hard-won mechanism here transfers.

**The real economics: 18 cycles, $430.00 total (CYCLES.md rows sum exactly to $430.00), 1 SHIPPED (eclipse-v2, $16.59). 4 FAILED ($248.50 = 58% of all spend), 9 INCOMPLETE, 3 GATE PASS / NO PANEL, 1 GATE PASS / UNJUDGED.** The one shipped product cost $16.59 directly but ~$430 fully loaded. The money was lost to harness bugs and bad selection, not to bad geometry — that is the headline for Bob.

---

## a) Reuse-verbatim list

These are files/mechanisms Bob should copy nearly unchanged (swap CAD nouns for game nouns):

1. **`autoloop.py` (202 lines) — the whole daily-cycle wrapper.** Idempotency marker file per day (`out/.cycles/<date>`), `.heartbeat` file written first thing, pre-flight source-health check, single subprocess with wall-clock ceiling, log streamed to file (not `capture_output` — they got burned: "capture_output buffered EVERYTHING … for up to 8 hours there was no live log at all"), tail-of-log Telegram summary, lessons-tier auto-commit. Copy structure verbatim.
2. **`watchdog.sh` (18 lines) — dead-man alert.** Separate cron, checks `.heartbeat` mtime > 28h (100800s), Telegram DM. Comment cites the origin: "silent-channel death must alarm — 4-night scraper blackout 6/5–6/8, admindash $13 silent burn 8/9–8/10."
3. **`postmortem.py` — deterministic per-cycle accounting.** "No LLM call, no API key, so it always runs — including on a cycle that died because the key was exhausted." One `analyze()` function feeds both the markdown report and the CYCLES.md ledger row ("One function so a cycle can never be summarised two different ways"). CAUSE_RULES pattern→cause table, first match wins. Copy whole file; rewrite CAUSE_RULES for game failure modes.
4. **`CYCLES.md` ledger format** — `| product | result | cost | parts | repairs | cause |`, cause vocabulary shared with lessons.md so "a cause that keeps showing up here is where the pipeline is actually losing money."
5. **`lessons.md` header contract** — every entry `- [cause · phase · run date · cost · status]` with status `OPEN | OPEN→belongs in <phase> | GRADUATED→<code that now catches it>`. Plus the graduation rule verbatim: "A lesson that repeats must GRADUATE to code: a golden block, a gate linter check, or a brief-template constraint … never advisory text twice." `postmortem.py --lessons` tallies open lessons by cause — the RL signal for what to engineer next.
6. **`improve.py` (119 lines) — weekly self-improvement with two authority tiers.** Doc tier (`lessons.md`, `discover_lessons.md`, `BLOCKS.md`, `README.md`) auto-merges to main; **any** code change goes to a branch + `gh pr create` for human review. Hard rule: the deterministic testbench must print ALL PASS or everything is reverted (`git checkout -- .`). Copy verbatim; Bob's testbench = rules-engine self-tests / simulated-game smoke tests.
7. **The blind propose/judge panel + `pick_winner()`** (`text2cad` lines ~625–958). 3 propose lanes in parallel (ThreadPoolExecutor), each blind to the others ("do not hedge toward the middle"); 3 blind judges who must *search* for prior art — "`EXISTS <slug> yes <url>` only with a real listing you actually opened … a URL is the only thing that counts as a find"; one judge's find kills a candidate; then **`pick_winner()` is plain Python over medians, no LLM**: "a model that scores its own shortlist writes a self-critique that justifies the pick it already made — that is exactly how the pen holder won on 2026-08-12 — and a median over independent judges cannot be argued with." One re-propose round with the dead candidates as a blacklist, then "a day with no product beats a day spent building something a shopper can already buy."
8. **`taste.md` structure** — slop-ban list (14 named default shapes, "instant reject, however good the theme is"), a moves vocabulary, and intensity dials in env (`NOVELTY=8, MECHANISM=7, ORNAMENT=4, PARTS=6-14, CRAFT=6`). The themed-skin test transfers word-for-word to games: "If the winning idea's one-line description would still make sense after swapping the theme for any other theme, it is a themed skin — reject it." Also the scoping rule: taste.md is for DISCOVER/BRIEF only; lessons.md is injected into BUILD/REPAIR only — DISCOVER reading build lessons caused three straight generic products (see failure analysis).
9. **`run_phase()` telemetry envelope** — every `claude -p` call logs `{model, wall_s, num_turns, max_turns, subtype, cost_usd, cache_write, cache_read, out_tokens, is_error}` to `run.json`, persisted after every phase under a lock; repeated phase names get `#2, #3` suffixes instead of overwriting ("run.json reported $102.25 for a cycle that actually spent $116.67 — every figure the pipeline published about itself was 12% low"). Quota death (`usage limit|limit reached|rate limit` in an error) is `SystemExit(4)` + Telegram, never a retry.
10. **Per-phase model routing** — `model_for(phase)` reads `{PHASE}_MODEL` from `.env`, default `claude-sonnet-5`. Their mix: Opus 5 for discover/brief/build/arbitration/repair2/repair3/lens-fidelity ("spec/code errors cascade downstream"; fidelity "on Sonnet chronically exhausted 35 turns"), Sonnet 5 for draft/other lenses/repair1 ("cheap, re-gated / rescored anyway").
11. **`ship_decision()`** — ship only when `gate_pass AND no unjudged lens AND no failing lens`. "An absent lens verdict is not a passing one" (one-way-newsreel shipped with an empty panel). Panel results seeded to `"FAIL did not run"` *before* any lens executes.
12. **Publish-as-draft** (`publish.py`) — imports with `status=draft`; "The human confirmation IS the draft→public flip … this script never publishes anything publicly." Held-back runs are announced: "gate PASSED but NOT published — the panel did not clear it … publish by hand … if you disagree" — a silent skip "looks exactly like a publish that failed."
13. **Trend-seed citation rule** — every candidate must end with `Seed: <digest path> — "<exact trend item>"`; "A product whose origin cannot be traced back to a specific thing people were paying attention to is a product nobody asked for."
14. **`rejected_slugs()`** — human REJECT lines in `discover_lessons.md` are a harder kill than a marketplace find ("2026-08-13 the panel re-picked one-twist-coffee-doser after Tam had rejected it and --auto built it anyway").

## b) Failure analysis — why 4 FAILED and 9 INCOMPLETE

Ledger (CYCLES.md): FAILED = arc-coil-blaster-prop ($76.26; assembly, discover, fidelity), draft-stack-dock ($45.04; harness, 5 repairs), scram-rod-drop-desk-switch ($102.25; budget, fidelity), terminal-cursor-pen-holder ($24.95; discover, harness). INCOMPLETE = 9 rows, 6 of them $0.00 (variant/scratch runs that never reached the gate: eao-scrap-rifle-{color,pp}, finger-mirror-manipulator-{pp,trellis}, funhaus-canopy-bookend, reef-chameleon) plus finger-mirror-manipulator ($19.09), one-twist-coffee-doser ($9.91, human-REJECTED mid-pipeline), shadow-moire-contour-bench ($56.00, fidelity — milestone likeness 2/10, aborted).

By named cause (from code comments, lessons.md and commit messages):

**1. Harness bugs, not product bugs — the biggest bucket.**
- *3h ceiling killed healthy cycles*: "08-14 and 08-15 both finished the build right at the 3h kill, so publish never ran and the whole spend was lost" (autoloop.py). Later: "A ceiling sized for truncated phases now kills healthy ones, and a kill loses the entire spend" → 8h.
- *Turn-cap starvation misread as failure*: "Measured across 15 runs: DRAFT ran out of turns in 7 of them, the lenses in 3, BUILD in 2 … $49 went to phases that were starved rather than wrong" — and the pipeline "paid for a retry at the SAME cap." On 08-17 "every repair in the scram cycle ended at 71/70 turns … a cap that binds 3 times out of 3 is not a safety limit, it is the real constraint on the work."
- *64k output-token cap*: BUILD "died with 'Claude's response exceeded the 64000 output token maximum' … four ~15-minute attempts … producing nothing and burning $8.85" (fix: `CLAUDE_CODE_MAX_OUTPUT_TOKENS=128000`).
- *OOM took the whole box*: "2026-08-13 the kernel OOM-killed a 15.4GB boolean chain and took the whole cycle (and nearly the 15GB box) with it"; again 08-16 "the fidelity lens loaded all 14 part STLs into one trimesh process, hit 14.8GB and the kernel OOM-killed the WHOLE pipeline" (fix: `RLIMIT_AS` per phase, `PHASE_MEM_MB=12288`).
- *Crashed lens read as a verdict*: `lens:fidelity FAIL no output` recurred 3× on draft-stack-dock, "cost 3 repair tiers across 3 recurrences," each time geometry was fine — GRADUATED to a one-retry in `run_panel()`. Corollary shipped a product: one-way-newsreel published with gate PASS and an empty panel.
- *Quota death was silent*: "the 08-13 cycle died this way SILENTLY" — every retry burned wall-clock against an exhausted weekly cap.
- *Wrong likeness anchor*: --auto's fake GO made concept.png byte-identical to the render; lens honestly answered 0/10 ("no independent approved concept image"), milestone read 0 as "unsalvageable" and "killed a $29.49 run that had never been judged at all."

**2. Discover picked the wrong thing (the most expensive waste class).**
- Postmortem's own advice: "Money spent past DISCOVER on a candidate nobody wants is the most expensive kind of waste in this pipeline."
- *Lesson leakage*: a geometry lesson ("stranger must decode it in 3 seconds") was read by DISCOVER as an *idea filter* — "it scored down every abstract candidate and is how three straight cycles shipped a pen holder, a phone holder and a dock." Fix: hard scoping of corpora per phase.
- *Self-scoring*: single agent proposing + scoring its own shortlist "justifies the pick it already made" (pen holder, 08-12). Fix: blind lanes, blind judges, no-LLM `pick_winner()`.
- *Wrong objective*: "Optimizing novelty picked precision instruments the build stage can't deliver (shadow-moire-contour-bench: $56, likeness 2/10, no product)" → objective became desire+buildable+craft with novelty only as a floor (`NOVELTY_MIN=5, BUILDABLE_MIN=7, CRAFT=6`).
- *Ignoring the human's NO*: re-picked a rejected product and built it anyway → `rejected_slugs()` hard kill.

**3. Fidelity — the build drifting from the approved concept.**
- arc-coil-blaster-prop "spent its whole budget on detail and only learned at the END-of-cycle panel that the grip, guard and stock were off-concept — 17 hours and the repair budget gone before the first likeness verdict." Fix: mid-build likeness milestone at half budget, `MILESTONE_ABORT_BELOW=4` — "silhouette failures now cost half a build, not a whole cycle."

**4. Budget/spec conflicts the repair loop couldn't hear.**
- scram ($102.25): repair2 "swept ~21,000 candidates, proved the brief had ZERO legal (pivot_y, blade_r) pairs," but `is_stuck()` only listened for the literal word "STUCK" — "the pipeline did not hear it, spent repair3 (~50 min, $12.94) on the proven-impossible constraint." Fix: evidence regex (`0 legal pairs`, `geometrically impossible`, `over-constrained`…).
- Repeated class: "A repair session … cannot close a gap that traces back to two explicit, mutually-conflicting brief numbers — that must be caught when the brief is written" (eclipse-v2, scram). Hence the arbitration phase: repair budget exhausted → an agent decides spec-conflict vs defect, writes `brief_proposed.md`; the human applies it (`--amend`).

**The 9 INCOMPLETEs** are mostly the harness maturing: killed/aborted runs, scratch variants and re-runs of the same idea under a fixed pipeline (three finger-mirror variants, two eao-scrap-rifle variants). The pattern for Bob: early cycles die to infrastructure, and a cycle that dies before its gate must be labeled INCOMPLETE, not FAILED — "scratch dirs and killed runs would otherwise read as product failures" (postmortem.py).

## c) The ops pattern — cron + watchdog + Telegram, exact mechanics

```
15 0 * * *   autoloop.py    # daily cycle (UTC; 9 min after the 00:06 x-scrape lands)
0  1 * * 0   improve.py     # weekly self-improvement, Sunday
0  4 * * *   watchdog.sh    # dead-man check, daily
```

- **Heartbeat**: `autoloop.py` writes `.heartbeat` (today's date) as its *first* act, before the idempotency check — so a run that skips still proves cron fired. `watchdog.sh` (separate cron, separate process) alarms if the file is missing or `now - mtime > 100800s` (28h = 24h cadence + 4h grace). Both alert paths are Telegram DMs via raw `curl` to `api.telegram.org/bot<tok>/sendMessage`.
- **Idempotency**: marker file `out/.cycles/<ISO-date>`; re-runs same day are no-ops. Marker written even on timeout, so a killed cycle doesn't retry all day.
- **Pre-flight source health**: not "is the socket up" — the old check passed a 403 as reachable ("an expired token, or a scraper that quietly stopped, would both have been discovered only after the propose lanes had already been paid for"). The fix authenticates and fetches the actual digest for today *or yesterday*; missing both days = "the scraper … has stopped" → Telegram + skip the cycle. **Bob rule: verify the exact artifact the first phase will consume, with the real credentials, before spending anything.**
- **One process, one ceiling**: the entire cycle is one `subprocess.run(..., timeout=8*3600)` with stdout streamed to `logs/cycle-<date>.log`. On `TimeoutExpired`: append `--- KILLED ---` to the log, write the marker, Telegram "STUCK … no publish ran."
- **Result parsing from the log tail**: `== DONE <slug>: gate=… ship=…` and `total LLM cost $…` lines; Telegram gets `[OK]`/`[NEEDS ATTENTION]` + last 6 log lines (max 2500 chars).
- **Telegram touchpoints** (all fire-and-forget, ~30s curl timeout): source-dead skip, cycle stuck/killed, quota exhausted, daily summary, discover winner (~7 min in, "does not wait on renders"), draft hero photo FYI, per-repair escalations, ARBITRATION GO/NO with exact copy-paste commands (`GO: ./text2cad <slug> --amend / NO: rm out/<slug>/brief_proposed.md`), gate-passed-but-held notice, postmortem summary. The human is a *reviewer with one-line commands*, never a blocking gate in --auto.
- **Git as the memory bus**: autoloop auto-commits only `lessons.md`/`discover_lessons.md` with message `loop: lessons update <date> (<slug>, $<cost>)`; improve.py owns code via PR. `out/` is gitignored — "this table [CYCLES.md] is the part that travels."

## d) Cost-control mechanics worth copying

1. **Cost ledger per phase, from the CLI's own numbers**: `total_cost_usd` from `claude -p --output-format json`, persisted to `run.json` after *every* phase (crash-safe), never overwritten (`#n` suffixing). Postmortem's first section is literally "Where the money went," sorted by $.
2. **Rework accounting**: `burned = Σ cost of (is_error ∪ retries ∪ repairs)` reported as a % of total — e.g. renders "$X (N%) went to rework."
3. **Starved vs crashed, mechanically distinguished**: record `max_turns` and the CLI's `subtype` ("error_max_turns" vs "error_during_execution"); "num_turns >= max_turns … is simply false: a healthy judge came back 19/10 because num_turns counts messages." Opposite fixes: "Raise the cap or cut the task down; retrying at the same budget just buys the same wall" vs "transient agent failure … retry."
4. **Tiered repair budgets**: `TIER_BUDGET = {"broken": 2, "functional": 3, "cosmetic": 2}` — worst failure present picks the tier; one bonus repair per tier only if `scores_improving()` (every still-failing lens strictly rose last round); then arbitration, then ESCALATE to the human. Bounded worst-case spend per cycle.
5. **Half-budget milestone check + kill switch**: cheap mid-build likeness lens; abort the whole run below 4/10 ("shadow-moire scored 2/10 at milestone, then burned $8 build2 + panel anyway"). For Bob: a mid-design playtest of the half-built ruleset, with an abort threshold.
6. **Escalation ladder on models**: Sonnet for repair1, Opus for repair2/3 — pay for intelligence only after the cheap model failed.
7. **Cache-aware fan-out**: parallel siblings share the prompt-prefix cache — "judge-1 cost $4.37 while judge-2/3 cost $0.83/$0.94 for identical work." Run panels in parallel on purpose; log `cache_write/cache_read` so it doesn't look like a broken agent.
8. **No-LLM everything that can be no-LLM**: gate.py (mesh checks + real OrcaSlicer slice + lint of graduated lessons + `fit_checks.py`), pick_winner, postmortem, ledger. Deterministic code costs $0 per run and "always runs — including on a cycle that died because the key was exhausted." Bob's equivalents: rules-schema validator, component-count/complexity linter, deterministic simulator harness, winner-pick from judge medians.
9. **Quota-death circuit breaker**: regex on the error blob (`usage limit|limit reached|rate limit`) → Telegram + `SystemExit(4)`. "Once the weekly cap hits, each 'retry' burns wall-clock and produces nothing."
10. **Memory rlimits per phase** (`PHASE_MEM_MB`, `RLIMIT_AS` in `preexec_fn`) so one runaway phase dies recoverably instead of OOM-killing the box.
11. **Fail before you pay**: trend-source health check before propose; `stale_stl` gate check (refuse to score artifacts older than their source — cost "1 repair tier (2nd recurrence)" before graduating); `concept_ref_independent()` before asking an unanswerable question.
12. **Graduation as compounding cost reduction**: the loop's core RL move. Examples that went prose→code: bridge-span check (`GRADUATED→gate.bridge_span`), stale-STL refusal (`GRADUATED→gate.stale_stl`), blanket-fillet lint (`GRADUATED→gate lint`), lens crash retry (`GRADUATED→run_panel-retry`), camera-not-geometry rule (`GRADUATED→DRAFT-prompt`). Each graduation converts a repeated $10–25 lesson into a $0 deterministic check.

## What Bob should do differently (not in text2cad)

- text2cad has **no bandit / explicit reward function** — its "RL" is lessons-graduation plus one objective change made by hand. Bob's reward ledger and bandit over design directions are additive; keep the cause-tagged ledger as the bandit's evidence store.
- text2cad ships at most one product/day and got 1/18 out the door; Bob's "one good game per day-to-week" bar means the milestone-abort and discover-kill mechanics matter even more — kill early, kill cheap.
- The exists-gate ("a judge cannot find it for sale, URL required") maps to Bob as BoardGameGeek/marketplace search with a URL as kill evidence.
