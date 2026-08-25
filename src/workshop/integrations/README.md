# Integrations

Owns external adapters and Factory-specific request canonicalization for model,
CAD, publication, and delivery boundaries. Runtime owns the durable receipt
contracts those adapters produce. Secrets remain in the calling process and
never enter durable Workshop records.

Public API: `workshop.integrations` contains only adapter protocols. Concrete
Factory and Shop implementations stay in qualified modules and depend on
runtime-owned proof contracts; runtime code never imports an integration.
