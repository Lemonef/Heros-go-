import pygame
import random
import time
import os
import csv
import tkinter as tk
from collections import defaultdict
from settings_window import SettingsWindow

class ScreenManager:
    WIDTH, HEIGHT = 800, 400
    WHITE = (255, 255, 255)
    RED = (200, 0, 0)
    GREEN = (0, 200, 0)
    BLACK = (0, 0, 0)
    FPS = 60

    def __init__(self):
        pygame.init()
        self.surface = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Battle Heroes Defense")
        self.clock = pygame.time.Clock()

    def fill(self, color):
        self.surface.fill(color)

    def update(self):
        pygame.display.flip()

    def tick(self):
        self.clock.tick(self.FPS)

    def quit(self):
        pygame.quit()

class AnimationManager:
    @staticmethod
    def load_sprite_strip(path):
        sheet = pygame.image.load(path).convert_alpha()
        frame_height = sheet.get_height()
        frame_width = frame_height  # assume square
        cols = sheet.get_width() // frame_width
        return [sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)) for i in range(cols)]

    @staticmethod
    def load_animations_from_folder(folder):
        animations = {}
        for file in os.listdir(folder):
            if file.endswith(".png"):
                key = file.replace(".png", "").lower()
                animations[key] = AnimationManager.load_sprite_strip(os.path.join(folder, file))
        return animations

class Animation:
    def __init__(self, frames, interval=0.1, loop=True):
        self.frames = frames
        self.interval = interval
        self.index = 0
        self.last_time = time.time()
        self.loop = loop
        self.finished = False

    def update(self):
        if self.finished:
            return
        if time.time() - self.last_time >= self.interval:
            self.index += 1
            if self.index >= len(self.frames):
                if self.loop:
                    self.index = 0
                else:
                    self.index = len(self.frames) - 1
                    self.finished = True
            self.last_time = time.time()

    def get_frame(self):
        return self.frames[self.index]

class Tracker:
    def __init__(self, csv_filename="game_data.csv"):
        self.csv_filename = csv_filename
        self.snapshot_data = []
        self.last_snapshot_time = time.time()

        self.enemies_defeated = 0
        self.hero_spawn_counter = defaultdict(int)
        self.ability_usage_counter = defaultdict(int)
        self.energy_spent = 0
        self.heroes_defeated = 0

        self.initialize_csv_if_needed()

    def initialize_csv_if_needed(self):
        if not os.path.exists(self.csv_filename):
            with open(self.csv_filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "TotalEnergyUsed", "EnemiesDefeated",
                    "HeroesDefeated", "MostSpawnedHero", "MostSpawnedCount",
                    "Attack_speed_Buff_Used", "AOE_Used", "GroupHeal_Used"
                ])
            print(f"[Tracker] CSV initialized with header: {self.csv_filename}")
        else:
            print(f"[Tracker] CSV file already exists: {self.csv_filename}")

    def log_hero_defeated(self):
        self.heroes_defeated += 1

    def log_hero_spawn_count(self, hero_name):
        self.hero_spawn_counter[hero_name] += 1

    def log_ability_used(self, skill_name):
        self.ability_usage_counter[skill_name] += 1

    def log_enemy_defeated(self):
        self.enemies_defeated += 1

    def log_energy_spent(self, amount):
        self.energy_spent += amount 

    def try_snapshot(self):
        now = time.time()
        if now - self.last_snapshot_time >= 5:
            most_spawned = max(self.hero_spawn_counter.items(), key=lambda x: x[1], default=("None", 0))

            # Extract counts safely
            archer_count = self.ability_usage_counter.get("Buff", 0)
            mage_count = self.ability_usage_counter.get("AOE", 0)
            healer_count = self.ability_usage_counter.get("Group Heal", 0)

            self.snapshot_data.append([
                now,
                self.energy_spent,
                self.enemies_defeated,
                self.heroes_defeated,
                most_spawned[0],
                most_spawned[1],
                archer_count,
                mage_count,
                healer_count
            ])
            print(f"[Tracker] Snapshot taken at {now}")

            # Reset counters
            self.heroes_defeated = 0
            self.enemies_defeated = 0
            self.hero_spawn_counter.clear()
            self.ability_usage_counter.clear()
            self.last_snapshot_time = now

    def append_new_rows(self):
        if not self.snapshot_data:
            print("[Tracker] No new data to save.")
            return

        with open(self.csv_filename, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(self.snapshot_data)
        print(f"[Tracker] {len(self.snapshot_data)} new rows appended to {self.csv_filename}")

        self.snapshot_data.clear()



class Character:
    def __init__(self, x, y, health, speed):
        self.x, self.y = x, y
        self.health = self.max_health = health
        self.speed = speed
        self.alive = True

    def move(self):
        if self.alive:
            self.x += self.speed

class Attack:
    def __init__(self, dmg, cooldown):
        self.dmg = dmg
        self.cooldown = cooldown
        self.last_time = 0

    def can_attack(self):
        return time.time() - self.last_time >= self.cooldown

    def attack_target(self, target):
        if self.can_attack():
            if isinstance(target, BaseTarget):
                target.take_damage(self.dmg)
            else:
                target.health -= self.dmg
                if target.health <= 0:
                    target.alive = False
                    target.is_dying = True
            self.last_time = time.time()
    
class SkillEffect:
    def apply(self, user, targets):
        pass

class AreaDamageEffect(SkillEffect):
    def __init__(self, radius=100, damage=20):
        self.radius = radius
        self.damage = damage

    def apply(self, user, targets):
        for t in targets:
            if abs(user.x - t.x) <= self.radius and t.alive:
                t.health -= self.damage
                if t.health <= 0:
                    t.alive = False

class BuffAttackSpeedEffect(SkillEffect):
    def __init__(self, buff_amount=0.5, duration=5):
        self.buff_amount = buff_amount
        self.duration = duration
    def apply(self, user, targets):
        for ally in targets:
            if not hasattr(ally, "original_cooldown"):
                ally.original_cooldown = ally.attack.cooldown
            ally.attack.cooldown = max(0.1, ally.attack.cooldown - self.buff_amount)
            ally.buff_end_time = time.time() + self.duration

class GroupHealEffect(SkillEffect):
    def __init__(self, heal_amount=15):
        self.heal_amount = heal_amount

    def apply(self, user, targets):
        for t in targets:
            if t.alive and t.health < t.max_health:
                t.health += self.heal_amount
                if t.health > t.max_health:
                    t.health = t.max_health

class Skill:
    def __init__(self, name, skill_cooldown, effect: SkillEffect, skill_chance=1.0, cast_duration=0.3):
        self.name = name
        self.skill_cooldown = skill_cooldown
        self.effect = effect
        self.skill_chance = skill_chance
        self.cast_duration = cast_duration
        self.last_used_time = 0

    def can_use_skill(self):
        cooldown_ready = time.time() - self.last_used_time >= self.skill_cooldown
        chance_roll = random.random() < self.skill_chance
        return cooldown_ready and chance_roll

    def use(self, user, targets):
        if self.can_use_skill():
            self.effect.apply(user, targets)
            self.last_used_time = time.time()

class Projectile:
    def __init__(self, x, y, target_x, target_y, speed, image, damage, on_hit_callback=None, max_range=300):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.target_x = target_x
        self.target_y = target_y
        self.speed = speed
        self.image = image
        self.damage = damage
        self.on_hit_callback = on_hit_callback
        self.max_range = max_range
        self.alive = True

        dx = target_x - x
        dy = target_y - y
        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist != 0:
            self.dir_x = dx / dist
            self.dir_y = dy / dist
        else:
            self.dir_x = self.dir_y = 0

    def update(self):
        self.x += self.dir_x * self.speed
        self.y += self.dir_y * self.speed

        if self.has_reached_target():
            if self.on_hit_callback:
                self.on_hit_callback()
            self.alive = False

        dist_traveled = ((self.x - self.start_x) ** 2 + (self.y - self.start_y) ** 2) ** 0.5
        if dist_traveled >= self.max_range:
            self.alive = False

    def has_reached_target(self):
        return (abs(self.x - self.target_x) < 5) and (abs(self.y - self.target_y) < 5)

    def draw(self, surface):
        surface.blit(self.image, (self.x - self.image.get_width() // 2, self.y - self.image.get_height() // 2))


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

            # Draw HP bar above hero
            bar_width = 40
            bar_height = 6
            health_ratio = self.health / self.max_health
            hp_x = self.x - bar_width // 2
            hp_y = self.y + 30
            pygame.draw.rect(surface, (0, 0, 0), (hp_x - 1, hp_y - 1, bar_width + 2, bar_height + 2))  # border
            pygame.draw.rect(surface, (200, 0, 0), (hp_x, hp_y, bar_width, bar_height))  # background
            pygame.draw.rect(surface, (0, 200, 0), (hp_x, hp_y, int(bar_width * health_ratio), bar_height))  # current HP

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
                    proj_img.fill((255,100,0))  # placeholder color
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
            if e.alive
            and abs(self.x - e.x) <= self.attack_range
            and abs(self.y - e.y) <= 40
        ]
        enemies_in_front = [e for e in in_range if e.x > self.x and not isinstance(e, BaseTarget)]

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
        nearby_allies = [
            a for a in allies if a != self and a.alive and abs(self.x - a.x) <= self.buff_range
        ]
        self.try_skill(nearby_allies, game)


class Warrior(Hero):
    def __init__(self, sprites):
        super().__init__("Warrior", 150, 2, 15, 0.5, sprites["Warrior"])
        self.attack_range = 40

    def update(self, enemies, allies, game):
        super().update(enemies, allies, game)



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
        nearby_allies = [
            a for a in allies if a != self and a.alive and a.health < a.max_health and abs(self.x - a.x) <= self.heal_range
        ]
        self.try_skill(nearby_allies, game)

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
        self.dead_anim = Animation([], loop=False)  # empty animation
        self.dead_anim.finished = True  # instantly mark as finished

        
    def take_damage(self, dmg):
        self.health -= dmg
        self.base.health = self.health
        if self.health <= 0:
            self.alive = False

    def update(self, heroes):
        # Does nothing (no movement, no attack)
        pass

    def draw(self, surface):
        self.base.draw(surface)

class ResourceManager:
    def __init__(self):
        self.energy = 100
        self.max_energy = 100
        self.regen_rate = 0.1
        self.upgrade_clicks = 0
        self.last_upgrade_display_time = 0

    def can_afford(self, cost):
        return self.energy >= cost

    def spend(self, amt):
        self.energy -= amt

    def regenerate(self):
        if self.energy < self.max_energy:
            self.energy += self.regen_rate
            if self.energy > self.max_energy:
                self.energy = self.max_energy

    def upgrade_energy(self):
        upgrade_cost = 20 + 10 * self.upgrade_clicks
        if self.upgrade_clicks < 5 and self.energy >= upgrade_cost:
            self.energy -= upgrade_cost
            self.max_energy += 10
            self.regen_rate += 0.01
            self.upgrade_clicks += 1
            self.last_upgrade_display_time = time.time()

class Button:
    def __init__(self, rect, label, on_click=None, color=(0, 200, 0), text_color=(0, 0, 0), font_size=24):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.color = color
        self.text_color = text_color
        self.font_size = font_size
        self.enabled = True

    def draw(self, surface):
        mouse_over = self.rect.collidepoint(pygame.mouse.get_pos())
        current_color = tuple(min(255, c + 30) for c in self.color) if mouse_over and self.enabled else self.color

        # Draw shadow
        shadow_offset = 4
        shadow_rect = self.rect.move(shadow_offset, shadow_offset)
        pygame.draw.rect(surface, (50, 50, 50), shadow_rect, border_radius=5)

        # Main button
        pygame.draw.rect(surface, current_color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2, border_radius=5)

        font = pygame.font.SysFont("arial", self.font_size, bold=True)
        text_surf = font.render(self.label, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if not self.enabled or not self.on_click:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.on_click()

                
class UpgradeButton(Button):
    def __init__(self, x, y, width=120, height=55):
        super().__init__((x, y, width, height), label="", font_size=22)
        self.last_upgrade_time = 0
        self.last_fail_time = 0

    def update_label(self, res_mgr):
        if res_mgr.upgrade_clicks >= 5:
            self.label = "Maxed"
        elif time.time() - self.last_upgrade_time < 1:
            self.label = "Upgraded!"
        elif time.time() - self.last_fail_time < 1:
            self.label = "Not enough!"
        else:
            cost = 20 + 10 * res_mgr.upgrade_clicks
            self.label = f"Upgrade ({cost})"

    def draw(self, surface, res_mgr):
        self.update_label(res_mgr)
        mouse_over = self.rect.collidepoint(pygame.mouse.get_pos())

        if res_mgr.upgrade_clicks >= 5:
            color = (150, 150, 150)
        else:
            color = (250, 180, 0)
            if mouse_over:
                color = (255, 210, 50)

        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2, border_radius=5)

        font = pygame.font.Font(None, 24)
        label_surf = font.render(self.label, True, (0, 0, 0))

        label_x = self.rect.centerx - label_surf.get_width() // 2
        label_y = self.rect.centery - label_surf.get_height() // 2
        surface.blit(label_surf, (label_x, label_y))


    def try_click(self, event_pos, res_mgr):
        if self.rect.collidepoint(event_pos):
            upgrade_cost = 20 + 10 * res_mgr.upgrade_clicks
            if res_mgr.energy >= upgrade_cost and res_mgr.upgrade_clicks < 5:
                res_mgr.upgrade_energy()
                self.last_upgrade_time = time.time()
            else:
                self.last_fail_time = time.time()


class HeroButton(Button):
    def __init__(self, x, cls, cost, cooldown):
        self.cls = cls
        self.cost = cost
        self.cooldown = cooldown
        self.last = 0
        self.width = 80
        self.height = 55
        rect = (x, pygame.display.get_surface().get_height() - 70, self.width, self.height)

        super().__init__(rect=rect, label=cls.__name__, font_size=20)

    def is_ready(self):
        return time.time() - self.last >= self.cooldown

    def draw(self, surface, res_mgr):
        color_map = {
            'Archer': (0, 200, 0),
            'Warrior': (0, 100, 200),
            'Mage': (150, 0, 200),
            'Healer': (255, 100, 180)
        }
        base_color = color_map.get(self.cls.__name__, (180, 180, 180))
        ready = self.is_ready() and res_mgr.can_afford(self.cost)
        mouse_over = self.rect.collidepoint(pygame.mouse.get_pos())

        if not ready:
            color = (150, 150, 150)
        elif mouse_over:
            color = tuple(min(255, c + 40) for c in base_color)
        else:
            color = base_color

        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2, border_radius=5)

        name_font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 18)

        name_surf = name_font.render(self.cls.__name__, True, (0, 0, 0))
        cost_surf = small_font.render(f"{self.cost} Energy", True, (0, 0, 0))

        name_x = self.rect.x + (self.rect.width - name_surf.get_width()) // 2
        cost_x = self.rect.x + (self.rect.width - cost_surf.get_width()) // 2

        total_height = name_surf.get_height() + cost_surf.get_height() + 4
        name_y = self.rect.y + (self.rect.height - total_height) // 2
        cost_y = name_y + name_surf.get_height() + 4

        surface.blit(name_surf, (name_x, name_y))
        surface.blit(cost_surf, (cost_x, cost_y))

        if not self.is_ready():
            cd_ratio = (time.time() - self.last) / self.cooldown
            cd_ratio = min(max(cd_ratio, 0), 1)
            bar_width = int(self.width * cd_ratio)
            pygame.draw.rect(surface, (100, 100, 100), (self.rect.x, self.rect.y, bar_width, 5))


    def try_spawn(self, game):
        if self.is_ready() and game.res_mgr.can_afford(self.cost):
            hero = game.create_hero(self.cls)
            game.heroes.append(hero)
            game.res_mgr.spend(self.cost)
            game.tracker.log_energy_spent(self.cost)
            self.last = time.time()

class MainMenu:
    def __init__(self, screen_mgr):
        self.screen_mgr = screen_mgr
        self.result = None

        self.play_button = Button(
            rect=(ScreenManager.WIDTH // 2 - 60, ScreenManager.HEIGHT // 2 + 100, 120, 55),
            label="PLAY",
            on_click=self.start_game,
            color=(0, 200, 0)
        )

        self.quit_button = Button(
            rect=(ScreenManager.WIDTH - 110, 10, 100, 40),
            label="QUIT",
            on_click=self.quit_game,
            color=(200, 50, 50),
            text_color=(255, 255, 255),
            font_size=20
        )

        full_bg = pygame.image.load("assets/Background/Stage3.png").convert()
        cropped_height = full_bg.get_height() - 50
        cropped_bg = full_bg.subsurface(pygame.Rect(0, 0, full_bg.get_width(), cropped_height))
        self.background = pygame.transform.scale(cropped_bg, (ScreenManager.WIDTH, ScreenManager.HEIGHT))

    def start_game(self):
        self.result = "start"

    def quit_game(self):
        pygame.quit()
        import sys
        sys.exit()

    def draw(self):
        surface = self.screen_mgr.surface
        surface.blit(self.background, (0, 0))

        instructions_text = [
            "INSTRUCTIONS:",
            "- Click hero buttons to deploy units (costs energy)",
            "- Each hero has unique skills and attacks",
            "- Defeat enemies to protect your base",
            "- Upgrade energy to increase max and regen rate",
            "- Destroy enemy base to win!"
        ]

        font_instr = pygame.font.Font(None, 22)
        title_font = pygame.font.Font(None, 30)
        start_y = ScreenManager.HEIGHT // 4

        for i, line in enumerate(instructions_text):
            surf = title_font.render(line, True, ScreenManager.BLACK) if i == 0 else font_instr.render(line, True, ScreenManager.BLACK)
            surface.blit(surf, (ScreenManager.WIDTH // 2 - surf.get_width() // 2, start_y + i * 30))

        self.play_button.draw(surface)
        self.quit_button.draw(surface)
        self.screen_mgr.update()

    def handle_event(self, event):
        self.play_button.handle_event(event)
        self.quit_button.handle_event(event)
        return self.result


class EndScreen:
    def __init__(self, screen_mgr, is_victory):
        self.screen_mgr = screen_mgr
        self.is_victory = is_victory
        self.result = None

        self.play_again_btn = Button(
            rect=(ScreenManager.WIDTH // 2 - 180, ScreenManager.HEIGHT // 2 + 40, 160, 60),
            label="PLAY AGAIN",
            on_click=self.restart_game,
            color=(0, 200, 0)
        )
        self.home_btn = Button(
            rect=(ScreenManager.WIDTH // 2 + 20, ScreenManager.HEIGHT // 2 + 40, 160, 60),
            label="HOME",
            on_click=self.go_home,
            color=(0, 200, 0)
        )
        self.quit_btn = Button(
            rect=(ScreenManager.WIDTH // 2 - 80, ScreenManager.HEIGHT // 2 + 120, 160, 50),
            label="QUIT GAME",
            on_click=self.quit_game,
            color=(180, 50, 50),
            text_color=(255, 255, 255)
        )

        full_bg = pygame.image.load("assets/Background/Stage2.png").convert()
        cropped_height = full_bg.get_height() - 50
        cropped_bg = full_bg.subsurface(pygame.Rect(0, 0, full_bg.get_width(), cropped_height))
        self.background = pygame.transform.scale(cropped_bg, (ScreenManager.WIDTH, ScreenManager.HEIGHT))

    def restart_game(self):
        self.result = "restart"

    def go_home(self):
        self.result = "home"

    def quit_game(self):
        pygame.quit()
        import sys
        sys.exit()

    def draw(self):
        surface = self.screen_mgr.surface
        surface.blit(self.background, (0, 0))

        title_font = pygame.font.Font(None, 60)
        title_text = "VICTORY!" if self.is_victory else "GAME OVER"
        title_color = ScreenManager.GREEN if self.is_victory else ScreenManager.RED
        title_surf = title_font.render(title_text, True, title_color)
        surface.blit(
            title_surf,
            (ScreenManager.WIDTH // 2 - title_surf.get_width() // 2, ScreenManager.HEIGHT // 3)
        )

        sub_font = pygame.font.Font(None, 28)
        sub_text = "You destroyed the enemy base!" if self.is_victory else "Your base was destroyed!"
        sub_surf = sub_font.render(sub_text, True, ScreenManager.BLACK)
        surface.blit(
            sub_surf,
            (ScreenManager.WIDTH // 2 - sub_surf.get_width() // 2, ScreenManager.HEIGHT // 3 + 50)
        )

        self.play_again_btn.draw(surface)
        self.home_btn.draw(surface)
        self.quit_btn.draw(surface)

        self.screen_mgr.update()

    def handle_event(self, event):
        self.play_again_btn.handle_event(event)
        self.home_btn.handle_event(event)
        self.quit_btn.handle_event(event)
        return self.result



class GameManager:
    def __init__(self):
        self.screen_mgr = ScreenManager()
        self.tracker = Tracker()
        self.player_base = Base(10, ScreenManager.GREEN, "assets/Base/Base1.png", scale_factor=6)
        self.enemy_base = Base(ScreenManager.WIDTH - 60, ScreenManager.RED, "assets/Base/Base2.png", scale_factor=3)
        self.heroes = []
        self.enemies = []
        self.projectiles = []
        self.dying_heroes = []
        self.dying_enemies = []
        self.enemy_base_target = BaseTarget(self.enemy_base)
        self.enemies.append(self.enemy_base_target)
        self.res_mgr = ResourceManager()
        self.tk_root = tk.Tk()
        self.tk_root.withdraw()
        self.settings = SettingsWindow(self, self.tk_root)
        
        blue_slime_anims = AnimationManager.load_animations_from_folder("assets/Enemy/Blue_Slime")
        green_slime_anims = AnimationManager.load_animations_from_folder("assets/Enemy/Green_Slime")
        red_slime_anims = AnimationManager.load_animations_from_folder("assets/Enemy/Red_Slime")
    
        self.enemy_sprites = {
            "Blue_Slime": {
                "move": blue_slime_anims.get("run", []),
                "attack": blue_slime_anims.get("attack_1", []),
                "dead": blue_slime_anims.get("dead", []),
            },
            "Green_Slime": {
                "move": green_slime_anims.get("run", []),
                "attack": green_slime_anims.get("attack_1", []),
                "dead": green_slime_anims.get("dead", []),
            },
            "Red_Slime": {
                "move": red_slime_anims.get("run", []),
                "attack": red_slime_anims.get("attack_1", []),
                "dead": red_slime_anims.get("dead", []),
            }
        }        

        fighter_anims = AnimationManager.load_animations_from_folder("assets/Fighter")
        archer_anims = AnimationManager.load_animations_from_folder("assets/Samurai")
        mage_anims = AnimationManager.load_animations_from_folder("assets/Mage")
        healer_anims = AnimationManager.load_animations_from_folder("assets/Healer")

        full_bg = pygame.image.load("assets/Background/Stage1.png").convert()
        cropped_height = full_bg.get_height() - 50
        cropped_bg = full_bg.subsurface(pygame.Rect(0, 0, full_bg.get_width(), cropped_height))
        self.background = pygame.transform.scale(cropped_bg, (ScreenManager.WIDTH, ScreenManager.HEIGHT))

        self.hero_sprites = {
            "Archer": {
                "move": archer_anims.get("run", []),
                "attack": archer_anims.get("attack_2", []),
                "skill": archer_anims.get("idle", []),
                "dead": archer_anims.get("dead", []),
            },
            "Warrior": {
                "move": fighter_anims.get("run", []),
                "attack": fighter_anims.get("attack_2", []),
                "skill": fighter_anims.get("idle", []),
                "dead": fighter_anims.get("dead", []),
            },
            "Mage": {
                "move": mage_anims.get("walk", []),
                "attack": mage_anims.get("attack_1", []),
                "skill": mage_anims.get("attack_2", []),
                "dead": mage_anims.get("dead", []),
            },
            "Healer": {
                "move": healer_anims.get("walk", []),
                "attack": healer_anims.get("attack_4", []),
                "skill": healer_anims.get("scream", []),
                "dead": healer_anims.get("dead", []),
            }
        }

        self.hero_buttons = [
            HeroButton(100, Archer, 20, 3),
            HeroButton(190, Warrior, 10, 2),
            HeroButton(280, Mage, 20, 3),
            HeroButton(370, Healer, 15, 2)
        ]
        
        self.upgrade_button = UpgradeButton(520, ScreenManager.HEIGHT - 70, width=160)
        self.settings_button = Button(
            rect=(ScreenManager.WIDTH - 120, 10, 100, 40),
            label="Settings",
            on_click=lambda: self.settings.run(),
            color=(200, 200, 200),
            font_size=20
        )
        
        self.paused = False
        self.running = True

    def create_hero(self, cls):
        hero = cls(self.hero_sprites)
        self.tracker.log_hero_spawn_count(hero.name)
        return hero

    
    def spawn_enemy(self):
        now = time.time()
        if not hasattr(self, 'last_spawn_time'):
            self.last_spawn_time = now
        if not hasattr(self, 'spawn_interval'):
            self.spawn_interval = random.uniform(0.5, 2.0)

        if now - self.last_spawn_time >= self.spawn_interval:
            enemy_type = random.choice(["Blue_Slime", "Green_Slime", "Red_Slime"])
            enemy_anims = self.enemy_sprites[enemy_type]
            self.enemies.append(Enemy(enemy_anims))
            self.last_spawn_time = now
            self.spawn_interval = random.uniform(0.5, 2.0)
                
    def update(self):
        if self.paused:
            return
        for h in self.heroes[:]:
            h.update(self.enemies, self.heroes, self)

        for e in self.enemies[:]:
            e.update(self.heroes)
            
            if not e.alive and not getattr(e, "_death_logged", False):
                if not isinstance(e, BaseTarget):
                    self.tracker.log_enemy_defeated()
                e._death_logged = True 

            elif e.x <= 50 and not e.is_dying:
                self.player_base.health -= 5
                e.alive = False
                e.is_dying = True

        for e in self.enemies[:]:
            if e.is_dying:
                e.dead_anim.update()
                if e.dead_anim.finished:
                    self.enemies.remove(e)

        for proj in self.projectiles:
            proj.update()
        self.projectiles = [p for p in self.projectiles if p.alive]

        for h in self.heroes[:]:
            if h.is_dying:
                self.tracker.log_hero_defeated()
                self.dying_heroes.append(h)
                self.heroes.remove(h)

        for h in self.dying_heroes[:]:
            h.dead_anim.update()
            if h.dead_anim.finished:
                self.dying_heroes.remove(h)

        self.res_mgr.regenerate()

        if self.player_base.health <= 0:
            self.running = False
        elif self.enemy_base.health <= 0:
            self.running = False
            
        self.tracker.try_snapshot()

    def draw(self):
        sm = self.screen_mgr
        font = pygame.font.Font(None, 24)

        sm.surface.blit(self.background, (0, 0))
        self.player_base.draw(sm.surface)
        self.upgrade_button.draw(sm.surface, self.res_mgr)

        for proj in self.projectiles:
            proj.draw(sm.surface)
        for h in self.heroes:
            h.draw(sm.surface)
        for e in self.enemies:
            e.draw(sm.surface)
        for h in self.dying_heroes:
            h.draw(sm.surface)
        for e in self.dying_enemies:
            e.draw(sm.surface)

        for btn in self.hero_buttons:
            btn.draw(sm.surface, self.res_mgr)

        energy_text = f"Energy: {int(self.res_mgr.energy)} / {int(self.res_mgr.max_energy)}"
        energy_render = font.render(energy_text, True, ScreenManager.BLACK)
        sm.surface.blit(energy_render, (10, 10))

        self.settings_button.draw(sm.surface)

        if time.time() - self.res_mgr.last_upgrade_display_time < 1:
            plus_text = font.render("+10", True, (0, 200, 0))
            sm.surface.blit(plus_text, (10 + energy_render.get_width() + 5, 10))

        sm.update()

        

def main():
    screen_mgr = ScreenManager()
    main_menu = MainMenu(screen_mgr)
    game = None
    end_screen = None
    game_state = "menu"

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and game_state == "playing":
                    game.settings.run()

            if game_state == "menu":
                result = main_menu.handle_event(event)
                if result == "start":
                    game = GameManager()
                    game_state = "playing"

            elif game_state == "playing":
                for b in game.hero_buttons:
                    if event.type == pygame.MOUSEBUTTONDOWN and b.rect.collidepoint(event.pos):
                        b.try_spawn(game)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    game.upgrade_button.try_click(event.pos, game.res_mgr)
                    game.settings_button.handle_event(event)


            elif game_state == "end":
                result = end_screen.handle_event(event)
                if result == "restart":
                    game = GameManager()  # restart game
                    game.tracker.snapshot_data.clear()
                    game_state = "playing"
                elif result == "home":
                    game_state = "menu"

        # Drawing
        if game_state == "menu":
            main_menu.draw()

        elif game_state == "playing":
            if not game.paused:
                game.spawn_enemy()
                game.update()
            game.draw()

            # Check for game over
            if not game.running:
                game.tracker.append_new_rows()
                end_screen = EndScreen(screen_mgr, is_victory=game.enemy_base.health <= 0)
                game_state = "end"
                continue

        elif game_state == "end":
            end_screen.draw()

        screen_mgr.tick()
        if game:
            try:
                game.tk_root.update()
            except tk.TclError:
                pass

    if game:
        print("Saving CSV data...")
        game.tracker.append_new_rows()

    screen_mgr.quit()

if __name__ == "__main__":
    main()
