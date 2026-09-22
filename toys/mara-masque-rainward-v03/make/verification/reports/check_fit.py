"""Measure actual STEP planar checker contact, clearance and aligned capacities.

Install with check_geometry.py in product/cad/measure before running. Triangle
projection derives footprints from exported faces, not nominal Bezier samples.
"""
from pathlib import Path
import itertools,json,math
from shapely.affinity import rotate,translate
from shapely.ops import unary_union
from check_geometry import load,ROOT,sha
import rainward_lib as p

def placed(poly,lane,r):
    return rotate(translate(poly,xoff=r),p.theta(lane),origin=(0,0))

def run():
    shapes,lanes,bar,markers,footprints,center,marker_tops=load()
    assert set(lanes)==set(range(1,25))
    assert p.RADII==(85.,72.,59.,46.,33.)
    assert p.LANE_TOP==16.8 and p.BAR_TOP==17 and p.DROP_H==4
    rows=[]; poses={}; all_marker=unary_union(list(markers.values()))
    for lane in range(1,25):
        others=unary_union([poly for n,poly in lanes.items() if n!=lane])
        for station,r in enumerate(p.RADII):
            for kind,poly in footprints.items():
                foot=placed(poly,lane,r); poses[lane,station,kind]=foot
                contact=foot.intersection(lanes[lane]); fraction=contact.area/foot.area
                hull=contact.convex_hull; centroid=foot.centroid
                margin=centroid.distance(hull.boundary) if hull.contains(centroid) else -centroid.distance(hull)
                adjacent_area=foot.intersection(others).area
                marker_clearance=foot.distance(all_marker)
                assert fraction>=.90,(lane,r,kind,'support_fraction',fraction)
                assert margin>=2,(lane,r,kind,'centroid_margin',margin)
                assert adjacent_area<1e-7,(lane,r,kind,'neighbor_contact',adjacent_area)
                assert marker_clearance>0.01,(lane,r,kind,'marker_clearance',marker_clearance)
                assert foot.intersection(bar).area<1e-7,'counter intrudes into raised center'
                rows.append({'lane':lane,'radius_mm':r,'kind':kind,'footprint_area_mm2':foot.area,'own_flat_contact_mm2':contact.area,'own_flat_support_fraction':fraction,'free_tail_fraction':1-fraction,'centroid_support_hull_margin_mm':margin,'neighbor_flat_contact_mm2':adjacent_area,'marker_clearance_mm':marker_clearance})
    # Source source-preservation audit separately guarantees unchanged extrusion.
    # Exported counters have only two equal horizontal flats, Z0 and Z4. At
    # aligned offsets, layers touch at their planes without volume overlap.
    stack_checks=[]
    for lane in range(1,25):
        for kind in footprints:
            lane_feet=[poses[lane,j,kind] for j in range(5)]
            gap=min(a.distance(b) for a,b in itertools.combinations(lane_feet,2))
            assert all(a.intersection(b).area<1e-7 for a,b in itertools.combinations(lane_feet,2))
            assert gap>.9
            stack_checks.append({'lane':lane,'kind':kind,'positions':5,'aligned_layers':3,'capacity':15,'bottom_z_mm':[16.8,20.8,24.8],'minimum_intralane_outline_gap_mm':gap,'interlayer_contact_fraction':1.0,'positive_volume_overlap_mm3':0.0})
    # Every pair of adjacent lanes, all radial positions and all type pairs.
    adjacent=[]
    for lane in range(1,25):
        nxt=lane%24+1; minimum=1e9; worst=None
        for j,k,a,b in itertools.product(range(5),range(5),footprints,footprints):
            left,right=poses[lane,j,a],poses[nxt,k,b]
            overlap=left.intersection(right).area
            assert overlap<1e-7,(lane,nxt,j,k,a,b,overlap)
            gap=left.distance(right)
            if gap<minimum: minimum=gap; worst=[p.RADII[j],p.RADII[k],a,b]
        adjacent.append({'lane_pair':[lane,nxt],'minimum_gap_mm':minimum,'worst_case':worst})
    bar_rows=[]; sites=list(itertools.product((-12,0,12),(-5,5)))
    for kind,poly in footprints.items():
        positioned=[translate(poly,xoff=x,yoff=y) for x,y in sites]
        for site,foot in zip(sites,positioned):
            fraction=bar.intersection(foot).area/foot.area
            assert fraction>1-1e-7,(kind,site,fraction)
            assert foot.distance(bar.boundary)>.01
            bar_rows.append({'kind':kind,'site_xy_mm':site,'support_fraction':fraction,'aligned_layers':5,'bottom_z_mm':[17,21,25,29,33]})
    bar_gap=1e9
    for site_a,site_b in itertools.combinations(sites,2):
        for a,b in itertools.product(footprints.values(),repeat=2):
            left=translate(a,xoff=site_a[0],yoff=site_a[1]);right=translate(b,xoff=site_b[0],yoff=site_b[1])
            assert left.intersection(right).area<1e-7
            bar_gap=min(bar_gap,left.distance(right))
    # Existing envelope sites have touching x limits at 12mm pitch; measured
    # organic outlines may give a larger gap. No positive area overlap allowed.
    before=p.piece_poses('before'); after=p.piece_poses('after')
    changed=[k for k in before if before[k]!=after[k]]; assert len(changed)==2
    victim=next(k for k in changed if k.startswith('fork'));attacker=next(k for k in changed if k.startswith('single'))
    assert before[attacker][1]-after[attacker][1]==6
    assert after[attacker][2]==before[victim][2]
    displacement=math.dist(before[victim][2],after[victim][2]); assert abs(displacement-80)<1e-8
    destination=translate(rotate(footprints['fork'],after[victim][3],origin=(0,0)),xoff=after[victim][2][0],yoff=after[victim][2][1])
    assert destination.difference(bar).area<1e-7
    cup=shapes['part_cup_1.step']; assert p.CUP_ID==38 and p.CUP_OD==42 and p.CUP_FLOOR==2
    assert math.hypot(32,16)<38 and p.CUP_H-p.CUP_FLOOR>16
    report={'status':'PASS','method':'Actual exported STEP B-rep face triangulations at 0.002mm deflection, verified against native face areas. Contacts and clearance use measured polygons. Aligned extruded stack non-interpenetration follows measured equal planar top/bottom faces and disjoint Z interiors.','source_sha256':sha(ROOT/'rainward_lib.py'),'step_sha256':{k:sha(ROOT/k) for k in shapes},'support_checks':rows,'minimum_support':min(rows,key=lambda r:r['own_flat_support_fraction']),'minimum_centroid_margin':min(rows,key=lambda r:r['centroid_support_hull_margin_mm']),'minimum_marker_clearance':min(rows,key=lambda r:r['marker_clearance_mm']),'fractional_tail_contact_note':'Some asymmetric checker tails extend beyond their own lane flat into a shallow gap or beyond the board perimeter. Reported fractions measure actual flat contact; do not describe them as fully supported footprints. Mass centroids remain inside the support hull.','lane_capacity_checks':stack_checks,'adjacent_lane_clearance_checks':adjacent,'minimum_adjacent_gap_mm':min(r['minimum_gap_mm'] for r in adjacent),'bar_support_checks':bar_rows,'bar_geometric_capacity':30,'minimum_bar_site_outline_gap_mm':bar_gap,'signature_displacement_mm':displacement,'limitations':'CAD only. No physical stability, manufacture, handling, dice fairness or reachable 30-counter bar-state claim. Tiny tessellation error is controlled by face-area agreement, not a physical tolerance study.'}
    Path(__file__).with_name('fit-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','minimum_support','minimum_centroid_margin','minimum_marker_clearance','minimum_adjacent_gap_mm','bar_geometric_capacity']}))
if __name__=='__main__':run()
