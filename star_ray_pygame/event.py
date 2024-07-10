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
from star_ray_xml import XMLQuery, XPathQuery, Update, Select, Insert, Delete, Replace


class MouseButtonEvent(_MouseButtonEvent):

    position_raw: Tuple[float, float] | Tuple[int, int]


class MouseMotionEvent(_MouseMotionEvent):

    position_raw: Tuple[float, float] | Tuple[int, int]
    relative_raw: Tuple[float, float] | Tuple[int, int]


MouseEvent = MouseButtonEvent | MouseMotionEvent
WindowEvent = WindowCloseEvent | WindowOpenEvent | WindowFocusEvent | WindowMoveEvent | WindowResizeEvent
UserInputEvent = MouseEvent | KeyEvent | WindowEvent

__all__ = (
    "UserInputEvent",
    "MouseEvent",
    "WindowEvent",
    "MouseButtonEvent",
    "MouseMotionEvent",
    "KeyEvent",
    "WindowCloseEvent",
    "WindowFocusEvent",
    "WindowMoveEvent",
    "WindowOpenEvent",
    "WindowResizeEvent",
    "XMLQuery",
    "XPathQuery",
    "Update",
    "Select",
    "Insert",
    "Delete",
    "Replace",
)
