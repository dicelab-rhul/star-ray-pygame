""" TODO """

# pylint: disable=no-member

import pygame
from pygame.event import EventType

from star_ray.event import (
    MouseButtonEvent,
    MouseMotionEvent,
    KeyEvent,
    WindowCloseEvent,
    WindowOpenEvent,
    WindowResizeEvent,
    WindowMoveEvent,
    WindowFocusEvent,
)

# constant values
PYGAME_KEYDOWN = pygame.KEYDOWN
PYGAME_KEYUP = pygame.KEYUP
PYGAME_QUIT = pygame.QUIT
PYGAME_MOUSEDOWN = pygame.MOUSEBUTTONDOWN
PYGAME_MOUSEUP = pygame.MOUSEBUTTONUP
PYGAME_MOUSEMOTION = pygame.MOUSEMOTION
PYGAME_WINDOWRESIZE = pygame.VIDEORESIZE
PYGAME_WINDOWMOVE = pygame.USEREVENT + 1
PYGAME_WINDOWFOCUS = pygame.USEREVENT + 2
PYGAME_WINDOWOPEN = pygame.USEREVENT + 3
PYGAME_WINDOWCLOSE = PYGAME_QUIT  # alias for PYGAME_QUIT

PYGAME_LEFTMOUSEBUTTON = 1
PYGAME_MIDDLEMOUSEBUTTON = 2
PYGAME_RIGHTMOUSEBUTTON = 3

MOUSE_BUTTON_MAP = {
    PYGAME_LEFTMOUSEBUTTON: MouseButtonEvent.BUTTON_LEFT,
    PYGAME_MIDDLEMOUSEBUTTON: MouseButtonEvent.BUTTON_MIDDLE,
    PYGAME_RIGHTMOUSEBUTTON: MouseButtonEvent.BUTTON_RIGHT,
}


def create_window_move_event_from_pygame_event(
    pygame_event: EventType,
):
    """Creates a `WindowMoveEvent` from a `pygame` event.

    Args:
        `pygame_event` (`pygame.event.EventType`): The `pygame` event.

    Returns:
        `WindowMoveEvent`: The `WindowMoveEvent` instance.

    Raises:
        `ValueError`: If the `pygame` event type does not match `PYGAME_WINDOWMOVE`.
    """
    if pygame_event.type != PYGAME_WINDOWMOVE:
        raise ValueError(
            "The provided pygame event is not a `PYGAME_WINDOWMOVE` event."
        )
    return WindowMoveEvent(position=pygame_event.position)


def create_window_focus_event_from_pygame_event(
    pygame_event: EventType,
):
    """Creates a `WindowFocusEvent` from a `pygame` event.

    Args:
        `pygame_event` (`pygame.event.EventType`): The `pygame` event.

    Returns:
        `WindowFocusEvent`: The `WindowFocusEvent` instance.

    Raises:
        `ValueError`: If the `pygame` event type does not match `PYGAME_WINDOWFOCUS`.
    """
    if pygame_event.type != PYGAME_WINDOWFOCUS:
        raise ValueError(
            "The provided pygame event is not a `PYGAME_WINDOWFOCUS` event."
        )
    return WindowFocusEvent(has_focus=pygame_event.has_focus)


def create_window_resize_event_from_pygame_event(
    pygame_event: EventType,
):
    """Creates a `WindowResizeEvent` from a `pygame` event.

    Args:
        `pygame_event` (`pygame.event.EventType`): The `pygame` event.

    Returns:
        `WindowResizeEvent`: The `WindowResizeEvent` instance.

    Raises:
        `ValueError`: If the `pygame` event type does not match `PYGAME_WINDOWRESIZE`.
    """
    if pygame_event.type != PYGAME_WINDOWRESIZE:
        raise ValueError(
            "The provided pygame event is not a `PYGAME_WINDOWRESIZE` event."
        )
    return WindowResizeEvent(size=tuple(pygame_event.size))


def create_window_close_event_from_pygame_event(pygame_event: EventType):
    """Creates an `WindowCloseEvent` from a `pygame` event.

    Args:
        `pygame_event` (`pygame.event.EventType`): The `pygame` event.

    Returns:
        `WindowCloseEvent`: The `WindowCloseEvent` instance.

    Raises:
        `ValueError`: If the `pygame` event type does not match `PYGAME_QUIT`.
    """
    if pygame_event.type != PYGAME_QUIT:
        raise ValueError("The provided pygame event is not a `PYGAME_QUIT` event.")
    return WindowCloseEvent()


def create_window_open_event_from_pygame_event(pygame_event: EventType):
    """Creates an `WindowOpenEvent` from a `pygame` event.

    Args:
        `pygame_event` (`pygame.event.EventType`): The `pygame` event.

    Returns:
        `WindowOpenEvent`: The `WindowOpenEvent` instance.

    Raises:
        `ValueError`: If the `pygame` event type does not match `PYGAME_QUIT`.
    """
    if pygame_event.type != PYGAME_WINDOWOPEN:
        raise ValueError(
            "The provided pygame event is not a `PYGAME_WINDOWOPEN` event."
        )
    return WindowOpenEvent()


def create_key_event_from_pygame_event(pygame_event):
    """Creates a `KeyEvent` instance from a `pygame` keyboard event.

    Args:
        `pygame_event` (`pygame.event.Event`): The `pygame` event from which to create the `KeyEvent`.
    Returns:
        `KeyEvent`: A new instance of `KeyEvent` initialized with the `pygame` event data.

    Raises:
        `ValueError`: If the provided `pygame` event is not a `KEYDOWN` or `KEYUP` event.
    """
    if pygame_event.type not in (PYGAME_KEYDOWN, PYGAME_KEYUP):
        raise ValueError(
            "The provided pygame event is not a `PYGAME_KEYDOWN` or `PYGAME_KEYUP` event."
        )
    status = KeyEvent.DOWN if pygame_event.type == PYGAME_KEYDOWN else KeyEvent.UP
    return KeyEvent(
        key=pygame.key.name(pygame_event.key),
        keycode=pygame_event.key,
        status=status,
    )


def create_mouse_button_event_from_pygame_event(pygame_event):
    """
    Creates a `MouseButtonEvent` instance from a `pygame` mouse event.

    Args:
        `pygame_event` (`pygame.event.EventType`): The `pygame` event from which to create the `MouseButtonEvent`.

    Returns:
        `MouseButtonEvent`: A new instance of `MouseButtonEvent` initialized with the `pygame` event data.

    Raises:
        `ValueError`: If the provided `pygame` event is not a `PYGAME_MOUSEDOWN` or `PYGAME_MOUSEUP` event.
    """
    if pygame_event.type not in (PYGAME_MOUSEDOWN, PYGAME_MOUSEUP):
        raise ValueError(
            f"The provided pygame event is not a `PYGAME_MOUSEDOWN` or `PYGAME_MOUSEUP` event."
        )

    status = (
        MouseButtonEvent.DOWN
        if pygame_event.type == PYGAME_MOUSEDOWN
        else MouseButtonEvent.UP
    )

    return MouseButtonEvent(
        button=MOUSE_BUTTON_MAP[pygame_event.button],
        position=pygame_event.pos,
        status=status,
        target=[],
    )


def create_mouse_motion_event_from_pygame_event(pygame_event):
    """
    Creates a `MouseMotionEvent` instance from a `pygame` mouse movement event.

    Args:
        `pygame_event` (`pygame.event.EventType`): The `pygame` event from which to create the `MouseMotionEvent`.

    Returns:
        `MouseMotionEvent`: A new instance of `MouseMotionEvent` initialized with the `pygame` event data.

    Raises:
        `ValueError`: If the provided `pygame` event is not a `pyame.MOUSEMOTION` event.
    """
    if pygame_event.type != PYGAME_MOUSEMOTION:
        raise ValueError(
            f"The provided pygame event is not a `PYGAME_MOUSEMOTION` event."
        )
    # TODO target...
    return MouseMotionEvent(
        position=pygame_event.pos, relative=pygame_event.rel, target=[]
    )


EVENT_MAP = {
    PYGAME_KEYDOWN: create_key_event_from_pygame_event,
    PYGAME_KEYUP: create_key_event_from_pygame_event,
    PYGAME_QUIT: create_window_close_event_from_pygame_event,
    PYGAME_MOUSEDOWN: create_mouse_button_event_from_pygame_event,
    PYGAME_MOUSEUP: create_mouse_button_event_from_pygame_event,
    PYGAME_MOUSEMOTION: create_mouse_motion_event_from_pygame_event,
    PYGAME_WINDOWRESIZE: create_window_resize_event_from_pygame_event,
    PYGAME_WINDOWMOVE: create_window_move_event_from_pygame_event,
    PYGAME_WINDOWFOCUS: create_window_focus_event_from_pygame_event,
}
