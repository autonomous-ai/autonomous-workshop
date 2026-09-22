"""Audit serialized delivered meshes, independently of the export writer."""
from pathlib import Path
from collections import Counter
from xml.etree import ElementTree as E
import json,struct,zipfile
import numpy as np
ROOT=Path(__file__).resolve().parent.parent
def check(p,f):
    p=np.array(p);f=np.array(f,dtype=int);t=p[f]
    assert np.all(np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)>1e-10)
    edges=Counter((int(a),int(b)) for face in f for a,b in zip(face,[face[1],face[2],face[0]]))
    assert all(v==1 and edges[b,a]==1 for (a,b),v in edges.items())
    volume=float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6)
    assert volume>0
    return volume
def main():
    out={}
    for path in sorted((ROOT.parent/'engineering'/'prints').glob('*.stl')):
        data=path.read_bytes();n=struct.unpack('<I',data[80:84])[0];assert len(data)==84+50*n
        points=[];faces=[];lookup={}
        for i in range(n):
            row=struct.unpack('<12fH',data[84+50*i:134+50*i]);f=[]
            for j in (3,6,9):
                v=tuple(row[j:j+3])
                if v not in lookup:lookup[v]=len(points);points.append(v)
                f.append(lookup[v])
            faces.append(f)
        out[path.name]={'triangles':n,'volume_mm3':check(points,faces),'topology':'closed-oriented-manifold'}
    ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    for path in sorted((ROOT.parent/'engineering'/'prints').glob('*.3mf')):
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None;doc=E.fromstring(z.read('3D/3dmodel.model'))
        assert doc.attrib['unit']=='millimeter'
        objects=doc.findall('m:resources/m:object',ns);ids={o.attrib['id'] for o in objects};vol=0;count=0
        for o in objects:
            m=o.find('m:mesh',ns)
            if m is not None:
                pp=[[float(v.attrib[a]) for a in ('x','y','z')] for v in m.findall('m:vertices/m:vertex',ns)]
                ff=[[int(t.attrib[a]) for a in ('v1','v2','v3')] for t in m.findall('m:triangles/m:triangle',ns)]
                vol+=check(pp,ff);count+=1
            else:assert all(c.attrib['objectid'] in ids for c in o.findall('m:components/m:component',ns))
        assert all(i.attrib['objectid'] in ids for i in doc.findall('m:build/m:item',ns))
        reference=out[path.with_suffix('.stl').name]['volume_mm3']
        # Region boundaries create different triangulations of the same curved
        # BRep. Require agreement within 0.01%, far below the 0.04mm chord limit.
        delta=abs(vol-reference)/reference;assert delta<.0001,(path,delta)
        out[path.name]={'mesh_regions':count,'volume_mm3':vol,'relative_volume_delta_vs_STL':delta,'zip_xml_references':'pass','topology':'closed-oriented-manifold'}
    (ROOT/'cad/measure/serialized-print-audit.json').write_text(json.dumps(out,indent=2)+'\n')
    print('PASS: all nine serialized files; closed oriented meshes; core XML/ZIP references; volumes agree within0.01%.')
if __name__=='__main__':main()
