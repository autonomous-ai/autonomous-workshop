# Runtime

Owns durable events, effects, leases, retries, execution environments, and
Workshop persistence. It contains no creative stage policy.

Public API: `workshop.runtime`. The runtime owns the durable external-effect
`Receipt` contract; integrations produce Receipts but do not own the contract.
