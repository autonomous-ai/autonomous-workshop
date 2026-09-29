# Component selection

Read this reference when choosing or replacing a motor, servo, solenoid,
battery, converter, controller, switch, connector, LED, lamp, light module or
other carried electrical hardware. The goal is not the closest catalog name;
it is an exact purchasable part whose complete powered and physical integration
is supported by evidence.

## The selection method

The contract fields, what counts as evidence, the hard gates (functional,
electrical, physical, integration, evidence, procurement), preference ranking
and the substitution rule are design knowledge:
`skills/wiki/pages/electronics/electrical-component-selection.md`
(`wiki show electrical-component-selection`). Follow it in this order: write
the contract with tagged values, compare exact MPN candidates, mark every
hard gate `pass`/`fail`/`unresolved` with its evidence, rank only survivors on
the user's stated priorities, and record the chosen MPN, the nearest viable
alternative and what would make it preferable.

## Close the decision in CAD

Download the chosen exact STEP into `<project>/ref/` and record its URL,
revision, license or terms and SHA-256. If no exact STEP exists, create a
`validation_envelope` from the manufacturer drawing and keep its dimensions and
provenance beside that artifact.

Derive the seat and bolt pattern from that STEP with `cadmount`; derive mating
clearance once through `cadfits`. Include the connector, cable bend, service
loop, strain relief, removal space and thermal clearance in the modeled handoff.
Then use:

- `check_power` for ratings and complete source-to-return paths;
- `check_mount` for seated clash, clearance and bolt access;
- `check_motion` for insertion, retention and removal paths;
- a real-hardware fit coupon or prototype before claiming physical fit where
  manufacturing tolerance, contacts or compliant retention matter.

Changing the MPN reopens the selection contract and these CAD checks
(`wiki show electrical-component-selection#a-substitution-reopens-everything`).
