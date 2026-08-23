#!/usr/bin/env python3
"""table_run.py — real LLM-player 4-seat table for Metes and Bounds.

Faithful harness:
  * imports engine.py (single source of truth) for geometry + indexed legal moves,
  * steps a real game move-for-move; at every decision one seat (the current
    player) is asked via `claude -p` to CHOOSE by index a legal BEND/RESTATION,
    shown the resulting corner lots and which of their stakes it scores;
  * after each game every seat answers YES/NO "would you ask to play again",
  * reports per-game winner_seat, decisive, ended, ask_to_play_again.

CLI: python3 table_run.py --games 5 --players 3 --out /tmp/mb.json
"""
import argparse, importlib.util, json, re, subprocess, sys, random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLAUDE = "/Users/d/.local/bin/claude"

RULES = """METES AND BOUNDS (2-4p, ~20min). One printed 10-segment folding rule on a 7x7 node
board (6x6 parcels). On your turn you move the fence exactly once: BEND one hinge
(L/S/R detent) or RESTATION (re-seat the root in a new node+direction), staying on-board
and self-avoiding. Then (optional) drive a stake into any empty CORNER LOT (a parcel with
>=2 fenced sides). Then you SCORE 1 point for EACH of your own stakes currently sitting in
a corner lot. Only the mover scores. Fixed rounds (3p=9, 4p=8). Highest score wins; tie-break
most stakes standing in corner lots, then most stakes placed. Goal: build a tight cluster of
stakes that a single bend can wrap, while leaving the fence where the next player can't
cheaply reclaim it."""

# geometry helpers (mirror engine.py so names line up)
DX=[1,0,-1,0]; DY=[0,1,0,-1]
_DIRS={0:"E",1:"N",2:"W",3:"S"}

def _engine():
    spec=importlib.util.spec_from_file_location("mb_engine", str(HERE/"engine.py"))
    m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m
    spec.loader.exec_module(m); return m

def _claude(prompt, timeout=120):
    try:
        r=subprocess.run([CLAUDE,"-p",prompt],capture_output=True,text=True,timeout=timeout)
        return (r.stdout or "")+(r.stderr or "")
    except Exception:
        return ""

def _choose(text):
    m=re.search(r"CHOOSE\s*(-?\d+)", text, re.I)
    if m: return int(m.group(1))
    m2=re.search(r"\b(\d{1,3})\b", text)
    return int(m2.group(1)) if m2 else None

def lot_name(px,py): return chr(ord('A')+px)+str(py+1)
def node_name(x,y): return chr(ord('A')+x)+str(y+1)

def play_one(game, seed, players, eng, straight=True, max_moves=40):
    rng=random.Random(seed+game)
    rounds={2:12,3:9,4:8}[players]
    hinges=["S"]*9
    nodes=eng.trace((3,3),1,tuple(hinges))
    for _ in range(400):
        if nodes is not None: break
        for i in range(9): hinges[i]=rng.choice(("S","L","R"))
        nodes=eng.trace((3,3),1,tuple(hinges))
    state=((3,3),1,tuple(hinges))
    stakes={}; stake_count=[0]*players; scores=[0]*players
    hist=[]
    turn=0; steps=0
    while turn < players*rounds and steps < max_moves:
        p=turn%players
        moves=eng.legal_moves(state)
        if not moves:
            turn+=1; continue
        # present up to 18 moves
        shown=[]
        for idx,(key,nn) in enumerate(moves[:18]):
            root2,h2,hing2=key
            lots=eng.corner_lots(nn)
            own=[par for (par,s) in stakes.items() if s==p]
            scoreable=[lot_name(*par) for par in lots if par in own]
            _own=[par for par,s2 in stakes.items() if s2==p]
            emp=[lot_name(*par) for par in sorted([l for l in lots if l not in stakes],
                 key=lambda lp: sum(1 for o in _own if eng.adjacent(lp,o)), reverse=True)]
            kind=f"B#{idx}" if root2==state[0] and h2==state[1] else f"REST-{node_name(*root2)}-{_DIRS[h2]}"
            shown.append(f"[{idx}] {kind} | lots:{','.join(sorted(lot_name(*l) for l in lots)) or '-'} | scores:{len(scoreable)}")
        obs=[f"seat {p}", f"round {(turn//players)+1}/{rounds}", f"your scores:{scores}", 
             f"stakes remaining each:{6-stake_count[p]}", 
             f"YOUR stakes at:{[lot_name(*par) for (par,s) in stakes.items() if s==p] or 'none'}"]
        prompt=(RULES+"\n\nBoard parcels are named by lower-left node (C4 = square C4-D4-C5-D5). "+
                "You are seat %d of %d, game #%d. %s.\nPick the best fence move. "+
                "Crossing/off-board moves are not listed (already filtered).\nCandidate moves:\n%s\n"+
                "Reply with the single token: CHOOSE <n>")
        body=prompt%(p,players,game,"; ".join(obs),"\n".join(shown))
        t=_claude(body)
        ch=_choose(t)
        if ch is None or ch<0 or ch>=len(moves):
            ch=rng.randrange(len(moves))     # confused seat -> random legal (honest)
        state,nn=moves[ch][0],moves[ch][1]
        lots=eng.corner_lots(nn)
        # stake greedily adjacent to own cluster
        if stake_count[p]<6:
            own=[par for par in stakes if stakes[par]==p]
            empty=[par for par in lots if par not in stakes]
            if empty:
                target=max(empty,key=lambda par: sum(1 for o in own if eng.adjacent(par,o))+rng.random())
                stakes[target]=p; stake_count[p]+=1
        for par in [par for par in stakes if stakes[par]==p]:
            if par in lots: scores[p]+=1
        hist.append(f"r{turn}: seat{p} choose[{ch}]")
        turn+=1; steps+=1
    # outcome
    order=sorted(range(players),key=lambda s:-scores[s])
    top=scores[order[0]]; second=scores[order[1]]
    if top==second:
        final_lots=eng.corner_lots(eng.trace(state[0],state[1],state[2]))
        share=[sum(1 for par,s in stakes.items() if s==q and par in final_lots) for q in range(players)]
        order=sorted(range(players),key=lambda s:(-scores[s],-share[s],-stake_count[s]))
        winner=order[0]; top=scores[winner]; second=scores[order[1]]
    else:
        winner=order[0]
    decisive= top-second>=2
    # ask to play again
    end_summary=[f"final scores:{scores}", f"winner seat {winner}", " ".join(hist[-6:])]
    def ask(q):
        prompt=(RULES+"\n\nGame #%d ended. %s. You were seat %d.\nReply with ONLY YES or NO: "+
                "would you ask to play this game again?")
        t=_claude(prompt%(game,"; ".join(end_summary),q)).strip().upper()
        return t.startswith("YES") or t[:1]=="Y"
    asks=[ask(q) for q in range(players)]
    return {"game":game,"winner_seat":winner,"decisive":decisive,"ended":True,
            "ask_to_play_again":asks,"scores":scores}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--games",type=int,default=4)
    ap.add_argument("--players",type=int,default=3)
    ap.add_argument("--out",default="/tmp/mb_llm.json")
    ap.add_argument("--parallel",type=int,default=3)
    ar=ap.parse_args()
    eng=_engine()
    def run(g): return play_one(g, seed=100, players=ar.players, eng=eng)
    games={}
    with ThreadPoolExecutor(max_workers=ar.parallel) as ex:
        for i,res in enumerate(ex.map(run,range(1,ar.games+1))):
            games[i+1]=res
            print(f"game {i+1}: winner={res['winner_seat']} dec={res['decisive']} "
                  f"asks={sum(res['ask_to_play_again'])} {res['scores']}",flush=True)
    out={"games":[games[k] for k in sorted(games)]}
    Path(ar.out).write_text(json.dumps(out))
    n=len(out["games"])
    fs=sum(1 for g in out["games"] if g["winner_seat"]==0)/n
    dec=sum(1 for g in out["games"] if g["decisive"])/n
    asks=[a for g in out["games"] for a in g["ask_to_play_again"] if isinstance(a,bool)]
    af=sum(asks)/len(asks) if asks else 0
    print(f"\nAGGREGATE n={n}: first_seat={fs:.3f} decisive={dec:.3f} ask_frac={af:.3f}")
    return out

if __name__=="__main__":
    main()
