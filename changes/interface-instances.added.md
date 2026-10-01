- Design Contract schema 2: an Interface may name one instance of a Unique
  Geometry whose count is above 1, written `<id>#<n>` (`wing#1`, `wing#2`), in
  its components, envelope sides, yielding Component and pose-table movers. A
  mirror pair that meshes is now a Coupled Interface checked before assembly.
  The geometry's one Component file builds and places each instance through
  `assembly_pose(shape, pose, instance)` and an optional
  `gen_step(instance=1)`; `make_round --interface` and the Keep-out Envelope
  check understand instances, and the run report lists them by name.
  Contracts with bare ids, schema 1 contracts and frozen runs are unchanged.
