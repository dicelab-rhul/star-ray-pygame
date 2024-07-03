""" TODO """

from typing import List, Type, Callable
from star_ray import Sensor, Actuator
from star_ray.event import Event, ActiveObservation, ErrorObservation
from star_ray_xml import XMLState, XMLSensor, Update, Insert, Replace, Delete
from star_ray.ui import WindowConfiguration
from star_ray.agent import RoutedActionAgent

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
from .utils import LOGGER


class Avatar(RoutedActionAgent):

    def __init__(
        self,
        sensors: List[Sensor],
        actuators: List[Actuator],
        *args,
        window_config: WindowConfiguration = None,
        **kwargs,
    ):
        actuators = actuators if actuators else []
        sensors = sensors if sensors else []
        self._xml_sensor = XMLSensor(
            subscriptions=(Update, Insert, Replace, Delete))
        sensors.append(self._xml_sensor)
        super().__init__(sensors, actuators, *args, **kwargs)
        if not window_config:
            window_config = WindowConfiguration()  # use default values
        self._view = View(window_config=window_config)
        self._state = None
        # local callbacks
        self.add_event_callback(WindowFocusEvent, self.on_window_focus_event)
        self.add_event_callback(WindowMoveEvent, self.on_window_move_event)
        self.add_event_callback(WindowResizeEvent, self.on_window_resize_event)
        self.add_event_callback(WindowCloseEvent, self.on_window_close_event)
        self.add_event_callback(WindowOpenEvent, self.on_window_open_event)
        self.add_event_callback(MouseButtonEvent, self.on_mouse_button_event)
        self.add_event_callback(MouseMotionEvent, self.on_mouse_motion_event)
        self.add_event_callback(KeyEvent, self.on_key_event)

    def add_event_callback(
        self, event_type: Type[Event], callback: Callable[[Event], None]
    ):
        cls_name = RoutedActionAgent.get_fully_qualified_name(event_type)
        self._action_router_map[cls_name].add(callback)

    def remove_event_callback(
        self, event_type: Type[Event], callback: Callable[[Event], None]
    ):
        cls_name = RoutedActionAgent.get_fully_qualified_name(event_type)
        self._action_router_map[cls_name].remove(callback)

    def on_window_open_event(self, event: WindowOpenEvent):
        LOGGER.debug(f"%s@%s", type(self), event)

    def on_window_close_event(self, event: WindowCloseEvent):
        LOGGER.debug(f"%s@%s", type(self), event)

    def on_mouse_button_event(self, event: MouseButtonEvent):
        LOGGER.debug(f"%s@%s", type(self), event)

    def on_mouse_motion_event(self, event: MouseMotionEvent):
        LOGGER.debug(f"%s@%s", type(self), event)

    def on_key_event(self, event: KeyEvent):
        LOGGER.debug(f"%s@%s", type(self), event)

    def on_window_focus_event(self, event: WindowFocusEvent):
        LOGGER.debug(f"%s@%s", type(self), event)

    def on_window_move_event(self, event: WindowMoveEvent):
        LOGGER.debug(f"%s@%s", type(self), event)

    def on_window_resize_event(self, event: WindowResizeEvent):
        LOGGER.debug(f"%s@%s", type(self), event)

    def get_screen_info(self):
        return self._view.get_screen_info()

    def get_window_info(self):
        return self._view.get_window_info()

    def on_error_observation(self, observation: ErrorObservation):
        raise observation.exception()

    def __cycle__(self):
        # TODO support additional sensors?
        # assert set([self._xml_sensor]) == set(self.sensors)
        for observation in self._xml_sensor.iter_observations():
            if isinstance(observation, ErrorObservation):
                self.on_error_observation(observation)
            elif isinstance(observation, ActiveObservation):
                assert self._state is None
                assert len(observation.values) == 1
                self._state = XMLState(observation.values[0])
                # TODO this is a bit of a hack, it assumes all namespaces are defined in the root, which may not be the case.
                # TODO make an official note of this, or create an action that can get the actual namespaces from the environment...?
                self._state._namespaces = self._state.get_root().nsmap
            # TODO better not to distinguish between these, define a function in XML that handles any event?
            # TODO subscriptions should probably have a wrapper?
            elif isinstance(observation, Update):
                self._state.update(observation)
            elif isinstance(observation, Insert):
                self._state.insert(observation)
            elif isinstance(observation, Delete):
                self._state.delete(observation)
            elif isinstance(observation, Replace):
                self._state.replace(observation)
            else:
                raise ValueError(
                    f"Recieve observation of unknown type: {type(observation)}"
                )
        user_events = self._view.get_events()
        # NOTE: there will on be a single MouseMotionEvent produced by pygame on each call to get_events.
        self.__attempt__(user_events)
        # TODO consider refactoring the view to make use of XMLState
        self._view.update(self._state.get_root()._base)
        self._view.render()
        for actuator in self.get_actuators():
            for observation in actuator.iter_observations():
                if isinstance(observation, ErrorObservation):
                    self.on_error_observation(observation)

    @staticmethod
    def get_screen_size():
        return get_screen_size()
