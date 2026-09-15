"""Cratercade loading receiver: exact handed counterpart of the reset part.

The loading assembly mirrors its receiver across local YZ. Its hinge nut
cages make a repeated reset print unsuitable under the tested180-degree pose.
Supply the actual reflected geometry as a separate printable part.
"""
from build123d import Plane
from parts.access_door import receiver, print_pose

PRINTABLE = True


def gen_step():
    return print_pose(receiver().mirror(Plane.YZ), 'receiver')
