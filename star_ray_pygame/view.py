""" Defines the pygame view that is used to render SVG """

from .event import MouseButtonEvent, MouseMotionEvent
from star_ray.utils import _LOGGER
from star_ray.event import (
    Event,
    KeyEvent,
    WindowCloseEvent,
    WindowOpenEvent,
    WindowResizeEvent,
    WindowMoveEvent,
    WindowFocusEvent,
)
from star_ray.ui import WindowConfiguration
from lxml import etree as ET
from pygame.event import EventType
import pywinctl as pwc  # pylint: disable = E0401
import pygame
import time
import copy
import math
from typing import Any, List, Tuple

from .cairosurface import CairoSVGSurface

# Constant values
PYGAME_KEYDOWN = pygame.KEYDOWN
PYGAME_KEYUP = pygame.KEYUP
PYGAME_QUIT = pygame.QUIT
PYGAME_MOUSEDOWN = pygame.MOUSEBUTTONDOWN
PYGAME_MOUSEUP = pygame.MOUSEBUTTONUP
PYGAME_MOUSEMOTION = pygame.MOUSEMOTION
PYGAME_WINDOWRESIZE = pygame.VIDEORESIZE
PYGAME_WINDOWMOVE = pygame.USEREVENT + 1
PYGAME_WINDOWFOCUS = pygame.USEREVENT + 2
PYGAME_WINDOWOPEN = pygame.USEREVENT + 3
PYGAME_WINDOWCLOSE = PYGAME_QUIT  # Alias for PYGAME_QUIT

PYGAME_LEFTMOUSEBUTTON = 1
PYGAME_MIDDLEMOUSEBUTTON = 2
PYGAME_RIGHTMOUSEBUTTON = 3

MOUSE_BUTTON_MAP = {
    PYGAME_LEFTMOUSEBUTTON: MouseButtonEvent.BUTTON_LEFT,
    PYGAME_MIDDLEMOUSEBUTTON: MouseButtonEvent.BUTTON_MIDDLE,
    PYGAME_RIGHTMOUSEBUTTON: MouseButtonEvent.BUTTON_RIGHT,
}


class View:

    def __init__(
        self, window_config: WindowConfiguration, surface_size: Tuple[int, int] = None
    ):
        pygame.init()  # pylint: disable=no-member
        self._window_config = copy.deepcopy(window_config)
        self._screen_size = get_screen_size()

        flags = 0
        if window_config.resizable:
            # this should be false until we can resize/scale the context...
            flags |= pygame.RESIZABLE  # pylint: disable=no-member
        if window_config.fullscreen:
            # set the window size to be the screen size if full screen
            self._window_config.width = self._screen_size[0]
            self._window_config.height = self._screen_size[1]
            flags |= pygame.FULLSCREEN  # pylint: disable=no-member
        self._window_flags = flags
        self._window = pygame.display.set_mode(
            self.window_size, flags=self._window_flags
        )
        if self._window_config.title:
            pygame.display.set_caption(self._window_config.title)
        if surface_size is None:
            PADDING = 20
            aspect = self.get_window_aspect()
            surface_size = (
                self.window_size[0] - PADDING * aspect,
                self.window_size[1] - PADDING,
            )
        # this is where the svg is rendered. It should be the same size as the svg image
        self._surface = CairoSVGSurface(surface_size)
        self._closed = False
        self._pwc_window = None
        self._pwc_window = self._setup_pwc_window()

        # initial events that are the window position/size
        time.sleep(0.1)  # this is unfortunate...
        window_info = self.get_window_info()
        self._window_resize_callback(window_info["size"])
        self._window_moved_callback(window_info["position"])

    def get_window_info(self):
        return dict(
            title=self._pwc_window.title,
            position=self._pwc_window.position,
            size=self._pwc_window.size,
        )

    def get_window_aspect(self):
        return self.window_size[0] / self.window_size[1]

    def get_screen_info(self):
        return dict(monitor=0, size=self._screen_size)

    def update(self, svg_tree: ET.ElementBase):
        self._surface.update(svg_tree)

    def render(self):
        self._surface.render(self._window)

    def elements_under(self, point: Tuple[float, float], transform: bool = False):
        return self._surface.elements_under(point, transform=transform)

    def pixel_to_svg(self, point: Tuple[float, float]) -> Tuple[float, float]:
        return self._surface.pixel_to_svg(point)

    def svg_to_pixel(self, point: Tuple[float, float]) -> Tuple[float, float]:
        return self._surface.svg_to_pixel(point)

    def pixel_scale_to_svg_scale(
        self, point: Tuple[float, float]
    ) -> Tuple[float, float]:
        return self._surface.pixel_scale_to_svg_scale(point)

    def svg_scale_to_pixel_scale(
        self, point: Tuple[float, float]
    ) -> Tuple[float, float]:
        return self._surface.svg_scale_to_pixel_scale(point)

    def get_events(self) -> List[Event]:
        events = []
        for pg_event in pygame.event.get():
            fun = EVENT_MAP.get(pg_event.type, None)
            if fun:
                try:
                    events.append(fun(self, pg_event))
                except Exception as e:  # pylint: disable=W0718
                    _LOGGER.exception(
                        "Failed to convert `pygame` event: %s  to `star_ray` event as an error occured: %s",
                        pg_event,
                        e,
                    )
        return events

    @property
    def is_open(self):
        return not self._closed

    def close(self):
        self._closed = True
        self._pwc_window.watchdog.stop()
        pygame.quit()  # pylint: disable=no-member

    @property
    def window_config(self):
        return copy.deepcopy(self._window_config)  # read only!

    @property
    def window_size(self):
        return (int(self._window_config.width), int(self._window_config.height))

    @window_size.setter
    def window_size(self, value):
        window_size = (self._window_config.width, self._window_config.height)
        if window_size != value:
            # NOTE: resizing using set_mode will break pywinctl watch dog because a new window is created
            # be careful using pygame.display.set_mode in this class!
            width, height = int(math.ceil(value[0])), int(math.ceil(value[1]))
            self._window = pygame.display.set_mode(
                (width, height), flags=self._window_flags
            )
            # pygame creates a new window... pwc needs to find it again
            self._pwc_window = self._setup_pwc_window()
            self._window_config.width = width
            self._window_config.height = height
            # this doesnt seem to get called during `set_mode` above...
            self._window_resize_callback((width, height))

    def _window_open_callback(self):
        """Callback for when the pygame window is opened for the first time. A custom pygame event is added to the queue internally. The associated event timestamp is not accurate, but the event serves as an indication of when this view is ready to for updating/rendering."""
        pygame.event.post(pygame.event.Event(PYGAME_WINDOWOPEN))

    def _window_focus_callback(self, has_focus):
        """Callback for `pywinctl` when the pygame window losses or gains focus. A custom pygame event is added to the queue internally."""
        pygame.event.post(pygame.event.Event(
            PYGAME_WINDOWFOCUS, has_focus=has_focus))

    def _window_moved_callback(self, position):
        """Callback for `pywinctl` when the pygame window is moved. A custom pygame event is added to the queue internally."""
        pygame.event.post(pygame.event.Event(
            PYGAME_WINDOWMOVE, position=position))

    def _window_resize_callback(self, size):
        """Callback for `pywinctl` when the pygame window is resized. A custom pygame event is added to the queue internally."""
        pygame.event.post(pygame.event.Event(PYGAME_WINDOWRESIZE, size=size))

    def _setup_pwc_window(self):
        """Getter for the `pywinctl` window object. This object is used to watch changes to the pygame window and addresses some pygame limitations."""
        if self._pwc_window:
            self._pwc_window.watchdog.stop()

        title = self._window_config.title
        windows = pwc.getWindowsWithTitle(self._window_config.title)
        if len(windows) == 0:
            raise ValueError(
                f"Failed to get screen info: couldn't find pygame window with title: {title}"
            )
        if len(windows) > 1:
            raise ValueError(
                f"Failed to get screen info: found multiple windows ({len(windows)}) with the same title: {title}"
            )
        pwc_window = windows[0]
        pwc_window.watchdog.start(
            isActiveCB=self._window_focus_callback,
            movedCB=self._window_moved_callback,
            interval=0.05,
        )
        return pwc_window


def get_screen_size():
    screen_sizes = pygame.display.get_desktop_sizes()
    assert len(screen_sizes) == 1  # TODO multiple monitors not supported...
    return screen_sizes[0]


def create_window_move_event_from_pygame_event(
    view: View,
    pygame_event: EventType,
) -> WindowMoveEvent:
    """Creates a `WindowMoveEvent` from a `pygame` window move event."""
    if pygame_event.type != PYGAME_WINDOWMOVE:
        raise ValueError(
            "The provided pygame event is not a `PYGAME_WINDOWMOVE` event."
        )
    return WindowMoveEvent(position=pygame_event.position)


def create_window_focus_event_from_pygame_event(
    view: View,
    pygame_event: EventType,
) -> WindowFocusEvent:
    """Creates a `WindowFocusEvent` from a `pygame` window focus event."""
    if pygame_event.type != PYGAME_WINDOWFOCUS:
        raise ValueError(
            "The provided pygame event is not a `PYGAME_WINDOWFOCUS` event."
        )
    return WindowFocusEvent(has_focus=pygame_event.has_focus)


def create_window_resize_event_from_pygame_event(
    view: View,
    pygame_event: EventType,
) -> WindowResizeEvent:
    """Creates a `WindowResizeEvent` from a `pygame` window resize event."""
    if pygame_event.type != PYGAME_WINDOWRESIZE:
        raise ValueError(
            "The provided pygame event is not a `PYGAME_WINDOWRESIZE` event."
        )
    return WindowResizeEvent(size=tuple(pygame_event.size))


def create_window_close_event_from_pygame_event(
    view: View,
    pygame_event: EventType,
) -> WindowCloseEvent:
    """Creates an `WindowCloseEvent` from a `pygame` window close event."""
    if pygame_event.type != PYGAME_QUIT:
        raise ValueError(
            "The provided pygame event is not a `PYGAME_QUIT` event.")
    return WindowCloseEvent()


def create_window_open_event_from_pygame_event(
    view: View,
    pygame_event: EventType,
) -> WindowOpenEvent:
    """Creates an `WindowOpenEvent` from a `pygame` window open event."""
    if pygame_event.type != PYGAME_WINDOWOPEN:
        raise ValueError(
            "The provided pygame event is not a `PYGAME_WINDOWOPEN` event."
        )
    return WindowOpenEvent()


def create_key_event_from_pygame_event(view: View, pygame_event: EventType) -> KeyEvent:
    """Creates a `KeyEvent` instance from a `pygame` keyboard event."""
    if pygame_event.type not in (PYGAME_KEYDOWN, PYGAME_KEYUP):
        raise ValueError(
            "The provided pygame event is not a `KEYDOWN` or `KEYUP` event."
        )
    status = KeyEvent.DOWN if pygame_event.type == PYGAME_KEYDOWN else KeyEvent.UP
    return KeyEvent(
        key=pygame.key.name(pygame_event.key), keycode=pygame_event.key, status=status
    )


def create_mouse_button_event_from_pygame_event(
    view: View,
    pygame_event: EventType,
) -> MouseButtonEvent:
    """Creates a `MouseButtonEvent` instance from a `pygame` mouse event."""
    if pygame_event.type not in (PYGAME_MOUSEDOWN, PYGAME_MOUSEUP):
        raise ValueError(
            "The provided pygame event is not a `MOUSEDOWN` or `MOUSEUP` event."
        )
    status = (
        MouseButtonEvent.DOWN
        if pygame_event.type == PYGAME_MOUSEDOWN
        else MouseButtonEvent.UP
    )
    position_raw = pygame_event.pos
    position = view.pixel_to_svg(position_raw)
    target = view.elements_under(position, transform=False)

    return MouseButtonEvent(
        button=MOUSE_BUTTON_MAP[pygame_event.button],
        position=position,
        status=status,
        target=target,
        position_raw=position_raw,
    )


def create_mouse_motion_event_from_pygame_event(
    view: View,
    pygame_event: EventType,
) -> MouseMotionEvent:
    """Creates a `MouseMotionEvent` instance from a `pygame` mouse movement event."""
    if pygame_event.type != PYGAME_MOUSEMOTION:
        raise ValueError(
            "The provided pygame event is not a `MOUSEMOTION` event.")

    position_raw = pygame_event.pos
    relative_raw = pygame_event.rel
    position = view.pixel_to_svg(position_raw)
    relative = view.pixel_scale_to_svg_scale(relative_raw)
    target = view.elements_under(position, transform=False)
    return MouseMotionEvent(
        position=position,
        relative=relative,
        position_raw=position_raw,
        relative_raw=relative_raw,
        target=target,
    )


# Dictionary mapping pygame event types to corresponding event creation functions
EVENT_MAP = {
    PYGAME_KEYDOWN: create_key_event_from_pygame_event,
    PYGAME_KEYUP: create_key_event_from_pygame_event,
    PYGAME_QUIT: create_window_close_event_from_pygame_event,
    PYGAME_MOUSEDOWN: create_mouse_button_event_from_pygame_event,
    PYGAME_MOUSEUP: create_mouse_button_event_from_pygame_event,
    PYGAME_MOUSEMOTION: create_mouse_motion_event_from_pygame_event,
    PYGAME_WINDOWRESIZE: create_window_resize_event_from_pygame_event,
    PYGAME_WINDOWMOVE: create_window_move_event_from_pygame_event,
    PYGAME_WINDOWFOCUS: create_window_focus_event_from_pygame_event,
}
