"""Manufacturing leaf: left bird; common mirrored feature builder."""
from parts.bird import bird_half

def bird_left(print_pose=False):
    return bird_half(-1, print_pose=print_pose)
