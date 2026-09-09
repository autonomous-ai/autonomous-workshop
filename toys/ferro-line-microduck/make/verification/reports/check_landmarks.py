"""Measure every defining visual landmark from returned BRep topology."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_spec import f,contract,near
from build123d import GeomType

def main():
    c=contract();a=f.build_assembly();parts={p.label:p for p in a.children};rows=[]
    required={'head crown and rim','purple lens annulus','dark primary lens','small oval sensor','yellow bill and mouth seam','long segmented dark neck','compact torso and paired hip bosses','left yellow boot','right raised yellow boot','left purple sole','right purple sole','left dark shin','right dark shin','winding knob and shaft','left drive wheel','left rear roller','right rear roller','replaceable elastic anchor'}
    assert len(c['landmarks'])==len(required) and {r['feature'] for r in c['landmarks']}==required,'landmark ledger omitted or duplicated defining feature'
    for row in c['landmarks']:
        p=parts[row['label']];bb=p.bounding_box()
        for end in ['min','max']:
            for i,axis in enumerate('XYZ'):
                near(f"{row['feature']} {end}.{axis}",tuple(getattr(bb,end))[i],row['bbox'][end][i],row.get('tolerance_mm',0.25))
        assert len(p.solids())==1, f"{row['feature']}: expected one solid"
        assert len(p.faces())>=row['min_faces'],f"{row['feature']}: expected ≥{row['min_faces']} faces, actual {len(p.faces())}"
        if 'circular_radii_mm' in row:
            radii={round(e.radius,5) for e in p.edges() if e.geom_type==GeomType.CIRCLE}
            for r in row['circular_radii_mm']:
                assert any(abs(r-v)<1e-4 for v in radii),f"{row['feature']}: missing radius {r}, actual {sorted(radii)}"
        rows.append({'feature':row['feature'],'label':row['label'],'faces':len(p.faces()),'bbox_mm':{'min':list(bb.min),'max':list(bb.max)}})
    frame=parts['frame'];circles=[e for e in frame.edges() if e.geom_type==GeomType.CIRCLE]
    for x,z in [(-10,62),(22,63)]:
        matched=[e for e in circles if abs(e.radius-2)<1e-5 and abs(e.arc_center.X-x)<1e-5 and abs(e.arc_center.Z-z)<1e-5]
        assert matched,f'paired hip recess at X{x},Z{z}: expected radius2 topology'
    for station in [91,103,115,128]:
        rib_edges=[e for e in circles if abs(e.radius-.8)<1e-5 and abs(e.arc_center.Y)<1e-5 and abs(e.arc_center.Z-station)<2]
        assert rib_edges,f'neck rib at Z{station}: missing radius0.8 fillet topology'
    torso_faces=[face for face in frame.faces() if face.geom_type==GeomType.PLANE and abs(face.center().Y+8)<1e-5]
    assert torso_faces,'compact torso front plane Y−8 missing'
    torso=max(torso_faces,key=lambda face:face.area).bounding_box()
    near('compact torso width',torso.size.X,47.5714286,.25)
    near('compact torso shoulder/cable top',torso.max.Z,(600-289)*180/560,.25)
    near('compact torso bottom',torso.min.Z,71.6785714,.25)
    lens=parts['lens'].bounding_box(); sensor=parts['sensor'].bounding_box()
    assert sensor.min.X>lens.max.X,'small sensor must lie right of purple lens'
    for side in ['left','right']:
        boot=parts['boot_'+side].bounding_box();sole=parts['sole_'+side].bounding_box();shin=parts['shin_'+side].bounding_box()
        near(side+' boot/sole seam',boot.min.Z-sole.max.Z,0.2,1e-5)
        near(side+' shin/boot seam',shin.min.Z-boot.max.Z,0.2,1e-5)
    near('right raised boot offset',parts['boot_right'].bounding_box().min.Z-parts['boot_left'].bounding_box().min.Z,8,1e-5)
    # Mouth groove adds its own internal edges and a recessed planar bottom.
    bill=parts['bill'];mouth_planes=[face for face in bill.faces() if face.geom_type==GeomType.PLANE and abs(face.center().Y+15.2)<1e-5]
    assert mouth_planes and sum(face.area for face in mouth_planes)>50,'yellow bill: missing deep mouth groove bottom'
    print(json.dumps({'ok':True,'landmarks':rows,'hip_recesses':2,'mouth_groove_bottom_area_mm2':sum(p.area for p in mouth_planes),'limitations':['Geometry landmarks do not certify reference silhouette; separate hero likeness must pass 0.90.','No physical print, traction or durability claim.']}))
if __name__=='__main__':
    try: main()
    except (AssertionError,KeyError) as e: print('FAIL landmarks:',e);sys.exit(1)
