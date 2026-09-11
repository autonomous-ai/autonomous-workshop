# Mixed-material Spark MVP

Date: 2026-09-10.

**Implementation status: initial code implemented in `make/mixed-material-products`,
with deterministic contract tests and a real CAD tool smoke check.** The
manufacturing manifest, printed-subset checks and private/public handoff are
implemented. All six live CLI pilots are under evaluation; completed products and human
prototype work remain pending. Live commands and outcomes are tracked in
[the CLI run record](mixed-material-cli-runs.md). The material study is
[KiwiCo materials research](kiwico-materials-research.md).

## Accepted product brief

Autonomous is an AI × human collaboration workshop that creates original
finished products at the scale and mechanical complexity of KiwiCo references.
The AI designs the product and its engineering package. Autonomous's internal
engineers and workshop staff source components, fabricate parts, assemble,
test, finish and ship the completed product.

The MVP is a **small collection of different original finished products**, not
only a generic material schema. Together, the products should demonstrate the
researched KiwiCo material families through purposeful combinations: an
AI-native KiwiCo 2.0 made and assembled inside Autonomous. The six pilots below
are proposed Wish recipes and coverage targets, not generated products or
claims of manufacturing readiness.

The internal workshop has 3D printing, laser cutting, CNC, woodworking and
fabric capabilities. Design should use an appropriate combination rather than
making additive manufacturing the default for every component. Paperboard,
wood, felt, fabric, cord, elastic bands, springs, hardware and simple bought
functional components are legitimate parts of one product.

The customer sees a beautifully presented **complete product**, following the
finished-product presentation of
[Civic Skyline](https://www.autonomous.ai/toys/product/civic-skyline). This brief
does not ask the customer to source parts, print pieces or assemble a kit. BOMs,
supplier details, manufacturing files, stock/cut lists and assembly/test
instructions are internal operations information. The public site may describe
materials as part of the product's appearance or experience; it must not turn
that description into a public manufacturing workspace.

Scope is **Spark and Make only**. Spark retains `Wish -> Make -> Release`, with
Make owning creative and engineering work and the host publishing its existing
approved public assets. This work adds no lifecycle stage, Forge/Quest support,
Daydream expansion or second agent framework. Physical operations follow the
Workshop handoff; this MVP does not move factory workers into the native agent
session or claim automated fabrication.

## Bounded portfolio palette

Start with passive mechanisms and mixed rigid/soft/flat assemblies: printed
connectors and custom shapes; cut board/wood panels; dowels and rods; cord,
felt/fabric, rubber bands, springs, fasteners and play objects such as marbles.
Simple powered variants may use specified battery holders, cells, switches,
motors or gearmotors, lights and insulated leads/connectors. Existing mount and
power evidence should support those assemblies.

Raspberry Pi, custom PCBs, firmware development, wireless networking and broad
robotics are outside the MVP. The collection must cover the researched families,
including textiles, clay/plaster and simple purchased optical or powered parts.
Material/process support must be added and demonstrated before a corresponding
pilot is considered complete. KiwiCo products are references for functional
combinations and craft methods; Workshop products must have original designs.

## Proposed original pilot collection

**Portfolio status: all six pilots launched through the CLI; Make work is in
progress. None is yet claimed fabricated or physically tested.** The MVP is a collection of compelling interactive products,
not a collection of material demonstrations. Each starts from a successful
play/mechanism category and seeks an original interaction, silhouette and repeat
play loop. “Stronger than the reference” is an ambition until comparable physical
trials support it. These names are working titles, not published product names.

The six pilots are independent Spark products. Dependencies below describe
implementation and internal prototype order, not additional lifecycle stages.
Their Wish outlines become launchable recipes only after the relevant contract,
tools, private handoff and public presentation behavior have been proven.

| Reference benchmark | Capability to demonstrate | Original pilot and distinctive interaction | Repeat-play loop | Measurable human prototype tests |
|---|---|---|---|---|
| Pinball Machine | Predictable rolling, flippers, elastic energy, mechanical targets | **P1 Harbor Relay Pinball:** captured deliveries change a visible harbor route and open a final destination | Choose a route, launch a limited set of balls, complete deliveries, reset and improve | Successful launches/target registrations, stalls per trial, flipper return, measured ball size and operating force |
| Marble Roller Coaster | Lift, gravity routing, transfer reliability, repeatable circulation | **P2 Cloudline Coaster:** marbles take selectable skyline routes whose bascule transfer moves visibly | Change a route, predict the destination/timing, run repeated circuits | Circuit completions, transfer failures, lift slip, motor load/runtime, timing across route settings |
| Domino Machine / Chain Reaction Workshop | Modular physical signals, energy transfer, reconfiguration | **P3 Switchyard Relay:** two domino/ball paths compete or cooperate to reach a shared mechanical signal | Build routes, predict which signal arrives first, trigger, diagnose, reconfigure | Trigger force/travel, module-to-module success rate, repeat timing, false releases and reset reliability |
| Drawing Machine / Programmable Music Box | A repeatable mechanical program and meaningful material-dependent output | **P4 Rainmark Studio:** one crank-driven rhythm strikes chimes and stamps its visible beat pattern into a sand disc | Set a phase/rhythm, predict the pattern, listen and inspect, erase and change | Missed/double notes, mark visibility, alignment of sounds/marks, crank effort, repeat consistency |
| Moving Creature / Plane Launcher | Lightweight character form, elastic propulsion, trim and trajectory | **P5 Liltwing Flight Garden:** a moth-shaped foam glider carries a paper message toward fabric landing meadows | Choose a destination, adjust trim/launch setting, send, observe and retry | Launch repeatability, flight/landing dispersion, payload sensitivity, trim effect, impact and reset behavior |
| Mechanical Lock Box / puzzle mechanisms | Legible physical state, tactile/optical clues, mechanical interlocks | **P6 Atlas Vault:** rubbing a cast terrain clue and viewing its reflection reveal the dial order that opens an original landscape box | Solve a clue route, open, change the internal clue configuration, challenge another player | Correct/incorrect unlock trials, jam rate, dial torque, clue legibility, part registration and wear |

### P1. Harbor Relay Pinball — first manageable mechanical pilot

**Wish outline:** Make a finished tabletop pinball harbor with two generous
flippers and three delivery docks. A captured ball should raise its dock's
paper signal and change a clearly visible gate; completing the deliveries opens
the final lighthouse destination. The player gets a small, defined set of balls
before resetting. Create an original curved harbor silhouette and satisfying
mechanical feedback. Deliver an assembled product, with manufacturing details
reserved for Autonomous staff.

**Components/processes:** CNC/woodworked base and dowels; a specified smooth
playfield; printed flippers, rails, gates and custom joints; laser-cut
wood/chipboard structures; folded card/paper signals; bought marbles, elastic
bands, a sourced plunger/return spring as designed, metal axles and hardware;
felt catch lining, foam stops, rubber feet, paint and suitable adhesives. The
playfield material must earn its choice through rolling/flatness trials; a
cardboard scene does not require a cardboard rolling surface.

**Signature:** A ball visibly changes the harbor's state and the next shot's
possibilities. Board, paper, felt and elastic have real jobs. This pilot proves
a complete mixed-material game without attempting every portfolio material.

**Physical checks:** Count successful launches, flipper returns and dock
registrations across repeated games; measure ball diameters, launch/flipper
force and unintended stalls. Inspect impact joints, board distortion and reset
access. A rendered dock mechanism is a proposal until those observations exist.

### P2. Cloudline Coaster — a changing marble transport network

**Wish outline:** Make a finished motorized marble skyline where a slow lift
feeds two selectable gravity routes. A visible bascule should transfer marbles
between levels, and route settings should produce visibly different journeys.
One simple switch runs the lift; the child predicts and changes destinations.
Avoid copying a reference coaster's track plan, outline or lift decoration.

**Components/processes:** CNC/laser wood towers; printed tracks, lift carriers,
switches and bascule pivots where justified; purchased marbles; specified rigid
or clear-plastic track inserts; silicone/rubber traction elements; foam/felt
quiet catches; metal rods, springs and fasteners; simple DC gearmotor, battery
holder, switch and insulated leads. Sheet machining, tube/rod cutting and
measured module mounting belong in the internal operation sequence.

**Signature:** Selecting a path changes where and when a marble joins the
skyline's circulation, rather than only changing a static display.

**Physical checks:** Record complete circuits and failure locations; test lift
slip, bascule reset and track joins across actual marble samples. Measure loaded
motor behavior, runtime and jam response under specified conditions. Compare
route timing against the promised play choices.

### P3. Switchyard Relay — a game of competing physical signals

**Wish outline:** Make a finished modular tabletop signal game containing
original tipping, rolling, spring-transfer and flag modules, plus dominoes.
Players arrange two paths to make one signal arrive first or both meet at a
shared mechanical finish. Use a common interface that makes reconfiguration
clear. Include bounded challenge cards with multiple possible solutions.

**Components/processes:** Wood base/modules and dominoes; printed clips,
tracks, guides and interlocks; metal springs, axles, wire and hardware; rubber
bands, cord and foam bumpers; paper/chipboard flags and cards. Captured magnets
and ferrous counterparts may register modules when their retention is verified.
Soft felt catch areas complete the play board. Manufacture and supply enough
complete modules for a meaningful game, rather than asking customers to source
household parts.

**Signature:** Independent routes become competing or cooperating messages;
players reason about timing and energy, then see exactly where a chain succeeds
or stops.

**Physical checks:** Measure the input force/travel each module needs and the
output it supplies; repeat transfers in several valid configurations; count
false releases, incomplete resets and unintended detachments. Check route
repeatability and whether the supplied challenge cards have physically working
solutions.

**Coverage limit:** This demonstrates domino interaction and chain-reaction
composition. An automated moving domino dispenser is a separate, currently
unplanned extension; it is not implied by including dominoes.

### P4. Rainmark Studio — hear a rhythm and see its trace

**Wish outline:** Make a finished hand-cranked rhythm machine whose repeating
mechanical pattern strikes a small set of wooden/metallic notes and stamps
corresponding marks into a slowly rotating shallow sand disc. A large phase
control changes the rhythm. The child can hear the motif, inspect its circular
score, sweep the disc clean and make another. Use one coherent mechanical
program for both outputs; omit an output if it cannot be made reliable and
record the resulting portfolio gap.

**Components/processes:** CNC wood housing; printed cams, gears, disc and
linkages; wooden hammers; sourced brass tubes or other specified metal
resonators; formed-wire suspension; springs; rubber drive/feet; felt damping;
specified sand/play medium; silicone reset blade; clear-plastic guard; paper
experiment cards, finish and hardware. Tube cutting, wire forming, acoustic
adjustment and sand-medium selection are explicit workshop processes.

**Signature:** The same physical events become an audible rhythm and a visible
record, so changing phase produces a discoverable relationship rather than two
unrelated toys sharing a housing. There are no electronics or software controls.

**Physical checks:** Count missed/double strikes and unclear marks; compare
sound timing with disc marks over repeats and control settings; measure crank
effort and reset quality. Select sand by measured marking/flow behavior; test
containment, cleanability and separation from gears. A nonworking sand recorder
cannot be replaced with a generated animation and called demonstrated.

### P5. Liltwing Flight Garden — send a tiny message through the air

**Wish outline:** Make a finished moth-shaped glider game with a bounded
hand-operated elastic launcher and three distinct soft landing meadows. A light
paper message travels with the glider. Players choose a meadow, adjust a simple
trim setting and send the moth on a visible flight. Give the aircraft and its
landscape original forms, and make a successful landing feel like a delivery.

**Components/processes:** Cut foam wings, a light printed nose/trim fitting,
card/paper tail and message carrier, specified elastic or spring launch
mechanism, wood launcher frame, rods/fasteners and cord as needed. Fabric/felt
meadows and yarn/cord markers give the target areas tactile structure and
retrievable message pockets. Rigid/transparent plastic can expose the launch
setting. Fabric work is an internal cut/sew operation, not customer assembly.

**Signature:** A tiny delivered message makes tuning the flight purposeful.
Wing compliance, mass distribution, payload and launch energy must be designed
together; do not replace the foam aircraft with an untested heavy printed form.

**Physical checks:** Record launch repeatability and landing dispersion;
compare trim effects and payload sensitivity; measure operating effort; inspect
wing/nose damage and launcher retention after repeated use. Test whether the
three target choices create distinguishable, attainable challenges.

**Coverage limit:** This covers character-led flight. Articulated walking,
crawling or flapping robots remain a future benchmark; the static glider is not
claimed to demonstrate those mechanisms.

### P6. Atlas Vault — a tactile and optical landscape puzzle

**Wish outline:** Make a finished mechanical puzzle box that resembles an
original miniature archipelago. Its terrain hides tactile patterns: a paper
rubbing and a simple mirrored view reveal the order for a set of large
mechanical dials. Solving that order releases a concealed compartment. Provide
several reconfigurable clue routes so the owner can set a new puzzle for someone
else without sourcing materials or disassembling the mechanism.

**Components/processes:** CNC/laser wood box; printed interlocks, dials, clue
holders and original molds/jigs; cast plaster relief tiles; specified
paper/air-dry clay scenery or tactile markers, and polymer-clay keys/characters
where a firm small form serves the puzzle; paper/card clue strips; a sourced
mirror and clear-plastic viewing insert; a simple bought battery/switch light
for the enclosed clue chamber; felt pads, metal hardware, magnetic
registration if required, paint and adhesives. Modeling clay may be an internal
master-making aid. The actual clay subtypes and supplier-specific cure/bake
processes must be recorded rather than assuming all clays are interchangeable.

**Signature:** Players transform a three-dimensional clue into a readable trace
and reflection, then see a real mechanical state change. Plaster relief, clay
markers and paper are required puzzle information, not decorative materials
added to satisfy a checklist. Internal molds and tools do not ship as play items.

**Physical checks:** Measure correct/incorrect unlocking and dial torque;
check clue legibility, reflected ordering, rubbing quality and tile alignment;
inspect chipping, shrinkage, coating wear and retained-part integrity. Verify
that reconfigured clue routes lead to the intended combinations. If fragile
cast parts cannot withstand intended handling, revise the construction and keep
that material capability pending.

## Planned material and process coverage

This matrix is a **planned coverage checklist**, not a built/tested BOM.
Reference evidence means the family was disclosed in the linked
[research](kiwico-materials-research.md); household DIY evidence remains distinct
from retail inventories. It does not establish every KiwiCo catalog item,
proprietary formulation, grade or supplier. A completed row requires an actual
selected material, fabrication record and relevant physical observation.

| Researched family / component | Pilot and necessary role | Planned fabrication / sourcing process | Evidence boundary |
|---|---|---|---|
| Wood and dowels | P1 play structure; P2 towers; P3 modules; P4 resonators/base; P5 launcher; P6 box | CNC, laser cutting, woodworking, drilling and joining | Wood disclosed across kits; species/lamination generally unknown. |
| Cardboard / chipboard | P1 harbor structures; P3 flags; P5 message structures; P6 clues | Select stock, cut, score, fold and join | Village-kit chipboard and separately documented cardboard DIY mechanisms. |
| Paper / cardstock | P1 signals; P3 challenge cards; P4 experiments; P5 messages; P6 rubbings | Print/cut/fold; supply replaceable play stock | Several paper mechanisms and plant/graphic sheets; weight not universal. |
| Felt / fabric / canvas | P1/P2 catches; P3 play surface; P4 damping; P5 landing pockets; P6 pads | Cut, sew, edge-finish, pad and attach | Felt, cotton/canvas and plush examples; actual fibers must be selected. |
| Yarn / cord / string | P3 transmission; P5 textile target construction and messages | Cut-to-length, knot, sew, route and tension | Arcade, macrame and supply kits; yarn fiber often undisclosed. |
| Foam | P1/P3 stops; P2 quiet catches; P5 aircraft | Select density/stiffness, cut and bond | Explicit foam components; not universally EVA or one density. |
| Rubber bands / pads | P1 flippers; P2 traction; P3 return mechanisms; P4 drive/feet; P5 propulsion | Source specified elastic/stock; fit and measure | References use rubber for different physical jobs. |
| Silicone | P2 traction sleeve as designed; P4 sand reset blade | Buy/cut suitable sheet or tubing and fit | Silicone tube and silicone objects are verified families; grade unassigned. |
| Metal fasteners / axles | P1–P6 moving joints and assembly | Source exact dimensions; drill, fit, fasten and inspect | Brads, nuts, bolts, screws and washers are disclosed. |
| Springs | P1/P2 returns; P3 signal transfer; P4 striker return; P5 launcher if selected | Source measured component; mount and limit travel | Type/rate/preload must be specified, not inferred from the word spring. |
| Metal wire / tubing | P3 signal link; P4 resonators and suspension | Cut, bend, deburr and attach | Himmeli brass tubes and floral/aluminum wire; exact alloys/gauges unknown. |
| Rigid / clear plastics | P1 smooth surface if selected; P2 tracks; P4 guard; P5 setting window; P6 viewer | Source suitable sheet/components; supported cutting/machining and joining | Plastic explicit; clear appearance does not prove acrylic. |
| Mirrors / optics | P6 clue transformation | Source measured insert, mount and adjust | Kaleidoscope mirrors disclosed; substrate/coating need selection. |
| Motors / batteries / switch / leads | P2 marble lift | Source compatible bounded modules; mount, connect and test | Simple powered kits; operating ratings require actual specification. |
| Light | P6 enclosed clue illumination | Install/test a bought battery/switch light module | Verified light products; the enclosed clue chamber gives illumination a required optical role. |
| Marbles / rolling play objects | P1 shots; P2 circulation; P3 signals | Source dimensions/mass; test path and capture | Marble products; ball material not consistently disclosed. |
| Sand / play medium | P4 visible rhythm record | Select medium, meter quantity, contain and test | Sensory-sand product disclosed; formulation/flow are not universal. |
| Magnets / ferrous counterparts | P3 module or P6 clue registration | Source, capture and test alignment/retention | Passive magnetic DIY evidence; no assumed grade/pull strength. |
| Clay family | P6 clue pieces and possible internal masters | Sculpt/mold; air-dry or bake according to selected medium | Paper, air-dry, modeling and polymer clay documented separately; report actual subtypes used. |
| Plaster | P6 information-bearing relief tiles | Original mold, mix/cast, cure, demold and finish | Plaster/plaster of Paris supported; cement not substantiated. |
| Paint / adhesives / tape / finish | Product-specific surface information and joints throughout | Prepare surfaces, apply measured material, cure and inspect | Craft families verified; compatibility and chemistry need selection. |
| Printed polymer | Custom interfaces/mechanisms or tooling in P1–P6 | Make source/STEP design and supported print checks | Autonomous manufacturing choice, not a claim of printed retail KiwiCo parts. |

Process coverage is deliberate: P1 proves a complete passive game and ordinary
CNC/laser/wood/board assembly; P2 adds simple motor integration; P3 adds modular
signal/elastic interfaces; P4 adds tube/wire work, acoustic tuning and granular
medium behavior; P5 adds flight-critical foam work and fabric sewing; P6 adds
optical mounting, molding, casting, sculpting and finishing. Additive
manufacturing supports bespoke mechanisms and tooling throughout.

## Sequence, coverage gaps and completion evidence

Begin P1 after digital contract and public/private transport checks pass. P2 and
P3 then exercise bounded powered and modular mechanisms. P4 requires working
cam/transmission and material trials; P5 requires a measured lightweight
propulsion design; P6 requires supported casting, clay and optical assembly
instructions. These are readiness dependencies for independent Spark Wishes,
not new workflow paths or permission to launch pilots from this document.

The six pilots aim to cover the researched families across distinct playful
products. They do not yet cover every KiwiCo mechanism or every material
subtype. Automatic domino laying, articulated walking/crawling/flapping,
hydraulic/pneumatic play, and a qualified example of each separate clay
formulation remain explicit gaps. The required P6 clue illumination must be physically demonstrated; it cannot
be counted from an unused BOM option. Likewise, a magnet or silicone alternative that is never installed
cannot count as completed coverage.

Do not add materials to a product solely to close a row. If a required family
cannot earn a useful role in these games, propose an additional original pilot
and explain its experience before adding scope. Track each pilot separately as
specified, digitally checked, internally fabricated, assembled, physically
tested and (only with real evidence) shipped. A material fixture is useful
infrastructure but cannot stand in for this original product collection.

## Authorized CLI launch recipes

The six pilots were originally launched through the CLI with Spark, Codex Astra,
ultra reasoning effort and a 100,000,000-token allowance per product. The user
subsequently authorized **medium effort and a 500,000,000-token total allowance
per existing product**, preserving the original sessions and consumed tokens.
The six updated allowances total 3,000,000,000 tokens; usage is accounted per
run, and these are ceilings rather than targets. The authoritative
[CLI pilot record](mixed-material-cli-runs.md) contains the exact commands,
selected Inventors, Dee account connections, run IDs, failures and resumes.

The operator launches and monitors all runs; the recipes add no scheduler or
workflow route. Use the documented `status` and `resume` commands to inspect
or continue an existing session. Ordinary resumes keep the saved settings;
apply explicit operator changes with `resume --effort medium --max-tokens
500000000` through the host, as described in ADR 0065. Fix observed
Make implementation failures in the builder checkout with focused validation;
a repository edit does not silently rewrite a running product's frozen skill
bytes. Monitor the real runs for contract, engineering, complete-product visual
and public/internal separation failures without inventing completed evidence.

## Proposed Make-owned product model

Make should deliver one coherent product definition with stable internal IDs:

| Internal record | Required meaning |
|---|---|
| Component | Identity/function, material or constituent description, fabrication/sourcing route, quantity/unit, dimensions/interfaces and evidence references. |
| Installed occurrence | Which component is placed where; quantity and identity remain consistent with the assembly. Flexible paths or approximate envelopes identify their representation honestly. |
| Stock and consumables | Sheet or linear stock, cut lengths, useful yield/waste allowance, adhesive/finish consumption, purchase quantity versus required usage. |
| Manufacturing operation | Input material/part, process and output, drawing/pattern/reference, tools or fixtures, relevant setup and check. |
| Assembly and test operation | Components joined, fastening/routing/orientation, access and sequencing, required observation and recorded result. |
| Product presentation | Exact finished-product images and supported motion/use views, with titles and descriptions appropriate for customers. |

Material and process are independent: a cardboard panel is board cut from
stock; a printed hinge is polymer made additively; a motor is a bought
multi-material assembly. A source filename or a rendering color cannot replace
those distinctions. Tools and fixtures are internal resources, not installed
parts or customer deliverables.

Represent the actual finished form for inspection and rendering. Retain the
manufacturing representation where different: a flat pattern and its assembled
pose, a cord cut length and installed route, a supplier envelope and measured
mount interface. Passing the CAD checks for a printed subset does not certify
fabrication or operation of the complete mixed-material product.

## Proposed milestones

### 1. Internal contract and Spark scope

Define a versioned Make-owned mixed-material specification, joining components,
occurrences, processes and evidence by stable IDs. Require coherent quantities
and references; represent unavailable supplier properties as unresolved rather
than fabricated facts. Scope its use to newly supported Spark output without
silently upgrading frozen sessions or changing other workflow routes.

Acceptance: a deterministic fixture describes a complete passive mixed-material
product; malformed references, invalid quantities and missing required process
inputs fail clearly. Existing single-material products retain their supported
behavior. This is contract validation, not a new host engineering review.

### 2. Internal fabrication and assembly handoff

Produce an internal package sufficient for equipped workshop staff to source,
fabricate, assemble and test the product. Separate printed components from
laser/CNC/wood/fabric operations and bought parts. Record supplier/interface
requirements, cut schedules, fixture needs, assembly order and material-specific
checks. Exact file formats for additional manufacturing patterns require an
explicit supported contract; equipment availability alone is not a new exporter.

Acceptance: every required component has a fabrication or sourcing route, every
assembly operation names its inputs, and the staff handoff identifies unresolved
measurements and physical checks. No part is sent for printing merely because
it has a solid representation.

### 3. Complete-product visual presentation

Make produces finished-product hero images and useful secondary views showing
all visible required materials and components in their intended assembled
positions. Wood, board, felt, rubber, metal and printed polymer should look
appropriate to the actual design. An optional motion view should show the
product's behavior where supported by its evidence.

Acceptance: visual review concerns the whole designed product, including play
objects and visible bought components. The public page presents the product and
what a customer receives as a finished item. Internal BOM rows, sourcing links,
cut lists, assembly diagrams and production archives are excluded from public
presentation and public download paths.

### 4. Explicit public/internal artifact boundary

Give the existing Spark handoff an explicit distinction between public
presentation assets and the private manufacturing package. Both must preserve
the exact accepted bytes and trace back to the same product revision. This is
a necessary data/transport boundary: hiding a BOM in the page UI is insufficient
if the underlying archive or endpoint still exposes it.

Acceptance: deterministic publication/carrier tests prove that the approved
complete-product visuals arrive unchanged and that internal manufacturing
artifacts are not publicly accessible through the generated public payload.
Preserve host-only authenticated publication and its receipts. Confirm external
Factory/frontend behavior separately before claiming live support.

### 5. Workshop trial and evidence

Execute the proposed pilot portfolio, beginning with P1's passive mechanism
after the code and handoff are proven. Staff source the specified items,
fabricate and assemble each product, record actual dimensions and substitutions,
then test fit, motion and intended play. Progress through the planned coverage
matrix rather than declaring the MVP complete after a schema or one product.
Unresolved physical mechanisms or unsupported processes require a recorded
revision or an explicit remaining gap; they cannot be hidden by a beauty render.

Acceptance: digital completion, fabrication, assembled condition, tested
behavior and shipment remain distinct recorded facts. A render or deterministic
fixture cannot establish a physical result. Physical fabrication, procurement
and shipment remain authorized human/host operations, not side effects of
running a repository test or generating a design.

## Architecture and verification constraints

The native Manager owns design, material selection, inspection and repair.
Python remains deterministic contracts, tools, artifact identity, durable state
and effect boundaries. Make owns its engineering checks and visual review;
Spark gains no duplicate host CAD/material acceptance pass or native Release
turn. See [ADR 0061](../adr/0061-spark-make-owned-verification.md).

STEP remains the geometry export boundary. Do not reintroduce STL, 3MF or GLB
deliverables through a viewer or manufacturing-package shortcut. Additional
2D pattern/manufacturing formats need a deliberate policy decision consistent
with [ADR 0062](../adr/0062-step-only-cad-toolchain.md); this proposal does not
authorize them implicitly. Printed-part claims continue to require applicable
source/nozzle evidence under
[ADR 0063](../adr/0063-print-gates-on-source.md), including Spark's existing
Make-owned verification exception to host reruns.

Shipping finished products is the accepted business outcome. Publishing a page
or sealing a Make package does not itself prove that fabrication, testing or
shipment happened. The internal product contract should enable those operations
without inventing their results or expanding agent effect authority.
