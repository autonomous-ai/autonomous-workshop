"""Single bonded shell half, maximum elliptical section flat on the print bed."""
from parts.body import body_half
PRINTABLE = True
def gen_step():
    return body_half(7, 'front')
