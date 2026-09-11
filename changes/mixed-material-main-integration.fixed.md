- Rebase mixed-material Spark/Make onto main while preserving Astra defaults,
  operator turn boundaries, sealed STEP covers, all 22 Inventors, and the
  original mixed-material publication/privacy contracts.
- Honor explicitly selected native turn limits through the token-budget
  launcher's final reconstruction. Ordinary token-budget runs remain untimed;
  changing effort or the total cap preserves the exact native session, Make
  mode, frozen input identities and prior usage.
- Increase the frozen input inventory capacity from 256 to 512 files so the
  combined roster can initialize. Keep the 4 MiB input-byte budget and all
  checkpoint, privacy and exact-byte checks; reject the 513th input.
- Move the bounded compressed carrier codec and its unit tests into the
  artifacts component, which owns the archive internals it uses. Carrier
  format, bytes, limits, cache identity and effect reconciliation are unchanged.
- Reseal the combined Make-round guidance and resolve the duplicate ADR 0064
  number by assigning the mixed-material decision ADR 0067.
