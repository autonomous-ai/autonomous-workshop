# Contributors

Owns the lean reusable Inventor source contract: strict schema-v8 manifests,
exact Taste loading, safe source discovery, and static skill-tree validation.

Public API: `workshop.contributors`.

An Inventor source bundle contains `inventor.json`, `TASTE.md`, `skills/`, and
at most an optional concise `README.md`. Its v8 manifest records the stable id,
status, source, and an exact sorted inventory of namespaced Codex skills. Each
skill has a root `SKILL.md` and may include `scripts/`, `references/`, and
`assets/`; the manifest binds the complete tree by SHA-256. Older manifests are
rejected.

Validation hashes and scans every declared byte but never imports or runs a
contributor script. A skill is context and tooling for a selected native
Inventor, not an entrypoint, hook, stage worker, lifecycle transition, model
launcher, effect authority, or credential channel. Runtime sandboxing and host
gates remain authoritative.

Contributors does not perform Inventor-selection reasoning, route agents, or
own a product loop. The host validates reusable source bytes and materializes
each eligible Inventor into `.codex/agents/<id>.toml`; that directory is the
sole Inventor roster inside a toy project. Selection is folded into the first
active creative stage; new runs have no separate Match turn. One native Codex
Goal owns each active Invent, Make, Playtest, or Release attempt, and Codex
performs the observe -> act -> evaluate -> improve behavior while pursuing it.
Shared deterministic tools remain owned by their Workshop stages.
