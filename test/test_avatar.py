"""Test that runs a simple simulation with an `Avatar`."""

from star_ray_pygame import SVGAmbient, WindowConfiguration
from star_ray import Environment
from star_ray_pygame.avatar import Avatar
from star_ray_pygame.event import MouseButtonEvent
from star_ray_pygame.actuator import AvatarActuator, attempt
from star_ray_pygame.utils import LOGGER
from star_ray_xml import insert, update
import logging

LOGGER.setLevel(logging.INFO)

WIDTH, HEIGHT = 640, 480
NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

RECT1 = f"""<svg:rect id="myrect1" x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="yellow" xmlns:svg="http://www.w3.org/2000/svg"/>"""
RECT2 = f"""<svg:rect id="myrect2" x="-100" y="0" width="{WIDTH}" height="{HEIGHT}" fill="green" xmlns:svg="http://www.w3.org/2000/svg"/>"""
RECT3 = """<svg:rect id="myrect3" x="0" y="0" width="100" height="100" fill="blue xmlns:svg="http://www.w3.org/2000/svg""/>"""
CIRCLE1 = """<svg:circle id="mycircle1" cx="50" cy="50" r="40" fill="yellow" stroke="black" stroke-width="2" xmlns:svg="http://www.w3.org/2000/svg"/>"""

window_config = WindowConfiguration(
    width=WIDTH, height=HEIGHT, title="svg test", resizable=True, fullscreen=False
)


class TestActuator(AvatarActuator):
    """Test Actuator that changes the colour of a circle when clicking left/right mouse."""

    @attempt
    def on_click(self, event: MouseButtonEvent):  # noqa: D102
        color = ["red", "blue", "yellow"][event.button]
        return update(xpath="/svg:svg/svg:circle", attrs={"fill": color})


avatar = Avatar([], [TestActuator()], window_config=window_config)
ambient = SVGAmbient([avatar], svg_position=(0, 0), svg_size=(WIDTH, HEIGHT))
ambient.__update__(insert("/svg:svg", element=RECT1, index=0))
ambient.__update__(insert("/svg:svg", element=RECT2, index=1))
ambient.__update__(insert("/svg:svg", element=RECT3, index=2))
ambient.__update__(insert("/svg:svg", element=CIRCLE1, index=3))

environment = Environment(ambient, wait=0.1)
environment.run()
