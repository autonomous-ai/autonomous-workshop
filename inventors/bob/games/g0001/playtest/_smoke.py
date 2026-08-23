"""Throwaway smoke + benchmark for the CRANK engine. Delete after use."""
import statistics
import sys
import time

sys.path.insert(0, "/Users/d/code/inventors/bob/games/g0001/playtest")
import engine as E  # noqa


def snap(s):
    return (s.n, s.turn, s.to_move, s.last_cranker, s.idle, s.over,
            s.board[:E.B_OCC], s.board[E.B_JAM], s.dials, s.tray, s.mag,
            s.tokens, s.win, s.sc)


def playout(n, seed, cap=400, policy="random"):
    import random
    rng = random.Random(seed * 7919 + 13)
    s = E.new_game(n, seed)
    moves = 0
    branch = []
    while not E.is_over(s) and moves < cap:
        lm = E.legal_moves(s)
        if not lm:
            return {"deadlock": True, "len": moves, "branch": branch, "s": s}
        branch.append(len(lm))
        m = lm[rng.randrange(len(lm))]
        s = E.apply(s, m)
        moves += 1
    return {"deadlock": False, "len": moves, "branch": branch, "s": s,
            "over": E.is_over(s), "win": E.winners(s)}


def main():
    print("ASSUMPTIONS:", len(E.ASSUMPTIONS))
    t0 = time.time()
    lens = []
    allbranch = []
    deadlocks = 0
    unfinished = 0
    for n in (2, 3, 4):
        for seed in (0, 1):
            for g in range(50):
                r = playout(n, seed * 1000 + g)
                if r["deadlock"]:
                    deadlocks += 1
                    print("DEADLOCK", n, seed, g, r["len"])
                    continue
                if not r["over"]:
                    unfinished += 1
                    print("UNFINISHED", n, seed, g, r["len"])
                    continue
                lens.append(r["len"])
                allbranch.extend(r["branch"])
                w = r["win"]
                assert len(w) == 1, w
    dt = time.time() - t0
    print("300 random games in %.1fs" % dt)
    print("length: min %d med %d max %d" % (min(lens), statistics.median(lens),
                                            max(lens)))
    print("branching: med %.1f mean %.1f max %d  forced_frac %.3f" % (
        statistics.median(allbranch), statistics.mean(allbranch),
        max(allbranch),
        sum(1 for b in allbranch if b <= 1) / float(len(allbranch))))
    print("deadlocks", deadlocks, "unfinished", unfinished)

    # purity: apply must not mutate
    s = E.new_game(3, 7)
    for _ in range(25):
        lm = E.legal_moves(s)
        before = snap(s)
        for m in lm:
            E.apply(s, m)
        assert snap(s) == before, "apply mutated its input"
        s = E.apply(s, lm[len(lm) // 2])
        if E.is_over(s):
            break
    print("purity OK")

    # determinism: same seed -> identical transcript
    for n in (2, 3, 4):
        a = playout(n, 42)
        b = playout(n, 42)
        assert a["len"] == b["len"] and a["win"] == b["win"] and \
            a["branch"] == b["branch"], "nondeterministic at n=%d" % n
    print("determinism OK")

    # scores move during play
    s = E.new_game(3, 5)
    tr = []
    while not E.is_over(s) and len(tr) < 200:
        lm = E.legal_moves(s)
        s = E.apply(s, lm[len(lm) // 3])
        tr.append(tuple(E.scores(s)))
    changed = sum(1 for i in range(1, len(tr)) if tr[i] != tr[i - 1])
    print("scores changed on %d/%d turns" % (changed, len(tr) - 1))

    # timing
    s = E.new_game(4, 3)
    for _ in range(12):
        s = E.apply(s, E.legal_moves(s)[0])
    lm = E.legal_moves(s)
    t0 = time.time()
    for _ in range(200):
        E.legal_moves(E.apply(s, lm[0]))
    t_lm = (time.time() - t0) / 200.0
    t0 = time.time()
    for _ in range(2000):
        E.apply(s, lm[0])
    t_ap = (time.time() - t0) / 2000.0
    print("mid-game: %d legal moves, apply %.1fus, legal_moves %.0fus"
          % (len(lm), t_ap * 1e6, (t_lm - t_ap) * 1e6))

    print(E.observation(s, 0))


main()
