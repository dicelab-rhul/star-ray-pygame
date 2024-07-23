"""The module defines the `SVGAmbient` class which is an extension of `star_ray_xml.XMLAmbient`. This ambient supports pub-sub of XML queries, and contains some useful functionality regarding the handling of SVG data."""

from typing import Any
from star_ray.event import ActiveObservation, ErrorActiveObservation
from star_ray.pubsub._action import Subscribe, Unsubscribe
from star_ray import Agent
from star_ray.utils.type_routing import TypeRouter
from star_ray.pubsub import TypePublisher
from star_ray_xml import XMLAmbient, XMLQuery, Update, Select

from .event import Event, WindowCloseEvent, UserInputEvent
from .utils import LOGGER

__all__ = ("SVGAmbient",)


class SVGAmbient(XMLAmbient):
    """An `Ambient` implementation that provides some useful SVG related functionality, as well as pub-sub support for SVG related queries."""

    DEFAULT_SVG_NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}
    DEFAULT_SVG = """<svg:svg id="root" x="0" y="0" xmlns:svg="http://www.w3.org/2000/svg"></svg:svg>"""
    DEFAULT_SVG_SIZE = (640, 640)
    DEFAULT_SVG_POSITION = (0, 0)

    def __init__(
        self,
        agents: list[Agent],
        svg_size: tuple[float, float] | None = None,
        svg_position: tuple[float, float] | None = None,
        svg_namespaces: dict[str, str] | None = None,
        terminate_on_window_close=True,
        **kwargs,
        # TODO add an option of the root canvas id?
    ):
        """Constructor.

        This will create a root SVG canvas to which all other elements will be drawn. The root svg element id attribute is `root`. This can be changed with an `update` query is desired.

        Args:
            agents (list[Agent]): list of agents to add to this Ambient initially.
            svg_size (tuple[float, float] | None, optional): size of the root svg element. Defaults to None, meaning `width` and `height` will remain undefined.
            svg_position (tuple[float, float] | None, optional): position of the root svg element. Defaults to None, which sets both `x` and `y` to zero.
            svg_namespaces (dict[str, str] | None, optional): the namespaces used. Defaults to the standard svg namespace URI mapping (see `SVGAmbient.DEFAULT_SVG_NAMESPACES`).
            terminate_on_window_close (bool, optional): whether to terminate the environment if a `WindowClosedEvent` occurs, this typically means the user has exited the simulation. Defaults to True.
            kwargs (dict[str,Any]): additional optional arguments.
        """
        # this publisher is used in __subscribe__ to publish events to agents that want them.
        self._publisher = TypePublisher()

        svg = SVGAmbient.DEFAULT_SVG
        svg_namespaces = svg_namespaces if svg_namespaces else dict()
        for k, v in SVGAmbient.DEFAULT_SVG_NAMESPACES.items():
            svg_namespaces.setdefault(k, v)
        super().__init__(agents, xml=svg, namespaces=svg_namespaces, **kwargs)

        self._terminate_on_window_close = terminate_on_window_close
        self._initialise_root(svg_size=svg_size, svg_position=svg_position)

        # this will resolve the types present in `on_user_input_event` type hint and ensure the relevant events are correctly forwarded
        try:
            self._user_input_types = tuple(
                TypeRouter.resolve_first_argument_types(self.on_user_input_event)
            )
            LOGGER.debug(f"user input types: {self._user_input_types}")
        except TypeError as e:
            raise TypeError(
                f"Invalid type hint on method {self.on_user_input_event.__name__}"
            ) from e

    def _initialise_root(
        self,
        svg_size: tuple[float, float] = None,
        svg_position: tuple[float, float] = None,
        **kwargs,
    ):
        """Initialise attributes of the root svg element."""
        # see what has already been defined
        root_attributes = self.__select__(
            Select.new("/svg:svg", ["x", "y", "width", "height"])
        ).values[0]
        # filter out None values
        root_attributes = {k: v for k, v in root_attributes.items() if v is not None}

        if svg_size:
            assert len(svg_size) == 2
            root_attributes["width"] = svg_size[0]
            root_attributes["height"] = svg_size[1]
        if svg_position:
            assert len(svg_position) == 2
            root_attributes["x"] = svg_position[0]
            root_attributes["y"] = svg_position[1]

        root_attributes.setdefault("x", SVGAmbient.DEFAULT_SVG_POSITION[0])
        root_attributes.setdefault("y", SVGAmbient.DEFAULT_SVG_POSITION[1])
        root_attributes.setdefault("width", SVGAmbient.DEFAULT_SVG_SIZE[0])
        root_attributes.setdefault("height", SVGAmbient.DEFAULT_SVG_SIZE[1])
        result = self.__update__(Update.new("/svg:svg", root_attributes))
        if isinstance(result, ErrorActiveObservation):
            raise result.exception()  # something bad happened...

    def on_xml_event(self, action: XMLQuery) -> None:
        """A callback that is triggered immediately AFTER an XMLQuery is executed in `__update__`.

        Args:
            action (XMLQuery): the action
        """
        assert isinstance(action, XMLQuery)

    def on_user_input_event(self, action: UserInputEvent):
        """Callback that is triggered when a user input action is executed in `__update__`. The type hint `UserInputEvent` is used to determine which user input events can be processed by this ambient, it MUST be provided by an override of this method.

        Args:
            action (UserInputEvent): action
        """
        LOGGER.debug("User input event: %s", action)

    def on_unknown_event(self, action: Event):
        """Callback that is triggered when an action of unknown type is executed in `__update__`. This may be overriden for custom handling of such events. Otherwise a ValueError will be raised.

        Args:
            action (Event): unknown action

        Raises:
            ValueError: raised by default.
        """
        # TODO this should be an UnknownEventTypeError? make this a thing
        raise ValueError(f"Action: {action} has unknown type: {type(action)}.")

    def on_exit_event(self, action: WindowCloseEvent):
        """Callback that is triggered when a `WindowCloseEvent` is executed in `__update__`. By default this will flag the environment from termination. This behaviour can be overriden in a subclass.

        Args:
            action (WindowCloseEvent): window close action
        """
        assert isinstance(action, WindowCloseEvent)
        if self._terminate_on_window_close:
            LOGGER.debug("Window closed: %s, shutting down...", action)
            self._is_alive = False  # flag trigger termination

    def __subscribe__(
        self, action: Subscribe | Unsubscribe
    ) -> ActiveObservation | ErrorActiveObservation:
        """Subscribe to receive XMLQuery events from this environment. This will be called automatically when the relevant actions are executed and should not be called manually. Supported actions are only those that inherit from `star_ray_xml.XMLQuery`.

        Args:
            action (Subscribe | Unsubscribe): the subscription action

        Raises:
            TypeError: if the action is not a subscription action

        Returns:
            ActiveObservation | ErrorActiveObservation: the resulting observation - confirmation that the subscription was successful (or not).
        """
        if isinstance(action, Subscribe):
            self._publisher.subscribe(action.topic, action.subscriber)
            return ActiveObservation(action_id=action)
        elif isinstance(action, Unsubscribe):
            self._publisher.unsubscribe(action.topic, action.subscriber)
            return ActiveObservation(action_id=action)
        else:
            raise TypeError(f"Unknown subscription action type: {type(action)}")

    def __update__(self, action: Any) -> ActiveObservation | ErrorActiveObservation:
        """Execute a write action in this `Ambient`.

        Supported action types:
        - Any action that inherits from `XMLQuery`
        - User input actions (types specified by the type hint in `SVGAmbient.on_user_input_event`, see its docs for details.)
        - `WindowCloseEvent`s

        Unsupported actions will be routed to `SVGAmbient.on_unknown_event`, which may raise an exception.

        Args:
            action (Any): action

        Returns:
            ActiveObservation | ErrorActiveObservation: the resulting observation
        """
        try:
            result = None
            if isinstance(action, XMLQuery):
                result = super().__update__(action)
                self.on_xml_event(action)
            elif isinstance(action, self._user_input_types):
                result = self.on_user_input_event(action)
            else:
                result = self.on_unknown_event(action)
            # exit on close?
            if isinstance(action, WindowCloseEvent):
                self.on_exit_event(action)
            # publish the action for any that wish to see it
            self._publisher.publish(action)
            return result
        except Exception as e:
            return ErrorActiveObservation.from_exception(action, e)
