from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Sequence, Tuple

import pygame

from .actions import move_piece, rotate_piece
from .audio import AudioManager
from .constants import (
    AUTO_REPEAT_INITIAL,
    AUTO_REPEAT_INTERVAL,
    BOARD_PIXEL_WIDTH,
    FPS,
    SIDE_PANEL,
    WINDOW_HEIGHT,
)
from .controls import ActionResult, InputMapping, handle_key_down
from .render import PlayerView, draw
from .state import GameState


class GameMode(Enum):
    SINGLE = auto()
    MULTI = auto()


def drop_delay_for_level(level: int) -> int:
    return max(100, 800 - (level - 1) * 60)


@dataclass
class PlayerRuntime:
    label: str
    state: GameState
    mapping: InputMapping
    origin: Tuple[int, int]
    controls_hint: Sequence[str]
    drop_event: int
    soft_drop_event: int
    move_left_event: int
    move_right_event: int
    rotate_event: int
    soft_drop_active: bool = False
    left_held: bool = False
    right_held: bool = False
    rotate_held: bool = False
    left_repeat_fast: bool = False
    right_repeat_fast: bool = False
    rotate_repeat_fast: bool = False

    def reset(self) -> None:
        self.state = GameState()
        self.soft_drop_active = False
        self.left_held = self.right_held = self.rotate_held = False
        self.left_repeat_fast = self.right_repeat_fast = self.rotate_repeat_fast = False
        self.set_drop_timer(drop_delay_for_level(self.state.level))
        pygame.time.set_timer(self.soft_drop_event, 0)
        self.stop_repeat_timers()

    def set_drop_timer(self, interval: int) -> None:
        pygame.time.set_timer(self.drop_event, interval)

    def stop_drop_timer(self) -> None:
        pygame.time.set_timer(self.drop_event, 0)

    def stop_soft_drop(self) -> None:
        self.soft_drop_active = False
        pygame.time.set_timer(self.soft_drop_event, 0)

    def stop_repeat_timers(self) -> None:
        pygame.time.set_timer(self.move_left_event, 0)
        pygame.time.set_timer(self.move_right_event, 0)
        pygame.time.set_timer(self.rotate_event, 0)

    def apply_pending_garbage(self) -> None:
        self.state.apply_pending_garbage()


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Tetris")
    base_width = BOARD_PIXEL_WIDTH + SIDE_PANEL + 60
    screen = pygame.display.set_mode((base_width, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 32)
    small_font = pygame.font.Font(None, 24)
    title_font = pygame.font.Font(None, 64)

    audio = AudioManager()

    running = True
    while running:
        mode = show_menu(screen, clock, title_font, font, small_font)
        if mode is None:
            break
        running = run_game(screen, clock, font, small_font, audio, mode)

    pygame.quit()


def window_size_for_mode(mode: GameMode) -> Tuple[int, int]:
    if mode == GameMode.SINGLE:
        width = BOARD_PIXEL_WIDTH + SIDE_PANEL + 60
    else:
        width = 2 * (BOARD_PIXEL_WIDTH + SIDE_PANEL) + 100
    return width, WINDOW_HEIGHT


def create_player_runtime(
    label: str,
    mapping: InputMapping,
    origin: Tuple[int, int],
    controls_hint: Sequence[str],
) -> PlayerRuntime:
    runtime = PlayerRuntime(
        label=label,
        state=GameState(),
        mapping=mapping,
        origin=origin,
        controls_hint=controls_hint,
        drop_event=pygame.event.custom_type(),
        soft_drop_event=pygame.event.custom_type(),
        move_left_event=pygame.event.custom_type(),
        move_right_event=pygame.event.custom_type(),
        rotate_event=pygame.event.custom_type(),
    )
    runtime.set_drop_timer(drop_delay_for_level(runtime.state.level))
    return runtime


def run_game(
    screen: pygame.Surface,
    clock: pygame.time.Clock,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    audio: AudioManager,
    mode: GameMode,
) -> bool:
    width, height = window_size_for_mode(mode)
    screen = pygame.display.set_mode((width, height))

    player_runtimes = create_players(mode)

    event_map: Dict[int, Tuple[str, PlayerRuntime]] = {}
    for runtime in player_runtimes:
        event_map[runtime.drop_event] = ("drop", runtime)
        event_map[runtime.soft_drop_event] = ("soft_drop", runtime)
        event_map[runtime.move_left_event] = ("move_left", runtime)
        event_map[runtime.move_right_event] = ("move_right", runtime)
        event_map[runtime.rotate_event] = ("rotate", runtime)

    running = True
    return_to_menu = False

    while running:
        clock.tick(FPS)
        for runtime in player_runtimes:
            runtime.apply_pending_garbage()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return_to_menu = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    return_to_menu = True
                    break
                elif event.key == pygame.K_r:
                    for runtime in player_runtimes:
                        runtime.reset()
                    continue

                for idx, runtime in enumerate(player_runtimes):
                    state = runtime.state
                    if state.game_over:
                        continue
                    result = handle_key_down(
                        event,
                        state,
                        runtime.soft_drop_active,
                        audio,
                        runtime.mapping,
                    )
                    if result is not None:
                        lines = result.lines_cleared
                        process_locked_piece(
                            idx,
                            runtime,
                            lines,
                            player_runtimes,
                            mode,
                            already_advanced=result.handled_lock,
                        )
                        runtime.stop_soft_drop()
                        if runtime.state.game_over:
                            runtime.stop_drop_timer()
                            runtime.stop_repeat_timers()
                        else:
                            runtime.set_drop_timer(drop_delay_for_level(runtime.state.level))

                    mapping = runtime.mapping
                    if event.key == mapping.down:
                        runtime.soft_drop_active = True
                        pygame.time.set_timer(runtime.soft_drop_event, 50)
                    elif event.key == mapping.left and not runtime.left_held:
                        runtime.left_held = True
                        runtime.left_repeat_fast = False
                        pygame.time.set_timer(runtime.move_left_event, AUTO_REPEAT_INITIAL)
                    elif event.key == mapping.right and not runtime.right_held:
                        runtime.right_held = True
                        runtime.right_repeat_fast = False
                        pygame.time.set_timer(runtime.move_right_event, AUTO_REPEAT_INITIAL)
                    elif event.key == mapping.rotate_cw and not runtime.rotate_held:
                        runtime.rotate_held = True
                        runtime.rotate_repeat_fast = False
                        pygame.time.set_timer(runtime.rotate_event, AUTO_REPEAT_INITIAL)

            elif event.type == pygame.KEYUP:
                for runtime in player_runtimes:
                    mapping = runtime.mapping
                    if event.key == mapping.down:
                        runtime.stop_soft_drop()
                    elif event.key == mapping.left:
                        runtime.left_held = False
                        runtime.left_repeat_fast = False
                        pygame.time.set_timer(runtime.move_left_event, 0)
                    elif event.key == mapping.right:
                        runtime.right_held = False
                        runtime.right_repeat_fast = False
                        pygame.time.set_timer(runtime.move_right_event, 0)
                    elif event.key == mapping.rotate_cw:
                        runtime.rotate_held = False
                        runtime.rotate_repeat_fast = False
                        pygame.time.set_timer(runtime.rotate_event, 0)

            elif event.type in event_map:
                action, runtime = event_map[event.type]
                state = runtime.state
                if state.game_over:
                    continue
                if action == "drop":
                    if not move_piece(state, dy=1):
                        lines = lock_current_piece(state, audio)
                        process_locked_piece(
                            player_runtimes.index(runtime),
                            runtime,
                            lines,
                            player_runtimes,
                            mode,
                            already_advanced=False,
                        )
                        if state.game_over:
                            runtime.stop_drop_timer()
                            runtime.stop_soft_drop()
                            runtime.stop_repeat_timers()
                        else:
                            runtime.set_drop_timer(drop_delay_for_level(state.level))
                elif action == "soft_drop" and runtime.soft_drop_active:
                    if move_piece(state, dy=1):
                        state.score += 1
                    else:
                        runtime.stop_soft_drop()
                elif action == "move_left":
                    if runtime.left_held and not state.game_over:
                        move_piece(state, dx=-1, audio=audio)
                        if not runtime.left_repeat_fast:
                            pygame.time.set_timer(runtime.move_left_event, AUTO_REPEAT_INTERVAL)
                            runtime.left_repeat_fast = True
                    else:
                        pygame.time.set_timer(runtime.move_left_event, 0)
                        runtime.left_repeat_fast = False
                elif action == "move_right":
                    if runtime.right_held and not state.game_over:
                        move_piece(state, dx=1, audio=audio)
                        if not runtime.right_repeat_fast:
                            pygame.time.set_timer(runtime.move_right_event, AUTO_REPEAT_INTERVAL)
                            runtime.right_repeat_fast = True
                    else:
                        pygame.time.set_timer(runtime.move_right_event, 0)
                        runtime.right_repeat_fast = False
                elif action == "rotate":
                    if runtime.rotate_held and not state.game_over:
                        rotate_piece(state, 1, audio=audio)
                        if not runtime.rotate_repeat_fast:
                            pygame.time.set_timer(runtime.rotate_event, AUTO_REPEAT_INTERVAL)
                            runtime.rotate_repeat_fast = True
                    else:
                        pygame.time.set_timer(runtime.rotate_event, 0)
                        runtime.rotate_repeat_fast = False

        player_views = [
            PlayerView(
                state=runtime.state,
                label=runtime.label,
                origin=runtime.origin,
                controls=runtime.controls_hint,
            )
            for runtime in player_runtimes
        ]
        draw(screen, player_views, font, small_font)
        pygame.display.flip()

    if return_to_menu:
        return True
    return False


def create_players(mode: GameMode) -> List[PlayerRuntime]:
    base_origin = (20, 0)

    arrow_controls = [
        "←/→ move",
        "↓ soft drop",
        "↑ rotate, Z ccw",
        "Space hard drop",
        "R restart",
        "Esc menu",
    ]
    arrow_mapping = InputMapping(
        left=pygame.K_LEFT,
        right=pygame.K_RIGHT,
        down=pygame.K_DOWN,
        rotate_cw=pygame.K_UP,
        rotate_ccw=pygame.K_z,
        hard_drop=pygame.K_SPACE,
    )

    if mode == GameMode.SINGLE:
        return [
            create_player_runtime(
                label="Player 1",
                mapping=arrow_mapping,
                origin=base_origin,
                controls_hint=arrow_controls,
            )
        ]

    spacing = BOARD_PIXEL_WIDTH + SIDE_PANEL + 40
    wasd_controls = [
        "A/D move",
        "S soft drop",
        "W rotate, Q ccw",
        "Left Shift hard drop",
        "R restart",
        "Esc menu",
    ]
    wasd_mapping = InputMapping(
        left=pygame.K_a,
        right=pygame.K_d,
        down=pygame.K_s,
        rotate_cw=pygame.K_w,
        rotate_ccw=pygame.K_q,
        hard_drop=pygame.K_LSHIFT,
    )

    left_player = create_player_runtime(
        label="Player 1 (WASD)",
        mapping=wasd_mapping,
        origin=base_origin,
        controls_hint=wasd_controls,
    )
    right_player = create_player_runtime(
        label="Player 2 (Arrows)",
        mapping=arrow_mapping,
        origin=(base_origin[0] + spacing, base_origin[1]),
        controls_hint=arrow_controls,
    )

    return [left_player, right_player]


def process_locked_piece(
    player_index: int,
    runtime: PlayerRuntime,
    lines: int,
    players: Sequence[PlayerRuntime],
    mode: GameMode,
    already_advanced: bool,
) -> None:
    if lines < 0:
        lines = 0
    if not already_advanced:
        runtime.state.add_score_for_lines(lines)
        runtime.state.spawn_next()
        if runtime.state.game_over:
            runtime.stop_drop_timer()
            runtime.stop_soft_drop()
            runtime.stop_repeat_timers()

    if runtime.state.game_over:
        runtime.stop_drop_timer()
        runtime.stop_soft_drop()
        runtime.stop_repeat_timers()

    if mode == GameMode.MULTI and lines > 0:
        garbage = max(0, lines - 1)
        if garbage > 0:
            for idx, other in enumerate(players):
                if idx == player_index:
                    continue
                if not other.state.game_over:
                    other.state.queue_garbage(garbage)


def lock_current_piece(state: GameState, audio: Optional[AudioManager]) -> int:
    lines = state.board.lock_piece(state.current_piece)
    if audio:
        audio.play_lock(lines)
    return lines


def show_menu(
    screen: pygame.Surface,
    clock: pygame.time.Clock,
    title_font: pygame.font.Font,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
) -> Optional[GameMode]:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key in (pygame.K_1, pygame.K_KP1):
                    return GameMode.SINGLE
                if event.key in (pygame.K_2, pygame.K_KP2):
                    return GameMode.MULTI

        screen.fill((10, 10, 16))
        title = title_font.render("Tetris", True, (240, 240, 240))
        subtitle = font.render("Press 1 for Single Player", True, (200, 200, 200))
        subtitle2 = font.render("Press 2 for Battle", True, (200, 200, 200))
        info = small_font.render("Esc to quit", True, (160, 160, 160))

        screen.blit(title, title.get_rect(center=(screen.get_width() // 2, 120)))
        screen.blit(subtitle, subtitle.get_rect(center=(screen.get_width() // 2, 220)))
        screen.blit(subtitle2, subtitle2.get_rect(center=(screen.get_width() // 2, 270)))
        screen.blit(info, info.get_rect(center=(screen.get_width() // 2, 340)))
        pygame.display.flip()
        clock.tick(60)
