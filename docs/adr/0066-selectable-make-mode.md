# ADR 0066: Selectable print and mixed Make modes

- Status: Accepted
- Date: 2026-09-11
- Owners: Make, CLI, runtime packaging and Workflow
- Refines: ADR 0067 for newly selected runs; existing runs retain its opt-in contract

## Context

Some creators want products they can make with a 3D printer. Others have access
to stock materials, laser cutting, woodworking, textiles and purchased parts.
Enabling mixed-material Make globally silently expands the first group's scope.
The operator requested a short CLI choice and 3D printing as the default.

## Decision

`workshop wish "..." --make print|mixed` selects Make independently of the
workflow, inventor, model and reasoning effort. The default is `print`.
`workshop start` forwards the same choice into each product it starts. Mixed
Make is supported only with Spark in this MVP; incompatible workflows are
rejected before starting work. This does not expand Daydream's creative scope.

Every new CLI run freezes an immutable root `MAKE.json` containing exactly
`{"schema_version":1,"mode":"print"}` or the equivalent `mixed` selection.
The exact bytes are bound by the existing input manifest and native session
identity. Stage packets expose the same mapping as `inputs.make_mode`; receipts
expose its mode as `make_mode`. Native inventor selection and creation obey it.

Print Make designs printed product components with the established CAD and
print checks. It omits the `mixed-materials` domain skill and refuses a mixed
manufacturing marker. Make's own finalizer requires printable production
sources and refuses explicitly nonprinted production entries; it uses the
canonical print-source discovery without executing product CAD. Reference and
combined assembly geometry can remain nonprintable. Scope checks do not prove
printability or replace Make's engineering and visual evidence.

Mixed Make includes the mixed-material skill and requires its versioned
manufacturing manifest, complete assembly and explicit public asset selection.
The workshop receives the internal BOM and fabrication/assembly instructions;
the customer sees the complete finished product. Print checks cover the printed
subset. Physical fabrication and testing remain Operations work.

The host checks the selected output contract's marker shape and presence while
sealing exact bytes. It adds no second CAD, BOM, visual or engineering review.
Both choices use the same native session and Spark lifecycle; shared CAD tools
remain shared instead of being forked into two engines.

## Compatibility

`resume` offers no mode override. Tool refresh retains the frozen selection
and cannot add mixed-material capabilities to a selected print run. Existing
runs without `MAKE.json` remain explicitly unselected in status and retain
their original material scope, tool roster and manifest opt-in behavior. This
includes the six running mixed-material pilots. They are not relabeled print
and need no workspace mutation or restart.

The library's optional `make_mode=None` preserves legacy programmatic callers;
the CLI always passes the selected mode, including its default. Unknown values,
malformed selections and changed or missing frozen bytes fail closed.

## Verification

Deterministic tests cover CLI defaults and forwarding, invalid selections,
frozen input/session identity, stage packets, mode-specific materialization and
refresh, legacy resumes, and both passing and rejected Make output contracts.
No test result claims manufacture or live publication.
