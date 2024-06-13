""" This package defines the PygameSVGEngine class. """

from typing import List, Tuple
import math
import copy
import asyncio
import re
import pygame
import cairosvg
import numpy as np
import pywinctl as pwc  # pylint: disable = E0401

from lxml import etree as ET
from star_ray.ui import WindowConfiguration
from star_ray import Event
from star_ray.utils import _LOGGER


from .event import EVENT_MAP, PYGAME_WINDOWFOCUS, PYGAME_WINDOWMOVE, PYGAME_WINDOWOPEN


class View:

    def __init__(self, window_config: WindowConfiguration):
        pygame.init()  # pylint: disable=no-member
        self._window_config = window_config
        flags = 0
        if window_config.resizable:
            # this should be false until we can resize/scale the context...
            flags |= pygame.RESIZABLE  # pylint: disable=no-member
        if window_config.fullscreen:
            flags |= pygame.FULLSCREEN  # pylint: disable=no-member
        print("initial window_size:", self.window_size)
        self._window = pygame.display.set_mode(self.window_size, flags=flags)
        self._window_flags = flags
        if self._window_config.title:
            pygame.display.set_caption(self._window_config.title)
        self._surface = pygame.Surface(self.window_size)  # surface used to render
        self._root = None  # root of the svg tree
        self._source = None  # source of the svg (required by cairosvg unfortunately)
        self._closed = False
        screen_info = pygame.display.get_desktop_sizes()
        assert len(screen_info) == 1  # TODO multiple monitors not supported...
        self._screen_size = screen_info[0]
        self._pwc_window = None
        self._pwc_window = self._setup_pwc_window()

    def get_window_info(self):
        # sanity check...
        # pygame_size = (self._window.get_width(), self._window.get_height())
        return dict(
            title=self._pwc_window.title,
            position=self._pwc_window.position,
            size=self._pwc_window.size,
        )

    def get_screen_info(self):
        return dict(monitor=0, size=self._screen_size)

    def update(self, svg_tree: ET.ElementBase):
        self._root = svg_tree
        # svg element should be at the root...
        assert self._root.tag.endswith("svg")
        # TODO support scaling of the svg to fit the window
        window_size = (float(self._root.get("width")), float(self._root.get("height")))
        # TODO this is not required... we need to implement window resizing carefully
        self.window_size = window_size  # this just resizes to fit the root svg size
        self._source = ET.tostring(self._root, method="c14n2", with_comments=False)

    def render(self):
        # self._window.fill(self._window_config.background_color)
        array = self._svg_to_npim(self._source)
        pygame.surfarray.blit_array(self._surface, array)
        self._window.blit(self._surface, (0, 0))
        pygame.display.flip()

    def elements_under(self, point: Tuple[float, float]):
        return elements_under(self._root, point)

    def get_events(self) -> List[Event]:
        events = []
        for pg_event in pygame.event.get():
            fun = EVENT_MAP.get(pg_event.type, None)
            if fun:
                event = fun(pg_event)
                # TODO this is temporary, it should be done in `fun` when creating the event, fun should contain an argument that is this `View`
                try:
                    if hasattr(event, "target"):
                        event.target = self.elements_under(event.position)
                except Exception as e:
                    _LOGGER.exception(
                        "Failed to find targets for event: %s as an error occured: %s",
                        event,
                        e,
                    )
                events.append(event)
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
            self._window = pygame.display.set_mode((width, height))
            # pygame creates a new window... pwc needs to find it again
            self._pwc_window = self._setup_pwc_window()
            self._window_config.width = width
            self._window_config.height = height
            self._surface = pygame.Surface((width, height))

    def _window_open_callback(self):
        """Callback for when the pygame window is opened for the first time. A custom pygame event is added to the queue internally.
        The associated event timestamp is not accurate, but the event serves as an indication of when this view is ready to for updating/rendering.
        """
        pygame.event.post(pygame.event.Event(PYGAME_WINDOWOPEN))

    def _window_focus_callback(self, has_focus):
        """Callback for `pywinctl` when the pygame window losses or gains focus. A custom pygame event is added to the queue internally."""
        pygame.event.post(pygame.event.Event(PYGAME_WINDOWFOCUS, has_focus=has_focus))

    def _window_moved_callback(self, position):
        """Callback for `pywinctl` when the pygame window is moved. A custom pygame event is added to the queue internally."""
        pygame.event.post(pygame.event.Event(PYGAME_WINDOWMOVE, position=position))

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

    def _surface_to_npim(self, surface):
        """Transforms a Cairo surface into a numpy array."""
        im = np.frombuffer(surface.get_data(), np.uint8)
        H, W = surface.get_height(), surface.get_width()
        im.shape = (H, W, 4)  # for RGBA
        # a copy must be made to avoid a seg fault if the backing array disappears... (not sure why this happens!)
        im = im[:, :, :3].transpose(1, 0, 2)[:, :, ::-1].copy()
        return im

    def _svg_to_npim(self, svg_bytestring, dpi=100):
        """Renders a svg bytestring as a RGB image in a numpy array"""
        tree = cairosvg.parser.Tree(bytestring=svg_bytestring)
        surf = cairosvg.surface.PNGSurface(
            tree, None, dpi, background_color=self.window_config.background_color
        ).cairo
        return self._surface_to_npim(surf)


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
