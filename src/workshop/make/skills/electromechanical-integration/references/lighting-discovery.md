# Lighting discovery

Read this reference whenever an image, brief or existing CAD contains a
functional LED, lamp, beacon, strobe, headlight, light strip, illuminated
control, light pipe or backlight. Do not wait for the user to ask for component
research separately.

## First separate what the image conflates

A visible light usually has four different objects:

1. the emitter or bought light module;
2. its driver/controller and connector;
3. the lens, light pipe or diffuser that owns the visible exterior;
4. the printed seat, bezel, wire channel and service feature.

Do not model one coloured primitive and call all four complete. Inventory each
visible light with:

| Field | Record |
|---|---|
| function | position/navigation, head/landing/work, brake/indicator, beacon/strobe, status, decorative/ambient, backlight, IR/UV, or an explicit project term |
| position | part, face and assembly pose |
| colour | observed/requested colour; wavelength only from a datasheet |
| behavior | steady, dimmed, blink, pulse, strobe pattern, addressable animation |
| optical direction | viewing direction, beam/viewing angle if sourced, and which surface is luminous |
| implementation | discrete LED, addressable pixel, strip, COB/module, lamp, light pipe or unresolved |
| evidence | `[observed]`, `[inferred]` or `[assumed]` for image-derived work |

A lens colour and glow in a render may identify function, but never an exact
manufacturer part number. Treat compliance terms such as “navigation light” or
“warning beacon” as a design convention until an applicable standard and its
photometric requirements are explicitly in scope.

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

KiCad package geometry is useful for PCB rendering, board-envelope checks and a
documented generic package stand-in. It is not evidence that a lamp mates with
a socket, and it does not authorize a drilled hole, bayonet path or twist-lock
receiver. Unless the library model can be traced to the exact selected MPN and
drawing revision, label it `validation_envelope`; obtain mating dimensions from
the lamp/socket manufacturer or a measured exact sample.

The service's model is mechanical evidence only. Electrical and optical facts
still come from the manufacturer or an applicable standard. Record each query
in schema 2 or 3 `component_search` with service, URL, decision and reason. For
a used STEP, also record the exact MPN, project-local path, SHA-256 and the
license or terms that cover use of the downloaded artifact.

### 3. Required authoritative facts

Before selection, obtain as applicable:

- accepted supply or forward-voltage range;
- continuous current and worst-case pulse/peak current;
- whether a resistor, constant-current driver, level shifter or controller is
  required;
- wavelength/colour, luminous intensity or flux, viewing/beam angle and maximum
  duty cycle when these affect the requested function;
- package drawing, emitting-surface datum, lead/connector orientation, bend
  limits and thermal constraints.

If a required rating cannot be sourced, leave compatibility unresolved. Do not
fill it with a value from a similar-looking part or from the GitHub analogy.

## Selection and CAD handoff

Select against the whole product, in this order:

1. exact requested function and colour/behavior;
2. full source-voltage compatibility and worst-case current;
3. exact lamp MPN, its exact mating socket/contact system, geometry and a
   serviceable assembly path;
4. optical direction and visible optic;
5. driver heat, wire bend, connector access and replacement access.

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

A removable lamp is not selected until the receiver and electrical contacts
are selected too. Treat the following as separate bought parts with separate
component rows, evidence, search records and mounts:

- the exact lamp/emitter MPN;
- the exact purchased socket MPN, when one exists;
- a separate contact or connector MPN when it is not included in the socket.

Prefer a purchased socket whose manufacturer documentation explicitly names
the lamp family or mating interface. The printed product then seats the socket;
it does not recreate uncertain spring contacts, terminal geometry or an
undocumented proprietary lamp base. If no authoritative drawing or verified
physical sample defines the mate, do not invent a twist-lock channel, drill a
nominal hole, or claim compatibility from a similar-looking KiCad/STEP model.

A printed receiver is allowed only when the interface is documented and its
electrical contacts remain bought, rated components. Its female path must be
derived from the male lamp lugs/threads from one source dimension, with
clearance applied once through `cadfits`. Record why a purchased socket was not
used. The interface declaration must then carry:

- lamp and receiver/contact MPNs plus source URL and revision;
- interface type and datum, lug count, insertion depth, lock angle/direction;
- selected CAD clearance and the method that derived it;
- retention stop, connector access, tool/finger access and service direction;
- the five motion-condition IDs and the fit-coupon record below.

### Motion is a five-phase contract

Every removable lamp writes all five conditions to `measure/motion.json` and
references their IDs from `power.json`:

1. `insert`: axial insertion to the rotation datum is clear;
2. `lock`: the locking rotation is clear;
3. `retained`: an axial pull in the removal direction is blocked while locked;
4. `unlock`: reverse rotation is clear;
5. `remove`: axial extraction after unlocking is clear.

Use `allow_seated_contact` for phases that begin installed. A clear insertion
alone proves only that a pocket is reachable; it does not prove capture. A
blocked pull alone can be a collision in the wrong direction; state which way
the user or stored energy drives the lamp and put the retaining shoulder in
front of that direction.

For a threaded interface, the rotation condition is only a rigid-body proxy;
`check_motion` cannot follow helical thread engagement or predict tightening
torque. Keep those as coupon/prototype findings rather than geometry-gate claims.

### Physical fit needs a real-hardware coupon

CAD and exact STEP booleans cannot predict printer shrinkage, elephant foot,
surface texture, support scars, material creep, contact spring force or vendor
tolerance. Before claiming that a printed receiver physically fits, print a
small coupon containing the complete insertion and locking interface in the
same material, process, nozzle/layer settings and orientation as the final
part. Test at least three declared candidate clearances with the exact
production lamp and receiver/contact samples.

Record `status`, material, process, orientation, hardware sample identifiers,
candidate clearances, method and result. `planned` means physical fit is still
unverified. `failed` blocks the interface. `passed` must name a
`selected_clearance_mm` that was actually among the tested candidates; update
the CAD and spec to that value before final manufacture. The current
`geometry.clearance_mm` must be included in the candidate set even while the
coupon is only planned.

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
