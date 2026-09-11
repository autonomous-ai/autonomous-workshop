# ADR 0065: Explicit reasoning-effort changes for saved Spark products

- Status: Accepted
- Date: 2026-09-10
- Owners: CLI and Workflow maintainers
- Supersedes: ADR 0043's prohibition on explicit effort changes, only for the
  supported Codex Spark token-budget profile described below

## Context

The operator requested that six existing mixed-material Spark products continue
with medium reasoning and a 500M-token total allowance. Recreating their Wishes
would lose the existing session relationship and separate prior consumption
from the new allowance. A plain resume must still preserve saved settings.

## Decision

`workshop resume ID --effort medium --max-tokens 500000000` explicitly changes
the reasoning setting and total allowance of the existing product. Omitting
either flag retains its saved value. The 500M maximum is documented in ADR 0049;
the default remains 30M.

Effort changes are supported only for marked Codex Spark token-budget products
with schema-v2 Manager selection and the existing budgets capability that binds
their native runtime profile. The model and workflow cannot change. The host
validates the requested effort against the existing model; for example, ultra
still requires Astra. Older profiles and other workflows are refused.

Under the exclusive run mutation lock, the host changes only the reasoning
field of `MANAGER.json`, its exact input binding, and the checkpoint revision.
A private write-ahead record allows an interrupted correction to finish on the
next resume. Recovery admits only the recorded before/after identities and
retains an idempotent correction ledger. Ordinary checkpoint reads do not
repair or mutate pending corrections.

The native session, Wish, Inventor roster, model, workflow, tool bytes, artifacts,
engineering checks, publication authority and consumed tokens remain intact.
The next native launch reads the new saved effort and passes it explicitly to
Codex. This profile already binds its runtime policy to the frozen budgets
capability; the correction does not replace the session or relax its binding.

## Alternatives considered

Starting a new Wish would discard continuity. Changing only the CLI launch
argument would disagree with the persisted Manager selection and make status
misleading. Directly editing a live workspace would bypass host identity checks.

## Consequences

The operator must stop an active CLI before issuing the resume command; the run
lock prevents concurrent mutation. Native work uses the newly selected effort
after resume. Historical usage and past high/ultra work remain historical facts.
This adds no model-selection agent, automatic effort policy or new lifecycle.

## Compatibility and migration

Existing runs retain their current settings until an explicit supported change.
The original Wish text and frozen skill instructions remain exact. The host
Manager selection is the authority for the explicitly changed runtime setting.

## Verification

Targeted tests cover CLI forwarding and invalid options, exact Manager/input
changes, preserved session and budget identities, unsupported profiles, and
recovery across interrupted writes. The six live CLI changes and subsequent
status checks are recorded separately in the mixed-material CLI pilot record.
