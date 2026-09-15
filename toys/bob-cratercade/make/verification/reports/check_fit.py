"""Shared fit equations and connector ledger, alongside native geometry gates.

Run with the CAD skill scripts and this CAD project on PYTHONPATH. This audit
does not repeat printable body, bed, topology or pairwise interference checks.
"""
import hashlib,json,sys
from pathlib import Path
CAD=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(CAD))
import params as p
from assemblies.hardware import deck_fasteners
from assemblies.deck import fastener_rows
from assemblies.playfield import deck_mounts as playfield_mounts
from assemblies.return_system import deck_mounts as return_mounts

def audit():
    checks=[]
    def check(name,passed,detail):
        checks.append({'name':name,'pass':bool(passed),'detail':detail})
    check('M4 nominal shaft clearance',p.M4_BORE>=p.M4_D+0.4,
          {'bore_mm':p.M4_BORE,'nominal_shaft_mm':p.M4_D})
    check('Qualified countersunk head clearance',p.CSK_RECESS_D>p.CSK_HEAD_MAX_D,
          {'recess_mm':p.CSK_RECESS_D,'supplier_max_head_mm':p.CSK_HEAD_MAX_D})
    check('Thin-nut side clearance',p.NUT_POCKET_AF>p.NUT_AF,
          {'pocket_af_mm':p.NUT_POCKET_AF,'supplier_nut_af_mm':p.NUT_AF})
    check('Flipper sleeve sliding clearance',p.FLIPPER_ROTOR_BORE>p.FLIPPER_SLEEVE_OD,
          {'radial_mm':(p.FLIPPER_ROTOR_BORE-p.FLIPPER_SLEEVE_OD)/2})
    check('Launcher square guide clearance',p.LAUNCH_GUIDE_SIDE>p.LAUNCH_ROD_SIDE,
          {'per_side_mm':(p.LAUNCH_GUIDE_SIDE-p.LAUNCH_ROD_SIDE)/2})
    check('Axle sleeve clearance',p.FRAME_AXLE_BORE>p.AXLE_D and p.AXLE_BORE>p.AXLE_D,
          {'frame_diametral_mm':p.FRAME_AXLE_BORE-p.AXLE_D,'rocker_diametral_mm':p.AXLE_BORE-p.AXLE_D})
    check('Located deck seam allowance',p.DECK_STRAP_SOCKET_D>p.DECK_STRAP_PIN_D and
          p.DECK_STRAP_SOCKET_DEPTH>p.DECK_STRAP_PIN_H,
          {'diametral_mm':p.DECK_STRAP_SOCKET_D-p.DECK_STRAP_PIN_D,
           'depth_mm':p.DECK_STRAP_SOCKET_DEPTH-p.DECK_STRAP_PIN_H})
    check('Return minimum marble section',min(p.RETURN_INNER_W,p.RETURN_CLEAR_H,p.HOPPER_THROAT_ID)>p.MARBLE_MAX_D,
          {'width_mm':p.RETURN_INNER_W,'height_mm':p.RETURN_CLEAR_H,'marble_max_mm':p.MARBLE_MAX_D})
    check('Drain minimum marble section',min(p.CUP_DRAIN_X[1]-p.CUP_DRAIN_X[0],p.CUP_DRAIN_Y[1]-p.CUP_DRAIN_Y[0])>p.MARBLE_MAX_D,
          {'width_mm':p.CUP_DRAIN_X[1]-p.CUP_DRAIN_X[0],'length_mm':p.CUP_DRAIN_Y[1]-p.CUP_DRAIN_Y[0]})
    ledger=[]
    def connector(label,head,nut_bottom,length=16,kind='countersunk'):
        tip=head-length
        top=nut_bottom+p.NUT_T
        shaft_top=head-(p.CSK_HEAD_MAX_H if kind=='countersunk' else 0)
        engagement=max(0,min(shaft_top,top)-max(tip,nut_bottom))
        row={'label':label,'kind':kind,'head_datum_mm':head,'tip_mm':tip,
             'nut_bottom_mm':nut_bottom,'nut_top_mm':top,
             'nominal_engagement_mm':engagement,'tip_projection_mm':nut_bottom-tip}
        ledger.append(row)
        check('Nominal nut engagement: '+label,engagement>=p.NUT_T-1e-8,row)
    for name,_,_,head,kind in deck_fasteners():
        connector(name,head,-p.DECK_T-p.NUT_T,25 if kind=='socket' else 16,
                  'socket' if kind=='socket' else 'countersunk')
    for name,_,_,head,bottom in fastener_rows()+return_mounts():
        connector(name,head,bottom)
    for mission in ('A','B'):
        for i,row in enumerate(playfield_mounts(mission)):
            connector(f"mission_{mission}_{row['part']}_{i}",row['head_z'],row['nut_bottom_z'])
    return {'scope':'Shared nominal fits and deck-root connector stacks; threads, preload and physical tolerance remain untested',
            'params_sha256':hashlib.sha256((CAD/'params.py').read_bytes()).hexdigest(),
            'checks':checks,'connector_ledger':ledger,'pass':all(c['pass'] for c in checks)}

if __name__=='__main__':
    result=audit()
    Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'pass':result['pass'],'checks':len(result['checks']),
                      'failures':[c for c in result['checks'] if not c['pass']]},indent=2))
    raise SystemExit(0 if result['pass'] else 1)
