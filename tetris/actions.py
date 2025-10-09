from typing import Optional

from .audio import AudioManager
from .state import GameState


def move_piece(state: GameState, dx: int = 0, dy: int = 0, audio: Optional[AudioManager] = None) -> bool:
    piece = state.current_piece
    if state.board.valid(piece, dx=dx, dy=dy):
        piece.x += dx
        piece.y += dy
        if dx != 0 and audio:
            audio.play_move()
        return True
    return False


def rotate_piece(state: GameState, direction: int, audio: Optional[AudioManager] = None) -> bool:
    piece = state.current_piece
    target_rotation = piece.rotated(direction)
    kicks = [(0, 0), (-1, 0), (1, 0), (0, -1)]
    for dx, dy in kicks:
        if state.board.valid(piece, dx=dx, dy=dy, rotation=target_rotation):
            piece.rotation = target_rotation
            piece.x += dx
            piece.y += dy
            if audio:
                audio.play_rotate()
            return True
    return False


def hard_drop(state: GameState, audio: Optional[AudioManager] = None) -> bool:
    piece = state.current_piece
    distance = 0
    while state.board.valid(piece, dy=1):
        piece.y += 1
        distance += 1
    if distance:
        state.score += distance * 2
    lines = state.board.lock_piece(piece)
    if audio:
        audio.play_hard_drop(lines)
    state.add_score_for_lines(lines)
    state.spawn_next()
    return True
