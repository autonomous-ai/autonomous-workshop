# Product quality and token economics

Autonomous Workshop's North Star is an order-of-magnitude better toy at one
tenth the creation cost. The two requirements are conjunctive: a cheaper dull
toy and an extravagant beautiful toy both miss the target.

## Cost is a vector, not a made-up total

Codex reports input, cached input, cache-write input, output, and reasoning
output for each native turn. Workshop records those values separately by stage
and derives uncached input. It never adds token categories or infers dollars,
because model pricing and the relative price of cached input can change.

A two-turn Codex CLI probe on 2026-08-30 confirmed the semantics:

| Turn | Input | Cached input | Uncached input | Output |
|---|---:|---:|---:|---:|
| New session | 14,589 | 11,008 | 3,581 | 5 |
| Same session resumed | 17,780 | 14,080 | 3,700 | 6 |

The resumed turn reports its whole effective context again, mostly as cached
input. Therefore gross input is useful capacity telemetry but not a proxy for
fresh context. Compare like-for-like runs on all reported categories and turn
coverage. A 0.1x cost claim requires no category to hide an increase behind a
combined total.

## Quality is comparative evidence, not a model score

Host gates prove contracts, exact bytes, CAD properties, and publication; they
do not prove delight. Compare a challenger against a named baseline without
revealing which workflow produced which toy. Review the exact product renders,
interaction/rules, printable files, and manual on these dimensions:

- Wish fit and emotional promise;
- novelty and an unmistakable anti-generic signature;
- strength of the physical play or transformation moment;
- coherence of form, mechanism, components, and constraints;
- product-render legibility and desirability;
- first-owner clarity and delight of the in-box manual;
- deterministic CAD/printability evidence and truthful limitations.

An order-of-magnitude quality claim means a clear experience-category leap, not
ten times a self-assigned number: the challenger is strongly preferred on the
signature experience and most other dimensions, loses none of the deterministic
gates, and has no new unsupported claim. Keep the raw comparison and reviewer
notes beside the benchmark; do not turn them into lifecycle gate authority.

## Optimization order

1. Remove retries, timeouts, and repeated passed work.
2. Reduce tool calls and tool-output context with bounded inspection and one
   quick-iteration/final-verification funnel.
3. Use the roster once, choose one Inventor, and spend depth on one signature
   interaction instead of broad candidate fan-out.
4. Carry sealed summaries, manifests, and renders forward instead of resurveying
   stable source at every stage.
5. Reuse deterministic CAD, render, and manual layout primitives so native
   reasoning chooses the product rather than repeatedly rebuilding plumbing.
6. Only after comparable benchmarks, tune model or reasoning effort. A cheaper
   runtime configuration is not a win if blind product preference falls.
