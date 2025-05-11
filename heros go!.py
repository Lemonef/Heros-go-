from core.screen import ScreenManager
from ui.menu import MainMenu, EndScreen
from settings.settings_window import SettingsWindow
from units.base import Base, BaseTarget
from units.hero import Archer, Warrior, Mage, Healer
from units.enemy import Enemy
from core.animation import AnimationManager
from core.tracker import Tracker
from core.resource import ResourceManager
from ui.button import HeroButton, UpgradeButton, Button
import pygame
import tkinter as tk
import time
import random

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

        blue = AnimationManager.load_animations_from_folder("assets/Enemy/Blue_Slime")
        green = AnimationManager.load_animations_from_folder("assets/Enemy/Green_Slime")
        red = AnimationManager.load_animations_from_folder("assets/Enemy/Red_Slime")

        self.enemy_sprites = {
            "Blue_Slime": {"move": blue.get("run", []), "attack": blue.get("attack_1", []), "dead": blue.get("dead", [])},
            "Green_Slime": {"move": green.get("run", []), "attack": green.get("attack_1", []), "dead": green.get("dead", [])},
            "Red_Slime": {"move": red.get("run", []), "attack": red.get("attack_1", []), "dead": red.get("dead", [])},
        }

        fighter = AnimationManager.load_animations_from_folder("assets/Fighter")
        archer = AnimationManager.load_animations_from_folder("assets/Samurai")
        mage = AnimationManager.load_animations_from_folder("assets/Mage")
        healer = AnimationManager.load_animations_from_folder("assets/Healer")

        bg = pygame.image.load("assets/Background/Stage1.png").convert()
        cropped = bg.subsurface(pygame.Rect(0, 0, bg.get_width(), bg.get_height() - 50))
        self.background = pygame.transform.scale(cropped, (ScreenManager.WIDTH, ScreenManager.HEIGHT))

        self.hero_sprites = {
            "Archer": {"move": archer["run"], "attack": archer["attack_2"], "skill": archer["idle"], "dead": archer["dead"]},
            "Warrior": {"move": fighter["run"], "attack": fighter["attack_2"], "skill": fighter["idle"], "dead": fighter["dead"]},
            "Mage": {"move": mage["walk"], "attack": mage["attack_1"], "skill": mage["attack_2"], "dead": mage["dead"]},
            "Healer": {"move": healer["walk"], "attack": healer["attack_4"], "skill": healer["scream"], "dead": healer["dead"]},
        }

        self.hero_buttons = [
            HeroButton(100, Archer, 20, 3),
            HeroButton(190, Warrior, 10, 2),
            HeroButton(280, Mage, 20, 3),
            HeroButton(370, Healer, 15, 2),
        ]

        self.upgrade_button = UpgradeButton(520, ScreenManager.HEIGHT - 70, width=160)
        self.settings_button = Button(
            rect=(ScreenManager.WIDTH - 120, 10, 100, 40),
            label="Settings", on_click=lambda: self.settings.run(),
            color=(200, 200, 200), font_size=20
        )

        self.paused = False
        self.running = True
        self.was_forced_quit = False

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
            choice = random.choice(list(self.enemy_sprites.keys()))
            anims = self.enemy_sprites[choice]
            self.enemies.append(Enemy(anims))
            self.last_spawn_time = now
            self.spawn_interval = random.uniform(0.5, 2.0)

    def update(self):
        if self.paused:
            return
        for h in self.heroes[:]:
            h.update(self.enemies, self.heroes, self)

        for e in self.enemies[:]:
            e.update(self.heroes)
            if not e.alive and not getattr(e, '_death_logged', False):
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
                    main_menu.result = None
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
                    game = GameManager()
                    game.tracker.snapshot_data.clear()
                    game_state = "playing"
                elif result == "home":
                    main_menu = MainMenu(screen_mgr)
                    game_state = "menu"

        if game_state == "menu":
            main_menu.draw()
        elif game_state == "playing":
            if not game.paused:
                game.spawn_enemy()
                game.update()
            game.draw()
            if not game.running:
                game.tracker.append_new_rows()
                if game.was_forced_quit:
                    end_screen = EndScreen(screen_mgr, is_victory=None)
                else:
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
        game.tracker.append_new_rows()
    screen_mgr.quit()

if __name__ == "__main__":
    main()