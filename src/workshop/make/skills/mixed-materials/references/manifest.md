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
  `occurrences`, unless a purchased component uses the optional
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
- Lists are bounded to 512 items; manifest JSON is bounded to 2 MiB; each
  referenced file is a nonempty regular file no larger than 95 MiB. Duplicate
  JSON keys, nonfinite numeric values, traversal and symlinks fail closed.

## Purchased subassemblies: physical units and colored CAD parts

A purchased motor can be one procurement unit represented by several colored
CAD leaves. Preserve its complete imported hierarchy and colors. Do not report
two motors because its body and terminal appear separately, or flatten the
geometry just to satisfy the BOM count.

For a `purchased` component only, optionally add `assembly_unit_ids`:

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
  motors use two distinct subassembly IDs, even when their geometry is shared.
- The union of each selected unit's descendant leaves must equal the
  component's existing `occurrences` list exactly. Units cannot overlap or
  include both an ancestor and its descendant. Every product leaf remains
  covered by exactly one component across the complete BOM.
- The hierarchy must agree with the descriptor's leaf IDs/names and each
  node's `leafPartIds`, have unique node IDs with consistent parent paths, and
  cover all rendered leaves exactly once. The opt-in hierarchy check is bounded
  to 64 levels and 2,048 nodes. It reads data only; it never runs CAD.
- Without `assembly_unit_ids`, existing manifests keep the original leaf-count
  rule and do not require hierarchy/occurrence-ID fields. Printed and fabricated
  components retain that rule; this option does not change their print subset.

The supplier specification still establishes what is bought as a unit. Exact
CAD grouping is structural identity, not proof of supplier packaging, physical
assembly, pricing or performance. The public projection remains unchanged and
never includes these internal procurement relationships.

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
