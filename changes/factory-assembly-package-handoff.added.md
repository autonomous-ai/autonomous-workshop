- Hand each sealed occurrence of a multi-part toy to the Factory as its own
  production mesh. The Factory adapter now reads the cadgen assembly-package
  Make seals at `assembled.step.json`, resolves every occurrence to its
  build-group STL under `parts/`, and transports `assembled_parts/<name>.stl`
  with the synthesized sidecar; the existing `factory-part-colors` effect then
  colours the meshes the shop reports. The Make gate rejects a package with two
  or more occurrences that lacks those STLs (`make-production-parts-missing`,
  naming the paths), and the release receipt records `handoff_transport`,
  `occurrence_count`, and why a toy crossed as a single mesh.
