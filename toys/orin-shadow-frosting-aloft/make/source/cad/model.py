from build123d import Align, Axis, Box, Cylinder, Compound, Face, Location, Vector, Wire, extrude
import params

def prism(poly, depth, label):
    wire = Wire.make_polygon([Vector(x, y, 0) for x, y in poly], close=True)
    body = extrude(Face(wire), amount=depth)
    body.label = label
    return body

def base_print():
    p = params
    wrapper = prism([(-26,0),(26,0),(22,p.WRAPPER_HEIGHT),(-22,p.WRAPPER_HEIGHT)], p.DEPTH, "wrapper_basket")
    # Sink the rim into the tapered wrapper so the upper guide bridge fuses
    # robustly instead of meeting it on a numerically fragile boundary.
    rim = Box(46, 8, p.DEPTH, align=(Align.MIN,Align.MIN,Align.MIN)).located(Location((-23,p.WRAPPER_HEIGHT-5,0)))
    ribs = []
    for x in (-17,-8,8,17):
        ribs.append(prism([(x-1,2),(x+1,2),(x+2,p.WRAPPER_HEIGHT-2),(x-2,p.WRAPPER_HEIGHT-2)], p.DEPTH, "wrapper_flute"))
    guides = []
    for x in (-p.GUIDE_X,p.GUIDE_X):
        stem = Box(p.GUIDE_W,p.GUIDE_TOP-p.WRAPPER_HEIGHT+2,p.DEPTH,align=(Align.MIN,Align.MIN,Align.MIN)).located(Location((x-p.GUIDE_W/2,p.WRAPPER_HEIGHT-2,0)))
        # Overlap the stem by 1 mm so the rounded travel stop is one printable body.
        marker = Cylinder(3.5,p.DEPTH,align=(Align.CENTER,Align.CENTER,Align.MIN)).located(Location((x,p.GUIDE_TOP-1,0)))
        guides.extend([stem,marker])
    # The tapered wrapper is also the balloon basket; no separate plinth is
    # needed, which keeps the raised transformation visibly two-part.
    basket_floor = Box(52, 4, p.DEPTH, align=(Align.CENTER,Align.MIN,Align.MIN)).located(Location((0,0,0)))
    shape = wrapper + rim + basket_floor
    for body in ribs + guides:
        shape = shape + body
    shape.label = "wrapper_guide_base"
    return shape

def cap_print():
    p=params
    # One continuous full-depth outline avoids fragile tangent unions while
    # retaining three frosting lobes, a cherry grip, and the raised balloon read.
    body = prism([
        (-20,26),(-20,32),(-28,32),(-28,38),(-34,38),(-34,44),(-39,44),(-39,62),(-32,62),(-32,70),
        (-12,70),(-12,76),(-6,76),(-6,84),(6,84),(6,76),
        (12,76),(12,70),(32,70),(32,62),(39,62),(39,44),
        (34,44),(34,38),(28,38),(28,32),(20,32),(20,26)
    ][::-1], p.DEPTH, "frosting_balloon_face")
    # High-relief pixel features keep the lowered state unmistakably cupcake-like
    # even in a single-material render: two eyes, a three-segment smile, and stem.
    relief_z = p.DEPTH - 0.2
    for x in (-12, 12):
        body = body + Box(4, 5, 1.6, align=(Align.CENTER,Align.CENTER,Align.MIN)).located(Location((x,55,relief_z)))
    body = body + Box(18, 3, 1.6, align=(Align.CENTER,Align.CENTER,Align.MIN)).located(Location((0,43,relief_z)))
    for x in (-10, 10):
        body = body + Box(3, 6, 1.6, align=(Align.CENTER,Align.CENTER,Align.MIN)).located(Location((x,46,relief_z)))
    body = body + Box(3, 9, p.DEPTH, align=(Align.CENTER,Align.MIN,Align.MIN)).located(Location((0,82,0)))
    # Rear cheek pairs form open guide channels; cheeks connect to the filled face.
    cheek_depth = 6.0
    for x in (-p.GUIDE_X,p.GUIDE_X):
        gap = p.GUIDE_W + 2*p.SLIDE_CLEARANCE
        for sx in (-1,1):
            cx = x + sx*(gap/2 + 1.6)
            cheek = Box(3.2,31,cheek_depth,align=(Align.MIN,Align.MIN,Align.MIN)).located(Location((cx-1.6,34,-5.0)))
            body = body + cheek
    body.label = "frosting_slider_cap"
    return body

def cap_bed():
    """Cap in its broad-face, support-free print orientation at Z=0."""
    return cap_print().translate((0,0,5.0))

def upright(shape, depth_offset, z_offset=0):
    return shape.rotate(Axis.X,90).translate((0,depth_offset,z_offset))

def assembly(state="raised"):
    travel = 0 if state == "lowered" else params.TRAVEL if state == "raised" else params.TRAVEL/2
    base = upright(base_print(), params.BASE_FOOT_DEPTH)
    cap = upright(cap_print(), params.DEPTH, z_offset=travel)
    base.label="base_fixed"
    cap.label=f"cap_{state}"
    return Compound(children=[base,cap], label=f"frosting_aloft_{state}")
