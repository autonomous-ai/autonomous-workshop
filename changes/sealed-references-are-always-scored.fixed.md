- **A Make round can no longer pass without scoring the references the Wish
  sealed.** `ad-astra-antisol-v01` sealed eight reference images and kept
  twenty copies under its CAD project's `ref/`. Yet its assembly round state
  records `"likeness": {}` and every component round records `"refs": []`.
  No silhouette was scored and every round reported a pass. `make_round`
  found references only through `--ref` or a ledger in `*_spec.md` that the
  Manager writes by hand, and an empty list passed `all(...)`. The assembly
  round now reads the sealed list from `WISH.json` directly (ADR 0072).
- **The build-spec template could never feed the ledger.** image-to-cad's
  Likeness handoff is a markdown table, and the ledger parser only read
  `LABEL=ref/<file>` lines. A completely filled template therefore produced no
  references. The parser now reads the table row as well.
- **Component references stay with their Component.** A sealed reference that
  a current, passing component round already scored is not scored again
  against the whole object. Any other sealed reference is scored against the
  assembly. When one fails there, the summary names the component-round
  command that would score it at the right scope. Component rounds still score
  only the references they are given explicitly (ADR 0063).
- **Missing or altered references fail loudly.** A sealed reference that is
  missing or no longer matches its hash, or a `WISH.json` that cannot be read,
  fails the round and names the reference. It is never silently dropped.
  Projects outside a Workshop run keep their ledger-only behaviour.
