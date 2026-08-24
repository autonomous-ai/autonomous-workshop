# lessons — the fast learning layer

One entry per lesson, evidence-tied, appended by the postmortem step of any
loop. Header contract (from text2cad, kept verbatim because it worked):

`- [cause · phase · date · cost · status]` where status is
`OPEN | OPEN→belongs in <phase> | GRADUATED→<code that now catches it>`.

**The graduation rule: a lesson that repeats MUST graduate to code — a queue
check, a gate test, a prompt-template constraint. Never advisory text twice.**
Each graduation converts a repeated $10–25 lesson into a $0 deterministic
check. The weekly improve session tallies OPEN lessons by cause; that tally is
the engineering backlog.

Cap: ~30 active lessons. When the file grows past that, the improve session
must graduate or delete, not append. An unbounded lore file is noise
(Reflexion's buffer works because it is short).

Seed lessons (inherited from the sibling inventors' receipts, already
graduated into Bob's design — kept here so the improver knows they are load-bearing):

- [sequencing · pipeline · 2026-08-17 · 6 CAD repair rounds · GRADUATED→queue gate order] Rules must be machine-played and LLM-tabled before any CAD spend (Armillary).
- [staleness · verdicts · 2026-08-17 · 1 dead-game verdict · GRADUATED→idea_sha in every verdict artifact] A verdict must be provably bound to the version it judged.
- [selection · discover · 2026-08-12 · 3 generic products · GRADUATED→blind lanes + no-LLM winner pick] A model that scores its own shortlist justifies the pick it already made.
- [quota · runner · 2026-08-13 · 1 silent dead cycle · GRADUATED→QuotaExhausted + quota_wait] A retry against an exhausted cap burns wall-clock and produces nothing.
- [caps · runner · 2026-08-17 · $49 starved phases · GRADUATED→Starved vs AgentError] num_turns at max is starvation, not failure; never retry at the same cap.

## 2026-08-23 — the first production night (six games, one draft shipped)

- [ceilings · every generator stage · 2026-08-23 · ~6 parked games · GRADUATED→per-stage max_minutes/max_turns] Chat-sized walls killed the rules writer, brief writer, engine writer and CAD builder. A ceiling that binds is the real constraint, not a safety limit.
- [artifacts-over-replies · rules/brief/build · 2026-08-23 · 2 dead games · GRADUATED→cwd tools + file validation] A rulebook is not a chat reply. Heavy stages write files as they go; a killed agent's partial work survives and the loop judges the FILES.
- [exit-codes · built · 2026-08-23 · 79 files discarded · GRADUATED→invent._handle_built crash fallthrough] A killed builder is not a lost build. The deterministic gate judges a build, never the agent's exit code.
- [quota · runner · 2026-08-23 · 3 healthy games parked · GRADUATED→agents.py quota regex "session limit"] The usage-limit window returns is_error with subtype=success. If the regex does not know the wording, healthy games burn crash counters.
- [instrument-vs-game · simulated · 2026-08-23 · 2 false kills · GRADUATED→simmetrics INVERSION_TOLERANCE + beam] A gate that fails the instrument instead of the game is decoration. 2-ply score minimax cannot see information value in a deduction game; the hard gate is skill-exists + no-inversion.
- [measurement-budget · tabled · 2026-08-23 · 2 runs, 0 votes · GRADUATED→tablerun verdict_reserve] The verdict IS the product; turns are only how we reach a position to judge. Reserve the verdict money before the turn loop can spend it.
- [table-cost · tabled · 2026-08-23 · $50 of $123 · GRADUATED→MAX_TABLE_TURNS 60] A table samples an experience; it does not play a tournament. Duration questions belong to the sim's 1,000 games, not to a $5 table.
- [unargued-booleans · build lens · 2026-08-23 · physical_hook zeroed on a game built around a felt click · GRADUATED→bob-build-lens rubric] A judge boolean with no reasoning is a defective verdict. Define the question exactly and demand the sentence before the answer.
- [state-honesty · published · 2026-08-23 · queue claimed a listing that did not exist, twice · GRADUATED→_handle_published requires platform design id + public status] A slug is not a listing. The queue is the one artifact that must never lie.
- [scheduling · published · 2026-08-23 · two games starved · GRADUATED→park a draft awaiting a human] A game that is done until a person acts must leave the schedulable set, or it wins the closest-to-done race forever.
- [transport · publish/novelty · 2026-08-23 · first real import died at the wire · GRADUATED→curl fallback on both network seams] urllib dies on this machine's intercepted TLS. The house lesson held for the third time.
- [wire-contracts · publish · 2026-08-23 · 3 rejected calls · GRADUATED→publish.py + page-writer prompt] Live API truths beat docs: category must be a real slug (toys), story blocks use `lead` not `label`, and the PUT wants {"story_blocks": [...]} not a bare array.
