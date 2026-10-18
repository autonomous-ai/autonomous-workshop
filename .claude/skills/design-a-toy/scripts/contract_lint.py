#!/usr/bin/env python3
"""Contract lint for design-a-toy Stage 3e: one fact, one value, everywhere.

    python3 contract_lint.py CONTRACT.md FACTS.json [--claims CLAIMS.json] [--json]

A Design Contract states most facts more than once: in the prose, in the
`design-contract` block (`envelope_mm`, `extents_mm`, `wall_min_mm`,
Interface poses) and in the requirement rows. The toy's Stage 3d model
script is the one place those numbers are computed. This tool compares them
and never judges design: it reports where two statements of one fact
disagree, so an amendment that changed one of them cannot leave the others
behind.

FACTS.json is written by the toy's model script (millimetres, assembly frame,
Display Pose):

    {
      "envelope": {"x": [lo, hi], "y": [lo, hi], "z": [lo, hi]},
      "components": {
        "shin#1": {"geometry": "shin", "bbox": {"x": [..], "y": [..], "z": [..]},
                   "profile": [[z, x_lo, x_hi], ...]},   # X span at each 1 mm of Z
        ...
      },
      "extents": {"wing": [39.25, 43, 12]},      # optional: a geometry measured in its own frame
      "moves": {"wing#1": [{"rotation_deg": 60}], "shin#1": [{"translation": [0, 0, 19.25]}]}
    }

CLAIMS.json is the Stage 3e extraction: every number the prose and the rows
state about a Component, transcribed by a fresh reader, never computed:

    [{"kind": "move", "component": "wing", "deg": 90, "joint": "wing-hinge", "quote": "..."},
     {"kind": "range", "component": "shin", "axis": "x", "from": 7.5, "to": 29.5, "quote": "..."},
     {"kind": "size", "component": "forearm", "feature": "thumb", "value": 2.8, "quote": "..."},
     {"kind": "envelope", "axis": "y", "value": 83.25, "quote": "..."}]

`component` is a geometry id, an instance (`shin#1`) or `assembly`. A move's
`joint` names the Interface it turns about (`wing-hinge` matches `wing-hinge-1`
and `-2`); without one, any move the model makes of that Component matches.
A range is checked only against the Component's whole box, so it catches a
position outside the part, not one shifted inside it. A size
claim may carry `"exception": true` when the contract names it as an
exception to the floor.

Checks, each an error unless marked warn:
  envelope     block envelope_mm against the model's Display Pose box
  extents      block extents_mm (sorted) against the model (sorted)
  moves        every Interface pose against the model's moves for that mover
  claims       moves, ranges and envelope sizes in the text against the model;
               sizes against the geometry's wall_min_mm
  alignment    (warn) going up a Component, or from a Component onto one an
               Interface joins it to, one X edge stays (0.5) while the other
               steps by more than 2 mm: the part leans to one side; compare
               the assembly image's edges there

Exit 1 when any error is found.
"""
import argparse, json, re, sys

TOL = 0.05


def block(path):
    text = open(path, encoding="utf-8").read()
    m = re.search(r"```design-contract\n(.*?)\n```", text, re.S)
    if not m:
        sys.exit("no design-contract block in %s" % path)
    return json.loads(m.group(1))


def size(r):
    return r[1] - r[0]


def instances(facts, comp):
    """Instance names for a geometry id, an instance name, or []."""
    cs = facts["components"]
    if comp in cs:
        return [comp]
    return sorted(n for n, c in cs.items() if c["geometry"] == comp)


def lint(contract, facts, claims):
    out = []

    def add(level, check, msg):
        out.append({"level": level, "check": check, "message": msg})

    env = facts["envelope"]
    got = [size(env[a]) for a in "xyz"]
    for a, want, have in zip("xyz", contract["envelope_mm"], got):
        if abs(want - have) > TOL:
            add("error", "envelope", "envelope_mm %s %g, model %g" % (a.upper(), want, round(have, 3)))

    for g in contract["geometries"]:
        names = instances(facts, g["id"])
        if g["id"] in facts.get("extents", {}):
            have = facts["extents"][g["id"]]
        elif names:
            have = [size(facts["components"][names[0]]["bbox"][a]) for a in "xyz"]
        else:
            add("error", "extents", "%s: no Component in the model" % g["id"])
            continue
        w, h = sorted(g["extents_mm"]), sorted(round(v, 3) for v in have)
        if any(abs(a - b) > TOL for a, b in zip(w, h)):
            add("error", "extents", "%s: extents_mm %s, model %s" % (g["id"], g["extents_mm"], [round(v, 3) for v in have]))

    moves = facts.get("moves", {})

    def model_moves(comp):
        return [mv for n in instances(facts, comp) for mv in moves.get(n, [])]

    def same(pose, mv):
        if "rotation" in pose and "rotation_deg" in mv:
            r = pose["rotation"]
            return abs(abs(r["end_deg"] - r["start_deg"]) - abs(mv["rotation_deg"])) <= TOL
        if "translation" in pose and "translation" in mv:
            return all(abs(abs(a) - abs(b)) <= TOL for a, b in zip(pose["translation"]["vector"], mv["translation"]))
        return False

    for itf in contract.get("interfaces", []):
        for mover in (itf.get("poses") or {}).get("movers", []):
            ms = model_moves(mover["component"])
            if not any(same(mover, mv) for mv in ms):
                add("error", "moves", "%s: %s moves %s, model %s" % (
                    itf["id"], mover["component"],
                    mover.get("rotation") or mover.get("translation"), ms or "no move"))

    wall = {g["id"]: g["wall_min_mm"] for g in contract["geometries"]}
    for c in claims:
        k, comp, q = c["kind"], c.get("component"), c.get("quote", "")[:120]
        if k == "move":
            if c.get("joint"):
                # the Interface poses for this joint (wing-hinge matches wing-hinge-1 and -2) and this mover
                geo = comp.split("#")[0]
                degs = [abs(m["rotation"]["end_deg"] - m["rotation"]["start_deg"])
                        for itf in contract.get("interfaces", []) if itf["id"] == c["joint"] or itf["id"].startswith(c["joint"] + "-")
                        for m in (itf.get("poses") or {}).get("movers", [])
                        if "rotation" in m and m["component"].split("#")[0] == geo]
                if not degs:
                    add("error", "claims", "%s turns %g about %s in the text, but no Interface %s turns it: \"%s\"" % (
                        comp, c["deg"], c["joint"], c["joint"], q))
            else:
                degs = [abs(mv["rotation_deg"]) for mv in model_moves(comp) if "rotation_deg" in mv]
            if degs and not any(abs(abs(c["deg"]) - d) <= TOL for d in degs):
                add("error", "claims", "%s turns %g in the text, %s %s: \"%s\"" % (
                    comp, c["deg"], "Interface " + c["joint"] if c.get("joint") else "model", sorted(set(degs)), q))
        elif k == "range":
            for n in instances(facts, comp)[:1]:
                lo, hi = facts["components"][n]["bbox"][c["axis"]]
                if c["from"] < lo - TOL or c["to"] > hi + TOL:
                    add("error", "claims", "%s %s %g to %g in the text, outside the model's %g to %g: \"%s\"" % (
                        n, c["axis"].upper(), c["from"], c["to"], lo, hi, q))
        elif k == "size":
            geo = comp.split("#")[0]
            if geo in wall and c["value"] < wall[geo] - 1e-9 and not c.get("exception"):
                add("error", "claims", "%s %s %g is under the geometry's wall_min_mm %g: \"%s\"" % (
                    geo, c.get("feature", "feature"), c["value"], wall[geo], q))
        elif k == "envelope":
            have = size(env[c["axis"]])
            if abs(c["value"] - have) > TOL:
                add("error", "claims", "envelope %s %g in the text, model %g: \"%s\"" % (c["axis"].upper(), c["value"], round(have, 3), q))

    cs = facts["components"]

    def one_sided(lo_row, hi_row):
        """(static edge, step) when going up from lo_row to hi_row keeps one X edge and moves the other by over 2."""
        d0, d1 = hi_row[1] - lo_row[1], hi_row[2] - lo_row[2]
        if abs(d0) <= 0.501 and abs(d1) > 2:
            return d1
        if abs(d1) <= 0.501 and abs(d0) > 2:
            return d0
        return None

    for n, c in sorted(cs.items()):
        rows = c.get("profile") or []
        steps = [(r1[0], r0, r1) for r0, r1 in zip(rows, rows[1:])
                 if r1[0] - r0[0] <= 1 and one_sided(r0, r1) is not None]
        # a step that returns within 12 mm is a local feature (a boss, a vent), not the part's outline
        local = set()
        for i, (z, r0, _) in enumerate(steps):
            for j in range(i + 1, len(steps)):
                z2, _, r3 = steps[j]
                if z2 - z <= 12 and abs(r3[1] - r0[1]) <= 0.5 and abs(r3[2] - r0[2]) <= 0.5:
                    local |= {i, j}
        for i, (z, r0, r1) in enumerate(steps):
            if i not in local:
                add("warn", "alignment", "%s steps on one side only at Z %g: X %g..%g below, %g..%g above" % (
                    n, z, r0[1], r0[2], r1[1], r1[2]))
    seen = set()
    for itf in contract.get("interfaces", []):
        names = [n for comp in itf["components"] for n in instances(facts, comp)]
        for up in names:
            for low in names:
                if up == low or (up, low) in seen:
                    continue
                seen.add((up, low))
                ur, lr = cs[up].get("profile") or [], cs[low].get("profile") or []
                if not ur or not lr:
                    continue
                zb = ur[0][0]
                below = [r for r in lr if zb - 2 <= r[0] < zb]
                if not below or lr[-1][0] >= ur[-1][0]:
                    continue
                r0, r1 = below[-1], ur[0]
                if min(r0[2], r1[2]) - max(r0[1], r1[1]) < 0.5 * min(r0[2] - r0[1], r1[2] - r1[1]):
                    continue
                if one_sided(r0, r1) is not None:
                    add("warn", "alignment", "%s sits on %s flush on one side only at Z %g: X %g..%g below, %g..%g above" % (
                        up, low, zb, r0[1], r0[2], r1[1], r1[2]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("contract")
    ap.add_argument("facts")
    ap.add_argument("--claims")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    claims = json.load(open(a.claims, encoding="utf-8")) if a.claims else []
    out = lint(block(a.contract), json.load(open(a.facts, encoding="utf-8")), claims)
    if a.json:
        print(json.dumps(out, indent=1))
    else:
        for f in out:
            print("%-5s %-9s %s" % (f["level"].upper(), f["check"], f["message"]))
        e = sum(f["level"] == "error" for f in out)
        print("%d error(s), %d warning(s)%s" % (e, len(out) - e, "" if claims else "; no claims file, text not checked"))
    sys.exit(1 if any(f["level"] == "error" for f in out) else 0)


if __name__ == "__main__":
    main()
