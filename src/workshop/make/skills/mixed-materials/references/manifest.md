# Manufacturing manifest v1

This is an **internal Autonomous manufacturing handoff**. Autonomous fabricates,
sources, assembles and ships the finished product. The customer's page contains
the finished product and approved customer content; the BOM, stock quantities,
suppliers, source files and production instructions remain private.

This contract does not prove physical manufacture, fit, operation, material
strength, electrical suitability or safety. Existing CAD, print, motion and
power evidence still own their respective claims. No purchase or manufacture
is performed by this validator.

## Entry point and API

Opt in through root `product.json`:

```json
{
  "title": "Finished product name",
  "summary": "A description of the assembled product.",
  "manufacturing": {
    "schema_version": 1,
    "manifest_path": "internal/manufacturing.json",
    "manifest_sha256": "<SHA-256 of the exact manifest bytes>"
  }
}
```

No marker means legacy behavior, with no manufacturing checks. A partial,
unknown-version or malformed marker is an error. The manifest path is fixed.
Hash every referenced file after it is final; write the manifest, then hash the
manifest into `product.json`. Never hash the manifest into itself.

The standalone standard-library script exposes:

- `read_manifest(product_root: Path, product: Mapping) -> dict | None`: validates
  the marker, exact manifest bytes, strict JSON, version, kind and delivery.
- `validate_manifest(product_root, product, *, cad_project_path=None) -> dict | None`:
  performs all structural Make checks below, without executing CAD.
- `public_asset_paths(product_root, product) -> tuple[str, ...] | None`: validates
  only the identity and explicit public projection. It does not repeat Make's
  component, stock, source, occurrence or print-scope validation.

All validation failures raise `ManufacturingManifestError`, a `ValueError`
subclass. CLI:

```sh
python manufacturing_manifest.py <product-root> --cad-project-path cad
python manufacturing_manifest.py <product-root> --public-assets
```

`--cad-project` is an alias. The first command reports a structural PASS or a
failure, never an engineering certification. The second returns only public
asset paths. These are Make tools, not additional host geometry gates.

## Complete shape

All fields shown below are required unless marked optional. An object has no
extra fields. Replace placeholder hashes with lowercase 64-digit SHA-256.
`files` and other lists may be empty only where explained after the example.
This abbreviated product has a printed frame and bought elastic loop; a real
mechanism must include every other installed component it uses.

```json
{
  "schema_version": 1,
  "kind": "workshop.manufacturing",
  "delivery": "assembled-product",
  "assembly": {
    "step": {"path": "assembled.step", "sha256": "<sha256>"},
    "occurrences": {"path": "internal/assembled.step.json", "sha256": "<sha256>"}
  },
  "components": [
    {
      "id": "frame",
      "name": "Printed frame",
      "material": {"family": "polymer", "specification": "Blue PLA"},
      "process": "3d-print",
      "quantity": 1,
      "occurrences": ["frame"],
      "specification": "Build from source at the declared print orientation; 0.4 mm nozzle.",
      "files": [{"path": "cad/part_frame.step.py", "sha256": "<sha256>"}],
      "stock_ids": ["pla_stock"]
    },
    {
      "id": "return_loop",
      "name": "Return elastic loop",
      "material": {"family": "elastomer", "specification": "Selected supplier's natural-rubber loop"},
      "process": "purchased",
      "quantity": 1,
      "occurrences": ["return_loop"],
      "specification": "Relaxed flat length 60 mm, width 3 mm, section thickness 1 mm. Loaded behavior remains a physical test.",
      "files": [],
      "stock_ids": [],
      "sourcing": {
        "url": "https://supplier.example/selected-loop",
        "specification": "Replace this example with the actual source and exact selected size."
      },
      "dimensions_mm": {"relaxed_flat_length": 60, "width": 3, "thickness": 1}
    }
  ],
  "stock": [
    {"id": "pla_stock", "name": "PLA filament", "quantity": 45, "unit": "g", "specification": "Blue PLA, total includes stated allowance."}
  ],
  "consumables": [],
  "tools": [
    {"id": "assembly_hook", "name": "Assembly hook", "specification": "Rounded hook for placing the loop without cutting it."}
  ],
  "assembly_steps": [
    {
      "id": "install_loop",
      "title": "Install the return loop",
      "instructions": "Seat the selected loop on the named frame anchors. Confirm its route and inspect for damage before testing.",
      "components": ["frame", "return_loop"],
      "consumables": [],
      "tools": ["assembly_hook"],
      "files": []
    }
  ],
  "public_assets": [
    {"path": "public/assembled.step", "sha256": "<same hash as assembly.step>"},
    {"path": "public/hero.png", "sha256": "<sha256>"}
  ]
}
```

## Field rules

- Component, stock, consumable, tool and step IDs are globally unique lowercase
  identifiers: letters/digits followed by letters/digits/underscore/hyphen,
  at most 128 characters. Occurrence names follow the same grammar but may
  equal the component they represent.
- Supported `material.family` values: `polymer`, `paper`, `paperboard`, `wood`,
  `elastomer`, `foam`, `textile`, `metal`, `glass`, `ceramic`, `composite`,
  `mixed`, `other`. The family is a label; `specification` supplies the actual
  material, thickness, grade, grain/flute, finish or relevant constraints.
  A motor normally has `mixed` material and `purchased` process.
- Supported `process` values: `3d-print`, `laser-cut`, `cnc`, `cut-fold`, `sew`,
  `cut-to-length`, `purchased`, `handcraft`. These describe responsibility and
  preparation, not a claim that a CAM toolchain exists.
- Component `quantity` is a positive integer equal to the number of names in
  `occurrences`, unless a purchased or printed component uses the optional
  `assembly_unit_ids` representation below. Each complete-assembly leaf still
  belongs to exactly one component definition; no missing, extra or multiply
  claimed occurrences.
- The descriptor is a strict JSON `kind: "assembly-package"`,
  `schemaVersion: 2`, `entryKind: "assembly"` document from the CAD assembly.
  Its internal copy must match root `assembled.step.json` byte-for-byte.
  `assembly.step` must likewise match root `assembled.step`. Do not author a
  separate convenient occurrence list to hide components.
  `gen --write` produces the descriptor at
  `cad/__cadgen__/models/<combined-name>.step.py/assembly.json`; it does not
  create a sibling `assembled.step.json`. Copy those exact generated JSON
  bytes to both canonical and internal descriptor paths before the finalizer
  prunes derived caches. Copy the final combined STEP to root
  `assembled.step` and its declared public display path without changing it.
- Every fabricated component has nonempty `files` and `stock_ids`. Source and
  fabrication/assembly documents are hash-bound private files. `purchased`
  components may have empty files and stock IDs, but always require
  `sourcing: {url, specification}` and a nonempty `dimensions_mm` map of named,
  positive dimensions. `sourcing.part_number` is optional. A household marble
  can be specified by source and diameter without inventing an MPN.
- `sourcing` and `dimensions_mm` are optional on other processes. Source URLs
  use public HTTPS and cannot contain credentials. Dimensions are nominal
  declarations, not measured proof. Specify each dimension's meaning in its
  key and the component's text.
- `stock` records total required procurement/preparation quantities and units.
  Describe individual cut lengths, nesting/yield, allowances and consumption
  in component/stock specifications. V1 does not calculate cutting layouts,
  procurement packages or per-component material consumption automatically.
- `consumables` use the same `{id,name,quantity,unit,specification}` fields as
  stock. `tools` have `{id,name,specification}` and are reusable production
  resources. These three inventories may be empty. Quantities must be positive
  finite numbers; units are explicit strings such as `sheet`, `mm`, `g`, `mL`.
- `assembly_steps` is a nonempty array in execution order. Each step names at
  least one known component, every component appears in at least one step,
  and consumable/tool references must resolve. Step `files` bind any additional
  private instructions or evidence. No network fetch is performed.
- Geometry instances have a separate 4,096-item bound: descriptor
  `occurrences`, each component's `occurrences` and `assembly_unit_ids`, and
  hierarchy `children`/`leafPartIds`. This allows many repeated parts or colored
  display regions without adding that many manufacturing definitions.
  Component definitions, stock, consumables, tools, assembly steps, public
  assets and all other lists remain bounded to 512 items.
- Manifest JSON and the occurrence descriptor are each bounded to 2 MiB;
  other referenced files are nonempty regular files no larger than 95 MiB.
  All bounds apply independently: detailed descriptors may reach the byte cap
  before 4,096 occurrences. Duplicate JSON keys, nonfinite numeric values,
  traversal and symlinks fail closed.

Before final independent review, check the generated complete STEP against the
95 MiB per-file bound and the sealed Make tree against its 512 MiB bound. New
mixed Factory imports use the explicit host `factory-mixed-deflate-v1` carrier:
50 MiB compressed, 512 MiB expanded, with the same 95 MiB member limit. It
contains the public assets, extra exact STEP and hero aliases, and host metadata.
Raw totals alone cannot establish its compressed size or acceptance. The host
persists its first exact bytes before import and reuses those bytes on retries;
existing import intents retain their original format. Canonical `workshop pack`
and print carriers remain stored ZIPs with the existing 50 MiB limit. The native
manifest and public projection schemas, asset identities and checks are unchanged.

## Physical units and colored CAD parts

A purchased motor can be one procurement unit represented by several colored
CAD leaves. Preserve its complete imported hierarchy and colors. Do not report
two motors because its body and terminal appear separately, or flatten the
geometry just to satisfy the BOM count.

For a `purchased` component, optionally add `assembly_unit_ids`:

```json
{
  "quantity": 1,
  "occurrences": ["motor_body", "motor_terminal"],
  "assembly_unit_ids": ["o1.2"]
}
```

These are additional fields within the otherwise complete purchased component,
not a replacement component schema. `o1.2` must identify the exact subassembly
node in the sealed descriptor's `assembly.root` hierarchy. Its descendant leaf
IDs resolve through `descriptor.occurrences` to `motor_body` and
`motor_terminal`. Parent display names are not identifiers: two units may both
be named "motor" but have different occurrence IDs.

- `assembly_unit_ids` is a nonempty list of unique exact CAD subassembly IDs,
  such as `o1.2` or `o1.4.1`. Root assembly IDs, individual leaf IDs and unknown
  IDs are refused. IDs contain positive numeric path segments and are bounded
  to 128 characters.
- `quantity` equals the number of selected physical units. Two placed bought
  motors (or two printed copies, as described below) use two distinct
  subassembly IDs, even when their geometry is shared.
- The union of each selected unit's descendant leaves must equal the
  component's existing `occurrences` list exactly. Units cannot overlap or
  include both an ancestor and its descendant. Every product leaf remains
  covered by exactly one component across the complete BOM.
- The hierarchy must agree with the descriptor's leaf IDs/names and each
  node's `leafPartIds`, have unique node IDs with consistent parent paths, and
  cover all rendered leaves exactly once. The opt-in hierarchy check is bounded
  to 64 levels and 8,192 nodes, including the root and leaves. These bounds
  also apply alongside the 4,096-item geometry-list and 2 MiB descriptor caps;
  for example, 4,096 separate subassemblies each containing a leaf would exceed
  the node cap once the root is counted. It reads data only; it never runs CAD.
- Without `assembly_unit_ids`, existing manifests keep the original leaf-count
  rule and do not require hierarchy/occurrence-ID fields. Other fabrication
  processes retain that rule. Grouping does not change the print subset.

The supplier specification still establishes what is bought as a unit. Exact
CAD grouping is structural identity, not proof of supplier packaging, physical
assembly, pricing or performance. The public projection remains unchanged and
never includes these internal procurement relationships.

### One printed part with several display colors

The CAD `organic-lofts` reference supports a fused printable source and a
combined scene that partitions that same solid into disjoint colored regions.
Those regions need not inflate the physical part count. For `3d-print` only,
`assembly_unit_ids` may name one non-root subassembly per physical copy, with
the same exact hierarchy, leaf coverage and quantity rules above. Nest each
copy's regions under its own subassembly in the generated scene; do not invent
descriptor IDs or group several separately manufactured parts into one unit.

Every grouped printed component adds `production_part` with exactly
`source_path` and `step_path`, alongside its unit references and existing files:

```json
{
  "quantity": 2,
  "occurrences": ["body_first", "detail_first", "body_second", "detail_second"],
  "assembly_unit_ids": ["o1.1", "o1.2"],
  "production_part": {
    "source_path": "cad/part_figure.step.py",
    "step_path": "cad/part_figure.step"
  },
  "files": [
    {"path": "cad/part_figure.step.py", "sha256": "<sha256>"},
    {"path": "cad/part_figure.step", "sha256": "<sha256>"}
  ]
}
```

These are fields within an otherwise complete `3d-print` component. Both
`production_part` paths must reference exact hash-bound entries in that same
component's private `files`. It has exactly one `*.step.py` source, named
`part_<role>.step.py`, with a nonempty role and literal `PRINTABLE = True`.
The STEP is that source's generated sibling with only `.py` removed; an
unrelated filename or another directory is refused. Both remain inside the
declared CAD project. Additional private instructions/helper files are allowed,
but another `*.step.py` is not. One source still belongs to one component
definition; repeated copies use its multiple assembly unit IDs.

`production_part` is required for grouped printed components and forbidden on
purchased components, other fabrication processes and ungrouped components.
Neither grouping nor this object runs CAD. The binding establishes declared
production identity, not proof that the colored regions equal the fused part.
Native Make derives the display regions from that same fused source and owns
equivalence, validity, noninterference, print gates and visual review. The
fused production source retains its nozzle-specific checks; the combined
display entry remains `PRINTABLE = False`. Public asset selection and the
host's byte-only publication boundary are unchanged.

Paint and applied finishes belong in consumables and finishing steps, with
quantities, preparation and application details. Where adequate, an authored
color on the real part's leaf shows the finish without changing geometry;
record the underlying printing stock separately. Fine coating solids are not
required. If several colors require display regions, use the disjoint-source
pattern above rather than extra overlapping material volumes. The canonical
renderer currently colors whole leaves, not separate faces within one leaf.

## Print subset and fabrication representations

Every `3d-print` component references at least one `*.step.py` source with an
explicit module-level literal `PRINTABLE = True`. One source belongs to one
component definition; use multiple occurrences for repeated parts.

Nonprinted `*.step.py` files explicitly declare `PRINTABLE = False`, including
the combined review entry. The validator scans the declared CAD project (or
product tree when omitted) and rejects undeclared printable entries or ambiguous
implicit declarations. It parses Python with AST; it never imports or executes
CAD. Production source hashes also change when a flag changes.

Craft methods need source geometry and/or precise production documents in their
`files`, with dimensioned cut/fold/assembly details in their specifications. A
cardboard panel can have a thin STEP representation plus a dimensioned PDF or
Markdown instruction file. STEP remains the only geometry deliverable. V1 does
not support mesh delivery, DXF, DWG, G-code or NC/CAM output.

## Public projection

Only explicitly listed files beneath `public/` may be published for an opted-in
product. Include a complete assembled STEP (same bytes as `assembly.step`) and
at least one finished-product image. Individual production STEPs cannot be
substituted for the assembled product. Paths are unique and hash-bound.

Allowed formats: STEP/STP; PNG/JPEG/WebP/GIF; MP4/WebM; PDF; UTF-8 Markdown,
plain text or static HTML. File signatures reject obvious type disguises.
JSON, Python/source, BOM and private manufacturing files cannot be allowlisted.
No hidden directories, symlinks, parent traversal or remote code is allowed.
Public customer-document resource links must resolve to another allowlisted
public asset; external links are public HTTPS without credentials. HTML is
static and cannot contain executable scripts, embedded applications or event
handlers. Author public content specifically for the finished product. Format
and link checks do not semantically certify that arbitrary prose is appropriate
customer copy.

Keep root facts/customer prose free of internal BOM content. A private plan
copied into a public document is still a disclosure, even if its extension is
allowed. The caller must use this public projection for the Factory carrier,
archive and optional customer document, not copy the full Make tree.

For executable synthetic examples, see
`tests/make/test_manufacturing_manifest.py::make_mixed_product`. Those fixtures
exercise structural contracts and are not physical or rendered-product evidence.
