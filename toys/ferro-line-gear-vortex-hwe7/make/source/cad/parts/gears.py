"""Seven swept-spoke planet sizes and the stationary core wheel."""
from functools import lru_cache
from build123d import Color,Box,Pos
from params import TEETH,GEAR_BORE,HUB_RADIUS,SUN_TEETH,SUN_BORE,SUN_HUB_RADIUS,BRASS
from features.gearing import gear_solid

@lru_cache(maxsize=None)
def planet_by_teeth(teeth):
    index=TEETH.index(teeth)
    body=gear_solid(teeth,GEAR_BORE,HUB_RADIUS,-1 if index%2==0 else 1)
    body.color=Color(*BRASS)
    return body

def planet(index):
    return planet_by_teeth(TEETH[index])

@lru_cache(maxsize=None)
def sun():
    body=gear_solid(SUN_TEETH,SUN_BORE,SUN_HUB_RADIUS,1)
    from features.threads import cylinder
    keyfill=cylinder(SUN_BORE/2+.2,5)&(Pos(8.3+1,0,2.5)*Box(2,8,5))
    body=body.fuse(keyfill)
    body.color=Color(*BRASS)
    return body
