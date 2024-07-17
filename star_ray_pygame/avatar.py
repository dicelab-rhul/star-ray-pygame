""" TODO """

from .utils import LOGGER
from typing import List, Type, Callable
from star_ray import Sensor, Actuator, Component
from star_ray.event import Event, ActiveObservation, ErrorObservation
from star_ray_xml import _XMLState, XMLSensor, XMLQuery
from star_ray.ui import WindowConfiguration
from star_ray.agent import AgentRouted, attempt, observe, decide

from .view import View, get_screen_size
from .event import (
    WindowFocusEvent,
    WindowMoveEvent,
    WindowResizeEvent,
    WindowCloseEvent,
    WindowOpenEvent,
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
)

UserInputEvent = (
    WindowFocusEvent
    | WindowMoveEvent
    | WindowResizeEvent
    | WindowCloseEvent
    | WindowOpenEvent
    | MouseButtonEvent
    | MouseMotionEvent
    | KeyEvent
)


class AvatarActuator(Actuator):

    @attempt()
    def user_input(self, action: UserInputEvent):
        return action


class Avatar(AgentRouted):

    def __init__(
        self,
        sensors: List[Sensor] = None,
        actuators: List[Actuator] = None,
        window_config: WindowConfiguration | None = None,
        **kwargs,
    ):
        actuators = actuators if actuators else []
        sensors = sensors if sensors else []
        sensors.append(XMLSensor())
        super().__init__(sensors, actuators, **kwargs)
        if window_config is None:
            window_config = WindowConfiguration()  # use default values
        self._view = View(window_config=window_config)
        self._state = None  # set on the first cycle

    @property
    def xml_sensor(self):
        return next(filter(lambda x: isinstance(x, XMLSensor), self.sensors))

    def get_screen_info(self):
        return self._view.get_screen_info()

    def get_window_info(self):
        return self._view.get_window_info()

    @observe
    def on_error_observation(self, observation: ErrorObservation):
        raise observation.exception()

    @observe
    def on_observation(self, observation: ActiveObservation, component: Component):
        # this is only called on the first cycle to set the initialise xml state
        assert self._state is None
        assert len(observation.values) == 1
        print(observation.values[0])
        self._state = _XMLState(observation.values[0])
        # TODO this is a bit of a hack, it assumes all namespaces are defined in the root, which may not be the case.
        # TODO make an official note of this, or create an action that can get the actual namespaces from the environment...?
        self._state._namespaces = self._state.get_root().nsmap

    @observe
    def _on_xml_change(self, observation: XMLQuery):
        # this is called whenever an xml event it received from the XMLSensor attached to this agent.
        # it will update the state of the view
        observation.__execute__(self._state)

    @decide
    def get_user_input(self):
        """`decide` method that will return all user generated events. These events will then be forwarded to the relevant actuators according to the `decide` protocol.

        This method may be overriden in a subclass but must be decorated with `decide`.

        Returns:
            List[Event]: user input events
        """
        # NOTE: there will on be a single MouseMotionEvent produced by pygame on each call to get_events.
        return self._view.get_events()

    def __cycle__(self):
        super().__cycle__()
        self.render()

    def render(self):
        """Render the UI."""
        # TODO consider refactoring the view to make use of XMLState rather than the underlying lxml <- this is a big job...
        self._view.update(self._state.get_root()._base)
        self._view.render()

    @staticmethod
    def get_screen_size():
        """Get the size of the screen (monitor)."""
        return get_screen_size()
