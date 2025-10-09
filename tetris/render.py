from typing import Tuple

import pygame

from .board import Board
from .constants import BLOCK_SIZE, BOARD_HEIGHT, BOARD_WIDTH, PIECE_COLORS, WINDOW_HEIGHT
from .pieces import Tetromino
from .state import GameState


def draw(screen: pygame.Surface, state: GameState, font: pygame.font.Font, small_font: pygame.font.Font) -> None:
    screen.fill((12, 12, 12))
    draw_board(screen, state.board)
    draw_ghost_piece(screen, state.board, state.current_piece)
    draw_piece(screen, state.current_piece, PIECE_COLORS[state.current_piece.shape_key])
    draw_sidebar(screen, state, font, small_font)
    draw_grid(screen)
    if state.game_over:
        draw_game_over(screen, font)


def draw_board(screen: pygame.Surface, board: Board) -> None:
    for y in range(BOARD_HEIGHT):
        for x in range(BOARD_WIDTH):
            color = board.grid[y][x]
            if color:
                pygame.draw.rect(
                    screen,
                    color,
                    pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE),
                )


def draw_piece(screen: pygame.Surface, piece: Tetromino, color: Tuple[int, int, int]) -> None:
    for cx, cy in piece.cells():
        board_y = piece.y + cy
        if board_y < 0:
            continue
        px = (piece.x + cx) * BLOCK_SIZE
        py = board_y * BLOCK_SIZE
        pygame.draw.rect(screen, color, pygame.Rect(px, py, BLOCK_SIZE, BLOCK_SIZE))


def draw_ghost_piece(screen: pygame.Surface, board: Board, piece: Tetromino) -> None:
    offset = 0
    while board.valid(piece, dy=offset + 1):
        offset += 1
    ghost_y = piece.y + offset
    ghost_color = tuple(max(0, c - 100) for c in PIECE_COLORS[piece.shape_key])
    for cx, cy in piece.cells():
        board_y = ghost_y + cy
        if board_y < 0:
            continue
        px = (piece.x + cx) * BLOCK_SIZE
        py = board_y * BLOCK_SIZE
        pygame.draw.rect(
            screen,
            ghost_color,
            pygame.Rect(px, py, BLOCK_SIZE, BLOCK_SIZE),
            1,
        )


def draw_sidebar(screen: pygame.Surface, state: GameState, font: pygame.font.Font, small_font: pygame.font.Font) -> None:
    offset_x = BOARD_WIDTH * BLOCK_SIZE + 20
    score_text = font.render(f"Score: {state.score}", True, (240, 240, 240))
    level_text = font.render(f"Level: {state.level}", True, (240, 240, 240))
    lines_text = font.render(f"Lines: {state.board.lines_cleared}", True, (240, 240, 240))
    screen.blit(score_text, (offset_x, 30))
    screen.blit(level_text, (offset_x, 70))
    screen.blit(lines_text, (offset_x, 110))

    next_label = font.render("Next", True, (240, 240, 240))
    screen.blit(next_label, (offset_x, 170))
    draw_next_piece_preview(screen, state.next_piece, (offset_x, 210))

    controls = [
        "←/→ move",
        "↑ rotate",
        "Z ccw rotate",
        "↓ soft drop",
        "Space hard drop",
        "R restart",
        "Esc quit",
    ]
    y = WINDOW_HEIGHT - 160
    for text in controls:
        surface = small_font.render(text, True, (160, 160, 160))
        screen.blit(surface, (offset_x, y))
        y += 24


def draw_next_piece_preview(screen: pygame.Surface, piece: Tetromino, top_left: Tuple[int, int]) -> None:
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


def draw_grid(screen: pygame.Surface) -> None:
    for x in range(BOARD_WIDTH + 1):
        start_pos = (x * BLOCK_SIZE, 0)
        end_pos = (x * BLOCK_SIZE, BOARD_HEIGHT * BLOCK_SIZE)
        pygame.draw.line(screen, (40, 40, 40), start_pos, end_pos)
    for y in range(BOARD_HEIGHT + 1):
        start_pos = (0, y * BLOCK_SIZE)
        end_pos = (BOARD_WIDTH * BLOCK_SIZE, y * BLOCK_SIZE)
        pygame.draw.line(screen, (40, 40, 40), start_pos, end_pos)


def draw_game_over(screen: pygame.Surface, font: pygame.font.Font) -> None:
    overlay = pygame.Surface((BOARD_WIDTH * BLOCK_SIZE, BOARD_HEIGHT * BLOCK_SIZE), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    text = font.render("Game Over - Press R", True, (250, 250, 250))
    text_rect = text.get_rect(center=(BOARD_WIDTH * BLOCK_SIZE // 2, BOARD_HEIGHT * BLOCK_SIZE // 2))
    screen.blit(text, text_rect)
