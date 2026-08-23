# Research basis

Alice's architecture is derived from current long-running-agent practice,
agent evaluation research, general game systems, automated playtesting, and the
existing Autonomous Vibe/Shop Door and legacy publication-backend work.

## Long-running and multi-agent systems

- Anthropic's [effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
  use an initializer, incremental sessions, structured requirements, progress
  artifacts, clean handoffs, and end-to-end verification. Alice turns that into
  a durable database, one leased work item per session, and typed state gates.
- Anthropic's [multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
  shows where orchestrator-worker parallelism buys breadth and warns that it is
  expensive. Alice uses independent agents for search, divergent invention,
  player personas, and adversaries—not for deterministic transitions.
- [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
  favors simple composable patterns and evaluator-optimizer loops with clear
  stopping conditions. Alice's deterministic coordinator composes those
  patterns instead of creating a free-form society of agents.
- [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
  separates tasks, trials, graders, traces, and outcomes. Alice stores each
  separately, runs multiple seeded trials, and grades the end artifact.
- [Context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
  documents context degradation and the value of just-in-time retrieval,
  compaction, and subagents. Alice's append-only ledger and archivist provide
  compact cited context without making the transcript the database.
- Anthropic's [long-running app harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps)
  uses planner-generator-evaluator separation, structured handoffs, and
  context resets. Alice adds a skeptical evaluator and policy boundary.
- Anthropic's [C compiler agent teams](https://www.anthropic.com/engineering/building-c-compiler)
  demonstrate task locking, isolated work, deterministic tests, progress
  records, and the importance of strong oracles. Alice uses leases, replayable
  traces, and evidence gates for the same reason.
- Anthropic's [managed agents](https://www.anthropic.com/engineering/managed-agents)
  separate durable sessions, stateless harness logic, and isolated sandboxes.
  Alice uses the event ledger, coordinator, and narrow tool adapters as those
  three layers.

## Games and playtesting

- [Ludii](https://ludii.games/) and the [Digital Ludeme Project](https://ludeme.eu/outputs/)
  provide a computational language and historical/cultural evidence for
  traditional games. They are the seed for Alice's long-horizon mechanism map;
  they are not a claim that the corpus already contains every game ever made.
- [BoardGameGeek XML API2](https://boardgamegeek.com/wiki/page/BGG_XML_API2)
  supplies modern game metadata under rate and usage constraints. Alice should
  store identifiers, mechanics, relationships, and citations, not scrape or
  reproduce copyrighted rulebooks.
- [OpenSpiel](https://github.com/google-deepmind/open_spiel) supplies reference
  games and algorithms for multi-player, general/zero-sum, perfect/imperfect
  information, search, and reinforcement learning. Alice's adapter contract is
  compatible with a game implementation and seeded trace output.
- [Procedural personas for playtesting](https://arxiv.org/abs/1802.06881)
  motivates distinct optimizing and behavior-driven agents rather than one
  average simulated player.
- [Reward hacking in iterative self-refinement](https://arxiv.org/abs/2407.04549)
  shows that a generator and evaluator can increase model scores while human
  preference stagnates or falls. Alice therefore reserves release authority
  for independent evidence and prohibits self-modification of gates.
- [Evolutionary tabletop game design](https://arxiv.org/abs/2310.20008)
  supports mutation/search over game designs, while Alice's held-out human and
  physical gates prevent the search objective from becoming the product.

## Book laboratory

`config/library.json` seeds the user's core shelf and a broader discovery queue.
Alice treats books as sources of testable design claims, not authority or prompt
decoration. Each note binds to an edition and page/location, an adversary finds
counterexamples, and a playtest experiment decides whether a principle belongs
in durable operating knowledge. Access must be owned, licensed, borrowed,
public-domain, author/publisher supplied, or a legally available excerpt; Alice
does not collect full copyrighted text.

## Existing Autonomous implementations

The implementation review covers the live Vibe/Shop Door services, the frozen
Vibe desktop, Leonardo's durable inventor, and the three team experiments:
`peterat617/text-to-3d`, `reinSPQR/vibe-ideas`, and `nohope88/text2cad`.
Concrete contracts and keep/replace decisions live in
[INTEGRATIONS.md](INTEGRATIONS.md).

## Decisions and rejected designs

| Decision | Rejected alternative | Reason |
|---|---|---|
| Restartable leased sessions | One conversation running forever | Context rots; crashes lose truth |
| Deterministic policy owns transitions | Agents vote themselves “done” | Persuasive traces are not evidence |
| Three active candidates max | Generate hundreds daily | Cheap volume hides weak falsification |
| Held-out human outcomes lead reward | Same-model judge score | Documented reward-hacking risk |
| Contextual bandit/evolutionary repair | End-to-end deep RL today | Too few, delayed, changing rewards |
| Multi-agent only for independent work | Agent for every step | Cost and coordination exceed value |
| Real print and receipt | Render/CAD screenshot | The product is physical |
| Shop Door adapter behind policy | Repo-coupled ad-hoc publishing | Sending must be idempotent and auditable |
| Learn ludemes/metadata with provenance | Copy every rulebook | Copyright, source quality, and scale |

## What remains uncertain

- The existing `vibe-ideas` operator is the supported private-draft handoff.
  Public release remains blocked until the live backend advertises and enforces
  Alice's atomic expected-history and packet/hash echo contract.
- Digital simulation quality depends on executable game definitions. Some
  social or dexterity designs will move to humans earlier and carry lower
  confidence.
- “Original” is always a bounded prior-art claim, never proof that no similar
  game existed anywhere over thousands of years.
- Human replay and paid outcomes require real distribution. Fixture runs and
  internal model panels cannot validate them.
