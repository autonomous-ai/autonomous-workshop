#!/usr/bin/env python3
"""Crosscurrent revision 1 deterministic rules engine and bounded verification.

This program executes a fixed game model and fixed policy experiments. It does
not judge, revise, schedule agents, select Workshop stages, or run a retry loop.
"""
import argparse
import collections
import hashlib
import itertools
import json
import math
import random
from pathlib import Path

REWARDS = (2, 4, 3, 2, 4, 3)
POLICIES = ("optimizing", "social", "exploratory", "adversarial", "greedy")


def initial(n):
    assert 2 <= n <= 5
    return {"round": 1, "positions": [[[0, (6*p)//n], [1, ((6*p)//n+3)%6]] for p in range(n)],
            "remaining": [[-1, 0, 1] for _ in range(n)], "scores": [0]*n}


def legal(s, p):
    return [(b, d) for b in (0, 1) for d in s["remaining"][p]]


def outcome(s, orders):
    """Pure score snapshot; all memberships come from the pre-reveal state."""
    totals = [0, 0]
    for p, (b, d) in enumerate(orders):
        totals[s["positions"][p][b][0]] += d
    harbors = [(s["positions"][p][b][1] + totals[s["positions"][p][b][0]]) % 6
               for p, (b, _) in enumerate(orders)]
    crowd = collections.Counter(harbors)
    gains = [REWARDS[h]//crowd[h] for h in harbors]
    return totals, harbors, gains


def step(s, orders):
    if s["round"] > 12:
        raise ValueError("Game already ended")
    if len(orders) != len(s["scores"]):
        raise ValueError("One order per player required")
    for p, order in enumerate(orders):
        if tuple(order) not in legal(s, p):
            raise ValueError("Illegal boat or unavailable direction")
    totals, harbors, gains = outcome(s, orders)
    pos = [[[r, (h+totals[r]) % 6] for r, h in pair] for pair in s["positions"]]
    remaining = [list(x) for x in s["remaining"]]
    for p, (b, d) in enumerate(orders):
        old_ring = s["positions"][p][b][0]
        pos[p][b] = [1-old_ring, (harbors[p]+1) % 6]
        remaining[p].remove(d)
    if s["round"] in (3, 6, 9):
        remaining = [[-1, 0, 1] for _ in orders]
    new = {"round": s["round"]+1, "positions": pos, "remaining": remaining,
           "scores": [x+y for x, y in zip(s["scores"], gains)]}
    detail = {"totals": totals, "scored_harbors_zero_based": harbors, "gains": gains,
              "crowd": dict(collections.Counter(harbors))}
    return new, detail


def choose(s, p, policy, rng, samples=16):
    actions = legal(s, p)
    if policy == "exploratory":
        return rng.choice(actions)
    if policy == "always_a":
        return rng.choice([a for a in actions if a[0] == 0])
    if policy == "alternate":
        return rng.choice([a for a in actions if a[0] == (s["round"] % 2)])
    if policy == "fixed_arrow":
        d = min(s["remaining"][p])
        return rng.choice([a for a in actions if a[1] == d])
    if policy == "greedy":
        return max(actions, key=lambda a: (REWARDS[(s["positions"][p][a[0]][1]+a[1])%6], rng.random()))
    # Common random opponent samples make own candidate comparisons meaningful.
    # Opponent CURRENT orders are never passed into this function.
    joints = [[rng.choice(legal(s, q)) for q in range(len(s["scores"]))] for _ in range(samples)]
    leader = max((q for q in range(len(s["scores"])) if q != p), key=lambda q: s["scores"][q])
    values = []
    for a in actions:
        total = 0.0
        for joint in joints:
            orders = list(joint)
            orders[p] = a
            turns, hs, gains = outcome(s, orders)
            val = float(gains[p])
            if policy == "social":
                val += 0.22 * sum(gains[q] for q in range(len(gains)) if q != p)
            elif policy == "adversarial":
                val -= 0.65*gains[leader]
            elif policy == "collision":
                val = -gains[leader] + 0.15*gains[p]
            elif policy == "optimizing":
                # Bounded one-step positional option value, not a future oracle.
                b, d = a
                other = 1-b
                r, h = s["positions"][p][other]
                future_hs = [(hs[p]+1)%6, (h+turns[r])%6]
                available = [v for v in s["remaining"][p] if v != d] or [-1,0,1]
                if s["round"] < 12:
                    val += 0.12 * max(REWARDS[(h2+d2)%6] for h2 in future_hs for d2 in available)
            total += val
        values.append(total/len(joints))
    best = max(values)
    return rng.choice([a for a,v in zip(actions, values) if abs(v-best)<1e-12])


def play(seed, policies, samples=16):
    rng = random.Random(seed)
    s = initial(len(policies))
    trace = []
    for _ in range(12):
        orders = [choose(s, p, pol, rng, samples) for p, pol in enumerate(policies)]
        new, details = step(s, orders)
        trace.append({"before": s, "orders": orders, "resolution": details, "after": new})
        s = new
    assert s["round"] == 13
    assert all(not rem for rem in s["remaining"])
    for p in range(len(policies)):
        assert collections.Counter(t["orders"][p][1] for t in trace) == {-1:4, 0:4, 1:4}
    return {"seed": seed, "policies": policies, "scores": s["scores"], "trace": trace}


def edge_tests():
    passed = []
    def check(name, condition):
        assert condition, name
        passed.append(name)
    s = initial(5)
    s["positions"] = [[[p%2, 1], [1-p%2, 1]] for p in range(5)]
    n,d = step(s, [(0,0)]*5)
    check("five-way reward-four crowd is zero", d["gains"] == [0]*5)
    check("crowd combines both rings", d["crowd"] == {1:5})
    check("all selected boats cross and drift from snapshot", all(n["positions"][p][0] == [1-p%2, 2] for p in range(5)))
    check("unselected boats remain and do not harvest", all(n["positions"][p][1] == s["positions"][p][1] for p in range(5)))
    s = initial(2)
    s["positions"] = [[[0,0],[1,1]], [[0,2],[1,1]]]
    n,d=step(s,[(0,1),(0,-1)])
    check("opposing same-ring arrows cancel",d["totals"]==[0,0])
    check("worked mixed-ring reward snapshot", d["gains"]==[2,3])
    s=initial(3)
    s["positions"]=[[[0,0],[1,0]],[[0,2],[1,2]],[[1,3],[0,3]]]
    n,d=step(s,[(0,1),(0,-1),(0,1)])
    check("manual worked example",d["totals"]==[0,1] and d["gains"]==[2,3,4] and [p[0] for p in n["positions"]]==[[1,1],[1,3],[0,5]])
    for count in (3,4,5):
        for direction in (-1,1):
            s=initial(count)
            s["positions"]=[[[0,5],[1,5]] for _ in range(count)]
            n,d=step(s,[(0,direction)]*count)
            check(f"signed total {count*direction} modulo and occupied destination", all(p[0]==[1,(6+count*direction)%6] for p in n["positions"]))
    s=initial(2)
    n,_=step(s,[(0,1),(1,1)])
    try:
        step(n,[(0,1),(1,0)])
        raise AssertionError("accepted used arrow")
    except ValueError:
        passed.append("used arrow rejected")
    for seed in range(30):
        game=play(seed,["exploratory"]*(2+seed%4))
        for t in game["trace"]:
            s,o=t["before"],t["orders"]
            perm=list(reversed(range(len(o))))
            ps={"round":s["round"],"positions":[s["positions"][p] for p in perm],"remaining":[s["remaining"][p] for p in perm],"scores":[s["scores"][p] for p in perm]}
            pn,_=step(ps,[o[p] for p in perm])
            assert pn["scores"]==[t["after"]["scores"][p] for p in perm]
            assert pn["positions"]==[t["after"]["positions"][p] for p in perm]
            swapped={**s,"positions":[list(reversed(pair)) for pair in s["positions"]]}
            sn,_=step(swapped,[(1-b,d) for b,d in o])
            assert sn["scores"]==t["after"]["scores"]
            assert sn["positions"]==[list(reversed(pair)) for pair in t["after"]["positions"]]
    passed.extend(["360 seeded transitions permutation invariant", "360 seeded transitions A/B identity invariant", "thirty full games exact termination and card conservation"])
    try:
        step(game["trace"][-1]["after"],[(0,0)]*len(game["scores"]))
        raise AssertionError("accepted thirteenth round")
    except ValueError:
        passed.append("thirteenth round rejected")
    return passed


def summarize(games):
    by_policy=collections.defaultdict(lambda: {"games":0,"points":0,"fractional_wins":0.0})
    seats=collections.defaultdict(lambda: {"games":0,"points":0,"fractional_wins":0.0})
    zeros=selected=ties=collisions=rounds=0
    turns=collections.Counter()
    for g in games:
        top=max(g["scores"])
        winners=sum(x==top for x in g["scores"])
        ties += winners>1
        for p,(policy,score) in enumerate(zip(g["policies"],g["scores"])):
            for record in (by_policy[policy],seats[f'{len(g["scores"])}p-seat{p}']):
                record["games"]+=1;record["points"]+=score
                record["fractional_wins"] += (1/winners if score==top else 0)
        for t in g["trace"]:
            gains=t["resolution"]["gains"]
            zeros+=sum(v==0 for v in gains);selected+=len(gains);rounds+=1
            collisions+=any(v>1 for v in t["resolution"]["crowd"].values())
            turns.update(str(v%6) for v in t["resolution"]["totals"])
    def finish(records):
        return {k:{**v,"mean_score":round(v["points"]/v["games"],4),"fractional_win_rate":round(v["fractional_wins"]/v["games"],4)} for k,v in records.items()}
    return {"games":len(games),"rounds":rounds,"ties":ties,"zero_pay_harvests":zeros,"harvests":selected,"congested_rounds":collisions,"ring_turns_modulo6":dict(turns),"policy":finish(by_policy),"seat":finish(seats)}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--games",type=int,default=1000)
    parser.add_argument("--output",default="evidence/crosscurrent")
    args=parser.parse_args()
    output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
    checks=edge_tests()
    games=[]
    with (output/"traces.ndjson").open("w") as f:
        for i in range(args.games):
            n=2+i%4
            policies=list(POLICIES[:n])
            random.Random(700000+i).shuffle(policies)
            g=play(10000+i,policies)
            f.write(json.dumps(g,separators=(",",":"))+"\n")
            games.append(g)
    # Separate matched experiment: search versus uniform random and fixed rules.
    experiments=[]
    with (output/"adversarial-traces.ndjson").open("w") as f:
        for j,opponent in enumerate(("exploratory","greedy","always_a","alternate","fixed_arrow","collision")):
            for n in range(2,6):
                for repeat in range(20):
                    seat=repeat%n
                    policies=[opponent]*n;policies[seat]="optimizing"
                    g=play(100000+j*10000+n*100+repeat,policies,samples=32)
                    g["experiment"]={"opponent":opponent,"optimizing_seat":seat}
                    f.write(json.dumps(g,separators=(",",":"))+"\n")
                    experiments.append(g)
    report={"kind":"crosscurrent.make-rules-verification","revision":1,"engine_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"configuration":{"validation_seeds":[10000,9999+args.games],"samples_per_candidate":16,"adversarial_samples":32,"rounds":12,"player_counts":[2,3,4,5],"optimization":"public-state Monte Carlo immediate utility plus 0.12 next-position option value; no current secret opponent orders"},"edge_checks":checks,"failures":[],"main":summarize(games),"adversarial":{op:summarize([g for g in experiments if g["experiment"]["opponent"]==op]) for op in ("exploratory","greedy","always_a","alternate","fixed_arrow","collision")},"limitations":["AI rules execution only; no human playtesting or proof of fun, age suitability, duration or physical handling.","Finite policy comparisons do not prove absence of dominant strategies or global balance.","Policy assignments differ by player count; aggregate policy win rates are not a controlled ranking.","Geometry/fit/printability require separate evidence."]}
    (output/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"games":len(games),"adversarial_games":len(experiments),"edge_checks":len(checks),"report":str(output/"report.json"),"main_policy":report["main"]["policy"],"versus_random":report["adversarial"]["exploratory"]["policy"]},indent=2))


if __name__=="__main__":
    main()
