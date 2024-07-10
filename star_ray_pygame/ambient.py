from typing import List, Dict, Any
from copy import deepcopy
from star_ray.event import ActiveObservation, ErrorActiveObservation
from star_ray_xml import XMLAmbient, Insert, Update, Replace, Delete
from star_ray import Event, Agent, Environment
from star_ray.agent import _TypeRouter
from star_ray_xml.query import XMLQuery

from .event import WindowCloseEvent, UserInputEvent
from .utils import LOGGER

__all__ = ("Environment", "Ambient")


class Ambient(XMLAmbient):
    DEFAULT_SVG = """<svg:svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"></svg:svg>"""
    DEFAULT_SVG_NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

    def __init__(
            self, agents: List[Agent], svg: str = None, namespaces: Dict[str, str] = None, terminate_on_window_close=True,
            ** kwargs):
        if svg is None:
            svg = deepcopy(Ambient.DEFAULT_SVG)
        if namespaces is None:
            namespaces = deepcopy(Ambient.DEFAULT_SVG_NAMESPACES)
        self._terminate_on_window_close = terminate_on_window_close
        # self._pause_on_window_focus_lost = pause_on_window_focus_lost
        # assert not pause_on_window_focus_lost  # TODO not implemented yet...
        super().__init__(agents, xml=svg, namespaces=namespaces, **kwargs)
        self._event_router = _TypeRouter()
        for method in _TypeRouter.get_all_decorated_methods(self):
            self._event_router.add(method)

    @_TypeRouter.route
    def on_xml_event(self, action: XMLQuery):
        assert isinstance(action, XMLQuery)
        return super().__update__(action)

    @_TypeRouter.route
    def on_exit_event(self, action: WindowCloseEvent):
        assert isinstance(action, WindowCloseEvent)
        if self._terminate_on_window_close:
            LOGGER.debug("Window closed: %s, shutting down...", action)
            self._is_alive = False  # flag trigger termination

    @_TypeRouter.route
    def on_user_input_event(self, action: UserInputEvent):
        LOGGER.debug("User input event: %s", action)

    @_TypeRouter.route
    def on_unknown_action(self, action: Any):
        raise ValueError(f"Action: {action} has unknown type: {type(action)}.")

    def __update__(self, action: Any) -> ActiveObservation | ErrorActiveObservation:
        try:
            results = self._event_router(action)
            # TODO for now, the action should be routed to a single method to produce a single observation?
            # QUESTION: can a single action produce multiple observations? I suppose this would be handy...
            assert len(results) == 1
            return results[0]
        except Exception as e:
            return ErrorActiveObservation.from_exception(action, e)
