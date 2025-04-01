import pygame
import random
import time

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

# Sprite sheet loader
def load_sprite_sheet_by_row(path, frame_width, frame_height):
    sheet = pygame.image.load(path).convert_alpha()
    rows = sheet.get_height() // frame_height
    cols = sheet.get_width() // frame_width
    animations = {}
    for row, name in enumerate(["move", "attack", "skill"]):
        frames = []
        for col in range(cols):
            frame = sheet.subsurface(pygame.Rect(col * frame_width, row * frame_height, frame_width, frame_height))
            frames.append(frame)
        animations[name] = frames
    return animations

class AnimationManager:
    @staticmethod
    def load_sprite_sheet_by_row(path, frame_width, frame_height):
        sheet = pygame.image.load(path).convert_alpha()
        rows = sheet.get_height() // frame_height
        cols = sheet.get_width() // frame_width
        animations = {}
        for row, name in enumerate(["move", "attack", "skill"]):
            frames = []
            for col in range(cols):
                frame = sheet.subsurface(pygame.Rect(col * frame_width, row * frame_height, frame_width, frame_height))
                frames.append(frame)
            animations[name] = frames
        return animations

    @staticmethod
    def load_hero_sprites():
        return {
            name: AnimationManager.load_sprite_sheet_by_row("Heros-go-/assets/temp_spritesheet.png", 40, 40)
            for name in ["Archer", "Warrior", "Mage", "Tank", "Healer"]
        }

    @staticmethod
    def create_enemy_surface():
        surface = pygame.Surface((40, 40))
        surface.fill(ScreenManager.RED)
        return surface

class Animation:
    def __init__(self, frames, interval=0.1):
        self.frames = frames
        self.interval = interval
        self.current_frame = 0
        self.last_frame_time = time.time()

    def update(self):
        if time.time() - self.last_frame_time > self.interval:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.last_frame_time = time.time()

    def get_frame(self):
        return self.frames[self.current_frame]

class Character:
    def __init__(self, x, y, health, speed):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = health
        self.speed = speed
        self.alive = True

    def move(self):
        if self.alive:
            self.x += self.speed

class Attack:
    def __init__(self, damage, attack_cooldown):
        self.damage = damage
        self.attack_cooldown = attack_cooldown
        self.last_attack_time = 0

    def can_attack(self):
        return time.time() - self.last_attack_time >= self.attack_cooldown

    def attack_target(self, target):
        if self.can_attack():
            target.health -= self.damage
            if target.health <= 0:
                target.alive = False
            self.last_attack_time = time.time()

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
        print("Shield applied (placeholder)")

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
    def __init__(self, name, skill_cooldown, effect: SkillEffect, skill_chance=1.0):
        self.name = name
        self.skill_cooldown = skill_cooldown
        self.effect = effect
        self.skill_chance = skill_chance
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
    def __init__(self, name, health, speed, damage, attack_cooldown, sprite_frames, skill=None):
        super().__init__(50, ScreenManager.HEIGHT // 2, health, speed)
        self.name = name
        self.attack = Attack(damage, attack_cooldown)
        self.skill = skill
        self.current_state = "move"
        self.animations = {state: Animation(sprite_frames[state]) for state in sprite_frames}

    def update_animation(self):
        self.animations[self.current_state].update()

    def draw(self, surface):
        if self.alive:
            self.update_animation()
            frame = self.animations[self.current_state].get_frame()
            surface.blit(frame, (self.x, self.y))

    def try_skill(self, targets):
        if self.skill and self.skill.can_use_skill():
            self.current_state = "skill"
            self.skill.use(self, targets)

    def try_attack(self, target):
        if self.attack.can_attack():
            self.current_state = "attack"
            self.attack.attack_target(target)

    def reset_state(self):
        self.current_state = "move"

class Mage(Hero):
    def __init__(self, sprites):
        super().__init__("Mage", 80, 1, 10, 1, sprites["Mage"], Skill("AOE", 3, AreaDamageEffect(), 0.6))
        self.attack_range = 350

    def update(self, enemies):
        in_range = [e for e in enemies if abs(self.x - e.x) <= self.attack_range and e.alive]
        if in_range:
            self.try_attack(in_range[0])
            self.try_skill(enemies)
        else:
            self.reset_state()
            self.move()

class Archer(Hero):
    def __init__(self, sprites):
        super().__init__("Archer", 60, 2, 5, 0.5, sprites["Archer"], Skill("Buff", 5, BuffAttackSpeedEffect(), 0.4))
        self.attack_range = 500

    def update(self, enemies):
        in_range = [e for e in enemies if abs(self.x - e.x) <= self.attack_range and e.alive]
        if in_range:
            self.try_attack(in_range[0])
            self.try_skill([])
        else:
            self.reset_state()
            self.move()

class Warrior(Hero):
    def __init__(self, sprites):
        super().__init__("Warrior", 150, 2, 15, 1.5, sprites["Warrior"], None)
        self.attack_range = 40

    def update(self, enemies):
        for enemy in enemies:
            if abs(self.x - enemy.x) <= self.attack_range:
                self.try_attack(enemy)
                return
        self.reset_state()
        self.move()

class Tank(Hero):
    def __init__(self, sprites):
        super().__init__("Tank", 300, 2, 0, 1, sprites["Tank"], Skill("Shield", 6, ShieldEffect(), 0.8))

    def update(self, enemies):
        close_enemies = [e for e in enemies if abs(self.x - e.x) < 40 and e.alive]
        if close_enemies:
            self.try_skill([])
        else:
            self.reset_state()
            self.move()

class Healer(Hero):
    def __init__(self, sprites):
        super().__init__("Healer", 70, 1.5, 0, 1, sprites["Healer"], Skill("Group Heal", 5, GroupHealEffect(), 1.0))
        self.heal_range = 100

    def update(self, heroes):
        near_allies = [a for a in heroes if a != self and a.alive and abs(self.x - a.x) <= self.heal_range]
        wounded = [a for a in near_allies if a.health < a.max_health]

        if wounded and self.skill.can_use_skill():
            self.try_skill(wounded)
        elif near_allies:
            self.reset_state()
        else:
            self.reset_state()
            self.move()

class Enemy(Character):
    def __init__(self, image):
        super().__init__(ScreenManager.WIDTH - 50, ScreenManager.HEIGHT // 2, 30, -1.5)
        self.attack = Attack(5, 1)
        self.image = image

    def update(self, heroes):
        for hero in heroes:
            if abs(self.x - hero.x) < 40:
                self.attack.attack_target(hero)
                return
        self.move()

    def draw(self, surface):
        if self.alive:
            surface.blit(self.image, (self.x, self.y))

class Base:
    def __init__(self, x, color):
        self.health = 100
        self.x = x
        self.color = color

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x, ScreenManager.HEIGHT // 2, 50, 50))
        pygame.draw.rect(surface, ScreenManager.WHITE, (self.x, ScreenManager.HEIGHT // 2 - 20, 50, 10))
        pygame.draw.rect(surface, ScreenManager.RED, (self.x, ScreenManager.HEIGHT // 2 - 20, self.health / 2, 10))

class ResourceManager:
    def __init__(self):
        self.energy = 100

    def can_afford(self, cost):
        return self.energy >= cost

    def spend(self, amount):
        self.energy -= amount

    def regenerate(self):
        if self.energy < 500:
            self.energy += 1

class HeroButton:
    def __init__(self, x, hero_type, cost, cooldown):
        self.x = x
        self.hero_type = hero_type
        self.cost = cost
        self.cooldown = cooldown
        self.last_pressed = 0
        self.rect = pygame.Rect(x, ScreenManager.HEIGHT - 50, 70, 30)

    def is_ready(self):
        return time.time() - self.last_pressed >= self.cooldown

    def draw(self, surface, font, res_mgr):
        color = ScreenManager.GREEN if self.is_ready() and res_mgr.can_afford(self.cost) else ScreenManager.RED
        pygame.draw.rect(surface, color, self.rect)
        label = font.render(self.hero_type.__name__, True, ScreenManager.BLACK)
        surface.blit(label, (self.x + 7.5, ScreenManager.HEIGHT - 45))

    def try_spawn(self, game):
        if self.is_ready() and game.res_mgr.can_afford(self.cost):
            hero = game.create_hero(self.hero_type)
            game.heroes.append(hero)
            game.res_mgr.spend(self.cost)
            self.last_pressed = time.time()

class GameManager:
    def __init__(self):
        screen_mgr = ScreenManager()
        self.screen_mgr = screen_mgr
        self.player_base = Base(10, ScreenManager.GREEN)
        self.enemy_base = Base(ScreenManager.WIDTH - 60, ScreenManager.RED)
        self.heroes = []
        self.enemies = []
        self.res_mgr = ResourceManager()
        self.hero_sprites = AnimationManager.load_hero_sprites()
        self.enemy_img = AnimationManager.create_enemy_surface()
        self.hero_buttons = [
            HeroButton(100, Archer, 10, 1),
            HeroButton(180, Warrior, 15, 2),
            HeroButton(260, Mage, 20, 3),
            HeroButton(340, Tank, 20, 4),
            HeroButton(420, Healer, 15, 2)
        ]
        self.running = True


    def spawn_enemy(self):
        if random.randint(1, 100) > 98:
            self.enemies.append(Enemy(self.enemy_img))
            
    def create_hero(self, hero_class):
        return hero_class(self.hero_sprites)

    def update(self):
        for hero in self.heroes:
            if isinstance(hero, Healer):
                hero.update(self.heroes)
            else:
                hero.update(self.enemies)

        for enemy in self.enemies:
            enemy.update(self.heroes)

        self.heroes = [h for h in self.heroes if h.alive]
        self.enemies = [e for e in self.enemies if e.alive]

        for hero in self.heroes:
            if hero.x >= ScreenManager.WIDTH - 60:
                self.enemy_base.health -= 5
                hero.alive = False

        for enemy in self.enemies:
            if enemy.x <= 50:
                self.player_base.health -= 5
                enemy.alive = False

        self.res_mgr.regenerate()

        if self.player_base.health <= 0:
            self.running = False
            print("Game Over! You lost!")
        elif self.enemy_base.health <= 0:
            self.running = False
            print("Victory! You won!")

    def draw(self):
        self.screen_mgr.fill(ScreenManager.WHITE)
        self.player_base.draw(self.screen_mgr.surface)
        self.enemy_base.draw(self.screen_mgr.surface)

        for hero in self.heroes:
            hero.draw(self.screen_mgr.surface)
        for enemy in self.enemies:
            enemy.draw(self.screen_mgr.surface)

        font = pygame.font.Font(None, 24)
        for btn in self.hero_buttons:
            btn.draw(self.screen_mgr.surface, font, self.res_mgr)

        energy_text = font.render(f"Energy: {int(self.res_mgr.energy)}", True, ScreenManager.BLACK)
        self.screen_mgr.surface.blit(energy_text, (10, 10))
        self.screen_mgr.update()


def main():
    game = GameManager()
    while game.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for btn in game.hero_buttons:
                    if btn.rect.collidepoint(event.pos):
                        btn.try_spawn(game)

        game.spawn_enemy()
        game.update()
        game.draw()

        game.screen_mgr.tick()

    game.screen_mgr.quit()

if __name__ == "__main__":
    main()
