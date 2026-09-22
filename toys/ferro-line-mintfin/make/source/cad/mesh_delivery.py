"""Explicitly requested mesh delivery; exact STEP tessellation with topology audit.
No inference, mesh healing or geometry substitution. Units millimetres.
"""
from collections import Counter, defaultdict
from pathlib import Path
import json, math, struct, zipfile
from xml.etree import ElementTree as ET
import numpy as np
from build123d import import_step


def mesh(shape):
    verts, triangles = shape.tessellate(0.04, 0.08)
    lookup, points, index = {}, [], []
    for v in verts:
        key = tuple(round(float(c), 6) for c in v)
        if key not in lookup:
            lookup[key] = len(points)
            points.append(key)
        index.append(lookup[key])
    faces = [tuple(index[i] for i in f) for f in triangles]
    assert all(len(set(f)) == 3 for f in faces), 'Collapsed triangle'
    assert len({tuple(sorted(f)) for f in faces}) == len(faces), 'Duplicate triangle'
    edges, directed = Counter(), Counter()
    adjacent = defaultdict(set)
    for f in faces:
        for a,b in zip(f, (f[1],f[2],f[0])):
            edges[tuple(sorted((a,b)))] += 1
            directed[(a,b)] += 1
            adjacent[a].add(b); adjacent[b].add(a)
    assert set(edges.values()) == {2}, 'Nonmanifold or open edge'
    assert all(directed[(a,b)] == directed[(b,a)] == 1 for a,b in edges), 'Inconsistent winding'
    unseen = set(range(len(points))); shells = 0
    while unseen:
        shells += 1; stack = [unseen.pop()]
        while stack:
            for j in adjacent[stack.pop()]:
                if j in unseen:
                    unseen.remove(j); stack.append(j)
    p = np.array(points)
    volume = sum(float(np.dot(p[a], np.cross(p[b], p[c])))/6 for a,b,c in faces)
    assert volume > 0, 'Nonpositive mesh volume'
    return points, faces, {'vertices':len(points),'triangles':len(faces),'shells':shells,'volume_mm3':volume,'watertight':True,'manifold':True,'consistent_winding':True}


def stl(path, points, faces):
    p=np.array(points)
    with Path(path).open('wb') as f:
        f.write(b'Mintfin exact validated STEP tessellation'.ljust(80,b' '))
        f.write(struct.pack('<I',len(faces)))
        for a,b,c in faces:
            normal=np.cross(p[b]-p[a],p[c]-p[a]); length=np.linalg.norm(normal)
            assert length > 1e-10
            values=[*(normal/length),*p[a],*p[b],*p[c]]
            f.write(struct.pack('<12fH',*values,0))


def three_mf(path, objects, groups):
    """Objects: name/color/points/faces; groups: name and object-index members."""
    ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    ET.register_namespace('',ns)
    def tag(n): return '{'+ns+'}'+n
    model=ET.Element(tag('model'),{'unit':'millimeter','xml:lang':'en-US'})
    resources=ET.SubElement(model,tag('resources'))
    materials=ET.SubElement(resources,tag('basematerials'),{'id':'1'})
    palette=list(dict.fromkeys(o['color'] for o in objects))
    for color in palette: ET.SubElement(materials,tag('base'),{'name':color,'displaycolor':color+'FF'})
    for i,o in enumerate(objects,2):
        obj=ET.SubElement(resources,tag('object'),{'id':str(i),'type':'model','name':o['name'],'pid':'1','pindex':str(palette.index(o['color']))})
        m=ET.SubElement(obj,tag('mesh')); vv=ET.SubElement(m,tag('vertices')); tt=ET.SubElement(m,tag('triangles'))
        for p in o['points']: ET.SubElement(vv,tag('vertex'),dict(zip(('x','y','z'),map(str,p))))
        for f in o['faces']: ET.SubElement(tt,tag('triangle'),dict(zip(('v1','v2','v3'),map(str,f))))
    build=ET.SubElement(model,tag('build'))
    for i,g in enumerate(groups,len(objects)+2):
        obj=ET.SubElement(resources,tag('object'),{'id':str(i),'type':'model','name':g['name']})
        cc=ET.SubElement(obj,tag('components'))
        for j in g['members']: ET.SubElement(cc,tag('component'),{'objectid':str(j+2)})
        ET.SubElement(build,tag('item'),{'objectid':str(i)})
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
