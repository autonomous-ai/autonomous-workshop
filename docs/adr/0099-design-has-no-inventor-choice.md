# ADR 0099: Design asks for no Inventor; the author defaults to Rowan Vale

- **Status:** Accepted on 2026-11-10 (owner decision).
- **Scope:** the owner-facing skills `design-a-toy` and `build-a-toy` only.
  The Workshop runtime's Inventor machinery is unchanged: Spark setup
  selection, the `.codex/agents/` roster, `workshop wish --inventor`, the
  contract's required `inventor` field and every frozen run.
- **Relates to:** ADR 0093 (Contract Proof), ADR 0096 (the Approved Proof
  is the build), ADR 0098 (seeded Make).

## Context

`design-a-toy` asked the owner to choose an Inventor ("There is no default
Inventor") and then judged every trade-off "as the Inventor, against the
Taste". In practice the Inventor no longer shapes the design:

- Concepts come from `brainstorm-concepts` and the owner's picks.
- The Proof builder (`proof-prompt.md`) and the Proof Critic
  (`critic-prompt.md`) never read `TASTE.md`.
- A seeded Make (ADR 0098) certifies the Approved Proof with almost no
  model work.
- What remains is authorship: the contract's `inventor` is passed to
  `workshop wish --inventor`; the run's toy directory is
  `toys/<inventor>-<slug>/`; Release's product facts carry the Inventor's
  Taste `name`; and the Inventor's own Factory account publishes and owns
  the listing (a Listing Update refuses a design whose author is another
  account). Rowan Vale authors almost every recent toy.

## Decision

1. `design-a-toy` no longer asks the owner to choose an Inventor and reads
   no `TASTE.md`. The contract's `inventor` is `rowan-vale` unless the
   owner names another roster Inventor.
2. Trade-offs once decided "against the Taste" are decided by four plain
   criteria, in order: the owner's answers, the chosen concept,
   readability, and printability.
3. `build-a-toy` passes the contract's `inventor` as `--inventor`, as
   before.
4. `brainstorm-trend` is a separate owner-chosen flow. It sets
   `inventor: trend-lab` and lets its personalities decide trade-offs; it
   does not use the removed choice step and keeps its behaviour.

## Consequences

- One owner question fewer per design; no design judgment depends on a
  Taste file the rest of the pipeline ignores.
- The published author is Rowan Vale by default. Publishing under another
  Inventor still needs that Inventor's own Factory credential.
- Inventor Tastes still govern runs that use them: `workshop start`
  daydreams, unseeded native Make and frozen runs.
