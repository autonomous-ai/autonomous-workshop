"""Deterministic geometry and conditional torsion calculation, not physical testing."""
from pathlib import Path
import sys,json,math,hashlib
P=Path(__file__).resolve().parents[1]
# CAD dependencies are provided by the verifier/runtime, independent of host workspace.
sys.path.insert(0,str(P))
from build123d import Pos,Box,CenterOf
import drive_lib as d
import duck_lib as f

def main():
    frame=f.build_frame();rotor=d.build_rotor();anchor=d.build_fixed_anchor()
    core=d.x_cylinder(d.CORD_D/2,-39.2,33,d.DRIVE_Y,10.5)
    intersections={name:(core&shape).volume for name,shape in [('frame',frame),('rotor',rotor),('anchor',anchor)]}
    assert max(intersections.values())<1e-5,intersections
    # Conservative wrap boxes exclude the cleats they intentionally touch.
    aw=Pos(-40.2,-6,7.5)*Box(10,4,10)
    rw=Pos(41,-6,10)*Box(10,4,10.4)
    for name,a,b in [('anchor wrap/frame',aw,frame),('anchor wrap/rotor',aw,rotor),('anchor wrap/left wheel',aw,d.build_left_drive_wheel()),('right wrap/frame',rw,frame)]:
        intersections[name]=(a&b).volume
        assert intersections[name]<1e-5,(name,intersections[name])
    # Remove only the exact intentional crossbar contact from the reserved wrap.
    crossbar=Pos(41,-6,10)*Box(2,12.2,2.4)
    intersections['right wrap/rotor outside cleat']=((rw-crossbar)&rotor).volume
    assert intersections['right wrap/rotor outside cleat']<1e-5,intersections
    assert anchor.bounding_box().min.Z>=.49
    assert d.BAND_BORE_D-d.CORD_D>=1.4-1e-9
    assert 5.7-1-d.CORD_D>=.7-1e-9
    assert 6-1.2-d.CORD_D>=.8-1e-9
    parts=[frame,rotor,anchor,d.build_left_drive_wheel(),f.build_bill(),f.build_lens()]
    for side in (-1,1):parts.extend([d.build_rear_roller(side),d.build_rear_pin(side)])
    for name in ['head_rim','dark_lens','sensor','neck_skin']:parts.append(getattr(f,'build_'+name)())
    for side in (-1,1):parts.extend([f.build_boot(side),f.build_boot(side,True),f.build_shin_skin(side)])
    # Full-density CAD mass is deliberately used, not unverified slicer infill mass.
    volume=sum(p.volume for p in parts)
    c=[sum(p.volume*tuple(p.center(CenterOf.MASS))[i] for p in parts)/volume for i in range(3)]
    weight=volume*1.24e-6*9.80665
    front=weight*(12-c[1])/18;rear=weight-front
    assert front>0 and rear>0
    L=d.CORD_WORKING_SPAN;theta=2*math.pi*d.MAX_WINDING_TURNS
    J=math.pi*d.CORD_D**4/32
    gamma=d.CORD_D/2*theta/L
    assert gamma<.35
    def E(s):return .0981*(56+7.66*s)/(.137505*(254-2.54*s))
    # Gent hardness correlation is an estimate, not a supplied material modulus.
    moduli=[{'shore_A':s,'estimated_E_MPa':E(s),'estimated_G_MPa':E(s)/3,'estimated_initial_torque_Nmm':E(s)/3*J*theta/L} for s in (55,60,65)]
    low=moduli[0]['estimated_initial_torque_Nmm']*.7 # additional assumed 30% reduction
    high=moduli[-1]['estimated_initial_torque_Nmm']
    # At most 0.5% fitting extension; estimating its thrust friction conservatively.
    tension=moduli[-1]['estimated_E_MPa']*math.pi*d.CORD_D**2/4*.005
    shaft_J=math.pi*(d.AXLE_D**4-d.BAND_BORE_D**4)/32
    flat_wall=d.KEY_FLAT_RADIUS-d.BAND_BORE_D/2
    assert flat_wall>=1.2-1e-9
    shaft_stress=high*(d.AXLE_D/2)/shaft_J
    friction=[]
    for mu in (.03,.05,.10,.15,.20,.25):
        loss=mu*(front*d.AXLE_D/2+rear*1.6*10/6+tension*8)+.01*weight*10
        friction.append({'assumed_journal_and_thrust_mu':mu,'assumed_rolling_coefficient':.01,'loss_torque_Nmm':loss,'initial_margin_Nmm':low-loss,'quasistatic_distance_mm':max(0,1-loss/low)*d.MAX_WINDING_TURNS*2*math.pi*10})
    pitch_torque=weight*min(c[1]+6,12-c[1])
    report={'ok':True,'scope':'geometry and conditional calculation only; no running qualification',
      'source_sha256':{n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ('drive_lib.py','duck_lib.py')},
      'cord':{'supplier':'MVQ Silicones 60 Shore A silicone solid cord, 4.0 mm','cut_length_mm':240,'working_span_mm':L,'maximum_fitting_extension_fraction':.005,'maximum_turns':d.MAX_WINDING_TURNS,'bore_radial_clearance_mm':.7,'surface_shear_strain':gamma,'polar_moment_mm4':J},
      'shaft':{'outside_diameter_mm':d.AXLE_D,'bore_diameter_mm':d.BAND_BORE_D,'minimum_flat_wall_mm':flat_wall,'annular_polar_moment_mm4':shaft_J,'nominal_annular_shear_MPa':shaft_stress,'assumed_20_percent_section_reduction_shear_MPa':shaft_stress/.8,'note':'Annular nominal stress and assumed reduction are screening estimates, not exact D-section warping or printed strength.'},
      'clearance_intersection_mm3':intersections,'estimated_moduli':moduli,'derated_low_torque_Nmm':low,'maximum_estimated_tension_N':tension,
      'uniform_density_com_mm':c,'full_density_mass_kg':weight/9.80665,'normal_loads_N':{'drive':front,'rear':rear},'friction_sensitivity':friction,
      'required_ground_friction_for_high_torque':high/(10*front),'minimum_static_pitch_moment_Nmm':pitch_torque,'high_torque_to_pitch_moment_ratio':high/pitch_torque,
      'ideal_two_turn_distance_mm':d.MAX_WINDING_TURNS*2*math.pi*10,
      'print_transition':{'outer_radial_growth_per_vertical_mm':2/3,'inner_radial_shrink_per_vertical_mm':1,'knob_face_and_crossbar_on_bed_X':42},
      'limitations':['Gent-derived moduli and 30% reduction are modeling assumptions, not measured cord torsion data.','Friction coefficients, hysteresis, knot slip, wear and printed bonds require physical checks.','Computed travel assumes quasi-static rolling on level ground; inertia and lateral drift omitted.','Core and external tie clearance checked; knot shape and local bending/contact stress are not finite-element validated.','Mass includes current appearance solids at uniform PLA density; actual infill and adhesive change mass distribution.']}
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
