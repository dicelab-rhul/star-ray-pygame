"""The `star_ray_pygame` package is an extension of [`star_ray`](https://github.com/dicelab-rhul/star-ray) that implements UI functionality backed by the `pygame` and `star_ray_xml` packages.

`star_ray_pygame` implements a specific type of `Agent` known as an `Avatar` which represents a user (typically human) who is interacting with the environment and the agents within it. The UI backend is `pygame`, and `svg` (Scalable Vector Graphics) are used to render the UI. The UI state completely integrated with the state of the environment allowing other agents to view and potentially modify it. This is a dramatic departure from some common software engineering practices such as the MVC (or similar) design pattern. The UI is NOT decoupled from the program state - in fact, for the most part it IS the program state. This package relies on another extension `star_ray_xml` to manage the state of the UI (as well as any other state variables).

This extension has been developed with the intention of exploring human-agent interactions. Agents are able to view a structured version of the UI and modify it as a means of interacting with the user in the most general way. They are able to effectively render text and graphics via their actions. The (human) user may take similar action (via their peripheral devices - mouse, keyboard, etc.) to communicate back (according to whatever functionality the UI is exposing). Agents are able to listen to these user inputs and make futher decisions based on them.

This package serves as a very flexible foundation for supporting researching into human-agent (or AI) interactions on digital devices by leveraging some existing technologies.

See for example, the [`icua2`](https://github.com/dicelab-rhul/icua2) project.
"""
# turn of auto-formating, the order of the imports matters!

import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# ======================================================= #
# NOTE: this must appear before importing other modules! (careful! -> auto-format might move it!)
from .utils import _check_libcairo_install

# this will check for install issues with cairo, its a real pain on windows...
_check_libcairo_install()
# ======================================================= #

from star_ray import Environment  # noqa: E402
from .view import View, WindowConfiguration  # noqa: E402
from .avatar import Avatar  # noqa: E402
from .actuator import AvatarActuator  # noqa: E402
from .ambient import SVGAmbient  # noqa: E402


__all__ = (
    "SVGAmbient",
    "View",
    "Avatar",
    "AvatarActuator",
    "WindowConfiguration",
    "Environment",
)
