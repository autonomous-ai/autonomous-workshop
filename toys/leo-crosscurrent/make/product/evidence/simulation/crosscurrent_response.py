#!/usr/bin/env python3
"""Bounded informed counter-policy check for fixed-boat stress findings."""
import collections
import hashlib
import importlib.util
import itertools
import json
import random
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if not (ROOT/"report.json").exists():
    ROOT=Path("artifacts/make/r0001/product/evidence/simulation")
spec=importlib.util.spec_from_file_location("game",Path(__file__).with_name("crosscurrent_sim.py"))
game=importlib.util.module_from_spec(spec);spec.loader.exec_module(game)


def informed(s,p,kind,rng):
    others=[q for q in range(len(s["scores"])) if q!=p]
    distributions=[]
    for q in others:
        b=0 if kind=="always_a" else s["round"]%2
        distributions.append([a for a in game.legal(s,q) if a[0]==b])
    joint_orders=list(itertools.product(*distributions))
    values=[]
    for a in game.legal(s,p):
        total=0
        for joint in joint_orders:
            orders=[None]*len(s["scores"]);orders[p]=a
            for q,o in zip(others,joint):orders[q]=o
            gains=game.outcome(s,orders)[2]
            # Relative immediate score reflects win-oriented optimization.
            total+=gains[p]-sum(gains[q] for q in others)/len(others)
        values.append((total/len(joint_orders),a))
    best=max(v for v,a in values)
    return rng.choice([a for v,a in values if abs(v-best)<1e-12])


def main():
    results=collections.defaultdict(list)
    with (ROOT/"informed-response-traces.ndjson").open("w") as f:
        for k,kind in enumerate(("always_a","alternate")):
            for n in (4,5):
                for trial in range(40):
                    seed=300000+k*10000+n*100+trial;rng=random.Random(seed)
                    p=trial%n;s=game.initial(n);trace=[]
                    for r in range(12):
                        # Choice computed before actual opponent random orders.
                        mine=informed(s,p,kind,rng)
                        orders=[game.choose(s,q,kind,rng) if q!=p else mine for q in range(n)]
                        after,detail=game.step(s,orders)
                        trace.append({"before":s,"orders":orders,"resolution":detail,"after":after});s=after
                    g={"seed":seed,"opponent":kind,"responding_seat":p,"scores":s["scores"],"trace":trace}
                    f.write(json.dumps(g,separators=(",",":"))+"\n")
                    scores=s["scores"];wins=(1/scores.count(max(scores)) if scores[p]==max(scores) else 0)
                    results[f"{kind}-{n}p"].append((scores[p],(sum(scores)-scores[p])/(n-1),wins))
    report={"kind":"crosscurrent.informed-policy-response","games":160,"rules_changed":False,
            "policy_information":"Exact expectation over opponent fixed boat pattern and uniformly random remaining arrows. Pattern is declared to responder; actual current orders remain hidden. Maximizes own immediate score minus average opponent immediate score.",
            "results":{key:{"games":len(rows),"responding_mean_score":sum(r[0] for r in rows)/len(rows),"opponent_mean_score":sum(r[1] for r in rows)/len(rows),"responding_fractional_win_rate":sum(r[2] for r in rows)/len(rows)} for key,rows in results.items()},
            "limitations":["Known-policy stress response tests exploitability; not a claim that children will infer this policy or that it is globally optimal.","No physical or human playtesting."]}
    (ROOT/"informed-response.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":main()
