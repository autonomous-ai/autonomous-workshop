"""Pearl Pulse algebraic fit audit; no solid construction or motion checking.

Run directly, or through the CAD project's check_fit/verify_project runner.
A pass proves only the equations below. Generic fit/mesh/validation/interference
checks still own actual geometry. Multiple bodies in part_chain.step.py are
intentional captive PIP members, not a disconnected purported single part.
"""
from pathlib import Path
import ast
import json
import math
import sys

PROJECT = Path(__file__).resolve().parents[1]
# verify_project supplies this path; direct execution finds the materialized skill.
for parent in PROJECT.parents:
    scripts = parent / '.agents/skills/cad/scripts'
    if scripts.is_dir():
        sys.path.insert(0, str(scripts))
        break
sys.path.insert(0, str(PROJECT))
import params as p
from parts.moving import keeper_pin_datums

checks = []
def require(name, condition, detail):
    if not condition:
        raise AssertionError(f'{name}: {detail}')
    checks.append({'name': name, 'detail': detail})

def close(name, actual, expected, tolerance=1e-7):
    require(name, math.isclose(actual, expected, abs_tol=tolerance),
            {'actual': actual, 'expected': expected})

def gap(name, actual, minimum, maximum):
    require(name, minimum-1e-8 <= actual <= maximum+1e-8,
            {'clearance_mm': actual, 'allowed_mm': [minimum, maximum]})

def function_node(module, name):
    tree = ast.parse((PROJECT / 'parts' / f'{module}.py').read_text())
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)

def assignment(module, function, target):
    node = function_node(module, function)
    return next(n.value for n in ast.walk(node) if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == target for t in n.targets))

def numeric(expr):
    # Only source expressions explicitly selected below are evaluated, with no
    # builtins, imports or geometry constructors in their evaluation context.
    return eval(compile(ast.Expression(expr), '<source-algebra>', 'eval'),
                {'__builtins__': {}, 'math': math}, vars(p))

# Independently band-check actual female-minus-male results, not a tautological
# restatement of a clearance already added to its own local temporary variable.
gap('stand / guide radial', p.GUIDE_BORE/2-p.STAND_R, .25, .35)
gap('pivot / root bore radial', (p.PIVOT_BORE-p.PIVOT_D)/2, .25, .35)
gap('PIP shaft / eye radial', (p.CHAIN_BORE_D-p.CHAIN_PIN_D)/2, .35, .45)
gap('keeper shaft / pilot radial', (p.KEEPER_PILOT_D-p.KEEPER_PIN_D)/2, .25, .35)
close('keeper upper/lower bore alignment', p.KEEPER_HOLE_D, p.KEEPER_PILOT_D)
gap('fork / root tangential', (p.FORK_INNER-p.CHAIN_PIVOT_H)/2, .35, .45)
gap('square shaft / cam per side', (p.CAM_COUPLING-p.AXLE_D)/2, .15, .25)
gap('return shank / floor per side', (p.RETURN_TAB_HOLE-p.RETURN_TAB_WIDTH)/2, .15, .25)
gap('column / carrier socket per side', (p.COLUMN_SOCKET-p.COLUMN_WIDTH)/2, .08, .12)
close('carrier stop / hand stroke', p.GUIDE_BOTTOM-p.SUPPORT_STOP_Z, p.STROKE)
close('floor/horn lower clearance', p.PIVOT_Z-p.PIVOT_D/2-(p.RING_FLOOR_Z+p.RING_FLOOR_H), .3)
close('keeper/horn upper clearance', p.KEEPER_Z-(p.PIVOT_Z+p.PIVOT_D/2), .3)
gap('return cap / keeper vertical', p.KEEPER_Z-(p.RING_FLOOR_Z+p.RING_FLOOR_H+p.RETURN_TAB_TOP_H), .15, .25)
close('frame column seated in socket', p.FRAME_POST_BOTTOM, p.CARRIER_Z+p.SUPPORT_SOCKET_FLOOR)
gap('column conservative radial / ring', p.COLUMN_R-p.COLUMN_WIDTH/math.sqrt(2)-p.RING_OUTER_R, .5, 1.0)

# Finite-radius sphere tangency to the tilted cam plane at the nominal rest.
slope = p.STROKE/(2*p.CAM_TRACK_R)
cam_at_follower = p.ROTOR_TOP-p.CAM_MIN_THICKNESS-p.STROKE/2+slope*p.CAM_TRACK_R
close('sphere / cam plane normal distance',
      (cam_at_follower-p.FOLLOWER_NOSE_Z)/math.sqrt(1+slope*slope), p.FOLLOWER_NOSE_R)
close('cam / shoulder seat', p.DRIVE_SHAFT_SHOULDER_TOP, p.DRIVE_CAM_WEB_BOTTOM)
gap('shoulder / fixed stand', p.DRIVE_SHAFT_SHOULDER_BOTTOM-p.STAND_TOP, .3, .5)
close('grease nominal axial gap', p.STATOR_FACE_Z-p.CUP_BOTTOM-p.CUP_FLOOR_H, p.GREASE_GAP)
close('cup upper stop / stator roof', p.STATOR_CAVITY_TOP-(p.CUP_BOTTOM+p.CUP_FLOOR_H+p.DRIVE_CUP_OUTER_WALL_H), p.DRIVE_AXIAL_END_FLOAT)
gap('minimum bounded grease gap', p.GREASE_GAP-p.DRIVE_AXIAL_END_FLOAT, .55, .65)
close('cross-key / washer bearing datum', p.DRIVE_RETAINER_BOTTOM, p.DRIVE_THRUST_WASHER_BOTTOM+p.DRIVE_THRUST_WASHER_H)
gap('key thickness / transverse slot', (p.DRIVE_RETAINER_SLOT_WIDTH-p.DRIVE_RETAINER_WIDTH)/2, .08, .12)
gap('key top / slot top', p.DRIVE_RETAINER_SLOT_TOP-p.DRIVE_RETAINER_TOP, .15, .25)
gap('upper hook / stand bore radial', p.STAND_BORE_R-math.hypot(p.DRIVE_HOOK_OUTER_HALF_WIDTH,p.AXLE_D/2), .25, .35)

# Inline geometry literals are read from their real builder expressions.
journal_points = [numeric(arg) for arg in assignment('drive','shaft','octagon').args]
frame_cuts = assignment('support','frame','cuts')
frame_bore = numeric(frame_cuts.elts[0].args[0])
gap('upper journal / frame radial', frame_bore-max(math.hypot(*q) for q in journal_points), .15, .2)
inner_cavity = frame_cuts.elts[3]
cavity_outer, cavity_inner = (numeric(inner_cavity.args[i]) for i in (0,1))
# Check the actual appended boss-floor cutter, not only its named datum.
boss_bottom = numeric(assignment('support','frame','boss_bottom'))
boss_cut = next(n.args[0] for n in ast.walk(function_node('support','frame'))
                if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
                and isinstance(n.func.value,ast.Name) and n.func.value.id=='cuts'
                and n.func.attr=='append' and len(n.args)==1
                and isinstance(n.args[0],ast.Call)
                and isinstance(n.args[0].func,ast.Name) and n.args[0].func.id=='cylinder'
                and any(isinstance(q,ast.Name) and q.id=='boss_bottom' for q in ast.walk(n.args[0])))
boss_cut_values = [eval(compile(ast.Expression(arg),'<boss-cut>','eval'),
                        {'__builtins__':{}},dict(vars(p),boss_bottom=boss_bottom))
                   for arg in boss_cut.args]
close('boss cutter reaches central boss radius', boss_cut_values[0], cavity_inner)
close('boss cutter reaches declared lower bearing face', boss_cut_values[1]+boss_cut_values[2], boss_bottom)
close('boss / cup floor nominal axial gap', boss_bottom-(p.CUP_BOTTOM+p.CUP_FLOOR_H), .4)
gap('boss / cup floor bounded endfloat gap',
    boss_bottom-(p.CUP_BOTTOM+p.CUP_FLOOR_H+p.DRIVE_AXIAL_END_FLOAT), .15, .25)
gap('inner cup wall / central boss', p.CUP_INNER_WALL_INNER-cavity_inner, .35, .45)
gap('inner cup wall / outer cavity', cavity_outer-p.CUP_INNER_WALL_OUTER, .35, .45)
gap('outer cup wall / stator inner land', p.CUP_OUTER_WALL_INNER-p.STATOR_CAVITY_INNER, .35, .45)
gap('outer cup wall / stator rim', p.STATOR_CAVITY_OUTER-p.CUP_OUTER_R, .35, .45)
barb_points = numeric(assignment('drive','drive_retainer','barb').args[0])
barb_radius = max(math.hypot(y,p.DRIVE_RETAINER_WIDTH/2) for y,z in barb_points)
gap('positive barb / washer bore', p.DRIVE_THRUST_WASHER_INNER-barb_radius, .3, .4)

axes = keeper_pin_datums()
require('keeper staggered source axes', axes == ((21.,22.5),(21.,157.5),(21.,292.5)), axes)
head_radius = numeric(assignment('moving','keeper_pin','s').args[0])
for r,a in axes:
    gap(f'keeper head / rotor radial {a}', r-head_radius-p.ROTOR_R, .9, 1.1)
    distances = [math.sqrt(r*r+(p.PIVOT_R-p.HORN_LENGTH)**2-2*r*(p.PIVOT_R-p.HORN_LENGTH)*math.cos(math.radians(a-h))) for h in range(0,360,45)]
    gap(f'keeper boss / horn separation {a}', min(distances)-p.KEEPER_BOSS_R-p.PIVOT_D/2, 4.5, 5.0)

# Inspect the live ribbon centre expression at its seated floor interval. This
# is a few algebraic samples of its print outline, not a kinematic sweep.
ribbon_expr = assignment('moving','ribbon','x')
for depth in (0.,p.RING_FLOOR_H/2,p.RING_FLOOR_H):
    centre = eval(compile(ast.Expression(ribbon_expr), '<ribbon-neck>', 'eval'),
                  {'__builtins__': {}, 'math': math, 'max': max},
                  dict(vars(p), length=depth))
    close(f'straight ribbon neck through floor {depth}', centre, 0.)

# Manufacturing intent/connector ledger. No module builder is called here.
gap('PIP head / eye radial retention', p.CHAIN_HEAD_R-p.CHAIN_BORE_D/2, .7, .9)
gap('PIP eye / head axial separation', p.CHAIN_PIN_H-p.CHAIN_EYE_H, .35, .45)
require('eight repeatable captive joints', p.CHAIN_COUNT == 8 and len(p.CHAIN_PRINT_ANGLES)==8,
        {'per_strand_bodies':1+p.CHAIN_COUNT,'strands':8,'total_bodies':8*(1+p.CHAIN_COUNT)})
chain_entry = ast.parse((PROJECT/'part_chain.step.py').read_text())
generator = next(n for n in chain_entry.body if isinstance(n,ast.FunctionDef) and n.name=='gen_step')
require('PIP entry preserves complete manufacturing layout',
        isinstance(generator.body[0],ast.Return) and isinstance(generator.body[0].value,ast.Call)
        and isinstance(generator.body[0].value.func,ast.Name) and generator.body[0].value.func.id=='print_module',
        'part_chain.step.py returns print_module(): root + 8 beads; never split into loose printed pieces')
required_entries = ('support','anchor','carrier','frame','cam','cup','shaft','drive_retainer',
                    'drive_thrust_washer','slider','keeper','keeper_pin','pivot_pin',
                    'pivot_retainer','return_arm','ribbon','chain','bell_pearl','bell_blush','bell_mist')
require('all named physical connector entries exist',
        all((PROJECT/f'part_{role}.step.py').is_file() for role in required_entries), list(required_entries))
print(json.dumps({'ok':True,'scope':'algebraic shared datums only','checks':checks,
                  'intentional_multibody':{'part_chain.step.py':9},
                  'motion':'unverified','physical_fit':'unverified'}))
