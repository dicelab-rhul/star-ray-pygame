"""Module defines the `Avatar` class, see class for details."""

from star_ray import Sensor, Actuator, Component
from star_ray.event import ActiveObservation, ErrorObservation
from star_ray_xml import _XMLState, XMLSensor, XMLQuery
from star_ray.ui import WindowConfiguration
from star_ray.agent import AgentRouted, observe, decide

from .view import View, get_screen_size


class Avatar(AgentRouted):
    """Class implementing an `Agent` that acts on behalf of a (human) user. It displays a UI that the user can interact with. User input (clicks, key presses, etc.) will be captured and executed via this agents actuators. Such actuators will typically convert these user input events to actions that will mutate the environment in some way, or request new information to be displayed in the UI. It is also typical for user input events to be made avaliable to other agents in the environment (via `star_ray`s pub-sub mechanism), this can be done simply by forwarding them directly to the environment via a dedicated actuator."""

    def __init__(
        self,
        sensors: list[Sensor] = None,
        actuators: list[Actuator] = None,
        window_config: WindowConfiguration | None = None,
        **kwargs,
    ):
        """Constructor.

        Args:
            sensors (list[Sensor], optional): list of sensors. Defaults to None. An `XMLSensor` will always be added to this list.
            actuators (list[Actuator], optional): list of actuators. Defaults to None.
            window_config (WindowConfiguration | None, optional): window configuration for the pygame window. Defaults to None, see default in `star_ray_pygame.View`.
            kwargs (dict[str,Any]): additional optional arguments.
        """
        actuators = actuators if actuators else []
        sensors = sensors if sensors else []
        sensors.append(XMLSensor())
        super().__init__(sensors, actuators, **kwargs)
        if window_config is None:
            window_config = WindowConfiguration()  # use default values
        self._view = View(window_config=window_config)
        self._state = None  # set on the first cycle when svg data has been sensed

    @property
    def xml_sensor(self) -> XMLSensor:
        """Getter for the `XMLSensor` that is attached to this agent.

        Returns:
            XMLSensor: the sensor
        """
        return next(filter(lambda x: isinstance(x, XMLSensor), self.sensors))

    def get_screen_info(self):
        """Get information about the screen (monitor), including the monitor index and size.

        NOTE: Currently only single monitor setups are supported, the monitor index will always be zero.

        Returns:
            dict[str,Any]: screen information
        """
        return self._view.get_screen_info()

    def get_window_info(self):
        """Get information about the display window, including: title, position (on the monitor) and size (in pixels).

        Returns:
            dict[str,Any]: window information
        """
        return self._view.get_window_info()

    @observe
    def on_error_observation(self, observation: ErrorObservation):
        """Callback for error observations, by default an exception is raised. Override for custom handling of these errors.

        Args:
            observation (ErrorObservation): observation containing the error.

        Raises:
            observation.exception: the exception contained in the observation (raised by default).
        """
        raise observation.exception()

    @observe
    def on_observation(self, observation: ActiveObservation, component: Component):
        """Callback when receiving an observation. By default this is only expected to be called upon the first observation made by the attached `XMLSensor` which senses the full state of the environment (all svg code).

        Args:
            observation (ActiveObservation): observation containing svg code for rendering.
            component (Component): component that the observation originated from
        """
        if isinstance(component, XMLSensor):
            # TODO we can do some checks to determine whether this is infact the first observation...
            # otherwise, this should only called on the first cycle to set the initialise xml state
            assert self._state is None
            assert len(observation.values) == 1
            self._state = _XMLState(observation.values[0])
            # TODO this is a bit of a hack, it assumes all namespaces are defined in the root, which may not be the case.
            # TODO make an official note of this, or create an action that can get the actual namespaces from the environment...?
            self._state._namespaces = self._state.get_root().nsmap

    @observe
    def _on_xml_change(self, observation: XMLQuery):
        """Called whenever an `XMLQuery` event is received via the `XMLSensor` attached to this agent, it will update the state of the view."""
        # update view state from xml query
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

    def __cycle__(self):  # noqa: D105
        super().__cycle__()
        self.render()

    def render(self) -> None:
        """Render the UI."""
        # TODO consider refactoring the view to make use of XMLState rather than the underlying lxml <- this is a big job...
        self._view.update(self._state.get_root()._base)
        self._view.render()

    @staticmethod
    def get_screen_size() -> tuple[int, int]:
        """Get the screen/monitor size (in pixels).

        Returns:
            tuple[int, int]: screen size
        """
        return get_screen_size()
