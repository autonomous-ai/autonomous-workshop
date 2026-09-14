"""Analytic tangent arcs and planar channel footprints, supplied dimensions."""
from math import acos,tan
from build123d import Edge,Face,Kind,Polygon,Vector,Wire

def centerline(points,radius):
    pts=[Vector(x,y,0) for x,y in points]
    edges=[]
    last=pts[0]
    for previous,corner,following in zip(pts,pts[1:],pts[2:]):
        incoming=(corner-previous).normalized()
        outgoing=(following-corner).normalized()
        angle=acos(max(-1,min(1,incoming.dot(outgoing))))
        distance=radius*tan(angle/2)
        if distance>=min((corner-previous).length,(following-corner).length):
            raise ValueError('Tangent arc exceeds adjacent route segment')
        a,b=corner-incoming*distance,corner+outgoing*distance
        sign=1 if incoming.cross(outgoing).Z>0 else -1
        center=a+Vector(-incoming.Y,incoming.X,0)*radius*sign
        middle=center+((a-center)+(b-center)).normalized()*radius
        edges.extend((Edge.make_line(last,a),Edge.make_three_point_arc(a,middle,b)))
        last=b
    edges.append(Edge.make_line(last,pts[-1]))
    return Wire(edges)

def footprint(path,half_width,open_start,open_end,gap,bound):
    face=Face(path.offset_2d(half_width,kind=Kind.ARC))
    for at_start,opened in ((True,open_start),(False,open_end)):
        if not opened: continue
        t=0 if at_start else 1
        point=path.position_at(t)
        tangent=path.tangent_at(t).normalized()*(1 if at_start else -1)
        point+=tangent*gap/2
        normal=Vector(-tangent.Y,tangent.X,0)
        corners=[point-normal*bound,point+normal*bound,
                 point+normal*bound+tangent*bound,point-normal*bound+tangent*bound]
        keep=Polygon(*[(q.X,q.Y) for q in corners],align=None)
        pieces=face.intersect(keep)
        faces=list(pieces.faces()) if hasattr(pieces,'faces') else [f for part in pieces for f in part.faces()]
        if len(faces)!=1:
            raise ValueError(f'Route clipping must preserve one face, got {len(faces)}')
        face=faces[0]
    return face

def station(path,fraction,offset):
    point=path.position_at(fraction)
    direction=path.tangent_at(fraction).normalized()
    point+=Vector(-direction.Y,direction.X,0)*offset
    return point.X,point.Y
