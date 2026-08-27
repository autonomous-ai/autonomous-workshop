# Power manifest

Write `<project>/measure/power.json` after selecting the actual electrical loads
and power hardware. Values are engineering declarations backed by cited
evidence; the checker only verifies their internal consistency.

## Schema version 3

New manifests use version 3. Versions 1 and 2 remain accepted for existing
projects. Version 2 added auditable public component discovery and
non-actuating loads such as lighting. Version 3 adds explicit installation and
mating-interface evidence for removable lights.

Add a `component_search` record for every public catalog/service query that
changes or confirms component selection:

```json
{
  "schema_version": 3,
  "component_search": [
    {
      "query": "EXAMPLE-LAMP red lamp STEP datasheet",
      "service": "manufacturer",
      "url": "https://manufacturer.example/EXAMPLE-LAMP",
      "decision": "used",
      "component_id": "left_position_light",
      "part_number": "EXAMPLE-LAMP",
      "artifacts": ["datasheet", "step"],
      "license_or_terms": "manufacturer CAD download terms",
      "local_file": "ref/EXAMPLE-LAMP.step",
      "sha256": "<64 hex characters>"
    },
    {
      "query": "EXAMPLE-LAMP",
      "service": "step.parts",
      "url": "https://api.step.parts/v1/parts?q=EXAMPLE-LAMP",
      "decision": "miss",
      "reason": "reachable API returned no exact or alias match"
    },
    {
      "query": "EXAMPLE-SOCKET lamp socket STEP datasheet",
      "service": "manufacturer",
      "url": "https://manufacturer.example/EXAMPLE-SOCKET",
      "decision": "used",
      "component_id": "left_position_socket",
      "part_number": "EXAMPLE-SOCKET",
      "artifacts": ["datasheet", "step"],
      "license_or_terms": "manufacturer CAD download terms",
      "local_file": "ref/EXAMPLE-SOCKET.step",
      "sha256": "<64 hex characters>"
    }
  ]
}
```

A used STEP record needs its project-local file and checksum. A used datasheet
without STEP lists `artifacts: ["datasheet"]` and may omit those two fields. A
login wall or network failure is `unavailable`, not `miss`.

Lighting is a `load`, not an actuator:

```json
{
  "id": "left_position_light",
  "role": "load",
  "load_type": "lighting",
  "carried": true,
  "mount_id": "left_position_light_mount",
  "cad": {
    "mode": "assembly",
    "rendered": true,
    "source": "ref/EXAMPLE-LAMP.step"
  },
  "evidence": {
    "kind": "manufacturer_datasheet",
    "url": "https://manufacturer.example/EXAMPLE-LAMP.pdf"
  },
  "voltage_v": {"min": 3.0, "max": 5.5},
  "continuous_current_a": 0.02,
  "peak_current_a": 0.08,
  "lighting": {
    "function": "left position",
    "color": "red",
    "behavior": "steady with pulsed strobe override",
    "installation": {
      "mode": "removable_socket",
      "interface_id": "left-position-twist-lock",
      "receiver": "left_position_socket"
    }
  }
}
```

The matching purchased socket is a separate connector component:

```json
{
  "id": "left_position_socket",
  "role": "connector",
  "carried": true,
  "mount_id": "left_position_socket_mount",
  "cad": {
    "mode": "assembly",
    "rendered": true,
    "source": "ref/EXAMPLE-SOCKET.step"
  },
  "evidence": {
    "kind": "manufacturer_datasheet",
    "url": "https://manufacturer.example/EXAMPLE-SOCKET.pdf"
  },
  "voltage_v": {"min": 0.0, "max": 12.0},
  "continuous_current_a": 0.5,
  "peak_current_a": 0.5
}
```

Schema 3 installation modes are `removable_socket`, `soldered`, `fixed_module`
and `integrated`. Every `removable_socket` light uses assembly CAD and has one
matching top-level interface record:

```json
{
  "mating_interfaces": [
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
  ]
}
```

The purchased receiver is itself a `connector` component, uses
`cad.mode: "assembly"`, has a separate mount, and appears in the electrical
path. If the contacts are separate, `contact_component` names their own
connector row. A `printed_receiver` omits `receiver_mpn`, adds a non-empty
`printed_receiver_justification`, and still uses a bought, rated connector for
the contacts.

The five condition IDs must exist in `measure/motion.json`: insertion and lock
are clear, axial removal while locked is blocked, then unlock and removal are
clear. `check_power` verifies distinct IDs, phase-specific `expect`, the linear
versus rotational check type and seated-contact declarations; `check_motion`
evaluates the actual sweeps and capture direction.

Fit coupons distinguish a CAD claim from a physical fit claim. `planned` is
valid while hardware is unavailable but means fit is unverified. `failed`
blocks the design. `passed` requires `selected_clearance_mm`, and it must be one
of the declared candidates tested with the exact lamp and socket/contact, using
the final material, process and orientation. The current
`geometry.clearance_mm` must always be among the declared candidates and, after
a pass, must equal the selected tested value.

Its independently rated branch uses `load` in place of `actuator`:

```json
{
  "id": "left_position_branch",
  "source": "battery",
  "load": "left_position_light",
  "sequence": [
    "battery", "fuse", "lighting_controller", "left_supply_wire",
    "left_position_socket", "left_position_light", "left_return_wire",
    "battery"
  ],
  "required_continuous_current_a": 0.02,
  "required_peak_current_a": 0.08,
  "protection": {"status": "present", "component": "fuse"},
  "control": {"status": "present", "component": "lighting_controller"},
  "route": {
    "modeled": true,
    "clearance_envelope_mm": 1.5,
    "strain_relief": true,
    "service_access": "removable lens bezel and controller hatch"
  }
}
```

Write one path per independently rated parallel branch. A manufacturer-rated
strip or light module may remain one load. The declared source appears exactly
twice, at the two endpoints; the declared actuator/load appears exactly once;
and no second source, actuator or load may be inline on that branch.

For every carried component, `mount_id` must name a unique row in
`measure/mounts.json`, and that row's `component` path must equal the
component's `cad.source`. Merely naming an existing mount id is not sufficient:
otherwise a light can accidentally claim the motor's valid seat.

## Legacy schema version 1 example

```json
{
  "schema_version": 1,
  "project": "motorized_product",
  "boundary": "onboard",
  "github_search": [
    {
      "query": "brushed dc 3-6v toy aircraft battery hatch wiring CAD",
      "url": "https://github.com/example/open-aircraft",
      "license": "MIT",
      "decision": "used",
      "artifacts": ["cad", "bom", "wiring", "assembly"],
      "relevant_feature": "central service hatch and fore-aft battery tray",
      "idea_taken": "a removable hatch exposes an adjustable battery cradle",
      "compatibility": {
        "actuator_family": "brushed_dc",
        "source_voltage_v": [3.0, 4.2]
      }
    }
  ],
  "components": [
    {
      "id": "battery",
      "role": "source",
      "carried": true,
      "mount_id": "battery_mount",
      "cad": {
        "mode": "validation_envelope",
        "rendered": false,
        "source": "ref/validation/battery-envelope.step"
      },
      "evidence": {
        "kind": "manufacturer_datasheet",
        "url": "https://manufacturer.example/battery-datasheet.pdf"
      },
      "voltage_v": {"min": 3.0, "max": 4.2},
      "continuous_current_a": 3.0,
      "peak_current_a": 6.0
    },
    {
      "id": "fuse",
      "role": "protection",
      "carried": true,
      "mount_id": "fuse_mount",
      "cad": {
        "mode": "validation_envelope",
        "rendered": false,
        "source": "ref/validation/fuse-envelope.step"
      },
      "evidence": {
        "kind": "manufacturer_datasheet",
        "url": "https://manufacturer.example/fuse-datasheet.pdf"
      },
      "voltage_v": {"min": 0.0, "max": 32.0},
      "continuous_current_a": 2.0,
      "peak_current_a": 4.0
    },
    {
      "id": "switch",
      "role": "switch",
      "carried": true,
      "mount_id": "switch_mount",
      "cad": {
        "mode": "assembly",
        "rendered": true,
        "source": "ref/power-switch.step"
      },
      "evidence": {
        "kind": "manufacturer_datasheet",
        "url": "https://manufacturer.example/switch-datasheet.pdf"
      },
      "voltage_v": {"min": 0.0, "max": 12.0},
      "continuous_current_a": 2.0,
      "peak_current_a": 4.0
    },
    {
      "id": "supply_wire",
      "role": "wire",
      "carried": true,
      "mount_id": "supply_wire_envelope",
      "cad": {
        "mode": "validation_envelope",
        "rendered": false,
        "source": "ref/validation/supply-wire-envelope.step"
      },
      "evidence": {
        "kind": "manufacturer_datasheet",
        "url": "https://manufacturer.example/wire-datasheet.pdf"
      },
      "continuous_current_a": 3.0,
      "peak_current_a": 6.0
    },
    {
      "id": "motor",
      "role": "actuator",
      "carried": true,
      "mount_id": "motor_mount",
      "cad": {
        "mode": "assembly",
        "rendered": true,
        "source": "ref/motor.step"
      },
      "evidence": {
        "kind": "manufacturer_datasheet",
        "url": "https://manufacturer.example/motor-datasheet.pdf"
      },
      "voltage_v": {"min": 3.0, "max": 6.0},
      "running_current_a": 0.5,
      "stall_current_a": 1.5
    },
    {
      "id": "return_wire",
      "role": "wire",
      "carried": true,
      "mount_id": "return_wire_envelope",
      "cad": {
        "mode": "validation_envelope",
        "rendered": false,
        "source": "ref/validation/return-wire-envelope.step"
      },
      "evidence": {
        "kind": "manufacturer_datasheet",
        "url": "https://manufacturer.example/wire-datasheet.pdf"
      },
      "continuous_current_a": 3.0,
      "peak_current_a": 6.0
    }
  ],
  "paths": [
    {
      "id": "propulsion",
      "source": "battery",
      "actuator": "motor",
      "sequence": [
        "battery",
        "fuse",
        "switch",
        "supply_wire",
        "motor",
        "return_wire",
        "battery"
      ],
      "required_continuous_current_a": 0.5,
      "required_peak_current_a": 1.5,
      "protection": {"status": "present", "component": "fuse"},
      "control": {"status": "present", "component": "switch"},
      "route": {
        "modeled": true,
        "clearance_envelope_mm": 3.0,
        "strain_relief": true,
        "service_access": "removable upper hatch"
      }
    }
  ]
}
```

## Required decisions

- `boundary` is `onboard` or `external`. An onboard design carries its source;
  an external design carries an `inlet` component.
- `github_search` contains at least one `used`, `rejected`, or `miss` record.
  A used record needs a GitHub repository URL, license, relevant feature,
  precise idea taken, CAD plus at least one BOM/wiring/schematic/assembly
  artifact, an immutable `revision` in schema 2 or 3, and a compatibility summary
  containing `load_family` (legacy
  `actuator_family` is accepted for schema 1) and the source-voltage interval.
  A miss needs a reason.
- Schema 2 or 3 `component_search` contains at least one public catalog/service
  record. A used result names the manifest component, exact part number,
  artifacts and license/terms. A used STEP also names the project-local file and
  its SHA-256; the gate reads the file and verifies that checksum. Rejections,
  misses and unavailable services carry a reason.
- Component roles are `source`, `protection`, `switch`, `controller`,
  `connector`, `wire`, `actuator`, `load`, or `inlet`. An actuator declares
  running and stall/start current. A general load declares continuous and peak
  current plus `load_type`; lighting additionally declares function, colour and
  behavior. Schema 3 lighting declares its installation mode. Every removable
  socket light names exactly one `mating_interfaces` record.
- A removable-light interface names the exact lamp, purchased socket or
  justified printed receiver, bought contact component, evidence revisions,
  complete mating geometry, all five motion phases, and the physical fit-coupon
  record. `lamp_mpn`, `receiver_mpn` and `contact_mpn` must exactly match a
  `part_number` in a `used` component-search record for the named component.
  Purchased sockets are carried `connector` components with assembly CAD and
  their own mount.
- Every component cites authoritative evidence. Supported evidence kinds are
  `manufacturer_datasheet`, `manufacturer_product_page`, `standard`, and
  `measured`. A measured value also needs a non-empty `method`.
- Every carried component, including each wire envelope, has a `mount_id` found
  in `measure/mounts.json` and a `cad` declaration. `cad.mode` is `assembly`
  with `rendered: true`, or `validation_envelope` with `rendered: false` and a
  project-local STEP/STP `source`. Validation-only sources stay out of the
  combined assembly and render; `check_mount` inserts them only for clash and
  clearance measurement.
- A path names exactly one `actuator` or `load`, begins and ends at its source,
  and includes that target. Its source voltage interval must fit within every
  non-wire component's declared interval.
- The required continuous and peak currents must cover an actuator's running
  and stall/start currents or a load's continuous and peak currents. Every
  source, protection, switch, controller, connector, inlet and wire on the path
  must meet both requirements.
- Protection and control are either `present` with a component on the path, or
  `not_required` with a non-empty justification and `evidence_url`. The checker
  verifies the declaration, not whether that engineering decision is correct.
- `route.modeled`, `route.strain_relief`, a positive clearance envelope, and
  non-empty service access are mandatory. Use a separate path for each source
  or independently protected actuator circuit.

## Mount manifest interaction

The gate reads `<project>/measure/mounts.json` and compares its `mounts[*].id`
values with component `mount_id` values. Put validation-only STEP files under
`ref/validation/` and list the printed parts they must clear in the matching
mount record. A catalog miss may use a documented envelope component, but it
still needs a project-local mount declaration and must remain labeled as an
envelope rather than a verified vendor shape. The product spec must record the
same render policy and name `check_mount` as its collision gate.
