#!/usr/bin/env python3
"""Independent replay and fixed public-information oracle checks."""
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
spec=importlib.util.spec_from_file_location("game", Path(__file__).with_name("crosscurrent_sim.py"))
game=importlib.util.module_from_spec(spec);spec.loader.exec_module(game)


def reference(before, orders):
    """Apply each vote one step to every token on its frozen ring.

    Deliberately does not call production outcome/step or use its total formula.
    """
    after=json.loads(json.dumps(before))
    voters=[before["positions"][p][b][0] for p,(b,d) in enumerate(orders)]
    for voter_ring,(b,d) in zip(voters,orders):
        for pair in after["positions"]:
            for token in pair:
                if token[0] == voter_ring:
                    for _ in range(abs(d)):
                        token[1] += (1 if d > 0 else -1)
                        if token[1]==6: token[1]=0
                        if token[1]==-1: token[1]=5
    locations=[after["positions"][p][b][1] for p,(b,d) in enumerate(orders)]
    for p,(b,d) in enumerate(orders):
        h=locations[p]
        peers=sum(other==h for other in locations)
        after["scores"][p] += (2,4,3,2,4,3)[h]//peers
        after["positions"][p][b]=[1-voters[p], 0 if h==5 else h+1]
        after["remaining"][p].remove(d)
    if before["round"] in (3,6,9):
        after["remaining"]=[[-1,0,1] for _ in orders]
    after["round"]+=1
    return after


def main():
    transitions=0;records=[];digests={}
    filenames=["traces.ndjson","adversarial-traces.ndjson"]
    if (ROOT/"informed-response-traces.ndjson").exists():
        filenames.append("informed-response-traces.ndjson")
    for filename in filenames:
        path=ROOT/filename
        digests[filename]=hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open() as f:
            for line in f:
                g=json.loads(line);prev=game.initial(len(g["scores"]))
                for t in g["trace"]:
                    assert t["before"]==prev
                    assert reference(t["before"],t["orders"])==t["after"]
                    for p,o in enumerate(t["orders"]):
                        assert tuple(o) in game.legal(t["before"],p)
                    prev=t["after"];transitions+=1
                assert len(g["trace"])==12 and g["scores"]==prev["scores"]
                if filename=="adversarial-traces.ndjson": records.append(g)
    trials=[]
    # Exact expectation oracle versus UNIFORM legal opponent orders, not actual
    # opponent current choices. Sample 120 reproducible 2–4 player states.
    for index in range(120):
        n=2+index%3
        sample=game.play(900000+index,["exploratory"]*n)
        s=sample["trace"][index%12]["before"];p=index%n
        chosen=game.choose(s,p,"optimizing",random.Random(880000+index),samples=32)
        actions=game.legal(s,p);values={}
        others=[q for q in range(n) if q!=p]
        for a in actions:
            total=count=0
            for joint in itertools.product(*(game.legal(s,q) for q in others)):
                orders=[None]*n;orders[p]=a
                for q,o in zip(others,joint):orders[q]=o
                total+=game.outcome(s,orders)[2][p];count+=1
            values[a]=total/count
        trials.append({"seed":900000+index,"round":s["round"],"player":p,"chosen":chosen,
                       "chosen_expected":values[chosen],"random_expected":sum(values.values())/len(values),
                       "oracle_expected":max(values.values()),"actions":[{"order":a,"expected":v} for a,v in values.items()]})
    breakdown={}
    for opponent in ("exploratory","greedy","always_a","alternate","fixed_arrow","collision"):
        breakdown[opponent]={}
        for n in range(2,6):
            subset=[g for g in records if g["experiment"]["opponent"]==opponent and len(g["scores"])==n]
            own=other=wins=0
            for g in subset:
                p=g["experiment"]["optimizing_seat"];scores=g["scores"]
                own+=scores[p];other+=sum(scores)-scores[p]
                if scores[p]==max(scores):wins+=1/scores.count(max(scores))
            breakdown[opponent][str(n)]={"games":len(subset),"optimizing_mean_score":own/len(subset),"opponent_mean_score":other/(len(subset)*(n-1)),"optimizing_fractional_win_rate":wins/len(subset),"equal_strength_reference":1/n}
    report={"kind":"crosscurrent.independent-replay-audit","transitions_replayed":transitions,
            "trace_sha256":digests,"independent_reference_agrees":True,"oracle_trials":trials,
            "oracle_summary":{key:sum(t[key] for t in trials)/len(trials) for key in ("chosen_expected","random_expected","oracle_expected")},
            "controlled_by_player_count":breakdown,"failures":[],
            "limitations":["Independent reference authored by same specialist agent; separate formulation catches implementation errors but is not independent human review.","Oracle is exact only for one-step scoring against uniform legal opponents, not globally optimal play.","Twenty validation games per opponent/player-count cell are exploratory and not proof of strategy dominance."]}
    (ROOT/"audit.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k in ("transitions_replayed","oracle_summary","controlled_by_player_count")},indent=2))


if __name__=="__main__":main()
