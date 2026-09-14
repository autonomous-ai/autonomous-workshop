"""Deterministic source-BRep return-path audit; no trajectory/physical claim."""
import json,math
from pathlib import Path
from build123d import Pos,Sphere
import params as p
from assemblies.return_system import components,hardware_parts
from parts.return_channel import route

def volume(shape):
    if shape is None:return 0.0
    if hasattr(shape,'volume'):return abs(shape.volume)
    return sum(abs(s.volume) for s in shape)

def audit():
    parts=components()+hardware_parts()
    fixed=[(name,s,s.bounding_box()) for name,s,_ in parts]
    failures=[];samples=[]
    def test(label,point):
        sphere=Pos(*point)*Sphere(p.MARBLE_MAX_D/2)
        sb=sphere.bounding_box();maximum=0.0
        for name,shape,b in fixed:
            if any(getattr(sb.max,k)<getattr(b.min,k) or getattr(b.max,k)<getattr(sb.min,k) for k in 'XYZ'):
                continue
            overlap=volume(sphere.intersect(shape))
            maximum=max(maximum,overlap)
            if overlap>0.001:failures.append({'pose':label,'part':name,'center':point,'overlap_mm3':overlap})
        samples.append({'pose':label,'center':point,'maximum_overlap_mm3':maximum})
    heights=[]
    for i,points in enumerate(p.RETURN_PATHS):
        path=route(i)
        steps=math.ceil(path.length/2)
        for j in range(steps+1):
            v=path.position_at(j/steps)
            point=(v.X+points[0][0],v.Y+points[0][1],p.RETURN_FLOOR_Z+p.MARBLE_MAX_D/2)
            test(f'channel_{i}_{j}',point)
            heights.append(point[1]*math.sin(math.radians(p.INCLINE_DEG))+point[2]*math.cos(math.radians(p.INCLINE_DEG)))
    for j in range(133):
        z=p.HOPPER_TOP_Z-j*(p.HOPPER_TOP_Z-p.RETURN_FLOOR_Z-p.MARBLE_MAX_D/2)/132
        test(f'hopper_drop_{j}',(*p.HOPPER_CENTER,z))
    x,y=p.RETURN_PATHS[-1][-1]
    direction=route(len(p.RETURN_PATHS)-1).tangent_at(1).normalized()
    radius=p.MARBLE_MAX_D/2
    end_angle=math.acos(1-(p.RETURN_FLOOR_Z-p.CUP_FLOOR_Z)/radius)
    for j in range(17):
        # Clearance envelope rolls over the real terminal edge before dropping;
        # a vertical descent while still straddling that edge is impossible.
        angle=end_angle*j/16
        advance=radius*math.sin(angle)
        z=p.RETURN_FLOOR_Z+radius*math.cos(angle)
        test(f'cup_rolloff_{j}',(x+direction.X*advance,y+direction.Y*advance,z))
    return {'scope':'Source free-space samples against return parts/hardware only; not a predicted trajectory or physical test',
            'sample_count':len(samples),'marble_diameter_mm':p.MARBLE_MAX_D,
            'downhill_centerline':all(b<=a+1e-7 for a,b in zip(heights,heights[1:])),
            'failures':failures,'samples':samples,'pass':not failures and all(b<=a+1e-7 for a,b in zip(heights,heights[1:]))}

if __name__=='__main__':
    result=audit()
    Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='samples'},indent=2))
    raise SystemExit(0 if result['pass'] else 1)
