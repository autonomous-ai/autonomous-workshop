# Contributors

Owns the lean native Inventor contract: strict schema-v7 manifests, exact Taste
loading, safe catalog discovery, and static extension validation.

Public API: `workshop.contributors`.

An Inventor is one bundle: `inventor.json`, `TASTE.md`, `skills/`, and at most
an optional concise `README.md`. Its v7 manifest declares an exact, sorted
inventory of namespaced Codex skills. Each skill has a root `SKILL.md` and may
include `scripts/`, `references/`, and `assets/`; the manifest binds the
complete tree by SHA-256. Pre-v7 manifests are rejected.

Validation hashes and scans every declared byte but never imports or runs a
contributor script. An extension is context and tooling for the selected native
Inventor, not an entrypoint, hook, stage worker, lifecycle
transition, model launcher, effect authority, or credential channel. Runtime
sandboxing and host gates remain authoritative. There is no executable-profile
or legacy-manifest compatibility path.

Contributors does not perform Match reasoning or lifecycle orchestration. The
host materializes validated Inventor bytes into the private native-agent run;
shared deterministic tools remain owned by their Workshop stages.
