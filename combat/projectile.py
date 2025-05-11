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