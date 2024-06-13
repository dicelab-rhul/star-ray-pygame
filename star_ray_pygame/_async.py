from typing import Callable, Any
from star_ray import Ambient, Agent

from star_ray_xml import XMLAmbient
import asyncio
from .view import View


class ViewAsync(View):

    def __init__(self, ambient: XMLAmbient, avatar_factory: Callable[[], Agent]):
        super().__init__(self)
        self._ambient = ambient
        self._avatar_factory = avatar_factory
        # self._has_changed = asyncio.Event()

    # def __notify__(self, _: Any) -> None:
    #     self._has_changed.set()

    async def run(self, dt=1 / 30):
        while self.is_open:
            await asyncio.sleep(dt)
            events = self.step()
            print(events)
            # TODO pipe these events to the avatar!
        self.close()


#     async def _update_on_change(self, dt):
#         while self.is_open:
#             await asyncio.sleep(dt)
#             await self._has_changed.wait()
#             if self.is_open:
#                 self.update(self._ambient.get_state().get_root())
#                 self.render()
#             self._has_changed.clear()  # this wont cause a race condition, asycnio is just a hack ;)
# result = self._ambient.__subscribe__(
#             Subscribe(topic=(Update, Insert, Replace, Delete), subscriber=self)
#         )  # TODO check that result is ok
