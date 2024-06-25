from typing import Tuple
from star_ray.event import (
    MouseButtonEvent as _MouseButtonEvent,
    MouseMotionEvent as _MouseMotionEvent,
    KeyEvent,
    WindowCloseEvent,
    WindowFocusEvent,
    WindowMoveEvent,
    WindowOpenEvent,
    WindowResizeEvent,
)

__all__ = (
    "MouseButtonEvent",
    "MouseMotionEvent",
    "KeyEvent",
    "WindowCloseEvent",
    "WindowFocusEvent",
    "WindowMoveEvent",
    "WindowOpenEvent",
    "WindowResizeEvent",
)


class MouseButtonEvent(_MouseButtonEvent):

    position_raw: Tuple[float, float] | Tuple[int, int]


class MouseMotionEvent(_MouseMotionEvent):

    position_raw: Tuple[float, float] | Tuple[int, int]
    relative_raw: Tuple[float, float] | Tuple[int, int]
