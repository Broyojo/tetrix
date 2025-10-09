import random
from typing import Optional

from .board import Board
from .constants import BOARD_WIDTH, SCORES_PER_LINE
from .pieces import TETROMINO_SHAPES, Tetromino


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
