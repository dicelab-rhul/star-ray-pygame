""" Defines the pygame view that is used to render SVG """
from typing import Any, List, Tuple
from lxml import etree as ET
import numpy as np
import cairosvg
import pygame
import re


class CairoSVGSurface:
    """ A surface implementation that is able to render svg graphics to a pygame window."""

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
        surface_position = (p[0] * self.scaling_factor,
                            p[1] * self.scaling_factor)
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
        array = self._svg_to_npim(
            self._svg_source, background_color=background_color)
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


def parse_transform(transform: str):
    if transform is None:
        return ((1, 1), None, None)
    scale_match = re.search(r"scale\(([^)]+)\)", transform)
    rotation_match = re.search(r"rotate\(([^)]+)\)", transform)
    translate_match = re.search(r"translate\(([^)]+)\)", transform)

    scale = tuple(map(float, scale_match.group(1).split(","))
                  ) if scale_match else None
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
