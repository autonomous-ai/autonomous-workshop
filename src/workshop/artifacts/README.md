# Artifacts

Owns manifests, canonical byte identity, packing, inspection, sealing, and the
registry that discovers component-owned JSON schemas.

Public API: `workshop.artifacts`. Adapters that must upload exact bytes use
`load_artifact_payload`; callers that already hold bytes use
`validate_artifact_payload`. Private helpers in `pack.py` are not component
boundaries.
