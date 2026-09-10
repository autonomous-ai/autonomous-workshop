Token-budget products no longer stop at a wall-clock timeout, native-turn
count, proposal-rejection count or lifecycle-round count. Native usage remains
mandatory and all product gates remain required. New signature-review tools
accept positive review counts beyond two. Explicit `resume --refresh-tools`
can update an allowlisted set of token-budget review tools and references,
record the correction, and rebind the same session and exact token ledger.
Temporary provider overload/service failures resume with backoff. Native token
accounting no longer caps a product at 32 sessions. Token-budget products run
host CAD verification without a wall-clock deadline, retaining cancellation
cleanup and bounded output capture.
Token-only runs also drain diagnostic stderr without a cumulative-volume stop,
preserve growing usage ledgers and checkpoints, and no longer stop at cumulative
artifact-size or host-artifact-count caps. Rejection histories validate iteratively
instead of exhausting Python recursion, and Spark retries preserve their actual
Make-to-Release transition.
Valid pending requests no longer have a three-minute first-usage deadline.
Completed root-turn usage is reconciled with native terminal counters; unresolved
accounting is durable across resumes and cannot be bypassed by a saved proposal.
In-flight or canceled descendants remain explicitly pending, and reaching the
token cap alone does not prevent an already-made product's host-only publication.
