from core.screen import ScreenManager
from combat.character import Character
from core.animation import Animation
import pygame

class Base:
    def __init__(self, x, color, image_path, scale_factor=6):
        self.x = x
        self.health = 100
        self.color = color
        self.image = pygame.image.load(image_path).convert_alpha()
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.image = pygame.transform.scale(
            self.image,
            (self.width // scale_factor, self.height // scale_factor)
        )

    def draw(self, surface):
        y_pos = ScreenManager.HEIGHT // 2
        surface.blit(self.image, (self.x, y_pos))
        pygame.draw.rect(surface, ScreenManager.RED, (self.x, y_pos - 20, self.health / 2, 10))

class BaseTarget(Character):
    def __init__(self, base: Base):
        super().__init__(base.x - 20, ScreenManager.HEIGHT // 2, base.health, 0)
        self.base = base
        self.is_dying = False
        self.dead_anim = Animation([], loop=False)
        self.dead_anim.finished = True

    def take_damage(self, dmg):
        self.health -= dmg
        self.base.health = self.health
        if self.health <= 0:
            self.alive = False

    def update(self, heroes):
        pass

    def draw(self, surface):
        self.base.draw(surface)
