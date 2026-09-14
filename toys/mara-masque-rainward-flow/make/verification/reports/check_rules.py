"""Independent rule/state checks for Rainward Sun; invokes no shape constructor.

Run with the CAD project's Python environment. Importing rainward_lib makes
piece_poses available, but sun/drop/cup/die/assembly are never called.
This checks the documented trace and pose conservation, not physical play.
"""
from collections import Counter
from copy import deepcopy
from itertools import product
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainward_lib import piece_poses


def checked(condition, message):
    if not condition:
        raise AssertionError(message)


def conserved(state):
    for side in ('single', 'fork'):
        checked(sum(state[side].values()) == 15, f'{side} inventory changed')
        checked(all(0 <= p <= 24 and n >= 0 for p, n in state[side].items()), 'invalid state')
    checked(not any(state['single'].get(p, 0) and state['fork'].get(p, 0)
                    for p in range(1, 25)), 'opponents share point')


def submove(state, side, origin, die):
    """Only entry, ordinary travel and hits; this trace never bears off.

    Zero denotes the common bar. Separate side counters retain ownership.
    All legality checks happen before the input state is copied or changed.
    """
    checked(1 <= die <= 6, 'die outside 1..6')
    own = state[side]
    other = 'fork' if side == 'single' else 'single'
    checked(own.get(origin, 0) > 0, 'no moving drop')
    checked(not own.get(0, 0) or origin == 0, 'bar must enter first')
    if origin == 0:
        destination = 25 - die if side == 'single' else die
    else:
        destination = origin - die if side == 'single' else origin + die
    checked(1 <= destination <= 24, 'bearing off outside this trace checker')
    checked(state[other].get(destination, 0) < 2, 'opposing point blocked')
    out = deepcopy(state)
    out[side][origin] -= 1
    if out[side][origin] == 0:
        del out[side][origin]
    if out[other].get(destination, 0) == 1:
        del out[other][destination]
        out[other][0] = out[other].get(0, 0) + 1
    out[side][destination] = out[side].get(destination, 0) + 1
    conserved(out)
    return out


def pose_counts(poses):
    out = {'single': Counter(), 'fork': Counter()}
    checked(len(poses) == 30, 'expected 30 pose occurrences')
    for name, (kind, point, position, angle) in poses.items():
        checked(kind in out and name.startswith(kind + '_'), 'ownership/name mismatch')
        checked(len(position) == 3 and all(math.isfinite(x) for x in position), 'invalid pose')
        checked(math.isfinite(angle), 'invalid angle')
        out[kind][point] += 1
    conserved(out)
    return out


def main():
    # Independent standard setup, expressed in each player's own coordinates.
    own_setup = {24: 2, 13: 5, 8: 3, 6: 5}
    expected_setup = {'single': dict(own_setup),
                      'fork': {25 - point: count for point, count in own_setup.items()}}
    conserved(expected_setup)
    checked(pose_counts(piece_poses('setup')) == expected_setup, 'CAD setup differs from ordinary setup')

    # Exact two-turn provenance for the signature BEFORE state.
    state = submove(expected_setup, 'single', 13, 6)
    state = submove(state, 'single', 8, 1)
    state = submove(state, 'fork', 12, 6)  # B own 13 -> 7.
    state = submove(state, 'fork', 1, 1)   # B own 24 -> 23.
    before = piece_poses('before')
    checked(pose_counts(before) == state, 'before state does not follow documented legal rolls')

    expected_after = submove(state, 'single', 7, 6)
    after = piece_poses('after')
    checked(pose_counts(after) == expected_after, 'after state differs from legal hit')
    checked(set(before) == set(after), 'signature changed occurrence identities')
    changed = [key for key in before if before[key] != after[key]]
    checked(len(changed) == 2, 'exactly attacker and victim must move')
    attacker = next(key for key in changed if before[key][0] == 'single')
    victim = next(key for key in changed if before[key][0] == 'fork')
    checked(before[attacker][1] == 7 and after[attacker][1] == 1, 'attacker not six points away')
    checked(before[victim][1] == 1 and after[victim][1] == 0, 'victim did not move to bar')
    checked(after[attacker][2:] == before[victim][2:], 'attacker did not replace victim pose exactly')
    displacement = math.dist(before[victim][2], after[victim][2])
    checked(math.isclose(displacement, 80.0, abs_tol=1e-9), 'victim displacement not 80 mm')
    checked(after[victim][2][2] > before[victim][2][2], 'bar is not raised')
    unchanged = sum(before[key] == after[key] for key in before)
    checked(unchanged == 28, 'other drops must keep exact poses')

    # The pictured submove leaves a genuinely usable second die in the 6,2 roll.
    completed_throw = submove(expected_after, 'single', 8, 2)
    checked(completed_throw['single'][6] == 6, 'remaining die 2 was not playable')

    # A barred player may not move another drop, and pairs actually block.
    for invalid_state, side, origin, die, label in [
        (expected_after, 'fork', 2, 1, 'bar-first'),
        (expected_setup, 'single', 24, 5, 'pair-block'),
    ]:
        try:
            submove(invalid_state, side, origin, die)
        except AssertionError:
            pass
        else:
            raise AssertionError(label + ' violation accepted')
    # Hit drop can re-enter via die2 at global2, occupied only by its own side.
    entered = submove(expected_after, 'fork', 0, 2)
    checked(entered['fork'].get(0, 0) == 0 and entered['fork'][2] == 2, 'bar re-entry wrong')

    ordered_rolls = list(product(range(1, 7), repeat=2))
    checked(len(ordered_rolls) == 36 and len(set(ordered_rolls)) == 36, 'ideal dice outcome count')
    report = {
        'kind': 'rainward-sun.rules-and-state-check',
        'status': 'pass',
        'scope': 'Digital standard setup, documented legal hit trace, bar-first and pair-block constraints, exact pose conservation; no physical play or full-game simulation.',
        'standard_setup': 'pass',
        'signature_trace': ['A 6,1: 13->7; 8->7', 'B 6,1: own13->7; own24->23', 'A 6,2: 7->1 hit; die2 remains'],
        'all_states_drop_count': 30,
        'each_side_count': 15,
        'signature_changed_occurrences': changed,
        'signature_unchanged_occurrences': unchanged,
        'victim_displacement_mm': displacement,
        'remaining_die_2_is_playable': True,
        'bar_first_rejection': True,
        'opposing_pair_rejection': True,
        'bar_reentry': True,
        'ideal_ordered_dice_outcomes': 36,
        'printed_dice_fairness': 'not physically tested',
    }
    destination = Path(__file__).with_name('rules-check.json')
    destination.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
