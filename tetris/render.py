from dataclasses import dataclass
from typing import Sequence, Tuple

import pygame

from .board import Board
from .constants import (
    BLOCK_SIZE,
    BOARD_HEIGHT,
    BOARD_PIXEL_WIDTH,
    BOARD_WIDTH,
    PIECE_COLORS,
    WINDOW_HEIGHT,
)
from .pieces import Tetromino
from .state import GameState


@dataclass
class PlayerView:
    state: GameState
    label: str
    origin: Tuple[int, int]
    controls: Sequence[str]


def draw(
    screen: pygame.Surface,
    players: Sequence[PlayerView],
    font: pygame.font.Font,
    small_font: pygame.font.Font,
) -> None:
    screen.fill((12, 12, 12))
    for view in players:
        draw_player_area(screen, view, font, small_font)


def draw_player_area(
    screen: pygame.Surface,
    view: PlayerView,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
) -> None:
    origin_x, origin_y = view.origin
    state = view.state
    draw_board(screen, state.board, origin_x, origin_y)
    draw_ghost_piece(screen, state.board, state.current_piece, origin_x, origin_y)
    draw_piece(
        screen,
        state.current_piece,
        PIECE_COLORS[state.current_piece.shape_key],
        origin_x,
        origin_y,
    )
    draw_sidebar(
        screen,
        state,
        font,
        small_font,
        origin_x,
        origin_y,
        view.label,
        view.controls,
    )
    draw_grid(screen, origin_x, origin_y)
    if state.game_over:
        draw_game_over(screen, font, origin_x, origin_y)


def draw_board(
    screen: pygame.Surface, board: Board, offset_x: int, offset_y: int
) -> None:
    for y in range(BOARD_HEIGHT):
        for x in range(BOARD_WIDTH):
            color = board.grid[y][x]
            if color:
                pygame.draw.rect(
                    screen,
                    color,
                    pygame.Rect(
                        offset_x + x * BLOCK_SIZE,
                        offset_y + y * BLOCK_SIZE,
                        BLOCK_SIZE,
                        BLOCK_SIZE,
                    ),
                )


def draw_piece(
    screen: pygame.Surface,
    piece: Tetromino,
    color: Tuple[int, int, int],
    offset_x: int,
    offset_y: int,
) -> None:
    for cx, cy in piece.cells():
        board_y = piece.y + cy
        if board_y < 0:
            continue
        px = offset_x + (piece.x + cx) * BLOCK_SIZE
        py = offset_y + board_y * BLOCK_SIZE
        pygame.draw.rect(screen, color, pygame.Rect(px, py, BLOCK_SIZE, BLOCK_SIZE))


def draw_ghost_piece(
    screen: pygame.Surface,
    board: Board,
    piece: Tetromino,
    offset_x: int,
    offset_y: int,
) -> None:
    offset = 0
    while board.valid(piece, dy=offset + 1):
        offset += 1
    ghost_y = piece.y + offset
    base_color = PIECE_COLORS[piece.shape_key]
    fill_color = (*base_color, 80)
    outline_color = tuple(min(255, c + 60) for c in base_color)
    ghost_cell_surface = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
    ghost_cell_surface.fill(fill_color)
    for cx, cy in piece.cells():
        board_y = ghost_y + cy
        if board_y < 0:
            continue
        px = offset_x + (piece.x + cx) * BLOCK_SIZE
        py = offset_y + board_y * BLOCK_SIZE
        screen.blit(ghost_cell_surface, (px, py))
        pygame.draw.rect(
            screen,
            outline_color,
            pygame.Rect(px, py, BLOCK_SIZE, BLOCK_SIZE),
            2,
        )


def draw_sidebar(
    screen: pygame.Surface,
    state: GameState,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    offset_x: int,
    offset_y: int,
    label: str,
    controls_hint: Sequence[str],
) -> None:
    panel_x = offset_x + BOARD_PIXEL_WIDTH + 20
    score_text = font.render(f"{label}", True, (255, 255, 255))
    screen.blit(score_text, (panel_x, offset_y + 10))

    stats = [
        f"Score: {state.score}",
        f"Level: {state.level}",
        f"Lines: {state.board.lines_cleared}",
    ]
    y = offset_y + 60
    for text in stats:
        surface = font.render(text, True, (240, 240, 240))
        screen.blit(surface, (panel_x, y))
        y += 40

    next_label = font.render("Next", True, (240, 240, 240))
    screen.blit(next_label, (panel_x, y))
    draw_next_piece_preview(screen, state.next_piece, (panel_x, y + 40))

    y = offset_y + WINDOW_HEIGHT - 150
    for text in controls_hint:
        surface = small_font.render(text, True, (160, 160, 160))
        screen.blit(surface, (panel_x, y))
        y += 24


def draw_next_piece_preview(
    screen: pygame.Surface, piece: Tetromino, top_left: Tuple[int, int]
) -> None:
    preview_x, preview_y = top_left
    from .pieces import TETROMINO_SHAPES

    layout = TETROMINO_SHAPES[piece.shape_key][0]
    color = PIECE_COLORS[piece.shape_key]
    for row_idx, row in enumerate(layout):
        for col_idx, char in enumerate(row):
            if char == "X":
                rect = pygame.Rect(
                    preview_x + col_idx * (BLOCK_SIZE // 2),
                    preview_y + row_idx * (BLOCK_SIZE // 2),
                    BLOCK_SIZE // 2,
                    BLOCK_SIZE // 2,
                )
                pygame.draw.rect(screen, color, rect)


def draw_grid(screen: pygame.Surface, offset_x: int, offset_y: int) -> None:
    for x in range(BOARD_WIDTH + 1):
        start_pos = (offset_x + x * BLOCK_SIZE, offset_y)
        end_pos = (offset_x + x * BLOCK_SIZE, offset_y + BOARD_HEIGHT * BLOCK_SIZE)
        pygame.draw.line(screen, (40, 40, 40), start_pos, end_pos)
    for y in range(BOARD_HEIGHT + 1):
        start_pos = (offset_x, offset_y + y * BLOCK_SIZE)
        end_pos = (offset_x + BOARD_WIDTH * BLOCK_SIZE, offset_y + y * BLOCK_SIZE)
        pygame.draw.line(screen, (40, 40, 40), start_pos, end_pos)


def draw_game_over(
    screen: pygame.Surface, font: pygame.font.Font, offset_x: int, offset_y: int
) -> None:
    overlay = pygame.Surface(
        (BOARD_WIDTH * BLOCK_SIZE, BOARD_HEIGHT * BLOCK_SIZE), pygame.SRCALPHA
    )
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (offset_x, offset_y))
    text = font.render("Game Over - Press R", True, (250, 250, 250))
    text_rect = text.get_rect(
        center=(offset_x + BOARD_PIXEL_WIDTH // 2, offset_y + WINDOW_HEIGHT // 2)
    )
    screen.blit(text, text_rect)
