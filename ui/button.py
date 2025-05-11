import pygame
import time

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
        shadow_offset = 4
        shadow_rect = self.rect.move(shadow_offset, shadow_offset)
        pygame.draw.rect(surface, (50, 50, 50), shadow_rect, border_radius=5)
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
        color = (150, 150, 150) if res_mgr.upgrade_clicks >= 5 else (250, 180, 0)
        if mouse_over and res_mgr.upgrade_clicks < 5:
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
        color = (150, 150, 150) if not ready else (tuple(min(255, c + 40) for c in base_color) if mouse_over else base_color)
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