# Invent

Owns the deterministic `Invented` handoff contract that seals the selected
product concept and its research for Make. Codex performs native search, source
evaluation, concept exploration, selection, physical specification, synthesis,
and specialist delegation in the product project; this Python package does not
implement a research agent, prompt chain, reward loop, or stage orchestrator.

Public API: `workshop.invent`.

## Design vault

`workshop.invent.vault` reads an Obsidian-compatible design vault — mechanism,
anti-pattern, rule-pattern, constraint, component, combo, and game nodes
joined by typed wikilinks — with the standard library only, lints it, packs
it into one content-addressed JSON document, and answers deterministic
questions: `read_node`, `follow_links`, `resolve`, `check_compatibility`, and
`guidance`. No model call and no search index: agents traverse the links the
vault declares.

The vault itself lives on the panda VM (`github.com/nohope88/gamevault`) and
is served by admindash's `/api/gamevault/*` behind one bearer token.
`workshop.invent.gamevault` is the host-only client: the URL and token come
from `WORKSHOP_GAMEVAULT_URL` / `WORKSHOP_GAMEVAULT_TOKEN` or the private
`$WORKSHOP_HOME/credentials/gamevault.env`, and never reach a product run.
Before every Invent, Make, and Playtest phase the host exports the whole
vault live, caches the packed snapshot per checkpoint under host state, and
writes it into the run as the read-only `VAULT.json` bound by hash in
`STAGE.json`; the run's `design-vault` skill queries that snapshot offline.
An unreachable vault stops the phase before the session starts and
`workshop resume` retries. `workshop vault lint|check` read the API (or a
local checkout with `--root`).
