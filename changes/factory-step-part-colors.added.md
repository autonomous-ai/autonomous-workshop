- Publish a toy in the colours Make actually sealed. Release now reads the
  per-part surface colours out of the run's sealed STEP bytes and, when a
  colour addresses a mesh the shop reports for the imported draft, sends them
  to `PATCH /designs/{slug}/part-colors` so the listing's thumbnail renders
  in those colours instead of the shop's defaults. A run whose STEP carries
  no colour sends nothing and is unchanged.
- Read those colours with `workshop.make.cad.step_color.read_step_part_colors`,
  a standard-library-only reader over sealed STEP bytes. `cadgen` stores a
  colour as linear RGB, so the reader applies the sRGB transfer function to
  recover the hex a designer picked, and drops any part whose colour is
  missing, unreadable, or contradicted by another sealed file.
- The colour write is a durable Factory effect like import, page content, and
  publish: intent first, one partial merge, then authenticated readback. This
  adds the `factory-part-colors` effect kind and migrates the effect ledger to
  schema version 3; an existing version 1 or 2 ledger is rebuilt in place on
  first open.
