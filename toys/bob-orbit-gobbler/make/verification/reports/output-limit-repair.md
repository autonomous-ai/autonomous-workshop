# CAD verifier output-limit repair

- Rejection SHA-256: `f05c6981c65b313563451d17f230c51e4f4852089b20312fa8ff820225868339`
- Rejected Made identity: `336ae33352ab20f9abbc07796eeb569992a79a656cc27937ffb65bd9a292015a`
- Rejected product artifact: `54d912f4d073dd9e7650458980747677bf7a34dbdd8133aa3ed1f8c0c7c2d29f`
- Rejected stdout: 66,161 bytes
- Host stdout limit: 65,536 bytes
- Repaired isolated stdout: 61,677 bytes
- Margin: 3,859 bytes
- Repaired isolated stderr: 2,022 bytes
- Exact isolated command result: exit 0

The reduction comes from artifact truth, not suppressed checks. The 23-piece BOM contained two pairs whose geometry was already identical: central-axle/grip snap clips and central-axle/grip thrust washers. They now use one printable entry per shared type with quantity two. The final verifier still runs strict fit, all local audits, motion, reference/validity/interference inspection, STL export, mesh integrity, and wall thickness on every one of the 19 unique printable targets.

The full candidate-tree run is recorded in `verification-pipeline.md`. The exact copied-project stdout and stderr are retained outside the bounded product artifact at `work/make/r0001/output-limit-repair/verify-isolated.stdout` and `.stderr`.
