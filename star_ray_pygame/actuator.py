from star_ray.agent import Actuator, attempt

from .event import UserInputEvent

__all__ = ("DefaultActuator",)


class DefaultActuator(Actuator):
    """This simple actuator will automatically foward all user input events (see `star_ray_pygame.UserInputEvent` for a full list) to the environment. This allows other agents to subscribe to receive these events, or for them to be processed by the `Ambient`.
    """

    @attempt
    def attempt(self, action: UserInputEvent) -> UserInputEvent:
        """Default attempt method, simply forwards any `UserInputEvent`s to the environment (assuming the use of a `star_ray.agent.AgentRouted`).

        Args:
            action (UserInputEvent): to forward

        Returns:
            UserInputEvent: the action (returning the action is default attempt method behaviour).
        """
        return action
