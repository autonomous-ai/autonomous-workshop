Track an existing Factory design's immutable-version import as a distinct
`factory-import-version` effect. The schema-4 ledger migration preserves prior
intent bytes, states, and receipts; unknown version effects cannot be blindly
reopened or replaced. Historical ledgers remain inspectable without migration.
