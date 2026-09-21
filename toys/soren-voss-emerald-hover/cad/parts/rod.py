"""One square pushrod, shortened for the lowered crosshead tongue."""
from build123d import Box,Align
import params as p
from features.primitives import finish

def rod():
    return finish(Box(p.ROD_SIDE,p.ROD_SIDE,p.ROD_LENGTH,align=(Align.CENTER,Align.CENTER,Align.MIN)),'vertical_pushrod',p.DARK_BRASS)
