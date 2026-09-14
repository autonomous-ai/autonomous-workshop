"""Continuous rectangular-section band on a one- or two-lap stadium route.

This is nominal deformed geometry, not a spring/elasticity model. A double lap
is one closed (2,1) route. Radial and vertical wobble separate the two strands;
there are no disconnected rings or hidden joining solids. Root owns dimensions
and physical-material qualification; every dimensional input is explicit.
"""
from math import cos, hypot, pi, sin
from build123d import Face, Vector, Wire, loft


def _stadium_station(fixed, moving, radius, fraction):
    dx, dy = moving[0]-fixed[0], moving[1]-fixed[1]
    distance = hypot(dx, dy)
    if distance <= 0 or radius <= 0:
        raise ValueError("Stadium needs separated posts and a positive radius")
    e = Vector(dx/distance, dy/distance, 0)
    n = Vector(-e.Y, e.X, 0)
    f, m = Vector(*fixed, 0), Vector(*moving, 0)
    length = 2*distance+2*pi*radius
    s = (fraction % 1.0)*length
    if s < distance:
        center, normal = f+e*s+n*radius, n
    elif s < distance+pi*radius:
        theta = (s-distance)/radius
        normal = n*cos(theta)+e*sin(theta)
        center = m+normal*radius
    elif s < 2*distance+pi*radius:
        center, normal = m-e*(s-distance-pi*radius)-n*radius, -n
    else:
        theta = (s-2*distance-pi*radius)/radius
        normal = -n*cos(theta)-e*sin(theta)
        center = f+normal*radius
    return center, normal, length


def section(fixed, moving, radius, thickness, width, center_z, turns,
            radial_wobble, axial_wobble, fraction):
    """Exact radial × axial rectangle, with no orientation inferred by a sweep."""
    u = 2*pi*fraction
    center, normal, _ = _stadium_station(fixed,moving,radius,turns*fraction)
    center += normal*(radial_wobble*cos(u))
    center += Vector(0,0,center_z+axial_wobble*sin(u))
    dr, dz = normal*(thickness/2), Vector(0,0,width/2)
    corners = [center-dr-dz, center+dr-dz, center+dr+dz, center-dr+dz]
    return Face(Wire.make_polygon(corners,close=True))


def band(fixed, moving, radius, thickness, width, center_z, turns,
         radial_wobble, axial_wobble, samples_per_lap=128):
    """One closed solid, supplied post positions, and explicitly supplied sizes.

    Ruled sections preserve the declared physical radial/vertical cross-section.
    More sections refine the post arcs; root must check the final chosen count.
    A single turn uses zero wobble. Two turns require a separated (2,1) route.
    """
    if turns not in (1,2):
        raise ValueError("Only the qualified single and double routes are supported")
    if thickness <= 0 or width <= 0:
        raise ValueError("Band section must have positive dimensions")
    if turns == 1 and (radial_wobble != 0 or axial_wobble != 0):
        raise ValueError("Single-lap route uses zero wobble")
    if turns == 2 and radial_wobble <= 0:
        raise ValueError("Double route needs radial separation as well as height")
    count = int(samples_per_lap)*turns
    sections = [section(fixed,moving,radius,thickness,width,center_z,turns,
                        radial_wobble,axial_wobble,i/count) for i in range(count)]
    sections.append(sections[0])
    shape = loft(sections,ruled=True)
    shape.label = f"continuous_rubber_band_{turns}_turn"
    if len(shape.solids()) != 1 or not shape.is_valid or shape.volume <= 0:
        raise ValueError("Band did not produce one valid positive-volume solid")
    return shape


def route_length(fixed,moving,radius,center_z,turns,radial_wobble,
                 axial_wobble,samples=4096):
    """Numerical length of this modeled deformed centerline, not material strain."""
    points = []
    for i in range(samples+1):
        fraction = i/samples
        center, normal, _ = _stadium_station(fixed,moving,radius,turns*fraction)
        u = 2*pi*fraction
        points.append(center+normal*(radial_wobble*cos(u))+
                      Vector(0,0,center_z+axial_wobble*sin(u)))
    return sum((points[i+1]-points[i]).length for i in range(samples))
