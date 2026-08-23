# Evaluation, reward, and self-improvement

## Release is lexicographic

A weighted score can hide a fatal flaw, so Alice evaluates in this order:

1. Evidence integrity: unique trials, valid provenance, immutable artifacts,
   no self-asserted human or production result.
2. Safety, IP, rules completeness, termination, and critical exploit gates.
3. Blind human, real print/yield, economics, and exact-packet gates.
4. Minimum score for every quality dimension.
5. Aggregate quality and confidence thresholds.

Failure at an earlier tier stops evaluation. A high fun score cannot average
away an unsafe component or a rule system that does not terminate.

## Quality vector

All dimensions are normalized to `[0, 1]` and retain their raw evidence:

| Dimension | Weight | Representative evidence |
|---|---:|---|
| Fun and replay | 0.30 | spontaneous replay choice, completion, later replay |
| Clarity and teach | 0.15 | blind setup/teach success, hints, disputes |
| Depth and agency | 0.15 | meaningful choices, decision entropy, learning curve |
| Balance | 0.10 | seat/faction win rates, comeback paths, no dominant strategy |
| Novelty | 0.10 | nearest-neighbor distance plus human articulation of difference |
| Physical delight | 0.10 | legibility, handling, print yield, assembly, durability |
| Economics/market | 0.10 | landed margin, conversion, returns, support burden |

The aggregate is a weighted geometric mean, then reduced by confidence and
explicit penalties. The geometric mean makes a weak dimension expensive rather
than easy to hide. Publication additionally requires every dimension to clear
its floor.

## Primary outcomes

The highest-value early metric is the fraction of blind groups who choose to
play again without being asked to please the designer. Later, paid conversion,
repeat play, refund/return rate, support burden, review language, print yield,
and gross margin supersede launch-time model scores.

Alice starts with a small but real market prior: purchases have occurred across
two distinct 3D-printable chess-set designs, including the San Francisco set.
The available fact does not establish unit count. It raises the prior for the
print-on-demand category, while its small sample and chess concentration mean it
does not unlock a new game's market gate.

Surrogates such as LLM critique, simulated balance, novelty embeddings, and
rule-lint scores are useful because they are fast. They receive lower evidence
classes and can never satisfy external gates. This directly addresses iterative
self-refinement reward hacking, where model scores can improve without human
preference improving.

## Contextual reinforcement learning

At one product per week, end-to-end deep reinforcement learning would be mostly
fiction: rewards are sparse, delayed, and non-stationary. Alice instead uses an
auditable contextual Thompson-sampling policy.

Context includes mechanism family, player count, duration, interaction type,
current stage, failed dimension, and audience. Actions are explicit mutations:
`simplify_rules`, `rebalance_resources`, `increase_player_agency`,
`reduce_downtime`, `clarify_teach`, `change_setup`,
`strengthen_social_tension`, `mechanism_pivot`, and `kill_candidate`.

For a chosen mutation, success means the preregistered held-out measure improved
without regressing a hard gate or another quality floor. A Beta posterior per
context/action updates only from verified held-out or external evidence. State
is serializable and every decision records seed, posterior, action, expectation,
and result. A fixed exploration/control allocation prevents the policy from
optimizing only what it already believes.

## Self-improving harness

Harness changes use the same scientific discipline:

- freeze a representative suite of passed, failed, killed, and published games;
- state the expected improvement and failure risk before running;
- compare current and candidate harness over multiple isolated trials;
- grade end states and evidence quality, not persuasive traces;
- include deterministic graders, independent model graders, and humans where
  judgment is the product;
- measure cost and latency as well as quality;
- activate only a reviewed policy hash; retain instant rollback.

The runtime can recommend a change. It cannot change the reward function,
external-evidence definition, held-out suite, or live publication policy.

## Publication minimums (default policy)

- three independent blind groups, two games per group;
- no designer hints required for setup or basic turn flow;
- spontaneous replay evidence above the configured floor;
- zero critical rules, safety, IP, or dominant-strategy failures;
- all dimensions at least `0.65`, aggregate at least `0.72`, confidence at
  least `0.70`;
- real print yield at least `95%` for the validated build, with the production
  receipt bound to the same print profile, canonical material specification,
  per-set BOM, and packing recipe that will be sold and fulfilled;
- gross margin at least `50%` on evidenced landed cost;
- the exact packet reviewed is the packet hashed and published.

Thresholds are policy, not truth. They should be changed only from accumulated
outcomes and shadow evals, never to rescue the current candidate.
