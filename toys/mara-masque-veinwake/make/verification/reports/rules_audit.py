"""Exhaustive digital rule equivalence; no physical or human playtest claim."""
import json
from pathlib import Path

LINES = ((0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6))
MASKS = tuple(sum(1 << i for i in line) for line in LINES)

def traditional(board):
    for player in ('X', 'O'):
        if any(all(board[i] == player for i in line) for line in LINES):
            return player, ()
    empty = tuple(i for i, cell in enumerate(board) if cell == '.')
    return ('draw' if not empty else None), empty

def mineral(teeth, bubbles):
    for bits, name in ((teeth, 'tooth'), (bubbles, 'bubble')):
        if any(bits & line == line for line in MASKS):
            return name, ()
    occupied = teeth | bubbles
    return ('draw' if occupied == 511 else None), tuple(i for i in range(9) if not occupied & (1 << i))

def run():
    visited = set()
    terminal_traces = {'X': 0, 'O': 0, 'draw': 0}
    edges = 0
    def visit(board, teeth, bubbles, player):
        nonlocal edges
        result, choices = traditional(board)
        mineral_result, mineral_choices = mineral(teeth, bubbles)
        assert {'tooth':'X', 'bubble':'O', 'draw':'draw', None:None}[mineral_result] == result
        assert choices == mineral_choices
        assert teeth.bit_count() <= 5 and bubbles.bit_count() <= 4
        visited.add(board)
        if result:
            terminal_traces[result] += 1
            return
        for cell in choices:
            edges += 1
            child = board[:cell] + player + board[cell+1:]
            visit(child, teeth | (1<<cell) if player == 'X' else teeth,
                  bubbles | (1<<cell) if player == 'O' else bubbles,
                  'O' if player == 'X' else 'X')
    visit('.'*9, 0, 0, 'X')
    before = 'XX.OO....'
    after = 'XXXOO....'
    assert traditional(before) == (None, (2,5,6,7,8))
    assert traditional(after) == ('X', ())
    assert traditional('XOXXOOOXX') == ('draw', ())
    result = {'status':'pass', 'scope':'Exhaustive digital rules audit only; no human or physical playtest.',
              'distinct_reachable_states':len(visited), 'legal_trace_edges':edges,
              'terminal_traces':terminal_traces, 'differences':0,
              'signature_trace':[0,3,1,4,2], 'before':before, 'after':after,
              'full_inventory_draw':'XOXXOOOXX'}
    Path(__file__).with_name('rules-audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))

if __name__ == '__main__':
    run()
