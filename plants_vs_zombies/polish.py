"""Small visual helpers; no combat timing or hit boxes live here."""
import math
import pygame


class Feedback:
    """Short, self-contained planting and collection responses."""
    def __init__(self, pos, kind='plant', amount=0):
        self.x, self.y = pos
        self.kind = kind
        self.amount = amount
        self.age = 0.0
        self.life = 0.65 if kind == 'sun' else 0.38

    def update(self, dt):
        self.age += dt

    @property
    def alive(self):
        return self.age < self.life

    def draw(self, canvas, font):
        t = min(1, self.age / self.life)
        layer = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
        alpha = round(200 * (1 - t))
        if self.kind == 'sun':
            color = (255, 220, 95)
            for i in range(6):
                a = i * math.tau / 6
                radius = 12 + 26 * t
                x, y = self.x + math.cos(a) * radius, self.y + math.sin(a) * radius - 16 * t
                pygame.draw.circle(layer, (*color, alpha), (round(x), round(y)), max(1, round(3 * (1 - t))))
            label = font.render(f'+{self.amount}', True, color)
            label.set_alpha(round(255 * (1 - t)))
            layer.blit(label, label.get_rect(center=(round(self.x), round(self.y - 18 - 35 * t))))
        else:
            color = (192, 226, 115) if self.kind == 'plant' else (232, 143, 95)
            pygame.draw.ellipse(layer, (*color, alpha), (round(self.x - 18 - 24 * t), round(self.y - 5 - 8 * t),
                                round(36 + 48 * t), round(10 + 16 * t)), 2)
            for i in range(5):
                a = i * math.tau / 5
                x = self.x + math.cos(a) * (14 + 25 * t)
                y = self.y - math.sin(t * math.pi) * 16 + math.sin(a) * 7
                pygame.draw.ellipse(layer, (*color, alpha), (round(x), round(y), 5, 3))
        canvas.blit(layer, (0, 0))
