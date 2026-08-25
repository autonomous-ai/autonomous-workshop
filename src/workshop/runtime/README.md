# Runtime

Owns durable events, effects, leases, retries, execution environments, and
Workshop persistence. It contains no creative stage policy.

Public API: `workshop.runtime`. The runtime owns durable effect proof contracts
(`Receipt`, `SendResult`, and their compatibility aliases); integrations
produce those contracts but do not own them.
