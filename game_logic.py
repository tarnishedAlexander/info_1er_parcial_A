import math
import arcade
from dataclasses import dataclass
from logging import getLogger

logger = getLogger(__name__)


@dataclass
class ImpulseVector:
    angle: float
    impulse: float


@dataclass
class Point2D:
    x: float = 0
    y: float = 0


def get_angle_radians(point_a: Point2D, point_b: Point2D) -> float:
    ### ---------------------- ###
    ### SU IMPLEMENTACION AQUI ###
    ### ---------------------- ###
    dx = point_b.x - point_a.x
    dy = point_b.y - point_a.y
    return math.atan2(dy, dx)


def get_distance(point_a: Point2D, point_b: Point2D) -> float:
    ### ---------------------- ###
    ### SU IMPLEMENTACION AQUI ###
    ### ---------------------- ###
    dx = point_b.x - point_a.x
    dy = point_b.y - point_a.y
    return math.sqrt(dx * dx + dy * dy)


def get_impulse_vector(start_point: Point2D, end_point: Point2D) -> ImpulseVector:
    ### ---------------------- ###
    ### SU IMPLEMENTACION AQUI ###
    ### ---------------------- ###
    angle = get_angle_radians(start_point, end_point)
    # Reverse the direction by adding π (180 degrees) for slingshot effect
    opposite_angle = angle + math.pi
    impulse = get_distance(start_point, end_point)
    return ImpulseVector(opposite_angle, impulse)