# Independent supporting-neck audit
Auditor: Mara Masque. Scope: source review plus numeric 2D cubic sampling only; no CAD generation or product geometry edits. Source rainward_lib.py SHA256: 3260b49a181874915c7c1f6b3c7a53aa35e7a183b21ba615e0028dbb268b2efc.

**The current upper split branch does need a lower notch.** Its supporting neck is materially below 2 mm, not merely the natural narrowing at a rounded cap.

Actual cubic segments sampled at 401–601 evenly spaced parameters were compared by Euclidean distance between opposing non-terminal boundaries. These are approximate design-screening distances, not the CAD thickness gate.

- Current upper outside to upper notch edge: 1.467 mm near outer(−2.461,3.018) and inner(−3.2,1.75).
- Current upper outside to rounded notch root: 1.391 mm near outer(−2.234,2.885) and root(−2.934,1.683). This occurs in the load path, far from the terminal cap.
- Current lower branch: 2.000 mm minimum at its cap shoulder x−4; rounded root clearance about 2.311 mm.
- Current single tail: 1.981 mm at outer(−4.091,3.826) and inner(−4.740,1.954). This is a small supporting-neck shortfall. Strict 2 mm preservation merits the adjustment below.

## Exact recommended split-tail correction
Keep LEADING, TRAILING and the first outer sweep unchanged. Replace FORK_CURVES segments 3 through 10 (zero-indexed full concatenated list) with:
~~~
[(-5,4),(-5.552,4),(-6,3.5296),(-6,2.95)]
[(-6,2.95),(-6,2.3704),(-5.552,1.9),(-5,1.9)]
[(-5,1.9),(-4.3,1.9),(-3.7,.8),(-3.2,.8)]
[(-3.2,.8),(-2.533,.8),(-2.533,-.2),(-3.2,-.2)]
[(-3.2,-.2),(-3.6,-.2),(-3.7,-.45),(-4,-.45)]
[(-4,-.45),(-4.552,-.45),(-5,-.898),(-5,-1.45)]
[(-5,-1.45),(-5,-2.002),(-4.552,-2.45),(-4,-2.45)]
[(-4,-2.45),(-2.8,-2.45),(-2.1,-2.2),(-1,-2.8)]
~~~
These lower the upper-notch root by 0.95 mm and the complete short lower branch by 0.95 mm, retaining its 2 mm cap diameter. The upper terminal cap becomes a slightly oval 1.0×1.05 mm half-cap, providing 2.1 mm vertical shoulder thickness. Exact envelope remains x−6→6 and y−4→4. Branches remain staggered 1 mm longitudinally with a curved split in the final approximately 3 mm.

Approximate opposing-boundary distances for this candidate:
- Upper outside to upper inner edge: 2.078 mm.
- Upper outside to rounded notch root: 2.213 mm.
- Lower branch outside to inside: 2.000 mm at cap shoulder.
- Lower outside to rounded root: 2.217 mm.

Lowering only the upper notch while leaving the lower branch fixed would consume the gap or weaken the lower branch; move both notch and short branch as specified.

## Single-tail minor adjustment
Keep its outer sweep, LEADING and TRAILING. Replace the two terminal cap segments with the same oval-cap segments above, then replace its return segment by:
~~~
[(-5,1.9),(-3.6,1.9),(-2.1,-2.2),(-1,-2.8)]
~~~
This adds 0.1 mm shoulder material without changing the envelope. Recompute the final distance after application; do not round the original 1.981 mm up to a 2 mm claim.

Terminal cap interiors are excluded deliberately: slices approaching a rounded endpoint tend to zero and do not measure a neck. Proposed coordinates still require exact wire validity, adjacent-lane clearance, thickness gates and visual inspection. No blind-recognition pass is claimed.
