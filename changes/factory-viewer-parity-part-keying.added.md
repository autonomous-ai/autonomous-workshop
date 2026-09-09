- Key part colours the way the Factory viewer resolves them. The host now
  reproduces the viewer's part grouping of the sealed `assembled.stl`
  (manifold-edge shells, loose facets owned by the shell they face, dense
  numbering in triangle order), owns every group with the sealed production
  mesh's shape signature and the posed occurrence geometry of the sealed STEP
  (`workshop.make.cad.fe_parts`, `posed_occurrences`), and sends one
  `assembly_parts` entry per viewer group (`order`, the slide or `#slot` key,
  owner `mesh_name`, sealed colour) through the part-colours effect, so a part
  that splits into several shells or sheds slivers no longer shifts the
  listing's colours. This replaces the one-shell-per-part rule that dropped a
  30-part locomotive to a single mesh. Sidecar parts carry `index`; receipts
  record `viewer_groups` and `viewer_group_keys`.
- Require a sealed surface colour on every part of a multi-part Make
  (`make-part-colours-missing`, naming the uncoloured occurrences), so every
  listing can be coloured.
