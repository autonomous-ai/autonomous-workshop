---
title: Removable lamp and socket interfaces
tags: [lamp, socket, bayonet, twist-lock, contact, removable, coupon, motion, fit]
aliases: [lamp socket, twist lock, bayonet mount, printed receiver, replaceable bulb, fit coupon, test coupon]
sources:
  - skills/electromechanical-integration/references/lighting-discovery.md
  - skills/cad/references/motion-manifests.md
  - "experience: CAD booleans that could not predict shrinkage, elephant foot or contact spring force at a printed receiver"
related: [lighting-design, electrical-component-selection, joints, mechanism-verification, bayonet-and-twist-locks]
updated: 2026-10-01
---

# Removable lamp and socket interfaces

A removable lamp is not selected until its receiver and electrical contacts
are selected too. The same reasoning applies to any bought part that
twist-locks or bayonets into a printed body.

## Three bought parts, not one

Treat these as separate bought parts, each with its own evidence, search
record and mount:

- the exact lamp/emitter MPN;
- the exact purchased socket MPN, when one exists;
- a separate contact or connector MPN, when the socket does not include one.

## Prefer a purchased socket

Prefer a purchased socket whose manufacturer documentation explicitly names
the lamp family or mating interface. The printed product then *seats the
socket*. It does not recreate uncertain spring contacts, terminal geometry or
an undocumented proprietary lamp base. If no authoritative drawing or verified
physical sample defines the mate, do not invent a twist-lock channel, drill a
nominal hole, or claim compatibility from a similar-looking package model.

## When a printed receiver is allowed

Only when the interface is documented and its electrical contacts remain
bought, rated components:

- derive the female path from the male lamp lugs or threads, from one source
  dimension, with clearance applied once through `cadfits`
  ([[joints#two-fit-classes-per-project]]);
- record why a purchased socket was not used;
- declare lamp and receiver/contact MPNs with source URL and revision; the
  interface type and datum, lug count, insertion depth, lock angle and
  direction; the CAD clearance and how it was derived; the retention stop;
  connector, tool/finger access and service direction.

## Motion is a five-phase contract

Every removable lamp is checked through all five phases:

1. `insert`: axial insertion to the rotation datum is clear;
2. `lock`: the locking rotation is clear;
3. `retained`: an axial pull in the removal direction is blocked while locked;
4. `unlock`: the reverse rotation is clear;
5. `remove`: axial extraction after unlocking is clear.

Phases that begin installed are allowed seated contact. **A clear insertion
alone proves only that a pocket is reachable, not capture.** A blocked pull
alone can be a collision in the wrong direction: state which way the user or
stored energy drives the lamp, and put the retaining shoulder in front of that
direction ([[mechanism-verification#4-what-the-manifest-must-contain]]).

For a threaded interface, the rotation is only a rigid-body proxy. A rigid
sweep cannot follow helical thread engagement or predict tightening torque.
Those remain coupon or prototype findings, not geometry claims.

## Physical fit needs a real-hardware coupon

CAD and exact STEP booleans cannot predict printer shrinkage, elephant foot,
surface texture, support scars, material creep, contact spring force or vendor
tolerance. Before claiming that a printed receiver physically fits:

- print a small coupon containing the complete insertion and locking
  interface, in the same material, process, nozzle/layer settings and
  orientation as the final part;
- test **at least three** candidate clearances with the exact production lamp
  and receiver/contact samples (for example 0.15 / 0.25 / 0.35 mm), and keep the
  current CAD clearance among the candidates even while the coupon is only
  planned;
- record status, material, process, orientation, hardware sample identifiers,
  candidate clearances, method and result.

`planned` means physical fit is still unverified. `failed` blocks the
interface. `passed` must name a selected clearance that was actually among the
tested candidates, and the CAD and spec are updated to that value before final
manufacture.
