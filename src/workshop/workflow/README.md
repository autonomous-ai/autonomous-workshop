# Workflow

Owns sequencing, bounded Make–Playtest feedback, checkpoints, and the final run
projection. Stage implementations remain in their owning components.

Composition defaults live in `workshop.bootstrap`.

`Workshop` consumes explicit `WorkshopTools`; applications and generated
profiles use `workshop.bootstrap.configured_workshop` when they want the shared
default workers.
