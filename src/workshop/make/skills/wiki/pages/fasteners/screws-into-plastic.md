---
title: Screwing directly into plastic
tags: [self-tapping, thread-forming, pilot-hole, boss, delta-pt, pt-screw, direct-screwing]
aliases: [self tapper, plastite, thread forming screw, pilot hole for plastic, screw boss, WN 1411, WN 1442]
sources:
  - EJOT PT® Screw brochure 02.11, boss design pp. 6–7, torque pp. 8–9, WN 1411 dimensions p. 11 (https://apexfasteners.com/fasteners/images/Brochure_EJOT_PT_02.11_en.pdf)
  - https://www.ejot.de/medias/sys_master/Industry_Flyer/Industry_Flyer/h11/hc7/9331662782494/EJOT-DELTA-PT-Flyer-08.23-en.pdf (search excerpt: dh = 0.8 × d1, up to 0.88 × d1; boss di = 2 × d1)
  - https://www.cnckitchen.com/blog/threaded-inserts-for-3d-prints-cheap-vs-expensive (M3 into 2.7 mm printed hole, 142 kg, 1 Nm)
  - https://hackaday.com/2025/09/02/no-need-for-inserts-if-youre-prepared-to-use-self-tappers/ (practitioner hole sizes)
related: [heat-set-inserts, fastener-torque-and-stripping, metric-screw-clearance-holes, wall-thickness-and-hollowing, printed-threads-and-bosses]
updated: 2026-09-23
---

# Screwing directly into plastic

A screw can form its own thread in a printed hole. It holds almost as well as an
insert in pull-out but tolerates far less torque and few re-assemblies
([[heat-set-inserts#what-the-tests-show]]). Use it for joints assembled once or
rarely.

## Pilot hole: about 0.8 × the screw diameter

EJOT's design rule for its PT and DELTA PT plastic-forming screws is a hole of
`db = 0.8 × d1` (d1 = nominal screw diameter). For heavily filled or
high-strength plastics it rises to `0.88 × d1`. EJOT's per-material table for
PT screws (hole Ø, boss outer Ø, installation depth):

| material | hole db | boss outer dA | installation depth ti |
|---|---|---|---|
| ABS, ABS/PC | 0.80 d | 2.00 d | 2.00 d |
| ASA | 0.78 d | 2.00 d | 2.00 d |
| PA 6, PA 6.6, PBT, PET | 0.75 d | 1.85 d | 1.70 d |
| PET-GF30 | 0.80 d | 1.80 d | 1.70 d |
| PE-LD | 0.70 d | 2.00 d | 2.00 d |
| PE-HD | 0.75 d | 1.80 d | 1.80 d |
| POM | 0.75 d | 1.95 d | 2.00 d |
| PP | 0.70 d | 2.00 d | 2.00 d |
| PP-GF30 | 0.72 d | 2.00 d | 2.00 d |
| PS, PVC (rigid) | 0.80 d | 2.00 d | 2.00 d |
| SAN | 0.77 d | 2.00 d | 1.90 d |

These are moulded-plastic numbers. EJOT lists PC, PMMA, PPO, PEEK, PPS and
glass-filled PA/PBT for its DELTA PT screw instead. For printed parts, treat
the table as the starting ratio and prove it on a coupon; printed holes come
out undersize ([[metric-screw-clearance-holes#printed-clearance-holes]]).

Practitioner data points for machine screws in printed parts: an M3 in a
2.7 mm hole (0.9 d) pulled out at 142 kg in CNC Kitchen's test. Makers report
M3 in a 3.0 mm printed hole and M4 in 3.7 mm working in PLA (anecdotal, no
test data).

## The boss

EJOT's boss geometry: counterbore the entry to `de = d1 + 0.2 mm` (EJOT: this
balancing hole spreads the edge stress), and make the outer diameter about 2 × d1 (per
material in the table above). If the boss cracks during assembly, EJOT's order
of repair is:

1. reduce the boss outer diameter (a moulding concern: thick sections sink);
2. enlarge the hole, which lowers axial strength;
3. win that back by increasing installation depth.

Printed bosses are also anisotropic: see [[layer-anisotropy]] before relying
on hoop strength across layers.

## Torque window

A thread-forming joint has an installation (forming) torque Ti and a stripping
torque Ts. A reliable assembly needs the tightening torque clearly between
the two. EJOT picks the hole where Ts,min / Ti,max is largest and sets:

```text
Tt = 0.5 × (0.5 × Ts,min + 1.5 × Ti,max)
```

Worked example from EJOT (K40 screw, PA6-GF30, 3.2 mm hole, 6 mm depth):
Ti,max = 1.01 Nm, Ts,min = 3.01 Nm → Tt = 1.51 Nm. Drive speed at most
500 rpm (300–500 recommended) to avoid damaging the plastic.

## Screw forms

EJOT PT K30 to K100 (d = 3–10 mm) have a 30° flank angle, and a pitch of
about 0.45 × d (K40: pitch 1.79 mm, core 2.17 mm). That is coarser than a
machine screw (M4: 0.7 mm). The narrow flank displaces less plastic, so the
radial stress that splits the boss stays lower. A machine screw also works in
a printed hole. In CNC Kitchen's M3 tests its plastic thread sheared at about
1 Nm, against 3–4 Nm for an insert ([[fastener-torque-and-stripping]]).

## Checks

```python
assert 0.70 * d <= hole_d <= 0.90 * d, "pilot hole outside the plastic-forming range"
assert boss_od >= 1.8 * d, "boss thinner than the EJOT table (1.80–2.00 d)"
assert engagement >= 1.7 * d, "installation depth below the EJOT minimum"
```
