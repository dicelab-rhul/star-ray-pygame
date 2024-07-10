""" TODO """

from .utils import LOGGER
from typing import List, Type, Callable
from star_ray import Sensor, Actuator, Component
from star_ray.event import Event, ActiveObservation, ErrorObservation
from star_ray_xml import XMLState, XMLSensor, Update, Insert, Replace, Delete
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
UserInputEvent = WindowFocusEvent | WindowMoveEvent | WindowResizeEvent | WindowCloseEvent | WindowOpenEvent | MouseButtonEvent | MouseMotionEvent | KeyEvent


class AvatarActuator(Actuator):

    @attempt()
    def user_input(self, action: UserInputEvent):
        return action


class Avatar(AgentRouted):

    def __init__(
        self,
        sensors: List[Sensor],
        actuators: List[Actuator],
        *args,
        window_config: WindowConfiguration | None = None,
        **kwargs,
    ):
        actuators = actuators if actuators else []
        sensors = sensors if sensors else []
        self._xml_sensor = XMLSensor(
            subscriptions=(Update, Insert, Replace, Delete))
        sensors.append(self._xml_sensor)
        super().__init__(sensors, actuators, *args, **kwargs)
        if window_config is None:
            window_config = WindowConfiguration()  # use default values
        self._view = View(window_config=window_config)
        self._state = None  # set on the first cycle

    def get_screen_info(self):
        return self._view.get_screen_info()

    def get_window_info(self):
        return self._view.get_window_info()

    @observe
    def on_error_observation(self, observation: ErrorObservation):
        raise observation.exception()

    @observe
    def _on_xml_change(self, observation: Update | Insert | Delete | Replace):
        if isinstance(observation, Update):
            self._state.update(observation)
        elif isinstance(observation, Insert):
            self._state.insert(observation)
        elif isinstance(observation, Delete):
            self._state.delete(observation)
        elif isinstance(observation, Replace):
            self._state.replace(observation)

    @observe
    def on_observation(self, observation: ActiveObservation, component: Component):
        # this is only called on the first cycle to set the initial xml state
        assert self._state is None
        assert len(observation.values) == 1
        self._state = XMLState(observation.values[0])
        # TODO this is a bit of a hack, it assumes all namespaces are defined in the root, which may not be the case.
        # TODO make an official note of this, or create an action that can get the actual namespaces from the environment...?
        self._state._namespaces = self._state.get_root().nsmap

    @decide
    def _get_user_input(self):
        # NOTE: there will on be a single MouseMotionEvent produced by pygame on each call to get_events.
        return self._view.get_events()

    def __cycle__(self):
        super().__cycle__()
        # TODO consider refactoring the view to make use of XMLState rather than the underlying lxml <- this is a big job...
        self._view.update(self._state.get_root()._base)
        self._view.render()

    @ staticmethod
    def get_screen_size():
        return get_screen_size()
