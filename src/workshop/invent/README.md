# Invent

Owns the deterministic `Invented` handoff contract that seals the selected
product concept and its research for Make. Codex performs native search, source
evaluation, concept exploration, selection, physical specification, synthesis,
and specialist delegation in the product project; this Python package does not
implement a research agent, prompt chain, reward loop, or stage orchestrator.

Public API: `workshop.invent`.

## Design vault

`workshop.invent.vault` reads an Obsidian-compatible design vault — mechanism,
anti-pattern, rule-pattern, constraint, and component nodes joined by typed
wikilinks — with the standard library only, lints it, packs it into one
content-addressed JSON document, and answers deterministic questions:
`read_node`, `follow_links`, `resolve`, `check_compatibility`, and `guidance`.
The seed under `vault/` ships with the distribution (see
`vault/PROVENANCE.md`); `workshop vault seed` copies it into the host-owned
`$WORKSHOP_HOME/vault/`, which humans edit and `workshop vault lint` checks.
No model call and no search index: agents traverse the links the vault
declares.
