# Daydream

Daydream is the mandatory first creative step of every
`workshop start <inventor>` cycle. It runs before a Wish exists and is not a
product-run stage. `workshop start --idea` reuses a completed, sealed
Daydream; the separate `workshop wish` command remains the entry point for a
person's already-authored Wish.

One Daydream turns current-world evidence, one selected Inventor's immutable
Taste and specialist method, prior work, portfolio history, Design Vault leads,
and factual downstream outcomes into one **creative product thesis**. That
exact thesis becomes immutable Wish intent; later Workshop results teach the
next Dream without pretending to predict build quality before Invent or Make.

Public API: `workshop.daydream`.

## Boundary

Daydream owns:

- why the product should exist now, or which evergreen tension still matters;
- the physical action, response, payoff, and anti-generic signature;
- exact Taste promises and rejection boundaries;
- a source-backed novelty thesis and nearest prior art;
- an observable proof mode with concrete kill criteria; and
- the minimum Workshop route capable of preserving and proving the thesis.

The kill criteria must be jointly satisfiable: the native pre-mortem must be
able to name at least one plausible result that passes all of them.
Mutually exhaustive failure conditions are an impossible contract, not a
stronger proof plan.

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
6. disposition the newest unresolved notebook learning by exact memory hash,
   either repairing it or abandoning that direction; and
7. finalize exactly one schema-v3 `work/IDEA.json` with the run-local standard-
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
Schema-v3 also requires `evidence_boundary`, which states what sources do not
establish—especially demand, benefit, motivation, and repeat use—so the
Taste-specific product translation stays visibly hypothetical rather than
masquerading as a sourced fact.

Before commitment, the same Goal must try to falsify the thesis across nine
independent dimensions:

- Taste fidelity;
- opportunity grounding;
- mechanism or play novelty after theme removal;
- the anti-generic signature;
- proof observability;
- route fit;
- whether the thesis is worth build time; and
- whether the Invent handoff preserves the experience without pre-solving it;
  and
- whether claimed repair/abandonment substantively closes the exact prior
  feedback it cites.

Worth-building includes a reason to return after the first reveal is understood,
such as a continuing decision, discovery, mastery, expression, or changing
causal response. A solved demonstration with cosmetic variation is rejected.

This is an Inventor pre-commit audit, not a self-score or a second native
session. A separate predictive Judge was tested and retired after replay against
real Workshop outcomes rejected both failed builds and published products. It
was an uncalibrated wall, not evidence. Historical schema-v1/v2 records and
their verdicts remain readable, but new schema-v3 theses do not create or gate
on a verdict. Daydream may simplify or change a thesis, select a capable route,
or abandon a direction; it may not demand dimensions, prototypes, coupons,
simulations, or other Invent/Make evidence from itself.

## Knowledge and memory

The workspace keeps four evidence planes visibly distinct:

- Inventor notebook: exact content-hashed structural traces, novelty rejections,
  factual downstream outcomes, and explicit repair-or-abandon learning closures;
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

Every schema-v3 seal binds the exact hashes of the Daydream prompt,
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
    host-state/
      IDEA.json
      INVENTOR.json
      VAULT-BINDING.json [and VAULT.json when available]
      PROVENANCE.json
```

Daydream and host-state directories are private and symlink-resistant. Agent
work is accepted only when the finalizer marker names the exact file hash and
the host re-parses the same schema independently. Novelty lint is deliberately
a conservative lexical floor plus structural portfolio projection, not a claim
that Python can judge global originality; semantic novelty remains native
Inventor work backed by source citations.

## Verification

Contract/finalizer parity tests share adversarial corpora. Workspace tests cover
Inventor/Vault materialization, live-search proof, exact provenance, route and
time failures, novelty, private state, historical verdict parsing, and their
non-authority for new Dreams. The focused end-to-end learning loop executes
materialized finalizers across an actual downstream failure and a repaired
second Dream, proving that exact evidence reaches the next Goal and that the
sealed thesis crosses into Wish unchanged.
