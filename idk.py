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

class Hero(Character):
    def __init__(self, name, health, speed, dmg, atk_cd, anims):
        super().__init__(50, ScreenManager.HEIGHT // 2, health, speed)
        self.name = name
        self.attack = Attack(dmg, atk_cd)
        self.animations = {k: Animation(v) for k, v in anims.items()}
        self.current_state = "move"

    def update_animation(self):
        if self.current_state in self.animations:
            self.animations[self.current_state].update()

    def draw(self, surface):
        if self.alive and self.current_state in self.animations:
            self.update_animation()
            frame = self.animations[self.current_state].get_frame()
            surface.blit(frame, (self.x, self.y))

    def try_attack(self, target):
        if self.attack.can_attack():
            self.current_state = "attack"
            self.attack.attack_target(target)

    def reset_state(self):
        self.current_state = "move"

    def update(self, enemies):
        for e in enemies:
            if abs(self.x - e.x) < 40:
                self.try_attack(e)
                return
        self.reset_state()
        self.move()

class Enemy(Character):
    def __init__(self, image):
        super().__init__(ScreenManager.WIDTH - 50, ScreenManager.HEIGHT // 2, 30, -1.5)
        self.attack = Attack(5, 1)
        self.image = image

    def update(self, heroes):
        for h in heroes:
            if abs(self.x - h.x) < 40:
                self.attack.attack_target(h)
                return
        self.move()

    def draw(self, surface):
        if self.alive:
            surface.blit(self.image, (self.x, self.y))

class Base:
    def __init__(self, x, color):
        self.x = x
        self.health = 100
        self.color = color

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x, ScreenManager.HEIGHT // 2, 50, 50))
        pygame.draw.rect(surface, ScreenManager.RED, (self.x, ScreenManager.HEIGHT // 2 - 20, self.health / 2, 10))

class ResourceManager:
    def __init__(self):
        self.energy = 100

    def can_afford(self, cost): return self.energy >= cost
    def spend(self, amt): self.energy -= amt
    def regenerate(self):
        if self.energy < 500:
            self.energy += 1

class HeroButton:
    def __init__(self, x, cls, cost, cooldown):
        self.x = x
        self.cls = cls
        self.cost = cost
        self.cd = cooldown
        self.last = 0
        self.rect = pygame.Rect(x, ScreenManager.HEIGHT - 50, 70, 30)

    def is_ready(self): return time.time() - self.last >= self.cd

    def draw(self, surface, font, res_mgr):
        c = ScreenManager.GREEN if self.is_ready() and res_mgr.can_afford(self.cost) else ScreenManager.RED
        pygame.draw.rect(surface, c, self.rect)
        surface.blit(font.render(self.cls.__name__, True, ScreenManager.BLACK), (self.x + 7, ScreenManager.HEIGHT - 45))

    def try_spawn(self, game):
        if self.is_ready() and game.res_mgr.can_afford(self.cost):
            game.heroes.append(game.create_hero(self.cls))
            game.res_mgr.spend(self.cost)
            self.last = time.time()

class GameManager:
    def __init__(self):
        self.screen_mgr = ScreenManager()
        self.player_base = Base(10, ScreenManager.GREEN)
        self.enemy_base = Base(ScreenManager.WIDTH - 60, ScreenManager.RED)
        self.heroes = []
        self.enemies = []
        self.res_mgr = ResourceManager()
        self.enemy_img = AnimationManager.create_enemy_surface()

        folder = "Heros-go-/assets/Fighter"
        fighter_anims = AnimationManager.load_animations_from_folder(folder)

        self.hero_sprites = {
            name: {
                "move": fighter_anims.get("run", []),
                "attack": fighter_anims.get("attack_2", []),
                "skill": fighter_anims.get("idle", [])
            } for name in ["Archer", "Warrior", "Mage", "Tank", "Healer"]
        }

        self.hero_buttons = [
            HeroButton(100, Hero, 10, 1),
            HeroButton(180, Hero, 15, 2),
            HeroButton(260, Hero, 20, 3),
            HeroButton(340, Hero, 20, 4),
            HeroButton(420, Hero, 15, 2)
        ]
        self.running = True

    def create_hero(self, cls):
        return Hero("Fighter", 100, 2, 10, 1, self.hero_sprites["Warrior"])

    def spawn_enemy(self):
        if random.randint(1, 100) > 98:
            self.enemies.append(Enemy(self.enemy_img))

    def update(self):
        for h in self.heroes:
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
        sm.fill(ScreenManager.WHITE)
        self.player_base.draw(sm.surface)
        self.enemy_base.draw(sm.surface)
        for h in self.heroes:
            h.draw(sm.surface)
        for e in self.enemies:
            e.draw(sm.surface)
        font = pygame.font.Font(None, 24)
        for btn in self.hero_buttons:
            btn.draw(sm.surface, font, self.res_mgr)
        sm.surface.blit(font.render(f"Energy: {int(self.res_mgr.energy)}", True, ScreenManager.BLACK), (10, 10))
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
