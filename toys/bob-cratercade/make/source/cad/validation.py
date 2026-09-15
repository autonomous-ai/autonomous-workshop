"""Parameter preconditions; exported-geometry gates supply actual proof."""
import params as p

def validate_parameters():
    assert p.MARBLE_MIN_D <= p.MARBLE_D <= p.MARBLE_MAX_D
    assert p.M4_BORE > p.M4_D
    assert p.NUT_POCKET_AF > p.NUT_AF
    assert p.RAMP_INNER_W > p.MARBLE_MAX_D
    assert -45 < p.JACKPOT_TRAVEL_DEG < 0
