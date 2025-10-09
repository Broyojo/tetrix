from pathlib import Path

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
MOVE_LEFT_EVENT = pygame.USEREVENT + 3
MOVE_RIGHT_EVENT = pygame.USEREVENT + 4
ROTATE_EVENT = pygame.USEREVENT + 5

AUTO_REPEAT_INITIAL = 180
AUTO_REPEAT_INTERVAL = 60

SAMPLE_RATE = 44_100

SCORES_PER_LINE = {1: 100, 2: 300, 3: 500, 4: 800}

PIECE_COLORS = {
    "I": (0, 240, 240),
    "O": (240, 240, 0),
    "T": (160, 0, 240),
    "S": (0, 240, 0),
    "Z": (240, 0, 0),
    "J": (0, 0, 240),
    "L": (240, 160, 0),
}

TRACK_PATH = Path(__file__).resolve().parent.parent / "assets" / "yi_jian_mei.mp3"
