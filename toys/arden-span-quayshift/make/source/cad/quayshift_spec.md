# QUAYSHIFT construction specification

## 1. Overall read
Original miniature canal-town construction puzzle. One perspective concept collage was observed; hidden sides and all metric geometry are newly designed. See reference_read.md and ref/concept.png. Deep voids, varied flat-roof masses and broad terraces carry the architecture. Exact inventory follows the user's grammar, not the unverified illustration.

## 2. Top view
[assumed] PITCH=32 mm; BOARD=184 mm; MARGIN=12 mm. Logical field is five columns by five rows. C1 and C5 are the only perimeter openings. Reserved arch strips have end-cell feet and one through-cell; D is an L, E/F are dominoes, G/H singletons. Placement states are in layouts.json; all pieces upright, quarter-turn orientations, no stacking. Inset feet leave [assumed] INSET=0.4 mm boundary tolerance. Ornament remains inside the cell reservation.

## 3. Front view
[assumed] FLOOR=4 mm. Maximum tower is [assumed]84 mm above floor. High arch width [assumed]32 mm, HIGH_SPRING=28 mm, semicircle radius [assumed]16 mm and apex [inferred]44 mm. Low arch apex [assumed]16 mm rejects the cabin. Neither opening has a sill. Ferry is [assumed] FERRY_HEIGHT=20 mm above floor, FERRY_RADIUS=13 mm.

## 4. Side view
[assumed] PORTAL_DEPTH=12 mm; PORTAL_Y=19.6 mm. Spans end flush with rear feet at [inferred]31.6 mm. Print arches on rear faces. A high arch's elevated semicircle and end towers create true architectural mass. Other buildings have stepped porches, set-back walls and roof terraces. All rear sides are reconstructed.

### 4b. Visible components
Eight architecture modules each have integral feet and substantial upper mass. A/B are differently massed high bridge buildings; C is a visibly lower gate with side houses. D joins perpendicular wings around an open corner. E/F pair tall houses with lower terraces. G/H are different-height tower houses. The board is a continuous dark water field inside a substantial rim. The ochre ferry has a broad round-envelope hull with flat stern, tapered underside and lower recessed-window cabin. No trees, figures, railings, moving drive or decorative extra parts.

## 5. Size and confidence
User starting dimensions anchor the design; values remain design assumptions until measured. [assumed] CABIN_WIDTH=12 mm and CABIN_LENGTH=18 mm. Cabin width was reduced from [assumed]14 mm after fore/aft-only finger access failed in the first exact proof. A [assumed]10 mm diameter vertical fingertip proxy can use corner and side contacts; physical comfort remains unproven. Floor grid is recessed [assumed]0.25 mm by [assumed]0.35 mm, never a raised seam. Bed declaration: --bed 220x220x220.

## 6. Decomposition and selected design
Ten separate removable rigid parts: A–H, tray, ferry. One single-color solid per part using specified sRGB channels; no color inserts. Broad loose gravity contacts, no fasteners. Full strip reservations prevent interpenetrating placement. Selected rear-flush bridges provide a flat manufacturing datum; centered spans were rejected. Selected rounded cabin in a circular ferry envelope makes turning conservative. No standard mechanical, electrical, powered or bought device geometry is needed. No powered design domain is active. No research-derived supplier dimensions or originality clearance claimed.

### 6g. Construction selection
Exterior: unions of prismatic architectural masses and actual recessed arched openings. Mechanics: freely placed rigid solids; height-filtered hand-translated travel. Electrical, lighting and bought devices: N/A. Initial proof sources/results are preserved outside the delivery CAD tree. Every final layout must be rebuilt against final solids.

## 7. Feature operations and verification
Floor and perimeter: Box unions; shallow Box and custom glyph-profile cuts. Plinths: connected inset Boxes confined to footprint. Towers: Box union, roof pocket Box subtract, arched window Cylinder plus jamb Box cutter. Portals: rear slab minus full-depth jamb and circular profile; no floor under the gap. Steps: union tread Boxes with monotonically increasing heights and full bearing. Ferry: Cone and Cylinder hull union, stern/foredeck cuts and RectangleRounded cabin extrude; blind window cuts preserve solid cabin. Local selectors are named assembly children a–h/tray/ferry; coordinate-target audits resolve portal and roof features from exact solids. Cosmetic geometry may be revised for source print checks without changing grammar.

Required evidence: all solids positive and single; assembled positioning and interference; finite swept envelope contains actual ferry and clears every advertised route including right-angle turns and outer entry/exit; actual low-gate collision; fingertips and vertical access; floor continuity; support COM assumptions; print orientation and source gates; independent final image review. No CAD result proves manufacture, comfort, fun or demand.
