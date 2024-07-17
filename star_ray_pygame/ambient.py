from typing import List, Dict, Any, Tuple
from star_ray.event import ActiveObservation, ErrorActiveObservation
from star_ray.pubsub._action import Subscribe, Unsubscribe
from star_ray_xml import XMLAmbient, XMLQuery, Update
from star_ray import Agent
from star_ray.agent.component.type_routing import resolve_first_argument_types
from star_ray.pubsub import TypePublisher

from .event import Event, WindowCloseEvent, UserInputEvent
from .utils import LOGGER

__all__ = ("SVGAmbient",)

DEFAULT_SVG_NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}
DEFAULT_SVG = """<svg:svg id="root" x="0" y="0" xmlns:svg="http://www.w3.org/2000/svg"></svg:svg>"""


class SVGAmbient(XMLAmbient):
    DEFAULT_SVG = (
        """<svg:svg xmlns="http://www.w3.org/2000/svg" x="0" y="0"></svg:svg>"""
    )
    DEFAULT_SVG_NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

    def __init__(
        self,
        agents: List[Agent],
        svg_size: Tuple[float, float] = None,
        svg_position: Tuple[float, float] = None,
        svg_namespaces: Dict[str, str] = None,
        terminate_on_window_close=True,
        **kwargs,
    ):
        svg = DEFAULT_SVG
        svg_namespaces = svg_namespaces if svg_namespaces else dict()
        for k, v in DEFAULT_SVG_NAMESPACES.items():
            svg_namespaces.setdefault(k, v)
        super().__init__(agents, xml=svg, namespaces=svg_namespaces, **kwargs)

        self._terminate_on_window_close = terminate_on_window_close
        self._initialise_root(svg_size=svg_size, svg_position=svg_position)

        # this publisher is used in __subscribe__ to publish events to agents that want them.
        self._publisher = TypePublisher()

        # this will resolve the types present in `on_user_input_event` type hint and ensure the relevant events are correctly forwarded
        try:
            self._user_input_types = tuple(
                resolve_first_argument_types(self.on_user_input_event)
            )
            LOGGER.debug(f"user input types: {self._user_input_types}")
        except TypeError as e:
            raise ValueError(
                f"Invalid type hint on method {self.on_user_input_event.__name__}"
            ) from e

    def _initialise_root(
        self,
        svg_size: Tuple[float, float] = None,
        svg_position: Tuple[float, float] = None,
        **kwargs,
    ):
        root_attributes = {}
        if svg_size:
            assert len(svg_size) == 2
            root_attributes["width"] = svg_size[0]
            root_attributes["height"] = svg_size[1]
        if svg_position:
            assert len(svg_position) == 2
            root_attributes["x"] = svg_position[0]
            root_attributes["y"] = svg_position[1]
        self.__update__(Update(xpath="/svg:svg", attrs=root_attributes))

    def on_xml_event(self, action: XMLQuery):
        assert isinstance(action, XMLQuery)
        return super().__update__(action)

    def on_user_input_event(self, action: UserInputEvent):
        LOGGER.debug("User input event: %s", action)

    def on_unknown_event(self, action: Event):
        raise ValueError(f"Action: {action} has unknown type: {type(action)}.")

    def on_exit_event(self, action: WindowCloseEvent):
        assert isinstance(action, WindowCloseEvent)
        if self._terminate_on_window_close:
            LOGGER.debug("Window closed: %s, shutting down...", action)
            self._is_alive = False  # flag trigger termination

    def __subscribe__(
        self, action: Subscribe | Unsubscribe
    ) -> ActiveObservation | ErrorActiveObservation:
        if isinstance(action, Subscribe):
            self._publisher.subscribe(action.topic, action.subscriber)
        elif isinstance(action, Unsubscribe):
            self._publisher.unsubscribe(action.topic, action.subscriber)
        else:
            raise TypeError(f"Unknown subscription action type: {type(action)}")

    def __update__(self, action: Any) -> ActiveObservation | ErrorActiveObservation:
        try:
            if isinstance(action, XMLQuery):
                self.on_xml_event(action)
            elif isinstance(action, self._user_input_types):
                self.on_user_input_event(action)
            else:
                self.on_unknown_event(action)
            # exit on close?
            if isinstance(action, WindowCloseEvent):
                self.on_exit_event(action)
            # publish the action for any that wish to see it
            self._publisher.publish(action)
        except Exception as e:
            return ErrorActiveObservation.from_exception(action, e)
