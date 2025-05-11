from core.screen import ScreenManager
from combat.character import Character, Attack
from combat.skill import Skill, AreaDamageEffect, BuffAttackSpeedEffect, GroupHealEffect
from combat.projectile import Projectile
from core.animation import Animation
import pygame
import time

class Hero(Character):
    def __init__(self, name, health, speed, dmg, atk_cd, anims, skill=None):
        sprite_height = anims["move"][0].get_height()
        y = (ScreenManager.HEIGHT // 2 + 50) - sprite_height
        center_x = 50
        super().__init__(center_x, y , health, speed)
        self.name = name
        self.attack = Attack(dmg, atk_cd)
        self.animations = {k: Animation(v) for k, v in anims.items()}
        self.current_state = "move"
        self.skill = skill
        self.dead_anim = Animation(anims["dead"], loop=False)
        self.is_dying = False
        self.ready_to_remove = False
        self.skill_anim_start_time = 0
        self.skill_anim_duration = 0
        self.skill_completed = False

    def update_animation(self):
        if self.current_state == "skill":
            elapsed = time.time() - self.skill_anim_start_time
            if elapsed >= self.skill_anim_duration and not self.skill_completed:
                self.skill_completed = True
                self.reset_state()

        if self.current_state in self.animations:
            self.animations[self.current_state].update()

    def draw(self, surface):
        if self.is_dying and self.dead_anim:
            frame = self.dead_anim.get_frame()
            surface.blit(frame, (self.x - frame.get_width() // 2, self.y))
            return

        if self.alive and self.current_state in self.animations:
            self.update_animation()
            frame = self.animations[self.current_state].get_frame()
            surface.blit(frame, (self.x - frame.get_width() // 2, self.y))
            bar_width = 40
            bar_height = 6
            health_ratio = self.health / self.max_health
            hp_x = self.x - bar_width // 2
            hp_y = self.y + 30
            pygame.draw.rect(surface, (0, 0, 0), (hp_x - 1, hp_y - 1, bar_width + 2, bar_height + 2))
            pygame.draw.rect(surface, (200, 0, 0), (hp_x, hp_y, bar_width, bar_height))
            pygame.draw.rect(surface, (0, 200, 0), (hp_x, hp_y, int(bar_width * health_ratio), bar_height))

            if self.current_state == "skill":
                import math
                radius = 5 + 1.5 * math.sin(time.time() * 8)
                center = (int(self.x), int(self.y - 12))
                pygame.draw.circle(surface, (0, 0, 0), center, int(radius) + 2)
                pygame.draw.circle(surface, (255, 255, 0), center, int(radius))

    def try_attack(self, target):
        if self.attack.can_attack():
            self.current_state = "attack"
            self.attack.attack_target(target)

    def try_skill(self, targets, game):
        if self.skill and self.skill.can_use_skill():
            self.current_state = "skill"
            self.skill.use(self, targets)
            game.tracker.log_ability_used(self.skill.name)
            self.skill_anim_start_time = time.time()
            self.skill_anim_duration = self.skill.cast_duration
            self.skill_completed = False

            if isinstance(self.skill.effect, AreaDamageEffect) and targets:
                for target in targets:
                    proj_img = pygame.Surface((10,10))
                    proj_img.fill((255,100,0))
                    proj = Projectile(
                        self.x, self.y,
                        target.x, target.y,
                        speed=4,
                        image=proj_img,
                        damage=self.skill.effect.damage,
                        on_hit_callback=lambda t=target: self.skill.effect.apply(self, [t]),
                        max_range=300
                    )
                    game.projectiles.append(proj)

    def reset_state(self):
        self.current_state = "move"

    def update(self, enemies, allies, game):
        if hasattr(self, "buff_end_time") and time.time() >= self.buff_end_time:
            if hasattr(self, "original_cooldown"):
                self.attack.cooldown = self.original_cooldown
                del self.buff_end_time
                del self.original_cooldown

        self.update_animation()
        if self.current_state == "skill":
            return

        in_range = [
            e for e in enemies
            if e.alive and abs(self.x - e.x) <= self.attack_range and abs(self.y - e.y) <= 40
        ]
        enemies_in_front = [e for e in in_range if e.x > self.x and not hasattr(e, 'take_damage')]

        if enemies_in_front:
            target = min(enemies_in_front, key=lambda e: e.x)
            self.try_attack(target)
        elif game.enemy_base_target and abs(self.x - game.enemy_base_target.x) <= self.attack_range:
            self.try_attack(game.enemy_base_target)
        else:
            self.reset_state()
            self.move()

class Archer(Hero):
    def __init__(self, sprites):
        super().__init__(
            "Archer", 60, 2, 10, 0.5, sprites["Archer"],
            Skill("Buff", 5, BuffAttackSpeedEffect(), 0.4)
        )
        self.attack_range = 500
        self.buff_range = 150

    def update(self, enemies, allies, game):
        super().update(enemies, allies, game)
        nearby_allies = [a for a in allies if a != self and a.alive and abs(self.x - a.x) <= self.buff_range]
        self.try_skill(nearby_allies, game)

class Warrior(Hero):
    def __init__(self, sprites):
        super().__init__("Warrior", 150, 2, 15, 0.5, sprites["Warrior"])
        self.attack_range = 40

class Mage(Hero):
    def __init__(self, sprites):
        super().__init__(
            "Mage", 80, 1, 10, 1, sprites["Mage"],
            Skill("AOE", 3, AreaDamageEffect(), 0.6)
        )
        self.attack_range = 350

    def update(self, enemies, allies, game):
        super().update(enemies, allies, game)
        self.try_skill(enemies, game)

class Healer(Hero):
    def __init__(self, sprites):
        super().__init__(
            "Healer", 70, 1.5, 3, 1, sprites["Healer"],
            Skill("Group Heal", 5, GroupHealEffect(), 1.0, cast_duration=1.5)
        )
        self.attack_range = 200
        self.heal_range = 150

    def update(self, enemies, allies, game):
        super().update(enemies, allies, game)
        nearby_allies = [a for a in allies if a != self and a.alive and a.health < a.max_health and abs(self.x - a.x) <= self.heal_range]
        self.try_skill(nearby_allies, game)