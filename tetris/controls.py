from typing import Optional

import pygame

from .actions import hard_drop, move_piece, rotate_piece
from .audio import AudioManager
from .state import GameState


def handle_key_down(
    event: pygame.event.Event,
    state: GameState,
    soft_drop_active: bool,
    audio: Optional[AudioManager],
) -> bool:
    locked = False
    if event.key == pygame.K_LEFT:
        move_piece(state, dx=-1, audio=audio)
    elif event.key == pygame.K_RIGHT:
        move_piece(state, dx=1, audio=audio)
    elif event.key == pygame.K_DOWN and not soft_drop_active:
        if move_piece(state, dy=1, audio=audio):
            state.score += 1
    elif event.key == pygame.K_UP:
        rotate_piece(state, 1, audio=audio)
    elif event.key == pygame.K_z:
        rotate_piece(state, -1, audio=audio)
    elif event.key == pygame.K_SPACE:
        locked = hard_drop(state, audio=audio)
    return locked
