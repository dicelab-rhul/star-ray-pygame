import os
from .view import View, WindowConfiguration
from ._async import ViewAsync

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

__all__ = ("View", "ViewAsync", "WindowConfiguration")
