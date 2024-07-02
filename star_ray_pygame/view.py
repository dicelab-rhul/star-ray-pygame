""" Defines the pygame view that is used to render SVG """

from .utils import _check_libcairo_install
_check_libcairo_install() # this will check for install issues with cairo, its a real pain on windows...

# pylint: disable=E1101
from typing import Any, List, Tuple
import math
import copy
import re
import time
import pygame
import cairosvg
import numpy as np
import pywinctl as pwc  # pylint: disable = E0401

from pygame.event import EventType
from lxml import etree as ET
from star_ray.ui import WindowConfiguration

from star_ray.event import (
    Event,
    KeyEvent,
    WindowCloseEvent,
    WindowOpenEvent,
    WindowResizeEvent,
    WindowMoveEvent,
    WindowFocusEvent,
)
from star_ray.utils import _LOGGER

from .event import MouseButtonEvent, MouseMotionEvent


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


class CairoSVGSurface:

    def __init__(self, surface_size: Tuple[int, int]):
        super().__init__()
        self._svg_source = """<svg xmlns="http://www.w3.org/2000/svg"></svg>"""
        self._svg_tree = ET.fromstring(self._svg_source)
        self._surface = pygame.Surface(surface_size)
        # position defined in the svg, this is NOT in pixels but in svg coordinates
        self._svg_position = (0, 0)
        # size defined in the svg, this is NOT in pixels but in svg coordinates
        self._svg_size = (0, 0)
        # the scaling factor (maintaining aspect ratio) of the svg to ensure it fits in the surface
        self._scaling_factor = 1.0
        # pixel offset when rendering the svg to the surface, this is needed because
        # the svg is automatically centered in the surface during the render
        self._surface_offset = (0, 0)
        # size of the pygame window (or surface) we are rendering to
        self._window_size = (0, 0)

    def update(self, svg_tree: ET.ElementBase):
        self._svg_tree = svg_tree
        # svg element must be at the root
        assert self._svg_tree.tag.endswith("svg")
        # the svg size MUST be defined...
        self._svg_size = (
            int(self._svg_tree.get("width")),
            int(self._svg_tree.get("height")),
        )
        self._svg_position = (
            int(self._svg_tree.get("x", 0)),
            int(self._svg_tree.get("y", 0)),
        )
        # convert the svg tree to its source string so that Cairo can render it
        self._svg_source = ET.tostring(
            self._svg_tree, method="c14n2", with_comments=False
        )

    @property
    def svg_size(self):
        return self._svg_size

    @property
    def surface_position(self):
        # compute the surface position based on svg position and scaling factor
        p = self._svg_position
        surface_position = (p[0] * self.scaling_factor, p[1] * self.scaling_factor)
        # center the surface in the window
        surface_size = self.surface_size
        window_size = self._window_size
        centering_offset = (
            (window_size[0] - surface_size[0]) / 2,
            (window_size[1] - surface_size[1]) / 2,
        )
        return (
            centering_offset[0] + surface_position[0],
            centering_offset[1] + surface_position[1],
        )

    @property
    def surface_size(self):
        return self._surface.get_size()

    @property
    def scaling_factor(self):
        return self._scaling_factor

    def pixel_to_svg(self, point: Tuple[float, float]) -> Tuple[float, float]:
        """Transforms a point from pixel space to svg space."""
        spos = self.surface_position
        sfac = self.scaling_factor
        return (
            (point[0] - self._surface_offset[0] - spos[0]) / sfac,
            (point[1] - self._surface_offset[1] - spos[1]) / sfac,
        )

    def pixel_scale_to_svg_scale(
        self, point: Tuple[float, float]
    ) -> Tuple[float, float]:
        """Scales a point from pixel space to svg space (ignores any other transformations)."""
        sfac = self.scaling_factor
        return (point[0] * sfac, point[1] * sfac)

    def svg_to_pixel(self, point: Tuple[float, float]) -> Tuple[float, float]:
        raise NotImplementedError()  # TODO

    def svg_scale_to_pixel_scale(
        self, point: Tuple[float, float]
    ) -> Tuple[float, float]:
        raise NotImplementedError()  # TODO

    def render(self, window: pygame.Surface, background_color="#ffffff"):
        # center the svg in the window
        self._window_size = window.get_size()
        array = self._svg_to_npim(self._svg_source, background_color=background_color)
        pygame.surfarray.blit_array(self._surface, array)
        window.fill(background_color)
        window.blit(self._surface, self.surface_position)
        pygame.display.flip()

    def _surface_to_npim(self, surface: cairosvg.surface.PNGSurface):
        """Transforms a Cairo surface into a numpy array."""
        # a copy must be made to avoid a seg fault if the backing array disappears... (not sure why this happens!)
        surface = surface.cairo
        H, W = surface.get_height(), surface.get_width()
        im = np.frombuffer(surface.get_data(), np.uint8)
        im.shape = (H, W, 4)  # for RGBA
        im = im[:, :, :3].transpose(1, 0, 2)[:, :, ::-1].copy()
        return im

    def _svg_to_npim(self, svg_bytestring, dpi=96, background_color="#ffffff"):
        """Renders a svg bytestring as a RGB image in a numpy array"""
        tree = cairosvg.parser.Tree(bytestring=svg_bytestring)
        output_size = self.surface_size
        # this will render to the surface while maintaining the aspect ratio - cool!
        # to compute true window position we need to manaully compute this new position/size of the svg image
        # note that the top-level svg position (x and y attributes) are ignored when rendering, we need to handle this ourselves
        surf = cairosvg.surface.PNGSurface(
            tree,
            None,
            dpi=dpi,
            background_color=background_color,
            output_width=output_size[0],
            output_height=output_size[1],
        )
        # compute the scaling factor this is computed in when rendering the svg above
        # we need to manually compute it here to to be able to transform points to
        # svg space and position the canvas surface
        svg_size, sur_size = self.svg_size, self.surface_size
        scaling_factor_width = sur_size[0] / svg_size[0]
        scaling_factor_height = sur_size[1] / svg_size[1]
        # TODO we are going to want to center the image aswell..
        self._scaling_factor = min(scaling_factor_width, scaling_factor_height)

        # the aspect ratio is maintained, but the image is always centered in the output surface,
        # we need to compute this centering manually to be able to reconstruct the svg coordinate transform
        self._surface_offset = (
            (sur_size[0] - (svg_size[0] * self._scaling_factor)) / 2,
            (sur_size[1] - (svg_size[1] * self._scaling_factor)) / 2,
        )
        # surf.finish()
        return self._surface_to_npim(surf)

    def elements_under(
        self, point: Tuple[float, float], transform: bool = False
    ) -> List[str]:
        """Gets all svg elements ids that are under the given `point`.

        Args:
            point (Tuple[float, float]): to check under
            transform (bool, optional): whether to transform the given `point` to svg space. Defaults to False.

        Returns:
            List[str]: list of element ids that are under the `point`.
        """
        if transform:
            point = self.pixel_to_svg(point)
        return elements_under(self._svg_tree, point)


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
        pygame.event.post(pygame.event.Event(PYGAME_WINDOWFOCUS, has_focus=has_focus))

    def _window_moved_callback(self, position):
        """Callback for `pywinctl` when the pygame window is moved. A custom pygame event is added to the queue internally."""
        pygame.event.post(pygame.event.Event(PYGAME_WINDOWMOVE, position=position))

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


def point_in_rect(rect, point):
    """Determine if a point is inside a rectangle."""
    try:
        x, y = point
        rx, ry, width, height = [
            float(rect.get(attr)) for attr in ("x", "y", "width", "height")
        ]
    except ValueError as e:
        missing = [
            attr for attr in ("x", "y", "width", "height") if not attr in rect.attrib
        ]
        raise ValueError(
            f"Missing required attributes {missing} on rect: '{rect.get('id', '<MISSING ID>')}'"
        ) from e
    return rx <= x <= rx + width and ry <= y <= ry + height, point


def point_in_circle(circle, point):
    """Determine if a point is inside a circle."""
    x, y = point
    cx, cy, r = [float(circle.get(attr)) for attr in ("cx", "cy", "r")]
    return ((x - cx) ** 2 + (y - cy) ** 2) <= r**2, point


# def apply_viewbox_transform(point, viewBox, svg_size):
#     """Apply viewBox transformation to a point."""
#     if not viewBox:
#         return point  # No transformation needed

#     vb_x, vb_y, vb_width, vb_height = [float(v) for v in viewBox.split()]
#     svg_width, svg_height = svg_size

#     # Simple proportional scaling based on width and height
#     x = (point[0] / svg_width) * vb_width + vb_x
#     y = (point[1] / svg_height) * vb_height + vb_y

#     return x, y


# def apply_inverse_viewbox_transform(transformed_point, viewBox, svg_size):
#     """Apply inverse viewBox transformation to a point."""
#     if not viewBox:
#         return transformed_point  # No transformation needed

#     vb_x, vb_y, vb_width, vb_height = [float(v) for v in viewBox.split()]
#     svg_width, svg_height = svg_size

#     # Inverse proportional scaling and translation
#     x = (transformed_point[0] - vb_x) * (svg_width / vb_width)
#     y = (transformed_point[1] - vb_y) * (svg_height / vb_height)

#     return x, y


def parse_transform(transform: str):
    if transform is None:
        return ((1, 1), None, None)
    scale_match = re.search(r"scale\(([^)]+)\)", transform)
    rotation_match = re.search(r"rotate\(([^)]+)\)", transform)
    translate_match = re.search(r"translate\(([^)]+)\)", transform)

    scale = tuple(map(float, scale_match.group(1).split(","))) if scale_match else None
    rotation = (
        tuple(map(float, rotation_match.group(1).split(",")))
        if rotation_match
        else None
    )
    translate = (
        tuple(map(float, translate_match.group(1).split(",")))
        if translate_match
        else None
    )
    scale = scale if scale else (1.0, 1.0)
    if len(scale) == 1:
        scale = (scale[0], scale[0])
    # TODO rotate
    # if len(rotation) == 1:
    #    return (rotation, 0.0, 0.0)
    # TODO translate
    return scale, rotation, translate


def in_svg(node, point):
    x = node.get("x", None)
    y = node.get("y", None)
    width = node.get("width", None)
    height = node.get("height", None)
    scale, rotation, translate = parse_transform(node.get("transform", None))
    assert rotation is None  # not yet supported
    assert translate is None  # not yet supported
    point = list(point)
    isin = True
    if not x is None:
        point[0] -= float(x)
        point[0] /= scale[0]
        isin &= point[0] >= 0.0
        if not width is None:
            isin &= point[0] <= float(width)
    if not y is None:
        point[1] -= float(y)
        point[1] /= scale[1]
        isin &= point[1] >= 0.0
        if not height is None:
            isin &= point[1] <= float(height)
    return isin, point


def in_group(node, point):
    assert node.get("transform", None) is None  # not supported
    return True, point


def elements_under(node, point: Tuple[float, float]):
    SUPPORTED_SHAPES = {
        "{http://www.w3.org/2000/svg}svg": in_svg,
        "{http://www.w3.org/2000/svg}g": in_group,
        "{http://www.w3.org/2000/svg}rect": point_in_rect,
        "{http://www.w3.org/2000/svg}circle": point_in_circle,
    }
    if not node.tag in SUPPORTED_SHAPES:
        # _LOGGER.warn(f"encountered unsupported shape: %s", node.tag)
        return []
    node_id = node.get("id", None)
    # check if we are
    isin, tpoint = SUPPORTED_SHAPES[node.tag](node, point)
    if isin:
        result = [node_id] if node_id else []
        for child in node:
            result.extend(elements_under(child, tpoint))
        return result
    return []


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
        raise ValueError("The provided pygame event is not a `PYGAME_QUIT` event.")
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
        raise ValueError("The provided pygame event is not a `MOUSEMOTION` event.")

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
