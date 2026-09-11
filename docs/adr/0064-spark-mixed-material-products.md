# ADR 0064: Spark Make describes and publishes complete mixed-material products

- Status: Accepted
- Date: 2026-09-10
- Owners: Make, runtime packaging, Release, Factory integration

## Context

Autonomous operates an internal workshop with additive manufacturing, sheet
cutting, CNC, woodworking, textiles and handcraft. Its staff assemble finished
products before shipping them. A printed part is one possible component of a
product. A customer-facing product page needs the complete object, while staff
need a bill of materials, purchased-part specifications and assembly instructions.

The first capability portfolio uses a few original toys covering leading
KiwiCo play categories and verified material families. This is a benchmark for
design and workshop capability, not evidence that a generated toy has been
physically tested or outperforms an existing product.

## Decision

New Spark Make products may opt into a versioned `manufacturing` marker in
`product.json`. It binds the exact internal manufacturing manifest. Make owns
its standalone structural validator and skill. The manifest separates installed
components and repeated assembly occurrences from raw stock, consumables,
reusable tools and workshop assembly steps. Components have a material family,
specification, process, quantity and fabrication files or sourced dimensions.
Its assembly binds the canonical complete STEP and assembly descriptor.

Optional `assembly_unit_ids` separate physical unit counts from their colored
CAD leaves. Purchased subassemblies retain their existing sourcing contract.
A grouped `3d-print` component additionally declares `production_part`, binding
one explicit printable `part_<role>.step.py` and its generated sibling STEP
through that component's exact file hashes. Each selected subassembly is one
repetition of that production definition. All of its leaves must be covered
exactly once, and source ownership and the normal print subset remain enforced.
Other fabrication processes do not gain grouped-unit support.

This aligns mixed-material inventories with CAD's existing disjoint color-region
representation of a single fused printed part. The binding proves file identity,
hierarchy and declared quantities; it does not prove that the displayed regions
reconstruct the production solid. Make derives those regions from the same
source and retains its geometry, interference, print and visual checks. Paint
remains a finishing consumable; the BOM does not require tiny coating solids.

The Make finalizer validates this specification before sealing the complete
private product tree. Printed entries explicitly declare `PRINTABLE = True`;
nonprinted and display entries declare `False`. Source print checks apply only
to printed entries. Existing engineering and independent visual review remain
Make's responsibility. No Python planner, sourcing agent, machine operator or
physical-test judge is added. STEP remains the only geometry deliverable.

The manifest explicitly selects public files beneath `public/`, including a
byte-identical complete assembly STEP and an image. Host publication checks
that selection's exact identity. It does not repeat manufacturing validation,
rebuild the assembly or create new renders. Factory receives only those selected
assets plus deterministic customer metadata. A root `assembled.step` carrier
alias is an exact copy of the selected scene and its source mapping is recorded.
The public archive uses the same selection and omits private BOMs, source,
supplier specifications, full Wish facts and prior internal attempts.

The complete Made contract remains local. The publication anchor binds its
opaque identity and the selected public file identities, allowing readback
reconciliation without exposing the manufacturing package. Customer copy and
authored public images still require native review: path and hash checks cannot
judge whether prose or a drawing reveals an internal detail.

## Alternatives considered

Treating every occurrence as a printed solid misrepresents sheet, textile and
purchased components. Hiding an internal BOM link leaves publicly uploaded
bytes exposed. A second host engineering pass duplicates Make and contradicts
ADR 0061. New electronics orchestration, procurement, machine toolpaths and
physical Operations are outside this MVP.

## Consequences

The workshop can receive a coherent mixed-material handoff while customers see
the finished toy. A structurally valid manifest proves file identity, quantities,
references and declared scope, not buildability, supplier availability, physical
safety, durability or delight. Internal prototype checks remain explicit work
for Autonomous staff. This change does not authorize purchases or manufacture.

## Compatibility and migration

The marker is optional and accepted only for Spark. Missing markers retain the
existing path; malformed markers fail closed. NativeMade's schema and private
identity are unchanged. Spark's schema-4 Release accepts an optional versioned
public projection. Forge, Quest and unmarked historical products retain their
contracts. Frozen runs retain their tool snapshots unless an operator uses the
existing explicit CLI refresh mechanism.

## Verification

Contract and failure-path tests cover occurrence/quantity coverage, source
declarations, fabrication and sourcing requirements, canonical assembly identity,
tampering, unsafe paths and explicit public selection. Finalizer tests seal a
synthetic mixed product without executing its CAD. Factory and archive tests
place private sentinels in the Made tree and prove they never enter public
assets, metadata or historical copies. Synthetic evidence is not live product
acceptance. CLI pilot commands and observed outcomes are recorded separately
in `docs/ideas/mixed-material-cli-runs.md`.
