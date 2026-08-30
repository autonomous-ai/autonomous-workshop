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

## Named production baseline

Moonchase Fox is the first complete schema-v3 Spark baseline:

| Measure | Whole run | Make | Release |
|---|---:|---:|---:|
| Gross input | 24,616,026 | 22,343,631 | 2,272,395 |
| Cached input | 24,101,632 | 22,059,008 | 2,042,624 |
| Uncached input | 514,394 | 284,623 | 229,771 |
| Output | 88,501 | 68,149 | 20,352 |
| Elapsed | 49m 28s | 39m 21s native work | 9m 5s native work |

The public snapshot is `toys/pico-press-moonchase-fox/`. It passed full-tier
CAD and publication gates; Release's visual review also found and repaired real
manual collisions. The next comparable Spark run must beat that artifact on
quality while using no more than 2,461,602 gross input tokens to establish the
0.1x economics target. Cached, uncached, and output counts remain visible so a
nominal win cannot hide a regression in another category.

The first low-reasoning challenger, Starling Gate, established that runtime
tuning alone is insufficient:

| Measure | Whole run | Make | Release |
|---|---:|---:|---:|
| Gross input | 7,144,631 | 3,247,116 | 3,897,515 |
| Cached input | 6,983,552 | 3,142,784 | 3,840,768 |
| Uncached input | 161,079 | 104,332 | 56,747 |
| Output | 24,291 | 12,055 | 12,236 |
| Reasoning output | 2,884 | 1,510 | 1,374 |
| Elapsed | 19m 50s | 10m 42s native work | 6m 17s native work |

This cut gross input by about 71% and reasoning output by about 91%, but missed
the 0.1x input target. More importantly, its exact imagery did not make the
promised bird-to-shooting-star transformation legible. Release then cost more
input than Make while teaching that unproven promise. The next optimization
therefore moves signature-experience proof into Make, selects the Inventor for
the hardest-to-fake magic rather than fabrication convenience, and batches the
full manual review into one render command.

Pocket Eclipse Menagerie tested those evidence-first instructions:

| Measure | Whole run | Make | Release |
|---|---:|---:|---:|
| Gross input | 7,957,133 | 3,451,567 | 4,505,566 |
| Cached input | 7,764,992 | 3,336,704 | 4,428,288 |
| Uncached input | 192,141 | 114,863 | 77,278 |
| Output | 32,290 | 18,962 | 13,328 |
| Reasoning output | 5,709 | 4,220 | 1,489 |
| Elapsed | 22m 59s | 13m 33s native work | 6m 54s native work |

It selected Orin Shadow for the Wish's perceptual problem and produced a clean,
truthful manual, but used more tokens and time than Starling Gate. Its final
signature sheet showed object rotations rather than unmistakable shadow
outcomes, and Release made four complete manual render rounds for a one-piece
toy. The one persistent session entered Release with roughly 105k tokens of
effective context and grew to roughly 161k; more than 98% of Release input was
cached. This is the evidence behind Spark v2's 64k automatic compaction ceiling,
hash-bound independent final signature review, and double-sided-card default.
The combined quality and 0.1x economics target remains unproven until a new
permanent production challenger passes both comparisons.

Mooncoil Dragon then tested Spark v2's compaction and review policy in a real
published run:

| Measure | Whole run | Make | Release |
|---|---:|---:|---:|
| Gross input | 7,468,236 | 5,734,110 | 1,734,126 |
| Cached input | 7,034,240 | 5,401,088 | 1,633,152 |
| Uncached input | 433,996 | 333,022 | 100,974 |
| Output | 50,674 | 35,873 | 14,801 |
| Reasoning output | 11,186 | 8,076 | 3,110 |
| Elapsed | 44m 43s | 32m 58s native work | 7m 50s native work |

The two-sided manual was concise, clear, and visually strong. Release input
fell about 61.5% from Pocket Eclipse Menagerie's 4,505,566, showing that the
64k compaction ceiling and smaller manual path improved the later stage. Make
input rose about 66%, however. Private aggregate inventory showed repeated
rebuild, render, review, and complete-verifier cycles before the final CAD was
sealed, plus identical final render families in two locations. The prompted
critic even identified that the dragon's central mass competed with the
intended crescent, then affirmed readability anyway. The finished render still
read more as a flat dragon cutout than an unmistakable magical two-truth object.

This evidence changes the next optimization from another runtime knob to a
better work order. New Make runs conduct an unprimed visual read from only the
candidate images before the expensive integrated verifier, allow one focused
visual repair, then perform one stable full verification. One canonical final
render family is sealed. Inventor selection distinguishes the Wish's defining
creative problem from a mechanism that merely carries it. Release names exactly
two complete review packets: initial and final. The target remains unproven.

Moonwake Turn tested that work order in another permanent published Spark:

| Measure | Whole run | Make | Release |
|---|---:|---:|---:|
| Gross input | **>=4,040,564 partial** | **>=2,460,653 partial** | 1,579,911 |
| Cached input | **>=3,823,104 partial** | **>=2,329,472 partial** | 1,493,632 |
| Uncached input | **>=217,460 partial** | **>=131,181 partial** | 86,279 |
| Output | **>=29,364 partial** | **>=18,292 partial** | 11,072 |
| Reasoning output | **>=5,521 partial** | **>=3,956 partial** | 1,565 |
| Turn coverage | 2 / 3 | 1 / 2 | 1 / 1 |
| Elapsed | 1h 20m 45s | includes one 1h timeout | measured turn completed |

Every `>=` value is a measured floor, not a total or a valid reduction claim.
The first Make turn exhausted the historical one-hour boundary without a
terminal usage event, so no token category exists for that turn. The recovery
correctly resumed the same session and completed the toy, but the run cannot
establish either the 4.04M nominal figure or a percentage improvement as its
true economics.

The in-box manual was polished and product-specific. The exact product evidence
still exposed a semantic failure: the Wish asked for a whale leaping *through*
a crescent, while the blind reviewer recorded a crescent *beside* a whale-like
animal and then passed the overall signature boolean. Shared nouns had hidden a
wrong spatial relationship. Private run inventory also showed repeated broad
build/export/verification activity inside the one timed-out turn; a single
stage attempt was not a meaningful inner-loop bound.

Spark v3 addresses those two evidenced leaks without lowering quality gates.
Each new native Spark turn has a frozen 20-minute boundary; one critic gets at
most two rounds and must compare subjects, action, and relationship separately;
and the integrated final CAD verifier refuses to begin until the exact
hash-bound review exists. Quick checks remain available for iteration. The next
permanent challenger must have complete turn telemetry, use no more than
2,461,602 gross input tokens, and win the blind signature comparison. Until
then, the combined 10x quality-and-economics target remains unproven.

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
2. Compact tool-heavy native history while keeping exact state in durable
   workspace files, stage packets, and sealed evidence.
3. Reduce tool calls and tool-output context with bounded inspection and one
   quick-iteration/final-verification funnel.
4. Use the roster once, choose one Inventor, and spend depth on one signature
   interaction instead of broad candidate fan-out.
5. Carry sealed summaries, manifests, and renders forward instead of resurveying
   stable source at every stage.
6. Reuse deterministic CAD, render, and manual layout primitives so native
   reasoning chooses the product rather than repeatedly rebuilding plumbing.
7. Tune frozen runtime policy only from comparable production evidence. A
   cheaper configuration is not a win if blind product preference falls.
