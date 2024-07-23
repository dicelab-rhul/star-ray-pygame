"""Module defining all user input event types and other userful event types such as XML query primitives. Many are collected from `star_ray` and exposed here. Notably the `MouseButtonEvent` and `MouseMotionEvent` have been redefined with additional fields. See these classes for details."""

from star_ray.event import (
    Event,
    MouseButtonEvent as _MouseButtonEvent,
    MouseMotionEvent as _MouseMotionEvent,
    KeyEvent,
    WindowCloseEvent,
    WindowFocusEvent,
    WindowMoveEvent,
    WindowOpenEvent,
    WindowResizeEvent,
    ScreenSizeEvent,
)
from star_ray_xml import XMLQuery, XPathQuery, Update, Select, Insert, Delete, Replace


class MouseButtonEvent(_MouseButtonEvent):
    """An extension of the original `star_ray.event.MouseButtonEvent` which now operates in SVG space by default. The raw (pixel) position is instead stored in the `position_raw` field."""

    position_raw: tuple[float, float] | tuple[int, int]


class MouseMotionEvent(_MouseMotionEvent):
    """An extension of the original `star_ray.event.MouseMotionEvent` which now operates in SVG space by default. The raw (pixel) position is instead stored in the `position_raw` field, and similarly for the relative position in `relative_raw`."""

    position_raw: tuple[float, float] | tuple[int, int]
    relative_raw: tuple[float, float] | tuple[int, int]


MouseEvent = MouseButtonEvent | MouseMotionEvent
WindowEvent = (
    WindowCloseEvent
    | WindowOpenEvent
    | WindowFocusEvent
    | WindowMoveEvent
    | WindowResizeEvent
)
UserInputEvent = MouseEvent | KeyEvent | WindowEvent

__all__ = (
    "Event",
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
    "ScreenSizeEvent",
    "XMLQuery",
    "XPathQuery",
    "Update",
    "Select",
    "Insert",
    "Delete",
    "Replace",
)
