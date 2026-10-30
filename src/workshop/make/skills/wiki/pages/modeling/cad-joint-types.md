---
title: CAD joint types for assembly placement
tags: [assembly, joint, placement, location, revolute, linear, cylindrical, ball, rigid, build123d]
aliases: [RigidJoint, RevoluteJoint, LinearJoint, CylindricalJoint, BallJoint, connect_to, AssemblyHelper frame, mate, joints api, angular_range, linear_range, joint_location]
sources:
  - skills/cad/references/positioning.md (joint selection sections; before the move)
  - https://build123d.readthedocs.io/en/latest/joints.html
related: [joints, modeling-failure-modes, frames-and-rotations, build123d-operations-and-export]
updated: 2026-10-10
---

# CAD joint types for assembly placement

These are *placement* joints in source — how a part is positioned in the
generated model — not the physical joints a mechanism needs (those are
[[joints]]). A build123d joint repositions the moving part once, when the
source runs; the exported STEP holds the resolved static placement, not a
persistent constraint.

## When a joint beats a raw transform

Use `AssemblyHelper` / build123d joints when assembly intent is clearer as a
relationship between part datums than as a raw transform:

- lid-to-base, cover-to-frame, bracket-to-rail, flange-to-pipe, pin-to-hole,
  shaft-to-bearing;
- hinge, slider, screw-like, cylindrical, ball/gimbal, or other
  motion-positioned assemblies;
- repeated or library components that already expose joints;
- source assemblies where a change to one dimension should recompute part
  placement.

Direct `Location(...)` transforms are acceptable for simple static layouts
when they are parameterised and documented, such as a row of identical
spacers or a visual exploded view. Raw build123d joints are acceptable for
advanced cases `AssemblyHelper` does not cover. The datum every numeric
`Location` must name, the fixed-first `connect_to()` direction, and how to
frame an imported part from its measured faces, axes and bolt pattern are in
`skills/cad/references/positioning.md`.

## Choosing the joint type

Use the simplest joint that expresses the relationship:

| joint | helper frame | use for | defined by |
|---|---|---|---|
| `RigidJoint` | `asm.rigid_frame()` | fixed placement, face-to-face seating, mounting datums, imported components with known interfaces | a `Location` |
| `RevoluteJoint` | `asm.revolute_frame()` | hinge or rotational pose | an `Axis`, driven by an angle parameter for a static pose |
| `LinearJoint` | `asm.linear_frame()` | slider, latch, telescoping component | an `Axis`, driven by a position parameter |
| `CylindricalJoint` | `asm.cylindrical_frame()` | combined axial translation and rotation: screw-like or pin-in-slot | an `Axis` |
| `BallJoint` | `asm.ball_frame()` | gimbal or spherical orientation | a `Location` and angular ranges |

When only final static placement matters and no meaningful joint datum exists,
use explicit `Location` transforms and validate them.

For a moving mechanism the pose comes from the kinematic solution, not from a
joint angle chosen by eye ([[mechanism-verification#2-one-kinematics-module]]).

## Joints API contract

The five joint classes are `RigidJoint`, `RevoluteJoint`, `LinearJoint`,
`CylindricalJoint` and `BallJoint`. They take `label` (unique within a part),
`to_part`, and then `joint_location` (Rigid, Ball) or `axis` (Revolute,
Linear, Cylindrical) plus `angular_range` / `linear_range`.

- `a.joints["x"].connect_to(b.joints["y"])` keeps **a's** part fixed and
  **moves b's** part.
- Valid pairs: Rigid↔Rigid; Ball↔Rigid (`angles`); Revolute↔Rigid (`angle`);
  Linear↔Rigid or Revolute (`position`); Cylindrical↔Rigid (`position`,
  `angle`).
- A value outside the declared range raises an exception, which is a free
  limit check.
- Inside a `BuildPart` the `to_part` is optional, because the builder
  attaches the joints on exit.
