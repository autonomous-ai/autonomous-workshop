"""Reference-shaped back-flat robot chassis. All units mm; source proportions observed in hero.png.
The common rear plane is a deliberate print face, not a hidden sealed cavity.
"""
from build123d import *
from cadgen import AssemblyHelper
import cadfits
from drive_lib import drive_frame_cutters, rear_pin_socket, rear_wheel_clearance, anchor_tab_socket
from drive_lib import build_rotor, build_left_drive_wheel, build_rear_roller, build_rear_pin, build_fixed_anchor

HEIGHT = 180.0
PIXEL_SCALE = HEIGHT / 560
REAR_Y = 18.0
FRONT_HEAD_Y = -12.0
WALL_MIN = 2.4
LENS_OUTER_D = 19.6
LENS_INNER_D = 10.0
LENS_CENTER = (-1.45, -15.0, 160.4)
FACE_GAP = 0.2
GREY = Color(0.40, 0.42, 0.42)
PURPLE = Color(0.57, 0.46, 0.72)
YELLOW = Color(0.95, 0.79, 0.15)
BLACK = Color(0.08, 0.09, 0.09)
# The manually observed front contour retains the canted bill and neck offset.
HEAD_PIXELS = [(82,165),(81,130),(84,108),(89,89),(97,73),(109,61),(128,52),(151,45),(181,40),(204,40),(222,44),(237,55),(247,70),(256,93),(266,122),(275,153),(274,182),(259,199),(219,207),(174,209),(132,202),(103,190)]
NECK_PIXELS = [(150,211),(224,194),(240,213),(237,251),(236,278),(232,330),(213,344),(184,338),(185,311),(178,304),(177,274),(182,250),(167,240),(156,230)]
TORSO_PIXELS = [(98,308),(125,301),(143,296),(143,289),(153,292),(160,301),(169,303),(207,315),(238,316),(239,356),(234,373),(202,377),(121,374),(103,367),(93,355),(91,322)]
PELVIS_PIXELS = [(112,369),(222,370),(237,393),(227,447),(190,452),(174,455),(146,455),(120,450),(106,436)]
LEFT_LEG_PIXELS = [(100,392),(123,405),(118,454),(115,489),(128,530),(138,555),(105,572),(76,561),(66,515),(83,492),(45,496),(35,477),(29,438),(34,421),(62,398),(80,391)]
RIGHT_LEG_PIXELS = [(221,388),(275,386),(292,398),(294,418),(278,450),(263,478),(264,507),(280,544),(255,556),(213,551),(207,514),(209,486),(195,463),(184,433),(191,405)]
# Bill lower-left relief accounts for the front-plane projection; right lug follows observed pixels135..157.
BILL_PIXELS = [(82,165),(274,132),(281,135),(282,143),(284,149),(283,157),(282,185),(274,201),(254,211),(224,214),(220,201),(180,200),(155,205),(140,207),(112,196),(88,189),(82,180)]


def profile(pixels, front, back):
    points=[((x-170)*PIXEL_SCALE, (600-z)*PIXEL_SCALE) for x,z in pixels]
    wire=Wire.make_polygon([Vector(x,front,z) for x,z in points], close=True)
    return extrude(Face(wire), amount=back-front, dir=(0,1,0))


def cyl_y(radius, length, x, y, z):
    return Pos(x,y,z)*Rot(-90,0,0)*Cylinder(radius,length,align=(Align.CENTER,Align.CENTER,Align.MIN))


def rounded_block(width,depth,height,x,y,z,radius=2):
    p=Box(width,depth,height)
    p=fillet(p.edges().filter_by(Axis.Y),radius)
    return Pos(x,y,z)*p


def foot_blank(side):
    return rounded_block(33 if side<0 else 34,38,15,-19.5 if side<0 else 25,-1,9.9 if side<0 else 17.9,4)


def foot_front_blank(side, gap=0.2):
    # The broad flat front is the print face. The rear foot remains structural.
    return foot_blank(side) & (Pos(0,-28.6-gap/2,10)*Box(120,43.2-gap,40))


def build_boot(side, sole=False):
    p=foot_front_blank(side)
    zlo,zhi=(2.4,7.2) if sole else (7.4,17.4)
    if side>0: zlo+=8; zhi+=8
    p &= Pos(0,0,(zlo+zhi)/2)*Box(120,100,zhi-zlo)
    p -= drive_frame_cutters()
    # Open outer rear panel corners instead of leaving a thin wheel-cut web.
    p -= Pos(-48.5 if side<0 else 48.5,-2.6,10)*Box(43,29.2,50)
    if side<0 and not sole:
        p -= Pos(-42,0,18.1)*Box(26,100,3.8)
    p.label=('sole_' if sole else 'boot_')+('left' if side<0 else 'right')
    p.color=PURPLE if sole else YELLOW
    return p


def build_head_rim():
    # A raised C-shaped bezel follows the crown; its ends stop at the bill.
    inset=[(177+(x-177)*0.87,125+(z-125)*0.85) for x,z in HEAD_PIXELS]
    p=profile(HEAD_PIXELS,-15.0,-12.2)-profile(inset,-15.1,-12.1)
    p-=profile(BILL_PIXELS,-16,-12)
    # The bill separates a redundant lower crescent; end the bezel above it.
    p &= Pos(0,0,192)*Box(200,100,100)
    p.label='head_rim';p.color=BLACK
    return p


def build_dark_lens():
    p=cyl_y(4.6,5.2,LENS_CENTER[0],-14.8,LENS_CENTER[2])
    p.label='dark_lens';p.color=BLACK
    return p


def build_sensor():
    p=Pos(14.8,-13.0,160.4)*Rot(-90,0,0)*extrude(Ellipse(2.9,1.5),amount=3.0)
    p.label='sensor';p.color=BLACK
    return p


def build_neck_skin():
    # Segmented dark service spine; grey ribs remain parts of the rear frame.
    p=profile(NECK_PIXELS,0,2.8)
    p-=profile(HEAD_PIXELS,-1,4)
    p-=profile(TORSO_PIXELS,-1,4)
    p &= Pos(0,0,112)*Box(150,50,32)
    for z in (91,103,115,128):
        p-=rounded_block(12.4,5,4.4,13,1,z,1.0)
    p.label='neck_skin';p.color=BLACK
    return p


def build_shin_skin(side):
    pixels=([(69,501),(99,496),(120,544),(100,551),(79,549)] if side<0 else
            [(225,480),(257,477),(271,539),(239,539)])
    p=profile(pixels,2,4.8)
    # End each shin above its boot; leave a visible 0.2 mm assembly seam.
    floor=17.6 if side<0 else 25.6
    p &= Pos(0,0,(floor+80)/2)*Box(200,100,80-floor)
    p.label='shin_'+('left' if side<0 else 'right');p.color=BLACK
    return p


def raw_frame():
    head=profile(HEAD_PIXELS,FRONT_HEAD_Y,REAR_Y)
    # Only depth-running edges are rounded; observed profile stations survive.
    try: head=fillet(head.edges().filter_by(Axis.Y),2.0)
    except ValueError: pass
    neck=profile(NECK_PIXELS,3,REAR_Y)
    torso=profile(TORSO_PIXELS,-8,REAR_Y)
    pelvis=profile(PELVIS_PIXELS,4,REAR_Y)
    legs=profile(LEFT_LEG_PIXELS,5,REAR_Y)+profile(RIGHT_LEG_PIXELS,5,REAR_Y)
    feet=foot_blank(-1)+foot_blank(1)
    # Raised far boot follows the observed staggered pose. Low bearing webs
    # preserve the common ground axle and rear idler support independently.
    feet+=rounded_block(6,14,14,25.6,-6,10,2)
    feet+=rounded_block(6,12,18,26,12,12,2)
    body=head+neck+torso+pelvis+legs+feet
    # Recessed lens and second sensor remain inspectable topology in the frame.
    body-=cyl_y(LENS_INNER_D/2,2.8,LENS_CENTER[0],FRONT_HEAD_Y-0.1,LENS_CENTER[2])
    body-=Pos(14.8,-12,160.4)*Rot(-90,0,0)*extrude(Ellipse(3.2,1.8),amount=2.4)
    # Raised neck ribs and paired circular mechanical hip bosses are structural relief.
    for z in (91,103,115,128):
        body+=rounded_block(12,4,4,13,2,z,0.8)
    for x,z in ((-10,62),(22,63)):
        body+=cyl_y(6.5,6,x,-1,z)
        body-=cyl_y(2.0,2.0,x,-1.1,z)
    return body


def build_frame():
    body=raw_frame()
    # Anchor support bridges into the left foot above the rotor corridor.
    body += Pos(-36.35,-6,20)*Box(12.3,10,10)
    # Overhead bridge and inner web keep the anchor connected after opening
    # exterior wheel access; both remain outside the swept drive envelope.
    body += Pos(-31.35,-6,23)*Box(22.3,10,4)
    body += Pos(-24,-6,18)*Box(4,10,14)
    # Continuous rear lands support the anchor bridge and low right bearing
    # when printed rear-face down. Avoid the recorded cantilevered-foot trap.
    body += Pos(-31.35,8.5,23)*Box(22.3,19,4)
    body += Pos(-40.25,8.5,20)*Box(4.5,19,10)
    body += Pos(25.6,2.5,12)*Box(6,31,18)
    body -= drive_frame_cutters()
    # A 45-degree teardrop crown above the horizontal shaft bore prints
    # rear-face down without a floating semicircular front lip.
    crown=Face(Wire.make_polygon([Vector(-28.6,y,z) for y,z in
        [(-12.23,10),(-9.11,6.89),(-9.11,13.11)]],close=True))
    body -= extrude(crown,amount=57.2,dir=(1,0,0))
    for side in (-1,1):
        body -= rear_pin_socket(side)
        body -= rear_wheel_clearance(side)
    body -= anchor_tab_socket()
    # Front boot panels are separate colour parts with a 0.2 mm adhesive seam.
    for side in (-1,1):
        body -= foot_front_blank(side, gap=0.0)
    # Open the feather-thin outer rear corner beyond the roller socket.
    body -= Pos(-39.8,18,6)*Box(20.4,5,12)
    # Open outboard wheel guards below the anchor bridge; coloured front boot
    # panels retain the observed foot outline without unsupported rear lips.
    body -= Pos(54.3,5.5,10)*Box(51.4,25,22)
    body -= Pos(-33.3,0,10)*Box(9.4,60,22)
    body -= Pos(-54,5.5,7)*Box(32,25,16)
    # Maintain the separate shin's seating clearance through the new bridge.
    # Open the seat through the front so no unsupported roof spans the recess.
    shin_clearance=profile([(69,501),(99,496),(120,544),(100,551),(79,549)],-20,5)
    shin_clearance &= Pos(0,0,48.8)*Box(200,100,62.4)
    body -= shin_clearance
    body.label='frame';body.color=GREY
    return body


def build_bill():
    # A shallow shaped cover seated on the head; adhesive joins the broad rear land.
    p=profile(BILL_PIXELS,-18,-12-FACE_GAP)
    mouth=[(91,168),(268,139),(269,144),(91,174)]
    p-=profile(mouth,-18.1,-15.2)
    p.label='bill';p.color=YELLOW
    return p


def build_lens():
    x,y,z=LENS_CENTER
    p=cyl_y(LENS_OUTER_D/2,3.0,x,y,z)-cyl_y(LENS_INNER_D/2,3.2,x,y-0.1,z)
    p.label='lens';p.color=PURPLE
    return p


def print_pose(p):
    p=p.rotate(Axis.X,-90)
    return p.translate((0,0,-p.bounding_box().min.Z))


def build_assembly():
    a=AssemblyHelper('microduck')
    a.add(build_frame(),'frame',color=GREY)
    a.add(build_bill(),'bill',color=YELLOW)
    a.add(build_lens(),'lens',color=PURPLE)
    for name,builder in [('head_rim',build_head_rim),('dark_lens',build_dark_lens),('sensor',build_sensor),('neck_skin',build_neck_skin)]:
        a.add(builder(),name,color=BLACK)
    for side,suffix in [(-1,'left'),(1,'right')]:
        a.add(build_boot(side),'boot_'+suffix,color=YELLOW)
        a.add(build_boot(side,True),'sole_'+suffix,color=PURPLE)
        a.add(build_shin_skin(side),'shin_'+suffix,color=BLACK)
    for name,part,color in [('rotor',build_rotor(),PURPLE),('left_wheel',build_left_drive_wheel(),PURPLE),('anchor',build_fixed_anchor(),BLACK)]:
        part.color=color; a.add(part,name,color=color)
    for side,suffix in [(-1,'left'),(1,'right')]:
        for role,builder,color in [('roller',build_rear_roller,PURPLE),('pin',build_rear_pin,GREY)]:
            part=builder(side);part.color=color;a.add(part,role+'_'+suffix,color=color)
    return a.build()
