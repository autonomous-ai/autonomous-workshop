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
