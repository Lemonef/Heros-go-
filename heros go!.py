import pygame
import random
import time

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 400
WHITE = (255, 255, 255)
RED = (200, 0, 0)
BLUE = (0, 0, 200)
GREEN = (0, 200, 0)
BLACK = (0, 0, 0)
YELLOW = (200, 200, 0)
PURPLE = (150, 0, 200)
GRAY = (100, 100, 100)
FPS = 60

# Init
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Battle Heroes Defense")

# Placeholder Assets
hero_imgs = {
    "Archer": pygame.Surface((40, 40)),
    "Warrior": pygame.Surface((40, 40)),
    "Mage": pygame.Surface((40, 40)),
    "Tank": pygame.Surface((40, 40)),
    "Healer": pygame.Surface((40, 40))
}
hero_imgs["Archer"].fill(YELLOW)
hero_imgs["Warrior"].fill(BLUE)
hero_imgs["Mage"].fill(PURPLE)
hero_imgs["Tank"].fill(GRAY)
hero_imgs["Healer"].fill(GREEN)

enemy_img = pygame.Surface((40, 40))
enemy_img.fill(RED)


# Character Base Class
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

# Enemy Class
class Enemy(Character):
    def __init__(self):
        super().__init__(SCREEN_WIDTH - 50, SCREEN_HEIGHT // 2, 30, -1.5)
        self.attack = 5

    def attack_hero(self, hero):
        hero.health -= self.attack
        if hero.health <= 0:
            hero.alive = False

    def draw(self, screen):
        if self.alive:
            screen.blit(enemy_img, (self.x, self.y))

# Hero Base Class
class Hero(Character):
    def __init__(self, name, health, speed):
        super().__init__(50, SCREEN_HEIGHT // 2, health, speed)
        self.name = name
        self.attack = 0
        self.attack_cooldown = 1
        self.last_attack = 0

    def can_attack(self):
        return time.time() - self.last_attack >= self.attack_cooldown

    def draw(self, screen):
        if self.alive:
            screen.blit(hero_imgs[self.name], (self.x, self.y))

# Archer
class Archer(Hero):
    def __init__(self):
        super().__init__("Archer", 60, 2)
        self.attack = 5
        self.attack_range = 100
        self.attack_cooldown = 0.5

    def update(self, enemies):
        self.move()
        for enemy in enemies:
            if abs(self.x - enemy.x) <= self.attack_range and self.can_attack():
                enemy.health -= self.attack
                if enemy.health <= 0:
                    enemy.alive = False
                self.last_attack = time.time()
                break

# Warrior
class Warrior(Hero):
    def __init__(self):
        super().__init__("Warrior", 150, 1.5)
        self.attack = 15
        self.attack_range = 40
        self.attack_cooldown = 1.5

    def update(self, enemies):
        self.move()
        for enemy in enemies:
            if abs(self.x - enemy.x) <= self.attack_range and self.can_attack():
                enemy.health -= self.attack
                if enemy.health <= 0:
                    enemy.alive = False
                self.last_attack = time.time()
                break

# Mage
class Mage(Hero):
    def __init__(self):
        super().__init__("Mage", 80, 1.2)
        self.attack = 10
        self.attack_range = 120
        self.attack_cooldown = 2

    def update(self, enemies):
        for enemy in enemies:
            if abs(self.x - enemy.x) <= self.attack_range:
                if self.can_attack():
                    for e in enemies:
                        if abs(self.x - e.x) <= 50:
                            e.health -= self.attack
                            if e.health <= 0:
                                e.alive = False
                    self.last_attack = time.time()
                return
        self.move()

# Tank
class Tank(Hero):
    def __init__(self):
        super().__init__("Tank", 300, 1)
        self.attack = 0

    def update(self, enemies):
        for enemy in enemies:
            if abs(self.x - enemy.x) < 40:
                return  # stop moving
        self.move()

# Healer
class Healer(Hero):
    def __init__(self):
        super().__init__("Healer", 70, 1.5)
        self.heal_amount = 5
        self.heal_range = 100
        self.attack_cooldown = 1

    def update(self, heroes):
        for ally in heroes:
            if ally != self and ally.alive and abs(self.x - ally.x) <= self.heal_range and self.can_attack():
                ally.health += self.heal_amount
                self.last_attack = time.time()
                return
        self.move()

# Base Class
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
        self.energy += 2

# Hero Button
class HeroButton:
    def __init__(self, x, hero_type, cost, cooldown):
        self.x = x
        self.hero_type = hero_type
        self.cost = cost
        self.cooldown = cooldown
        self.last_pressed = 0
        self.rect = pygame.Rect(x, SCREEN_HEIGHT - 50, 60, 30)

    def is_ready(self):
        return time.time() - self.last_pressed >= self.cooldown

    def draw(self, screen, font, res_mgr):
        color = GREEN if self.is_ready() and res_mgr.can_afford(self.cost) else RED
        pygame.draw.rect(screen, color, self.rect)
        label = font.render(self.hero_type.__name__, True, BLACK)
        screen.blit(label, (self.x + 5, SCREEN_HEIGHT - 45))

    def try_spawn(self, game):
        if self.is_ready() and game.res_mgr.can_afford(self.cost):
            game.heroes.append(self.hero_type())
            game.res_mgr.spend(self.cost)
            self.last_pressed = time.time()

# GameManager
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

        self.enemies = [e for e in self.enemies if e.alive]

        for enemy in self.enemies:
            enemy.move()
            for hero in self.heroes:
                if abs(hero.x - enemy.x) < 40:
                    enemy.attack_hero(hero)

        self.heroes = [h for h in self.heroes if h.alive]

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

# Main Loop
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