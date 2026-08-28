# Component selection

Read this reference when choosing or replacing a motor, servo, solenoid,
battery, converter, controller, switch, connector, LED, lamp, light module or
other carried electrical hardware. The goal is not the closest catalog name;
it is an exact purchasable part whose complete powered and physical integration
is supported by evidence.

## Write the selection contract before searching

Translate the product request and approved exterior into measurable constraints.
Tag each value `[observed]`, `[inferred]`, `[assumed]` or with an authoritative
source. Do not silently turn an unknown into a convenient number.

Record, as applicable:

- required output and duty: torque, speed, force, travel, optical function,
  brightness or another load-specific measure, including the worst case;
- source minimum/nominal/maximum voltage, continuous and peak demand, control
  interface and required protection or driver;
- maximum component envelope, mounting datum, output/optical axis, fastener or
  retention strategy and allowed mass;
- insertion and removal direction, connector mate/unmate envelope, wire bend
  room, service loop, strain relief and access for tools or fingers;
- thermal, environmental, noise, lifetime or compliance constraints that are
  actually in scope;
- procurement constraints stated by the user, such as region, budget,
  availability or approved manufacturers.

If an unresolved choice changes the power boundary, requested function or
approved exterior, obtain the user's decision. Otherwise preserve the
uncertainty and show whether it changes the selection.

## Compare exact candidates, not families

Search exact MPNs and manufacturer aliases. For each plausible candidate,
record the manufacturer page or datasheet revision, component-search outcome,
CAD source and revision, and which values are still unresolved. A generic
family page, distributor title or visually similar STEP can discover a
candidate but cannot prove its ratings or mating geometry.

Do not accept the first catalog hit. Compare the viable candidates; when only
one remains, name the nearest rejected alternative and its first failed gate.
Do not invent a fixed candidate count when the market genuinely offers fewer
qualified parts.

## Decide in two stages

### 1. Hard gates

Mark each gate `pass`, `fail` or `unresolved`, with the evidence that produced
that result:

- **Functional:** rated output and duty cover the requested worst case.
- **Electrical:** the full source range is contained by the load and every
  inline component; continuous and peak capacities cover demand; the control
  interface is compatible.
- **Physical:** the exact part plus connector, cable and service envelopes fit
  the available space without changing the approved exterior; mounting datum,
  output axis and insertion/removal path are usable.
- **Integration:** protection, driver/controller, mating connector, mounting,
  strain relief, service access and required heat rejection have implementable
  paths.
- **Evidence:** the exact MPN and relevant revision have authoritative ratings
  and a manufacturer drawing, exact STEP or documented validation envelope.
- **Procurement:** any user-declared cost, region, lead-time or vendor rule is
  met.

A `fail` rejects the candidate. An `unresolved` blocks final selection when the
unknown could cause a gate to fail. Do not average a hard failure into a total
score.

### 2. Preferences

Rank only the candidates that passed every applicable hard gate. Use the
user's priorities—for example mass, efficiency, noise, thermal margin, price,
availability, serviceability or evidence quality—and state their ordering or
weights before scoring. Do not present arbitrary default weights as user
requirements. Prefer the candidate with useful margin over one that merely
equals a nominal value, but do not oversize it so far that mass, startup current,
driver size or heat creates a new integration problem.

Record the chosen MPN, why it wins, the nearest viable alternative and what
would make that alternative preferable. This keeps a later supply substitution
from becoming an unaudited geometry change.

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

Changing the MPN reopens the selection contract and these CAD checks. Similar
overall dimensions do not make a component a drop-in replacement.
