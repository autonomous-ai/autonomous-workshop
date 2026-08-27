# Playtest

Owns AI-player simulation, exact-artifact evidence, release proofs, and
actionable feedback to Make. Missing or stale evidence never passes.

Public API: `workshop.playtest`.

## Cross-run evidence ledger

`workshop.playtest.evidence_ledger` banks every sealed Playtest's feedback as
one row per finding under `$WORKSHOP_HOME/evidence/evidence.jsonl`, tagged
with the design-vault mechanisms the sealed concept resolved to and weighted
by provenance. The next run sharing a mechanism receives the strongest ten
rows as `prior_evidence`, never its own. Confirmed vault leads are banked on
the host vault's anti-pattern nodes; dismissals wait in `vault/_review/` for
a human. `workshop evidence harvest` rebuilds the ledger from the host's own
gate receipts and the sealed contracts they bind.
