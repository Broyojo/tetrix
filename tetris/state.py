import random

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
        self.pending_garbage = 0

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

    def queue_garbage(self, lines: int) -> None:
        if lines > 0:
            self.pending_garbage += lines

    def apply_pending_garbage(self) -> None:
        if self.pending_garbage <= 0 or self.game_over:
            return
        lines = self.pending_garbage
        self.pending_garbage = 0
        self.current_piece.y -= lines
        self.board.add_garbage(lines)
        while not self.board.valid(self.current_piece):
            self.current_piece.y -= 1
            if self.current_piece.y < -4:
                self.game_over = True
                break
