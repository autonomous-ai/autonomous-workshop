"""bird_left: sagittal bond plane on the print bed."""
from parts.bird_left import bird_left
PRINTABLE = True

def gen_step():
    return bird_left(print_pose=True)
