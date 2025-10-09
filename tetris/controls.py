from dataclasses import dataclass
from typing import Optional

import pygame

from .actions import hard_drop, move_piece, rotate_piece
from .audio import AudioManager
from .state import GameState


@dataclass(frozen=True)
class InputMapping:
    left: int
    right: int
    down: int
    rotate_cw: int
    rotate_ccw: Optional[int]
    hard_drop: int


@dataclass
class ActionResult:
    lines_cleared: int
    handled_lock: bool


def handle_key_down(
    event: pygame.event.Event,
    state: GameState,
    soft_drop_active: bool,
    audio: Optional[AudioManager],
    mapping: InputMapping,
) -> Optional[ActionResult]:
    if event.key == mapping.left:
        move_piece(state, dx=-1, audio=audio)
    elif event.key == mapping.right:
        move_piece(state, dx=1, audio=audio)
    elif event.key == mapping.down and not soft_drop_active:
        if move_piece(state, dy=1, audio=audio):
            state.score += 1
    elif event.key == mapping.rotate_cw:
        rotate_piece(state, 1, audio=audio)
    elif mapping.rotate_ccw is not None and event.key == mapping.rotate_ccw:
        rotate_piece(state, -1, audio=audio)
    elif event.key == mapping.hard_drop:
        lines = hard_drop(state, audio=audio)
        return ActionResult(lines_cleared=lines, handled_lock=True)
    return None
