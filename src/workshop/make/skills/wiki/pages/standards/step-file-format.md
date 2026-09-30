---
title: The STEP file format
tags: [step, iso-10303, ap203, ap214, ap242, pmi, units, assembly, exchange]
aliases: [stp, iso 10303-21, application protocol, part 21, step schema, step colours, step units, product structure]
sources:
  - https://en.wikipedia.org/wiki/ISO_10303
  - https://www.capvidia.com/blog/best-step-file-to-use-ap203-vs-ap214-vs-ap242
  - https://cadshift.com/blog/what-is-step-file-format/
  - https://occt3d.com/dev/doc/overview/html/occt_user_guides__step.html
related: [build123d-operations-and-export, brep-vs-source, occt-topology-and-tolerance, mesh-to-step-conversion]
updated: 2026-09-23
---

# The STEP file format

STEP (ISO 10303) is this repository's only deliverable format. Knowing what an
application protocol can carry, and how units, tolerances and assemblies are
encoded, explains most "the file opened wrong" reports.

## Application protocols

| AP | title | carries |
|---|---|---|
| **AP203** | Configuration controlled 3D designs of mechanical parts and assemblies | geometry, topology, configuration management, assembly structure; wireframe, surface, faceted and solid B-rep models. The minimum usable geometry-plus-assembly file |
| **AP214** | Core data for automotive mechanical design processes | everything in AP203 plus **colours and layers**, textual annotations tied to geometry, GD&T as graphical presentation, validation properties, kinematic structures |
| **AP242** | Managed model based 3D engineering (ed. 1 2014, ed. 2 2020) | merges AP203 and AP214 upward-compatibly, and adds **semantic PMI** (machine-readable GD&T), tessellated geometry, 3D kinematics, composites, harnesses, piping, colour on vertex, scanner data, additive-manufacturing data |

AP203 and AP214 are withdrawn as ISO standards and superseded by AP242.
They are still widely exchanged, and AP214 is still the default of many writers,
including OCCT's.

**Consequences:**
- Colours need AP214 or AP242. An AP203 file drops them.
- GD&T that a CAM or inspection tool can *read* needs AP242 semantic PMI.
  AP214's GD&T is only a picture.
- A mesh inside a STEP file (AP242 tessellation) is still a mesh. It is not an
  exact B-rep ([[mesh-to-step-conversion]]).

## File structure (Part 21)

A `.stp`/`.step` file is text:

```text
ISO-10303-21;
HEADER;  FILE_DESCRIPTION(...); FILE_NAME(...); FILE_SCHEMA(('AUTOMOTIVE_DESIGN ...'));  ENDSEC;
DATA;    #1=PRODUCT(...); #2=PRODUCT_DEFINITION(...); ... ENDSEC;
END-ISO-10303-21;
```

- `FILE_SCHEMA` names the AP. `AUTOMOTIVE_DESIGN` is AP214, for example.
  Read it first when a colour or PMI "went missing".
- Entities are numbered instances `#n=TYPE(...)` referencing each other.
  Part 28 is an XML encoding of the same model. Part 21 is what you will meet.

Entities worth recognising:

| entity | holds |
|---|---|
| `PRODUCT`, `PRODUCT_DEFINITION` | one part or assembly and its definition |
| `NEXT_ASSEMBLY_USAGE_OCCURRENCE` | a parent → child instance in the assembly tree |
| `STYLED_ITEM`, `COLOUR_RGB` | presentation colour on a shape |
| `SI_UNIT`, `CONVERSION_BASED_UNIT` | the length and angle units of the geometry |
| `UNCERTAINTY_MEASURE_WITH_UNIT` | the file's stated geometric uncertainty (tolerance) |

## Units are declared, not implied

Lengths are in the unit the file declares (`SI_UNIT` with a milli prefix
for mm, or `CONVERSION_BASED_UNIT` for inches). A reader that ignores the
declaration, or a writer that declares the wrong one, gives a part 25.4× off.
Check the bounding box against an expected size after any import
([[preferred-numbers-and-units#inch-and-millimetre]]).

## Tolerance in the file

`UNCERTAINTY_MEASURE_WITH_UNIT` records one global uncertainty, and each
kernel fills it differently. Parasolid derives it from per-edge tolerances,
ACIS/Inventor writes a fixed 0.1 mm, and OCCT offers least / average /
greatest. The same part exported by three kernels gives three different
files. On reading, OCCT uses the file's value by default
(`read.precision.mode = 0`), capped by `read.maxprecision.val` (default 1).

## What the translator writes

OCCT's STEP translator parameters (build123d's `export_step` sets the
equivalents):

| parameter | default | meaning |
|---|---|---|
| `write.step.schema` | AP214CD | also AP214DIS, AP203, AP214IS, AP242DIS |
| `write.precision.mode` | 0 (average) | −1 least, 1 greatest, 2 user value (`write.precision.val`, default 0.0001) |
| `write.step.unit` | MM | converts on write when set differently |
| `write.surfacecurve.mode` | 1 (on) | writes pcurves; off makes smaller files |
| `read.step.product.mode` | 1 | reads the assembly structure through `PRODUCT_DEFINITION` |
| `read.step.assembly.level` | 1 (all) | 2 assembly, 3 structure, 4 shape |
| `xstep.cascade.unit` | MM | the internal unit after reading |

Names, colours, layers and validation properties go through the XDE
translator (`STEPCAFControl`), which build123d uses when shapes carry
`label`/`color`. A bare shape written through the plain translator loses them.

## Checks after writing a STEP

- Re-import it: the solid count, bounding box and volume match the source.
- `FILE_SCHEMA` is the AP you intended (colours need AP214/AP242).
- The assembly tree has one `NEXT_ASSEMBLY_USAGE_OCCURRENCE` per placed
  instance, and child names are the labels you set.
