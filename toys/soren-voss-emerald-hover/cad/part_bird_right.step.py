"""bird_right: sagittal bond plane on the print bed."""
from parts.bird_right import bird_right
PRINTABLE = True

def gen_step():
    return bird_right(print_pose=True)
