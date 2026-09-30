# Lighting discovery

Read this reference whenever an image, brief or existing CAD contains a
functional LED, lamp, beacon, strobe, headlight, light strip, illuminated
control, light pipe or backlight. Do not wait for the user to ask for component
research separately.

## What a light is, and what must be recorded

A visible light is four objects (emitter, driver/connector, visible optic,
printed seat and service features), and each gets an inventory row: function,
position, colour, behaviour, optical direction, implementation, evidence. The
inventory table, why a lens colour never identifies an MPN, and when
compliance terms are only a convention:
`skills/wiki/pages/electronics/lighting-design.md`
(`wiki show lighting-design#a-visible-light-is-four-objects`).

## Automatic discovery sequence

### 1. GitHub analogy search

Search queries combine the product form, lighting function, supply class and an
integration artifact, for example:

```text
model aircraft navigation strobe LED 5V CAD KiCad BOM schematic license
printed enclosure status light pipe LED STEP wiring assembly
wearable addressable LED diffuser battery hatch CAD BOM license
```

Review at most five strong repositories. A used result must have source CAD or
KiCad **and** at least one of BOM, wiring, schematic or assembly instructions,
plus an explicit license. Record the repository URL, immutable commit or tag,
license, artifacts inspected, relevant feature and the precise construction
idea taken. GitHub supplies an integration pattern, not component ratings,
dimensions or a substitute exterior.

### 2. Bought-part geometry and evidence

Once an exact manufacturer part number is known, search in this order:

1. `step.parts`, using the bundled `$step-parts` client with the exact MPN,
   aliases and package tokens;
2. the manufacturer product page, datasheet and manufacturer-hosted CAD;
3. [TraceParts](https://www.traceparts.com/en), especially manufacturer
   catalogs that expose STEP AP203/AP214/AP242;
4. [SnapMagic Search](https://www.snapeda.com/) (formerly SnapEDA), which can
   supply ECAD data and STEP models;
5. [Ultra Librarian](https://app.ultralibrarian.com/manufacturers), searched by
   manufacturer and exact part number;
6. the current official
   [KiCad packages3D libraries](https://gitlab.com/kicad/libraries/kicad-packages3D)
   for a generic package shape when no MPN-specific model exists. The old
   [GitHub `KiCad/kicad-packages3D`](https://github.com/KiCad/kicad-packages3D)
   is an archived snapshot that points to that GitLab repository; do not pin
   new provenance to the archived default branch when the current library is
   available.

Search by function and package only to discover candidates. Before using a CAD
model, resolve it back to an exact MPN and compare the package/drawing revision.
Do not substitute a visually similar LED or module. Do not scrape, bypass a
login, or accept terms on the user's behalf. A service that requires unavailable
credentials is `unavailable`; continue searching and record it separately from
a genuine `miss`.

What a generic package model proves (and does not) about mating geometry:
`wiki show lighting-design#what-a-generic-package-model-proves`. Unless a
library model traces to the exact selected MPN and drawing revision, label it
`validation_envelope`.

The service's model is mechanical evidence only. Electrical and optical facts
still come from the manufacturer or an applicable standard. Record each query
in schema 2 or 3 `component_search` with service, URL, decision and reason. For
a used STEP, also record the exact MPN, project-local path, SHA-256 and the
license or terms that cover use of the downloaded artifact.

### 3. Required authoritative facts

Obtain the manufacturer facts listed in
`wiki show lighting-design#facts-that-must-come-from-the-manufacturer` before
selection. If a required rating cannot be sourced, leave compatibility
unresolved.

## Selection and CAD handoff

Select in the order given by `wiki show lighting-design#selection-order`.

Download a chosen STEP into `<project-dir>/ref/` and derive its seat with
`cadmount`; never type its dimensions into the generator. Third-party artifacts
also need a provenance record beside the file containing source URL, revision,
license/terms and checksum. If no exact STEP exists, build a documented envelope
from the manufacturer package drawing, label it `validation_envelope`, cite the
drawing revision and keep the numbers in that envelope's provenance rather than
pretending it is vendor CAD.

Visible lenses, bezels and diffusers belong in the combined assembly and
likeness renders. Hidden emitters, drivers and looms may be validation-only, but
every carried item still gets a mount id and `check_mount` obstacle list. Model
the full route from controller to emitter, including insulation diameter, bend
room, connector insertion/removal and strain relief.

## Removable lamp mating hardware

A removable lamp is not selected until its receiver and bought contacts are
selected too. The design rules (three bought parts, prefer a purchased socket,
when a printed receiver is allowed, why each motion phase is needed, why a
real-hardware coupon is required) are in
`skills/wiki/pages/electronics/removable-lamp-interfaces.md`
(`wiki show removable-lamp-interfaces`). What this skill requires:

- lamp, socket and any separate contact are separate component rows, each with
  evidence, a search record and a mount;
- a printed receiver records why a purchased socket was not used, derives its
  female path from the male lugs/threads through `cadfits`, and keeps bought
  contacts;
- the interface declaration carries lamp and receiver/contact MPNs plus source
  URL and revision; interface type and datum, lug count, insertion depth, lock
  angle/direction; the CAD clearance and its derivation method; retention stop,
  connector access, tool/finger access and service direction;
- all five motion conditions (`insert`, `lock`, `retained`, `unlock`,
  `remove`) are written to `measure/motion.json` and their IDs referenced from
  `power.json`; phases that begin installed use `allow_seated_contact`;
- a `fit_coupon` record with `status`, material, process, orientation,
  hardware sample identifiers, candidate clearances (at least three, including
  the current `geometry.clearance_mm`), method and result. `planned` leaves
  physical fit unverified, `failed` blocks the interface, and `passed` names a
  `selected_clearance_mm` drawn from the tested candidates, which is then
  written back into the CAD and the spec.

## Manifest shape

Use schema 3 for new work. Schema 1 and 2 remain accepted for old projects. A
non-actuating electrical load uses `role: "load"`; lighting also uses
`load_type: "lighting"`, its visible-function ledger and an installation
declaration:

```json
{
  "id": "left_position_light",
  "role": "load",
  "load_type": "lighting",
  "continuous_current_a": 0.02,
  "peak_current_a": 0.08,
  "lighting": {
    "function": "left position",
    "color": "red",
    "behavior": "steady with pulsed white strobe override",
    "installation": {
      "mode": "removable_socket",
      "interface_id": "left-position-twist-lock",
      "receiver": "left_position_socket"
    }
  }
}
```

The enclosing component still needs `carried`, `mount_id`, `cad`, `evidence`
and `voltage_v`. Its path names it with `"load": "left_position_light"`.
Write one path per independently rated parallel branch; a manufacturer-rated
strip or module may remain one load. A removable socket installation also needs
the corresponding `mating_interfaces` record:

```json
{
  "id": "left-position-twist-lock",
  "type": "twist_lock",
  "load_component": "left_position_light",
  "receiver_strategy": "purchased_socket",
  "receiver": "left_position_socket",
  "contact_component": "left_position_socket",
  "lamp_mpn": "EXAMPLE-LAMP",
  "receiver_mpn": "EXAMPLE-SOCKET",
  "contact_mpn": "EXAMPLE-SOCKET",
  "evidence": {
    "lamp_source": "https://manufacturer.example/lamp.pdf",
    "lamp_revision": "A",
    "receiver_source": "https://manufacturer.example/socket.pdf",
    "receiver_revision": "B"
  },
  "geometry": {
    "source_datum": "lamp flange underside to socket mounting face",
    "lug_count": 2,
    "insertion_depth_mm": 6.0,
    "lock_rotation_deg": 30.0,
    "lock_direction": "clockwise",
    "clearance_mm": 0.25,
    "clearance_method": "socket seat derived with cadfits slip clearance",
    "retention_stop": "socket end stops and lug shoulders",
    "connector_access": "rear terminals reachable through service hatch",
    "tool_access": "lamp can be gripped and rotated by hand"
  },
  "motion_conditions": {
    "insert": "left-light-insert",
    "lock": "left-light-lock",
    "retained": "left-light-retained",
    "unlock": "left-light-unlock",
    "remove": "left-light-remove"
  },
  "fit_coupon": {
    "status": "planned",
    "material": "PETG",
    "process": "FDM, 0.4 mm nozzle, 0.2 mm layer",
    "orientation": "socket axis vertical",
    "hardware_sample": "exact production lamp and socket samples",
    "candidate_clearances_mm": [0.15, 0.25, 0.35],
    "method": "print complete receiver coupons and dry-fit exact hardware",
    "result": "pending physical samples"
  }
}
```

The purchased socket and any separate contact also appear in `components`, in
`component_search`, and in the electrical path. A `printed_receiver` uses the
same record, omits `receiver_mpn`, adds
`printed_receiver_justification`, and still names a bought connector as
`contact_component`.
