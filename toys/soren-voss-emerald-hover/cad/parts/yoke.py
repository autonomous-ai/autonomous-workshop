"""One windowed gravity follower; contact rails remain continuous."""
from build123d import Box
import params as p
from features.primitives import box_at,finish
from features.prisms import xz_prism

def yoke():
    raw=Box(p.YOKE_X,p.YOKE_Y,p.YOKE_Z)-Box(p.YOKE_X+p.CUT_RADIAL_EXTENSION,p.TUNNEL_Y,p.TUNNEL_Z)
    raw=raw-box_at(-p.ROD_SOCKET/2,p.ROD_SOCKET/2,-p.ROD_SOCKET/2,p.ROD_SOCKET/2,p.YOKE_Z/2-p.ROD_SOCKET_DEPTH,p.YOKE_Z/2+p.CUT_EXTENSION)
    raw=raw-xz_prism(p.YOKE_WINDOW_XZ,*p.YOKE_WINDOW_Y)
    return finish(raw,'weighted_cam_yoke',p.BRASS)
