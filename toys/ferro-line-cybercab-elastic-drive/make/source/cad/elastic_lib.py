"""Purchased round elastic cord: connected installed-envelope approximation.

Not printable geometry; no strain, force, fatigue, run-distance or dynamics proof.
Cord centreline has 12 straight chords per semicircle with spherical joins.
Nominal cord radius is 0.7 mm. Angle is degrees about global +Y.
Backward winding is negative Y; forward release travels from -90 to 0 degrees.
Rear centreline radius5.1 clears the printable winding-finger buttress.
Material deformation/contact and tensioned seating are unqualified.
"""
from math import cos, sin, radians, sqrt, pi
from build123d import Solid, Plane

CORD_R = 0.7
ARC_INTERVALS = 12

def centreline(angle=0.0):
    """Ordered closed centreline vertices, without a repeated final vertex."""
    a = radians(angle)
    ca, sa = cos(a), sin(a)
    def rear(phi):
        # R_y(a)*(5, 5.1*cos(phi), +5.1*sin(phi)) + rear axle centre.
        x, y, z = 5.0, 5.1*cos(phi), 5.1*sin(phi)
        return (34.0+ca*x+sa*z, y, 16.5-sa*x+ca*z)
    points = [rear(pi*i/ARC_INTERVALS) for i in range(ARC_INTERVALS+1)]
    # rear +Y -> rear -Y -> front -Y -> front +Y -> rear +Y.
    points += [(134.0+4.2*cos(-pi/2+pi*i/ARC_INTERVALS),
                4.2*sin(-pi/2+pi*i/ARC_INTERVALS),14.5)
               for i in range(ARC_INTERVALS+1)]
    return points

def envelope_evidence(angle=0.0):
    points = centreline(angle)
    perimeter = sum(sqrt(sum((b[i]-a[i])**2 for i in range(3)))
                    for a,b in zip(points,points[1:]+points[:1]))
    return {'angle_deg':angle,'cord_radius_mm':CORD_R,
            'centreline_chord_perimeter_mm':perimeter,
            'rear_plus_y':points[0],'rear_minus_y':points[ARC_INTERVALS],
            'front_minus_y':points[ARC_INTERVALS+1], 'front_plus_y':points[-1]}

def elastic(angle=0.0):
    """One solid closed cord loop; spheres round each chord junction."""
    points = centreline(angle)
    shapes = [Solid.make_sphere(CORD_R, Plane(origin=p)) for p in points]
    for a,b in zip(points,points[1:]+points[:1]):
        delta = tuple(b[i]-a[i] for i in range(3))
        length = sqrt(sum(v*v for v in delta))
        shapes.append(Solid.make_cylinder(CORD_R,length,Plane(origin=a,z_dir=delta)))
    result = shapes[0].fuse(*shapes[1:]).clean()
    if len(result.solids()) != 1:
        raise ValueError('Elastic envelope must be one connected solid')
    return result
