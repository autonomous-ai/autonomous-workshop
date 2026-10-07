"""The Pixel Tree Key contract numbers (mm). Body bands: (y_lo, y_hi, x_lo, x_hi)."""
TREE = [  # name, y_lo, y_hi, half-width, top to bottom
 ("neck",32.0,33.0,1.25),("T1",30.0,32.0,3.1),("T2",25.75,30.0,4.9),("T3",23.75,25.75,6.75),
 ("T4",17.5,23.75,8.5),("T5",15.5,17.5,10.4),("T6",13.0,15.5,12.2),
 ("T7",10.75,13.0,13.9),("T8",8.5,10.75,15.6),("T9",6.0,8.5,17.3),("T10",3.5,6.0,18.95),("T11",0.0,3.5,20.7)]
def bands():
    b=[(n,lo,hi,-hw,hw) for n,lo,hi,hw in TREE]
    b += [("U1",-2.0,0.0,-18.95,18.95),("U2",-4.5,-2.0,-17.3,17.3),("U3",-6.5,-4.5,-7.5,7.5),
          ("shaft",-23.0,-6.5,-4.75,4.75),
          ("bit1",-25.0,-23.0,-4.75,7.75),("tooth1",-28.25,-25.0,-4.75,10.5),("bit2",-29.5,-28.25,-4.75,7.75),
          ("notch",-31.5,-29.5,-4.75,5.75),("tooth2a",-33.75,-31.5,-4.75,10.5),("tooth2b",-36.5,-33.75,-4.75,12.25),
          ("bit3",-39.0,-36.5,-4.75,7.75),("bit4",-41.0,-39.0,-4.75,5.75),("tab",-43.25,-41.0,-2.0,3.0)]
    return b
STAR = [("arm-bottom",33.0,35.0,-1.0,1.0),("bar",35.0,37.0,-3.0,3.0),("arm-top",37.0,39.0,-1.0,1.0)]
BAUBLES = {"R1":(0.5,19.2),"R2":(-5.5,15.25),"R3":(5.5,15.25),"R4":(4.25,4.0),"R5":(14.5,3.5),"R6":(-0.75,-0.25),
           "G1":(-1.9,22.85),"G2":(1.25,11.25),"G3":(8.75,8.0),"G4":(-5.0,7.25),"G5":(-13.5,4.5),"G6":(10.25,0.0)}
POCKET = (-11.15,11.15,-2.5,9.4)  # x0,x1,y0,y1 ; Z 0.8..1.8
GROOVE = (-0.5,0.5,-40.0,-6.0)
if __name__=="__main__":
    for b in bands(): print(b)
    import itertools
    ks=list(BAUBLES)
    for a,c in itertools.combinations(ks,2):
        (x1,y1),(x2,y2)=BAUBLES[a],BAUBLES[c]
        g=max(abs(x1-x2),abs(y1-y2))-2.0
        if g<1.6: print("web under 1.6",a,c,round(g,2))
    # bauble inside body with 1 mm margin
    bb=bands()
    def inside(x,y):
        return any(lo<=y<=hi and xl<=x<=xr for _,lo,hi,xl,xr in bb)
    for k,(x,y) in BAUBLES.items():
        ok=all(inside(x+dx,y+dy) for dx in (-2,2) for dy in (-2,2))
        print(k,'inside+1mm',ok, 'over pocket', POCKET[0]-1<x<POCKET[1]+1 and POCKET[2]-1<y<POCKET[3]+1)
