"""Module that defines the backend for svg rendering to a pygame surface. This relies on the cairosvg package."""

from lxml import etree as ET
import numpy as np
import cairosvg
import pygame
import re


class CairoSVGSurface:
    """A surface implementation that is able to render svg graphics to a pygame window."""

    def __init__(self, surface_size: tuple[int, int], _debug: bool = False):
        """Constructor.

        Args:
            surface_size (tuple[int,int]) : size of the render surface.
            _debug (bool, optional): whether to enable debug mode, this will render debug information to the UI. Defaults to False.
        """
        super().__init__()
        self._svg_source = """<svg xmlns="http://www.w3.org/2000/svg"></svg>"""
        self._svg_tree = ET.fromstring(self._svg_source)
        self._surface = pygame.Surface(surface_size)
        self._debug = _debug
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
        """Update internal svg data.

        Args:
            svg_tree (ET.ElementBase): root of the svg tree
        """
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
    def svg_size(self) -> tuple[float, float]:
        """Getter for the size of the root svg element (svg coordinates).

        Returns:
            tuple[float,float]: root svg element size
        """
        return self._svg_size

    @property
    def surface_position(self) -> tuple[float, float]:
        """Getter for the position of the surface in the window, this is used to place the surface in the window.

        Returns:
            tuple[float, float]: surface position in the window.
        """
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
    def surface_size(self) -> tuple[int, int]:
        """Getter for the size of the render surface (in pixels).

        Returns:
            tuple[int, int]: size of the render surface.
        """
        return self._surface.get_size()

    @property
    def scaling_factor(self) -> float:
        """Getter for the scaling factor (maintaining aspect ratio) of the svg to ensure it fits in the render surface.

        Returns:
            float: scaling factor
        """
        return self._scaling_factor

    def pixel_to_svg(self, point: tuple[float, float]) -> tuple[float, float]:
        """Transforms a point from pixel space to svg space.

        Args:
            point (tuple[float, float]): to transform

        Returns:
            tuple[float, float]: transformed point
        """
        spos = self.surface_position
        sfac = self.scaling_factor
        return (
            (point[0] - self._surface_offset[0] - spos[0]) / sfac,
            (point[1] - self._surface_offset[1] - spos[1]) / sfac,
        )

    def pixel_scale_to_svg_scale(
        self, point: tuple[float, float]
    ) -> tuple[float, float]:
        """Scale a point (typically a (width, height) pair or similar) that lies in pixel space to svg space. Only scaling is applied.

        Args:
            point (tuple[float, float]): point to scale

        Returns:
            tuple[float, float]: scaled point
        """
        sfac = self.scaling_factor
        return (point[0] * sfac, point[1] * sfac)

    def svg_to_pixel(self, point: tuple[float, float]) -> tuple[float, float]:
        """Transform a point from svg space to pixel space.

        Args:
            point (tuple[float, float]): to transform

        Returns:
            tuple[float, float]: transformed point
        """
        raise NotImplementedError()  # TODO

    def svg_scale_to_pixel_scale(
        self, point: tuple[float, float]
    ) -> tuple[float, float]:
        """Scale a point (typically a (width, height) pair or similar) that lies in svg space to pixel space. Only scaling is applied.

        Args:
            point (tuple[float, float]): point to scale

        Returns:
            tuple[float, float]: scaled point
        """
        raise NotImplementedError()  # TODO

    def render(self, window: pygame.Surface, background_color="#ffffff"):
        """Render the svg to the pygame surface `window`.

        Args:
            window (pygame.Surface): pygame surface
            background_color (str, optional): background color. Defaults to white.
        """
        # center the svg in the window
        self._window_size = window.get_size()
        array = self._svg_to_npim(self._svg_source, background_color=background_color)
        pygame.surfarray.blit_array(self._surface, array)
        window.fill(background_color)
        window.blit(self._surface, self.surface_position)
        pygame.display.flip()

    def render_to_array(self, size: tuple[int, int]) -> np.ndarray:
        """Render this cairo surface directly to a numpy array of the given size. `size` serves the role of the window size in the usual rendering process, it is assumed to be >= to the svg surface size.

        Args:
            size (tuple[int, int]): array size to render to (>= svg surface size).

        Returns:
            np.ndarray: the resulting array in WHC (uint8) format
        """
        self._window_size = size
        result = np.full((*self._window_size, 3), 255, dtype=np.uint8)
        array = self._svg_to_npim(self._svg_source, background_color="#ffffff")
        x, y = int(self.surface_position[0]), int(self.surface_position[1])
        result[
            x : x + array.shape[0],
            y : y + array.shape[1],
            :,
        ] = array
        return result

    def _surface_to_npim(self, surface: cairosvg.surface.PNGSurface):
        """Transforms a Cairo `surface` into a numpy array."""
        # a copy must be made to avoid a seg fault if the backing array disappears... (not sure why this happens!)
        surface = surface.cairo
        H, W = surface.get_height(), surface.get_width()
        im = np.frombuffer(surface.get_data(), np.uint8)
        im.shape = (H, W, 4)  # for RGBA
        im = im[:, :, :3].transpose(1, 0, 2)[:, :, ::-1].copy()
        return im

    def _svg_to_npim(self, svg_bytestring, dpi=96, background_color="#ffffff"):
        """Renders a svg bytestring as a RGB image in a numpy array."""
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
        # compute the scaling factor this is computed when rendering the svg above
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
        self, point: tuple[float, float], transform: bool = False
    ) -> list[str]:
        """Gets all svg element `id`s that are under the given `point`.

        Args:
            point (Tuple[float, float]): to check under, expected svg space unless `transform=True` in which case window space (pixels) is expected.
            transform (bool, optional): whether to transform the given `point` to svg space. Defaults to False.

        Returns:
            List[str]: list of element ids that are under the `point`.
        """
        if transform:
            point = self.pixel_to_svg(point)
        return elements_under(self._svg_tree, point)


def point_in_rect(rect, point):
    """Determine if a point is inside a rectangle."""
    try:
        x, y = point
        rx, ry, width, height = (
            float(rect.get(attr)) for attr in ("x", "y", "width", "height")
        )
    except ValueError as e:
        missing = [
            attr for attr in ("x", "y", "width", "height") if attr not in rect.attrib
        ]
        raise ValueError(
            f"Missing required attributes {missing} on rect: '{rect.get('id', '<MISSING ID>')}'"
        ) from e
    return rx <= x <= rx + width and ry <= y <= ry + height, point


def point_in_circle(circle, point):
    """Determine if a point is inside a circle."""
    x, y = point
    cx, cy, r = (float(circle.get(attr)) for attr in ("cx", "cy", "r"))
    return ((x - cx) ** 2 + (y - cy) ** 2) <= r**2, point


def parse_transform(transform: str) -> tuple[float, float, tuple[float, float]]:
    """Parses an svg `transform` attribute extracting the `scale`, `rotation` and `translation`."""
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


def in_svg(node: ET.ElementBase, point: tuple[float, float]):
    """Checks if the point is in the bounds of the svg element `node` and returns this aswell as the point transformed to the nodes coordinate space."""
    x = node.get("x", None)
    y = node.get("y", None)
    width = node.get("width", None)
    height = node.get("height", None)
    scale, rotation, translate = parse_transform(node.get("transform", None))
    assert rotation is None  # not yet supported
    assert translate is None  # not yet supported
    point = list(point)
    isin = True
    if x is not None:
        point[0] -= float(x)
        point[0] /= scale[0]
        isin &= point[0] >= 0.0
        if width is not None:
            isin &= point[0] <= float(width)
    if y is not None:
        point[1] -= float(y)
        point[1] /= scale[1]
        isin &= point[1] >= 0.0
        if height is not None:
            isin &= point[1] <= float(height)
    return isin, point


def in_group(node: ET.ElementBase, point: tuple[float, float]):
    """Checks if the point is in the bounds of the `group` element and returns this aswell as the point transformed to the nodes coordinate space."""
    assert node.get("transform", None) is None  # not supported
    return True, point


def elements_under(node: ET.ElementBase, point: tuple[float, float]):
    """Gets all svg elements ids that are under the given `point`. Note that not all svg transformation are supported.

    Args:
        node: the SVG element to check.
        point (Tuple[float, float]): to check under

    Returns:
        List[str]: list of element ids that are under the `point`.
    """
    SUPPORTED_SHAPES = {
        "{http://www.w3.org/2000/svg}svg": in_svg,
        "{http://www.w3.org/2000/svg}g": in_group,
        "{http://www.w3.org/2000/svg}rect": point_in_rect,
        "{http://www.w3.org/2000/svg}circle": point_in_circle,
    }
    if node.tag not in SUPPORTED_SHAPES:
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
