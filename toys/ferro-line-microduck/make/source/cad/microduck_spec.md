# Microduck — current source specification

This is the reconciled Make specification for `duck_lib.py` and `drive_lib.py`; the earlier `reference_spec.md` is an interpretation and proposed method, superseded wherever it differs below. Units are millimetres. CAD checks establish geometry only, not successful printing or physical operation.

The Wish requires a robot microduck resembling the supplied image and moving after winding a knob. [observed] `ref/hero.png` is the exact 453 × 638 RGBA reference, SHA-256 `5dca005c892bf2d3197bc469b8a152dda438bfb69f7a9148604b7cc673a7a2c2`. It depicts a tall grey mechanical duck, domed shield head with dark rim, large purple-ringed dark lens, smaller dark oval sensor, canted yellow bill, narrow dark segmented neck, small grey torso, jointed leg silhouettes, yellow boots and thick purple soles. There is one supplied whole-object viewpoint; hidden depths and engineering interfaces are invented.

[assumed] Height is 180 mm; 560 visually occupied reference pixels define the contour conversion 180/560 mm per pixel. Coordinates are X lateral, front −Y, Z upward, ground Z0. The final assembly target is X −45.3 to42, Y −20 to18, Z0 to180, with ±0.25 mm target tolerance. Contours are manually measured image-plane polygons, extruded in Y; they are not claimed to reconstruct unseen orthographic dimensions. The common rear plane Y18 provides a broad print face. The frame is a solid relief chassis, not a hollow shell or a loft. Rounded depth-running edges soften the head outline and boot corners. This explicitly replaces the preliminary suggested shell/loft construction.

The construction and landmark tables below are the machine-readable dimensional contract used by `measure/check_spec.py` and `measure/check_landmarks.py`. They intentionally use returned BRep bounds, circular edge radii and face counts in addition to AST construction-family checks. The full geometry/fit and print-thickness gates remain separate. A topology minimum is a deletion detector, not a substitute for silhouette or appearance review.

## Current mechanism and assembly

[invented adaptation] Two coaxial diameter20 drive wheels turn on the transverse hollow diameter8.4 shaft at Y−6,Z10. The right wheel, winding knob and shaft are one rotor. A separate left wheel uses a bonded D-flat interface; the D-flat is radius3.9 with matching socket radius4.0. Slip bores are diameter8.8; axial wheel/frame clearance is0.4 per side. Two diameter12 rear idlers at Y12,Z6 roll on diameter3.2 headed pins with diameter3.6 running bores. Pins bond into diameter3.4 frame sockets. This supplies front/rear support while the feet stay above the ground. No walking gait is claimed.

The replaceable single straight MVQ silicone cord has nominal diameter4, hardness60 Shore A, working span81.2 and maximum2 winding turns. It passes through the diameter5.4 shaft bore, using an external fixed left lacing eye and accessible right crossbar. The fixed eye is OD14/ID11.4, centered X−40.2,Y−6,Z7.5, with a2 mm crossbar and2 ×4 ×8 upper bonding tab. Its lowest point is Z0.5. The rotor shaft ends at X−34.7; right knob spans X38..42 with a taper from wheel radius10 to knob radius8 at X35..38. The enlarged knob opening has radius6 and a2.4 mm thick crossbar at X40..42. Cord torque and friction calculations are estimates with explicit material/traction assumptions; physical fit, bond strength, fatigue, runtime and travel are unverified. No electrical load is present.

The colour parts bond onto broad frame lands: crown bezel, bill, annular lens, dark lens, oval sensor, segmented neck skin, two shin plates, two boot fronts and two soles. Front boot panels end at Y−7.2 with0.2 adhesive clearance to the structural feet. Left boot Z7.4..17.4 and sole Z2.4..7.2; right boot Z15.4..25.4 and sole Z10.4..15.2. The right visible boot is raised8 mm to preserve the observed staggered stance; separate low bearing webs preserve the ground axle/idler positions. Each shin begins0.2 above its boot. The dark neck skin is clipped to Z96..128 and has rib clearances at Z91,103,115,128; the widened exposed upper skin reaches X−6.429 and ends at Z127.199 after subtraction of the head, below the Z128 clipping plane. The lens ring OD19.6/ID10 surrounds a separate dark diameter9.2 insert. The oval sensor is5.8 ×3 mm in the XZ plane. The bill spans Y−18..−12.2 and has a mouth recess ending at Y−15.2, leaving a3 mm rear land.

## Repair and evidence reconciliation

The earlier 0.75 adaptation exception is withdrawn. The integrated whole-object hero likeness floor is **0.90**, with no accepted mismatch. Separate qualitative review must still find the supplied subject unmistakable. Changes from preliminary design are explicit: one solid profile-extruded frame replaces proposed head/torso shells; single torsion cord replaces an unspecified rubber band; two driven wheels and two free rear idlers replace an underspecified wheel arrangement; colour fronts are separately printable; the right boot is raised; the crown bezel is clipped above Z142 and the neck skin is trimmed to remove disconnected or interfering material; the mouth slot ends are inset to avoid thin wedges. The left anchor bridge now ends at X−42.5; its tab is2 mm wide. The8.4 mm shaft and shortened X42 knob reduce the added drive silhouette while preserving the5.4 mm cord bore. Outer rear boot-panel corners are opened at |X|≥27,Y≥−17.2, and the left boot upper outer corner is cut at X≤−29,Z≥16.2; the frame rear left corner at X≤−29.6,Y≥15.5,Z≤12 is removed to eliminate feather-thin wheel-pocket remnants. Wheel exposure, winding knob, structural anchor bridge, service seams and simplified tiny wires/fasteners are invented deviations, not observed reference features.

The observed torso contour includes the small shoulder/cable hump through image pixels (143,296), (143,289), (153,292), (160,301). The pelvis underside follows (190,452), (174,455), (146,455), (120,450), (106,436), avoiding the earlier oversized crotch lip. These are source contour coordinates, not invented mechanical envelopes; their complete ordered polygons are audited below.

The final bill contour preserves the observed right lug through pixels (281,135), (282,143), (284,149), (283,157), and uses projection-corrected lower-left relief through (155,205), (140,207), (112,196). Its maximum X is36.642857 mm, derived from observed pixel284; its depth and recessed mouth remain unchanged. The complete ordered bill polygon is audited alongside the torso and pelvis.

Applicable recorded vault lessons are addressed by a listed anchor/retainer, explicit clearances, a four-contact support polygon, a bounded winding limit and source-driven fit/motion checks. Visual fidelity, torsion estimates and geometric interference are distinct evidence. Neither these records nor a render certifies a physical run.

## Dimensional and construction contract

```json
{
  "schema_version": 1,
  "likeness_floor": 0.9,
  "printed_parts": 20,
  "labels": [
    "frame",
    "bill",
    "lens",
    "head_rim",
    "dark_lens",
    "sensor",
    "neck_skin",
    "boot_left",
    "sole_left",
    "shin_left",
    "boot_right",
    "sole_right",
    "shin_right",
    "rotor",
    "left_wheel",
    "anchor",
    "roller_left",
    "pin_left",
    "roller_right",
    "pin_right"
  ],
  "overall_bbox": {
    "min": [
      -45.3,
      -20,
      0
    ],
    "max": [
      42,
      18,
      180
    ],
    "tolerance_mm": 0.25
  },
  "parameters": {
    "duck_lib": {
      "HEIGHT": 180,
      "PIXEL_SCALE": 0.32142857142857145,
      "REAR_Y": 18,
      "FRONT_HEAD_Y": -12,
      "WALL_MIN": 2.4,
      "LENS_OUTER_D": 19.6,
      "LENS_INNER_D": 10,
      "FACE_GAP": 0.2
    },
    "drive_lib": {
      "DRIVE_Y": -6,
      "DRIVE_Z": 10,
      "REAR_Y": 12,
      "REAR_Z": 6,
      "AXLE_D": 8.4,
      "BAND_BORE_D": 5.4,
      "BEARING_D": 8.8,
      "KEY_FLAT_RADIUS": 3.9,
      "KEY_FLAT_SOCKET": 4.0,
      "BONDED_WHEEL_BORE_D": 8.6,
      "PIN_D": 3.2,
      "ROLLER_BORE_D": 3.6,
      "PIN_SOCKET_D": 3.4,
      "AXIAL_GAP": 0.4,
      "CORD_D": 4,
      "CORD_WORKING_SPAN": 81.2,
      "MAX_WINDING_TURNS": 2
    }
  },
  "construction": [
    {
      "feature": "contour profiles",
      "module": "duck_lib",
      "function": "profile",
      "calls": [
        "make_polygon",
        "Face",
        "extrude"
      ],
      "operators": []
    },
    {
      "feature": "head, torso, pelvis, legs and mechanical relief",
      "module": "duck_lib",
      "function": "raw_frame",
      "calls": [
        "profile",
        "fillet",
        "cyl_y",
        "rounded_block",
        "extrude",
        "Ellipse"
      ],
      "operators": [
        "Add",
        "Sub"
      ]
    },
    {
      "feature": "bill and mouth recess",
      "module": "duck_lib",
      "function": "build_bill",
      "calls": [
        "profile"
      ],
      "operators": [
        "Sub"
      ]
    },
    {
      "feature": "purple lens ring",
      "module": "duck_lib",
      "function": "build_lens",
      "calls": [
        "cyl_y"
      ],
      "operators": [
        "Sub"
      ]
    },
    {
      "feature": "small oval sensor",
      "module": "duck_lib",
      "function": "build_sensor",
      "calls": [
        "extrude",
        "Ellipse"
      ],
      "operators": []
    },
    {
      "feature": "dark crown rim",
      "module": "duck_lib",
      "function": "build_head_rim",
      "calls": [
        "profile",
        "Box"
      ],
      "operators": [
        "Sub",
        "BitAnd"
      ]
    },
    {
      "feature": "segmented neck skin",
      "module": "duck_lib",
      "function": "build_neck_skin",
      "calls": [
        "profile",
        "rounded_block",
        "Box"
      ],
      "operators": [
        "Sub",
        "BitAnd"
      ]
    },
    {
      "feature": "rounded feet",
      "module": "duck_lib",
      "function": "foot_blank",
      "calls": [
        "rounded_block"
      ],
      "operators": []
    },
    {
      "feature": "rounded-block helper",
      "module": "duck_lib",
      "function": "rounded_block",
      "calls": [
        "Box",
        "fillet",
        "filter_by"
      ],
      "operators": []
    },
    {
      "feature": "boot/sole panels",
      "module": "duck_lib",
      "function": "build_boot",
      "calls": [
        "foot_front_blank",
        "Box",
        "drive_frame_cutters"
      ],
      "operators": [
        "Sub",
        "BitAnd"
      ]
    },
    {
      "feature": "shin plates",
      "module": "duck_lib",
      "function": "build_shin_skin",
      "calls": [
        "profile",
        "Box"
      ],
      "operators": [
        "BitAnd"
      ]
    },
    {
      "feature": "shaft wheel knob and bore",
      "module": "drive_lib",
      "function": "build_rotor",
      "calls": [
        "x_cylinder",
        "Cone",
        "Box"
      ],
      "operators": [
        "Add",
        "Sub"
      ]
    },
    {
      "feature": "bonded D-key wheel",
      "module": "drive_lib",
      "function": "build_left_drive_wheel",
      "calls": [
        "x_cylinder",
        "Box"
      ],
      "operators": [
        "Sub"
      ]
    },
    {
      "feature": "idler rings",
      "module": "drive_lib",
      "function": "build_rear_roller",
      "calls": [
        "x_cylinder",
        "mirror"
      ],
      "operators": [
        "Sub"
      ]
    },
    {
      "feature": "headed rear pins",
      "module": "drive_lib",
      "function": "build_rear_pin",
      "calls": [
        "x_cylinder",
        "mirror"
      ],
      "operators": [
        "Add"
      ]
    },
    {
      "feature": "fixed lacing anchor",
      "module": "drive_lib",
      "function": "build_fixed_anchor",
      "calls": [
        "x_cylinder",
        "Box"
      ],
      "operators": [
        "Add",
        "Sub"
      ]
    }
  ],
  "landmarks": [
    {
      "feature": "head crown and rim",
      "label": "head_rim",
      "bbox": {
        "min": [
          -28.607,
          -15,
          142
        ],
        "max": [
          31.868,
          -12.2,
          180
        ]
      },
      "min_faces": 30,
      "circular_radii_mm": [],
      "tolerance_mm": 0.25
    },
    {
      "feature": "purple lens annulus",
      "label": "lens",
      "bbox": {
        "min": [
          -11.25,
          -15,
          150.6
        ],
        "max": [
          8.35,
          -12,
          170.2
        ]
      },
      "min_faces": 4,
      "circular_radii_mm": [
        9.8,
        5
      ],
      "tolerance_mm": 0.25
    },
    {
      "feature": "dark primary lens",
      "label": "dark_lens",
      "bbox": {
        "min": [
          -6.05,
          -14.8,
          155.8
        ],
        "max": [
          3.15,
          -9.6,
          165
        ]
      },
      "min_faces": 3,
      "circular_radii_mm": [
        4.6
      ],
      "tolerance_mm": 0.25
    },
    {
      "feature": "small oval sensor",
      "label": "sensor",
      "bbox": {
        "min": [
          11.9,
          -13,
          158.9
        ],
        "max": [
          17.7,
          -10,
          161.9
        ]
      },
      "min_faces": 3,
      "circular_radii_mm": [],
      "tolerance_mm": 0.25
    },
    {
      "feature": "yellow bill and mouth seam",
      "label": "bill",
      "bbox": {
        "min": [
          -28.286,
          -18,
          124.071
        ],
        "max": [
          36.642857142857146,
          -12.2,
          150.429
        ]
      },
      "min_faces": 18,
      "circular_radii_mm": [],
      "tolerance_mm": 0.25
    },
    {
      "feature": "long segmented dark neck",
      "label": "neck_skin",
      "bbox": {
        "min": [
          -6.4285714,
          0,
          96
        ],
        "max": [
          22.5,
          2.8,
          127.1988416988417
        ]
      },
      "min_faces": 30,
      "circular_radii_mm": [],
      "tolerance_mm": 0.25
    },
    {
      "feature": "compact torso and paired hip bosses",
      "label": "frame",
      "bbox": {
        "min": [
          -45.3,
          -13,
          2.4
        ],
        "max": [
          42,
          18,
          180
        ]
      },
      "min_faces": 180,
      "circular_radii_mm": [
        2,
        6.5
      ],
      "tolerance_mm": 0.25
    },
    {
      "feature": "left yellow boot",
      "label": "boot_left",
      "bbox": {
        "min": [
          -36,
          -20,
          7.4
        ],
        "max": [
          -3,
          -7.2,
          17.4
        ]
      },
      "min_faces": 9,
      "circular_radii_mm": [],
      "tolerance_mm": 0.25
    },
    {
      "feature": "right raised yellow boot",
      "label": "boot_right",
      "bbox": {
        "min": [
          8,
          -20,
          15.4
        ],
        "max": [
          42,
          -7.2,
          25.4
        ]
      },
      "min_faces": 9,
      "circular_radii_mm": [],
      "tolerance_mm": 0.25
    },
    {
      "feature": "left purple sole",
      "label": "sole_left",
      "bbox": {
        "min": [
          -36,
          -20,
          2.4
        ],
        "max": [
          -3,
          -7.2,
          7.2
        ]
      },
      "min_faces": 9,
      "circular_radii_mm": [],
      "tolerance_mm": 0.25
    },
    {
      "feature": "right purple sole",
      "label": "sole_right",
      "bbox": {
        "min": [
          8,
          -20,
          10.4
        ],
        "max": [
          42,
          -7.2,
          15.2
        ]
      },
      "min_faces": 9,
      "circular_radii_mm": [],
      "tolerance_mm": 0.25
    },
    {
      "feature": "left dark shin",
      "label": "shin_left",
      "bbox": {
        "min": [
          -32.464,
          2,
          17.6
        ],
        "max": [
          -16.071,
          4.8,
          33.429
        ]
      },
      "min_faces": 6,
      "circular_radii_mm": [],
      "tolerance_mm": 0.25
    },
    {
      "feature": "right dark shin",
      "label": "shin_right",
      "bbox": {
        "min": [
          17.679,
          2,
          25.6
        ],
        "max": [
          31.111,
          4.8,
          39.536
        ]
      },
      "min_faces": 6,
      "circular_radii_mm": [],
      "tolerance_mm": 0.25
    },
    {
      "feature": "winding knob and shaft",
      "label": "rotor",
      "bbox": {
        "min": [
          -34.7,
          -16,
          0
        ],
        "max": [
          42,
          4,
          20
        ]
      },
      "min_faces": 12,
      "circular_radii_mm": [
        10,
        8,
        2.7
      ],
      "tolerance_mm": 0.25
    },
    {
      "feature": "left drive wheel",
      "label": "left_wheel",
      "bbox": {
        "min": [
          -35,
          -16,
          0
        ],
        "max": [
          -29,
          4,
          20
        ]
      },
      "min_faces": 5,
      "circular_radii_mm": [
        10
      ],
      "tolerance_mm": 0.25
    },
    {
      "feature": "left rear roller",
      "label": "roller_left",
      "bbox": {
        "min": [
          -34,
          6,
          0
        ],
        "max": [
          -30,
          18,
          12
        ]
      },
      "min_faces": 4,
      "circular_radii_mm": [
        6,
        1.8
      ],
      "tolerance_mm": 0.25
    },
    {
      "feature": "right rear roller",
      "label": "roller_right",
      "bbox": {
        "min": [
          30,
          6,
          0
        ],
        "max": [
          34,
          18,
          12
        ]
      },
      "min_faces": 4,
      "circular_radii_mm": [
        6,
        1.8
      ],
      "tolerance_mm": 0.25
    },
    {
      "feature": "replaceable elastic anchor",
      "label": "anchor",
      "bbox": {
        "min": [
          -41.2,
          -13,
          0.5
        ],
        "max": [
          -39.2,
          1,
          21
        ]
      },
      "min_faces": 12,
      "circular_radii_mm": [
        7,
        5.7
      ],
      "tolerance_mm": 0.25
    }
  ],
  "observed_contours": {
    "TORSO_PIXELS": [
      [
        98,
        308
      ],
      [
        125,
        301
      ],
      [
        143,
        296
      ],
      [
        143,
        289
      ],
      [
        153,
        292
      ],
      [
        160,
        301
      ],
      [
        169,
        303
      ],
      [
        207,
        315
      ],
      [
        238,
        316
      ],
      [
        239,
        356
      ],
      [
        234,
        373
      ],
      [
        202,
        377
      ],
      [
        121,
        374
      ],
      [
        103,
        367
      ],
      [
        93,
        355
      ],
      [
        91,
        322
      ]
    ],
    "PELVIS_PIXELS": [
      [
        112,
        369
      ],
      [
        222,
        370
      ],
      [
        237,
        393
      ],
      [
        227,
        447
      ],
      [
        190,
        452
      ],
      [
        174,
        455
      ],
      [
        146,
        455
      ],
      [
        120,
        450
      ],
      [
        106,
        436
      ]
    ],
    "BILL_PIXELS": [
      [
        82,
        165
      ],
      [
        274,
        132
      ],
      [
        281,
        135
      ],
      [
        282,
        143
      ],
      [
        284,
        149
      ],
      [
        283,
        157
      ],
      [
        282,
        185
      ],
      [
        274,
        201
      ],
      [
        254,
        211
      ],
      [
        224,
        214
      ],
      [
        220,
        201
      ],
      [
        180,
        200
      ],
      [
        155,
        205
      ],
      [
        140,
        207
      ],
      [
        112,
        196
      ],
      [
        88,
        189
      ],
      [
        82,
        180
      ]
    ]
  }
}
```
