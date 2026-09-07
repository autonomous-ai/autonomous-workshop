# Persistent native execution budget v1

This capability is enforced by the Codex adapter. Other adapters retain their
existing command clocks until they expose equivalent bounded launch support.

New Codex runs have 40 minutes of native execution per stage and 60 minutes across
the entire product, including all resumes and repairs. These are ceilings,
not a promise of completion. Preserve time for Release. A turn also retains
its frozen launcher limit. The host reserves time before launch; a process
crash conservatively consumes its outstanding reservation. Resume never
replenishes this budget. Exhaustion preserves artifacts and stops native work.

This allowance bounds native wall time, not token quantity, billing, host CAD
verification, remote publication waits, or elapsed time while stopped. Missing
native usage remains explicitly unmeasured; do not report a complete token
total or dollar cost from partial telemetry. No gate or physical-evidence
requirement is waived to finish within the allowance.
