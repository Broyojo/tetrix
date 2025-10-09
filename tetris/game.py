from typing import Optional

import pygame

from .actions import hard_drop, move_piece, rotate_piece
from .audio import AudioManager
from .constants import (
    AUTO_REPEAT_INITIAL,
    AUTO_REPEAT_INTERVAL,
    DROP_EVENT,
    FPS,
    MOVE_LEFT_EVENT,
    MOVE_RIGHT_EVENT,
    ROTATE_EVENT,
    SOFT_DROP_EVENT,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from .controls import handle_key_down
from .render import draw
from .state import GameState


def drop_delay_for_level(level: int) -> int:
    return max(100, 800 - (level - 1) * 60)


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Tetris")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 32)
    small_font = pygame.font.Font(None, 24)

    audio = AudioManager()

    state = GameState()
    drop_interval = drop_delay_for_level(state.level)
    pygame.time.set_timer(DROP_EVENT, drop_interval)

    running = True
    soft_drop_active = False
    left_held = right_held = up_held = False
    left_repeat_fast = right_repeat_fast = up_repeat_fast = False

    def stop_directional_repeats() -> None:
        nonlocal left_held, right_held, up_held
        nonlocal left_repeat_fast, right_repeat_fast, up_repeat_fast
        left_held = right_held = up_held = False
        left_repeat_fast = right_repeat_fast = up_repeat_fast = False
        pygame.time.set_timer(MOVE_LEFT_EVENT, 0)
        pygame.time.set_timer(MOVE_RIGHT_EVENT, 0)
        pygame.time.set_timer(ROTATE_EVENT, 0)

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    state.reset()
                    drop_interval = drop_delay_for_level(state.level)
                    pygame.time.set_timer(DROP_EVENT, drop_interval)
                    soft_drop_active = False
                    pygame.time.set_timer(SOFT_DROP_EVENT, 0)
                    stop_directional_repeats()
                elif not state.game_over:
                    locked = handle_key_down(event, state, soft_drop_active, audio)
                    if event.key == pygame.K_DOWN:
                        soft_drop_active = True
                        pygame.time.set_timer(SOFT_DROP_EVENT, 50)
                    if event.key == pygame.K_LEFT and not left_held:
                        left_held = True
                        left_repeat_fast = False
                        pygame.time.set_timer(MOVE_LEFT_EVENT, AUTO_REPEAT_INITIAL)
                    elif event.key == pygame.K_RIGHT and not right_held:
                        right_held = True
                        right_repeat_fast = False
                        pygame.time.set_timer(MOVE_RIGHT_EVENT, AUTO_REPEAT_INITIAL)
                    elif event.key == pygame.K_UP and not up_held:
                        up_held = True
                        up_repeat_fast = False
                        pygame.time.set_timer(ROTATE_EVENT, AUTO_REPEAT_INITIAL)
                    if locked:
                        soft_drop_active = False
                        pygame.time.set_timer(SOFT_DROP_EVENT, 0)
                        drop_interval = drop_delay_for_level(state.level)
                        if state.game_over:
                            pygame.time.set_timer(DROP_EVENT, 0)
                            stop_directional_repeats()
                        else:
                            pygame.time.set_timer(DROP_EVENT, drop_interval)
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    soft_drop_active = False
                    pygame.time.set_timer(SOFT_DROP_EVENT, 0)
                elif event.key == pygame.K_LEFT:
                    left_held = False
                    left_repeat_fast = False
                    pygame.time.set_timer(MOVE_LEFT_EVENT, 0)
                elif event.key == pygame.K_RIGHT:
                    right_held = False
                    right_repeat_fast = False
                    pygame.time.set_timer(MOVE_RIGHT_EVENT, 0)
                elif event.key == pygame.K_UP:
                    up_held = False
                    up_repeat_fast = False
                    pygame.time.set_timer(ROTATE_EVENT, 0)
            elif event.type == DROP_EVENT and not state.game_over:
                if not move_piece(state, dy=1):
                    lines = lock_current_piece(state, audio)
                    drop_interval = drop_delay_for_level(state.level)
                    if state.game_over:
                        pygame.time.set_timer(DROP_EVENT, 0)
                        pygame.time.set_timer(SOFT_DROP_EVENT, 0)
                        soft_drop_active = False
                        stop_directional_repeats()
                    else:
                        pygame.time.set_timer(DROP_EVENT, drop_interval)
            elif event.type == SOFT_DROP_EVENT and soft_drop_active and not state.game_over:
                if move_piece(state, dy=1):
                    state.score += 1
                else:
                    pygame.time.set_timer(SOFT_DROP_EVENT, 0)
                    soft_drop_active = False
            elif event.type == MOVE_LEFT_EVENT:
                if left_held and not state.game_over:
                    move_piece(state, dx=-1, audio=audio)
                    if not left_repeat_fast:
                        pygame.time.set_timer(MOVE_LEFT_EVENT, AUTO_REPEAT_INTERVAL)
                        left_repeat_fast = True
                else:
                    pygame.time.set_timer(MOVE_LEFT_EVENT, 0)
                    left_repeat_fast = False
            elif event.type == MOVE_RIGHT_EVENT:
                if right_held and not state.game_over:
                    move_piece(state, dx=1, audio=audio)
                    if not right_repeat_fast:
                        pygame.time.set_timer(MOVE_RIGHT_EVENT, AUTO_REPEAT_INTERVAL)
                        right_repeat_fast = True
                else:
                    pygame.time.set_timer(MOVE_RIGHT_EVENT, 0)
                    right_repeat_fast = False
            elif event.type == ROTATE_EVENT:
                if up_held and not state.game_over:
                    rotate_piece(state, 1, audio=audio)
                    if not up_repeat_fast:
                        pygame.time.set_timer(ROTATE_EVENT, AUTO_REPEAT_INTERVAL)
                        up_repeat_fast = True
                else:
                    pygame.time.set_timer(ROTATE_EVENT, 0)
                    up_repeat_fast = False

        draw(screen, state, font, small_font)
        pygame.display.flip()

    pygame.quit()


def lock_current_piece(state: GameState, audio: Optional[AudioManager]) -> int:
    lines = state.board.lock_piece(state.current_piece)
    if audio:
        audio.play_lock(lines)
    state.add_score_for_lines(lines)
    state.spawn_next()
    return lines
