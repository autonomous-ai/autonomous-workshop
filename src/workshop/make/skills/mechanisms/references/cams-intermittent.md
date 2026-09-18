# Cams and intermittent motion

## Cam + follower

A cam turns continuous rotation into any lift schedule: rise, dwell, fall,
dwell. Specify it as segments whose durations sum to 360°:

```python
CAM_SEGMENTS = [   # (duration_deg, lift_at_end_mm, law)
    (120, 8.0, "cycloidal"),
    ( 60, 8.0, "dwell"),
    (120, 0.0, "cycloidal"),
    ( 60, 0.0, "dwell"),
]
assert sum(d for d, _, _ in CAM_SEGMENTS) == 360
assert CAM_SEGMENTS[-1][1] == 0.0      # returns to where it started
```

### Motion laws (u = fraction of the segment, 0..1; lift fraction f(u))

| law | f(u) | use |
|---|---|---|
| cycloidal | `u - sin(2πu) / (2π)` | default: zero velocity and acceleration at both ends, quiet |
| harmonic | `(1 - cos(πu)) / 2` | smooth, but an acceleration jump at the ends |
| linear | `u` | infinite acceleration at the ends — the follower bangs; only for very slow hand cams |

### Base circle and pressure angle

For a radial translating follower with roller radius `Rr` on base circle `Rb`:

```text
tan φ = (ds/dθ) / (Rb + Rr + s)          φ = pressure angle
```

Keep `φ <= 30°` for a translating follower, `<= 45°` for an oscillating
one. Above that the follower wedges sideways in its guide instead of rising.
Fix it with a **larger base circle** or a **longer rise duration** — never by a
steeper law. Sample the lift table at ≥ 1° and assert the maximum.

The pitch curve is the roller centre path, radius `Rb + Rr + s(θ)`; the cam
profile is that curve offset inward by `Rr`. The concave parts of the profile
must have radius > `Rr` or the roller cannot follow them.

### Keeping the follower on the cam

| retention | how | note |
|---|---|---|
| gravity | follower above the cam, light | automata default; fails if the toy tips |
| spring / band | pulls the follower down | a force no rigid gate checks — open item |
| grooved (face) cam | follower pin in a track | positive both ways; the track width is `slot_for(pin, RUN)` |
| conjugate / yoke | two cams or a constant-breadth cam in a yoke | positive, no spring, more parts |

A follower guide (bushing) length ≥ 2 × the follower diameter, and the
follower's top stop (a head, a collar) is its `blocked` condition upward.

## Geneva drive

Indexes a wheel one slot per crank turn and locks it in between. `n` slots,
centre distance `C`:

```text
crank (pin) radius     a = C sin(π/n)
wheel slot-mouth radius b = C cos(π/n)
index per crank turn   360°/n
engaged crank angle    180° - 360°/n     (dwell: the rest)
minimum slot depth     a + b - C
wheel angle while engaged (crank φ from the line of centres, λ = sin(π/n)):
    tan β = λ sin φ / (1 - λ cos φ)
```

The pin must enter the slot tangentially, which the formulas above guarantee;
retyping `a` independently breaks it. The locking disc on the crank and the
concave arcs on the wheel hold the wheel during the dwell — both are
geometry, and the lock is a `blocked` rotation of the wheel with the crank at
mid-dwell. Output angular velocity peaks mid-index at several times the input:
sample for the wheel, not for the crank (see `verification.md`).

## Ratchet and pawl

- Tooth: radial face on the locking side, sloped back (~60°) on the other.
- Pawl pivot placed so the line of force from pawl tip to pivot passes
  *inside* the tooth tip: load pulls the pawl into the tooth, not out.
- Pawl held in by gravity, a printed flexure, or a band — say which.
- Checks: the wheel turns `clear` in the free direction, `blocked` in the
  locking direction with the pawl engaged; the pawl's own retention
  (its pivot) is in the retention chain.

## Escapement

An anchor escapement turns a stored torque into ticks and needs a pendulum
or balance to time it; printable, but tuning is empirical. Record the period
and the stored-energy runtime as open items — no geometry gate reaches them.
