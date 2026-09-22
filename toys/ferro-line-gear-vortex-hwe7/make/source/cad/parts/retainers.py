from functools import lru_cache
from build123d import Color,Cone,Pos,Align
from params import CAP_OD,CAP_HEIGHT,POST_DIAMETER,POST_THREAD_DEPTH,POST_THREAD_PITCH,THREAD_CLEARANCE,BLACK,CAP_LEAD_IN,CAP_LEAD_HEIGHT
from features.threads import cylinder,female_tool

@lru_cache(maxsize=None)
def gear_cap():
    body=cylinder(CAP_OD/2,CAP_HEIGHT)
    body=body-female_tool(POST_DIAMETER/2,POST_THREAD_DEPTH,POST_THREAD_PITCH,CAP_HEIGHT,THREAD_CLEARANCE)
    minor=POST_DIAMETER/2-POST_THREAD_DEPTH+THREAD_CLEARANCE
    lead=minor+CAP_LEAD_IN
    body=body-Cone(lead,minor,CAP_LEAD_HEIGHT,align=(Align.CENTER,Align.CENTER,Align.MIN))
    body=body-Pos(0,0,CAP_HEIGHT-CAP_LEAD_HEIGHT)*Cone(minor,lead,CAP_LEAD_HEIGHT,align=(Align.CENTER,Align.CENTER,Align.MIN))
    body.color=Color(*BLACK)
    return body
