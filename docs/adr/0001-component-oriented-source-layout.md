# ADR 0001: Component-oriented source layout

- Status: Accepted
- Date: 2026-08-25
- Owners: Repository maintainer and all component DRIs

## Context

The original Python implementation grew as one flat `inventor_workshop`
package. Stage contracts, agents, persistence, Factory behavior, CAD resources,
and CLI concerns became interwoven. A contributor could not identify one home
for Make, Playtest, or another Workshop responsibility, and broad modules such
as `jobs.py`, `models.py`, and the package root became merge-conflict points.

The project needs clear individual ownership while retaining one coherent
Workshop library. Publishing generic packages such as `make` and `match` at the
repository root would create ambiguous imports and imply independently released
products that do not exist.

## Decision

Keep the Python `src` layout and use `workshop` as the single library namespace:

```text
src/
├── workshop/
│   ├── wish/
│   ├── match/
│   ├── invent/
│   ├── make/
│   ├── playtest/
│   ├── instructions/
│   ├── deliver/
│   ├── reviews/
│   ├── workflow/
│   ├── product/
│   ├── artifacts/
│   ├── runtime/
│   ├── integrations/
│   └── contributors/
└── cli/

tests/
├── <mirrored owner directories>/
├── architecture/
├── packaging/
├── integration/
└── end_to_end/
```

The distribution remains `autonomous-workshop`; public library imports begin
with `workshop`; the installed command remains `workshop`; and `cli` is an
internal application package.

Every component owns:

- its public contracts and implementation;
- a concise component README;
- component-specific schemas, skills, fixtures, and adapters;
- its mirrored top-level test directory.

The root test categories own concerns that genuinely span components or an
installed distribution. No tests live inside `src/`.

## Alternatives considered

### Keep one flat package

Rejected because file ownership remains ambiguous and central modules continue
to accumulate unrelated contracts.

### Remove `src/`

Rejected because tests could import the checkout accidentally, hiding missing
package data, undeclared dependencies, and differences from an installed wheel.

### Put every component at the repository root

Rejected because generic top-level Python names collide easily and obscure the
single Workshop product boundary.

### Treat skills as the component architecture

Rejected because skills are versioned executable resources used by a component,
not owners of Python orchestration, state, or public contracts.

## Consequences

A component contributor has two predictable code/test locations and one clear
DRI. Cross-component behavior becomes visible in import and integration tests.
The repository retains some deliberate nesting, but that nesting represents
real packaging and product boundaries rather than duplicate ownership.

Component package roots are the canonical APIs. The root `workshop.__init__`
retains the established 0.x convenience surface through the 0.x line, but it
only re-exports component-owned values and is not a second ownership unit. New
code imports `workshop.wish`, `workshop.make`, `workshop.workflow`, and the
other documented component boundaries directly. Broad `jobs.py`, `models.py`,
`core`, `foundation`, `common`, and `utils` modules are not accepted as
permanent ownership units.

## Compatibility and migration

The source package rename from `inventor_workshop` to `workshop` is a Python API
change. It does not authorize renaming historical serialized identifiers,
rewriting durable state, or changing artifact bytes. Temporary forwarding
modules may keep migration commits green, but they contain no behavior and have
a documented removal release.

## Verification

- Build and install wheel and sdist outside the repository checkout.
- Confirm only intended top-level packages are installed.
- Confirm all skills and schemas are present with their locked bytes and modes.
- Enforce component ownership and dependency rules in architecture tests.
- Run component, integration, end-to-end, CLI, and packaging suites.
