"""Module contain various utilities used in the `star_ray_pygame` package."""

import os
import sys
from star_ray.utils import _LOGGER as LOGGER


def _check_libcairo_install():
    # LOGGER.debug("Checking libcairo installation...")
    WINDOW_NAME = "nt"
    ON_WINDOWS = os.name == WINDOW_NAME
    if ON_WINDOWS:
        LOGGER.debug("Checking libcairo installation...")

        # try to locate GTK installation and add it to path, this is typically not done by default
        gtkbin = r"C:\Program Files\GTK3-Runtime Win64\bin"
        if os.path.exists(gtkbin):
            os.environ["PATH"] = os.pathsep.join((gtkbin, os.environ["PATH"]))

    def _cairosvg_ok():
        try:
            import cairosvg  # noqa
        except OSError as e:
            return (False, e.args[0])
        return (True, None)

    def indent(text):
        indent = "    "  # 4 spaces, or you can use "\t" for a tab
        return "\n".join(indent + line for line in text.split("\n"))

    ok, err = _cairosvg_ok()
    if not ok:
        WINDOWS_INSTALL_MESSAGE = """>> On Windows: Install the latest GTK-3 runtime from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases, use the default install path!"""
        OTHER_INSTALL_MESSAGE = """>> On Linux/MacOS: Contact 'star-ray-pygame' package maintainer or check github issues: https://github.com/dicelab-rhul/star-ray-pygame/issues"""
        ERROR_MESSAGE = f"""'star-ray-pygame' requires a cairo installation which may not be installed automatically on some systems.\n  Cause:\n{indent(err)}\n\nACTION REQUIRED: Please ensure the required binaries are installed and accessible via your PATH environment variable.\n    {WINDOWS_INSTALL_MESSAGE if ON_WINDOWS else OTHER_INSTALL_MESSAGE}\n    >> See 'star-ray-pygame' README for more information: https://github.com/dicelab-rhul/star-ray-pygame.
        """
        LOGGER.error(ERROR_MESSAGE)
        sys.exit(-1)
