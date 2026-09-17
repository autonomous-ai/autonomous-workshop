"""Algebraic mechanism invariants independent of geometry gates."""
import math
import params as p

def validate_parameters():
    assert p.ECCENTRICITY < p.INPUT_ARM
    assert p.CAM_R-p.CAM_BORE/2-p.ECCENTRICITY > 1.2
    assert 0.19 < (p.SHAFT_BORE-p.SHAFT_D)/2 < 0.41
    assert 0.19 < (p.HINGE_BORE-p.HINGE_PIN_D)/2 < 0.41
    assert math.isclose(p.ROD_BASE_Z+p.ROD_LENGTH,p.CROSSHEAD_Z+p.CROSSHEAD_TONGUE_BOUNDS[4],abs_tol=1e-9)
    for i in range(361):
        q=p.ECCENTRICITY*math.sin(math.radians(i))
        phi=math.asin(-q/p.INPUT_ARM)
        pin_x=p.HINGE_X-p.INPUT_ARM*math.cos(phi)
        assert p.SLOT_X0+p.DRIVE_PIN_D/2 <= pin_x <= p.SLOT_X1-p.DRIVE_PIN_D/2
        assert math.isclose(p.HINGE_Z+q+p.DRIVE_PIN_D/2,p.CROSSHEAD_Z+q+p.SLOT_Z+p.SLOT_HEIGHT/2,abs_tol=1e-9)
validate_parameters()
