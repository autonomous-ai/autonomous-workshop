- Publish only the sealed assembled STEP to Factory. The handoff now drops every
  per-part and duplicate STEP/STP (`parts/*.step`, `part_*.step`, a second root
  copy) and no longer builds the multipart occurrence family, viewer-parity
  part keying or `assembled_parts/`; every toy crosses as one mesh and part
  colours are written by `mesh_name`/stem. Receipts drop
  `handoff_transport_reason`, `viewer_groups` and `viewer_group_keys`, and
  `project.json` no longer lists part names. Make still produces the part STEPs.
