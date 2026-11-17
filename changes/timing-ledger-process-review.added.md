Long-running Workshop steps now append one row each to a timing ledger under
the Workshop home (`timing/ledger.jsonl`): seeded batch steps and the
verify_project commands they print, seal_proof commands, make_round modes,
kit_sheets, kit_tree, kit_print, kit_manual, publish_direct and `workshop
wish`/`fix` stage operations, each with wall time, exit code, outcome
(pass, fail, unverified, killed) and a failure class (product defect, tool
error, stale input, killed). The ledger only records; no gate reads it.
`tools/process_review.py report` ranks the slowest steps, reruns on
unchanged inputs, expensive steps before cheap failures, non-product
failures and waits into `docs/research/process-review/<date>.md`;
`backfill` imports the existing toys-spec logs and `annotate` records an
agent's later diagnosis (ADR 0106).
