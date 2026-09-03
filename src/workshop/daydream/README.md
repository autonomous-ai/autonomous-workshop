# Daydream

Daydream is the mandatory first creative step of every
`workshop start <inventor>` cycle. It runs before a Wish exists and is not a
product-run stage. `workshop start --idea` reuses a completed, Judge-accepted
Daydream; the separate `workshop wish` command remains the entry point for a
person's already-authored Wish.

One Daydream turns current-world evidence, one selected Inventor's immutable
Taste and specialist method, prior work, portfolio history, Design Vault leads,
and factual downstream outcomes into one **creative product thesis**. An
independent Judge must accept that exact thesis before it can become immutable
Wish intent.

Public API: `workshop.daydream`.

## Boundary

Daydream owns:

- why the product should exist now, or which evergreen tension still matters;
- the physical action, response, payoff, and anti-generic signature;
- exact Taste promises and rejection boundaries;
- a source-backed novelty thesis and nearest prior art;
- an observable proof mode with concrete kill criteria; and
- the minimum Workshop route capable of preserving and proving the thesis.

Invent owns exact mechanisms, dimensions, materials, components, construction,
tolerances, compatibility, and research-backed physical facts. Spark Make keeps
its existing compound responsibility to seal those facts before building.
Daydream may offer mechanism or Vault leads, but they are advisory and cannot
become engineering truth here.

The host does not generate, fan out, rank, or semantically score candidates.
That creative work belongs to the native Manager and the selected Inventor.
Python owns bounded contracts, exact identities, deterministic gates, private
state, and the Wish handoff.

## Native Goals

The Inventor-side session gets one Goal named `Daydream`. It must:

1. read the exact `TASTE.md`, selected custom-agent binding and declared skill
   trees;
2. read `PRIOR-WORK.md`, cross-Inventor `PORTFOLIO.md`, `NOTEBOOK.md`, and the
   advisory Vault snapshot;
3. use live web search to inspect current news, behavior, practices, and needs;
4. diverge across materially different interaction families;
5. theme-strip and falsify serious candidates against Taste, prior art, proof,
   route, and portfolio repetition; and
6. finalize exactly one schema-v2 `work/IDEA.json` with the run-local standard-
   library finalizer.

The runtime must report an observed web-search event. Source URLs alone do not
prove that a current scan happened. Each thesis also carries two to six unique
world-signal URLs, an exact scan time, and the explicit translation:

```text
current signal -> durable human tension -> Taste-specific physical opportunity
```

The portable schema rejects malformed sources and publication times after the
scan. The host requires every scan and prior-art observation time to equal the
turn's exact UTC time, validates exact Taste excerpts, and rejects a
`route_floor` above the selected route. Hotness never acts as a quality score;
an evergreen thesis is legal only after the mandatory scan.

The independent Judge runs in a second short native session over the sealed
idea, exact Taste, and selected route. Its schema-v2 verdict separately tests:

- Taste fidelity;
- opportunity grounding;
- mechanism or play novelty after theme removal;
- the anti-generic signature;
- proof observability;
- route fit;
- whether the thesis is worth build time; and
- whether the Invent handoff preserves the experience without pre-solving it.

`build` is legal only when all eight booleans are true and every identity
matches. Confidence is a prediction, never evidence. `dream-again` retains
failed checks, risks, and actionable advice for the next Dream, but a new
schema-v2 rejected thesis cannot become Wish intent, including through
`--idea`. Historical schema-v1 records retain their frozen behavior.

## Knowledge and memory

The workspace keeps four evidence planes visibly distinct:

- Inventor notebook: exact structural traces, novelty rejections, and Judge
  predictions/advice;
- Workshop portfolio: a bounded projection of every other Inventor's notebook,
  used to catch renamed or re-themed repeats;
- Design Vault: shared causal craft evidence, read-only and advisory; and
- downstream outcomes: allowlisted host-observed status, needs, exact artifact
  lineage, Release, and Factory identities.

Outcome records are appended for Daydream-originated runs on every route and on
resume. They preserve the chain from Daydream and provenance hashes through
Invented, Made, Playtested, Release, product artifact, and Factory design/slug
when those facts exist. Model prose, session messages, private URLs, and
credentials are not copied. The next native Dream interprets these facts;
Python does not turn them into a reward score or rewrite Taste.

## Exact provenance and state

Every schema-v2 seal binds the exact hashes of the Daydream prompt,
constitutions, Taste, selected Inventor and skill bundle, Vault binding and
snapshot, prior work, portfolio, notebook/outcomes view, finalizer, portable
schema, world scan, prior art, and Manager spec. The Wish context carries the
Daydream, idea, provenance, Inventor, and route identities unchanged.

```text
$WORKSHOP_HOME/daydreams/<inventor-id>/
  NOTEBOOK.jsonl
  OUTCOMES.jsonl
  LOOP.json
  STOP
  <daydream-id>/
    workspace/
      AGENTS.md
      TASTE.md
      VAULT.md [and VAULT.json when available]
      PRIOR-WORK.md
      PORTFOLIO.md
      NOTEBOOK.md
      .codex/agents/<inventor-id>.toml
      .agents/skills/<declared-skill>/...
      finalize_daydream.py
      daydream_schema.py
      work/IDEA.json
      agent-outcome.json
    judge-workspace/
      IDEA.json
      TASTE.md
      ROUTE.md
      AGENTS.md
      work/VERDICT.json
      agent-outcome.json
    host-state/
      IDEA.json or REJECTED.json
      VERDICT.json
      INVENTOR.json
      VAULT-BINDING.json [and VAULT.json when available]
      PROVENANCE.json
```

Daydream and host-state directories are private and symlink-resistant. Agent
work is accepted only when the finalizer marker names the exact file hash and
the host re-parses the same schema independently. Novelty lint is deliberately
a conservative lexical floor plus structural portfolio projection, not a claim
that Python can judge global originality; semantic novelty remains native Judge
work backed by source citations.

## Verification

Contract/finalizer parity tests share adversarial corpora. Workspace tests cover
Inventor/Vault materialization, live-search proof, exact provenance, route and
time failures, novelty, private state, Judge identity, and historical parsing.
The focused end-to-end learning loop executes materialized finalizers across a
Judge rejection and a repaired second Dream, proving that exact advice reaches
the next Goal and that only the accepted thesis crosses into Wish.
