# Anthropic on Effective Agents & Agent Evals — applied to Bob

Research report for Bob, the autonomous board-game inventor. Sources:

- **[A]** "Building effective agents" — Anthropic Engineering, Dec 19 2024. https://www.anthropic.com/engineering/building-effective-agents
- **[B]** "Demystifying evals for AI agents" — Anthropic Engineering, Jan 09 2026. https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

All quotes verbatim from the source pages (fetched 2026-08-22). Bob-specific application notes are marked **→ Bob**.

---

## 1. Workflows vs. agents — the decision rule

Definitions [A]:

> "**Workflows** are systems where LLMs and tools are orchestrated through predefined code paths."
> "**Agents** are systems where LLMs dynamically direct their own processes and tool usage, maintaining control over how they accomplish tasks."

Decision rule [A]:

> "Workflows offer predictability and consistency for well-defined tasks, whereas agents are the better option when flexibility and model-driven decision-making are needed at scale."

And the meta-rule: find the simplest solution possible; only add complexity when the latency/cost tradeoff demonstrably buys task performance.

**→ Bob:** Bob's *outer loop* (tick → pick work item → run stage → grade → ledger → publish) is a well-defined, repeating process. That is a **workflow** — hard-code it in Python (queue state machine, exactly like reinSPQR/vibe-ideas already does). The *inside of a stage* ("invent a mechanic," "rewrite rules to fix ambiguity X," "playtest as 3 players") is open-ended — that's where a `claude` CLI agent call belongs. Don't let the model drive the pipeline; let it drive the creativity inside a pipeline the code drives.

---

## 2. The composable patterns and where each fits Bob

### 2.1 Augmented LLM (building block)
The base unit: "an LLM enhanced with augmentations such as retrieval, tools, and memory" that can be "generating their own search queries, selecting appropriate tools, and determining what information to retain." [A]
**→ Bob:** each `claude -p` invocation should get: the game's current state file, the lessons file (memory), and file tools. Nothing more.

### 2.2 Prompt chaining
"ideal for situations where the task can be easily and cleanly decomposed into fixed subtasks. The main goal is to trade off latency for higher accuracy, by making each LLM call an easier task." [A] Add programmatic **gates** between steps (their example: check an outline meets criteria before writing the full document).
**→ Bob:** the invention pipeline is a chain: concept → mechanics spec → full rulebook → components list → playtest script. Put a *code* gate between each (schema check on the spec, rules-completeness lint before playtesting). vibe-ideas' rules gate is exactly this pattern; keep it.

### 2.3 Routing
"works well for complex tasks where there are distinct categories that are better handled separately, and where classification can be handled accurately." Includes model routing: "easy questions to Haiku and hard questions to Sonnet." [A]
**→ Bob:** route by work type: cheap model for rules-linting, summarizing playtests, and ledger entries; frontier model for invention and revision. Also route revision work by failure category (ambiguity fix vs. balance fix vs. fun problem) to different specialized prompts.

### 2.4 Parallelization — sectioning and voting
"effective when the divided subtasks can be parallelized for speed, or when multiple perspectives or attempts are needed for higher confidence results." Voting example given: "Reviewing a piece of code for vulnerabilities, where several different prompts review and flag the code." [A]
**→ Bob:**
- *Sectioning:* run the 3–5 simulated playtest tables in parallel (different player counts / player personas).
- *Voting:* the publish gate should be a vote of several independent judge calls with different rubric emphases (clarity, balance, novelty, fun), not one judge. Anthropic explicitly lists "using parallelization for automating evals" as a use case.

### 2.5 Orchestrator-workers
"well-suited for complex tasks where you can't predict the subtasks needed... subtasks aren't pre-defined, but determined by the orchestrator based on the specific input." [A]
**→ Bob:** use *sparingly* — only in the revision stage, where the fix plan depends on what the playtests found. An orchestrator call reads the playtest reports, emits a concrete fix list, and workers execute each fix. Everywhere else, prefer the fixed chain (simpler, cheaper, debuggable).

### 2.6 Evaluator-optimizer
"particularly effective when we have clear evaluation criteria, and when iterative refinement provides measurable value." The fit test: "LLM responses can be demonstrably improved when a human articulates their feedback" and "the LLM can provide such feedback." [A]
**→ Bob:** this IS Bob's core inner loop — generate game → grade against reward function → revise → regrade, until threshold or max iterations. Board-game critique passes the fit test: a human can articulate "the second-player advantage is too strong," and so can a model. Design the reward function as *the evaluator half of this pattern*, not as an afterthought.

### 2.7 Agent-loop hygiene (for the autonomous parts)
[A]: agents must "gain 'ground truth' from the environment at each step (such as tool call results or code execution) to assess its progress"; "Agents can then pause for human feedback at checkpoints or when encountering blockers"; "it's also common to include stopping conditions (such as a maximum number of iterations) to maintain control"; autonomy brings "higher costs, and the potential for compounding errors" — so "extensive testing in sandboxed environments, along with the appropriate guardrails."
**→ Bob:** ground truth for a game = *executed* playtests (scripted table simulation with logged states), not the model's opinion of its own rules. Hard caps: max revision iterations per game (e.g. 8), max daily token/$ budget (text2cad's cost ledger pattern), Telegram gate to Dee before anything publishes publicly under the Autonomous name (vibe-ideas owner gates — keep them; publishing is outward-facing, which per the org playbook is a Dee decision).

### 2.8 The three core principles [A]
1. "Maintain simplicity in agent design."
2. "Prioritize transparency by explicitly showing planning steps."
3. "Carefully craft your agent-computer interface (ACI) through thorough tool documentation and testing."

**→ Bob:** (2) means every stage writes a human-readable plan/report file into the game's directory before acting — Dee can audit any game's history by reading its folder.

---

## 3. Agent-computer interface (ACI) design

Key quotes [A]:

- "Give the model enough tokens to 'think' before it writes itself into a corner."
- "Keep the format close to what the model has seen naturally occurring in text on the internet."
- "Make sure there's no formatting 'overhead' such as having to keep an accurate count of thousands of lines of code, or string-escaping any code it writes."
- "Put yourself in the model's shoes. Is it obvious how to use this tool, based on the description and parameters?" — include "example usage, edge cases, input format requirements, and clear boundaries from other tools."
- "Think of this as writing a great docstring for a junior developer on your team."
- Poka-yoke: "change the arguments so that it is harder to make mistakes." Their SWE-bench example: requiring **absolute filepaths** eliminated relative-path mistakes after directory changes.
- "plan to invest just as much effort in creating good agent-computer interfaces (ACI)" as goes into HCI.

**→ Bob:**
- Represent games as **markdown rulebooks + a small structured YAML/JSON spec**, not a bespoke DSL — markdown rules text is the format models have seen most (rulebooks, BGG threads).
- Every harness-provided script/tool Bob's agents call (playtest runner, publish, grade) takes absolute paths and validates inputs loudly (poka-yoke).
- Write real docstrings/`--help` for each tool; test them by running sample invocations and reading what the model does wrong, then fix the tool, not just the prompt.

---

## 4. Eval methodology (from "Demystifying evals for AI agents")

### 4.1 Vocabulary [B]
An eval is "a test for an AI system: give an AI an input, then apply grading logic to its output to measure success." Terms: **task** ("a single test with defined inputs and success criteria"), **trial** ("each attempt at a task"), **grader** ("logic that scores some aspect of the agent's performance"), **transcript** ("the complete record of a trial, including outputs, tool calls, reasoning, intermediate results"), **outcome** ("the final state in the environment at the end of the trial"), **eval harness** (runs tasks concurrently, records, grades, aggregates).

### 4.2 Grade end states, not paths [B]
> "There is a common instinct to check that agents followed very specific steps like a sequence of tool calls in the right order. We've found this approach too rigid and results in overly brittle tests."
> "...it's often better to grade what the agent produced, not the path it took."

Agents "regularly find valid approaches that eval designers didn't anticipate." Their example: a flight-booking agent may *say* "Your flight has been booked," "but the outcome is whether a reservation exists in the environment's SQL database."

**→ Bob:** the reward function grades the *artifact* — the rulebook + spec + playtest logs — never how the agent got there. "Did Bob call the brainstorm tool first?" is not a metric. "Does a legal, terminating, decision-rich game exist in the game directory?" is.

### 4.3 How to evaluate open-ended generative work [B]
For research (i.e. open-ended) agents: "research quality can only be judged relative to the task" and "experts may disagree on whether a synthesis is comprehensive." The prescription:

> "Combine grader types. Groundedness checks verify that claims are supported by retrieved sources, coverage checks define key facts a good answer must include, and source quality checks confirm the consulted sources are authoritative."

And: "LLM-based rubrics should be frequently calibrated against expert human judgment."

**→ Bob:** a game's reward = layered graders, cheapest first:
1. **Deterministic checks** (code): spec schema valid; component list consistent with rules; playtest sim terminates within N turns; no rules reference undefined terms; win condition reachable in logs.
2. **Coverage checks** (code + cheap LLM): rulebook answers a fixed checklist (setup, turn order, all edge cases the sim hit, endgame, tiebreaks).
3. **LLM rubric judges** (per-dimension, isolated — see 4.4): clarity, balance evidence from playtest logs, novelty vs. a corpus of known mechanics, fun proxies (meaningful decisions/turn, comeback potential, downtime).
4. **Human spot-check** (Dee, occasionally) to recalibrate layer 3.

### 4.4 LLM-as-judge: rubrics and failure modes [B]
Model-based graders (rubric scoring, natural-language assertions) are "flexible" and "scalable" but "non-deterministic" and need "calibration with human graders for accuracy." Key operational advice:

- **One dimension per judge:** "Create clear, structured rubrics to grade each dimension of a task, and then grade each dimension with an isolated LLM-as-judge rather than using one to grade all dimensions."
- **Hallucination escape hatch:** "Give the LLM a way out, like providing an instruction to return 'Unknown'."
- **Calibration:** "LLM-as-judge graders should be closely calibrated with human experts to gain confidence that there is little divergence between the human grading and model grading." "Model grading often takes careful iteration to validate accuracy."
- **Anti-cheating:** "Make your graders resistant to bypasses or hacks. The agent shouldn't be able to easily 'cheat' the eval."

Example task config from the post (support agent):
```yaml
graders:
  - type: llm_rubric
    rubric: prompts/support_quality.md
    assertions:
      - "Agent showed empathy for customer's frustration"
```

**→ Bob failure modes to design against:**
- **Reward hacking**: Bob's generator will learn what its judge rewards. Mitigations: judges never see the generator's self-assessment; judge prompts live outside the generator's context; rotate judge phrasing; deterministic layers can't be flattered; novelty judge compares against an external corpus, not Bob's claims.
- **Judge drift/leniency**: keep a frozen set of anchor games (known-good and known-bad, including a few published classics rewritten in Bob's format and a few deliberately broken games) and re-score them whenever the judge prompt or model changes — score movement on anchors = judge change, not game change.
- **Single-judge omniscience**: per §2.4, grade dimensions with isolated judges and vote.

### 4.5 pass@k vs pass^k, and non-determinism [B]
- pass@k: "the likelihood that an agent gets at least one correct solution in k attempts."
- pass^k: "the probability that all k trials succeed."
- "At k=1, they're identical... By k=10, they tell opposite stories: pass@k approaches 100% while pass^k falls to 0%."
- "If your agent has a 75% per-trial success rate and you run 3 trials, the probability of passing all three is (0.75)³ ≈ 42%."
- Rule: "Pass@k for tools where one success matters, pass^k for agents where consistency is essential."
- "a task that passed on one eval run might fail on the next" — run multiple trials; single-shot numbers are noise.

**→ Bob:** Bob is a **pass@k business**: it can generate k candidate concepts/revisions and only the best must clear the bar — one great game per day-to-week, discards are free. So: sample wide at the concept stage (k=5–10 cheap concepts, grade, keep 1–2), and *never* judge a pipeline change on a single game. Bob's *harness reliability* (playtest runner, publish step) is pass^k — it must work every tick — so eval those components for consistency separately.

### 4.6 Small-N evals while iterating [B]
> "In reality, 20-50 simple tasks drawn from real failures is a great start."
> "In early agent development, each change to the system often has a clear, noticeable impact, and this large effect size means small sample sizes suffice. More mature agents may need larger, more difficult evals to detect smaller effects, but it's best to take the 80/20 approach in the beginning."
> "Evals get harder to build the longer you wait. Early on, product requirements naturally translate into test cases. Wait too long and you're reverse-engineering success criteria from a live system."
> "Begin with the manual checks you run during development—the behaviors you verify before each release and common tasks end users try."

**→ Bob:** before Bob runs autonomously, build a starter eval set of ~20–30 tasks: e.g. "given this deliberately ambiguous rulebook, does the rules gate catch it," "given this degenerate game (first player always wins), do the playtest+balance judges catch it," "given this plagiarized-mechanic game, does the novelty judge catch it." Every real failure Bob hits in production becomes a new eval task (the vibe-ideas/text2cad lesson-file habit, but graduated into executable tests).

### 4.7 Human-in-the-loop calibration [B]
- "Systematic human studies" are the "gold-standard quality judgements from multiple human raters"; they "handle subjective or ambiguous tasks" and "provide signal for improving model-based graders."
- "Once the system is robust, it's sufficient to use human review only occasionally."

**→ Bob:** Dee's Telegram gate is not just a safety gate — it is **judge-training data**. Every approve/reject (with a one-line reason) is logged next to the judges' scores; weekly self-improvement compares Dee's verdicts to judge verdicts, and when they diverge, the *rubric* gets edited (a lesson that graduates to code/prompt). Over time the gate can move from "approve every publish" to "spot-check 1 in N," per the quote above.

### 4.8 Anthropic's 8-step eval roadmap [B]
1. Start early. 2. Convert manual checks to tasks. 3. Write unambiguous tasks with reference solutions. 4. Build balanced problem sets ("If you only test whether the agent searches when it should, you might end up with an agent that searches for almost everything. Try to avoid class-imbalanced evals."). 5. Build a robust harness with a stable, isolated environment ("Unnecessary shared state between runs... can cause correlated failures"; Claude once gained an "unfair advantage" by reading git history left over from previous trials). 6. Design graders thoughtfully (partial credit: "A support agent that correctly identifies the problem and verifies the customer but fails to process a refund is meaningfully better than one that fails immediately."). 7. **Check transcripts**: "You won't know if your graders are working well unless you read the transcripts and grades from many trials." 8. Monitor for saturation (SWE-bench Verified went "from 40% to >80%" in a year; when everything passes, the eval stops informing).

Other pitfalls worth quoting:
- "With frontier models, a 0% pass rate across many trials... is most often a signal of a broken task, not an incapable agent."
- "Everything the grader checks should be clear from the task description; agents shouldn't fail due to ambiguous specs."
- Brittle numeric grading: CORE-Bench initially scored Opus 4.5 at 42% because rigid grading "penalized '96.12' when expecting '96.124991…'".

**→ Bob:**
- Balanced sets: include *should-reject* games in the eval set, or the gate learns to approve everything (class imbalance).
- Isolation: each game gets its own directory; playtest sims run in fresh state; never let a trial read another game's artifacts (the git-history contamination lesson).
- Partial credit: the reward ledger records dimension scores, not just pass/fail — a game that's fun but unclear is a *revise*, not a *kill*, and the bandit over design directions needs graded signal, not binary.
- Saturation watch: when Bob's average first-draft score approaches the publish threshold, raise the threshold or add harder rubric dimensions — otherwise the self-improvement loop has no gradient.

---

## 5. Condensed design consequences for Bob

1. **Code drives the pipeline; models drive creativity.** Outer loop = Python workflow/state machine. Agent autonomy only inside stages. [A]
2. **The reward function is an evaluator-optimizer loop** with layered graders: deterministic → coverage → per-dimension LLM judges (voting) → occasional human. [A][B]
3. **Grade the game, not the trajectory.** Outcome grading on artifacts + executed playtest logs as ground truth. [B]
4. **pass@k at the concept stage** (generate many, keep best); **pass^k for harness plumbing**; multiple trials before believing any pipeline-change result. [B]
5. **Start with 20–50 eval tasks now**, drawn from manual checks and seeded failure cases (broken/degenerate/plagiarized games); grow the set from real failures. [B]
6. **Dee's gate doubles as judge calibration** — log approve/reject + reason, diff against judge scores weekly, edit rubrics on divergence, reduce human frequency as agreement rises. [B]
7. **Judges are attack surface**: isolate per-dimension judges, give "Unknown" outs, frozen anchor games to detect drift, external corpus for novelty, and make deterministic layers un-charm-able. [B]
8. **ACI care**: markdown rulebooks + small structured spec; absolute paths; docstring-quality tool help; watch transcripts of how agents misuse tools and fix the tools. [A]
9. **Read transcripts.** A weekly ritual: sample N trial transcripts and grades; this is the only way to know the graders work. [B]
10. **Stopping conditions and budgets everywhere**: max revisions per game, daily cost cap (text2cad ledger pattern), watchdog on stuck states. [A]
