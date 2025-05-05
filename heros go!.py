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
    def __init__(self, frames, interval=0.1):
        self.frames = frames
        self.interval = interval
        self.index = 0
        self.last_time = time.time()

    def update(self):
        if time.time() - self.last_time >= self.interval:
            self.index = (self.index + 1) % len(self.frames)
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
            target.health -= self.dmg
            target.alive = target.health > 0
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
        print("Buffing ally attack speed (placeholder)")

class ShieldEffect(SkillEffect):
    def apply(self, user, targets):
        if targets:
            print("Shield applied (placeholder)")
        else:
            print("Shield activated, but no targets.")

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
        if healed:
            print("Healing allies (placeholder)")
        else:
            print("Heal activated, but no targets needed healing.")

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
        self.skill_anim_start_time = 0
        self.skill_anim_duration = 0
        self.skill_completed = False


    def update_animation(self):
        if self.current_state == "skill":
            elapsed = time.time() - self.skill_anim_start_time
            if elapsed >= self.skill_anim_duration and not self.skill_completed:
                print(f"Skill animation completed after {elapsed} seconds")
                self.skill_completed = True
                self.reset_state()

        if self.current_state in self.animations:
            self.animations[self.current_state].update()


    def draw(self, surface):
        if self.alive and self.current_state in self.animations:
            self.update_animation()
            frame = self.animations[self.current_state].get_frame()
            surface.blit(frame, (self.x - frame.get_width() // 2, self.y))

    def try_attack(self, target):
        if self.attack.can_attack():
            self.current_state = "attack"
            self.attack.attack_target(target)
        
    def try_skill(self, targets):
        if self.skill and self.skill.can_use_skill():
            self.current_state = "skill"
            self.skill.use(self, targets)
            self.skill_anim_start_time = time.time()
            self.skill_anim_duration = self.skill.cast_duration
            self.skill_completed = False

    def reset_state(self):
        if self.current_state != "skill": 
            self.current_state = "move"

    def update(self, enemies):
        for e in enemies:
            if abs(self.x - e.x) < 40:
                self.try_attack(e)
                return
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

    def update(self, enemies, allies):
        in_range = [e for e in enemies if abs(self.x - e.x) <= self.attack_range and e.alive]
        nearby_allies = [a for a in allies if a != self and a.alive and abs(self.x - a.x) <= self.buff_range]

        if in_range:
            self.try_attack(in_range[0])
            self.try_skill(nearby_allies)
        else:
            self.reset_state()
            self.move()

class Warrior(Hero):
    def __init__(self, sprites):
        super().__init__("Warrior", 150, 2, 15, 0.5, sprites["Warrior"])
        self.attack_range = 40

    def update(self, enemies):
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

    def update(self, enemies):
        in_range = [e for e in enemies if abs(self.x - e.x) <= self.attack_range and e.alive]
        if in_range:
            self.try_attack(in_range[0])
            self.try_skill(enemies)
        else:
            self.reset_state()
            self.move()

class Tank(Hero):
    def __init__(self, sprites):
        super().__init__(
            "Tank", 300, 2, 0, 1, sprites["Tank"],
            Skill("Shield", 6, ShieldEffect(), 0.8)
        )
        self.attack_range = 40
        self.shield_trigger_range = 150

class Healer(Hero):
    def __init__(self, sprites):
        super().__init__(
            "Healer", 70, 1.5, 3, 1, sprites["Healer"],
            Skill("Group Heal", 5, GroupHealEffect(), 1.0, cast_duration=1.5)
        )
        self.attack_range = 200
        self.heal_range = 150

    def update(self, enemies, allies):
        in_range = [e for e in enemies if e.alive and abs(self.x - e.x) <= self.attack_range]
        nearby_allies = [a for a in allies if a != self and a.alive and a.health < a.max_health and abs(self.x - a.x) <= self.heal_range]

        if in_range:
            self.try_attack(in_range[0])
            self.try_skill(nearby_allies)
        else:
            self.reset_state()
            self.move()

class Enemy(Character):
    def __init__(self, image):
        center_x = ScreenManager.WIDTH - 50
        super().__init__(center_x, ScreenManager.HEIGHT // 2, 30, -1.5)
        self.attack = Attack(5, 1)
        self.image = image
        self.width = self.image.get_width()

    def update(self, heroes):
        for hero in heroes:
            hero_center = hero.x + 20  # assuming 40px hero
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



class ResourceManager:
    def __init__(self):
        self.energy = 100

    def can_afford(self, cost): return self.energy >= cost
    def spend(self, amt): self.energy -= amt
    def regenerate(self):
        if self.energy < 100:
            self.energy += 0.1

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

class GameManager:
    def __init__(self):
        self.screen_mgr = ScreenManager()
        self.player_base = Base(10, ScreenManager.GREEN, "assets/Base/Base1.png", scale_factor=6)
        self.enemy_base = Base(ScreenManager.WIDTH - 60, ScreenManager.RED, "assets/Base/Base2.png", scale_factor=3)
        self.heroes = []
        self.enemies = []
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
            },
            "Warrior": {
                "move": fighter_anims.get("run", []),
                "attack": fighter_anims.get("attack_2", []),
                "skill": fighter_anims.get("idle", []),
            },
            "Mage": {
                "move": mage_anims.get("walk", []), 
                "attack": mage_anims.get("attack_1", []),
                "skill": mage_anims.get("attack_2", []),
            },
            "Healer": {
                "move": healer_anims.get("walk", []),
                "attack": healer_anims.get("attack_4", []),
                "skill": healer_anims.get("scream", []),
            }
        }


        self.hero_buttons = [
            HeroButton(100, Archer, 10, 1),
            HeroButton(190, Warrior, 15, 2),
            HeroButton(280, Mage, 20, 3),
            HeroButton(370, Healer, 15, 2)
        ]
        self.running = True

    def create_hero(self, cls):
        return cls(self.hero_sprites)

    def spawn_enemy(self):
        if random.randint(1, 100) > 98:
            self.enemies.append(Enemy(self.enemy_img))

    def update(self):
        for h in self.heroes:
            if isinstance(h, (Healer, Archer, Tank)):
                h.update(self.enemies, self.heroes)
            else:
                h.update(self.enemies)
        for e in self.enemies:
            e.update(self.heroes)
        self.heroes = [h for h in self.heroes if h.alive]
        self.enemies = [e for e in self.enemies if e.alive]
        for h in self.heroes:
            if h.x >= ScreenManager.WIDTH - 60:
                self.enemy_base.health -= 5
                h.alive = False
        for e in self.enemies:
            if e.x <= 50:
                self.player_base.health -= 5
                e.alive = False
        self.res_mgr.regenerate()
        if self.player_base.health <= 0:
            self.running = False
            print("Game Over! You lost!")
        elif self.enemy_base.health <= 0:
            self.running = False
            print("Victory! You won!")

    def draw(self):
        sm = self.screen_mgr
        sm.surface.blit(self.background, (0, 0))
        self.player_base.draw(sm.surface)
        self.enemy_base.draw(sm.surface)
        for h in self.heroes:
            h.draw(sm.surface)
        for e in self.enemies:
            e.draw(sm.surface)
        font = pygame.font.Font(None, 24)
        for btn in self.hero_buttons:
            btn.draw(sm.surface, font, self.res_mgr)
        sm.surface.blit(font.render(f"Energy: {int(self.res_mgr.energy)} / 100", True, ScreenManager.BLACK), (10, 10))
        sm.update()

def main():
    game = GameManager()
    while game.running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                game.running = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                for b in game.hero_buttons:
                    if b.rect.collidepoint(e.pos):
                        b.try_spawn(game)
        game.spawn_enemy()
        game.update()
        game.draw()
        game.screen_mgr.tick()
    game.screen_mgr.quit()

if __name__ == "__main__":
    main()
