# ADR 0060: Visual feedback in Make rounds and three critic repair cycles

- Status: Accepted
- Date: 2026-09-09
- Supersedes for new runs: ADR 0057's optional round image inspection and
  ADR 0023's one-repair final Make allowance

## Decision

Each Make repair round generates front, top and isometric inspection images,
including when there are no likeness references. The native Manager examines
them against the Wish and concept for misplaced parts, size/proportion errors,
missing/extra parts, visible intersections and incorrect form. It records
concrete findings and proposed repairs using `make_round --record-visual`.
The same round summary then contains numeric and visual feedback.

The deterministic tool binds observations to a packet of source/constraint,
render and reference hashes. Missing inspection stays pending; render failure,
inconclusive observation, stale evidence or contradictory feedback cannot pass.
It never calls a model, reasons about imagery or edits CAD. Native inspection
remains distinct from independent blind review, and cannot replace that gate.

Final Make permits three focused repair-and-rereview cycles after the initial
independent review: four reviews maximum. Stop on the first pass. Regenerate
and pass print preflight before every rereview; retain exact observations before
comparison and disclose prior knowledge on rereviews. Exhaustion produces a
truthful failed outcome. Early-proof and Release manual review budgets do not
change. The final integrated verifier still runs after passing blind review;
only the host performs the authoritative isolated fresh rebuild.

## Compatibility

The new instructions, finalizer and CAD verifier are materialized and hashed
at run creation. Existing runs keep their original tool bytes and review
allowance. No existing workspace or host checkpoint is rewritten. Signature
review retains schema v6 and its exact fields; the bounded integer expands to
1–4 in new validators. The host replays the run's frozen verifier.

## Verification

Deterministic fakes exercise rendering without references, visual feedback,
stale source/image/reference rejection, contradictory and missing feedback,
and round summaries. Finalizer and CAD tests cover four-review acceptance and
five-review refusal. Production gates and thresholds remain intact.
