import pygame
from core.screen import ScreenManager
from ui.button import Button

class Menu:
    def __init__(self, screen_mgr, bg_image_path):
        self.screen_mgr = screen_mgr
        self.result = None
        full_bg = pygame.image.load(bg_image_path).convert()
        cropped_height = full_bg.get_height() - 50
        cropped_bg = full_bg.subsurface(pygame.Rect(0, 0, full_bg.get_width(), cropped_height))
        self.background = pygame.transform.scale(cropped_bg, (ScreenManager.WIDTH, ScreenManager.HEIGHT))
        self.buttons = []

    def draw_background(self):
        surface = self.screen_mgr.surface
        surface.blit(self.background, (0, 0))

    def draw_buttons(self):
        for btn in self.buttons:
            btn.draw(self.screen_mgr.surface)

    def handle_event(self, event):
        for btn in self.buttons:
            btn.handle_event(event)
        return self.result

    def draw(self):
        self.draw_background()
        self.draw_buttons()
        self.screen_mgr.update()

class MainMenu(Menu):
    def __init__(self, screen_mgr):
        super().__init__(screen_mgr, "assets/Background/Stage3.png")
        self.play_button = Button(
            rect=(ScreenManager.WIDTH // 2 - 60, ScreenManager.HEIGHT // 2 + 100, 120, 55),
            label="PLAY", on_click=self.start_game, color=(0, 200, 0)
        )
        self.quit_button = Button(
            rect=(ScreenManager.WIDTH - 110, 10, 100, 40),
            label="QUIT", on_click=self.quit_game, color=(200, 50, 50), text_color=(255, 255, 255), font_size=20
        )
        self.buttons = [self.play_button, self.quit_button]

    def start_game(self):
        self.result = "start"

    def quit_game(self):
        pygame.quit()
        import sys
        sys.exit()

    def draw(self):
        super().draw_background()
        instructions = [
            "INSTRUCTIONS:",
            "- Click hero buttons to deploy units (costs energy)",
            "- Each hero has unique skills and attacks",
            "- Defeat enemies to protect your base",
            "- Upgrade energy to increase max and regen rate",
            "- Win to advance to the next stage!",
            "- Destroy enemy base to win!"
        ]
        font_title = pygame.font.Font(None, 30)
        font_instr = pygame.font.Font(None, 22)
        y_start = ScreenManager.HEIGHT // 4 - 20
        for i, line in enumerate(instructions):
            font = font_title if i == 0 else font_instr
            surf = font.render(line, True, ScreenManager.BLACK)
            self.screen_mgr.surface.blit(surf, (ScreenManager.WIDTH // 2 - surf.get_width() // 2, y_start + i * 30))
        super().draw_buttons()
        self.screen_mgr.update()

class EndScreen(Menu):
    def __init__(self, screen_mgr, is_victory):
        super().__init__(screen_mgr, "assets/Background/Stage2.png")
        self.is_victory = is_victory
        self.play_again_btn = Button(
            rect=(ScreenManager.WIDTH // 2 - 180, ScreenManager.HEIGHT // 2 + 40, 160, 60),
            label="PLAY AGAIN", on_click=self.restart_game, color=(0, 200, 0)
        )
        self.home_btn = Button(
            rect=(ScreenManager.WIDTH // 2 + 20, ScreenManager.HEIGHT // 2 + 40, 160, 60),
            label="HOME", on_click=self.go_home, color=(0, 200, 0)
        )
        self.quit_btn = Button(
            rect=(ScreenManager.WIDTH // 2 - 80, ScreenManager.HEIGHT // 2 + 120, 160, 50),
            label="QUIT GAME", on_click=self.quit_game, color=(180, 50, 50), text_color=(255, 255, 255)
        )
        self.buttons = [self.play_again_btn, self.home_btn, self.quit_btn]

        if self.is_victory is True:
            self.next_stage_btn = Button(
                rect=(ScreenManager.WIDTH - 150, 10, 130, 45),
                label="NEXT STAGE",
                on_click=self.next_stage,
                color=(0, 150, 250)
            )
            self.buttons.insert(0, self.next_stage_btn)

    def restart_game(self):
        self.result = "restart"

    def go_home(self):
        self.result = "home"

    def next_stage(self):
        self.result = "next_stage"

    def quit_game(self):
        pygame.quit()
        import sys
        sys.exit()

    def draw(self):
        super().draw_background()
        font_title = pygame.font.Font(None, 60)
        font_sub = pygame.font.Font(None, 28)

        if self.is_victory is None:
            title = "BATTLE QUIT"
            subtitle = "You exited the game early."
            color = ScreenManager.BLACK
        elif self.is_victory:
            title = "VICTORY!"
            subtitle = "You destroyed the enemy base!"
            color = ScreenManager.GREEN
        else:
            title = "GAME OVER"
            subtitle = "Your base was destroyed!"
            color = ScreenManager.RED

        title_surf = font_title.render(title, True, color)
        subtitle_surf = font_sub.render(subtitle, True, ScreenManager.BLACK)

        surface = self.screen_mgr.surface
        surface.blit(title_surf, (ScreenManager.WIDTH // 2 - title_surf.get_width() // 2, ScreenManager.HEIGHT // 3))
        surface.blit(subtitle_surf, (ScreenManager.WIDTH // 2 - subtitle_surf.get_width() // 2, ScreenManager.HEIGHT // 3 + 50))

        super().draw_buttons()
        self.screen_mgr.update()