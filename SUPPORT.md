# Support

## Before opening an issue

1. Read the repository README and the component README nearest the problem.
2. Search existing issues for the error text or affected command.
3. Reproduce from a clean environment using a supported Python version.
4. Remove credentials, customer content, private artifact URLs, and local
   machine details that are not necessary to understand the problem.

## Where to ask

- **Bug or regression:** open a GitHub issue with the commit or version, exact
  command, expected behavior, actual behavior, and a minimal sanitized fixture.
- **Feature or component design:** open an issue naming the owning component
  from [MAINTAINERS.md](MAINTAINERS.md), the user outcome, and the boundary that
  would change.
- **Inventor contribution:** follow `docs/BUILD_AN_INVENTOR.md` and include the
  Taste lane and customization level.
- **Security, leaked secret, unauthorized effect, or private conduct report:**
  use [SECURITY.md](SECURITY.md); do not open a public issue.

## What maintainers can support

Maintainers support reproducible behavior in the current release and `main`,
the documented offline path, bundled schemas and skills, and checked-in
inventor profiles. Support is best-effort and has no response-time guarantee.

Provider accounts, printers, slicers, CAD installations, carrier agreements,
marketplace access, and operating-system configuration remain the operator's
responsibility unless a defect reproduces behind the Workshop's documented
provider boundary. Never share a live credential to obtain help.

Historical labs and imported snapshots document provenance and prior work.
They are not maintained as general-purpose applications unless their own
README explicitly says otherwise.

## Useful issue details

Provide the smallest useful set:

- Workshop version or commit;
- Python and operating-system versions;
- component and command;
- sanitized input or fixture;
- complete traceback or structured error;
- whether the problem reproduces offline;
- checks already run.

Replace secret values rather than partially masking them. If a real secret was
ever posted or committed, rotate it immediately and report it privately.
