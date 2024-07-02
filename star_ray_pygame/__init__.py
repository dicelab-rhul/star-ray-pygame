""" TODO """


import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

from .view import View, WindowConfiguration
from .avatar import Avatar

__all__ = ("View", "Avatar", "WindowConfiguration")
