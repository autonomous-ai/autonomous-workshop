# Feasibility arithmetic for the Formula racer mecha. Car frame: x from tail (0) to nose, robot z = height.
import math
L=230; rear_axle=40; front_axle=180; Rr=18; Rf=16
foot_h=25; leg_bottom=15; hip=120; shoulder=front_axle
z=lambda x: foot_h+(x-leg_bottom)          # car x on the standing car -> robot height
print("hip z",z(hip),"shoulder z",z(shoulder),"rear wheel centre z",z(rear_axle),"span",z(rear_axle)-Rr,z(rear_axle)+Rr)
head_top=z(shoulder)+Rf+12; print("shoulder wheel top",z(shoulder)+Rf,"head top ~",head_top)
nose=(L-front_axle); print("nose length",nose,"-> folded covers z",z(shoulder)-nose,"to",z(shoulder))
arm_shell=165-120; print("arm shell",arm_shell,"needed ~80 -> forearm slide-out",80-arm_shell)
for spine in (110,90):
    print("spine",spine,"wing top z",z(hip)+spine,"(head top",head_top,")  wing in car at x",hip-spine)
# rough centre of mass, robot frame x forward (+ = front), volumes in mm^3
B=[("torso",55*60*30,0),("nose+wing",18000,21),("head",7000,0),("front wheels",2*math.pi*Rf**2*14,0),
   ("arms",2*18*80*20,0),("spine",20*90*10,-30),("rear wing",80*15*20,-35),("airbox",6000,-30),
   ("legs",2*23*85*28,0),("rear wheels",2*math.pi*Rr**2*18,0),("feet",2*23*25*45,7.5)]
M=sum(v for _,v,_ in B); cx=sum(v*x for _,v,x in B)/M
print("COM x %.1f mm; foot without heel spans x 0..30, with heel -15..30"%cx)
