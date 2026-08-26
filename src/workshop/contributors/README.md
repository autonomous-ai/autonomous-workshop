# Contributors

Owns the lean native inventor-persona contract: schema-v6 manifests, exact
Taste loading, safe catalog discovery, static contribution validation, and the
two-file scaffold.

Public API: `workshop.contributors`.

A local persona is data, not executable code. Its folder contains
`inventor.json`, `TASTE.md`, and at most an optional concise `README.md`.
Validation never imports or starts contributor code. Legacy manifest schemas
remain readable during migration, but new local contributions must use schema
version 6 and cannot declare `entrypoint` or `checks`.

Contributors does not perform Match reasoning or lifecycle orchestration. The
host materializes validated persona bytes into the private native-agent run;
shared deterministic tools remain owned by their Workshop stages.
