from star_ray_pygame import View, WindowConfiguration
from star_ray.event import (
    WindowCloseEvent,
    MouseButtonEvent,
    WindowFocusEvent,
    WindowMoveEvent,
    WindowResizeEvent,
)
from lxml import etree
import time
from typing import Tuple
import asyncio


WIDTH, HEIGHT = 640, 480
SVG = f"""
<svg width="{WIDTH}" height="{HEIGHT}" xmlns="http://www.w3.org/2000/svg">
  <svg x="50" y="50" width="100" height="100">
        <rect id="myrect" x="0" y="0" width="100" height="200" fill="red"/>
        <circle id="mycircle" cx="50" cy="50" r="40" fill="yellow" stroke="black" stroke-width="2"/>
  </svg>  

  <g x="200" y="200" width="100" height="100">
        <rect id="myrect" x="0" y="0" width="100" height="200" fill="red"/>
        <circle id="mycircle" cx="50" cy="50" r="40" fill="yellow" stroke="black" stroke-width="2"/>
  </g>
</svg>"""

window_config = WindowConfiguration(
    width=WIDTH, height=HEIGHT, title="svg test", resizable=True, fullscreen=False
)


async def main():
    async def task():
        running = True
        view = View(window_config)
        view.update(etree.fromstring(SVG))
        while running:
            events = view.get_events()
            await asyncio.sleep(0.1)
            for event in events:
                if isinstance(event, WindowCloseEvent):
                    running = False
                elif isinstance(event, MouseButtonEvent):
                    print(event)
                elif isinstance(
                    event, (WindowFocusEvent, WindowMoveEvent, WindowResizeEvent)
                ):
                    print("window event:", event)
            view.render()

    task = asyncio.create_task(task())
    await task


asyncio.run(main())
