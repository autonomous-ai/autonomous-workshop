#!/usr/bin/env python3
"""Pack 27 pieces onto printer beds. Shelf packing, rotation allowed.

text2cad ships ONE product a day, so it never had to lay out a box of parts.
Two rules here are not general bin-packing, they are board game rules:

1. Every copy of a design goes on ONE plate. `ship` x12 drop through the
   magazine's exit port; twelve ships printed across twelve sessions carry
   twelve different shrink offsets, and the pair the GDD is tightest on
   (ship <-> ship_magazine, 0.4mm) is exactly where that shows up.
2. Print time never rejects a layout - Tam, 2026-08-14: one product a day is a
   design cadence, not a machine constraint. Report the hours, never gate them.
"""
import json
import sys
from pathlib import Path

GAP = 4.0  # mm between pieces, and from the bed edge


def _fits(w, h, bw, bh):
    return (w <= bw and h <= bh) or (h <= bw and w <= bh)


def pack_design(pieces, bed_x, bed_y):
    """Shelf-pack one design's copies onto as few plates as possible."""
    plates, cur, shelf_y, shelf_h, x = [], [], GAP, 0.0, GAP
    for w, h in pieces:
        if h > w and _fits(w, h, bed_x, bed_y) and w > bed_x - 2 * GAP:
            w, h = h, w                                  # rotate to fit width
        if x + w + GAP > bed_x:                          # new shelf
            shelf_y += shelf_h + GAP
            x, shelf_h = GAP, 0.0
        if shelf_y + h + GAP > bed_y:                    # new plate
            plates.append(cur)
            cur, shelf_y, shelf_h, x = [], GAP, 0.0, GAP
        cur.append({"x": round(x, 1), "y": round(shelf_y, 1),
                    "w": round(w, 1), "h": round(h, 1)})
        x += w + GAP
        shelf_h = max(shelf_h, h)
    if cur:
        plates.append(cur)
    return plates


def layout(components, bed_x=256.0, bed_y=256.0):
    """-> [{"plate": n, "designs": [...], "pieces": n, "used_mm2": f}]"""
    out, plate_no = [], 0
    big_first = sorted(components, key=lambda c: -max(c["target_bbox_mm"][0],
                                                      c["target_bbox_mm"][1]))
    for c in big_first:
        bx, by, _ = c["target_bbox_mm"]
        if not _fits(bx, by, bed_x, bed_y):
            out.append({"plate": None, "designs": [c["id"]], "pieces": c["qty"],
                        "used_mm2": 0.0,
                        "error": f"{c['id']} {bx}x{by}mm does not fit a "
                                 f"{bed_x}x{bed_y}mm bed"})
            continue
        for slots in pack_design([(bx, by)] * c["qty"], bed_x, bed_y):
            plate_no += 1
            out.append({"plate": plate_no, "designs": [c["id"]],
                        "pieces": len(slots),
                        "used_mm2": round(sum(s["w"] * s["h"] for s in slots), 1),
                        "slots": slots})
    return out


def main() -> int:
    out_dir = Path(sys.argv[1]).resolve()
    import os
    bed_x = float(os.environ.get("BED_X", "256"))
    bed_y = float(os.environ.get("BED_Y", "256"))
    data = json.loads((out_dir / "components.json").read_text(encoding="utf-8"))
    comps = data if isinstance(data, list) else data.get("components", [])
    plan = layout(comps, bed_x, bed_y)
    (out_dir / "plates.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    bad = [p for p in plan if p.get("error")]
    for p in plan:
        if p.get("error"):
            print(f"  PLATE ERROR: {p['error']}")
        else:
            pct = 100 * p["used_mm2"] / (bed_x * bed_y)
            print(f"  plate {p['plate']:>2}  {p['designs'][0]:<18} "
                  f"{p['pieces']:>2} pcs  {pct:4.1f}% bed")
    print(f"plates: {len([p for p in plan if not p.get('error')])} "
          f"for {sum(c['qty'] for c in comps)} pieces, {len(bad)} unplaceable")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
