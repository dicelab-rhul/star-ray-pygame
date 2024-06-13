"""Defines functions to create `star_ray` events from pygame events."""

# pylint: disable=E1101
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

# Constant values
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
PYGAME_WINDOWCLOSE = PYGAME_QUIT  # Alias for PYGAME_QUIT

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
) -> WindowMoveEvent:
    """Creates a `WindowMoveEvent` from a `pygame` window move event."""
    if pygame_event.type != PYGAME_WINDOWMOVE:
        raise ValueError(
            "The provided pygame event is not a `PYGAME_WINDOWMOVE` event."
        )
    return WindowMoveEvent(position=pygame_event.position)


def create_window_focus_event_from_pygame_event(
    pygame_event: EventType,
) -> WindowFocusEvent:
    """Creates a `WindowFocusEvent` from a `pygame` window focus event."""
    if pygame_event.type != PYGAME_WINDOWFOCUS:
        raise ValueError(
            "The provided pygame event is not a `PYGAME_WINDOWFOCUS` event."
        )
    return WindowFocusEvent(has_focus=pygame_event.has_focus)


def create_window_resize_event_from_pygame_event(
    pygame_event: EventType,
) -> WindowResizeEvent:
    """Creates a `WindowResizeEvent` from a `pygame` window resize event."""
    if pygame_event.type != PYGAME_WINDOWRESIZE:
        raise ValueError(
            "The provided pygame event is not a `PYGAME_WINDOWRESIZE` event."
        )
    return WindowResizeEvent(size=tuple(pygame_event.size))


def create_window_close_event_from_pygame_event(
    pygame_event: EventType,
) -> WindowCloseEvent:
    """Creates an `WindowCloseEvent` from a `pygame` window close event."""
    if pygame_event.type != PYGAME_QUIT:
        raise ValueError("The provided pygame event is not a `PYGAME_QUIT` event.")
    return WindowCloseEvent()


def create_window_open_event_from_pygame_event(
    pygame_event: EventType,
) -> WindowOpenEvent:
    """Creates an `WindowOpenEvent` from a `pygame` window open event."""
    if pygame_event.type != PYGAME_WINDOWOPEN:
        raise ValueError(
            "The provided pygame event is not a `PYGAME_WINDOWOPEN` event."
        )
    return WindowOpenEvent()


def create_key_event_from_pygame_event(pygame_event: EventType) -> KeyEvent:
    """Creates a `KeyEvent` instance from a `pygame` keyboard event."""
    if pygame_event.type not in (PYGAME_KEYDOWN, PYGAME_KEYUP):
        raise ValueError(
            "The provided pygame event is not a `KEYDOWN` or `KEYUP` event."
        )
    status = KeyEvent.DOWN if pygame_event.type == PYGAME_KEYDOWN else KeyEvent.UP
    return KeyEvent(
        key=pygame.key.name(pygame_event.key), keycode=pygame_event.key, status=status
    )


def create_mouse_button_event_from_pygame_event(
    pygame_event: EventType,
) -> MouseButtonEvent:
    """Creates a `MouseButtonEvent` instance from a `pygame` mouse event."""
    if pygame_event.type not in (PYGAME_MOUSEDOWN, PYGAME_MOUSEUP):
        raise ValueError(
            "The provided pygame event is not a `MOUSEDOWN` or `MOUSEUP` event."
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
    )


def create_mouse_motion_event_from_pygame_event(
    pygame_event: EventType,
) -> MouseMotionEvent:
    """Creates a `MouseMotionEvent` instance from a `pygame` mouse movement event."""
    if pygame_event.type != PYGAME_MOUSEMOTION:
        raise ValueError("The provided pygame event is not a `MOUSEMOTION` event.")
    return MouseMotionEvent(position=pygame_event.pos, relative=pygame_event.rel)


# Dictionary mapping pygame event types to corresponding event creation functions
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
