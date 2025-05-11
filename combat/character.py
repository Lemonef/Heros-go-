import time

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
            if hasattr(target, 'take_damage'):
                target.take_damage(self.dmg)
            else:
                target.health -= self.dmg
                if target.health <= 0:
                    target.alive = False
                    target.is_dying = True
            self.last_time = time.time()