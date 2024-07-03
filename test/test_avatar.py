from star_ray_pygame import View, WindowConfiguration
from star_ray_xml import XMLAmbient
from star_ray.event import (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    WindowCloseEvent,
    WindowOpenEvent,
    WindowFocusEvent,
    WindowMoveEvent,
    WindowResizeEvent,
)
from star_ray.agent import Actuator, attempt
from star_ray import Environment

from star_ray_pygame.avatar import Avatar

from star_ray_pygame.utils import LOGGER
import logging
LOGGER.setLevel(logging.INFO)

WIDTH, HEIGHT = 640, 480
NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

SVG = f"""
<svg x="100" y="100" width="{WIDTH}" height="{HEIGHT}" xmlns="http://www.w3.org/2000/svg">
  <svg x="50" y="50" width="100" height="100">
        <rect id="myrect" x="0" y="0" width="100" height="200" fill="red"/>
        <circle id="mycircle" cx="50" cy="50" r="40" fill="yellow" stroke="black" stroke-width="2"/>
  </svg>  

  <g x="200" y="200" width="100" height="100">
        <rect id="myrect" x="0" y="0" width="100" height="200" fill="red"/>
        <circle id="mycircle" cx="50" cy="50" r="40" fill="yellow" stroke="black" stroke-width="2"/>
  </g>
</svg>"""

SVG = f"""<svg x="0" y="0" width="{WIDTH}" height="{HEIGHT}" xmlns="http://www.w3.org/2000/svg">
    <rect id="myrect" x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="yellow"/>
    <rect id="myrect" x="-100" y="0" width="{WIDTH}" height="{HEIGHT}" fill="green"/>

    <rect id="myrect" x="0" y="0" width="100" height="100" fill="blue"/>
    <circle id="mycircle" cx="50" cy="50" r="40" fill="yellow" stroke="black" stroke-width="2"/>
</svg>"""

window_config = WindowConfiguration(
    width=WIDTH, height=HEIGHT, title="svg test", resizable=True, fullscreen=False
)


class MyAmbient(XMLAmbient):

    def __update__(self, action):
        if isinstance(action, WindowCloseEvent):
            self._is_alive = False  # trigger shutdown
        super().__update__(action)


class DefaultActuator(Actuator):
    @attempt(route_events=[MouseButtonEvent, MouseMotionEvent, KeyEvent, WindowCloseEvent,
                           WindowOpenEvent, WindowFocusEvent, WindowMoveEvent, WindowResizeEvent])
    def attempt(self, action):
        return action


avatar = Avatar([], [DefaultActuator()], window_config=window_config)
ambient = MyAmbient([avatar], xml=SVG, namespaces=NAMESPACES)
environment = Environment(ambient, wait=0.1)
environment.run()
