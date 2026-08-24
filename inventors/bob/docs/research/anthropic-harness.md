# Anthropic harness research — rules for Bob

Sources (fetched 2026-08-22):
- **[LRA]** "Effective harnesses for long-running agents" — https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- **[SDK]** "Building agents with the Claude Agent SDK" — https://claude.com/blog/building-agents-with-the-claude-agent-sdk (308 redirect from anthropic.com/engineering)
- **[CTX]** "Effective context engineering for AI agents" — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- **[TOOLS]** "Writing tools for agents" — https://www.anthropic.com/engineering/writing-tools-for-agents

Context: Bob is a 24/7 autonomous board-game inventor (plain-Python harness, `claude` CLI headless, launchd/cron ticks, ~1 good game per day-to-week, reward-driven iteration, publishes to Panda Social API).

---

## 1. The two-agent split: initializer vs worker [LRA]

The core architecture for work that outlives one context window is **one specialized first session + many incremental sessions**:

- **Initializer agent** (first session only): "The very first agent session uses a specialized prompt that asks the model to set up the initial environment." It creates:
  - an `init.sh` (environment bring-up script),
  - a `claude-progress.txt` (running log for the next session),
  - an initial git commit,
  - a comprehensive requirements file expanding the user prompt.
- **Coding agent** (every later session): "Every subsequent session asks the model to make incremental progress, then leave structured updates." Restricted to **one feature per session**; must leave the repo in a "clean state" suitable for merging to main.

Anthropic's stated key insight: "The key insight here was finding a way for agents to quickly understand the state of work when starting with a fresh context window."

**Bob application:** Each new game gets one initializer tick (create `toys/<slug>/` with GAME.md requirements, checklist JSON, progress log, git commit) and then N iterator ticks, each doing exactly one improvement (e.g., fix one rules ambiguity, rebalance one mechanic) and committing. Never "keep working until done" in one session.

## 2. Fixed startup sequence every session [LRA]

Mandated session-start ritual: (1) `pwd` to verify working dir, (2) read git log + progress files, (3) select the highest-priority incomplete item, (4) run `init.sh`, (5) run a basic end-to-end test **before** starting new work.

**Bob application:** Bob's tick prompt hardcodes this: read `progress.txt` + `git log --oneline -20` + the feature/quality checklist, re-run the rules-consistency check on the current game, *then* pick one item to improve. Catches state broken by a crashed prior tick before building on it.

## 3. Structured checklist the agent may only flip, never edit [LRA]

The harness maintains a JSON feature list (their app run had 200+ features, all initialized as failing) with per-item: category, description, step-by-step verification, `passes` boolean. Two hard rules:
- "We prompt coding agents to edit this file only by changing the status of a `passes` field."
- "It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality."

**Bob application:** Each game gets a `quality.json` (rules completeness, no dead strategies, playtest win-rate spread, component count sane, teachable-in-N-minutes, etc.), generated once by the initializer. Iterator agents can flip `passes: false → true` only after running the verification steps; the harness (Python, not the model) rejects diffs that delete or reword criteria.

## 4. Verification before "done" [LRA][SDK]

- Observed failure: "Claude tended to mark a feature as complete without proper testing." Fix: mandate real end-to-end verification (they used Puppeteer MCP browser automation) and "only mark features as 'passing' after careful testing."
- The SDK's whole loop is **gather context → take action → verify work → repeat**; verification is what makes agents "fundamentally more reliable."
- Feedback quality ladder [SDK]:
  1. **Rules-based feedback is best**: "The best form of feedback is providing clearly defined rules for an output, then explaining which rules failed and why." (Analogy: "it is usually better to generate TypeScript and lint it than it is to generate pure JavaScript.")
  2. **Visual feedback**: screenshots/renders checked against requirements.
  3. **LLM-as-judge**: works for fuzzy criteria but has "heavy latency tradeoffs."

**Bob application:** Bob already plans LLM table playtests (fuzzy judge) — per Anthropic, put a *rules layer under it first*: a Python "game linter" (schema-valid rules doc, every referenced component defined, turn loop terminates, victory condition reachable, no orphan mechanics) that emits *which rule failed and why*. Run linter every tick (cheap), playtest-judge only at gate points (expensive). A game is "publishable" only when the checklist is all-green from actual verification runs, not the model's self-assessment.

## 5. Files as memory; context window is scratch space [SDK][CTX]

- "The folder and file structure of an agent [is] a form of context engineering" — agents `grep`/`tail` to selectively retrieve, never load everything. [SDK]
- **Just-in-time retrieval** [CTX]: keep "lightweight identifiers (file paths, stored queries, web links, etc.)" in context and load data on demand — progressive disclosure over pre-loading.
- **Structured note-taking / agentic memory** [CTX]: "notes persisted to memory outside of the context window. These notes get pulled back into the context window at later times."

**Bob application:** All durable state is files in the repo: reward ledger (JSONL), lessons file, per-game dirs, bandit stats. The tick prompt contains *pointers* ("read `ledger/rewards.jsonl` tail, read `lessons.md`") not contents. Bob's self-improvement loop = the note-taking pattern: lessons written as files, best ones graduated into the prompt/code by a weekly reviewer tick.

## 6. Compaction and context budget [CTX][SDK]

- "Every new token introduced depletes this budget" — "Good context engineering means finding the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome." [CTX]
- Compaction = "taking a conversation nearing the context window limit, summarizing its contents, and reinitiating a new context window with the summary" — preserve architectural decisions, discard redundant tool outputs; "start by maximizing recall, then improve precision." [CTX]
- The Agent SDK "automatically summarizes previous messages when the context limit approaches." [SDK]

**Bob application:** With short launchd ticks, Bob mostly *avoids* compaction rather than performing it: each tick is a fresh context bootstrapped from files (the LRA pattern beats in-session compaction for 24/7 work). Cap each `claude` CLI run (max turns / timeout); if a tick can't finish, it writes its partial state to `progress.txt` and exits clean — the file *is* the compaction.

## 7. Subagents for isolation [CTX][SDK]

- "Subagents use their own isolated context windows, and only send relevant information back to the orchestrator, rather than their full context." [SDK]
- Each sub-agent returns "a condensed, distilled summary of its work (often 1,000-2,000 tokens)." [CTX]

**Bob application:** Playtesters, rules-lawyer critic, and market-scan are separate `claude` invocations returning small structured JSON verdicts (target 1–2K tokens) into files; the designer tick reads the verdict files, never the transcripts.

## 8. System prompt altitude [CTX]

Avoid both extremes — hardcoded brittle if/else logic and vague "make a good game" guidance. Prompts should be "specific enough to guide behavior effectively, yet flexible enough to provide the model with strong heuristics." Structure with Markdown/XML sections. Prefer "a set of diverse, canonical examples" over stuffing edge cases into instructions.

**Bob application:** Bob's designer prompt states the quality bar as heuristics + 2–3 canonical examples of *good* and *rejected* games (with why), not an exhaustive rulebook. Hard constraints (schema, checklist immutability, publish gate) live in Python, not prose.

## 9. Tool design: fewer, consolidated, token-efficient [TOOLS][CTX]

- "More tools don't always lead to better outcomes" — build "a few thoughtful tools targeting specific high-impact workflows," not one tool per API endpoint. Example: one `schedule_event` instead of `list_users` + `list_events` + `create_event`.
- "Tools should be self-contained, robust to error, and extremely clear with respect to their intended use. If humans can't definitively choose between tools, neither can agents." [CTX]
- Namespace by service/resource (`asana_search`, `asana_projects_search`).
- Token efficiency: "pagination, range selection, filtering, and/or truncation with sensible default parameter values"; Claude Code caps tool responses at **25,000 tokens** by default; a `response_format: concise|detailed` enum cut token use to "~⅓ of the tokens with concise responses."
- Responses carry "natural language names, terms, or identifiers" not UUIDs; errors give "specific and actionable improvements, rather than opaque error codes or tracebacks."
- Improve tools by evaluation: realistic multi-call tasks ("potentially dozens" of calls), held-out sets to avoid overfitting.

**Bob application:** Bob's harness exposes few consolidated commands as scripts the agent shells to: `bob_playtest <game> --format concise`, `bob_lint <game>`, `bob_publish <game>` (wrapping the whole Panda Social API dance in one call), `bob_ledger append|tail`. Outputs are truncated summaries by default with `--detailed` opt-in; lint errors say what to fix ("victory condition references 'gold' but no gold component defined"), never stack traces. Game IDs are slugs (`ember-court`), not UUIDs.

## 10. Clean state between sessions — "leave notes for the next session" [LRA]

The exit contract mirrors the entry contract: before a session ends it must **commit with a descriptive message and update the progress file** ("commit and document progress before each session ends"); code left mergeable-to-main clean.

**Bob application:** Bob's Python wrapper enforces this mechanically: after each `claude` run it checks `git status` is clean and `progress.txt` mtime advanced; if not, it runs a tiny "janitor" prompt whose only job is to commit/stash and write the note, so the next tick never inherits a mess. This plus the startup e2e check (rule 2) is the crash-safety story for a 24/7 launchd loop.

---

## The distilled Bob architecture these posts imply

1. **Cron tick → fresh `claude` session → files are the only memory.** No long-lived process holding context.
2. **Per game:** initializer session (requirements + immutable `quality.json` checklist + progress log + git init) → many one-improvement iterator sessions → publish gate.
3. **Every tick:** verify current state first, do one thing, verify it, flip at most one checklist item with evidence, commit, write the note.
4. **Reward function layering:** deterministic Python linter (every tick) → LLM playtest judges as subagents returning ≤2K-token JSON (gate points) → publish only on all-green checklist. Model never self-certifies.
5. **Few consolidated tools/scripts, concise-by-default outputs, actionable errors, slug identifiers.**
6. **Self-improvement = agentic memory:** lessons as files, pulled into ticks by reference, graduated to prompt/code weekly; evaluate tool/prompt changes against held-out past games to avoid overfitting the reward.
