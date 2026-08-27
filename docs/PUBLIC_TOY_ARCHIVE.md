# Public toy archive

After authenticated Factory readback proves that an exact Release is public,
Workshop can project a sanitized, content-addressed archive into
`toys/<inventor>-<slug>/`. The private product-run workspace remains the
lifecycle authority; the repository archive is a durable public record, not a
second workflow state store.

## Workflow-shaped layout

```text
toys/<inventor>-<slug>/
├── README.md
├── MANIFEST.json
├── wish/
│   ├── WISH.md
│   └── wish.json
├── match/
│   ├── assignment.json
│   └── ATTEMPTS.json
├── invent/                         # only when Invent ran
│   ├── invented.json
│   └── ATTEMPTS.json
├── make/
│   ├── invented.json              # Spark's compact Make-owned concept only
│   ├── made.json
│   ├── product.json
│   ├── ATTEMPTS.json
│   ├── source/cad/
│   ├── models/assembled.stl
│   ├── models/print/
│   ├── models/cad/
│   └── verification/
├── playtest/                       # only when Playtest ran
│   ├── playtested.json
│   ├── ATTEMPTS.json
│   └── evidence/
├── release/
│   ├── release.json
│   ├── product.json
│   ├── MANUAL.pdf
│   ├── PLAYTEST-NOT-RUN.json       # direct-Release routes only
│   └── ATTEMPTS.json
└── publication/
    └── PUBLICATION.json
```

Skipped lifecycle stages are absent. Publication is separate because it is a
host-owned authenticated effect, not agent-authored Release evidence.

## Evidence and privacy

- Exact Made and Release bytes are rehashed before projection.
- Historical Make and Playtest rounds contribute sanitized, content-addressed
  outcomes to `ATTEMPTS.json`; superseded working-directory caches do not.
- The exact Wish is withheld by default. Publishing its text requires the
  caller to opt in explicitly; either form retains the exact Wish hash.
- Agent prompts, transcripts, reasoning, session data, host state,
  credentials, and raw effect receipts are never copied.
- `MANIFEST.json` hashes every archive file except the root `README.md` and
  `MANIFEST.json` itself. Those exclusions avoid a recursive self-hash and are
  declared in the manifest.
- Public publication proves authenticated site readback of the exact digital
  Release. It does not prove physical manufacture, fit, durability, or
  delivery.

The projector installs a new archive exclusively and never merges or
overwrites a different existing tree. Versioned migrations must stage and
validate the complete replacement first, preserve the exact released manual,
product contract, and primary model bytes, and keep a recoverable copy until
the migration is committed.
