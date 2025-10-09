import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pygame


BOARD_WIDTH = 10
BOARD_HEIGHT = 20
BLOCK_SIZE = 32
SIDE_PANEL = 200
WINDOW_WIDTH = BOARD_WIDTH * BLOCK_SIZE + SIDE_PANEL
WINDOW_HEIGHT = BOARD_HEIGHT * BLOCK_SIZE
FPS = 60
DROP_EVENT = pygame.USEREVENT + 1
SOFT_DROP_EVENT = pygame.USEREVENT + 2

TETROMINO_SHAPES: Dict[str, Sequence[Sequence[str]]] = {
    "I": (
        ("....", "XXXX", "....", "...."),
        ("..X.", "..X.", "..X.", "..X."),
    ),
    "O": (
        (".XX.", ".XX.", "....", "...."),
    ),
    "T": (
        (".X..", "XXX.", "....", "...."),
        (".X..", ".XX.", ".X..", "...."),
        ("....", "XXX.", ".X..", "...."),
        (".X..", "XX..", ".X..", "...."),
    ),
    "S": (
        ("..XX", ".XX.", "....", "...."),
        (".X..", ".XX.", "..X.", "...."),
    ),
    "Z": (
        (".XX.", "..XX", "....", "...."),
        ("..X.", ".XX.", ".X..", "...."),
    ),
    "J": (
        ("X...", "XXX.", "....", "...."),
        (".XX.", ".X..", ".X..", "...."),
        ("....", "XXX.", "..X.", "...."),
        (".X..", ".X..", "XX..", "...."),
    ),
    "L": (
        ("..X.", "XXX.", "....", "...."),
        (".X..", ".X..", ".XX.", "...."),
        ("....", "XXX.", "X...", "...."),
        ("XX..", ".X..", ".X..", "...."),
    ),
}

PIECE_COLORS: Dict[str, Tuple[int, int, int]] = {
    "I": (0, 240, 240),
    "O": (240, 240, 0),
    "T": (160, 0, 240),
    "S": (0, 240, 0),
    "Z": (240, 0, 0),
    "J": (0, 0, 240),
    "L": (240, 160, 0),
}

SCORES_PER_LINE = {1: 100, 2: 300, 3: 500, 4: 800}


@dataclass
class Tetromino:
    shape_key: str
    rotation: int = 0
    x: int = BOARD_WIDTH // 2 - 2
    y: int = 0

    def cells(self, rotation: Optional[int] = None) -> Iterable[Tuple[int, int]]:
        rot = self._normalized_rotation(rotation)
        layout = TETROMINO_SHAPES[self.shape_key][rot]
        for row_idx, row in enumerate(layout):
            for col_idx, char in enumerate(row):
                if char == "X":
                    yield col_idx, row_idx

    def rotated(self, direction: int) -> int:
        return self._normalized_rotation(self.rotation + direction)

    def rotate(self, direction: int) -> None:
        self.rotation = self.rotated(direction)

    def _normalized_rotation(self, rotation: Optional[int]) -> int:
        options = len(TETROMINO_SHAPES[self.shape_key])
        return (self.rotation if rotation is None else rotation) % options


class Board:
    def __init__(self) -> None:
        self.grid: List[List[Optional[Tuple[int, int, int]]]] = [
            [None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)
        ]
        self.lines_cleared = 0

    def valid(self, piece: Tetromino, dx: int = 0, dy: int = 0, rotation: Optional[int] = None) -> bool:
        rot = piece._normalized_rotation(rotation)
        for cx, cy in piece.cells(rot):
            px = piece.x + cx + dx
            py = piece.y + cy + dy
            if px < 0 or px >= BOARD_WIDTH or py >= BOARD_HEIGHT:
                return False
            if py >= 0 and self.grid[py][px]:
                return False
        return True

    def lock_piece(self, piece: Tetromino) -> int:
        for cx, cy in piece.cells():
            px = piece.x + cx
            py = piece.y + cy
            if 0 <= px < BOARD_WIDTH and 0 <= py < BOARD_HEIGHT:
                self.grid[py][px] = PIECE_COLORS[piece.shape_key]
        lines = self._clear_lines()
        self.lines_cleared += lines
        return lines

    def _clear_lines(self) -> int:
        new_grid = [row for row in self.grid if any(cell is None for cell in row)]
        cleared = BOARD_HEIGHT - len(new_grid)
        while len(new_grid) < BOARD_HEIGHT:
            new_grid.insert(0, [None for _ in range(BOARD_WIDTH)])
        self.grid = new_grid
        return cleared

    def occupied(self, x: int, y: int) -> bool:
        return 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT and self.grid[y][x] is not None


class GameState:
    def __init__(self) -> None:
        self.board = Board()
        self.current_piece = self._make_piece()
        self.next_piece = self._make_piece()
        self.score = 0
        self.level = 1
        self.game_over = False

    def _make_piece(self) -> Tetromino:
        return Tetromino(random.choice(list(TETROMINO_SHAPES)))

    def reset(self) -> None:
        self.__init__()

    def spawn_next(self) -> None:
        self.current_piece = self.next_piece
        self.next_piece = self._make_piece()
        self.current_piece.rotation = 0
        self.current_piece.x = BOARD_WIDTH // 2 - 2
        self.current_piece.y = 0
        if not self.board.valid(self.current_piece):
            self.game_over = True

    def add_score_for_lines(self, lines: int) -> None:
        if not lines:
            return
        self.score += SCORES_PER_LINE.get(lines, lines * 100)
        self.level = self.board.lines_cleared // 10 + 1


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Tetris")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 32)
    small_font = pygame.font.Font(None, 24)

    state = GameState()
    drop_interval = drop_delay_for_level(state.level)
    pygame.time.set_timer(DROP_EVENT, drop_interval)

    running = True
    soft_drop_active = False

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
                elif not state.game_over:
                    locked = handle_key_down(event, state, soft_drop_active)
                    if event.key == pygame.K_DOWN:
                        soft_drop_active = True
                        pygame.time.set_timer(SOFT_DROP_EVENT, 50)
                    if locked:
                        soft_drop_active = False
                        pygame.time.set_timer(SOFT_DROP_EVENT, 0)
                        drop_interval = drop_delay_for_level(state.level)
                        if state.game_over:
                            pygame.time.set_timer(DROP_EVENT, 0)
                        else:
                            pygame.time.set_timer(DROP_EVENT, drop_interval)
            elif event.type == pygame.KEYUP and event.key == pygame.K_DOWN:
                soft_drop_active = False
                pygame.time.set_timer(SOFT_DROP_EVENT, 0)
            elif event.type == DROP_EVENT and not state.game_over:
                if not move_piece(state, dy=1):
                    lines = state.board.lock_piece(state.current_piece)
                    state.add_score_for_lines(lines)
                    state.spawn_next()
                    drop_interval = drop_delay_for_level(state.level)
                    if state.game_over:
                        pygame.time.set_timer(DROP_EVENT, 0)
                        pygame.time.set_timer(SOFT_DROP_EVENT, 0)
                        soft_drop_active = False
                    else:
                        pygame.time.set_timer(DROP_EVENT, drop_interval)
            elif event.type == SOFT_DROP_EVENT and soft_drop_active and not state.game_over:
                if move_piece(state, dy=1):
                    state.score += 1
                else:
                    pygame.time.set_timer(SOFT_DROP_EVENT, 0)
                    soft_drop_active = False

        draw(screen, state, font, small_font)
        pygame.display.flip()

    pygame.quit()


def handle_key_down(event: pygame.event.Event, state: GameState, soft_drop_active: bool) -> bool:
    locked = False
    if event.key == pygame.K_LEFT:
        move_piece(state, dx=-1)
    elif event.key == pygame.K_RIGHT:
        move_piece(state, dx=1)
    elif event.key == pygame.K_DOWN and not soft_drop_active:
        if move_piece(state, dy=1):
            state.score += 1
    elif event.key == pygame.K_UP:
        rotate_piece(state, 1)
    elif event.key == pygame.K_z:
        rotate_piece(state, -1)
    elif event.key == pygame.K_SPACE:
        locked = hard_drop(state)
    return locked


def move_piece(state: GameState, dx: int = 0, dy: int = 0) -> bool:
    piece = state.current_piece
    if state.board.valid(piece, dx=dx, dy=dy):
        piece.x += dx
        piece.y += dy
        return True
    return False


def rotate_piece(state: GameState, direction: int) -> None:
    piece = state.current_piece
    target_rotation = piece.rotated(direction)
    kicks = [(0, 0), (-1, 0), (1, 0), (0, -1)]
    for dx, dy in kicks:
        if state.board.valid(piece, dx=dx, dy=dy, rotation=target_rotation):
            piece.rotation = target_rotation
            piece.x += dx
            piece.y += dy
            return


def hard_drop(state: GameState) -> bool:
    piece = state.current_piece
    distance = 0
    while state.board.valid(piece, dy=1):
        piece.y += 1
        distance += 1
    state.score += distance * 2
    lines = state.board.lock_piece(piece)
    state.add_score_for_lines(lines)
    state.spawn_next()
    return True


def drop_delay_for_level(level: int) -> int:
    return max(100, 800 - (level - 1) * 60)


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

    controls: List[str] = [
        "←/→ move",
        "↑ / Z rotate",
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
        end_pos = (x * BLOCK_SIZE, WINDOW_HEIGHT)
        pygame.draw.line(screen, (40, 40, 40), start_pos, end_pos)
    for y in range(BOARD_HEIGHT + 1):
        start_pos = (0, y * BLOCK_SIZE)
        end_pos = (BOARD_WIDTH * BLOCK_SIZE, y * BLOCK_SIZE)
        pygame.draw.line(screen, (40, 40, 40), start_pos, end_pos)


def draw_game_over(screen: pygame.Surface, font: pygame.font.Font) -> None:
    overlay = pygame.Surface((BOARD_WIDTH * BLOCK_SIZE, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    text = font.render("Game Over - Press R", True, (250, 250, 250))
    text_rect = text.get_rect(center=(BOARD_WIDTH * BLOCK_SIZE // 2, WINDOW_HEIGHT // 2))
    screen.blit(text, text_rect)


if __name__ == "__main__":
    main()
