import random
from typing import List, Optional, Tuple

from .constants import BOARD_HEIGHT, BOARD_WIDTH, GARBAGE_COLOR, PIECE_COLORS
from .pieces import Tetromino


class Board:
    def __init__(self) -> None:
        self.grid: List[List[Optional[Tuple[int, int, int]]]] = [
            [None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)
        ]
        self.lines_cleared = 0

    def valid(
        self,
        piece: Tetromino,
        dx: int = 0,
        dy: int = 0,
        rotation: Optional[int] = None,
    ) -> bool:
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

    def add_garbage(self, lines: int) -> None:
        for _ in range(lines):
            hole = random.randrange(BOARD_WIDTH)
            garbage_row: List[Optional[Tuple[int, int, int]]] = [GARBAGE_COLOR for _ in range(BOARD_WIDTH)]
            garbage_row[hole] = None
            self.grid.pop(0)
            self.grid.append(garbage_row)
