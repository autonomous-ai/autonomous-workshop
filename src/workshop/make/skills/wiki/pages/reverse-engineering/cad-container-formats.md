---
title: Reading native CAD container files
tags: [solidworks, sldprt, sldasm, parasolid, file-format, assembly-pose, reverse-engineering]
aliases: [sldprt to step, sldasm poses, sw3d container, solidworks file format, native cad import]
sources:
  - https://github.com/BlinkingSun/sldprt2step (Apache-2.0)
  - "toolchain: SolidWorks 2015+ files decoded by hand (sw3d sections, nibble-swapped names, COMPINSTANCETREE XML)"
related: [kit-assembly-poses, mesh-to-step-conversion]
updated: 2026-09-23
---

# Reading native CAD container files

A supplied native CAD file is better evidence than any mesh exported from it:
it holds exact B-rep geometry, and an assembly file holds the poses.

## SolidWorks parts convert to STEP without SolidWorks

`github.com/BlinkingSun/sldprt2step` (Apache-2.0) converts `.SLDPRT` to STEP
AP214 in pure Python stdlib, with no network and no CAD kernel. It is a real
Parasolid XT reader, not a preview or mesh dump. Audit it before running
(external code): the converter core imports only stdlib,
`subprocess`/`tempfile`/`random` appear only under `tests/`, and it writes
exactly one file, the `-o` path.

- Its exit code is non-zero when the conversion emits warnings (approximated
  intersection curves). Check whether the `.step` was written before treating
  a non-zero exit as failure.
- It converts parts only. A `.SLDASM` fails with
  `no partition transmit found`, because an assembly holds no Parasolid
  geometry.

## The container is not encrypted

SolidWorks files from 2015 on are **not** OLE compound documents. They are
"sw3d" flat sections marked by the bytes `14 00 06 00 08 00`, each a
raw-deflate blob. A scan for the OLE magic, PNG headers or `Parasolid` finds
nothing, and the file looks encrypted (entropy ~7.98). It is not.

Section layout: the marker, the type id at +6, compressed/decompressed sizes at
+14/+18, the name length at +22, then the name and a raw-deflate payload.
**Section names are stored with each byte's nibbles swapped** (`0x43` 'C' is
written `0x34`). Unswapping makes the directory readable: `Contents/CMgr`,
`Contents/Config-0-MatesList`, `swXmlContents/COMPINSTANCETREE`, `PreviewPNG`.

Every `.SLDPRT` and `.SLDASM` also carries a 640 × 480 PNG preview inside one
of its deflate blobs. Carving those out gives a render of each part and of the
whole assembly without any CAD, which is usable reference imagery when the
assembly will not convert.

## Assembly files carry the poses

`swXmlContents/COMPINSTANCETREE` is UTF-8 XML with a NUL after every byte. It
holds every `swModel` and, for each `swReference`, a `swTransform` of sixteen
doubles: a row-major 4 × 4 matrix in the row-vector convention, translation in
**metres**. A part point `p` lands at `R^T p + t`. Sub-assemblies nest, and each
instance carries its own solved child transforms, so composing down the tree
gives every solid's world pose, by name, with determinant +1.

Scanning decompressed blobs for runs of nine doubles that form a rotation does
find matrices, but it cannot say whose they are, and a placement without a
name is not a placement. The tree gives name and matrix together.

Read the tree **before** concluding that a part set's pose must come from
renders or from mates ([[kit-assembly-poses#where-a-pose-can-come-from]]).
Check the result cheaply: transform each part's bore centres by its own matrix
and look for coincident groups.
