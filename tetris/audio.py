import math
from array import array
from typing import Optional

import pygame

from .constants import SAMPLE_RATE, TRACK_PATH


def _sine_wave(
    freq: float, duration: float, volume: float
) -> Optional[pygame.mixer.Sound]:
    if freq <= 0 or duration <= 0:
        return None
    sample_count = max(1, int(duration * SAMPLE_RATE))
    amplitude = int(32767 * volume)
    data = array("h")
    for i in range(sample_count):
        sample = int(amplitude * math.sin(2 * math.pi * freq * (i / SAMPLE_RATE)))
        data.append(sample)
    return pygame.mixer.Sound(buffer=data.tobytes())


class AudioManager:
    def __init__(self) -> None:
        self.enabled = False
        self.move_sound: Optional[pygame.mixer.Sound] = None
        self.rotate_sound: Optional[pygame.mixer.Sound] = None
        self.lock_sound: Optional[pygame.mixer.Sound] = None
        self.line_sound: Optional[pygame.mixer.Sound] = None
        self.hard_drop_sound: Optional[pygame.mixer.Sound] = None

        self._ensure_mixer()
        if not self.enabled:
            return

        pygame.mixer.set_num_channels(8)
        self._load_effects()
        self._start_music()

    def _ensure_mixer(self) -> None:
        if pygame.mixer.get_init() is not None:
            self.enabled = True
            return
        try:
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
        except pygame.error as exc:
            print(f"Audio unavailable: {exc}")
            self.enabled = False
        else:
            self.enabled = True

    def _load_effects(self) -> None:
        self.move_sound = _sine_wave(700, 0.05, 0.25)
        self.rotate_sound = _sine_wave(920, 0.08, 0.25)
        self.lock_sound = _sine_wave(320, 0.09, 0.35)
        self.line_sound = _sine_wave(880, 0.12, 0.4)
        self.hard_drop_sound = _sine_wave(180, 0.1, 0.4)

    def _start_music(self) -> None:
        if not TRACK_PATH.exists():
            print(f"Music track not found at {TRACK_PATH}")
            return
        try:
            pygame.mixer.music.load(str(TRACK_PATH))
            pygame.mixer.music.set_volume(0.35)
            pygame.mixer.music.play(loops=-1)
        except pygame.error as exc:
            print(f"Unable to play music track: {exc}")

    def play_move(self) -> None:
        if self.enabled and self.move_sound:
            pygame.mixer.Channel(1).play(self.move_sound)

    def play_rotate(self) -> None:
        if self.enabled and self.rotate_sound:
            pygame.mixer.Channel(2).play(self.rotate_sound)

    def play_lock(self, lines: int) -> None:
        if not self.enabled:
            return
        channel = pygame.mixer.Channel(3 if lines == 0 else 4)
        sound = self.lock_sound if lines == 0 else self.line_sound
        if sound:
            channel.play(sound)

    def play_hard_drop(self, lines: int) -> None:
        if not self.enabled:
            return
        if self.hard_drop_sound:
            pygame.mixer.Channel(5).play(self.hard_drop_sound)
        self.play_lock(lines)
