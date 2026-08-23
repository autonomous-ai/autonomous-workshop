# Anthropic's Multi-Agent Research System — Transferable Lessons for Bob

Source: https://www.anthropic.com/engineering/multi-agent-research-system (Anthropic engineering, June 2025).
Extracted 2026-08-22 for Bob, the 24/7 autonomous board-game inventor (plain-Python harness, `claude` CLI headless workers, publishes to Panda Social API).

All quotes below are verbatim from the article. Each section ends with a **Bob** note: how to apply it in our system.

---

## 1. Headline result and what actually drives it

- "A multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by 90.2% on our internal research eval."
- On BrowseComp, three factors "explained 95% of the performance variance." **"Token usage by itself explains 80% of the variance"**, with number of tool calls and model choice as the other two factors.

The mechanism: multi-agent works because it *spends more tokens in parallel contexts* on a task. It's a way to scale token budget past one context window, not magic coordination.

**Bob:** Quality per game will track total tokens spent on that game. Bob's biggest quality lever is not cleverer prompts — it's spending more tool calls/tokens on the games that deserve it (deeper playtests, more rules revisions, more adversarial review). Budget tokens per game explicitly in the reward ledger, and expect quality ∝ spend. Use a stronger model for the orchestrator/critic and cheaper models for parallel grunt work (playtest simulations, rules linting), mirroring Opus-lead + Sonnet-workers.

## 2. Orchestrator-worker pattern

- "an orchestrator-worker pattern, where a lead agent coordinates the process while delegating to specialized subagents that operate in parallel."
- The lead agent "analyzes [the query], develops a strategy, and spawns subagents to explore different aspects simultaneously."
- Lead agent saves "its plan to Memory to persist the context, since if the context window exceeds 200,000 tokens it will be truncated."

**Bob:** One lead "Inventor" process per game owns the plan (theme, mechanics hypothesis, target audience) and writes it to disk *first* (e.g. `games/<slug>/PLAN.md`). Workers — mechanic researcher, rules drafter, LLM playtesters, art/component briefer, marketplace-fit checker — are spawned `claude -p` calls that read the plan file, do one job, and write one artifact back. The lead never regenerates the plan from memory; it re-reads it from disk each tick (this is also what makes launchd ticks resumable).

## 3. Effort scaling — the explicit heuristics

The article's exact numbers (embedded in the lead-agent prompt as rules of thumb):

- "Simple fact-finding requires just 1 agent with 3-10 tool calls"
- "Direct comparisons might need 2-4 subagents with 10-15 calls each"
- "Complex research might use more than 10 subagents with clearly divided responsibilities"

Without these rules, agents over-invest in trivial queries — a confirmed failure mode ("agents continuing when they already had sufficient results").

**Bob:** Write an explicit effort table into the orchestrator prompt and enforce it in the Python harness (hard caps, not just prompt suggestions):
- Idea triage / trend scan: 1 agent, ≤10 tool calls.
- Mechanic exploration for a candidate: 2–4 subagents, 10–15 calls each (one per design direction from the bandit).
- Full game development to publishable: 10+ subagent runs across drafting, 3–5 independent playtest tables, rules-lawyer pass, blind rules test.
The harness kills any worker exceeding its call/token budget. Effort tier is chosen by the reward function's current estimate of the game's promise — don't spend "complex" budget on an idea the judge scored 0.4.

## 4. Prompt engineering for delegation

- Each subagent task needs: "an objective, an output format, guidance on the tools and sources to use, and clear task boundaries."
- Vague delegation fails concretely: instructions like "'research the semiconductor shortage'" were "vague enough that subagents misinterpreted the task or performed the exact same searches." Without detail, "agents duplicate work, leave gaps, or fail to find necessary information."
- "Small changes to the lead agent can unpredictably change how subagents behave." Understand the *interaction patterns*, not just each prompt.
- Embed expert heuristics, not scripts: prompts encode skilled-researcher strategies — "decomposing difficult questions into smaller tasks, carefully evaluating the quality of sources, adjusting search approaches based on new information, and recognizing when to focus on depth versus breadth."
- Start wide, then narrow: "prompting agents to start with short, broad queries, evaluate what's available, then progressively narrow focus" (counteracts the default of "overly long, specific queries that return few results").
- Extended thinking "can serve as a controllable scratchpad"; subagents use "interleaved thinking after tool results to evaluate quality, identify gaps, and refine their next query."
- "Think like your agents": run the actual prompts/tools in simulation and watch step-by-step. Observed failure modes: "agents continuing when they already had sufficient results, using overly verbose search queries, or selecting incorrect tools."

**Bob:** Every worker spawn is a structured brief written by the harness, never a bare sentence: `{objective, output_format (exact file path + schema), tools allowed, boundaries (what NOT to touch), effort budget}`. For parallel playtest tables, boundaries are what stop three tables testing the same thing — assign each table a distinct question ("does the endgame drag?", "is the catch-up mechanic exploitable?", "first-play comprehension"). Encode board-game-designer heuristics in the drafter prompt the way they encoded researcher heuristics (e.g. kill-your-darlings passes, count decisions-per-turn, check for dominant strategies, breadth-first mechanic search before committing). Turn on extended thinking for the design and critique steps. And keep a `bob replay` dev mode that runs one worker with its real prompt so we can watch it fail step-by-step.

## 5. Token economics

- "agents typically use about 4× more tokens than chat interactions, and multi-agent systems use about 15× more tokens than chats."
- Multi-agent is justified only for "tasks where the value of the task is high enough to pay for the increased performance."
- Poor fits: "domains that require all agents to share the same context or involve many dependencies between agents"; coding has "fewer truly parallelizable tasks than research."

**Bob:** Budget ~15x chat-level tokens per finished game and put it in the cost ledger (text2cad already has this pattern). At ~1 game/day-to-week this is fine; the discipline is *not* multi-agenting the steps that don't parallelize. Rules-text editing is a coding-like, high-dependency task — one agent, sequential. What parallelizes cleanly: independent playtest tables, competitor/BGG-style research, theme exploration branches. Split Bob's pipeline along that line.

## 6. Evaluation strategy

- **Start tiny:** "We started with a set of about 20 queries representing real usage patterns. Testing these queries often allowed us to clearly see the impact of changes." Don't wait for a big eval harness — at the start effect sizes are huge and n=20 shows them.
- **LLM-as-judge rubric** (their exact criteria): factual accuracy ("do claims match sources?"), citation accuracy, completeness ("are all requested aspects covered?"), source quality, tool efficiency. "a single LLM call with a single prompt outputting scores from 0.0-1.0 and a pass-fail grade was the most consistent" — better than multiple judges or per-criterion calls.
- **End-state, not process:** "Instead of judging whether the agent followed a specific process, evaluate whether it achieved the correct final state." Agents find "alternative paths to the same goal."
- **Humans still needed:** "People testing agents find edge cases that evals miss. These include hallucinated answers on unusual queries, system failures, or subtle source selection biases" (human testers caught an SEO-bias problem the evals missed).

**Bob:** This *is* the reward-function spec:
- One judge, one LLM call, one prompt, scores 0.0–1.0 per criterion + overall pass/fail. Bob's rubric analog: rules completeness & unambiguity, novelty vs. known games, decision depth, first-play accessibility, component/production feasibility, theme-mechanic fit.
- Judge the *end state* — the finished rulebook + playtest transcripts — not whether Bob followed the pipeline in order.
- Keep a fixed set of ~20 benchmark design briefs; rerun them whenever a prompt or the judge changes, so self-improvement is measured, not vibed.
- Dee's Telegram gate (from reinSPQR) is the human eval layer — it will catch the "SEO bias" equivalents: samey themes, derivative mechanics, judge reward-hacking. Feed every human override back into the lessons ledger.

## 7. Reliability for long-running stateful agents

- "Agents can run for long periods of time, maintaining state across many tool calls. This means we need to durably execute code and handle errors along the way."
- Errors compound: "one step failing can cause agents to explore entirely different trajectories, leading to unpredictable outcomes." "Minor changes cascade" into large behavioral changes.
- **Resume, don't restart:** build systems that "resume from where the agent was when the errors occurred" — restarting from scratch is expensive and frustrating at 15x token cost.
- **Checkpoints:** persist critical state (the plan) externally before context limits hit.
- **Let the model handle mess:** "letting the agent know when a tool is failing and letting it adapt works surprisingly well" — combine deterministic safeguards (retry, checkpoints) with model adaptability.
- **Rainbow deploys:** "gradually shifting traffic from old to new versions while keeping both running simultaneously" so a deploy never kills an in-flight agent.
- **Sync vs async:** their lead agent runs subagents synchronously — this "simplifies coordination, but creates bottlenecks." Async "adds challenges in result coordination, state consistency, and error propagation" — they deliberately hadn't paid that cost yet.
- **Tracing:** "Adding full production tracing let us diagnose why agents failed and fix issues systematically" — monitor decision patterns, since outputs are non-deterministic.

**Bob:** This maps almost 1:1 to a launchd-ticked Python harness:
- Every game is a directory with a state file (queue state machine, as in reinSPQR); every tick reads state from disk and advances one step. A crashed tick loses at most one step — resume-by-construction.
- Pass tool errors *into* the next claude call ("the Panda publish returned 502; adapt") instead of hard-failing the pipeline.
- Rainbow-deploy equivalent: never edit prompts/harness under an in-flight game. Version prompts (`prompts/v12/`); a game pins the version it started with; new games pick up the new version. Bandit stats stay comparable per version.
- Stay synchronous per game (one step per tick, workers within a step can be parallel subprocesses). Don't build async coordination Bob doesn't need — Anthropic shipped without it.
- Log every claude call: prompt hash, tokens, cost, output path, judge scores → JSONL trace per game. This is the debugging substrate *and* the RL ledger.

## 8. Tools and artifacts

- "Bad tool descriptions can send agents down completely wrong paths, so each tool needs a distinct purpose and a clear description."
- Tool-testing agent: "when given a flawed MCP tool, it attempts to use the tool and then rewrites the tool description to avoid failures. By testing the tool dozens of times, this agent found key nuances and bugs" → "a 40% decrease in task completion time for future agents using the new description."
- Self-improving prompts: "the Claude 4 models can be excellent prompt engineers. When given a prompt and a failure mode, they are able to diagnose why the agent is failing and suggest improvements."
- Filesystem artifacts: "Rather than requiring subagents to communicate everything through the lead agent, implement artifact systems where specialized agents can create outputs that persist independently" — subagents write outputs directly and pass back "lightweight references"; this "prevents information loss during multi-stage processing and reduces token overhead."
- Context management: agents "summarize completed work phases and store essential information in external memory before proceeding"; when limits approach, "spawn fresh subagents with clean contexts while maintaining continuity through careful handoffs."
- Parallelism payoff: parallel subagents + parallel tool calls within agents "cut research time by up to 90% for complex queries."

**Bob:** Workers exchange files, not conversation: rulebook.md, playtest transcripts, judge JSON all land in the game directory; the orchestrator passes paths. This is exactly the stdlib-Python-friendly design. For self-improvement, copy the tool-tester pattern directly: Bob's weekly improvement pass (text2cad pattern) feeds `{prompt, failure trace, judge scores}` to a claude call that proposes a prompt diff — validated against the 20-brief benchmark before it graduates to `prompts/vN+1/`. Lessons graduate to code the same way: a recurring judge complaint becomes a deterministic lint in the harness.

## 9. What NOT to copy

- Their domain (research) is read-only; Bob mutates state (publishes to a live marketplace). The appendix warns state-mutating agents need end-state evals precisely because process can't be replayed safely — gate irreversible steps (publish) behind the human check, per org guardrails.
- Don't build async orchestration, agent-to-agent chat, or dynamic mid-flight re-steering. Anthropic explicitly deferred all of these and still got the 90.2% win.
- Don't multi-agent low-value steps. The 15x cost only pays where parallel exploration adds real lift.

---

## One-page design digest for Bob

| Article lesson | Bob mechanism |
|---|---|
| Token spend explains 80% of performance variance | Per-game token budget in reward ledger; more spend on promising games |
| Orchestrator-worker, parallel subagents | Lead Inventor per game; parallel playtest/research workers via `claude -p` |
| Effort heuristics: 1 agent/3–10 calls → 10+ agents | Effort tiers enforced by harness caps, chosen by judge score |
| Delegation brief: objective, format, tools, boundaries | Structured JSON brief per worker; distinct question per playtest table |
| 15x token cost; needs high task value | Quality-over-quantity cadence (1 game/day-to-week) justifies spend |
| ~20-query eval set, single-call 0–1 LLM judge, end-state eval | 20 fixed design briefs; one-call rubric judge = the reward function |
| Humans catch what evals miss | Telegram owner gate; overrides feed lessons ledger |
| Resume from failure, checkpoints, durable state | Per-game state machine on disk; tick advances one step |
| Rainbow deploys | Versioned prompts pinned per in-flight game |
| Tell the agent the tool is failing | Error text passed into next claude call |
| Full tracing | JSONL trace per game: prompts, tokens, cost, scores |
| Tool-tester + Claude-as-prompt-engineer (40% faster) | Weekly self-improve pass proposes prompt diffs, gated on benchmark |
| Filesystem artifacts, lightweight references | Game directory is the message bus |
| Sync execution is fine | One step per tick; no async orchestration in v1 |
