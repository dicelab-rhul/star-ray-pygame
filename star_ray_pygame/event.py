from typing import Tuple
from star_ray.event import (
    MouseButtonEvent as _MouseButtonEvent,
    MouseMotionEvent as _MouseMotionEvent,
)

__all__ = ("MouseButtonEvent", "MouseMotionEvent")


class MouseButtonEvent(_MouseButtonEvent):

    position_raw: Tuple[float, float] | Tuple[int, int]


class MouseMotionEvent(_MouseMotionEvent):

    position_raw: Tuple[float, float] | Tuple[int, int]
    relative_raw: Tuple[float, float] | Tuple[int, int]
