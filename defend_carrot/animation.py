"""Small simulation-time sprite player; drawing never advances an animation."""
from dataclasses import dataclass


@dataclass
class Animation:
    frames: tuple[str, ...]
    frame_time: float = .15
    loop: bool = True
    elapsed: float = 0.0

    def update(self, dt):
        self.elapsed += max(0.0, dt)
        duration = len(self.frames) * self.frame_time
        if self.loop:
            self.elapsed %= duration
        else:
            self.elapsed = min(self.elapsed, duration)

    def restart(self):
        self.elapsed = 0.0

    @property
    def finished(self):
        return not self.loop and self.elapsed >= len(self.frames) * self.frame_time

    @property
    def frame(self):
        return self.frames[min(int((self.elapsed + 1e-9) / self.frame_time), len(self.frames) - 1)]
