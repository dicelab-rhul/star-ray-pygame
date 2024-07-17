""" TODO """

# fmt: off # turn of auto-formating, the order of the imports matters!

import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# ======================================================= #
# NOTE: this must appear before importing other modules! (careful! -> auto-format might move it!)
from .utils import _check_libcairo_install

# this will check for install issues with cairo, its a real pain on windows...
_check_libcairo_install()
# ======================================================= #
from star_ray import Environment

from .view import View, WindowConfiguration
from .avatar import Avatar
from .ambient import SVGAmbient


__all__ = (
    "View",
    "Avatar",
    "WindowConfiguration",
    "SVGAmbient",
    "Environment",
    "DEFAULT_SVG",
    "DEFAULT_SVG_NAMESPACES",
)
