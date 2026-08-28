# Terminal Release capability

The presence of this immutable, host-hashed file declares that the
materialized product-run finalizer uses `complete` as Release's forward
transition. Older run workspaces do not contain this marker and retain their
historical `release -> deliver` proposal protocol solely for migration.

For marked runs, Workshop is complete only after the host has verified the
full print-ready CAD tier, validated `MANUAL.pdf`, published the exact handoff
to Factory, and accepted authenticated public readback bound to those bytes.
Printing, physical QA, shipping, delivery, and customer review belong to the
downstream Operations workflow.
