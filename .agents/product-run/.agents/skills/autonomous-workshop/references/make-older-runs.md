# Make for older runs and older Design Contracts

Read this once, beside `make.md`, only when one of these holds. Each section
names its case; skip the others. Where a section differs from `make.md`, it
wins for that case.

## No run-root `MAKE-OPTIONS.json`

An older run without that file keeps mandatory motion verification: run the
motion sweeps, produce the required animation and its independent motion
review whatever `check_motion` would have said.

## A Spark packet without `inputs.workshop_selection`

A frozen older Spark run selects its Inventor inside Make. Rank the complete
roster once from `STAGE.json`'s compact `inventor_discovery_index`, read only
the best three full custom-agent TOMLs, select the Inventor whose Taste owns
the hardest-to-fake magic, and write the `--source` with exactly
`selected_inventor_id`, a roster-covering `ranking`, `concept` and
`research`.

## A sealed Design Contract below schema 4

Before schema 4 (ADR 0084) a component round's visual packet has no
`contract`, and Interfaces carry no `text`. Send the Component Reviewer the
packet path, its sha256 and, as the request's third item, that Component's
contract rows; send nothing else. Give each worker the rows of every
Interface its Component joins, without Interface text.

## A sealed Design Contract below schema 3

Before schema 3 (ADR 0083) references carry no Reference Camera and
Components need not define `assembly_pose(shape, None)` unless an Interface
places them. A component round renders the model in its print stance at the
reference's declared camera (`@AZ,EL` on the `--ref`, else the front view).
The reviewer has no camera-mismatch answer; ignore that part of `make.md`.
