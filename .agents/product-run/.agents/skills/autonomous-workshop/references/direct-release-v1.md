# Direct Release protocol v1

This immutable capability marker means the executable Workshop lifecycle is:

```text
Wish -> Match -> Invent -> Make -> Release
```

Playtest is intentionally deferred. Release must not claim that Playtest ran or
passed. The Release package instead contains the canonical
`PLAYTEST-NOT-RUN.json` omission record and binds its exact hash. Ready-to-print
CAD still must pass the host's full deterministic verifier before Release and
again before publication.
