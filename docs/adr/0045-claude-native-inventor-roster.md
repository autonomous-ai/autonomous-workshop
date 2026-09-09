# ADR 0045: Claude native Inventor roster

New Claude runs materialize the single Inventor roster under `.claude/agents/*.md`,
matching MANAGER.json. Canonical YAML scalar frontmatter selects name, description
and `model: inherit`; the Markdown body preserves the same exact manifest, Taste,
skill blocks and child authority boundaries as Codex's canonical TOML projection.

Host bindings, instruction hashes, Match/Spark source validation and immutable-tree
verification include the actual Claude paths and bytes. Secret-content scanning
still applies. `.claude` remains excluded from publication; the exact canonical
runtime input is scanned under a neutral filename, without broadening package rules.

Codex projection bytes remain unchanged. Existing frozen runs retain their original
agent files and finalizers; they are not silently migrated. Grok projection remains
unimplemented. This fixes Claude's missing roster, not a guarantee of model quality.

Validation uses real repository Inventors, roundtrip and mutation tests, native
Match/finalizer roster validation, and workflow regression tests. Official format:
https://code.claude.com/docs/en/sub-agents
