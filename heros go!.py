import pygame
import random
import time
import os

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

    @staticmethod
    def create_enemy_surface():
        s = pygame.Surface((40, 40))
        s.fill(ScreenManager.RED)
        return s

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
    def apply(self, user, targets):
        pass

class GroupHealEffect(SkillEffect):
    def __init__(self, heal_amount=15):
        self.heal_amount = heal_amount

    def apply(self, user, targets):
        healed = False
        for t in targets:
            if t.alive and t.health < t.max_health:
                t.health += self.heal_amount
                healed = True
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
        self.update_animation()

        if self.current_state == "skill":
            return 

        in_range = [e for e in enemies if e.alive and abs(self.x - e.x) <= self.attack_range]
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
        in_range = [e for e in enemies if abs(self.x - e.x) <= self.attack_range and e.alive]
        if in_range:
            self.try_attack(in_range[0])
        else:
            self.reset_state()
            self.move()

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
    def __init__(self, image):
        center_x = ScreenManager.WIDTH - 50
        super().__init__(center_x, ScreenManager.HEIGHT // 2, 30, -1.5)
        self.attack = Attack(5, 1)
        self.image = image
        self.width = self.image.get_width()

    def update(self, heroes):
        for hero in heroes:
                if not hero.alive or hero.is_dying:
                    continue  # skip dead or dying heroes
                hero_center = hero.x + 20
                if abs(self.x - hero_center) <= 40:
                    self.attack.attack_target(hero)
                    return
        self.move()

    def draw(self, surface):
        if self.alive:
            surface.blit(self.image, (self.x - self.image.get_width() // 2, self.y))


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
                
class UpgradeButton:
    def __init__(self, x, y, width=120, height=55):
        self.rect = pygame.Rect(x, y, width, height)
        self.last_upgrade_time = 0
        self.last_fail_time = 0

    def draw(self, surface, font, res_mgr):
        mouse_over = self.rect.collidepoint(pygame.mouse.get_pos())
        color = (250, 180, 0) if res_mgr.upgrade_clicks < 5 else (150, 150, 150)
        if mouse_over and res_mgr.upgrade_clicks < 5:
            color = (255, 210, 50)

        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (0,0,0), self.rect, width=2, border_radius=5)

        if res_mgr.upgrade_clicks >= 5:
            label = "Maxed"
        elif time.time() - self.last_upgrade_time < 1:
            label = "Upgraded!"
        elif time.time() - self.last_fail_time < 1:
            label = "Not enough!"
        else:
            upgrade_cost = 20 + 10 * res_mgr.upgrade_clicks
            label = f"Upgrade ({upgrade_cost})"

        text = font.render(label, True, (0,0,0))
        text_x = self.rect.x + (self.rect.width - text.get_width()) // 2
        text_y = self.rect.y + (self.rect.height - text.get_height()) // 2
        surface.blit(text, (text_x, text_y))

    def try_click(self, pos, res_mgr):
        if self.rect.collidepoint(pos) and res_mgr.upgrade_clicks < 5:
            upgrade_cost = 20 + 10 * res_mgr.upgrade_clicks
            if res_mgr.energy >= upgrade_cost:
                res_mgr.upgrade_energy()
                self.last_upgrade_time = time.time()
            else:
                self.last_fail_time = time.time()

class HeroButton:
    def __init__(self, x, cls, cost, cooldown):
        self.x = x
        self.cls = cls
        self.cost = cost
        self.cd = cooldown
        self.last = 0
        self.width = 80
        self.height = 55
        self.rect = pygame.Rect(x, ScreenManager.HEIGHT - 70, self.width, self.height)

    def is_ready(self):
        return time.time() - self.last >= self.cd

    def brighten(self, color, amount=40):
        return tuple(min(255, c + amount) for c in color)

    def draw(self, surface, font, res_mgr):
        color_map = {
            'Archer': (0, 200, 0),
            'Warrior': (0, 100, 200),
            'Mage': (150, 0, 200),
            'Healer': (255, 100, 180)
        }
        base_color = color_map.get(self.cls.__name__, ScreenManager.RED)
        color = base_color

        ready = self.is_ready() and res_mgr.can_afford(self.cost)
        mouse_over = self.rect.collidepoint(pygame.mouse.get_pos())

        if mouse_over and ready:
            color = self.brighten(color, 40)
        elif not ready:
            color = (150, 150, 150)  # greyed out when on cooldown or can't afford

        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, width=2, border_radius=5)

        # Cooldown bar
        if not self.is_ready():
            progress = (time.time() - self.last) / self.cd
            progress = min(max(progress, 0), 1)
            cooldown_bar_width = int(self.width * progress)
            cooldown_bar_rect = pygame.Rect(self.x, self.rect.y, cooldown_bar_width, 5)
            pygame.draw.rect(surface, (100, 100, 100), cooldown_bar_rect)

        name_text = font.render(self.cls.__name__, True, ScreenManager.BLACK)
        small_font = pygame.font.Font(None, 18)
        cost_text = small_font.render(f"{self.cost} Energy", True, ScreenManager.BLACK)

        name_x = self.x + (self.width - name_text.get_width()) // 2
        cost_x = self.x + (self.width - cost_text.get_width()) // 2

        total_text_height = name_text.get_height() + cost_text.get_height() + 4
        name_y = self.rect.y + (self.height - total_text_height) // 2 + 2
        cost_y = name_y + name_text.get_height() + 4

        surface.blit(name_text, (name_x, name_y))
        surface.blit(cost_text, (cost_x, cost_y))

    def try_spawn(self, game):
        if self.is_ready() and game.res_mgr.can_afford(self.cost):
            game.heroes.append(game.create_hero(self.cls))
            game.res_mgr.spend(self.cost)
            self.last = time.time()
            
class MainMenu:
    def __init__(self, screen_mgr):
        self.screen_mgr = screen_mgr
        self.play_button = pygame.Rect(ScreenManager.WIDTH // 2 - 60, ScreenManager.HEIGHT // 2 + 40, 120, 55)

    def draw(self):
        self.screen_mgr.fill(ScreenManager.WHITE)

        # Instruction text  
        instructions_text = [
            "INSTRUCTIONS:",
            "- Click hero buttons to deploy units (costs energy)",
            "- Each hero has unique skills and attacks",
            "- Defeat enemies to protect your base",
            "- Upgrade energy to increase max and regen rate",
            "- Destroy enemy base to win!"
        ]

        font_instr = pygame.font.Font(None, 24)
        title_font = pygame.font.Font(None, 30)
        start_y = ScreenManager.HEIGHT // 4 - 50

        for i, line in enumerate(instructions_text):
            if i == 0:
                text_surf = title_font.render(line, True, ScreenManager.BLACK)
            else:
                text_surf = font_instr.render(line, True, ScreenManager.BLACK)
            self.screen_mgr.surface.blit(
                text_surf,
                (ScreenManager.WIDTH // 2 - text_surf.get_width() // 2,
                start_y + i * 30)
            )

        # Draw PLAY button shadow
        shadow_offset = 4
        shadow_rect = self.play_button.move(shadow_offset, shadow_offset)
        pygame.draw.rect(self.screen_mgr.surface, (50, 50, 50), shadow_rect, border_radius=8)

        # Draw PLAY button
        pygame.draw.rect(self.screen_mgr.surface, (0, 200, 0), self.play_button, border_radius=8)
        pygame.draw.rect(self.screen_mgr.surface, (0, 0, 0), self.play_button, 2, border_radius=8)

        play_font = pygame.font.Font(None, 32)
        play_text = play_font.render("PLAY", True, (0, 0, 0))
        self.screen_mgr.surface.blit(
            play_text,
            (self.play_button.centerx - play_text.get_width() // 2,
            self.play_button.centery - play_text.get_height() // 2)
        )

        self.screen_mgr.update()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.play_button.collidepoint(event.pos):
            return "start"
        return None
    
class EndScreen:
    def __init__(self, screen_mgr, is_victory):
        self.screen_mgr = screen_mgr
        self.is_victory = is_victory
        self.button_rect = pygame.Rect(
            ScreenManager.WIDTH // 2 - 80,
            ScreenManager.HEIGHT // 2 + 60,
            160, 60
        )

    def draw(self):
        self.screen_mgr.fill(ScreenManager.WHITE)

        # Title
        title_font = pygame.font.Font(None, 60)
        title_text = "VICTORY!" if self.is_victory else "GAME OVER"
        title_color = ScreenManager.GREEN if self.is_victory else ScreenManager.RED
        title_surf = title_font.render(title_text, True, title_color)

        self.screen_mgr.surface.blit(
            title_surf,
            (ScreenManager.WIDTH // 2 - title_surf.get_width() // 2, ScreenManager.HEIGHT // 3)
        )

        # Subtitle
        sub_font = pygame.font.Font(None, 28)
        sub_text = "You destroyed the enemy base!" if self.is_victory else "Your base was destroyed!"
        sub_surf = sub_font.render(sub_text, True, ScreenManager.BLACK)

        self.screen_mgr.surface.blit(
            sub_surf,
            (ScreenManager.WIDTH // 2 - sub_surf.get_width() // 2, ScreenManager.HEIGHT // 3 + 50)
        )

        # Button shadow
        shadow_offset = 4
        shadow_rect = self.button_rect.move(shadow_offset, shadow_offset)
        pygame.draw.rect(self.screen_mgr.surface, (50, 50, 50), shadow_rect, border_radius=8)

        # Button
        pygame.draw.rect(self.screen_mgr.surface, (0, 200, 0), self.button_rect, border_radius=8)
        pygame.draw.rect(self.screen_mgr.surface, (0, 0, 0), self.button_rect, 2, border_radius=8)

        # Button text
        button_font = pygame.font.Font(None, 32)
        button_surf = button_font.render("PLAY AGAIN", True, (0, 0, 0))

        self.screen_mgr.surface.blit(
            button_surf,
            (self.button_rect.centerx - button_surf.get_width() // 2,
             self.button_rect.centery - button_surf.get_height() // 2)
        )

        self.screen_mgr.update()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.button_rect.collidepoint(event.pos):
            return "restart"
        return None


class GameManager:
    def __init__(self):
        self.screen_mgr = ScreenManager()
        self.player_base = Base(10, ScreenManager.GREEN, "assets/Base/Base1.png", scale_factor=6)
        self.enemy_base = Base(ScreenManager.WIDTH - 60, ScreenManager.RED, "assets/Base/Base2.png", scale_factor=3)
        self.heroes = []
        self.enemies = []
        self.projectiles = []
        self.dying_heroes = []
        self.enemy_base_target = BaseTarget(self.enemy_base)
        self.enemies.append(self.enemy_base_target)
        self.res_mgr = ResourceManager()
        self.enemy_img = AnimationManager.create_enemy_surface()

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
            HeroButton(100, Archer, 10, 1),
            HeroButton(190, Warrior, 15, 2),
            HeroButton(280, Mage, 20, 3),
            HeroButton(370, Healer, 15, 2)
        ]
        
        self.upgrade_button = UpgradeButton(520, ScreenManager.HEIGHT - 70, width=160)
        self.running = True

    def create_hero(self, cls):
        return cls(self.hero_sprites)

    def spawn_enemy(self):
        if random.randint(1, 100) > 98:
            self.enemies.append(Enemy(self.enemy_img))
            
    def update(self):
        for h in self.heroes[:]:
            h.update(self.enemies, self.heroes, self)

        for e in self.enemies[:]:
            e.update(self.heroes)

            if e.x <= 50 and not getattr(e, "is_dying", False):
                self.player_base.health -= 5
                e.alive = False
                e.is_dying = True
                self.enemies.remove(e)

        for proj in self.projectiles:
            proj.update()
        self.projectiles = [p for p in self.projectiles if p.alive]

        for h in self.heroes[:]:
            if h.is_dying:
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


    def draw(self):
        sm = self.screen_mgr
        font = pygame.font.Font(None, 24)
        sm.surface.blit(self.background, (0, 0))
        self.player_base.draw(sm.surface)
        self.upgrade_button.draw(sm.surface, font, self.res_mgr)
        for proj in self.projectiles:
            proj.draw(self.screen_mgr.surface)
        for h in self.heroes:
            h.draw(sm.surface)
        for e in self.enemies:
            e.draw(sm.surface)
        for h in self.dying_heroes:
            h.draw(sm.surface)
        font = pygame.font.Font(None, 24)
        for btn in self.hero_buttons:
            btn.draw(sm.surface, font, self.res_mgr)
        energy_text = f"Energy: {int(self.res_mgr.energy)} / {int(self.res_mgr.max_energy)}"
        energy_render = font.render(energy_text, True, ScreenManager.BLACK)
        sm.surface.blit(energy_render, (10, 10))
        
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

            elif game_state == "end":
                result = end_screen.handle_event(event)
                if result == "restart":
                    game = GameManager()  # restart game
                    game_state = "playing"

        # Drawing
        if game_state == "menu":
            main_menu.draw()

        elif game_state == "playing":
            game.spawn_enemy()
            game.update()
            game.draw()

            # Check for game over
            if not game.running:
                end_screen = EndScreen(screen_mgr, is_victory=game.enemy_base.health <= 0)
                game_state = "end"

        elif game_state == "end":
            end_screen.draw()

        screen_mgr.tick()

    screen_mgr.quit()

if __name__ == "__main__":
    main()
