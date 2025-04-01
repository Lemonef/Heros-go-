import pygame
import random
import time

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 400
WHITE = (255, 255, 255)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
BLACK = (0, 0, 0)
FPS = 60

# Init
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Battle Heroes Defense")

# Sprite loading
def load_sprite_sheet(path, frame_width, frame_height):
    sheet = pygame.image.load(path).convert_alpha()
    frames = []
    for i in range(sheet.get_width() // frame_width):
        frame = sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height))
        frames.append(frame)
    return frames

hero_sprites = {
    "Archer": load_sprite_sheet("assets/archer.png", 40, 40),
    "Warrior": load_sprite_sheet("assets/warrior.png", 40, 40),
    "Mage": load_sprite_sheet("assets/mage.png", 40, 40),
    "Tank": load_sprite_sheet("assets/tank.png", 40, 40),
    "Healer": load_sprite_sheet("assets/healer.png", 40, 40),
}

enemy_img = pygame.Surface((40, 40))
enemy_img.fill(RED)

# Skill Effect base
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
        print("Granting temporary shield or HP buff (placeholder)")

class GroupHealEffect(SkillEffect):
    def __init__(self, heal_amount=15):
        self.heal_amount = heal_amount

    def apply(self, user, targets):
        for t in targets:
            if t.alive:
                t.health += self.heal_amount

# Skill class
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


# Animation
class Animation:
    def __init__(self, frames, interval=0.1):
        self.frames = frames
        self.current_frame = 0
        self.last_frame_time = time.time()
        self.interval = interval

    def update(self):
        if time.time() - self.last_frame_time > self.interval:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.last_frame_time = time.time()

    def get_frame(self):
        return self.frames[self.current_frame]

# Character
class Character:
    def __init__(self, x, y, health, speed):
        self.x = x
        self.y = y
        self.health = health
        self.speed = speed
        self.alive = True

    def move(self):
        if self.alive:
            self.x += self.speed

# Attack
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

# Hero base class
class Hero(Character):
    def __init__(self, name, health, speed, damage, attack_cooldown, sprite_frames, skill=None):
        super().__init__(50, SCREEN_HEIGHT // 2, health, speed)
        self.name = name
        self.attack = Attack(damage, attack_cooldown)
        self.animation = Animation(sprite_frames)
        self.skill = skill

    def update_animation(self):
        self.animation.update()

    def draw(self, screen):
        if self.alive:
            self.update_animation()
            screen.blit(self.animation.get_frame(), (self.x, self.y))

    def try_skill(self, targets):
        if self.skill:
            self.skill.use(self, targets)

# Enemy
class Enemy(Character):
    def __init__(self):
        super().__init__(SCREEN_WIDTH - 50, SCREEN_HEIGHT // 2, 30, -1.5)
        self.attack = Attack(5, 1)

    def update(self, heroes):
        for hero in heroes:
            if abs(self.x - hero.x) < 40:
                self.attack.attack_target(hero)
                return
        self.move()

    def draw(self, screen):
        if self.alive:
            screen.blit(enemy_img, (self.x, self.y))


# Hero subclasses
class Mage(Hero):
    def __init__(self):
        super().__init__("Mage", 80, 1, 10, 1, hero_sprites["Mage"], Skill("AOE", 3, AreaDamageEffect()))
        self.attack_range = 350

    def update(self, enemies):
        in_range = [e for e in enemies if abs(self.x - e.x) <= self.attack_range and e.alive]
        if in_range:
            self.attack.attack_target(in_range[0])
            self.try_skill(enemies)
        else:
            self.move()

class Archer(Hero):
    def __init__(self):
        super().__init__("Archer", 60, 2, 5, 0.5, hero_sprites["Archer"], Skill("Buff", 5, BuffAttackSpeedEffect()))
        self.attack_range = 500

    def update(self, enemies):
        in_range = [e for e in enemies if abs(self.x - e.x) <= self.attack_range and e.alive]
        if in_range:
            self.attack.attack_target(in_range[0])
            self.try_skill([])
        else:
            self.move()

class Warrior(Hero):
    def __init__(self):
        super().__init__("Warrior", 150, 2, 15, 1.5, hero_sprites["Warrior"], None)
        self.attack_range = 40

    def update(self, enemies):
        for enemy in enemies:
            if abs(self.x - enemy.x) <= self.attack_range:
                self.attack.attack_target(enemy)
                return
        self.move()

class Tank(Hero):
    def __init__(self):
        super().__init__("Tank", 300, 2, 0, 1, hero_sprites["Tank"], Skill("Shield", 6, ShieldEffect()))

    def update(self, enemies):
        close_enemies = [e for e in enemies if abs(self.x - e.x) < 40 and e.alive]
        if close_enemies:
            self.try_skill([])
        else:
            self.move()

class Healer(Hero):
    def __init__(self):
        super().__init__("Healer", 70, 1.5, 0, 1, hero_sprites["Healer"], Skill("Group Heal", 5, GroupHealEffect()))
        self.heal_range = 100

    def update(self, heroes):
        for ally in heroes:
            if ally != self and ally.alive and abs(self.x - ally.x) <= self.heal_range:
                self.try_skill(heroes)
                return
        self.move()

# Base
class Base:
    def __init__(self, x, color):
        self.health = 100
        self.x = x
        self.color = color

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, SCREEN_HEIGHT // 2, 50, 50))
        pygame.draw.rect(screen, WHITE, (self.x, SCREEN_HEIGHT // 2 - 20, 50, 10))
        pygame.draw.rect(screen, RED, (self.x, SCREEN_HEIGHT // 2 - 20, self.health / 2, 10))

# Resource Manager
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

# Hero Button
class HeroButton:
    def __init__(self, x, hero_type, cost, cooldown):
        self.x = x
        self.hero_type = hero_type
        self.cost = cost
        self.cooldown = cooldown
        self.last_pressed = 0
        self.rect = pygame.Rect(x, SCREEN_HEIGHT - 50, 70, 30)

    def is_ready(self):
        return time.time() - self.last_pressed >= self.cooldown

    def draw(self, screen, font, res_mgr):
        color = GREEN if self.is_ready() and res_mgr.can_afford(self.cost) else RED
        pygame.draw.rect(screen, color, self.rect)
        label = font.render(self.hero_type.__name__, True, BLACK)
        screen.blit(label, (self.x + 7.5, SCREEN_HEIGHT - 45))

    def try_spawn(self, game):
        if self.is_ready() and game.res_mgr.can_afford(self.cost):
            hero = self.hero_type()
            game.heroes.append(hero)
            game.res_mgr.spend(self.cost)
            self.last_pressed = time.time()

# Game Manager
class GameManager:
    def __init__(self):
        self.player_base = Base(10, GREEN)
        self.enemy_base = Base(SCREEN_WIDTH - 60, RED)
        self.heroes = []
        self.enemies = []
        self.res_mgr = ResourceManager()
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
            self.enemies.append(Enemy())

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
            if hero.x >= SCREEN_WIDTH - 60:
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
        screen.fill(WHITE)
        self.player_base.draw(screen)
        self.enemy_base.draw(screen)

        for hero in self.heroes:
            hero.draw(screen)
        for enemy in self.enemies:
            enemy.draw(screen)

        font = pygame.font.Font(None, 24)
        for btn in self.hero_buttons:
            btn.draw(screen, font, self.res_mgr)

        energy_text = font.render(f"Energy: {int(self.res_mgr.energy)}", True, BLACK)
        screen.blit(energy_text, (10, 10))

# Main loop
clock = pygame.time.Clock()
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

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()