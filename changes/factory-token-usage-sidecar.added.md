- Factory imports now carry the product's lifetime token budget in a `usage`
  multipart field beside the sealed ZIP, so token spend stays visible in the
  shop. The document never enters the handoff bytes and never enters the
  effect identity: lifetime usage grows between resumes, and hashing it would
  mint a fresh intent on every retry and let one publication happen twice.
- Usage is statistics and cannot fail a release. A budget Factory will not
  take — malformed, or past the 1 MiB field ceiling — is reported as its
  totals without the per-thread observation, and dropped entirely when even
  those will not go. A direct `FactoryClient` caller still gets the contract
  error, because a malformed document there is a programming fault.
- `used_tokens` is the cumulative lifetime total, and `usage_status` is
  `"unavailable"` when usage could not be attributed: that case ships its
  status intact rather than reporting zero spend. Only Codex runs observe
  usage today, so a Claude run sends no `usage` field at all.
