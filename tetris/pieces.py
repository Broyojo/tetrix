from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Sequence, Tuple

from .constants import BOARD_WIDTH

TETROMINO_SHAPES: Dict[str, Sequence[Sequence[str]]] = {
    "I": (
        ("....", "XXXX", "....", "...."),
        ("..X.", "..X.", "..X.", "..X."),
    ),
    "O": ((".XX.", ".XX.", "....", "...."),),
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
