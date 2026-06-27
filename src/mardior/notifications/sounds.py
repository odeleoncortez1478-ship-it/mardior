from __future__ import annotations

import winsound
from typing import Optional

SOUNDS = {
    "influencer":    (800, 500),
    "exception":     (200, 800),
    "dispute":       (150, 1000),
    "delivered":     (1000, 200),
    "new_tracking":  (600, 300),
    "error":         (150, 1000),
    "startup":       (1200, 150),
    "notification":  (900, 250),
}


class SoundNotifier:
    def __init__(self):
        self.enabled = True

    def play(self, sound_type: str):
        if not self.enabled:
            return
        sound = SOUNDS.get(sound_type)
        if sound:
            try:
                winsound.Beep(sound[0], sound[1])
            except Exception:
                pass

    def play_influencer(self):
        self.play("influencer")

    def play_exception(self):
        self.play("exception")

    def play_delivered(self):
        self.play("delivered")

    def play_error(self):
        self.play("error")

    def play_startup(self):
        self.play("startup")
