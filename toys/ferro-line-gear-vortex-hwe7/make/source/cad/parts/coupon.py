"""Print this journal/mesh support with one extra14 and15 gear and two caps first."""
from functools import lru_cache
from build123d import Box,Pos,Color,Align
from params import *
from parts.carrier import post

@lru_cache(maxsize=None)
def coupon():
    body=Box(COUPON_LENGTH,COUPON_WIDTH,COUPON_HEIGHT,align=(Align.CENTER,Align.CENTER,Align.MIN))
    distance=M*(TEETH[0]+TEETH[1])/2
    body=body.fuse(Pos(-distance/2,0,0)*post(),Pos(distance/2,0,0)*post())
    body.color=Color(*BLACK)
    return body
