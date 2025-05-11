from core.screen import ScreenManager
from core.animation import Animation
from combat.character import Character, Attack
import pygame

class Enemy(Character):
    def __init__(self, anims):
        sprite_height = anims["move"][0].get_height()
        y = (ScreenManager.HEIGHT // 2 + 50) - sprite_height
        super().__init__(ScreenManager.WIDTH - 50, y, 200, -1.5)
        self.attack = Attack(20, 0.5)
        self.animations = {k: Animation(v) for k, v in anims.items()}
        self.current_state = "move"
        self.is_dying = False
        self.dead_anim = Animation(anims.get("dead", []), loop=False)

    def update(self, heroes):
        if self.is_dying:
            return
        self.animations[self.current_state].update()

        for hero in heroes:
            if not hero.alive or hero.is_dying:
                continue
            hero_center = hero.x + 20
            if abs(self.x - hero_center) <= 40:
                self.attack.attack_target(hero)
                return
        self.move()

    def draw(self, surface):
        if self.is_dying and self.dead_anim:
            if self.dead_anim.finished:
                return
            frame = self.dead_anim.get_frame()
            surface.blit(frame, (self.x - frame.get_width() // 2, self.y))
            return

        if self.alive and self.current_state in self.animations:
            self.animations[self.current_state].update()
            frame = self.animations[self.current_state].get_frame()
            surface.blit(frame, (self.x - frame.get_width() // 2, self.y))

            bar_width = 40
            bar_height = 6
            health_ratio = self.health / self.max_health
            hp_x = self.x - bar_width // 2
            hp_y = self.y + 80
            pygame.draw.rect(surface, (0, 0, 0), (hp_x - 1, hp_y - 1, bar_width + 2, bar_height + 2))
            pygame.draw.rect(surface, (200, 0, 0), (hp_x, hp_y, bar_width, bar_height))
            pygame.draw.rect(surface, (0, 200, 0), (hp_x, hp_y, int(bar_width * health_ratio), bar_height))